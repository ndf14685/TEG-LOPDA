"""Sanitización estricta de entradas de usuario."""

from __future__ import annotations

import re
import unicodedata

MAX_CHAT_LEN = 500
MAX_NICKNAME_LEN = 24

_ASSET_ID_RE = re.compile(r"^audio/[a-z0-9][a-z0-9/._-]{0,199}$")


def sanitize_text(text: str, max_len: int = MAX_CHAT_LEN) -> str:
    """Quita caracteres de control y recorta. No escapa HTML: el frontend debe
    renderizar siempre como texto plano."""
    cleaned = "".join(
        ch for ch in text if ch in ("\n", "\t") or unicodedata.category(ch)[0] != "C"
    )
    cleaned = re.sub(r"[ \t]+", " ", cleaned).strip()
    return cleaned[:max_len]


def sanitize_nickname(nickname: str) -> str:
    cleaned = sanitize_text(nickname, MAX_NICKNAME_LEN)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def is_valid_asset_id(asset_id: str) -> bool:
    """IDs lógicos tipo audio/taunts/player-x/to-player-y/evento-001.ogg.
    Sin path traversal, sin rutas absolutas, kebab-case en minúsculas."""
    if ".." in asset_id or asset_id.startswith("/"):
        return False
    return bool(_ASSET_ID_RE.fullmatch(asset_id))
