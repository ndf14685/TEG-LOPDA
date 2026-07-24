"""Pactos de no agresión: propuesta, respuesta, ruptura y traición al atacar."""

from conftest import (
    ADMIN, complete_placement, confirm_join, create_game, invite, recv_until,
)


def test_pact_flow_and_betrayal(client):
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
        reveal = complete_placement({p1: ws1, p2: ws2}, started)
        assert reveal["next_stage"] == "turns"
        turn_ev = recv_until(ws1, "turn.started")
        current = turn_ev["actor_id"]

        # propuesta y aceptación
        ws1.send_json({"type": "pact.propose", "payload": {"target_player_id": p2}})
        ev = recv_until(ws2, "pact.proposed")
        assert ev["actor_id"] == p1 and ev["target_id"] == p2
        ws2.send_json({"type": "pact.respond", "payload": {"accept": True}})
        ev = recv_until(ws1, "pact.accepted")
        assert ev["actor_id"] == p2 and ev["target_id"] == p1

        # doble propuesta con pacto vigente: rechazada
        ws1.send_json({"type": "pact.propose", "payload": {"target_player_id": p2}})
        err = recv_until(ws1, "error")
        assert err["payload"]["code"] == "INVALID_ACTION"

        # traición: atacar al aliado rompe el pacto públicamente
        ws_c = ws1 if current == p1 else ws2
        other = p2 if current == p1 else p1
        ws_c.send_json({"type": "attack", "payload": {
            "target_player_id": other, "attacker_dice": 3,
        }})
        ev = recv_until(ws_c, "pact.broken")
        assert ev["payload"]["betrayal"] is True
        assert ev["actor_id"] == current and ev["target_id"] == other
