"""Configuración por variables de entorno (prefijo TEG_)."""

from __future__ import annotations

import os
import secrets
from dataclasses import dataclass, field
from datetime import datetime


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
    media_dir: str = "data/media"
    # disco al límite en el host: audios cortos y con tope duro
    taunt_max_bytes: int = 512 * 1024
    taunt_max_per_profile: int = 40
    admin_token: str = ""
    admin_token_generated: bool = False
    public_base_url: str = "http://localhost:8123"
    cors_origins: list[str] = field(default_factory=lambda: ["http://localhost:5173"])
    log_level: str = "INFO"
    debug_page: bool = True

    ws_max_message_bytes: int = 8192
    ws_messages_per_window: int = 20
    ws_window_seconds: float = 5.0
    # tope por socket en el fan-out: el que no drena se cierra en vez de
    # frenar al resto de la mesa
    ws_send_timeout_seconds: float = 5.0
    rest_requests_per_minute: int = 240

    commentator_enabled: bool = True
    commentator_provider: str = "chain"  # chain | mock | ollama
    commentator_cooldown_seconds: float = 15.0
    commentator_max_chars: int = 280
    humor_level_default: int = 3
    # Nivel 4 = bardeo entre amigos, habilitado: bajar por env si un grupo
    # prefiere un relator más tranquilo.
    humor_level_max: int = 4

    ollama_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "llama3.2"

    ai_player_timeout_seconds: float = 5.0
    ai_player_think_seconds: float = 1.5

    reconnect_grace_seconds: float = 30.0
    turn_timeout_seconds: float = 180.0

    playtest_mode: bool = False
    playtest_until: str = ""
    playtest_build: str = ""
    playtest_db_path: str = "data/playtest.db"
    playtest_attachment_dir: str = "data/playtest-attachments"
    playtest_export_dir: str = "docs/playtest"
    playtest_retention_days: int = 14
    playtest_manual_reports_per_minute: int = 5
    playtest_incidents_per_minute: int = 12


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
        media_dir=os.environ.get("TEG_MEDIA_DIR", "data/media"),
        taunt_max_bytes=_int("TEG_TAUNT_MAX_BYTES", 512 * 1024),
        taunt_max_per_profile=_int("TEG_TAUNT_MAX_PER_PROFILE", 40),
        admin_token=admin_token,
        admin_token_generated=generated,
        public_base_url=os.environ.get("TEG_PUBLIC_BASE_URL", "http://localhost:8123").rstrip("/"),
        cors_origins=_list("TEG_CORS_ORIGINS", ["http://localhost:5173"]),
        log_level=os.environ.get("TEG_LOG_LEVEL", "INFO"),
        debug_page=_bool("TEG_DEBUG_PAGE", True),
        ws_max_message_bytes=_int("TEG_WS_MAX_MESSAGE_BYTES", 8192),
        ws_messages_per_window=_int("TEG_WS_MESSAGES_PER_WINDOW", 20),
        ws_window_seconds=_float("TEG_WS_WINDOW_SECONDS", 5.0),
        ws_send_timeout_seconds=_float("TEG_WS_SEND_TIMEOUT_SECONDS", 5.0),
        rest_requests_per_minute=_int("TEG_REST_REQUESTS_PER_MINUTE", 240),
        commentator_enabled=_bool("TEG_COMMENTATOR_ENABLED", True),
        commentator_provider=os.environ.get("TEG_COMMENTATOR_PROVIDER", "chain"),
        commentator_cooldown_seconds=_float("TEG_COMMENTATOR_COOLDOWN_SECONDS", 15.0),
        commentator_max_chars=_int("TEG_COMMENTATOR_MAX_CHARS", 280),
        humor_level_default=_int("TEG_HUMOR_LEVEL_DEFAULT", 3),
        humor_level_max=_int("TEG_HUMOR_LEVEL_MAX", 4),
        ollama_url=os.environ.get("TEG_OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/"),
        ollama_model=os.environ.get("TEG_OLLAMA_MODEL", "llama3.2"),
        ai_player_timeout_seconds=_float("TEG_AI_PLAYER_TIMEOUT_SECONDS", 5.0),
        ai_player_think_seconds=_float("TEG_AI_PLAYER_THINK_SECONDS", 1.5),
        reconnect_grace_seconds=_float("TEG_RECONNECT_GRACE_SECONDS", 30.0),
        turn_timeout_seconds=_float("TEG_TURN_TIMEOUT_SECONDS", 180.0),
        playtest_mode=_bool("PLAYTEST_MODE", False),
        playtest_until=os.environ.get("PLAYTEST_UNTIL", ""),
        playtest_build=os.environ.get("PLAYTEST_BUILD", ""),
        playtest_db_path=os.environ.get("PLAYTEST_DB_PATH", "data/playtest.db"),
        playtest_attachment_dir=os.environ.get("PLAYTEST_ATTACHMENT_DIR", "data/playtest-attachments"),
        playtest_export_dir=os.environ.get("PLAYTEST_EXPORT_DIR", "docs/playtest"),
        playtest_retention_days=_int("PLAYTEST_RETENTION_DAYS", 14),
        playtest_manual_reports_per_minute=_int("PLAYTEST_MANUAL_REPORTS_PER_MINUTE", 5),
        playtest_incidents_per_minute=_int("PLAYTEST_INCIDENTS_PER_MINUTE", 12),
    )
