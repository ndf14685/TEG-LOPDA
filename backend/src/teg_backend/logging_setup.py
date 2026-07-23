"""Logs estructurados en JSON por stdout (los recolecta Docker/systemd)."""

from __future__ import annotations

import json
import logging
import sys
import time


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        data: dict = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(record.created)),
            "level": record.levelname.lower(),
            "logger": record.name,
            "msg": record.getMessage(),
        }
        ctx = getattr(record, "ctx", None)
        if isinstance(ctx, dict):
            data.update(ctx)
        if record.exc_info:
            data["exc"] = self.formatException(record.exc_info)
        return json.dumps(data, ensure_ascii=False)


def setup_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level.upper())
    # uvicorn ya loguea accesos; bajamos ruido
    logging.getLogger("uvicorn.access").setLevel("WARNING")


def redact_token(token: str) -> str:
    """Nunca loguear tokens completos."""
    if len(token) <= 8:
        return "***"
    return token[:4] + "…" + token[-2:]
