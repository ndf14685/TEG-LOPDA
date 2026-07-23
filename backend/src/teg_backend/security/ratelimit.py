"""Rate limiting simple en memoria (suficiente para 10-20 jugadores)."""

from __future__ import annotations

import time


class SlidingWindowLimiter:
    """Limita a `limit` hits por `window_seconds` por clave."""

    def __init__(self, limit: int, window_seconds: float) -> None:
        self.limit = limit
        self.window = window_seconds
        self._hits: dict[str, list[float]] = {}

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        hits = self._hits.setdefault(key, [])
        cutoff = now - self.window
        while hits and hits[0] < cutoff:
            hits.pop(0)
        if len(hits) >= self.limit:
            return False
        hits.append(now)
        return True

    def cleanup(self) -> None:
        cutoff = time.monotonic() - self.window
        for key in list(self._hits):
            if not self._hits[key] or self._hits[key][-1] < cutoff:
                del self._hits[key]


class WsRateLimiter:
    """Limitador por conexión WebSocket."""

    def __init__(self, limit: int, window_seconds: float) -> None:
        self.limit = limit
        self.window = window_seconds
        self._hits: list[float] = []

    def allow(self) -> bool:
        now = time.monotonic()
        cutoff = now - self.window
        while self._hits and self._hits[0] < cutoff:
            self._hits.pop(0)
        if len(self._hits) >= self.limit:
            return False
        self._hits.append(now)
        return True
