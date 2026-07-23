"""Flujo de ingreso por link personalizado."""

from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from ..application.game_service import ServiceError
from .errors import to_http

router = APIRouter(prefix="/api/join", tags=["join"])


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
