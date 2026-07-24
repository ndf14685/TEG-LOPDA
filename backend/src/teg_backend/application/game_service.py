"""Orquestador central: única fuente de verdad de partidas y eventos.

Todo lo que cambia estado pasa por acá: valida, aplica en el dominio,
persiste, emite eventos y notifica a comentarista/taunts/IA.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from ..ai.ai_player import MoveRequest, build_ai_player, request_move
from ..ai.commentator import Comment, CommentatorService
from ..config import Settings
from ..domain import engine as eng
from ..domain.engine import EngineError, GameEngine
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
TAUNTABLE_EVENTS = {
    EventType.ATTACK_RESOLVED, EventType.TERRITORY_CONQUERED, EventType.PLAYER_ELIMINATED,
}


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
        self._ai_provider = build_ai_player("random")
        self._ai_tasks: dict[str, asyncio.Task] = {}
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
                await repo.append_event(self.db, event.model_dump(mode="json"))
        self.counters["events_emitted"] += 1
        roles = await self._roles_map(game_id)
        await self.manager.broadcast(game_id, event, roles)
        if persisted:
            await self._after_emit(game_id, event)
        return event

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
                asset_id = await repo.find_taunt(
                    self.db, game_id, event.actor_id, event.target_id, event.event_type
                )
                if asset_id:
                    await self.emit(
                        game_id,
                        EventType.TAUNT_TRIGGERED,
                        actor_id=event.actor_id,
                        target_id=event.target_id,
                        payload={
                            "audio_asset_id": asset_id,
                            "source_event_type": event.event_type,
                            "source_event_id": event.event_id,
                        },
                    )
        except Exception:
            log.warning("fallo en efectos post-evento", exc_info=True)

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
    ) -> dict:
        game = await self.get_game_or_404(game_id)
        if game["status"] not in ACTIVE_STATUSES:
            raise ServiceError(ErrorCode.GAME_STATE_CONFLICT, "la partida no admite invitaciones")
        if role not in (Role.ADMIN, Role.PLAYER, Role.SPECTATOR, Role.AI_PLAYER):
            raise ServiceError(ErrorCode.INVALID_PAYLOAD, f"rol inválido: {role}")
        nickname = sanitize_nickname(nickname)
        if not nickname:
            raise ServiceError(ErrorCode.INVALID_PAYLOAD, "apodo vacío")
        editable = (
            nickname_editable
            if nickname_editable is not None
            else bool(game["config"].get("nickname_editable_default", True))
        )
        token: str | None = None
        token_hash: str | None = None
        if role != Role.AI_PLAYER:
            token = tok.new_player_token()
            token_hash = tok.hash_token(token)
        player = await repo.create_player(
            self.db, game_id, nickname, role, token_hash, color, editable
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

    async def _start_turn(self, game_id: str, player_id: str | None, turn_number: int) -> None:
        if player_id is None:
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
            self._schedule_ai_turn(game_id, player_id)

    async def pause_game(self, game_id: str) -> None:
        game = await self.get_game_or_404(game_id)
        if game["status"] != GameStatus.RUNNING:
            raise ServiceError(ErrorCode.GAME_STATE_CONFLICT, "solo se pausa una partida en curso")
        await self._set_status(game_id, GameStatus.PAUSED)
        await self.emit(game_id, EventType.GAME_PAUSED)

    async def resume_game(self, game_id: str) -> None:
        game = await self.get_game_or_404(game_id)
        if game["status"] != GameStatus.PAUSED:
            raise ServiceError(ErrorCode.GAME_STATE_CONFLICT, "la partida no está pausada")
        await self._set_status(game_id, GameStatus.RUNNING)
        await self.emit(game_id, EventType.GAME_RESUMED)

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
        await self._set_status(game_id, GameStatus.FINISHED)
        await self.emit(game_id, EventType.GAME_FINISHED, target_id=winner_player_id, payload=summary)
        return summary

    async def cancel_game(self, game_id: str) -> None:
        game = await self.get_game_or_404(game_id)
        if game["status"] in (GameStatus.FINISHED, GameStatus.CANCELLED):
            raise ServiceError(ErrorCode.GAME_STATE_CONFLICT, "la partida ya terminó")
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
        if game["status"] not in ACTIVE_STATUSES:
            raise ServiceError(ErrorCode.GAME_STATE_CONFLICT, "la partida no admite ingresos")
        if nickname and player["nickname_editable"]:
            clean = sanitize_nickname(nickname)
            if clean:
                await repo.update_player(self.db, player["id"], nickname=clean)
                player["nickname"] = clean
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
            "turn": (
                engine.turn.to_dict()
                if game["status"] in (GameStatus.RUNNING, GameStatus.PAUSED)
                and engine.stage == "turns"
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
        room._offline_tasks[player_id] = asyncio.create_task(_grace())

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

            await self.emit(
                game_id, EventType.ATTACK_STARTED, actor_id=player_id,
                target_id=target_player_id,
                payload={"attacker_dice_count": len(attacker_dice)},
            )

            result = eng.resolve_combat(attacker_dice, defender_dice)
            payload = {
                "attacker_dice": result.attacker_dice,
                "defender_dice": result.defender_dice,
                "attacker_losses": result.attacker_losses,
                "defender_losses": result.defender_losses,
                "comparisons": result.comparisons,
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

    async def next_phase(self, game_id: str, player_id: str) -> dict:
        async with self.lock(game_id):
            engine = await self._require_running_turn(game_id, player_id)
            old_index = engine.turn.index
            if engine.turn.phase == "fortify":
                # cerrar el turno otorga la tarjeta por conquista si corresponde
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

    async def end_turn(self, game_id: str, player_id: str) -> None:
        async with self.lock(game_id):
            engine = await self._require_running_turn(game_id, player_id)
            await self._award_card_on_turn_close(game_id, engine, player_id)
            await self.emit(game_id, EventType.TURN_ENDED, actor_id=player_id, payload={})
            turn = engine.advance_turn()
            await self._save_engine(game_id)
        await self._start_turn(game_id, turn.current_player_id, turn.turn_number)

    # --- jugador IA ---------------------------------------------------------

    def _schedule_ai_placements(self, game_id: str) -> None:
        asyncio.create_task(self._ai_placements(game_id))

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
                    own = [t.territory_id for t in engine.territories.values()
                           if t.owner_player_id == pid]
                    tid = eng._rng.choice(own)
                    await self.place_initial(game_id, pid, tid, 1)
        except ServiceError as exc:
            log.info("colocación IA rechazada", extra={"ctx": {"code": exc.code}})
        except Exception:
            log.warning("fallo en colocación IA", exc_info=True)

    def _schedule_ai_turn(self, game_id: str, player_id: str) -> None:
        key = f"{game_id}:{player_id}"
        old = self._ai_tasks.get(key)
        if old and not old.done():
            return
        self._ai_tasks[key] = asyncio.create_task(self._ai_turn(game_id, player_id))

    async def _ai_turn(self, game_id: str, player_id: str) -> None:
        try:
            await asyncio.sleep(self.settings.ai_player_think_seconds)
            game = await repo.get_game(self.db, game_id)
            if game is None or game["status"] != GameStatus.RUNNING:
                return
            engine = await self._engine(game)
            if engine.turn.current_player_id != player_id:
                return
            # canje forzado y refuerzos: la IA nunca deja el turno trabado
            hand = engine.cards.hands.get(player_id, [])
            if len(hand) >= 5:
                trio = _first_valid_trio(hand)
                if trio:
                    await self.trade_cards(game_id, player_id, trio)
            engine = await self._engine(game)
            while (
                engine.turn.current_player_id == player_id
                and engine.turn.phase == "reinforcement"
                and engine.turn.reinforcements_available > 0
            ):
                own = [t.territory_id for t in engine.territories.values()
                       if t.owner_player_id == player_id]
                await self.place_reinforcement(
                    game_id, player_id, eng._rng.choice(own),
                    engine.turn.reinforcements_available,
                )
            legal = [
                {"action": "dice.roll", "payload": {"count": 3}},
                {"action": "turn.end", "payload": {}},
            ]
            request = MoveRequest(
                game_id=game_id, player_id=player_id,
                snapshot={"turn": engine.turn.to_dict(), "status": game["status"]},
                legal_actions=legal,
            )
            move = await request_move(
                self._ai_provider, request, self.settings.ai_player_timeout_seconds
            )
            if move.action == "dice.roll":
                await self.roll_dice(game_id, player_id, int(move.payload.get("count", 1)))
            # tras la jugada (o directamente), la IA cierra su turno
            await self.end_turn(game_id, player_id)
        except ServiceError as exc:
            log.info("jugada IA rechazada", extra={"ctx": {"code": exc.code}})
        except Exception:
            log.warning("fallo en turno IA", exc_info=True)

    # --- métricas -----------------------------------------------------------

    def metrics(self) -> dict:
        return {
            "games_created": self.counters["games_created"],
            "events_emitted": self.counters["events_emitted"],
            "active_connections": self.manager.connection_count(),
            "rooms": len(self.manager.rooms),
        }
