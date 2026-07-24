"""API de administración. Autenticación por header X-Admin-Token."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field

from ..application.game_service import ServiceError
from ..infrastructure import repository as repo
from .errors import to_http


async def admin_auth(request: Request, x_admin_token: str = Header(default="")) -> None:
    from ..security.tokens import constant_time_equals

    settings = request.app.state.settings
    if not constant_time_equals(x_admin_token, settings.admin_token):
        raise HTTPException(status_code=401, detail={"code": "AUTH_FAILED", "message": "token de admin inválido"})


router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(admin_auth)])


class CreateGameBody(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    config: dict = Field(default_factory=dict)


class InvitePlayerBody(BaseModel):
    nickname: str = Field(default="", max_length=64)
    role: str = "player"
    color: str | None = Field(default=None, max_length=16)
    nickname_editable: bool | None = None
    # invitar por perfil: el apodo/color salen del perfil si no se pisan
    profile_id: str | None = None


class CreateProfileBody(BaseModel):
    nickname: str = Field(min_length=1, max_length=64)
    color: str | None = Field(default=None, max_length=16)


class PatchPlayerBody(BaseModel):
    nickname: str | None = Field(default=None, max_length=64)
    color: str | None = Field(default=None, max_length=16)
    avatar_asset_id: str | None = Field(default=None, max_length=200)


class FinishBody(BaseModel):
    winner_player_id: str | None = None


class CommentatorBody(BaseModel):
    enabled: bool | None = None
    humor_level: int | None = Field(default=None, ge=0, le=4)
    muted: bool | None = None


class TauntBody(BaseModel):
    owner_player_id: str
    target_player_id: str
    event_type: str
    asset_id: str = Field(max_length=200)


def _admin_player_view(player: dict) -> dict:
    view = repo.public_player(player)
    view["token_revoked"] = player["token_revoked"]
    view["nickname_editable"] = player["nickname_editable"]
    return view


@router.post("/games")
async def create_game(body: CreateGameBody, request: Request) -> dict:
    service = request.app.state.service
    try:
        game = await service.create_game(body.name, body.config)
    except ServiceError as exc:
        raise to_http(exc)
    return {"game": game, "lobby_url": f"{service.settings.public_base_url}/join/{game['code']}"}


@router.get("/games")
async def list_games(request: Request) -> dict:
    return {"games": await repo.list_games(request.app.state.service.db)}


@router.get("/games/{game_id}")
async def get_game(game_id: str, request: Request) -> dict:
    service = request.app.state.service
    try:
        game = await service.get_game_or_404(game_id)
    except ServiceError as exc:
        raise to_http(exc)
    players = await repo.get_players(service.db, game_id)
    room = service.manager.room(game_id)
    return {
        "game": game,
        "players": [
            _admin_player_view(p) | {"presence": room.presence_of(p["id"])} for p in players
        ],
    }


@router.get("/games/{game_id}/events")
async def get_events(game_id: str, request: Request, after: int = 0, limit: int = 500) -> dict:
    service = request.app.state.service
    try:
        await service.get_game_or_404(game_id)
    except ServiceError as exc:
        raise to_http(exc)
    events = await repo.get_events(service.db, game_id, after=after, limit=min(limit, 1000))
    return {"events": events}


@router.post("/games/{game_id}/players")
async def invite_player(game_id: str, body: InvitePlayerBody, request: Request) -> dict:
    service = request.app.state.service
    try:
        result = await service.invite_player(
            game_id, body.nickname, body.role, body.color, body.nickname_editable,
            profile_id=body.profile_id,
        )
    except ServiceError as exc:
        raise to_http(exc)
    return {
        "player": _admin_player_view(result["player"]),
        # el token en claro solo viaja en esta respuesta; no se vuelve a mostrar
        "token": result["token"],
        "join_url": result["join_url"],
    }


@router.patch("/games/{game_id}/players/{player_id}")
async def patch_player(game_id: str, player_id: str, body: PatchPlayerBody, request: Request) -> dict:
    service = request.app.state.service
    player = await repo.get_player(service.db, player_id)
    if player is None or player["game_id"] != game_id:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "jugador inexistente"})
    from ..security.sanitize import is_valid_asset_id, sanitize_nickname

    fields: dict = {}
    if body.nickname is not None:
        clean = sanitize_nickname(body.nickname)
        if not clean:
            raise HTTPException(status_code=422, detail={"code": "INVALID_PAYLOAD", "message": "apodo inválido"})
        fields["nickname"] = clean
    if body.color is not None:
        fields["color"] = body.color
    if body.avatar_asset_id is not None:
        if not body.avatar_asset_id.startswith("avatar") and not is_valid_asset_id(body.avatar_asset_id):
            raise HTTPException(status_code=422, detail={"code": "INVALID_PAYLOAD", "message": "asset inválido"})
        fields["avatar_asset_id"] = body.avatar_asset_id
    await repo.update_player(service.db, player_id, **fields)
    updated = await repo.get_player(service.db, player_id)
    assert updated is not None
    return {"player": _admin_player_view(updated)}


@router.post("/games/{game_id}/players/{player_id}/regenerate-token")
async def regenerate_token(game_id: str, player_id: str, request: Request) -> dict:
    try:
        return await request.app.state.service.regenerate_token(game_id, player_id)
    except ServiceError as exc:
        raise to_http(exc)


@router.post("/games/{game_id}/players/{player_id}/kick")
async def kick_player(game_id: str, player_id: str, request: Request) -> dict:
    try:
        await request.app.state.service.kick_player(game_id, player_id)
    except ServiceError as exc:
        raise to_http(exc)
    return {"ok": True}


@router.post("/games/{game_id}/start")
async def start_game(game_id: str, request: Request) -> dict:
    try:
        return await request.app.state.service.start_game(game_id)
    except ServiceError as exc:
        raise to_http(exc)


@router.post("/games/{game_id}/pause")
async def pause_game(game_id: str, request: Request) -> dict:
    try:
        await request.app.state.service.pause_game(game_id)
    except ServiceError as exc:
        raise to_http(exc)
    return {"ok": True}


@router.post("/games/{game_id}/resume")
async def resume_game(game_id: str, request: Request) -> dict:
    try:
        await request.app.state.service.resume_game(game_id)
    except ServiceError as exc:
        raise to_http(exc)
    return {"ok": True}


@router.post("/games/{game_id}/finish")
async def finish_game(game_id: str, body: FinishBody, request: Request) -> dict:
    try:
        summary = await request.app.state.service.finish_game(game_id, body.winner_player_id)
    except ServiceError as exc:
        raise to_http(exc)
    return {"summary": summary}


@router.post("/games/{game_id}/cancel")
async def cancel_game(game_id: str, request: Request) -> dict:
    try:
        await request.app.state.service.cancel_game(game_id)
    except ServiceError as exc:
        raise to_http(exc)
    return {"ok": True}


@router.post("/games/{game_id}/commentator")
async def commentator_config(game_id: str, body: CommentatorBody, request: Request) -> dict:
    try:
        cfg = await request.app.state.service.update_commentator_config(
            game_id, enabled=body.enabled, humor_level=body.humor_level, muted=body.muted
        )
    except ServiceError as exc:
        raise to_http(exc)
    return {"config": cfg}


@router.post("/games/{game_id}/taunts")
async def set_taunt(game_id: str, body: TauntBody, request: Request) -> dict:
    try:
        taunt = await request.app.state.service.set_taunt(
            game_id, body.owner_player_id, body.target_player_id, body.event_type, body.asset_id
        )
    except ServiceError as exc:
        raise to_http(exc)
    return {"taunt": taunt}


# --- perfiles persistentes del grupo ---------------------------------------

@router.post("/profiles")
async def create_profile(body: CreateProfileBody, request: Request) -> dict:
    service = request.app.state.service
    try:
        return await service.create_profile(body.nickname, body.color)
    except ServiceError as exc:
        raise to_http(exc)


@router.get("/profiles")
async def list_profiles(request: Request) -> dict:
    service = request.app.state.service
    return {"profiles": await service.list_profiles()}


@router.post("/profiles/{profile_id}/regenerate-token")
async def regenerate_profile_token(profile_id: str, request: Request) -> dict:
    service = request.app.state.service
    try:
        return await service.regenerate_profile_token(profile_id)
    except ServiceError as exc:
        raise to_http(exc)


@router.post("/games/{game_id}/players/{player_id}/convert-to-ai")
async def convert_seat_to_ai(game_id: str, player_id: str, request: Request) -> dict:
    """Un ausente se convierte en bot; al reabrir su link recupera el asiento."""
    try:
        await request.app.state.service.convert_seat_to_ai(game_id, player_id)
    except ServiceError as exc:
        raise to_http(exc)
    return {"ok": True}


@router.get("/games/{game_id}/stats")
async def game_stats(game_id: str, request: Request) -> dict:
    service = request.app.state.service
    try:
        await service.get_game_or_404(game_id)
    except ServiceError as exc:
        raise to_http(exc)
    return {"stats": await repo.get_game_stats(service.db, game_id)}
