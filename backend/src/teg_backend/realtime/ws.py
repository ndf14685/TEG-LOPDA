"""Endpoint WebSocket: /ws/{code}?token=...

Protocolo cliente→servidor (JSON): {"type": "...", "payload": {...}}
Tipos: ping, ready.set, chat.send, dice.roll, attack, turn.end,
turn.place_reinforcement, turn.fortify, turn.next_phase,
placement.place, cards.trade
Servidor→cliente: siempre el envelope de GameEvent (ver shared/contracts).
"""

from __future__ import annotations

import json
import logging
import uuid

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from ..application.game_service import GameService, ServiceError
from ..domain.enums import ErrorCode, EventType, Visibility
from ..domain.events import GameEvent
from ..security.ratelimit import WsRateLimiter

log = logging.getLogger("teg.ws")

router = APIRouter()


async def _send_error(ws: WebSocket, game_id: str, code: str, message: str) -> None:
    event = GameEvent(
        event_type=EventType.ERROR, game_id=game_id,
        payload={"code": code, "message": message},
        visibility=Visibility.PRIVATE, persisted=False,
    )
    await ws.send_json(event.wire())


@router.websocket("/ws/{code}")
async def ws_endpoint(ws: WebSocket, code: str, token: str = Query(...)) -> None:
    service: GameService = ws.app.state.service
    settings = ws.app.state.settings
    try:
        resolved = await service.resolve_join(code, token)
    except ServiceError:
        await ws.close(code=4401, reason="auth failed")
        return
    game, player = resolved["game"], resolved["player"]
    if player["joined_at"] is None:
        # debe pasar antes por POST /api/join para confirmar apodo
        await ws.close(code=4403, reason="join not confirmed")
        return

    await ws.accept()
    request_id = str(uuid.uuid4())
    room = service.manager.room(game["id"])
    room.add(player["id"], ws)
    limiter = WsRateLimiter(settings.ws_messages_per_window, settings.ws_window_seconds)
    log.info(
        "ws conectado",
        extra={"ctx": {"game": game["id"], "player": player["id"], "request_id": request_id}},
    )
    try:
        # snapshot inicial (efímero, solo para esta conexión)
        snapshot = await service.snapshot(game, player["id"])
        event = GameEvent(
            event_type=EventType.GAME_SNAPSHOT, game_id=game["id"],
            target_id=player["id"], payload=snapshot,
            visibility=Visibility.PRIVATE, persisted=False,
        )
        await ws.send_json(event.wire())
        await service.on_connect(game, player)

        while True:
            raw = await ws.receive_text()
            if len(raw.encode("utf-8")) > settings.ws_max_message_bytes:
                await _send_error(ws, game["id"], ErrorCode.MESSAGE_TOO_LARGE, "mensaje demasiado grande")
                continue
            if not limiter.allow():
                await _send_error(ws, game["id"], ErrorCode.RATE_LIMITED, "demasiados mensajes")
                continue
            try:
                msg = json.loads(raw)
                mtype = str(msg.get("type", ""))
                payload = msg.get("payload") or {}
                if not isinstance(payload, dict):
                    raise ValueError("payload debe ser objeto")
            except (json.JSONDecodeError, ValueError) as exc:
                await _send_error(ws, game["id"], ErrorCode.INVALID_PAYLOAD, str(exc))
                continue

            try:
                await _dispatch(service, ws, game, player, mtype, payload)
            except ServiceError as exc:
                pt = getattr(ws.app.state, "playtest", None)
                if pt and pt.active:
                    await pt.create_occurrence({
                        "category": "action-did-not-work",
                        "title": f"Acción rechazada: {mtype}",
                        "message": exc.message,
                        "error_type": "ServiceError",
                        "component": "backend.ws",
                        "action": mtype,
                        "code": exc.code,
                        "game_id": game["id"],
                        "player_id": player["id"],
                        "player_alias": player["nickname"],
                        "request_id": request_id,
                        "build_version": ws.app.state.settings.playtest_build,
                    })
                await _send_error(ws, game["id"], exc.code, exc.message)
            except Exception as exc:
                pt = getattr(ws.app.state, "playtest", None)
                if pt and pt.active:
                    await pt.create_occurrence({
                        "category": "other",
                        "title": f"Error WebSocket: {mtype}",
                        "message": str(exc),
                        "error_type": exc.__class__.__name__,
                        "component": "backend.ws",
                        "action": mtype,
                        "game_id": game["id"],
                        "player_id": player["id"],
                        "player_alias": player["nickname"],
                        "request_id": request_id,
                        "build_version": ws.app.state.settings.playtest_build,
                    })
                log.exception("error ws no controlado", extra={"ctx": {"game": game["id"], "player": player["id"], "action": mtype, "request_id": request_id}})
                await _send_error(ws, game["id"], ErrorCode.INVALID_ACTION, "error interno")
    except WebSocketDisconnect:
        pass
    finally:
        gone = room.remove(player["id"], ws)
        if gone:
            try:
                await service.on_disconnect(game["id"], player["id"])
            except Exception:
                log.warning("fallo notificando desconexión", exc_info=True)


