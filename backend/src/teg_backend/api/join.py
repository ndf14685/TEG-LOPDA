"""Flujo de ingreso por link personalizado."""

from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from ..application.game_service import ServiceError
from .errors import to_http

router = APIRouter(prefix="/api/join", tags=["join"])
profile_router = APIRouter(prefix="/api/profile", tags=["profile"])


class ConfirmJoinBody(BaseModel):
    nickname: str | None = Field(default=None, max_length=64)


@router.get("/{code}/{token}")
async def resolve_join(code: str, token: str, request: Request) -> dict:
    service = request.app.state.service
    try:
        resolved = await service.resolve_join(code, token)
    except ServiceError as exc:
        raise to_http(exc)
    from ..infrastructure.repository import public_game

    game, player = resolved["game"], resolved["player"]
    return {
        "game": public_game(game),
        "player": {
            "id": player["id"],
            "nickname": player["nickname"],
            "role": player["role"],
            "color": player["color"],
            "nickname_editable": player["nickname_editable"],
            "already_joined": player["joined_at"] is not None,
        },
    }


@router.post("/{code}/{token}")
async def confirm_join(code: str, token: str, body: ConfirmJoinBody, request: Request) -> dict:
    service = request.app.state.service
    try:
        return await service.confirm_join(code, token, body.nickname)
    except ServiceError as exc:
        raise to_http(exc)


# --- link personal permanente de perfil ------------------------------------

@profile_router.get("/{token}")
async def resolve_profile(token: str, request: Request) -> dict:
    service = request.app.state.service
    try:
        return {"profile": await service.resolve_profile(token)}
    except ServiceError as exc:
        raise to_http(exc)


# --- replay paso a paso (solo participantes de la partida) -------------------

@router.get("/{code}/{token}/replay")
async def replay_index(code: str, token: str, request: Request) -> dict:
    """Índice del replay: turnos con snapshot disponible + jugadores."""
    service = request.app.state.service
    from ..infrastructure import repository as repo

    try:
        resolved = await service.resolve_join(code, token)
    except ServiceError as exc:
        raise to_http(exc)
    game = resolved["game"]
    players = await repo.get_players(service.db, game["id"])
    return {
        "game": repo.public_game(game),
        "players": [repo.public_player(p) for p in players],
        "turns": await repo.list_snapshot_turns(service.db, game["id"]),
    }


@router.get("/{code}/{token}/replay/{turn_number}")
async def replay_turn(code: str, token: str, turn_number: int, request: Request) -> dict:
    """Estado del mapa al inicio de ese turno + eventos públicos del turno."""
    service = request.app.state.service
    from ..infrastructure import repository as repo

    try:
        resolved = await service.resolve_join(code, token)
    except ServiceError as exc:
        raise to_http(exc)
    game = resolved["game"]
    state = await repo.get_turn_snapshot(service.db, game["id"], turn_number)
    if state is None:
        from fastapi import HTTPException

        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "turno sin snapshot"})

    # eventos del turno: entre este turn.started y el siguiente
    events = await repo.get_events(service.db, game["id"], limit=100000, public_only=True)
    start_seq, end_seq = None, None
    for ev in events:
        if ev["event_type"] == "turn.started" and ev["payload"].get("turn_number") == turn_number:
            if start_seq is None:
                start_seq = ev["sequence_number"]
        elif (
            start_seq is not None
            and ev["event_type"] == "turn.started"
            and ev["payload"].get("turn_number", 0) > turn_number
        ):
            end_seq = ev["sequence_number"]
            break
    turn_events = [
        ev for ev in events
        if start_seq is not None
        and ev["sequence_number"] >= start_seq
        and (end_seq is None or ev["sequence_number"] < end_seq)
    ]
    return {
        "turn_number": turn_number,
        "territories": state.get("territories", {}),
        "turn": state.get("turn", {}),
        "events": turn_events,
    }
