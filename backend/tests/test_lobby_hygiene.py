"""Higiene de lobby: color unico, tope de invitados, join tardio, count minimo."""

import pytest

from conftest import ADMIN, confirm_join, create_game, invite


def test_no_se_repiten_colores(client):
    """En el incidente del 27/07, Seba y Gabi tenian los dos 'red'."""
    game = create_game(client)
    a = client.post(f"/api/admin/games/{game['id']}/players",
                    json={"nickname": "Seba", "color": "red"}, headers=ADMIN).json()
    b = client.post(f"/api/admin/games/{game['id']}/players",
                    json={"nickname": "Gabi", "color": "red"}, headers=ADMIN).json()
    assert a["player"]["color"] != b["player"]["color"]


def test_no_se_puede_invitar_por_encima_del_maximo(client):
    """El maximo se validaba recien en start_game, con la gente ya en el lobby.

    Los primeros 8 usan colores fuera de la paleta ("c0".."c7") para que el
    rechazo del noveno sea inequivocamente por tope y no porque se acabaron
    los colores de la paleta (que tambien tiene 8 valores).
    """
    game = create_game(client, config={"game_mode": "classic_26"})
    for i in range(8):
        resp = client.post(f"/api/admin/games/{game['id']}/players",
                            json={"nickname": f"j{i}", "color": f"c{i}"}, headers=ADMIN)
        assert resp.status_code == 200, resp.text
    resp = client.post(f"/api/admin/games/{game['id']}/players",
                       json={"nickname": "sobrante"}, headers=ADMIN)
    assert resp.status_code >= 400, "deberia rechazar al noveno jugador"


def test_no_se_puede_joinear_una_partida_ya_empezada(client):
    """Caso Gabi: joined_at NULL, la partida arranca sin el, y despues podia
    entrar y quedar sin territorios, sin objetivo y fuera del turn.order."""
    game = create_game(client, config={"commentator_enabled": False})
    a, b = invite(client, game["id"], "Uno"), invite(client, game["id"], "Dos")
    tarde = invite(client, game["id"], "Tarde")
    confirm_join(client, game["code"], a["token"])
    confirm_join(client, game["code"], b["token"])
    with client.websocket_connect(f"/ws/{game['code']}?token={a['token']}") as w1, \
         client.websocket_connect(f"/ws/{game['code']}?token={b['token']}") as w2:
        for w in (w1, w2):
            w.send_json({"type": "ready.set", "payload": {"ready": True}})
        client.post(f"/api/admin/games/{game['id']}/start", headers=ADMIN)

    resp = client.post(f"/api/join/{game['code']}/{tarde['token']}", json={})
    assert resp.status_code >= 400, "no deberia poder unirse con la partida en curso"


def test_no_se_pueden_colocar_refuerzos_negativos():
    """count negativo restaba ejercitos y SUMABA refuerzos."""
    from teg_backend.domain import engine as eng

    motor = eng.GameEngine(map_id="tactical-26")
    motor.start(["p1", "p2"])
    while motor.stage != "turns":
        for pid in ("p1", "p2"):
            mios = [t for t, x in motor.territories.items() if x.owner_player_id == pid]
            while motor.placement_pools.get(pid, 0) > 0:
                motor.place_initial(pid, mios[0], 1)

    actual = motor.turn.order[motor.turn.index % len(motor.turn.order)]
    disponibles = motor.turn.reinforcements_available
    mio = next(t for t, x in motor.territories.items() if x.owner_player_id == actual)
    with pytest.raises(Exception):
        motor.place_reinforcement(actual, mio, -5)
    assert motor.turn.reinforcements_available == disponibles
