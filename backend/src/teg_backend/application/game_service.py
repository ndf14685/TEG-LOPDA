"""Orquestador central: única fuente de verdad de partidas y eventos.

Todo lo que cambia estado pasa por acá: valida, aplica en el dominio,
persiste, emite eventos y notifica a comentarista/taunts/IA.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from ..ai import bot
from ..ai.ai_player import MoveRequest, build_ai_player, request_move
from ..ai.commentator import Comment, CommentatorService
from ..config import Settings
from ..domain import engine as eng
from ..domain.engine import EngineError, GameEngine, TurnState
from ..domain.enums import (
    PLAYING_ROLES, ErrorCode, EventType, GameStatus, Role, Visibility,
)
from ..domain.modes import DEFAULT_MODE, GAME_MODES
from ..domain.events import GameEvent
from ..infrastructure import repository as repo
from ..infrastructure.db import Database
from ..realtime.manager import ConnectionManager
from ..security import tokens as tok
from ..security.sanitize import (
    is_valid_asset_id, sanitize_nickname, sanitize_text,
)

log = logging.getLogger("teg.service")

ACTIVE_STATUSES = {GameStatus.LOBBY, GameStatus.READY, GameStatus.RUNNING, GameStatus.PAUSED}
# Estados previos al arranque: quien no se une antes queda sin territorios,
# sin objetivo y fuera del turn.order (ver confirm_join).
PRE_START_STATUSES = (GameStatus.DRAFT, GameStatus.LOBBY, GameStatus.READY)
TAUNTABLE_EVENTS = {
    EventType.ATTACK_RESOLVED, EventType.TERRITORY_CONQUERED, EventType.PLAYER_ELIMINATED,
}
# Paleta que sabe pintar el frontend (frontend/src/utils/playerColors.ts).
# Son 10 y no 8 a proposito: con exactamente max_players colores, un solo
# asiento revocado (alguien que no llego y fue reemplazado) ya dejaba al
# ultimo jugador sin color libre.
COLORES_DISPONIBLES = (
    "red", "blue", "green", "yellow", "purple", "orange", "cyan", "pink",
    "lime", "white",
)


def _first_valid_trio(hand: list) -> list[str] | None:
    from itertools import combinations

    from ..domain.cards import is_valid_trio

    for combo in combinations(hand, 3):
        if is_valid_trio(list(combo)):
            return [c.id for c in combo]
    return None


class ServiceError(Exception):
    def __init__(self, code: ErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class GameService:
    def __init__(
        self,
        db: Database,
        manager: ConnectionManager,
        commentator: CommentatorService,
        settings: Settings,
    ) -> None:
        self.db = db
        self.manager = manager
        self.commentator = commentator
        self.settings = settings
        self.commentator.emit = self._emit_ai_comment
        self._engines: dict[str, GameEngine] = {}
        self._locks: dict[str, asyncio.Lock] = {}
        # serializa la asignación de sequence_number por partida (las acciones
        # del juego y el worker del comentarista persisten concurrentemente)
        self._seq_locks: dict[str, asyncio.Lock] = {}
        # Cola de envio por partida: el broadcast sale del lock de juego pero
        # conserva el orden. Sin esto, un cliente lento retenia el lock y
        # frenaba a los otros siete.
        self._send_queues: dict[str, asyncio.Queue] = {}
        self._send_workers: dict[str, asyncio.Task] = {}
        # una vez apagado el servicio no se reviven workers: si no, un emit
        # tardio recrearia una tarea justo cuando estamos cerrando la base
        self._envios_detenidos = False
        self._ai_provider = build_ai_player("random")
        self._ai_tasks: dict[str, asyncio.Task] = {}
        # timeout de turno: uno por partida, arrancado al empezar cada turno
        # humano; se cancela apenas el turno avanza por cualquier via.
        self._turn_timers: dict[str, asyncio.Task] = {}
        # bandera propia (no reusar _envios_detenidos): detener_timers() la
        # marca ANTES de cancelar, asi ningun _vencer() en vuelo puede crear
        # un timer nuevo que quede fuera del snapshot que se está cancelando
        self._timers_detenidos = False
        # idem para los timers de gracia de reconexión (Room._offline_tasks):
        # nadie los cancelaba en el apagado, un _grace() que ya paso su sleep
        # (tan chico como 0.05s en tests) podia escribir PLAYER_DISCONNECTED
        # (persistido) después de que el lifespan cerrara la base
        self._gracias_detenidas = False
        # Todas las tareas sueltas que tocan SQLite (turnos y colocaciones de
        # bot, fan-out de saludos, rearmado del reloj tras una caida) se
        # registran acá: sin esto quedaban corriendo contra una base que el
        # lifespan ya cerró. _schedule_ai_placements era el caso peor, porque
        # ni siquiera guardaba referencia a su tarea.
        self._tareas_de_fondo: set[asyncio.Task] = set()
        self._fondo_detenido = False
        self.counters: dict[str, int] = {"games_created": 0, "events_emitted": 0}

    # --- helpers -----------------------------------------------------------

    def lock(self, game_id: str) -> asyncio.Lock:
        return self._locks.setdefault(game_id, asyncio.Lock())

    def join_url(self, code: str, token: str) -> str:
        return f"{self.settings.public_base_url}/join/{code}/{token}"

    async def _engine(self, game: dict) -> GameEngine:
        game_id = game["id"]
        if game_id not in self._engines:
            mode = GAME_MODES.get(
                game.get("config", {}).get("game_mode", DEFAULT_MODE), GAME_MODES[DEFAULT_MODE]
            )
            self._engines[game_id] = GameEngine.from_dict(
                game.get("state") or {}, default_map_id=mode["map_id"]
            )
        return self._engines[game_id]

    async def _save_engine(self, game_id: str) -> None:
        engine = self._engines.get(game_id)
        if engine is not None:
            await repo.update_game_state(self.db, game_id, engine.to_dict())

    async def _roles_map(self, game_id: str) -> dict[str, str]:
        players = await repo.get_players(self.db, game_id)
        return {p["id"]: p["role"] for p in players}

    async def emit(
        self,
        game_id: str,
        event_type: str,
        *,
        actor_id: str | None = None,
        target_id: str | None = None,
        payload: dict[str, Any] | None = None,
        visibility: Visibility = Visibility.PUBLIC,
        persisted: bool = True,
    ) -> GameEvent:
        event = GameEvent(
            event_type=event_type,
            game_id=game_id,
            actor_id=actor_id,
            target_id=target_id,
            payload=payload or {},
            visibility=visibility,
            persisted=persisted,
        )
        if persisted:
            seq_lock = self._seq_locks.setdefault(game_id, asyncio.Lock())
            async with seq_lock:
                event.sequence_number = await repo.next_sequence_number(self.db, game_id)
                if visibility == Visibility.PUBLIC:
                    event.public_sequence = await repo.next_public_sequence(self.db, game_id)
                await repo.append_event(self.db, event.model_dump(mode="json"))
                # Encolar adentro del lock de secuencia: asi el orden de envio
                # es por construccion el mismo que el de sequence_number. Si se
                # encola afuera, dos emit concurrentes pueden interleavarse en
                # cualquier await intermedio y salir al reves de como se
                # numeraron.
                self._encolar_envio(game_id, event)
        else:
            self._encolar_envio(game_id, event)
        self.counters["events_emitted"] += 1
        if persisted:
            await self._after_emit(game_id, event)
        return event

    def _encolar_envio(self, game_id: str, event: GameEvent) -> None:
        if self._envios_detenidos:
            return
        cola = self._send_queues.setdefault(game_id, asyncio.Queue())
        cola.put_nowait(event)
        worker = self._send_workers.get(game_id)
        if worker is None or worker.done():
            self._send_workers[game_id] = asyncio.create_task(self._drenar_envios(game_id))

    async def _drenar_envios(self, game_id: str) -> None:
        """Un worker por partida, vivo mientras viva el proceso.

        No se apaga por inactividad a proposito: cuando lo hacia, entre que la
        tarea recibia la cancelacion del timeout y quedaba en done() pasaban
        ticks del loop en los que un emit veia "worker vivo", no creaba uno
        nuevo, y el evento quedaba encolado sin nadie que lo consumiera.
        """
        cola = self._send_queues[game_id]
        while True:
            event = await cola.get()
            try:
                # los roles se resuelven aca y no en emit: saca una consulta del
                # camino caliente y evita un await entre numerar y encolar
                roles = await self._roles_map(game_id)
                await self.manager.broadcast(game_id, event, roles)
            except Exception:
                # CancelledError es BaseException: no cae aca, se propaga y
                # apaga el worker (solo la manda detener_envios)
                log.warning("fallo en broadcast diferido", exc_info=True)
            finally:
                cola.task_done()

    async def detener_envios(self) -> None:
        """Cancela los workers de envio y los espera.

        Se llama en el apagado ANTES de cerrar las bases: los workers consultan
        la DB para resolver roles, y dejarlos sueltos compitiendo contra el
        cierre de SQLite es como se ensucian los WAL.
        """
        self._envios_detenidos = True
        workers = [w for w in self._send_workers.values() if not w.done()]
        for worker in workers:
            worker.cancel()
        if workers:
            await asyncio.gather(*workers, return_exceptions=True)
        self._send_workers.clear()
        self._send_queues.clear()

    async def detener_timers(self) -> None:
        """Cancela los timeouts de turno pendientes, igual que detener_envios
        con los workers de envio. Se llama en el apagado del proceso: un timer
        huerfano que dispare despues de cerrar la base rompe todo.

        La bandera se marca ANTES de armar la lista a cancelar: si no, un
        _vencer() que este a mitad de camino puede colarse y crear un timer
        nuevo (via _armar_timeout_de_turno) que no esta en ese snapshot y
        sobrevive al apagado."""
        self._timers_detenidos = True
        timers = [t for t in self._turn_timers.values() if not t.done()]
        for timer in timers:
            timer.cancel()
        if timers:
            await asyncio.gather(*timers, return_exceptions=True)
        self._turn_timers.clear()

    async def detener_gracias_de_reconexion(self) -> None:
        """Cancela los timers de gracia de reconexión pendientes en todas las
        salas (Room._offline_tasks), mismo patrón que detener_timers con
        _turn_timers. Se llama en el apagado, ANTES de cerrar la base: un
        _grace() que ya pasó su `asyncio.sleep(reconnect_grace_seconds)` (tan
        chico como 0.05s en tests, 30s por default en producción) puede
        emitir PLAYER_DISCONNECTED (persistido, con su propia escritura a
        SQLite) después de que el lifespan cierre la conexión, si nadie lo
        cancela primero. Nadie lo hacía: a diferencia de _turn_timers y los
        workers de envío, Room._offline_tasks nunca tuvo un `detener_*`
        correspondiente."""
        self._gracias_detenidas = True
        tareas = [
            t
            for room in self.manager.rooms.values()
            for t in room._offline_tasks.values()
            if not t.done()
        ]
        for t in tareas:
            t.cancel()
        if tareas:
            await asyncio.gather(*tareas, return_exceptions=True)

    def _crear_tarea_de_fondo(self, coro) -> asyncio.Task | None:
        """Crea una tarea suelta y la deja registrada para el apagado.

        Devuelve None si el apagado ya empezó (y descarta la corrutina para no
        dejar un "coroutine was never awaited" colgando).
        """
        if self._fondo_detenido:
            coro.close()
            return None
        tarea = asyncio.create_task(coro)
        self._tareas_de_fondo.add(tarea)
        tarea.add_done_callback(self._tareas_de_fondo.discard)
        return tarea

    async def detener_tareas_de_fondo(self) -> None:
        """Cancela las tareas sueltas y las espera, mismo patrón que
        detener_envios/detener_timers. Se llama en el apagado ANTES de cerrar
        las bases: turnos y colocaciones de bot consultan y escriben SQLite,
        y rehidratar_partidas_activas las CREA al arrancar, así que un
        proceso que se levanta y se baja enseguida las tenía garantizadas."""
        self._fondo_detenido = True
        tareas = [t for t in self._tareas_de_fondo if not t.done()]
        for tarea in tareas:
            tarea.cancel()
        if tareas:
            await asyncio.gather(*tareas, return_exceptions=True)
        self._tareas_de_fondo.clear()
        self._ai_tasks.clear()

    async def _after_emit(self, game_id: str, event: GameEvent) -> None:
        """Efectos secundarios que nunca deben voltear la acción principal."""
        try:
            game = await repo.get_game(self.db, game_id)
            if game is None:
                return
            players = await repo.get_players(self.db, game_id)
            config = game.get("config", {})
            humor = int(config.get("humor_level", self.settings.humor_level_default))
            humor = min(humor, self.settings.humor_level_max)
            if config.get("commentator_enabled", True):
                self.commentator.notify(
                    game_id,
                    event.wire(),
                    [repo.public_player(p) for p in players],
                    humor,
                )
            if (
                event.event_type in TAUNTABLE_EVENTS
                and event.actor_id
                and event.target_id
            ):
                await self._fire_taunt(
                    game_id, players, event.actor_id, event.target_id,
                    event.event_type, event.event_id,
                )
            if event.event_type == EventType.GAME_STARTED:
                # En tarea aparte: _after_emit se awaitea dentro de emit(), y el
                # emit de GAME_STARTED corre dentro del `async with
                # self.lock(game_id)` de start_game. Bajar de 56 a 8 saludos no
                # alcanzaba: esas 8 emisiones, con su INSERT y su fan-out cada
                # una, seguian reteniendo el lock de la partida justo cuando los
                # ocho clientes estan renderizando el mapa.
                self._crear_tarea_de_fondo(
                    self._saludos_de_bienvenida(game_id, players, event.event_id)
                )
        except Exception:
            log.warning("fallo en efectos post-evento", exc_info=True)

    async def _saludos_de_bienvenida(
        self, game_id: str, players: list[dict], source_event_id: str
    ) -> None:
        """Un saludo por jugador, no uno por PAR: el doble bucle original daba
        56 emisiones con 8 jugadores (O(n^2)).

        Cada uno saluda a un rival DISTINTO: la version anterior elegia
        siempre "el primer jugador sentado", asi que con 8 jugadores seis de
        ocho nunca disparaban su saludo real contra su rival y la grabacion
        quedaba muda. Con el corrimiento circular cada asiento saluda al
        siguiente y ningun par se repite.
        """
        try:
            seated = [
                p for p in players
                if p["role"] in PLAYING_ROLES and p.get("profile_id")
            ]
            if len(seated) < 2:
                return
            for i, owner in enumerate(seated):
                rival = seated[(i + 1) % len(seated)]
                await self._fire_taunt(
                    game_id, players, owner["id"], rival["id"],
                    EventType.GAME_STARTED, source_event_id,
                )
        except asyncio.CancelledError:
            raise
        except Exception:
            log.warning("fallo el fan-out de saludos", exc_info=True)

    async def _fire_taunt(
        self,
        game_id: str,
        players: list[dict],
        actor_id: str,
        target_id: str,
        event_type: str,
        source_event_id: str,
    ) -> None:
        """Prioridad: audio grabado del perfil > asset legado por partida."""
        by_id = {p["id"]: p for p in players}
        actor, target = by_id.get(actor_id), by_id.get(target_id)
        payload: dict | None = None
        if actor and target and actor.get("profile_id") and target.get("profile_id"):
            taunt = await repo.find_profile_taunt(
                self.db, actor["profile_id"], target["profile_id"], event_type
            )
            if taunt:
                payload = {
                    "audio_asset_id": taunt["filename"],
                    "audio_url": f"/api/media/taunts/{taunt['filename']}",
                    "source_event_type": event_type,
                    "source_event_id": source_event_id,
                }
        if payload is None:
            asset_id = await repo.find_taunt(self.db, game_id, actor_id, target_id, event_type)
            if asset_id:
                payload = {
                    "audio_asset_id": asset_id,
                    "source_event_type": event_type,
                    "source_event_id": source_event_id,
                }
        if payload:
            await self.emit(
                game_id, EventType.TAUNT_TRIGGERED,
                actor_id=actor_id, target_id=target_id, payload=payload,
            )

    async def _emit_ai_comment(self, game_id: str, comment: Comment) -> None:
        await self.emit(
            game_id,
            EventType.AI_COMMENT_GENERATED,
            target_id=comment.target_player_id,
            visibility=Visibility(comment.visibility),
            payload={
                "text": comment.text,
                "emotion": comment.emotion,
                "audio_asset": comment.audio_asset,
            },
        )

    # --- perfiles persistentes ---------------------------------------------

    async def create_profile(self, nickname: str, color: str | None = None) -> dict:
        clean = sanitize_nickname(nickname)
        if not clean:
            raise ServiceError(ErrorCode.INVALID_PAYLOAD, "apodo vacío")
        token = tok.new_player_token()
        profile = await repo.create_profile(self.db, clean, tok.hash_token(token), color)
        return {
            "profile": repo.public_profile(profile),
            "token": token,
            "profile_url": f"{self.settings.public_base_url}/p/{token}",
        }

    async def list_profiles(self) -> list[dict]:
        return [repo.public_profile(p) for p in await repo.list_profiles(self.db)]

    async def regenerate_profile_token(self, profile_id: str) -> dict:
        profile = await repo.get_profile(self.db, profile_id)
        if profile is None:
            raise ServiceError(ErrorCode.NOT_FOUND, "perfil inexistente")
        token = tok.new_player_token()
        await repo.update_profile(self.db, profile_id, token_hash=tok.hash_token(token))
        return {"token": token, "profile_url": f"{self.settings.public_base_url}/p/{token}"}

    async def resolve_profile(self, token: str) -> dict:
        profile = await repo.find_profile_by_token_hash(self.db, tok.hash_token(token))
        if profile is None:
            raise ServiceError(ErrorCode.NOT_FOUND, "link de perfil inválido")
        return repo.public_profile(profile)

    # --- admin: partidas ---------------------------------------------------

    async def create_game(self, name: str, config: dict | None = None) -> dict:
        name = sanitize_text(name, 60) or "partida-sin-nombre"
        cfg = {
            "commentator_enabled": self.settings.commentator_enabled,
            "humor_level": self.settings.humor_level_default,
            "nickname_editable_default": True,
        }
        if config:
            cfg.update(config)
        cfg["humor_level"] = max(0, min(int(cfg.get("humor_level", 2)), self.settings.humor_level_max))
        # contrato assets/contracts/game-init-schema.json: modo + assets de mapa
        mode = cfg.get("game_mode", DEFAULT_MODE)
        if mode not in GAME_MODES:
            raise ServiceError(ErrorCode.INVALID_PAYLOAD, f"game_mode inválido: {mode}")
        cfg["game_mode"] = mode
        cfg["map_assets"] = GAME_MODES[mode]["map_assets"]
        for _ in range(10):
            code = tok.new_game_code()
            if await repo.get_game_by_code(self.db, code) is None:
                break
        else:  # pragma: no cover
            raise ServiceError(ErrorCode.GAME_STATE_CONFLICT, "no se pudo generar código")
        game = await repo.create_game(self.db, code, name, cfg)
        await repo.update_game_status(self.db, game["id"], GameStatus.LOBBY)
        game["status"] = GameStatus.LOBBY
        self.counters["games_created"] += 1
        await self.emit(
            game["id"], EventType.GAME_CREATED,
            payload={
                "name": name, "code": code,
                "game_mode": cfg["game_mode"], "map_assets": cfg["map_assets"],
            },
        )
        return game

    async def get_game_or_404(self, game_id: str) -> dict:
        game = await repo.get_game(self.db, game_id)
        if game is None:
            raise ServiceError(ErrorCode.NOT_FOUND, "partida inexistente")
        return game

    async def invite_player(
        self,
        game_id: str,
        nickname: str,
        role: str = Role.PLAYER,
        color: str | None = None,
        nickname_editable: bool | None = None,
        profile_id: str | None = None,
    ) -> dict:
        game = await self.get_game_or_404(game_id)
        if game["status"] not in ACTIVE_STATUSES:
            raise ServiceError(ErrorCode.GAME_STATE_CONFLICT, "la partida no admite invitaciones")
        if role not in (Role.ADMIN, Role.PLAYER, Role.SPECTATOR, Role.AI_PLAYER):
            raise ServiceError(ErrorCode.INVALID_PAYLOAD, f"rol inválido: {role}")
        if profile_id:
            profile = await repo.get_profile(self.db, profile_id)
            if profile is None:
                raise ServiceError(ErrorCode.NOT_FOUND, "perfil inexistente")
            # el perfil manda: apodo y color del amigo, siempre iguales
            nickname = nickname or profile["nickname"]
            if not nickname.strip():
                nickname = profile["nickname"]
            if role in (Role.PLAYER, Role.AI_PLAYER):
                # solo quien se sienta a jugar hereda el color del perfil:
                # invitar a un amigo como espectador desde su perfil (el flujo
                # normal) le daba color y ese color salia de la paleta
                color = color or profile["color"]
        nickname = sanitize_nickname(nickname)
        if not nickname:
            raise ServiceError(ErrorCode.INVALID_PAYLOAD, "apodo vacío")
        editable = (
            nickname_editable
            if nickname_editable is not None
            else bool(game["config"].get("nickname_editable_default", True))
        )
        existentes = await repo.get_players(self.db, game_id)
        if role in (Role.PLAYER, Role.AI_PLAYER):
            # Mismo criterio que start_game: un asiento revocado (kick_player
            # solo marca token_revoked, la fila sobrevive) NO ocupa lugar. Sin
            # esto, echar a alguien que no llego y querer invitar su reemplazo
            # daba 409 "la partida admite hasta N jugadores" -- justo el caso
            # que motivo esta fase.
            jugando = [
                p for p in existentes
                if p["role"] in PLAYING_ROLES and not p["token_revoked"]
            ]
            modo = GAME_MODES[game["config"].get("game_mode", DEFAULT_MODE)]
            if len(jugando) >= modo["max_players"]:
                raise ServiceError(
                    ErrorCode.GAME_STATE_CONFLICT,
                    f"la partida admite hasta {modo['max_players']} jugadores",
                )
        # Color unico: dos jugadores del mismo color son indistinguibles en el mapa
        # (incidente 27/07: Seba y Gabi tenian los dos "red"). Solo aplica a
        # roles que se sientan a jugar: un espectador o admin sin color no debe
        # consumir la paleta (regresion: antes quedaban con color=None).
        if role in (Role.PLAYER, Role.AI_PLAYER):
            # `usados` se acota por rol Y por token_revoked, exactamente igual
            # que el conteo de asientos de arriba. Acotar solo por rol dejaba
            # A1 a medias: cada echado seguia reteniendo su color para siempre,
            # asi que echar+reemplazar en bucle agotaba la paleta igual (al
            # tercer reemplazo, 409 "no quedan colores libres"). Expandir la
            # paleta a 10 solo compraba dos reemplazos; la causa es esta.
            usados = {
                p["color"] for p in existentes
                if p.get("color")
                and p["role"] in PLAYING_ROLES
                and not p["token_revoked"]
            }
            if not color or color in usados:
                color = next((c for c in COLORES_DISPONIBLES if c not in usados), None)
                if color is None:
                    raise ServiceError(ErrorCode.GAME_STATE_CONFLICT, "no quedan colores libres")
        token: str | None = None
        token_hash: str | None = None
        if role != Role.AI_PLAYER:
            token = tok.new_player_token()
            token_hash = tok.hash_token(token)
        player = await repo.create_player(
            self.db, game_id, nickname, role, token_hash, color, editable,
            profile_id=profile_id,
        )
        if role == Role.AI_PLAYER:
            # los jugadores IA no tienen link: quedan "unidos" desde el alta
            await repo.update_player(self.db, player["id"], joined_at=player["created_at"], is_ready=True)
        await self.emit(
            game_id,
            EventType.PLAYER_INVITED,
            target_id=player["id"],
            visibility=Visibility.ADMIN,
            payload={"player": repo.public_player(player), "role": role},
        )
        return {
            "player": player,
            "token": token,
            "join_url": self.join_url(game["code"], token) if token else None,
        }

    async def regenerate_token(self, game_id: str, player_id: str) -> dict:
        game = await self.get_game_or_404(game_id)
        player = await repo.get_player(self.db, player_id)
        if player is None or player["game_id"] != game_id:
            raise ServiceError(ErrorCode.NOT_FOUND, "jugador inexistente")
        token = tok.new_player_token()
        await repo.update_player(
            self.db, player_id, token_hash=tok.hash_token(token), token_revoked=False
        )
        await self.manager.disconnect_player(game_id, player_id)
        await self.emit(
            game_id, EventType.TOKEN_REGENERATED, target_id=player_id,
            visibility=Visibility.ADMIN, payload={},
        )
        return {"token": token, "join_url": self.join_url(game["code"], token)}

    async def kick_player(self, game_id: str, player_id: str) -> None:
        game = await self.get_game_or_404(game_id)
        player = await repo.get_player(self.db, player_id)
        if player is None or player["game_id"] != game_id:
            raise ServiceError(ErrorCode.NOT_FOUND, "jugador inexistente")
        await repo.update_player(self.db, player_id, token_revoked=True)
        engine = await self._engine(game)
        engine.remove_player(player_id)
        await self._save_engine(game_id)
        await self.manager.disconnect_player(game_id, player_id)
        await self.emit(
            game_id, EventType.PLAYER_KICKED, target_id=player_id,
            payload={"nickname": player["nickname"]},
        )

    async def update_commentator_config(
        self, game_id: str, *, enabled: bool | None = None,
        humor_level: int | None = None, muted: bool | None = None,
    ) -> dict:
        game = await self.get_game_or_404(game_id)
        cfg = game["config"]
        if enabled is not None:
            cfg["commentator_enabled"] = bool(enabled)
        if humor_level is not None:
            level = max(0, min(int(humor_level), self.settings.humor_level_max))
            if int(humor_level) > self.settings.humor_level_max:
                log.info(
                    "humor_level pedido supera el máximo permitido",
                    extra={"ctx": {"requested": humor_level, "max": self.settings.humor_level_max}},
                )
            cfg["humor_level"] = level
        if muted is not None:
            self.commentator.set_muted(game_id, bool(muted))
            cfg["commentator_muted"] = bool(muted)
        await repo.update_game_config(self.db, game_id, cfg)
        return cfg

    async def set_taunt(
        self, game_id: str, owner_id: str, target_id: str, event_type: str, asset_id: str
    ) -> dict:
        await self.get_game_or_404(game_id)
        if event_type not in {e.value for e in TAUNTABLE_EVENTS}:
            raise ServiceError(ErrorCode.INVALID_PAYLOAD, f"evento no taunteable: {event_type}")
        if not is_valid_asset_id(asset_id):
            raise ServiceError(ErrorCode.INVALID_PAYLOAD, "asset_id inválido")
        for pid in (owner_id, target_id):
            p = await repo.get_player(self.db, pid)
            if p is None or p["game_id"] != game_id:
                raise ServiceError(ErrorCode.NOT_FOUND, f"jugador inexistente: {pid}")
        return await repo.upsert_taunt(self.db, game_id, owner_id, target_id, event_type, asset_id)

    # --- ciclo de vida de la partida --------------------------------------

    async def _set_status(self, game_id: str, status: GameStatus) -> None:
        await repo.update_game_status(self.db, game_id, status)

    async def start_game(self, game_id: str) -> dict:
        async with self.lock(game_id):
            game = await self.get_game_or_404(game_id)
            if game["status"] not in (GameStatus.LOBBY, GameStatus.READY):
                raise ServiceError(ErrorCode.GAME_STATE_CONFLICT, "la partida no está en lobby")
            players = await repo.get_players(self.db, game_id)
            seated = [
                p for p in players
                if p["role"] in PLAYING_ROLES and p["joined_at"] and not p["token_revoked"]
            ]
            mode = GAME_MODES[game["config"].get("game_mode", DEFAULT_MODE)]
            if len(seated) > mode["max_players"]:
                raise ServiceError(
                    ErrorCode.INVALID_ACTION,
                    f"máximo {mode['max_players']} jugadores para este modo",
                )
            if len(seated) < mode["min_players"]:
                raise ServiceError(
                    ErrorCode.INVALID_ACTION,
                    f"mínimo {mode['min_players']} jugadores para este modo",
                )
            engine = await self._engine(game)
            try:
                turn = engine.start([p["id"] for p in seated])
            except EngineError as exc:
                raise ServiceError(ErrorCode.INVALID_ACTION, str(exc)) from exc
            nicknames = {p["id"]: p["nickname"] for p in seated}
            objectives = engine.assign_objectives(nicknames)
            await self._save_engine(game_id)
            await self._set_status(game_id, GameStatus.RUNNING)
            await self.emit(
                game_id, EventType.GAME_STARTED,
                payload={
                    "turn_order": turn.order,
                    "players": [repo.public_player(p) for p in seated],
                    "territories": {tid: t.to_dict() for tid, t in engine.territories.items()},
                    "phase": turn.phase,
                    "reinforcements_available": turn.reinforcements_available,
                    "stage": engine.stage,
                },
            )
            for pid, obj in objectives.items():
                await self.emit(
                    game_id, EventType.OBJECTIVE_ASSIGNED, target_id=pid,
                    visibility=Visibility.PRIVATE,
                    payload={"objective": obj.public_view()},
                )
            await self.emit(
                game_id, EventType.PLACEMENT_STARTED,
                payload={
                    "stage": engine.stage,
                    "pool_size": eng.PLACEMENT_ROUNDS[0],
                    "players": list(engine.turn.order),
                },
            )
            self._schedule_ai_placements(game_id)
            return {"status": GameStatus.RUNNING, "turn_order": turn.order}

    def _cancelar_timeout_de_turno(self, game_id: str) -> None:
        viejo = self._turn_timers.pop(game_id, None)
        if viejo:
            viejo.cancel()

    def _armar_timeout_de_turno(self, game_id: str, player_id: str, turn_number: int) -> None:
        """Arranca el reloj del turno actual. Cancela cualquier timer previo
        de esta partida: siempre hay a lo sumo uno vivo por partida."""
        self._cancelar_timeout_de_turno(game_id)
        if self._timers_detenidos:
            return  # apagado en curso: no crear tareas nuevas

        async def _vencer() -> None:
            try:
                await asyncio.sleep(self.settings.turn_timeout_seconds)
                turn: TurnState | None = None
                async with self.lock(game_id):
                    # Todo bajo el mismo lock y sin soltarlo en el medio.
                    game = await self.get_game_or_404(game_id)
                    if game["status"] != GameStatus.RUNNING:
                        return  # se pausó/terminó/canceló mientras dormíamos
                    engine = await self._engine(game)
                    if (
                        engine.stage != "turns"
                        or engine.turn.turn_number != turn_number
                        or engine.turn.current_player_id != player_id
                    ):
                        return  # el turno ya avanzó (o cambió de dueño) por su cuenta
                    room = self.manager.room(game_id)
                    if room.sockets.get(player_id):
                        return  # reconectó: nunca se lo saltea
                    # A partir de acá, mutación SINCRÓNICA del estado, sin
                    # ningún await en el medio: registrar una reconexión no
                    # necesita este lock (room.add() es sincrónico, en el
                    # endpoint WS), así que cualquier await entre el chequeo
                    # de sockets y la mutación real es ventana suficiente
                    # para que el jugador reconecte y pierda el turno igual
                    # pese a estar presente (así se coló el hallazgo crítico
                    # de la ronda anterior: el emit incondicional de
                    # TURN_ENDED, con su round-trip a SQLite, quedaba en el
                    # medio). Se duplica a propósito la secuencia de
                    # _cerrar_y_avanzar_turno en vez de reusarla: ese helper
                    # intercala los emits ENTRE las mutaciones para el
                    # camino normal de end_turn, que ya funciona y no hay
                    # que tocar.
                    wager_result = engine.resolve_wager(player_id)
                    card = engine.award_card_if_due(player_id)
                    turn = engine.advance_turn()
                    # Desde acá el turno YA avanzó: los awaits que siguen son
                    # solo persistencia/notificación, no pueden "deshacer"
                    # el salteo aunque el jugador reconecte mientras corren.
                    await self._save_engine(game_id)
                    if wager_result is not None:
                        await self.emit(
                            game_id, EventType.WAGER_RESOLVED, actor_id=player_id,
                            payload=wager_result,
                        )
                    if card is not None:
                        await self.emit(
                            game_id, EventType.CARD_AWARDED, actor_id=player_id,
                            payload={"player_id": player_id},
                        )
                        await self._emit_hand(game_id, engine, player_id)
                    await self.emit(
                        game_id, EventType.TURN_ENDED, actor_id=player_id, payload={},
                    )
                # El evento se emite DESPUÉS de confirmar que el turno avanzó
                # de verdad: si algo arriba hubiera fallado o vuelto antes,
                # no queda un turn.skipped mintiendo en el historial.
                await self.emit(
                    game_id, EventType.TURN_SKIPPED, actor_id=player_id,
                    payload={"player_id": player_id, "reason": "offline"},
                )
                await self._start_turn(game_id, turn.current_player_id, turn.turn_number)
            except asyncio.CancelledError:
                raise
            except Exception:
                log.warning("fallo el timeout de turno", exc_info=True)

        self._turn_timers[game_id] = asyncio.create_task(_vencer())

    async def _start_turn(self, game_id: str, player_id: str | None, turn_number: int) -> None:
        if player_id is None:
            self._cancelar_timeout_de_turno(game_id)
            return
        game = await repo.get_game(self.db, game_id)
        engine = await self._engine(game) if game else None
        phase = engine.turn.phase if engine else "reinforcement"
        reinf = engine.turn.reinforcements_available if engine else 3
        if engine is not None:
            # snapshot del estado al inicio del turno: la base del replay
            await repo.save_turn_snapshot(
                self.db, game_id, engine.turn.turn_number, engine.to_dict()
            )
        await self.emit(
            game_id, EventType.TURN_STARTED, actor_id=player_id,
            payload={"turn_number": turn_number, "phase": phase, "reinforcements_available": reinf},
        )
        if engine is not None:
            await self.emit(
                game_id, EventType.LEGAL_ACTIONS, target_id=player_id,
                visibility=Visibility.PRIVATE,
                payload={"actions": engine.legal_actions(player_id)},
                persisted=False,
            )
        player = await repo.get_player(self.db, player_id)
        if player and player["role"] == Role.AI_PLAYER:
            # los bots ya tienen su propio agendado; no armar el timeout
            self._cancelar_timeout_de_turno(game_id)
            self._schedule_ai_turn(game_id, player_id)
        elif player:
            self._armar_timeout_de_turno(game_id, player_id, turn_number)
        else:
            self._cancelar_timeout_de_turno(game_id)

    async def pause_game(self, game_id: str) -> None:
        game = await self.get_game_or_404(game_id)
        if game["status"] != GameStatus.RUNNING:
            raise ServiceError(ErrorCode.GAME_STATE_CONFLICT, "solo se pausa una partida en curso")
        # nadie esta "en el reloj" mientras la partida esta pausada
        self._cancelar_timeout_de_turno(game_id)
        await self._set_status(game_id, GameStatus.PAUSED)
        await self.emit(game_id, EventType.GAME_PAUSED)

    async def resume_game(self, game_id: str) -> None:
        game = await self.get_game_or_404(game_id)
        if game["status"] != GameStatus.PAUSED:
            raise ServiceError(ErrorCode.GAME_STATE_CONFLICT, "la partida no está pausada")
        await self._set_status(game_id, GameStatus.RUNNING)
        await self.emit(game_id, EventType.GAME_RESUMED)
        # el turno sigue donde estaba: reactivar su reloj si es de un humano
        engine = await self._engine(game)
        current_id = engine.turn.current_player_id
        if current_id:
            player = await repo.get_player(self.db, current_id)
            if player and player["role"] != Role.AI_PLAYER:
                self._armar_timeout_de_turno(game_id, current_id, engine.turn.turn_number)

    async def finish_game(
        self,
        game_id: str,
        winner_player_id: str | None = None,
        winning_objective: dict | None = None,
    ) -> dict:
        game = await self.get_game_or_404(game_id)
        if game["status"] not in ACTIVE_STATUSES:
            raise ServiceError(ErrorCode.GAME_STATE_CONFLICT, "la partida no está activa")
        engine = await self._engine(game)
        events_count = await repo.next_sequence_number(self.db, game_id) - 1
        summary = {
            "turns_played": engine.turn.turn_number,
            "winner_player_id": winner_player_id,
            "total_events": events_count,
            "objective": winning_objective,
        }
        self._cancelar_timeout_de_turno(game_id)
        await self._set_status(game_id, GameStatus.FINISHED)
        await self.emit(game_id, EventType.GAME_FINISHED, target_id=winner_player_id, payload=summary)
        await self._publish_stats(game_id)
        return summary

    async def _publish_stats(self, game_id: str) -> None:
        """Calcula las estadísticas reales del event log y las publica."""
        try:
            from .stats import assign_trophies, compute_stats

            players = await repo.get_players(self.db, game_id)
            events = await repo.get_events(self.db, game_id, limit=100000)
            stats = compute_stats(events, players)
            trophies = assign_trophies(stats)
            by_id = {p["id"]: p for p in players}
            for pid, s in stats.items():
                await repo.save_game_stats(
                    self.db, game_id, pid, by_id.get(pid, {}).get("profile_id"),
                    s, trophies.get(pid, []),
                )
            await self.emit(
                game_id, EventType.STATS_READY,
                payload={"stats": stats, "trophies": trophies},
            )
        except Exception:
            log.warning("fallo publicando estadísticas", exc_info=True)

    async def cancel_game(self, game_id: str) -> None:
        game = await self.get_game_or_404(game_id)
        if game["status"] in (GameStatus.FINISHED, GameStatus.CANCELLED):
            raise ServiceError(ErrorCode.GAME_STATE_CONFLICT, "la partida ya terminó")
        self._cancelar_timeout_de_turno(game_id)
        await self._set_status(game_id, GameStatus.CANCELLED)
        await self.emit(game_id, EventType.GAME_CANCELLED)

    # --- acceso de jugadores ----------------------------------------------

    async def resolve_join(self, code: str, token: str) -> dict:
        game = await repo.get_game_by_code(self.db, code)
        if game is None:
            raise ServiceError(ErrorCode.NOT_FOUND, "link inválido")
        player = await repo.find_player_by_token_hash(self.db, game["id"], tok.hash_token(token))
        if player is None:
            # respuesta genérica: no revelar si el código existe o el token falló
            raise ServiceError(ErrorCode.NOT_FOUND, "link inválido")
        return {"game": game, "player": player}

    async def confirm_join(self, code: str, token: str, nickname: str | None) -> dict:
        resolved = await self.resolve_join(code, token)
        game, player = resolved["game"], resolved["player"]
        # Recuperar un asiento convertido a IA tiene que poder pasar con la
        # partida YA en curso: es exactamente para eso que existe la
        # conversion (convert_seat_to_ai promete que "su link sigue siendo
        # valido y al volver a entrar recupera el asiento"). Con la
        # restauracion despues del guard de PRE_START_STATUSES era codigo
        # inalcanzable: el jugador igual se conectaba por WebSocket y miraba
        # a un bot jugar su asiento, sin error y sin explicacion.
        # Se exige joined_at: quien nunca se unio no tiene asiento que
        # recuperar (no esta en turn.order ni tiene territorios) y sigue
        # cayendo en el guard, que es el caso original que hay que sostener.
        recupera_asiento_ia = bool(
            player["role"] == Role.AI_PLAYER
            and player["token_hash"]
            and player["joined_at"]
        )
        if game["status"] not in PRE_START_STATUSES and not recupera_asiento_ia:
            # Antes se aceptaba durante RUNNING/PAUSED: quien no habia entrado
            # antes del arranque quedaba conectado pero sin territorios, sin
            # objetivo y fuera del turn.order, sin ningun evento que lo explicara.
            raise ServiceError(
                ErrorCode.GAME_STATE_CONFLICT,
                "la partida ya empezó: pedile al anfitrión que te sume a la próxima",
            )
        if nickname and player["nickname_editable"]:
            clean = sanitize_nickname(nickname)
            if clean:
                await repo.update_player(self.db, player["id"], nickname=clean)
                player["nickname"] = clean
        if player["role"] == Role.AI_PLAYER and player["token_hash"]:
            # el humano vuelve: recupera el asiento que jugaba la IA
            await self._restaurar_asiento_humano(game, player)
        first_join = player["joined_at"] is None
        if first_join:
            from ..domain.events import utcnow_iso

            await repo.update_player(self.db, player["id"], joined_at=utcnow_iso())
            await self.emit(
                game["id"], EventType.PLAYER_JOINED, actor_id=player["id"],
                payload={"player": repo.public_player({**player, "joined_at": "x"})},
            )
        return {
            "game": repo.public_game(game),
            "player": repo.public_player(player) | {"nickname_editable": player["nickname_editable"]},
            "ws_path": f"/ws/{game['code']}",
        }

    async def snapshot(self, game: dict, for_player_id: str) -> dict:
        players = await repo.get_players(self.db, game["id"])
        room = self.manager.room(game["id"])
        engine = await self._engine(game)
        recent = await repo.get_events(self.db, game["id"], limit=50, public_only=True)
        return {
            "game": repo.public_game(game),
            "you": for_player_id,
            "players": [
                repo.public_player(p) | {"presence": room.presence_of(p["id"])}
                for p in players
                if not p["token_revoked"] or p["role"] == Role.AI_PLAYER
            ],
            # el turno viaja también durante la colocación: el orden ya está
            # sorteado y la UI lo necesita para armar el estado local
            "turn": (
                engine.turn.to_dict()
                if game["status"] in (GameStatus.RUNNING, GameStatus.PAUSED)
                else None
            ),
            "territories": {tid: t.to_dict() for tid, t in engine.territories.items()} if game["status"] in (GameStatus.RUNNING, GameStatus.PAUSED) else {},
            "stage": engine.stage,
            "placement": (
                {
                    "remaining": engine.placement_pools.get(for_player_id, 0),
                    "pending": engine.placement_pending.get(for_player_id, {}),
                    "players_done": [
                        pid for pid, n in engine.placement_pools.items() if n == 0
                    ],
                }
                if engine.stage in ("placement_1", "placement_2")
                else None
            ),
            "pacts": [k.split("|") for k in sorted(engine.pacts)],
            "pact_proposal_from": engine.pact_proposals.get(for_player_id),
            "your_cards": [c.to_dict() for c in engine.cards.hands.get(for_player_id, [])],
            "your_objective": (
                engine.objectives[for_player_id].public_view()
                if for_player_id in engine.objectives
                else None
            ),
            # adyacencia del mapa activo: el frontend resalta vecinos atacables
            "map_adjacency": {
                tid: sorted(t.neighbor_ids) for tid, t in engine.map.territories.items()
            },
            "recent_events": recent[-50:],
        }

    # --- presencia ---------------------------------------------------------

    async def on_connect(self, game: dict, player: dict) -> None:
        # el socket ya fue agregado a la sala por el endpoint WS
        await self.emit(
            game["id"], EventType.PRESENCE_CHANGED, actor_id=player["id"],
            payload={"presence": "online"}, persisted=False,
        )

    async def on_disconnect(self, game_id: str, player_id: str) -> None:
        room = self.manager.room(game_id)
        if player_id in room.sockets:
            return  # quedan otras pestañas abiertas
        room.presence[player_id] = "reconnecting"
        await self.emit(
            game_id, EventType.PRESENCE_CHANGED, actor_id=player_id,
            payload={"presence": "reconnecting"}, persisted=False,
        )
        # En tarea aparte, no en linea: el `finally` del endpoint WS puede
        # correr dentro de un cancel scope YA cancelado (TestClient al cerrar
        # el socket, uvicorn al apagarse), y ahi cualquier `await` levanta
        # CancelledError antes de llegar a la base. Verificado con
        # instrumentacion: en linea, la lectura de la partida nunca completaba.
        # Ademas saca I/O de SQLite del camino de la baja de una conexion.
        self._crear_tarea_de_fondo(
            self._rearmar_reloj_si_es_su_turno(game_id, player_id)
        )

        async def _grace() -> None:
            try:
                await asyncio.sleep(self.settings.reconnect_grace_seconds)
                if player_id not in room.sockets:
                    room.presence[player_id] = "offline"
                    await self.emit(
                        game_id, EventType.PLAYER_DISCONNECTED, actor_id=player_id,
                        payload={"presence": "offline"},
                    )
            except asyncio.CancelledError:
                raise
            except Exception:
                # p. ej. apagado del servicio durante la gracia de reconexión
                log.debug("gracia de reconexión interrumpida", exc_info=True)

        old = room._offline_tasks.get(player_id)
        if old:
            old.cancel()
        if self._gracias_detenidas:
            return  # apagado en curso: no crear tareas nuevas
        room._offline_tasks[player_id] = asyncio.create_task(_grace())

    async def _rearmar_reloj_si_es_su_turno(self, game_id: str, player_id: str) -> None:
        """El timeout de turno era de un solo disparo: _vencer() retorna sin
        rearmar nada si el jugador estaba online al cumplirse el plazo, y
        nadie lo volvia a armar. Con 8 personas los turnos superan los 180 s
        de forma rutinaria, asi que el jugador que estaba presente a los 180 s
        y se caia a los 181 s no tenia ningun reloj que lo salteara: la mesa
        quedaba esperandolo para siempre. Este es el camino COMUN, no un borde.

        No crea timers duplicados: _armar_timeout_de_turno cancela el timer
        previo de la partida antes de crear el nuevo (hay a lo sumo uno vivo
        por partida, por construccion).
        """
        try:
            game = await repo.get_game(self.db, game_id)
            if game is None or game["status"] != GameStatus.RUNNING:
                return
            engine = await self._engine(game)
            if engine.stage != "turns" or engine.turn.current_player_id != player_id:
                return
            player = await repo.get_player(self.db, player_id)
            if player is None or player["role"] == Role.AI_PLAYER:
                return
            self._armar_timeout_de_turno(game_id, player_id, engine.turn.turn_number)
        except Exception:
            # nunca debe voltear la baja de una conexion
            log.warning("no se pudo rearmar el reloj de turno", exc_info=True)

    # --- acciones de jugador ------------------------------------------------

    async def set_ready(self, game: dict, player: dict, ready: bool) -> None:
        # bajo el lock de la partida y releyendo estado: un "listo" que llega
        # mientras el admin inicia no debe pisar el estado running con ready
        async with self.lock(game["id"]):
            game = await self.get_game_or_404(game["id"])
            if game["status"] not in (GameStatus.LOBBY, GameStatus.READY):
                raise ServiceError(ErrorCode.GAME_STATE_CONFLICT, "la partida ya empezó")
            await repo.update_player(self.db, player["id"], is_ready=ready)
            players = await repo.get_players(self.db, game["id"])
            seated = [
                p for p in players
                if p["role"] in PLAYING_ROLES and p["joined_at"] and not p["token_revoked"]
            ]
            all_ready = len(seated) >= 2 and all(p["is_ready"] for p in seated)
            new_status = GameStatus.READY if all_ready else GameStatus.LOBBY
            if game["status"] != new_status:
                await self._set_status(game["id"], new_status)
        await self.emit(
            game["id"], EventType.PLAYER_READY, actor_id=player["id"],
            payload={"ready": ready, "all_ready": all_ready, "game_status": new_status},
        )

    async def chat(self, game: dict, player: dict, text: str, target_player_id: str | None) -> None:
        clean = sanitize_text(text)
        if not clean:
            raise ServiceError(ErrorCode.INVALID_PAYLOAD, "mensaje vacío")
        visibility = Visibility.PUBLIC
        if target_player_id:
            target = await repo.get_player(self.db, target_player_id)
            if target is None or target["game_id"] != game["id"]:
                raise ServiceError(ErrorCode.NOT_FOUND, "destinatario inexistente")
            visibility = Visibility.PRIVATE
        await self.emit(
            game["id"], EventType.CHAT_MESSAGE, actor_id=player["id"],
            target_id=target_player_id, visibility=visibility,
            payload={"text": clean},
        )

    async def propose_pact(self, game_id: str, player_id: str, target_id: str) -> None:
        async with self.lock(game_id):
            game = await self.get_game_or_404(game_id)
            if game["status"] != GameStatus.RUNNING:
                raise ServiceError(ErrorCode.GAME_NOT_RUNNING, "la partida no está en curso")
            engine = await self._engine(game)
            try:
                engine.propose_pact(player_id, target_id)
            except EngineError as exc:
                raise ServiceError(ErrorCode.INVALID_ACTION, str(exc)) from exc
            await self._save_engine(game_id)
            await self.emit(
                game_id, EventType.PACT_PROPOSED, actor_id=player_id,
                target_id=target_id, payload={},
            )

    async def respond_pact(self, game_id: str, player_id: str, accept: bool) -> None:
        async with self.lock(game_id):
            game = await self.get_game_or_404(game_id)
            engine = await self._engine(game)
            try:
                from_id = engine.respond_pact(player_id, accept)
            except EngineError as exc:
                raise ServiceError(ErrorCode.INVALID_ACTION, str(exc)) from exc
            await self._save_engine(game_id)
            await self.emit(
                game_id,
                EventType.PACT_ACCEPTED if accept else EventType.PACT_REJECTED,
                actor_id=player_id, target_id=from_id, payload={},
            )

    async def break_pact(self, game_id: str, player_id: str, other_id: str) -> None:
        async with self.lock(game_id):
            game = await self.get_game_or_404(game_id)
            engine = await self._engine(game)
            try:
                engine.break_pact(player_id, other_id)
            except EngineError as exc:
                raise ServiceError(ErrorCode.INVALID_ACTION, str(exc)) from exc
            await self._save_engine(game_id)
            await self.emit(
                game_id, EventType.PACT_BROKEN, actor_id=player_id,
                target_id=other_id, payload={"betrayal": False},
            )

    async def _require_running_turn(self, game_id: str, player_id: str) -> GameEngine:
        game = await self.get_game_or_404(game_id)
        if game["status"] != GameStatus.RUNNING:
            raise ServiceError(ErrorCode.GAME_NOT_RUNNING, "la partida no está en curso")
        engine = await self._engine(game)
        try:
            engine.require_turn(player_id)
        except EngineError as exc:
            raise ServiceError(ErrorCode.NOT_YOUR_TURN, str(exc)) from exc
        return engine

    async def roll_dice(self, game_id: str, player_id: str, count: int) -> list[int]:
        async with self.lock(game_id):
            await self._require_running_turn(game_id, player_id)
            try:
                dice = eng.roll_dice(int(count))
            except (EngineError, ValueError) as exc:
                raise ServiceError(ErrorCode.INVALID_PAYLOAD, str(exc)) from exc
            await self.emit(
                game_id, EventType.DICE_ROLLED, actor_id=player_id,
                payload={"dice": dice, "count": len(dice)},
            )
            return dice

    async def attack(
        self,
        game_id: str,
        player_id: str,
        target_player_id: str | None = None,
        attacker_dice_count: int = 3,
        source_territory_id: str | None = None,
        target_territory_id: str | None = None,
    ) -> dict:
        async with self.lock(game_id):
            engine = await self._require_running_turn(game_id, player_id)

            src_terr = engine.territories.get(source_territory_id) if source_territory_id else None
            tgt_terr = engine.territories.get(target_territory_id) if target_territory_id else None

            # el ataque territorial solo vale en la fase de ataque
            if (src_terr or tgt_terr) and engine.turn.phase != "attack":
                raise ServiceError(
                    ErrorCode.INVALID_ACTION,
                    f"no podés atacar en la fase de {engine.turn.phase}",
                )

            if src_terr:
                if src_terr.owner_player_id != player_id:
                    raise ServiceError(ErrorCode.INVALID_ACTION, "el territorio de origen no te pertenece")
                if src_terr.armies <= 1:
                    raise ServiceError(ErrorCode.INVALID_ACTION, "necesitás al menos 2 ejércitos para atacar")

            if tgt_terr:
                if tgt_terr.owner_player_id == player_id:
                    raise ServiceError(ErrorCode.INVALID_ACTION, "no podés atacar tu propio territorio")
                if not target_player_id:
                    target_player_id = tgt_terr.owner_player_id

            if src_terr and tgt_terr and not engine.are_neighbors(
                src_terr.territory_id, tgt_terr.territory_id
            ):
                raise ServiceError(ErrorCode.INVALID_ACTION, "esos territorios no son limítrofes")

            if not target_player_id:
                raise ServiceError(ErrorCode.INVALID_ACTION, "objetivo inválido")

            target = await repo.get_player(self.db, target_player_id)
            if (
                target is None or target["game_id"] != game_id
                or target["role"] not in PLAYING_ROLES or target["eliminated"]
            ):
                raise ServiceError(ErrorCode.INVALID_ACTION, "objetivo inválido")
            if target_player_id == player_id:
                raise ServiceError(ErrorCode.INVALID_ACTION, "no podés atacarte a vos mismo")

            max_att = min(src_terr.armies - 1, eng.MAX_ATTACK_DICE) if src_terr else eng.MAX_ATTACK_DICE
            actual_att_dice = min(int(attacker_dice_count), max_att)
            if actual_att_dice < 1:
                actual_att_dice = 1

            try:
                attacker_dice = eng.roll_dice(actual_att_dice)
            except (EngineError, ValueError) as exc:
                raise ServiceError(ErrorCode.INVALID_PAYLOAD, str(exc)) from exc

            def_dice_count = min(tgt_terr.armies, eng.MAX_DEFENSE_DICE) if tgt_terr else eng.MAX_DEFENSE_DICE
            if def_dice_count < 1:
                def_dice_count = 1
            defender_dice = eng.roll_dice(def_dice_count)

            # atacar a un aliado rompe el pacto: TRAICIÓN pública
            if engine.has_pact(player_id, target_player_id):
                engine.break_pact(player_id, target_player_id)
                await self.emit(
                    game_id, EventType.PACT_BROKEN, actor_id=player_id,
                    target_id=target_player_id,
                    payload={"betrayal": True},
                )

            await self.emit(
                game_id, EventType.ATTACK_STARTED, actor_id=player_id,
                target_id=target_player_id,
                payload={"attacker_dice_count": len(attacker_dice)},
            )

            result = eng.resolve_combat(attacker_dice, defender_dice)
            # la Arena de Combate reconstruye la batalla completa con estos
            # datos: territorios, tropas antes/después y desglose de parejas
            payload = {
                "attacker_dice": result.attacker_dice,
                "defender_dice": result.defender_dice,
                "attacker_losses": result.attacker_losses,
                "defender_losses": result.defender_losses,
                "comparisons": result.comparisons,
                "source_territory_id": src_terr.territory_id if src_terr else None,
                "target_territory_id": tgt_terr.territory_id if tgt_terr else None,
                "attacker_armies_before": src_terr.armies if src_terr else None,
                "defender_armies_before": tgt_terr.armies if tgt_terr else None,
                "attacker_armies_after": (src_terr.armies - result.attacker_losses) if src_terr else None,
                "defender_armies_after": (tgt_terr.armies - result.defender_losses) if tgt_terr else None,
            }
            await self.emit(
                game_id, EventType.ATTACK_RESOLVED, actor_id=player_id,
                target_id=target_player_id, payload=payload,
            )

            if src_terr and tgt_terr:
                src_terr.armies -= result.attacker_losses
                tgt_terr.armies -= result.defender_losses

                if tgt_terr.armies <= 0:
                    old_owner = tgt_terr.owner_player_id
                    tgt_terr.owner_player_id = player_id
                    moved = min(actual_att_dice, src_terr.armies - 1)
                    if moved < 1:
                        moved = 1
                    src_terr.armies -= moved
                    tgt_terr.armies = moved
                    engine.register_conquest(player_id)

                    await self.emit(
                        game_id, EventType.TERRITORY_CONQUERED, actor_id=player_id,
                        target_id=old_owner,
                        payload={
                            "territory": tgt_terr.to_dict(),
                            "source_territory": src_terr.to_dict(),
                            "conquered_by": player_id,
                            "previous_owner": old_owner,
                        },
                    )

                    if old_owner:
                        remaining_owner_terr = [t for t in engine.territories.values() if t.owner_player_id == old_owner]
                        if not remaining_owner_terr:
                            await repo.update_player(self.db, old_owner, eliminated=True)
                            engine.remove_player(old_owner)
                            inherited = engine.register_elimination(old_owner, player_id)
                            await self.emit(
                                game_id, EventType.PLAYER_ELIMINATED, actor_id=player_id,
                                target_id=old_owner,
                                payload={"player_id": old_owner, "eliminated_by": player_id},
                            )
                            if inherited:
                                await self._emit_hand(game_id, engine, player_id)

                    player_terrs = [t for t in engine.territories.values() if t.owner_player_id == player_id]
                    if len(player_terrs) == len(engine.territories) and len(engine.territories) > 0:
                        await self.finish_game(game_id, winner_player_id=player_id)
                    else:
                        winner = engine.check_victory()
                        if winner is not None:
                            win_pid, win_obj = winner
                            await self._save_engine(game_id)
                            await self.finish_game(
                                game_id, winner_player_id=win_pid,
                                winning_objective=win_obj.public_view(),
                            )

                await self._save_engine(game_id)
                await self.emit(
                    game_id, EventType.TERRITORY_UPDATED, actor_id=player_id,
                    payload={"territory": src_terr.to_dict(), "target_territory": tgt_terr.to_dict()},
                )

            return payload

    async def place_initial(
        self, game_id: str, player_id: str, territory_id: str, count: int = 1
    ) -> dict:
        async with self.lock(game_id):
            game = await self.get_game_or_404(game_id)
            if game["status"] != GameStatus.RUNNING:
                raise ServiceError(ErrorCode.GAME_NOT_RUNNING, "la partida no está en curso")
            engine = await self._engine(game)
            try:
                result = engine.place_initial(player_id, territory_id, int(count))
            except EngineError as exc:
                raise ServiceError(ErrorCode.INVALID_ACTION, str(exc)) from exc
            await self._save_engine(game_id)
            await self.emit(
                game_id, EventType.PLACEMENT_UPDATED, target_id=player_id,
                visibility=Visibility.PRIVATE,
                payload={"remaining": result["remaining"],
                         "pending": engine.placement_pending.get(player_id, {})},
                persisted=False,
            )
            if result["remaining"] == 0:
                await self.emit(
                    game_id, EventType.PLACEMENT_PROGRESS, actor_id=player_id,
                    payload={"player_id": player_id, "done": True},
                )
            revealed = result["revealed"]
            if revealed:
                await self.emit(game_id, EventType.PLACEMENT_REVEALED, payload=revealed)
                if revealed["next_stage"] == "turns":
                    await self._save_engine(game_id)
                    await self._start_turn(
                        game_id, engine.turn.current_player_id, engine.turn.turn_number
                    )
                else:
                    self._schedule_ai_placements(game_id)
            return result

    async def trade_cards(self, game_id: str, player_id: str, card_ids: list[str]) -> dict:
        async with self.lock(game_id):
            engine = await self._require_running_turn(game_id, player_id)
            try:
                result = engine.trade_cards(player_id, [str(c) for c in card_ids])
            except EngineError as exc:
                raise ServiceError(ErrorCode.INVALID_ACTION, str(exc)) from exc
            await self._save_engine(game_id)
            await self.emit(
                game_id, EventType.CARDS_TRADED, actor_id=player_id,
                payload={"value": result["value"],
                         "cards": result["cards"],
                         "country_bonuses": result["country_bonuses"],
                         "turn": engine.turn.to_dict()},
            )
            await self._emit_hand(game_id, engine, player_id)
            return result

    async def _emit_hand(self, game_id: str, engine: GameEngine, player_id: str) -> None:
        await self.emit(
            game_id, EventType.CARDS_HAND, target_id=player_id,
            visibility=Visibility.PRIVATE,
            payload={"your_cards": [c.to_dict()
                                    for c in engine.cards.hands.get(player_id, [])]},
            persisted=False,
        )

    async def place_reinforcement(self, game_id: str, player_id: str, territory_id: str, count: int = 1) -> dict:
        async with self.lock(game_id):
            engine = await self._require_running_turn(game_id, player_id)
            try:
                terr = engine.place_reinforcement(player_id, territory_id, count)
            except EngineError as exc:
                raise ServiceError(ErrorCode.INVALID_ACTION, str(exc)) from exc
            await self._save_engine(game_id)
            await self.emit(
                game_id, EventType.TERRITORY_UPDATED, actor_id=player_id,
                payload={"territory": terr.to_dict(), "turn": engine.turn.to_dict()},
            )
            return terr.to_dict()

    async def fortify(
        self, game_id: str, player_id: str, source_id: str, target_id: str, count: int
    ) -> dict:
        async with self.lock(game_id):
            engine = await self._require_running_turn(game_id, player_id)
            try:
                src, tgt = engine.fortify(player_id, source_id, target_id, count)
            except EngineError as exc:
                raise ServiceError(ErrorCode.INVALID_ACTION, str(exc)) from exc
            await self._save_engine(game_id)
            await self.emit(
                game_id, EventType.TERRITORY_UPDATED, actor_id=player_id,
                payload={"territory": src.to_dict(), "target_territory": tgt.to_dict()},
            )
            return {"source": src.to_dict(), "target": tgt.to_dict()}

    async def _award_card_on_turn_close(self, game_id: str, engine: GameEngine, player_id: str) -> None:
        card = engine.award_card_if_due(player_id)
        if card is not None:
            await self.emit(
                game_id, EventType.CARD_AWARDED, actor_id=player_id,
                payload={"player_id": player_id},
            )
            await self._emit_hand(game_id, engine, player_id)

    async def set_wager(self, game_id: str, player_id: str, amount: int) -> dict:
        async with self.lock(game_id):
            engine = await self._require_running_turn(game_id, player_id)
            try:
                turn = engine.set_wager(player_id, int(amount))
            except EngineError as exc:
                raise ServiceError(ErrorCode.INVALID_ACTION, str(exc)) from exc
            await self._save_engine(game_id)
            await self.emit(
                game_id, EventType.WAGER_PLACED, actor_id=player_id,
                payload={"turn": turn.to_dict(), "wager": turn.wager},
            )
            return turn.to_dict()

    async def _resolve_wager_on_turn_close(self, game_id: str, engine, player_id: str) -> None:
        """Resuelve la apuesta ANTES de otorgar la tarjeta (que resetea la
        marca de conquista). Emite el resultado para el toast del cliente."""
        result = engine.resolve_wager(player_id)
        if result is not None:
            await self.emit(
                game_id, EventType.WAGER_RESOLVED, actor_id=player_id, payload=result,
            )

    async def next_phase(self, game_id: str, player_id: str) -> dict:
        async with self.lock(game_id):
            engine = await self._require_running_turn(game_id, player_id)
            old_index = engine.turn.index
            if engine.turn.phase == "fortify":
                # cerrar el turno: primero la apuesta, después la tarjeta
                await self._resolve_wager_on_turn_close(game_id, engine, player_id)
                await self._award_card_on_turn_close(game_id, engine, player_id)
            turn = engine.next_phase(player_id)
            await self._save_engine(game_id)
            if turn.index != old_index:
                await self.emit(game_id, EventType.TURN_ENDED, actor_id=player_id, payload={})
                await self._start_turn(game_id, turn.current_player_id, turn.turn_number)
            else:
                await self.emit(
                    game_id, EventType.TURN_STARTED, actor_id=player_id,
                    payload={"turn_number": turn.turn_number, "phase": turn.phase},
                )
            return turn.to_dict()

    async def _cerrar_y_avanzar_turno(
        self, game_id: str, engine: GameEngine, player_id: str
    ) -> TurnState:
        """Núcleo compartido de fin de turno.

        Asume que el lock de la partida YA está tomado por quien llama. Está
        factorizado así para que el timeout de ausencia pueda revalidar
        presencia y turn_number bajo el MISMO lock que hace el avance de
        turno, sin soltarlo en el medio: si no, queda una ventana entre
        "está ausente" y "le sacamos el turno" en la que puede reconectar y
        perder el turno igual.
        """
        await self._resolve_wager_on_turn_close(game_id, engine, player_id)
        await self._award_card_on_turn_close(game_id, engine, player_id)
        await self.emit(game_id, EventType.TURN_ENDED, actor_id=player_id, payload={})
        turn = engine.advance_turn()
        await self._save_engine(game_id)
        return turn

    async def end_turn(self, game_id: str, player_id: str) -> None:
        async with self.lock(game_id):
            engine = await self._require_running_turn(game_id, player_id)
            turn = await self._cerrar_y_avanzar_turno(game_id, engine, player_id)
        await self._start_turn(game_id, turn.current_player_id, turn.turn_number)

    # --- jugador IA ---------------------------------------------------------

    def _schedule_ai_placements(self, game_id: str) -> None:
        self._crear_tarea_de_fondo(self._ai_placements(game_id))

    async def _ai_placements(self, game_id: str) -> None:
        """Los bots colocan su pool inicial apenas arranca cada ronda."""
        try:
            await asyncio.sleep(self.settings.ai_player_think_seconds)
            game = await repo.get_game(self.db, game_id)
            if game is None or game["status"] != GameStatus.RUNNING:
                return
            players = await repo.get_players(self.db, game_id)
            ai_ids = {p["id"] for p in players if p["role"] == Role.AI_PLAYER}
            engine = await self._engine(game)
            for pid in list(engine.placement_pools):
                if pid not in ai_ids:
                    continue
                while engine.placement_pools.get(pid, 0) > 0:
                    tid = bot.choose_placement(engine, pid)
                    await self.place_initial(game_id, pid, tid, 1)
        except ServiceError as exc:
            log.info("colocación IA rechazada", extra={"ctx": {"code": exc.code}})
        except Exception:
            log.warning("fallo en colocación IA", exc_info=True)

    def _schedule_ai_turn(self, game_id: str, player_id: str) -> None:
        key = f"{game_id}:{player_id}"
        old = self._ai_tasks.get(key)

        async def _run() -> None:
            # si el turno volvió al bot mientras su tarea anterior terminaba,
            # esperarla y jugar igual: descartar la jugada trababa la partida
            if old is not None and not old.done():
                try:
                    await old
                except Exception:
                    pass
            await self._ai_turn(game_id, player_id)

        tarea = self._crear_tarea_de_fondo(_run())
        if tarea is not None:
            self._ai_tasks[key] = tarea

    async def _ai_turn(self, game_id: str, player_id: str) -> None:
        """El bot juega el turno completo: canje, refuerzos, ataques y fortify.

        Ante cualquier rechazo o error, cierra el turno: nunca traba la partida.
        """
        try:
            await asyncio.sleep(self.settings.ai_player_think_seconds)
            game = await repo.get_game(self.db, game_id)
            if game is None or game["status"] != GameStatus.RUNNING:
                return
            engine = await self._engine(game)
            if engine.turn.current_player_id != player_id or engine.stage != "turns":
                return

            # 1. canje: siempre que haya trío (más ejércitos = mejor)
            trio = _first_valid_trio(engine.cards.hands.get(player_id, []))
            if trio and engine.turn.phase == "reinforcement":
                await self.trade_cards(game_id, player_id, trio)

            # 2. refuerzos a la frontera más caliente (sesgo al objetivo)
            while (
                engine.turn.current_player_id == player_id
                and engine.turn.phase == "reinforcement"
                and engine.turn.reinforcements_available > 0
            ):
                tid = bot.choose_reinforcement(engine, player_id)
                await self.place_reinforcement(
                    game_id, player_id, tid, engine.turn.reinforcements_available
                )

            # 3. ataques con ventaja (tope defensivo de 15 por turno)
            attacks = 0
            while attacks < 15 and engine.turn.current_player_id == player_id:
                game = await repo.get_game(self.db, game_id)
                if game is None or game["status"] != GameStatus.RUNNING:
                    return
                if engine.turn.phase != "attack":
                    break
                pick = bot.choose_attack(engine, player_id)
                if pick is None:
                    break
                src, tgt = pick
                await asyncio.sleep(self.settings.ai_player_think_seconds)
                await self.attack(
                    game_id, player_id,
                    source_territory_id=src, target_territory_id=tgt,
                    attacker_dice_count=3,
                )
                attacks += 1

            # la partida pudo terminar con el último ataque
            game = await repo.get_game(self.db, game_id)
            if game is None or game["status"] != GameStatus.RUNNING:
                return
            if engine.turn.current_player_id != player_id:
                return

            # 4. reagrupar tropas ociosas hacia la frontera
            if engine.turn.phase in ("reinforcement", "attack"):
                move = bot.choose_fortify(engine, player_id)
                if move is not None:
                    if engine.turn.phase == "reinforcement":
                        await self.next_phase(game_id, player_id)  # → attack
                    await self.next_phase(game_id, player_id)      # → fortify
                    src, tgt, count = move
                    await self.fortify(game_id, player_id, src, tgt, count)

            # 5. fin de turno (otorga tarjeta si conquistó)
            if engine.turn.current_player_id == player_id:
                await self.end_turn(game_id, player_id)
        except ServiceError as exc:
            log.info("jugada IA rechazada", extra={"ctx": {"code": exc.code}})
            await self._ai_close_turn(game_id, player_id)
        except Exception:
            log.warning("fallo en turno IA", exc_info=True)
            await self._ai_close_turn(game_id, player_id)

    async def _ai_close_turn(self, game_id: str, player_id: str) -> None:
        """Pase lo que pase, el bot suelta el turno: la partida jamás se traba."""
        try:
            game = await repo.get_game(self.db, game_id)
            if game is None or game["status"] != GameStatus.RUNNING:
                return
            engine = await self._engine(game)
            if engine.stage == "turns" and engine.turn.current_player_id == player_id:
                await self.end_turn(game_id, player_id)
        except Exception:
            log.warning("la IA no pudo cerrar su turno", exc_info=True)

    def _cancelar_tarea_ia(self, game_id: str, player_id: str) -> None:
        tarea = self._ai_tasks.pop(f"{game_id}:{player_id}", None)
        if tarea and not tarea.done():
            tarea.cancel()

    async def _restaurar_asiento_humano(self, game: dict, player: dict) -> None:
        """Inversa exacta de convert_seat_to_ai: el humano vuelve y recupera
        su asiento. Si la partida esta en curso y el turno es de ese asiento,
        hay que desagendar al bot y devolverle el reloj al humano; si no, el
        bot sigue jugando el turno de alguien que ya volvio."""
        game_id = game["id"]
        await repo.update_player(self.db, player["id"], role=Role.PLAYER)
        player["role"] = Role.PLAYER
        await self.emit(
            game_id, EventType.PLAYER_JOINED, actor_id=player["id"],
            payload={"player": repo.public_player(player)},
        )
        if game["status"] != GameStatus.RUNNING:
            return
        engine = await self._engine(game)
        if engine.stage == "turns" and engine.turn.current_player_id == player["id"]:
            self._cancelar_tarea_ia(game_id, player["id"])
            self._armar_timeout_de_turno(game_id, player["id"], engine.turn.turn_number)

    async def convert_seat_to_ai(self, game_id: str, player_id: str) -> None:
        """El admin convierte el asiento de un ausente en bot; su link sigue
        siendo válido y al volver a entrar recupera el asiento."""
        game = await self.get_game_or_404(game_id)
        player = await repo.get_player(self.db, player_id)
        if player is None or player["game_id"] != game_id:
            raise ServiceError(ErrorCode.NOT_FOUND, "jugador inexistente")
        if player["role"] != Role.PLAYER:
            raise ServiceError(ErrorCode.INVALID_ACTION, "solo un jugador humano se convierte en IA")
        await repo.update_player(self.db, player_id, role=Role.AI_PLAYER)
        await self.emit(
            game_id, EventType.PLAYER_JOINED, actor_id=player_id,
            payload={"player": repo.public_player(
                {**player, "role": Role.AI_PLAYER})},
        )
        engine = await self._engine(game)
        if game["status"] == GameStatus.RUNNING and engine.turn.current_player_id == player_id:
            # el asiento ya no es humano: el timeout de ausencia no aplica,
            # el bot tiene su propio agendado
            self._cancelar_timeout_de_turno(game_id)
            self._schedule_ai_turn(game_id, player_id)

    async def rehidratar_partidas_activas(self) -> int:
        """Reagenda los turnos de bot y los relojes de turno humanos al
        levantar el proceso.

        _ai_tasks y _turn_timers son memoria pura y el lifespan no recorria
        nada al arrancar: un reinicio durante el turno de un bot dejaba la
        partida trabada para siempre, y un reinicio durante el turno de un
        humano dejaba apagada la proteccion contra ausencias
        (_armar_timeout_de_turno solo se llama desde _start_turn y
        resume_game, y ninguno corre al levantar el proceso). Reiniciar es el
        flujo NORMAL de este proyecto -- el tunel es efimero y hay que
        regenerar los links en cada sesion -- asi que era el escenario mas
        comun, no un borde.

        Solo aplica a la fase de turnos ("stage" == "turns"); la colocación
        inicial ya se reintenta sola vía otros mecanismos y no es un "turno"
        en este sentido.

        Nunca debe impedir que el backend arranque: cualquier partida
        corrupta se loguea y se salta; si falla el listado entero, se loguea
        y se devuelve 0.
        """
        reagendados = 0
        relojes = 0
        try:
            partidas = await repo.list_games_by_status(self.db, GameStatus.RUNNING)
        except Exception:
            log.warning("no se pudieron listar las partidas activas", exc_info=True)
            return 0
        for game in partidas:
            try:
                engine = await self._engine(game)
                if engine.stage != "turns":
                    continue
                actual = engine.turn.current_player_id
                if actual is None:
                    continue
                player = await repo.get_player(self.db, actual)
                if player and player["role"] == Role.AI_PLAYER:
                    self._schedule_ai_turn(game["id"], actual)
                    reagendados += 1
                elif player:
                    self._armar_timeout_de_turno(
                        game["id"], actual, engine.turn.turn_number
                    )
                    relojes += 1
            except Exception:
                log.warning(
                    "fallo rehidratando una partida", exc_info=True,
                    extra={"ctx": {"game_id": game.get("id")}},
                )
        self.counters["ai_turns_rehydrated"] = reagendados
        self.counters["turn_timers_rehydrated"] = relojes
        return reagendados

    # --- métricas -----------------------------------------------------------

    def metrics(self) -> dict:
        return {
            "games_created": self.counters["games_created"],
            "events_emitted": self.counters["events_emitted"],
            "active_connections": self.manager.connection_count(),
            "rooms": len(self.manager.rooms),
        }
