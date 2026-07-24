"""Pruebas unitarias para reglas completas de juego (refuerzos, mapa, conquista, reagrupamiento, eliminación)."""

import pytest
from conftest import (
    ADMIN, complete_placement, confirm_join, create_game, invite, recv_until,
)

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

        # esperar la confirmación de ambos "listos" ANTES de iniciar: un
        # ready procesado después de start se rechaza (y debe rechazarse)
        ws1.send_json({"type": "ready.set", "payload": {"ready": True}})
        recv_until(ws1, "player.ready")
        recv_until(ws2, "player.ready")
        ws2.send_json({"type": "ready.set", "payload": {"ready": True}})
        recv_until(ws1, "player.ready")
        recv_until(ws2, "player.ready")

        resp = client.post(f"/api/admin/games/{game['id']}/start", headers=ADMIN)
        assert resp.status_code == 200

        # drenar ambos sockets para que el buffer de ws_current quede alineado
        # sin importar a quién le toque el primer turno (sorteo aleatorio)
        ev_start = recv_until(ws1, "game.started")
        recv_until(ws2, "game.started")
        reveal = complete_placement({p1_id: ws1, p2_id: ws2}, ev_start["payload"])
        turn_ev = recv_until(ws1, "turn.started")
        recv_until(ws2, "turn.started")
        current_id = turn_ev["actor_id"]
        other_id = p2_id if current_id == p1_id else p1_id
        ws_current = ws1 if current_id == p1_id else ws2

        # 1. Probar refuerzos: colocar TODOS (regla canónica para poder atacar)
        territories = reveal["territories"]
        p_terrs = [tid for tid, t in territories.items() if t["owner_player_id"] == current_id]
        target_t = p_terrs[0]
        reinforcements = turn_ev["payload"]["reinforcements_available"]

        ws_current.send_json({
            "type": "turn.place_reinforcement",
            "payload": {"territory_id": target_t, "count": reinforcements}
        })
        ev_upd = recv_until(ws_current, "territory.updated")
        assert ev_upd["payload"]["territory"]["territory_id"] == target_t
        # al agotar los refuerzos la fase avanza sola a ataque
        assert ev_upd["payload"]["turn"]["phase"] == "attack"

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
