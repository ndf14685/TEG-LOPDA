"""Sobre (envelope) estable de eventos. Contrato en shared/contracts/websocket/."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from .. import SCHEMA_VERSION
from .enums import Visibility


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class GameEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str
    game_id: str
    actor_id: str | None = None
    target_id: str | None = None
    timestamp: str = Field(default_factory=utcnow_iso)
    sequence_number: int = 0
    # Secuencia densa sobre eventos publicos. None para privados/admin.
    # Es lo que viaja al cliente; ver seqTracker.ts.
    public_sequence: int | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    visibility: Visibility = Visibility.PUBLIC
    schema_version: str = SCHEMA_VERSION
    # False para eventos efímeros (snapshot, presence, error): no van al historial.
    persisted: bool = True

    def wire(self) -> dict[str, Any]:
        data = self.model_dump(mode="json")
        # El cliente solo debe ver una secuencia sin huecos: la publica.
        # Los no publicos viajan con 0 y el SeqTracker los ignora.
        data["sequence_number"] = self.public_sequence or 0
        data.pop("public_sequence", None)
        return data
