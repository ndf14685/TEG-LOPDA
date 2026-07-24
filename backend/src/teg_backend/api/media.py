"""Audios personalizados (taunts) por perfil + servido de media.

Subida sin multipart (cero dependencias): el body es el audio crudo y los
metadatos van por query. El archivo se guarda con nombre aleatorio no
adivinable bajo media_dir/taunts.
"""

from __future__ import annotations

import re
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse

from ..application.game_service import ServiceError
from ..infrastructure import repository as repo
from .errors import to_http

router = APIRouter(prefix="/api", tags=["media"])

ALLOWED_EXT = {"webm": "audio/webm", "ogg": "audio/ogg", "mp3": "audio/mpeg"}
TAUNT_EVENT_TYPES = {
    "territory.conquered",  # te conquisté un país
    "player.eliminated",    # te eliminé
    "attack.resolved",      # combate resuelto contra vos
    "game.started",         # saludo al arrancar la partida
}
_FILENAME_RE = re.compile(r"^[0-9a-f-]{36}\.(webm|ogg|mp3)$")


def _taunts_dir(request: Request) -> Path:
    d = Path(request.app.state.settings.media_dir) / "taunts"
    d.mkdir(parents=True, exist_ok=True)
    return d


async def _profile_or_404(request: Request, token: str) -> dict:
    try:
        return await request.app.state.service.resolve_profile(token)
    except ServiceError as exc:
        raise to_http(exc)


def _taunt_view(taunt: dict) -> dict:
    return {
        "id": taunt["id"],
        "target_profile_id": taunt["target_profile_id"],
        "event_type": taunt["event_type"],
        "audio_url": f"/api/media/taunts/{taunt['filename']}",
    }


@router.post("/profile/{token}/taunts")
async def upload_taunt(
    token: str,
    request: Request,
    target_profile_id: str,
    event_type: str,
    ext: str = "webm",
) -> dict:
    settings = request.app.state.settings
    service = request.app.state.service
    profile = await _profile_or_404(request, token)
    if event_type not in TAUNT_EVENT_TYPES:
        raise HTTPException(422, detail={"code": "INVALID_PAYLOAD", "message": f"evento no taunteable: {event_type}"})
    if ext not in ALLOWED_EXT:
        raise HTTPException(422, detail={"code": "INVALID_PAYLOAD", "message": "formato: webm, ogg o mp3"})
    target = await repo.get_profile(service.db, target_profile_id)
    if target is None:
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "perfil rival inexistente"})
    if target["id"] == profile["id"]:
        raise HTTPException(422, detail={"code": "INVALID_PAYLOAD", "message": "no podés grabarte audios a vos mismo"})

    body = await request.body()
    if not body:
        raise HTTPException(422, detail={"code": "INVALID_PAYLOAD", "message": "audio vacío"})
    if len(body) > settings.taunt_max_bytes:
        raise HTTPException(
            413,
            detail={"code": "INVALID_PAYLOAD",
                    "message": f"audio demasiado grande (máx {settings.taunt_max_bytes // 1024} KB)"},
        )
    existing = await repo.find_profile_taunt(service.db, profile["id"], target_profile_id, event_type)
    count = await repo.count_profile_taunts(service.db, profile["id"])
    if existing is None and count >= settings.taunt_max_per_profile:
        raise HTTPException(
            422,
            detail={"code": "INVALID_PAYLOAD",
                    "message": f"tope de {settings.taunt_max_per_profile} audios por perfil"},
        )

    filename = f"{uuid.uuid4()}.{ext}"
    (_taunts_dir(request) / filename).write_bytes(body)
    if existing:  # reemplaza: borrar el archivo anterior
        old = _taunts_dir(request) / existing["filename"]
        old.unlink(missing_ok=True)
    taunt = await repo.upsert_profile_taunt(
        service.db, profile["id"], target_profile_id, event_type, filename
    )
    return {"taunt": _taunt_view(taunt)}


@router.get("/profile/{token}/taunts")
async def list_taunts(token: str, request: Request) -> dict:
    service = request.app.state.service
    profile = await _profile_or_404(request, token)
    taunts = await repo.list_profile_taunts(service.db, profile["id"])
    return {"taunts": [_taunt_view(t) for t in taunts]}


@router.delete("/profile/{token}/taunts/{taunt_id}")
async def delete_taunt(token: str, taunt_id: str, request: Request) -> dict:
    service = request.app.state.service
    profile = await _profile_or_404(request, token)
    filename = await repo.delete_profile_taunt(service.db, profile["id"], taunt_id)
    if filename is None:
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "audio inexistente"})
    (_taunts_dir(request) / filename).unlink(missing_ok=True)
    return {"ok": True}


@router.get("/profile-group")
async def profile_group(request: Request) -> dict:
    """Perfiles del grupo (nombre y color): lo usa el estudio de audios para
    elegir rival. Es un grupo de amigos; no expone tokens ni datos sensibles."""
    service = request.app.state.service
    return {"profiles": await service.list_profiles()}


@router.get("/media/taunts/{filename}")
async def serve_taunt(filename: str, request: Request) -> FileResponse:
    if not _FILENAME_RE.match(filename):
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "audio inexistente"})
    path = _taunts_dir(request) / filename
    if not path.is_file():
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "audio inexistente"})
    ext = filename.rsplit(".", 1)[1]
    return FileResponse(path, media_type=ALLOWED_EXT[ext])


@router.get("/profile/{token}/stats")
async def profile_stats(token: str, request: Request) -> dict:
    """Histórico del perfil: acumulados y trofeos de todas sus partidas."""
    service = request.app.state.service
    profile = await _profile_or_404(request, token)
    return {"stats": await repo.get_profile_stats(service.db, profile["id"])}
