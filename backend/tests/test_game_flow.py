"""Flujo completo por REST + WS: crear, invitar, entrar, ready, jugar."""

import time

from conftest import ADMIN, confirm_join, create_game, invite, recv_until


def test_full_game_flow(client):
    # el comentarista se desactiva para que el stream de eventos sea determinista
    game = create_game(client, config={"commentator_enabled": False})
    code = game["code"]

    inv1 = invite(client, game["id"], "Nessi")
    inv2 = invite(client, game["id"], "Daro")
    assert inv1["token"] and inv1["join_url"].endswith(inv1["token"])

    # el link resuelve la invitación sin unirse todavía
    resp = client.get(f"/api/join/{code}/{inv1['token']}")
    assert resp.status_code == 200
    assert resp.json()["player"]["nickname"] == "Nessi"
    assert resp.json()["player"]["already_joined"] is False

    # ambos confirman (uno edita su apodo)
    j1 = confirm_join(client, code, inv1["token"], nickname="Nessi la estratega")
    j2 = confirm_join(client, code, inv2["token"])
    assert j1["player"]["nickname"] == "Nessi la estratega"
    p1_id, p2_id = j1["player"]["id"], j2["player"]["id"]

    with client.websocket_connect(f"/ws/{code}?token={inv1['token']}") as ws1:
        snap = recv_until(ws1, "game.snapshot")
        assert {p["id"] for p in snap["payload"]["players"]} == {p1_id, p2_id}

        with client.websocket_connect(f"/ws/{code}?token={inv2['token']}") as ws2:
            recv_until(ws2, "game.snapshot")
            # ws1 ve conectarse a ws2
            ev = recv_until(ws1, "presence.changed")
            assert ev["payload"]["presence"] == "online"

            # ready de ambos
            ws1.send_json({"type": "ready.set", "payload": {"ready": True}})
            recv_until(ws2, "player.ready")
            ws2.send_json({"type": "ready.set", "payload": {"ready": True}})
            ev = recv_until(ws1, "player.ready")
            if ev["actor_id"] == p1_id:  # el propio ready llegó primero
                ev = recv_until(ws1, "player.ready")
            assert ev["payload"]["all_ready"] is True

            # inicia el admin
            resp = client.post(f"/api/admin/games/{game['id']}/start", headers=ADMIN)
            assert resp.status_code == 200
            order = resp.json()["turn_order"]
            assert set(order) == {p1_id, p2_id}

            recv_until(ws1, "game.started")
            turn = recv_until(ws1, "turn.started")
            current = turn["actor_id"]
            ws_current = ws1 if current == p1_id else ws2
            ws_other = ws2 if current == p1_id else ws1

            # dados autoritativos: solo el jugador de turno puede tirar
            ws_other.send_json({"type": "dice.roll", "payload": {"count": 3}})
            err = recv_until(ws_other, "error")
            assert err["payload"]["code"] == "NOT_YOUR_TURN"

            ws_current.send_json({"type": "dice.roll", "payload": {"count": 3}})
            ev = recv_until(ws_other, "dice.rolled")
            dice = ev["payload"]["dice"]
            assert len(dice) == 3 and all(1 <= d <= 6 for d in dice)

            # ataque con dados del servidor
            target = p2_id if current == p1_id else p1_id
            ws_current.send_json(
                {"type": "attack", "payload": {"target_player_id": target, "attacker_dice": 3}}
            )
            ev = recv_until(ws_other, "attack.resolved")
            assert ev["payload"]["attacker_losses"] + ev["payload"]["defender_losses"] == 3

            # chat público y privado
            ws1.send_json({"type": "chat.send", "payload": {"text": "hola <b>toda</b> la sala"}})
            ev = recv_until(ws2, "chat.message")
            assert ev["payload"]["text"] == "hola <b>toda</b> la sala"

            ws1.send_json(
                {"type": "chat.send", "payload": {"text": "secreto", "target_player_id": p2_id}}
            )
            ev = recv_until(ws2, "chat.message")
            assert ev["visibility"] == "private"

            # fin de turno rota al otro jugador
            ws_current.send_json({"type": "turn.end", "payload": {}})
            ev = recv_until(ws_other, "turn.started")
            assert ev["actor_id"] == target

    # historial persistido
    resp = client.get(f"/api/admin/games/{game['id']}/events", headers=ADMIN)
    types = [e["event_type"] for e in resp.json()["events"]]
    for expected in ("game.created", "player.joined", "game.started", "dice.rolled",
                     "attack.resolved", "chat.message", "turn.ended"):
        assert expected in types, f"falta {expected} en historial"

    # finalizar con resumen
    resp = client.post(f"/api/admin/games/{game['id']}/finish", json={}, headers=ADMIN)
    assert resp.status_code == 200
    assert resp.json()["summary"]["turns_played"] >= 2


