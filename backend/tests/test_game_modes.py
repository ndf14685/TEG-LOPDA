"""Contrato assets/contracts/game-init-schema.json: game_mode + map_assets."""

from conftest import ADMIN, create_game


def test_default_mode_is_classic_26(client):
    game = create_game(client)
    assert game["config"]["game_mode"] == "classic_26"
    assert game["config"]["map_assets"]["base_svg"] == "maps/base/map-base-tactical-26-001.svg"


def test_classic_50_mode(client):
    game = create_game(client, config={"game_mode": "classic_50"})
    assert game["config"]["map_assets"]["base_svg"] == "maps/base/map-base-tactical-50-001.svg"


def test_mega_world_mode(client):
    game = create_game(client, config={"game_mode": "mega_world_100"})
    assert game["config"]["map_assets"]["base_svg"] == "maps/base/map-base-tactical-100-001.svg"


def test_invalid_mode_rejected(client):
    resp = client.post(
        "/api/admin/games",
        json={"name": "x", "config": {"game_mode": "modo-inventado"}},
        headers=ADMIN,
    )
    assert resp.status_code == 422


def test_join_exposes_game_mode(client):
    from conftest import invite

    game = create_game(client, config={"commentator_enabled": False})
    inv = invite(client, game["id"], "Nessi")
    resp = client.get(f"/api/join/{game['code']}/{inv['token']}")
    body = resp.json()
    assert body["game"]["game_mode"] == "classic_26"
    assert body["game"]["map_assets"]["base_svg"].startswith("maps/base/")


def test_attack_blocked_outside_attack_phase(client):
    """El ataque territorial se rechaza durante la fase de refuerzos."""
    from conftest import ADMIN, complete_placement, confirm_join, invite, recv_until

    game = create_game(client, config={"commentator_enabled": False})
    inv1 = invite(client, game["id"], "A")
    inv2 = invite(client, game["id"], "B")
    confirm_join(client, game["code"], inv1["token"])
    confirm_join(client, game["code"], inv2["token"])
    p1, p2 = inv1["player"]["id"], inv2["player"]["id"]
    client.post(f"/api/admin/games/{game['id']}/start", headers=ADMIN)

    with client.websocket_connect(f"/ws/{game['code']}?token={inv1['token']}") as ws1, \
         client.websocket_connect(f"/ws/{game['code']}?token={inv2['token']}") as ws2:
        snap = recv_until(ws1, "game.snapshot")
        recv_until(ws2, "game.snapshot")
        # el snapshot lleva el estado completo de territorios con "id"
        # (contrato TS shared/contracts/src/map.ts) para pintar el mapa
        snap_terr = snap["payload"]["territories"]
        assert len(snap_terr) == 26
        assert all(td["id"] == tid for tid, td in snap_terr.items())
        assert snap["payload"]["stage"] == "placement_1"

        reveal = complete_placement({p1: ws1, p2: ws2}, {"territories": snap_terr})

        detail = client.get(f"/api/admin/games/{game['id']}", headers=ADMIN).json()
        state = detail["game"]["state"]
        assert state["turn"]["phase"] == "reinforcement"
        current = state["turn"]["order"][state["turn"]["index"]]
        territories = reveal["territories"]
        mine = next(t for t, d in territories.items() if d["owner_player_id"] == current)
        enemy = next(t for t, d in territories.items() if d["owner_player_id"] != current)
        ws = ws1 if p1 == current else ws2

        ws.send_json({"type": "attack", "payload": {
            "source_territory_id": mine, "target_territory_id": enemy, "attacker_dice": 3,
        }})
        err = recv_until(ws, "error")
        assert err["payload"]["code"] == "INVALID_ACTION"
        assert "fase" in err["payload"]["message"]
