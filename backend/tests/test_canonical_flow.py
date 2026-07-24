"""Flujo canónico completo por WS: colocación 5+3, objetivos, canje bloqueado."""

from conftest import ADMIN, confirm_join, create_game, invite, recv_until


def _setup_two_players(client):
    game = create_game(client, config={"commentator_enabled": False})
    inv1 = invite(client, game["id"], "Daro")
    inv2 = invite(client, game["id"], "Lord")
    confirm_join(client, game["code"], inv1["token"])
    confirm_join(client, game["code"], inv2["token"])
    return game, inv1, inv2


def _drain_ready_and_start(client, game, ws1, ws2):
    ws1.send_json({"type": "ready.set", "payload": {"ready": True}})
    recv_until(ws1, "player.ready")
    recv_until(ws2, "player.ready")
    ws2.send_json({"type": "ready.set", "payload": {"ready": True}})
    recv_until(ws1, "player.ready")
    recv_until(ws2, "player.ready")
    resp = client.post(f"/api/admin/games/{game['id']}/start", headers=ADMIN)
    assert resp.status_code == 200, resp.text


def test_full_placement_then_first_turn(client):
    game, inv1, inv2 = _setup_two_players(client)
    with client.websocket_connect(f"/ws/{game['code']}?token={inv1['token']}") as ws1, \
         client.websocket_connect(f"/ws/{game['code']}?token={inv2['token']}") as ws2:
        you1 = recv_until(ws1, "game.snapshot")["payload"]["you"]
        you2 = recv_until(ws2, "game.snapshot")["payload"]["you"]
        _drain_ready_and_start(client, game, ws1, ws2)

        started = recv_until(ws1, "game.started")["payload"]
        recv_until(ws2, "game.started")
        assert started["stage"] == "placement_1"
        obj1 = recv_until(ws1, "objective.assigned")
        assert obj1["payload"]["objective"]["title"]
        recv_until(ws2, "objective.assigned")
        recv_until(ws1, "placement.started")
        recv_until(ws2, "placement.started")

        territories = started["territories"]

        def own(pid):
            return next(t for t, d in territories.items() if d["owner_player_id"] == pid)

        # ronda 1: 5 ejércitos cada uno, ocultos hasta que ambos terminan
        ws1.send_json({"type": "placement.place",
                       "payload": {"territory_id": own(you1), "count": 5}})
        upd = recv_until(ws1, "placement.updated")
        assert upd["payload"]["remaining"] == 0
        ws2.send_json({"type": "placement.place",
                       "payload": {"territory_id": own(you2), "count": 5}})
        reveal = recv_until(ws1, "placement.revealed")
        assert reveal["payload"]["next_stage"] == "placement_2"
        recv_until(ws2, "placement.revealed")
        # lo colocado se aplicó recién en la revelación
        assert reveal["payload"]["territories"][own(you1)]["armies"] == 6

        # ronda 2: 3 ejércitos cada uno
        ws1.send_json({"type": "placement.place",
                       "payload": {"territory_id": own(you1), "count": 3}})
        ws2.send_json({"type": "placement.place",
                       "payload": {"territory_id": own(you2), "count": 3}})
        reveal2 = recv_until(ws1, "placement.revealed")
        assert reveal2["payload"]["next_stage"] == "turns"
        recv_until(ws2, "placement.revealed")

        turn_ev = recv_until(ws1, "turn.started")
        assert turn_ev["payload"]["reinforcements_available"] >= 3
        ws_current = ws1 if turn_ev["actor_id"] == you1 else ws2
        legal = recv_until(ws_current, "legal.actions")
        acts = {a["action"] for a in legal["payload"]["actions"]}
        assert "turn.place_reinforcement" in acts


def test_placement_rejects_foreign_territory(client):
    game, inv1, inv2 = _setup_two_players(client)
    with client.websocket_connect(f"/ws/{game['code']}?token={inv1['token']}") as ws1, \
         client.websocket_connect(f"/ws/{game['code']}?token={inv2['token']}") as ws2:
        you1 = recv_until(ws1, "game.snapshot")["payload"]["you"]
        recv_until(ws2, "game.snapshot")
        _drain_ready_and_start(client, game, ws1, ws2)
        started = recv_until(ws1, "game.started")["payload"]
        enemy_t = next(t for t, d in started["territories"].items()
                       if d["owner_player_id"] != you1)
        ws1.send_json({"type": "placement.place",
                       "payload": {"territory_id": enemy_t, "count": 1}})
        err = recv_until(ws1, "error")
        assert err["payload"]["code"] == "INVALID_ACTION"


def test_trade_rejected_without_cards(client):
    game, inv1, inv2 = _setup_two_players(client)
    with client.websocket_connect(f"/ws/{game['code']}?token={inv1['token']}") as ws1, \
         client.websocket_connect(f"/ws/{game['code']}?token={inv2['token']}") as ws2:
        recv_until(ws1, "game.snapshot")
        recv_until(ws2, "game.snapshot")
        _drain_ready_and_start(client, game, ws1, ws2)
        ws1.send_json({"type": "cards.trade", "payload": {"card_ids": ["a", "b", "c"]}})
        err = recv_until(ws1, "error")
        assert err["payload"]["code"] in ("INVALID_ACTION", "NOT_YOUR_TURN")


def test_snapshot_includes_stage_and_objective_after_start(client):
    game, inv1, inv2 = _setup_two_players(client)
    with client.websocket_connect(f"/ws/{game['code']}?token={inv1['token']}") as ws1, \
         client.websocket_connect(f"/ws/{game['code']}?token={inv2['token']}") as ws2:
        recv_until(ws1, "game.snapshot")
        recv_until(ws2, "game.snapshot")
        _drain_ready_and_start(client, game, ws1, ws2)
        recv_until(ws1, "game.started")
    # reconexión: el snapshot trae stage, colocación pendiente y objetivo
    with client.websocket_connect(f"/ws/{game['code']}?token={inv1['token']}") as ws:
        snap = recv_until(ws, "game.snapshot")["payload"]
        assert snap["stage"] == "placement_1"
        assert snap["placement"]["remaining"] == 5
        assert snap["your_objective"]["title"]
