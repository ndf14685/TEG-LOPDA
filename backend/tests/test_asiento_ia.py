"""Convertir un asiento a IA tiene que ser reversible.

convert_seat_to_ai promete en su docstring que "su link sigue siendo valido y
al volver a entrar recupera el asiento". Esa restauracion vivia en
confirm_join DESPUES del guard que rechaza todo lo que no este en
PRE_START_STATUSES, asi que con la partida en RUNNING era codigo inalcanzable:
el jugador se conectaba igual por WebSocket y miraba a un bot jugar su
asiento, sin error y sin explicacion.
"""

from __future__ import annotations

from conftest import ADMIN, confirm_join, create_game, invite, recv_until


def _arrancar_partida_de_dos(client):
    game = create_game(client, config={"commentator_enabled": False})
    uno = invite(client, game["id"], "Uno")
    dos = invite(client, game["id"], "Dos")
    confirm_join(client, game["code"], uno["token"])
    confirm_join(client, game["code"], dos["token"])
    with client.websocket_connect(f"/ws/{game['code']}?token={uno['token']}") as w1, \
         client.websocket_connect(f"/ws/{game['code']}?token={dos['token']}") as w2:
        recv_until(w1, "game.snapshot")
        recv_until(w2, "game.snapshot")
        for w in (w1, w2):
            w.send_json({"type": "ready.set", "payload": {"ready": True}})
        recv_until(w1, "player.ready")
        recv_until(w1, "player.ready")
        resp = client.post(f"/api/admin/games/{game['id']}/start", headers=ADMIN)
        assert resp.status_code == 200, resp.text
        recv_until(w1, "game.started")
        recv_until(w2, "game.started")
    return game, uno, dos


def test_el_asiento_convertido_a_ia_se_recupera_con_la_partida_en_curso(client):
    """El caso real: alguien se cae, el anfitrion pone un bot en su asiento, y
    despues la persona vuelve con el mismo link."""
    game, _uno, dos = _arrancar_partida_de_dos(client)
    pid = dos["player"]["id"]

    convertir = client.post(
        f"/api/admin/games/{game['id']}/players/{pid}/convert-to-ai", headers=ADMIN
    )
    assert convertir.status_code == 200, convertir.text

    vuelta = client.post(f"/api/join/{game['code']}/{dos['token']}", json={})
    assert vuelta.status_code == 200, (
        f"el jugador no pudo recuperar su asiento convertido a IA: {vuelta.text}"
    )
    assert vuelta.json()["player"]["role"] == "player"

    # y el cambio quedo persistido, no solo en la respuesta
    jugadores = client.get(
        f"/api/admin/games/{game['id']}", headers=ADMIN
    ).json()["players"]
    assert next(p for p in jugadores if p["id"] == pid)["role"] == "player"


def test_el_guard_sigue_rechazando_a_quien_nunca_se_unio(client):
    """La reapertura no debe abrir el join a quien nunca entro: sin joined_at
    no hay asiento que recuperar (ni territorios, ni objetivo, ni turn.order),
    que es el caso Gabi que motivo el guard."""
    game = create_game(client, config={"commentator_enabled": False})
    uno = invite(client, game["id"], "Uno")
    dos = invite(client, game["id"], "Dos")
    tarde = invite(client, game["id"], "Tarde")
    confirm_join(client, game["code"], uno["token"])
    confirm_join(client, game["code"], dos["token"])

    # el anfitrion convierte en bot el asiento del que nunca aparecio
    convertir = client.post(
        f"/api/admin/games/{game['id']}/players/{tarde['player']['id']}/convert-to-ai",
        headers=ADMIN,
    )
    assert convertir.status_code == 200, convertir.text

    with client.websocket_connect(f"/ws/{game['code']}?token={uno['token']}") as w1, \
         client.websocket_connect(f"/ws/{game['code']}?token={dos['token']}") as w2:
        recv_until(w1, "game.snapshot")
        recv_until(w2, "game.snapshot")
        for w in (w1, w2):
            w.send_json({"type": "ready.set", "payload": {"ready": True}})
        recv_until(w1, "player.ready")
        recv_until(w1, "player.ready")
        assert client.post(
            f"/api/admin/games/{game['id']}/start", headers=ADMIN
        ).status_code == 200
        recv_until(w1, "game.started")

    resp = client.post(f"/api/join/{game['code']}/{tarde['token']}", json={})
    assert resp.status_code >= 400, "no deberia poder unirse quien nunca se sento"


def test_al_volver_el_humano_se_desagenda_el_bot_de_su_asiento(client):
    """Si el turno era del asiento convertido, recuperar el asiento tiene que
    cancelar la tarea del bot y devolverle el reloj al humano; si no, el bot
    sigue jugando el turno de alguien que ya volvio."""
    game, _uno, dos = _arrancar_partida_de_dos(client)
    pid = dos["player"]["id"]
    service = client.app.state.service
    engine = service._engines[game["id"]]
    # forzar que el turno sea del asiento que se va a convertir, en la fase de
    # turnos (la conversion solo agenda al bot bajo esa condicion)
    engine.stage = "turns"
    engine.turn.order = [pid, _uno["player"]["id"]]
    engine.turn.index = 0

    assert client.post(
        f"/api/admin/games/{game['id']}/players/{pid}/convert-to-ai", headers=ADMIN
    ).status_code == 200
    assert f"{game['id']}:{pid}" in service._ai_tasks

    assert client.post(
        f"/api/join/{game['code']}/{dos['token']}", json={}
    ).status_code == 200
    assert f"{game['id']}:{pid}" not in service._ai_tasks, (
        "el bot sigue agendado sobre el asiento que el humano ya recupero"
    )
    assert game["id"] in service._turn_timers, (
        "el humano recupero el asiento pero se quedo sin reloj de turno"
    )
