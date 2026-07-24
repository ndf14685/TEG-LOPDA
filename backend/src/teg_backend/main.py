"""Fábrica de la aplicación FastAPI."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from . import __version__
from .ai.commentator import CommentatorService, build_provider
from .api import admin, health, join, media
from .application.game_service import GameService
from .config import Settings, load_settings
from .infrastructure.db import Database
from .logging_setup import redact_token, setup_logging
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
        manager = ConnectionManager()
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
        commentator.start()
        log.info(
            "backend iniciado",
            extra={"ctx": {"env": settings.env, "db": settings.db_path,
                           "commentator": provider.name, "version": __version__}},
        )
        try:
            yield
        finally:
            await commentator.stop()
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
        if request.url.path.startswith("/api/"):
            key = request.client.host if request.client else "unknown"
            if not rest_limiter.allow(key):
                return JSONResponse(
                    {"detail": {"code": "RATE_LIMITED", "message": "demasiadas peticiones"}},
                    status_code=429,
                )
        return await call_next(request)

    app.include_router(health.router)
    app.include_router(join.router)
    app.include_router(join.profile_router)
    app.include_router(media.router)
    app.include_router(admin.router)
    app.include_router(ws.router)

    if settings.debug_page:
        @app.get("/dev")
        async def dev_page() -> FileResponse:
            return FileResponse(STATIC_DIR / "dev-lobby.html")

    return app


# instancia por defecto para `uvicorn teg_backend.main:app`
app = create_app()
