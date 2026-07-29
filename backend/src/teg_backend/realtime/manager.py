"""Gestión de salas y conexiones WebSocket con routing por visibilidad."""

from __future__ import annotations

import asyncio
import contextlib
import logging
from typing import Any

from fastapi import WebSocket

from ..domain.enums import Role, Visibility
from ..domain.events import GameEvent

log = logging.getLogger("teg.realtime")


class Room:
    def __init__(self, game_id: str) -> None:
        self.game_id = game_id
        # player_id -> conexiones abiertas (puede haber más de una pestaña)
        self.sockets: dict[str, set[WebSocket]] = {}
        # player_id -> online | reconnecting | offline
        self.presence: dict[str, str] = {}
        self._offline_tasks: dict[str, asyncio.Task] = {}

    def add(self, player_id: str, ws: WebSocket) -> None:
        self.sockets.setdefault(player_id, set()).add(ws)
        self.presence[player_id] = "online"
        task = self._offline_tasks.pop(player_id, None)
        if task:
            task.cancel()

    def remove(self, player_id: str, ws: WebSocket) -> bool:
        """Devuelve True si el jugador quedó sin conexiones."""
        conns = self.sockets.get(player_id)
        if conns:
            conns.discard(ws)
            if not conns:
                del self.sockets[player_id]
        return player_id not in self.sockets

    def presence_of(self, player_id: str) -> str:
        return self.presence.get(player_id, "offline")

    def is_empty(self) -> bool:
        return not self.sockets


class ConnectionManager:
    def __init__(self, send_timeout_seconds: float = 5.0) -> None:
        self.rooms: dict[str, Room] = {}
        self.send_timeout_seconds = send_timeout_seconds

    def room(self, game_id: str) -> Room:
        return self.rooms.setdefault(game_id, Room(game_id))

    def connection_count(self) -> int:
        return sum(
            len(conns) for room in self.rooms.values() for conns in room.sockets.values()
        )

    def recipients_for(
        self, event: GameEvent, roles: dict[str, str]
    ) -> set[str] | None:
        """Devuelve player_ids destinatarios; None = todos los conectados.

        - public: todos (jugadores y espectadores).
        - private: actor, target y admins conectados (moderación).
        - admin: solo conexiones con rol admin.
        """
        if event.visibility == Visibility.PUBLIC:
            return None
        admins = {pid for pid, role in roles.items() if role == Role.ADMIN}
        if event.visibility == Visibility.ADMIN:
            return admins
        involved = {pid for pid in (event.actor_id, event.target_id) if pid}
        return involved | admins

    async def broadcast(self, game_id: str, event: GameEvent, roles: dict[str, str]) -> None:
        room = self.rooms.get(game_id)
        if room is None:
            return
        recipients = self.recipients_for(event, roles)
        payload = event.wire()
        targets: list[tuple[str, WebSocket]] = []
        for player_id, conns in room.sockets.items():
            if recipients is None or player_id in recipients:
                targets.extend((player_id, ws) for ws in conns)
        if not targets:
            return

        async def _enviar(player_id: str, ws: WebSocket) -> None:
            try:
                # Sin timeout, un socket cuyo buffer no drena (red mala, pestaña
                # suspendida) colgaba el broadcast entero y con él la partida.
                async with asyncio.timeout(self.send_timeout_seconds):
                    await ws.send_json(payload)
            except (TimeoutError, asyncio.CancelledError):
                log.info(
                    "socket lento: se cierra para no frenar la partida",
                    extra={"ctx": {"game_id": game_id, "player_id": player_id}},
                )
                # el endpoint WS hace la limpieza real en su finally
                with contextlib.suppress(Exception):
                    await ws.close(code=1011)
            except Exception:
                # la desconexión real la maneja el endpoint WS
                log.debug("fallo enviando a un socket", exc_info=True)

        await asyncio.gather(
            *(_enviar(pid, ws) for pid, ws in targets),
            return_exceptions=True,
        )

    async def send_to_player(self, game_id: str, player_id: str, data: dict[str, Any]) -> None:
        room = self.rooms.get(game_id)
        if room is None:
            return
        for ws in list(room.sockets.get(player_id, ())):
            try:
                await ws.send_json(data)
            except Exception:
                log.debug("fallo enviando a un socket", exc_info=True)

    async def disconnect_player(self, game_id: str, player_id: str) -> None:
        """Cierra todas las conexiones de un jugador (kick/revocación)."""
        room = self.rooms.get(game_id)
        if room is None:
            return
        for ws in list(room.sockets.get(player_id, ())):
            try:
                await ws.close(code=4001, reason="access revoked")
            except Exception:
                pass
