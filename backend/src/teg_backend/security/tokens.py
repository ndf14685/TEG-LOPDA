"""Tokens de acceso por jugador: aleatorios, revocables, guardados como hash."""

from __future__ import annotations

import hashlib
import hmac
import secrets

TOKEN_BYTES = 24  # 32 chars urlsafe aprox
CODE_ALPHABET = "abcdefghjkmnpqrstuvwxyz23456789"  # sin confusables (l/1, o/0)


def new_player_token() -> str:
    return secrets.token_urlsafe(TOKEN_BYTES)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def verify_token(token: str, token_hash: str) -> bool:
    return hmac.compare_digest(hash_token(token), token_hash)


def constant_time_equals(a: str, b: str) -> bool:
    return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))


def new_game_code(length: int = 8) -> str:
    return "".join(secrets.choice(CODE_ALPHABET) for _ in range(length))
