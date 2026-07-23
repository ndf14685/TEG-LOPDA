"""Comentarista IA desacoplado del motor.

Contrato: shared/contracts/schemas/ai-commentator-io.schema.json
- Recibe un contexto estructurado (nunca acceso libre a la aplicación).
- Corre asíncrono en su propio worker; si falla, el juego sigue.
- Cooldown, límite de longitud, niveles 0-4 (4 deshabilitado por defecto,
  ver Settings.humor_level_max).
"""

from __future__ import annotations

import asyncio
import logging
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Protocol

log = logging.getLogger("teg.ai.commentator")

# Eventos que ameritan comentario (el resto se ignora).
INTERESTING_EVENTS = {
    "game.started", "dice.rolled", "attack.resolved", "territory.conquered",
    "player.eliminated", "player.joined", "game.finished", "turn.started",
}


@dataclass(slots=True)
class CommentRequest:
    game_id: str
    event: dict[str, Any]
    recent_events: list[dict[str, Any]]
    players: list[dict[str, Any]]
    humor_level: int
    relationship_context: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Comment:
    text: str
    target_player_id: str | None = None
    visibility: str = "public"
    emotion: str = "neutral"
    audio_asset: str | None = None


class AICommentatorProvider(Protocol):
    name: str

    async def generate(self, request: CommentRequest) -> Comment | None: ...


def _nickname(players: list[dict], player_id: str | None) -> str:
    for p in players:
        if p["id"] == player_id:
            return p["nickname"]
    return "alguien"


class MockCommentator:
    """Determinista, para tests y para jugar sin modelo. Rota plantillas para
    no repetir siempre la misma frase y recuerda rachas por partida."""

    name = "mock"

    TEMPLATES: dict[str, dict[int, list[str]]] = {
        "game.started": {
            1: ["Comienza la partida. {n} jugadores en el tablero."],
            2: ["Arranca la partida. {n} valientes, un solo ganador.",
                "Se abre el telón: {n} jugadores y cero piedad."],
            3: ["{n} jugadores entran. Las amistades quedan suspendidas hasta nuevo aviso.",
                "Empieza el TEG: {n} estrategas, aunque alguno todavía no lo sabe."],
        },
        "dice.rolled": {
            1: ["{actor} tiró {dice}."],
            2: ["{actor} tiró {dice}. Los dados no mienten.",
                "{actor} sacó {dice}. Interesante elección del azar."],
            3: ["{actor} sacó {dice}. La estrategia todavía no fue localizada.",
                "{actor} tiró {dice}. El casino agradece su visita."],
        },
        "attack.resolved": {
            1: ["Ataque resuelto: atacante pierde {al}, defensor pierde {dl}."],
            2: ["{actor} atacó a {target}: {al} bajas propias, {dl} ajenas.",
                "Combate cerrado entre {actor} y {target}: {al} a {dl}."],
            3: ["{actor} atacó a {target} y perdió {al} ejércitos. Plan sólido.",
                "{actor} vs {target}: el defensor descorcha, {al} bajas atacantes."],
        },
        "territory.conquered": {
            1: ["{actor} conquistó un territorio de {target}."],
            2: ["{actor} le sacó un territorio a {target}. Duele.",
                "Nuevo dueño: {actor} se queda con tierra de {target}."],
            3: ["{actor} conquistó territorio de {target}, que ya mira el mapa con nostalgia.",
                "{actor} avanza y {target} redecora su imperio... más chico."],
        },
        "player.eliminated": {
            1: ["{target} fue eliminado de la partida."],
            2: ["{target} pasa a ser espectador profesional."],
            3: ["{target} eliminado. Dicen que ya está culpando a los dados."],
        },
        "player.joined": {
            1: ["{actor} entró a la sala."],
            2: ["{actor} llegó. Que empiece el show."],
            3: ["{actor} entró a la sala. Bajen las expectativas."],
        },
        "game.finished": {
            1: ["La partida terminó."],
            2: ["Fin de la partida. Hubo estrategia, hubo suerte, hubo de todo."],
            3: ["Se terminó. Los perdedores ya están pidiendo la revancha."],
        },
    }
    # TODO(humor-4): frases nivel 4 (bardeo entre amigos) se definen con el
    # grupo; deshabilitado por defecto vía humor_level_max.

    def __init__(self) -> None:
        self._rotation: dict[str, int] = {}
        self._streaks: dict[str, dict[str, int]] = {}

    def _pick(self, event_type: str, level: int, key: str) -> str | None:
        by_level = self.TEMPLATES.get(event_type)
        if not by_level:
            return None
        for lvl in range(min(level, 3), 0, -1):
            options = by_level.get(lvl)
            if options:
                idx = self._rotation.get(key, 0)
                self._rotation[key] = idx + 1
                return options[idx % len(options)]
        return None

    async def generate(self, request: CommentRequest) -> Comment | None:
        if request.humor_level <= 0:
            return None
        ev = request.event
        etype = ev["event_type"]
        players = request.players
        actor = _nickname(players, ev.get("actor_id"))
        target = _nickname(players, ev.get("target_id"))
        payload = ev.get("payload", {})
        emotion = "neutral"
        extra = ""

        # memoria simple: rachas de tiradas malas por jugador
        if etype == "dice.rolled" and ev.get("actor_id"):
            dice = payload.get("dice", [])
            streaks = self._streaks.setdefault(request.game_id, {})
            if dice and max(dice) <= 2:
                streaks[ev["actor_id"]] = streaks.get(ev["actor_id"], 0) + 1
                if streaks[ev["actor_id"]] >= 2 and request.humor_level >= 2:
                    extra = f" Van {streaks[ev['actor_id']]} tiradas horribles seguidas."
                    emotion = "mocking"
            else:
                streaks[ev["actor_id"]] = 0

        template = self._pick(etype, request.humor_level, f"{request.game_id}:{etype}")
        if template is None:
            return None
        if etype == "attack.resolved" and request.humor_level >= 3:
            emotion = "mocking"
        text = template.format(
            actor=actor,
            target=target,
            n=len([p for p in players if p["role"] in ("player", "ai_player")]),
            dice=payload.get("dice", ""),
            al=payload.get("attacker_losses", "?"),
            dl=payload.get("defender_losses", "?"),
        )
        return Comment(text=text + extra, emotion=emotion)


