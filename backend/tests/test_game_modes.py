"""Contrato assets/contracts/game-init-schema.json: game_mode + map_assets."""

from conftest import ADMIN, create_game


def test_default_mode_is_classic_50(client):
    game = create_game(client)
    assert game["config"]["game_mode"] == "classic_50"
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
    assert body["game"]["game_mode"] == "classic_50"
    assert body["game"]["map_assets"]["base_svg"].startswith("maps/base/")


def test_attack_blocked_outside_attack_phase(client):
    """El ataque territorial se rechaza durante la fase de refuerzos."""
    from conftest import ADMIN, confirm_join, invite

    game = create_game(client, config={"commentator_enabled": False})
    inv1 = invite(client, game["id"], "A")
    inv2 = invite(client, game["id"], "B")
    confirm_join(client, game["code"], inv1["token"])
    confirm_join(client, game["code"], inv2["token"])
    client.post(f"/api/admin/games/{game['id']}/start", headers=ADMIN)

    detail = client.get(f"/api/admin/games/{game['id']}", headers=ADMIN).json()
    state = detail["game"]["state"]
    assert state["turn"]["phase"] == "reinforcement"
    current = state["turn"]["order"][state["turn"]["index"]]
    territories = state["territories"]
    mine = next(t for t, d in territories.items() if d["owner_player_id"] == current)
    enemy = next(t for t, d in territories.items() if d["owner_player_id"] != current)
    token = inv1["token"] if inv1["player"]["id"] == current else inv2["token"]

    with client.websocket_connect(f"/ws/{game['code']}?token={token}") as ws:
        from conftest import recv_until

        recv_until(ws, "game.snapshot")
        ws.send_json({"type": "attack", "payload": {
            "source_territory_id": mine, "target_territory_id": enemy, "attacker_dice": 3,
        }})
        err = recv_until(ws, "error")
        assert err["payload"]["code"] == "INVALID_ACTION"
        assert "fase" in err["payload"]["message"]
