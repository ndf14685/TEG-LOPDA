"""Replay paso a paso: snapshots por turno + eventos del turno."""

import time

from conftest import ADMIN, create_game, invite


def test_replay_of_finished_bot_game(client):
    game = create_game(client, config={"commentator_enabled": False})
    inv_h = invite(client, game["id"], "Mirón", role="spectator")
    for name in ("BotA", "BotB"):
        invite(client, game["id"], name, role="ai_player")
    resp = client.post(f"/api/admin/games/{game['id']}/start", headers=ADMIN)
    assert resp.status_code == 200, resp.text

    deadline = time.time() + 120
    while time.time() < deadline:
        detail = client.get(f"/api/admin/games/{game['id']}", headers=ADMIN).json()
        if detail["game"]["status"] == "finished":
            break
        time.sleep(0.3)
    assert detail["game"]["status"] == "finished"

    code, token = game["code"], inv_h["token"]
    index = client.get(f"/api/join/{code}/{token}/replay").json()
    assert index["turns"], "toda partida jugada deja snapshots por turno"
    assert index["turns"] == sorted(index["turns"])

    first = index["turns"][0]
    turn = client.get(f"/api/join/{code}/{token}/replay/{first}").json()
    assert turn["territories"], "el snapshot trae el mapa completo del turno"
    types = {e["event_type"] for e in turn["events"]}
    assert "turn.started" in types

    # un turno inexistente da 404 y un token falso también
    assert client.get(f"/api/join/{code}/{token}/replay/99999").status_code == 404
    assert client.get(f"/api/join/{code}/token-falso/replay").status_code == 404
