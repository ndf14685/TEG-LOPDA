from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from .. import __version__

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    """Sin información sensible: solo vivo/versión."""
    return {"status": "ok", "version": __version__}


@router.get("/metrics")
async def metrics(request: Request) -> JSONResponse:
    """Solo loopback o con token de admin (no se expone por el proxy)."""
    settings = request.app.state.settings
    client_host = request.client.host if request.client else ""
    from ..security.tokens import constant_time_equals

    token = request.headers.get("x-admin-token", "")
    is_local = client_host in ("127.0.0.1", "::1", "testclient")
    if not is_local and not constant_time_equals(token, settings.admin_token):
        return JSONResponse({"detail": "forbidden"}, status_code=403)
    return JSONResponse(request.app.state.service.metrics())
