"""Configuración por variables de entorno (prefijo TEG_)."""

from __future__ import annotations

import os
import secrets
from dataclasses import dataclass, field


def _bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    return int(raw) if raw else default


def _float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    return float(raw) if raw else default


def _list(name: str, default: list[str]) -> list[str]:
    raw = os.environ.get(name)
    if not raw:
        return default
    return [item.strip() for item in raw.split(",") if item.strip()]


@dataclass(slots=True)
class Settings:
    env: str = "dev"
    host: str = "127.0.0.1"
    port: int = 8123
    db_path: str = "data/teg.db"
    admin_token: str = ""
    admin_token_generated: bool = False
    public_base_url: str = "http://localhost:8123"
    cors_origins: list[str] = field(default_factory=lambda: ["http://localhost:5173"])
    log_level: str = "INFO"
    debug_page: bool = True

    ws_max_message_bytes: int = 8192
    ws_messages_per_window: int = 20
    ws_window_seconds: float = 5.0
    rest_requests_per_minute: int = 240

    commentator_enabled: bool = True
    commentator_provider: str = "mock"  # mock | ollama
    commentator_cooldown_seconds: float = 15.0
    commentator_max_chars: int = 280
    humor_level_default: int = 2
    # Nivel 4 (bardeo entre amigos) deshabilitado por defecto: subir este tope
    # explícitamente por env para permitirlo.
    humor_level_max: int = 3

    ollama_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "llama3.2"

    ai_player_timeout_seconds: float = 5.0
    ai_player_think_seconds: float = 1.5

    reconnect_grace_seconds: float = 30.0


def load_settings() -> Settings:
    admin_token = os.environ.get("TEG_ADMIN_TOKEN", "")
    generated = False
    if not admin_token:
        admin_token = secrets.token_urlsafe(24)
        generated = True
    return Settings(
        env=os.environ.get("TEG_ENV", "dev"),
        host=os.environ.get("TEG_HOST", "127.0.0.1"),
        port=_int("TEG_PORT", 8123),
        db_path=os.environ.get("TEG_DB_PATH", "data/teg.db"),
        admin_token=admin_token,
        admin_token_generated=generated,
        public_base_url=os.environ.get("TEG_PUBLIC_BASE_URL", "http://localhost:8123").rstrip("/"),
        cors_origins=_list("TEG_CORS_ORIGINS", ["http://localhost:5173"]),
        log_level=os.environ.get("TEG_LOG_LEVEL", "INFO"),
        debug_page=_bool("TEG_DEBUG_PAGE", True),
        ws_max_message_bytes=_int("TEG_WS_MAX_MESSAGE_BYTES", 8192),
        ws_messages_per_window=_int("TEG_WS_MESSAGES_PER_WINDOW", 20),
        ws_window_seconds=_float("TEG_WS_WINDOW_SECONDS", 5.0),
        rest_requests_per_minute=_int("TEG_REST_REQUESTS_PER_MINUTE", 240),
        commentator_enabled=_bool("TEG_COMMENTATOR_ENABLED", True),
        commentator_provider=os.environ.get("TEG_COMMENTATOR_PROVIDER", "mock"),
        commentator_cooldown_seconds=_float("TEG_COMMENTATOR_COOLDOWN_SECONDS", 15.0),
        commentator_max_chars=_int("TEG_COMMENTATOR_MAX_CHARS", 280),
        humor_level_default=_int("TEG_HUMOR_LEVEL_DEFAULT", 2),
        humor_level_max=_int("TEG_HUMOR_LEVEL_MAX", 3),
        ollama_url=os.environ.get("TEG_OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/"),
        ollama_model=os.environ.get("TEG_OLLAMA_MODEL", "llama3.2"),
        ai_player_timeout_seconds=_float("TEG_AI_PLAYER_TIMEOUT_SECONDS", 5.0),
        ai_player_think_seconds=_float("TEG_AI_PLAYER_THINK_SECONDS", 1.5),
        reconnect_grace_seconds=_float("TEG_RECONNECT_GRACE_SECONDS", 30.0),
    )