class OllamaCommentator:
    """Adaptador a un modelo local vía Ollama. Nunca bloquea: timeout corto y
    fallback silencioso (None) ante cualquier error."""

    name = "ollama"

    def __init__(self, base_url: str, model: str, timeout_seconds: float = 8.0) -> None:
        self.base_url = base_url
        self.model = model
        self.timeout = timeout_seconds

    async def generate(self, request: CommentRequest) -> Comment | None:
        import httpx

        ev = request.event
        players = {p["id"]: p["nickname"] for p in request.players}
        prompt = (
            "Sos un relator argentino de una partida de TEG entre amigos. "
            f"Nivel de humor {request.humor_level}/4 "
            "(1 neutral, 2 suave, 3 picante, 4 bardeo). "
            "Comentá en UNA sola frase corta, en castellano rioplatense, "
            "sin insultos discriminatorios, el siguiente evento:\n"
            f"Evento: {ev['event_type']}\n"
            f"Jugadores: {players}\n"
            f"Datos: actor={ev.get('actor_id')}, target={ev.get('target_id')}, "
            f"payload={ev.get('payload')}\n"
            f"Últimos eventos: {[e['event_type'] for e in request.recent_events[-5:]]}\n"
        )
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    f"{self.base_url}/api/generate",
                    json={"model": self.model, "prompt": prompt, "stream": False},
                )
                resp.raise_for_status()
                text = (resp.json().get("response") or "").strip()
        except Exception:
            log.warning("ollama no disponible, se omite comentario", exc_info=True)
            return None
        if not text:
            return None
        return Comment(text=text.splitlines()[0], emotion="neutral")


def build_provider(name: str, *, ollama_url: str, ollama_model: str) -> AICommentatorProvider:
    if name == "ollama":
        return OllamaCommentator(ollama_url, ollama_model)
    # TODO(ai-providers): adaptador a CLI autenticado local (claude/codex) u
    # otro proveedor configurable, siempre opcional y sin API key obligatoria.
    return MockCommentator()


class CommentatorService:
    """Worker asíncrono con cola acotada y cooldown por partida."""

    def __init__(
        self,
        provider: AICommentatorProvider,
        *,
        enabled: bool,
        cooldown_seconds: float,
        max_chars: int,
        emit: Callable[[str, Comment], Awaitable[None]] | None = None,
    ) -> None:
        self.provider = provider
        self.enabled = enabled
        self.cooldown = cooldown_seconds
        self.max_chars = max_chars
        self.emit = emit  # lo inyecta GameService
        self._queue: asyncio.Queue[CommentRequest] = asyncio.Queue(maxsize=100)
        self._last_comment_at: dict[str, float] = {}
        self._recent: dict[str, deque] = {}
        self._task: asyncio.Task | None = None
        self._muted: set[str] = set()

    def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(self._worker(), name="commentator-worker")

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    def set_muted(self, game_id: str, muted: bool) -> None:
        (self._muted.add if muted else self._muted.discard)(game_id)

    def notify(
        self, game_id: str, event: dict, players: list[dict], humor_level: int
    ) -> None:
        """Llamado por el motor de eventos. Nunca bloquea ni lanza."""
        recent = self._recent.setdefault(game_id, deque(maxlen=20))
        recent.append(event)
        if not self.enabled or humor_level <= 0 or game_id in self._muted:
            return
        if event["event_type"] not in INTERESTING_EVENTS:
            return
        request = CommentRequest(
            game_id=game_id,
            event=event,
            recent_events=list(recent),
            players=players,
            humor_level=humor_level,
        )
        try:
            self._queue.put_nowait(request)
        except asyncio.QueueFull:
            log.debug("cola de comentarista llena, se descarta evento")

    async def _worker(self) -> None:
        loop = asyncio.get_running_loop()
        while True:
            request = await self._queue.get()
            try:
                now = loop.time()
                last = self._last_comment_at.get(request.game_id, -1e9)
                if now - last < self.cooldown:
                    continue
                comment = await asyncio.wait_for(
                    self.provider.generate(request), timeout=10.0
                )
                if comment is None or not comment.text.strip():
                    continue
                comment.text = comment.text.strip()[: self.max_chars]
                self._last_comment_at[request.game_id] = loop.time()
                if self.emit is not None:
                    await self.emit(request.game_id, comment)
            except asyncio.CancelledError:
                raise
            except Exception:
                # el comentarista jamás voltea el juego
                log.warning("fallo generando comentario", exc_info=True)