async def _dispatch(
    service: GameService,
    ws: WebSocket,
    game: dict,
    player: dict,
    mtype: str,
    payload: dict,
) -> None:
    # el estado del juego puede haber cambiado desde la conexión: releer
    game = await service.get_game_or_404(game["id"])
    match mtype:
        case "ping":
            await ws.send_json({"type": "pong"})
        case "ready.set":
            await service.set_ready(game, player, bool(payload.get("ready", True)))
        case "chat.send":
            await service.chat(
                game, player,
                str(payload.get("text", "")),
                payload.get("target_player_id"),
            )
        case "dice.roll":
            await service.roll_dice(game["id"], player["id"], int(payload.get("count", 1)))
        case "attack":
            await service.attack(
                game["id"], player["id"],
                target_player_id=payload.get("target_player_id"),
                attacker_dice_count=int(payload.get("attacker_dice", 3)),
                source_territory_id=payload.get("source_territory_id"),
                target_territory_id=payload.get("target_territory_id"),
            )
        case "turn.end":
            await service.end_turn(game["id"], player["id"])
        case "turn.place_reinforcement":
            await service.place_reinforcement(
                game["id"], player["id"],
                str(payload.get("territory_id", "")),
                int(payload.get("count", 1)),
            )
        case "turn.fortify":
            await service.fortify(
                game["id"], player["id"],
                str(payload.get("source_territory_id", "")),
                str(payload.get("target_territory_id", "")),
                int(payload.get("count", 1)),
            )
        case "turn.next_phase":
            await service.next_phase(game["id"], player["id"])
        case "turn.wager":
            await service.set_wager(game["id"], player["id"], int(payload.get("amount", 0)))
        case "placement.place":
            await service.place_initial(
                game["id"], player["id"],
                str(payload.get("territory_id", "")),
                int(payload.get("count", 1)),
            )
        case "cards.trade":
            ids = payload.get("card_ids")
            if not isinstance(ids, list):
                raise ServiceError(ErrorCode.INVALID_PAYLOAD, "card_ids debe ser lista")
            await service.trade_cards(game["id"], player["id"], [str(c) for c in ids])
        case "pact.propose":
            await service.propose_pact(
                game["id"], player["id"], str(payload.get("target_player_id", ""))
            )
        case "pact.respond":
            await service.respond_pact(
                game["id"], player["id"], bool(payload.get("accept", False))
            )
        case "pact.break":
            await service.break_pact(
                game["id"], player["id"], str(payload.get("target_player_id", ""))
            )
        case _:
            raise ServiceError(ErrorCode.INVALID_ACTION, f"tipo desconocido: {mtype}")
