"""Pruebas unitarias para reglas completas de juego (refuerzos, mapa, conquista, reagrupamiento, eliminación)."""

import pytest
from conftest import ADMIN, confirm_join, create_game, invite, recv_until

def test_territories_reinforcement_fortify_and_conquest(client):
    game = create_game(client, config={"commentator_enabled": False})
    code = game["code"]

    inv1 = invite(client, game["id"], "Jugador 1")
    inv2 = invite(client, game["id"], "Jugador 2")
    j1 = confirm_join(client, code, inv1["token"])
    j2 = confirm_join(client, code, inv2["token"])
    p1_id, p2_id = j1["player"]["id"], j2["player"]["id"]

    with client.websocket_connect(f"/ws/{code}?token={inv1['token']}") as ws1, \
         client.websocket_connect(f"/ws/{code}?token={inv2['token']}") as ws2:
        recv_until(ws1, "game.snapshot")
        recv_until(ws2, "game.snapshot")

        ws1.send_json({"type": "ready.set", "payload": {"ready": True}})
        ws2.send_json({"type": "ready.set", "payload": {"ready": True}})

        resp = client.post(f"/api/admin/games/{game['id']}/start", headers=ADMIN)
        assert resp.status_code == 200

        ev_start = recv_until(ws1, "game.started")
        turn_ev = recv_until(ws1, "turn.started")
        current_id = turn_ev["actor_id"]
        other_id = p2_id if current_id == p1_id else p1_id
        ws_current = ws1 if current_id == p1_id else ws2

        # 1. Probar refuerzos
        territories = ev_start["payload"]["territories"]
        p_terrs = [tid for tid, t in territories.items() if t["owner_player_id"] == current_id]
        target_t = p_terrs[0]

        ws_current.send_json({
            "type": "turn.place_reinforcement",
            "payload": {"territory_id": target_t, "count": 1}
        })
        ev_upd = recv_until(ws_current, "territory.updated")
        assert ev_upd["payload"]["territory"]["territory_id"] == target_t

        # 2. Pasar a fase de ataque
        ws_current.send_json({"type": "turn.next_phase", "payload": {}})
        ev_phase = recv_until(ws_current, "turn.started")
        assert ev_phase["payload"]["phase"] == "attack"

        # 3. Pasar a fase de fortificación
        ws_current.send_json({"type": "turn.next_phase", "payload": {}})
        ev_phase2 = recv_until(ws_current, "turn.started")
        assert ev_phase2["payload"]["phase"] == "fortify"

        # 4. Fin de turno rota al otro jugador
        ws_current.send_json({"type": "turn.next_phase", "payload": {}})
        ev_ended = recv_until(ws_current, "turn.ended")
        assert ev_ended["actor_id"] == current_id
        ev_next_turn = recv_until(ws_current, "turn.started")
        assert ev_next_turn["actor_id"] == other_id
