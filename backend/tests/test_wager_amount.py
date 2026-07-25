"""DEF-02: el monto de apuesta aceptado por el server = el solicitado."""

from conftest import (
    ADMIN, complete_placement, confirm_join, create_game, invite, recv_until,
)


def test_wager_accepts_exact_requested_amount(client):
    game = create_game(client, config={"commentator_enabled": False})
    inv1 = invite(client, game["id"], "Daro")
    inv2 = invite(client, game["id"], "Lord")
    confirm_join(client, game["code"], inv1["token"])
    confirm_join(client, game["code"], inv2["token"])
    p1, p2 = inv1["player"]["id"], inv2["player"]["id"]

    with client.websocket_connect(f"/ws/{game['code']}?token={inv1['token']}") as ws1, \
         client.websocket_connect(f"/ws/{game['code']}?token={inv2['token']}") as ws2:
        recv_until(ws1, "game.snapshot"); recv_until(ws2, "game.snapshot")
        ws1.send_json({"type": "ready.set", "payload": {"ready": True}})
        recv_until(ws1, "player.ready"); recv_until(ws2, "player.ready")
        ws2.send_json({"type": "ready.set", "payload": {"ready": True}})
        recv_until(ws1, "player.ready"); recv_until(ws2, "player.ready")
        client.post(f"/api/admin/games/{game['id']}/start", headers=ADMIN)
        started = recv_until(ws1, "game.started")["payload"]
        recv_until(ws2, "game.started")
        complete_placement({p1: ws1, p2: ws2}, started)

        turn_ev = recv_until(ws1, "turn.started")
        ws_c = ws1 if turn_ev["actor_id"] == p1 else ws2
        avail = turn_ev["payload"]["reinforcements_available"]
        assert avail >= 3, "el primer turno canónico siempre da ≥3 refuerzos"

        # pedir +3 → el evento wager.placed debe acreditar exactamente 3
        ws_c.send_json({"type": "turn.wager", "payload": {"amount": 3}})
        ev = recv_until(ws_c, "wager.placed")
        assert ev["payload"]["wager"] == 3, f"pedido 3, aceptado {ev['payload']['wager']}"
        assert ev["payload"]["turn"]["wager"] == 3
        assert ev["payload"]["turn"]["reinforcements_available"] == avail - 3

        # apuesta acumulativa: +1 encima → total 4
        ws_c.send_json({"type": "turn.wager", "payload": {"amount": 1}})
        ev = recv_until(ws_c, "wager.placed")
        assert ev["payload"]["wager"] == 4
