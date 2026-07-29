"""Fábrica de la aplicación FastAPI."""

from __future__ import annotations

import logging
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from . import __version__
from .ai.commentator import CommentatorService, build_provider
from .api import admin, health, join, media, playtest
from .application.game_service import GameService
from .config import Settings, load_settings
from .infrastructure.db import Database
from .logging_setup import redact_token, setup_logging
from .playtest.service import PlaytestService
from .realtime import ws
from .realtime.manager import ConnectionManager
from .security.ratelimit import SlidingWindowLimiter

log = logging.getLogger("teg.main")

STATIC_DIR = Path(__file__).resolve().parent / "static"


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or load_settings()
    setup_logging(settings.log_level)
    if settings.admin_token_generated:
        log.warning(
            "TEG_ADMIN_TOKEN no definido; se generó uno efímero",
            extra={"ctx": {"admin_token_hint": redact_token(settings.admin_token)}},
        )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        db = Database(settings.db_path)
        await db.connect()
        playtest_db = Database(settings.playtest_db_path)
        await playtest_db.connect()
        manager = ConnectionManager(send_timeout_seconds=settings.ws_send_timeout_seconds)
        provider = build_provider(
            settings.commentator_provider,
            ollama_url=settings.ollama_url,
            ollama_model=settings.ollama_model,
        )
        commentator = CommentatorService(
            provider,
            enabled=settings.commentator_enabled,
            cooldown_seconds=settings.commentator_cooldown_seconds,
            max_chars=settings.commentator_max_chars,
        )
        app.state.settings = settings
        app.state.service = GameService(db, manager, commentator, settings)
        app.state.playtest = PlaytestService(playtest_db, settings)
        await app.state.playtest.init()
        commentator.start()
        reagendados = await app.state.service.rehidratar_partidas_activas()
        if reagendados:
            log.info(
                "turnos de bot reagendados tras reinicio",
                extra={"ctx": {"turnos": reagendados}},
            )
        log.info(
            "backend iniciado",
            extra={"ctx": {"env": settings.env, "db": settings.db_path,
                           "commentator": provider.name, "version": __version__,
                           "playtest": settings.playtest_mode,
                           "playtest_build": settings.playtest_build}},
        )
        try:
            yield
        finally:
            # antes de cerrar las bases: timers y workers de envio las usan
            await app.state.service.detener_timers()
            await app.state.service.detener_envios()
            await commentator.stop()
            await playtest_db.close()
            await db.close()

    app = FastAPI(
        title="TEG LOPDA Backend",
        version=__version__,
        lifespan=lifespan,
        docs_url="/docs" if settings.env == "dev" else None,
        redoc_url=None,
        openapi_url="/openapi.json" if settings.env == "dev" else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Content-Type", "X-Admin-Token"],
    )

    rest_limiter = SlidingWindowLimiter(settings.rest_requests_per_minute, 60.0)

    @app.middleware("http")
    async def rate_limit_middleware(request: Request, call_next):
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        if request.url.path.startswith("/api/"):
            key = request.client.host if request.client else "unknown"
            if not rest_limiter.allow(key):
                return JSONResponse(
                    {"detail": {"code": "RATE_LIMITED", "message": "demasiadas peticiones"}},
                    status_code=429,
                    headers={"X-Request-ID": request_id},
                )
        try:
            response = await call_next(request)
        except Exception as exc:
            pt = getattr(request.app.state, "playtest", None)
            if pt and pt.active:
                try:
                    await pt.create_occurrence({
                        "category": "other",
                        "title": f"Backend exception {request.method} {request.url.path}",
                        "message": str(exc),
                        "error_type": exc.__class__.__name__,
                        "component": "backend",
                        "endpoint": request.url.path,
                        "request_id": request_id,
                        "build_version": settings.playtest_build,
                    })
                except Exception:
                    log.warning("fallo registrando incidente playtest", exc_info=True)
            log.exception("excepción no controlada", extra={"ctx": {"request_id": request_id, "path": request.url.path}})
            return JSONResponse(
                {"detail": {"code": "INTERNAL_ERROR", "message": "error interno"}},
                status_code=500,
                headers={"X-Request-ID": request_id},
            )
        response.headers["X-Request-ID"] = request_id
        if response.status_code >= 500:
            pt = getattr(request.app.state, "playtest", None)
            if pt and pt.active:
                try:
                    await pt.create_occurrence({
                        "category": "other",
                        "title": f"HTTP {response.status_code} {request.url.path}",
                        "message": f"HTTP {response.status_code}",
                        "error_type": "HTTP_5XX",
                        "component": "backend",
                        "endpoint": request.url.path,
                        "request_id": request_id,
                        "build_version": settings.playtest_build,
                    })
                except Exception:
                    log.warning("fallo registrando 5xx playtest", exc_info=True)
        return response

    app.include_router(health.router)
    app.include_router(join.router)
    app.include_router(join.profile_router)
    app.include_router(playtest.router)
    app.include_router(media.router)
    app.include_router(admin.router)
    app.include_router(playtest.admin_router)
    app.include_router(ws.router)

    if settings.debug_page:
        @app.get("/dev")
        async def dev_page() -> FileResponse:
            return FileResponse(STATIC_DIR / "dev-lobby.html")

    return app


# instancia por defecto para `uvicorn teg_backend.main:app`
app = create_app()
