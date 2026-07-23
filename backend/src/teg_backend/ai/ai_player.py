"""Jugador IA: propone jugadas, nunca toca el estado.

Contrato: shared/contracts/schemas/ai-player-io.schema.json
El motor valida toda jugada propuesta; ante timeout o jugada inválida se
aplica el fallback seguro (terminar el turno).
"""

from __future__ import annotations

import asyncio
import logging
import secrets
from dataclasses import dataclass, field
from typing import Any, Protocol

log = logging.getLogger("teg.ai.player")

_rng = secrets.SystemRandom()

FALLBACK_ACTION = "turn.end"


@dataclass(slots=True)
class MoveRequest:
    game_id: str
    player_id: str
    snapshot: dict[str, Any]
    legal_actions: list[dict[str, Any]] = field(default_factory=list)


@dataclass(slots=True)
class ProposedMove:
    action: str
    payload: dict[str, Any] = field(default_factory=dict)


class AIPlayerProvider(Protocol):
    name: str

    async def propose(self, request: MoveRequest) -> ProposedMove: ...


class DummyAIPlayer:
    """Siempre pasa el turno. Útil para probar el flujo completo."""

    name = "dummy"

    async def propose(self, request: MoveRequest) -> ProposedMove:
        return ProposedMove(action=FALLBACK_ACTION)


class RandomLegalMoveAI:
    """Elige una jugada legal al azar de las que ofrece el motor."""

    name = "random"

    async def propose(self, request: MoveRequest) -> ProposedMove:
        if not request.legal_actions:
            return ProposedMove(action=FALLBACK_ACTION)
        choice = _rng.choice(request.legal_actions)
        return ProposedMove(action=choice["action"], payload=choice.get("payload", {}))


def build_ai_player(name: str) -> AIPlayerProvider:
    if name == "random":
        return RandomLegalMoveAI()
    return DummyAIPlayer()


async def request_move(
    provider: AIPlayerProvider,
    request: MoveRequest,
    timeout_seconds: float,
) -> ProposedMove:
    """Pide una jugada con timeout y valida contra las acciones legales.

    Cualquier problema (timeout, excepción, acción ilegal) => fallback.
    """
    legal = {a["action"] for a in request.legal_actions} | {FALLBACK_ACTION}
    try:
        move = await asyncio.wait_for(provider.propose(request), timeout=timeout_seconds)
    except Exception:
        log.warning("IA no respondió a tiempo, fallback a fin de turno")
        return ProposedMove(action=FALLBACK_ACTION)
    if move.action not in legal:
        log.warning(
            "IA propuso accion ilegal, fallback", extra={"ctx": {"action": move.action}}
        )
        return ProposedMove(action=FALLBACK_ACTION)
    return move
