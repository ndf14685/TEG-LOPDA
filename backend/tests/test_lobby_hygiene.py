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


def test_espectadores_y_admins_no_consumen_la_paleta_de_colores(client):
    """El chequeo de color unico es solo para roles que se sientan a jugar.

    Antes del fix, un espectador/admin invitado sin color se comia igual un
    color de la paleta (8 valores == max_players de classic_26): el primero
    en pedir "red" por defecto dejaba al octavo jugador sin colores libres.
    """
    game = create_game(client, config={"game_mode": "classic_26"})
    miron = invite(client, game["id"], "Miron", role="spectator")
    admin_invitado = invite(client, game["id"], "ElAnfitrion", role="admin")
    assert miron["player"]["color"] is None
    assert admin_invitado["player"]["color"] is None

    colores = []
    for i in range(8):
        resp = client.post(f"/api/admin/games/{game['id']}/players",
                            json={"nickname": f"j{i}"}, headers=ADMIN)
        assert resp.status_code == 200, resp.text
        colores.append(resp.json()["player"]["color"])
    assert len(set(colores)) == 8, "los 8 jugadores deben poder sentarse con colores unicos"


def test_se_puede_invitar_el_reemplazo_de_un_jugador_echado(client):
    """El caso que origino la fase: alguien no llega y hay que reemplazarlo.

    kick_player solo marca token_revoked; la fila del jugador sobrevive. El
    tope al invitar contaba esas filas (start_game si las excluye), asi que
    invitar al reemplazo daba 409 "la partida admite hasta 8 jugadores" y el
    anfitrion se quedaba sin salida.

    Los 8 usan colores fuera de la paleta para que el unico motivo posible de
    rechazo del reemplazo sea el tope.
    """
    game = create_game(client, config={"game_mode": "classic_26"})
    ids = []
    for i in range(8):
        resp = client.post(f"/api/admin/games/{game['id']}/players",
                           json={"nickname": f"j{i}", "color": f"c{i}"}, headers=ADMIN)
        assert resp.status_code == 200, resp.text
        ids.append(resp.json()["player"]["id"])

    echado = client.post(
        f"/api/admin/games/{game['id']}/players/{ids[3]}/kick", headers=ADMIN
    )
    assert echado.status_code == 200, echado.text

    reemplazo = client.post(f"/api/admin/games/{game['id']}/players",
                            json={"nickname": "Reemplazo"}, headers=ADMIN)
    assert reemplazo.status_code == 200, (
        f"no se pudo invitar al reemplazo de un echado: {reemplazo.text}"
    )


def test_un_espectador_con_color_no_bloquea_ese_color_para_los_jugadores(client):
    """El set `usados` no estaba acotado por rol: alcanzaba con que un
    espectador tuviera color para que ese color desapareciera de la paleta.
    Se afirma sobre el color concreto, no sobre el tamano de la paleta."""
    game = create_game(client, config={"game_mode": "classic_26"})
    miron = client.post(f"/api/admin/games/{game['id']}/players",
                        json={"nickname": "Miron", "role": "spectator", "color": "red"},
                        headers=ADMIN)
    assert miron.status_code == 200, miron.text

    colores = []
    for i in range(8):
        resp = client.post(f"/api/admin/games/{game['id']}/players",
                           json={"nickname": f"j{i}"}, headers=ADMIN)
        assert resp.status_code == 200, resp.text
        colores.append(resp.json()["player"]["color"])
    assert "red" in colores, (
        f"el espectador se quedo con 'red' y ningun jugador pudo usarlo: {colores}"
    )
    assert len(set(colores)) == 8


def test_un_espectador_invitado_desde_un_perfil_no_hereda_color(client):
    """Flujo normal: se invita a un amigo como espectador desde su perfil.
    `color = color or profile["color"]` corria para todos los roles, asi que
    el miron se quedaba con un color de la paleta sin sentarse a jugar."""
    game = create_game(client, config={"game_mode": "classic_26"})
    perfil = client.post("/api/admin/profiles",
                         json={"nickname": "Miron", "color": "red"},
                         headers=ADMIN).json()["profile"]
    resp = client.post(f"/api/admin/games/{game['id']}/players",
                       json={"role": "spectator", "profile_id": perfil["id"]},
                       headers=ADMIN)
    assert resp.status_code == 200, resp.text
    assert resp.json()["player"]["color"] is None


def test_ocho_jugadores_entran_con_un_espectador_de_perfil_presente(client):
    """Regresion end-to-end del incidente reproducido: espectador 'red' + 8
    jugadores -> el octavo recibia 409 'no quedan colores libres'."""
    game = create_game(client, config={"game_mode": "classic_26"})
    perfil = client.post("/api/admin/profiles",
                         json={"nickname": "Miron", "color": "red"},
                         headers=ADMIN).json()["profile"]
    client.post(f"/api/admin/games/{game['id']}/players",
                json={"role": "spectator", "profile_id": perfil["id"]}, headers=ADMIN)
    for i in range(8):
        resp = client.post(f"/api/admin/games/{game['id']}/players",
                           json={"nickname": f"j{i}"}, headers=ADMIN)
        assert resp.status_code == 200, f"jugador {i}: {resp.text}"


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