def test_reconnection_keeps_session(client):
    game = create_game(client, config={"commentator_enabled": False})
    inv = invite(client, game["id"], "Nessi")
    invite(client, game["id"], "Daro")
    confirm_join(client, game["code"], inv["token"])

    with client.websocket_connect(f"/ws/{game['code']}?token={inv['token']}") as ws:
        recv_until(ws, "game.snapshot")
    # reconexión con el mismo token: sesión intacta, sin volver a confirmar
    with client.websocket_connect(f"/ws/{game['code']}?token={inv['token']}") as ws:
        snap = recv_until(ws, "game.snapshot")
        assert snap["payload"]["game"]["status"] == "lobby"


def test_kick_revokes_access(client):
    game = create_game(client, config={"commentator_enabled": False})
    inv = invite(client, game["id"], "Tramposo")
    confirm_join(client, game["code"], inv["token"])
    resp = client.post(
        f"/api/admin/games/{game['id']}/players/{inv['player']['id']}/kick", headers=ADMIN
    )
    assert resp.status_code == 200
    assert client.get(f"/api/join/{game['code']}/{inv['token']}").status_code == 404

    # regenerar le devuelve el acceso con un token nuevo
    resp = client.post(
        f"/api/admin/games/{game['id']}/players/{inv['player']['id']}/regenerate-token",
        headers=ADMIN,
    )
    new_token = resp.json()["token"]
    assert new_token != inv["token"]
    assert client.get(f"/api/join/{game['code']}/{new_token}").status_code == 200


def test_taunt_triggered_on_attack(client):
    game = create_game(client, config={"commentator_enabled": False})
    inv1 = invite(client, game["id"], "Nessi")
    inv2 = invite(client, game["id"], "Daro")
    p1, p2 = inv1["player"]["id"], inv2["player"]["id"]
    confirm_join(client, game["code"], inv1["token"])
    confirm_join(client, game["code"], inv2["token"])

    resp = client.post(
        f"/api/admin/games/{game['id']}/taunts",
        json={
            "owner_player_id": p1, "target_player_id": p2,
            "event_type": "attack.resolved",
            "asset_id": "audio/taunts/player-nessi/to-player-daro/attack-resolved-001.ogg",
        },
        headers=ADMIN,
    )
    assert resp.status_code == 200

    with client.websocket_connect(f"/ws/{game['code']}?token={inv1['token']}") as ws1, \
         client.websocket_connect(f"/ws/{game['code']}?token={inv2['token']}") as ws2:
        recv_until(ws1, "game.snapshot")
        recv_until(ws2, "game.snapshot")
        client.post(f"/api/admin/games/{game['id']}/start", headers=ADMIN)
        turn = recv_until(ws1, "turn.started")
        if turn["actor_id"] != p1:
            # cede el turno para que ataque quien tiene el taunt configurado
            ws2.send_json({"type": "turn.end", "payload": {}})
            recv_until(ws1, "turn.started")
        ws1.send_json({"type": "attack", "payload": {"target_player_id": p2, "attacker_dice": 3}})
        ev = recv_until(ws1, "taunt.triggered")
        assert ev["payload"]["audio_asset_id"].startswith("audio/taunts/")
        assert ev["payload"]["source_event_type"] == "attack.resolved"
