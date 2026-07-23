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
