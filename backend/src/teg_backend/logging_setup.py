"""Logs estructurados en JSON por stdout (los recolecta Docker/systemd)."""

from __future__ import annotations

import json
import logging
import re
import sys
import time

TOKEN_QUERY_RE = re.compile(r"([?&](?:token|admin|secret|password)=)[^&#\s\"]+", re.I)


def redact_log_value(value: object) -> object:
    if isinstance(value, str):
        return TOKEN_QUERY_RE.sub(r"\1***", value)
    if isinstance(value, tuple):
        return tuple(redact_log_value(v) for v in value)
    if isinstance(value, dict):
        return {k: redact_log_value(v) for k, v in value.items()}
    return value


class RedactionFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = redact_log_value(record.msg)
        record.args = redact_log_value(record.args)
        return True


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
    redaction_filter = RedactionFilter()
    handler.addFilter(redaction_filter)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level.upper())
    root.addFilter(redaction_filter)
    # Los access/handshake logs de Uvicorn incluyen query strings; los logs
    # estructurados teg.* cubren lo necesario sin exponer credenciales.
    logging.getLogger("uvicorn.access").setLevel("WARNING")
    logging.getLogger("uvicorn.error").setLevel("WARNING")
    logging.getLogger("uvicorn.error").addFilter(redaction_filter)


def redact_token(token: str) -> str:
    """Nunca loguear tokens completos."""
    if len(token) <= 8:
        return "***"
    return token[:4] + "…" + token[-2:]
