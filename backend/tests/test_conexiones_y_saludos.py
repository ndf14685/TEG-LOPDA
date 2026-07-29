"""Tope de conexiones por jugador y saludos de bienvenida lineales."""

import asyncio
import time

from conftest import ADMIN, confirm_join, create_game, invite, recv_until

from teg_backend.realtime.manager import MAX_SOCKETS_POR_JUGADOR, ConnectionManager


class SocketFalso:
    def __init__(self, n): self.n = n; self.cerrado = False
    async def send_json(self, payload): pass
    async def close(self, code=1000): self.cerrado = True


def test_tope_de_pestanas_por_jugador():
    """Sin tope, cada pestaña extra multiplicaba el fan-out de cada evento."""
    manager = ConnectionManager()
    room = manager.room("g1")
    sockets = [SocketFalso(i) for i in range(MAX_SOCKETS_POR_JUGADOR + 1)]
    desalojados = []
    for s in sockets:
        desalojados.extend(room.add("jugador", s))

    assert len(room.sockets["jugador"]) == MAX_SOCKETS_POR_JUGADOR
    # se desaloja la mas vieja, no se rechaza la nueva: reconectar nunca debe fallar
    assert sockets[0] in desalojados
    assert sockets[-1] in room.sockets["jugador"]


def _partida_de_ocho_con_perfiles(client):
    """Ocho jugadores con perfil asociado, unidos y listos.

    Los jugadores necesitan profile_id para entrar en el filtro `seated` del
    fan-out de saludos; sin perfil no se dispara ninguna llamada y cualquier
    conteo da 0 con y sin el bug.
    """
    game = create_game(client, config={"commentator_enabled": False})
    profiles = [
        client.post("/api/admin/profiles", json={"nickname": f"perfil{i}"},
                    headers=ADMIN).json()["profile"]
        for i in range(8)
    ]
    invs = []
    for i in range(8):
        resp = client.post(
            f"/api/admin/games/{game['id']}/players",
            json={"nickname": f"j{i}", "role": "player", "profile_id": profiles[i]["id"]},
            headers=ADMIN,
        )
        assert resp.status_code == 200, resp.text
        invs.append(resp.json())
    for inv in invs:
        confirm_join(client, game["code"], inv["token"])
    return game, invs


def test_los_saludos_de_bienvenida_son_lineales_y_cada_uno_a_su_rival(client, monkeypatch):
    """Cuenta invocaciones reales de _fire_taunt para GAME_STARTED.

    El doble bucle original invocaba _fire_taunt una vez por PAR ordenado
    (n*(n-1), 56 con 8 jugadores); el arreglo lo invoca a lo sumo una vez por
    jugador sentado. Ademas la version anterior elegia siempre "el primer
    jugador sentado" como rival, asi que con 8 jugadores seis de ocho nunca
    disparaban su saludo real contra su rival: por eso tambien se afirma que
    los ocho rivales son distintos.
    """
    game, invs = _partida_de_ocho_con_perfiles(client)
    service = client.app.state.service
    original = service._fire_taunt
    llamadas: list[tuple[str, str]] = []

    async def _contador(game_id, players, actor_id, target_id, event_type, source_event_id):
        if str(event_type) == "game.started":
            llamadas.append((actor_id, target_id))
        return await original(game_id, players, actor_id, target_id, event_type, source_event_id)

    monkeypatch.setattr(service, "_fire_taunt", _contador)

    with client.websocket_connect(f"/ws/{game['code']}?token={invs[0]['token']}") as ws:
        recv_until(ws, "game.snapshot")
        for inv in invs[1:]:
            with client.websocket_connect(f"/ws/{game['code']}?token={inv['token']}") as w:
                recv_until(w, "game.snapshot")
                w.send_json({"type": "ready.set", "payload": {"ready": True}})
        ws.send_json({"type": "ready.set", "payload": {"ready": True}})
        client.post(f"/api/admin/games/{game['id']}/start", headers=ADMIN)
        recv_until(ws, "placement.started")

    # el fan-out corre fuera del lock, en tarea aparte: esperar a que termine
    limite = time.monotonic() + 5.0
    while len(llamadas) < 8 and time.monotonic() < limite:
        time.sleep(0.02)

    assert len(llamadas) == 8, (
        f"_fire_taunt se invoco {len(llamadas)} veces para game.started, "
        f"esperabamos 8 (antes eran 56 con 8 jugadores)"
    )
    rivales = {target for _, target in llamadas}
    assert len(rivales) == 8, (
        f"solo {len(rivales)} rivales distintos entre 8 saludos: hay jugadores "
        f"que nunca disparan su saludo real contra su rival"
    )
    assert all(actor != target for actor, target in llamadas)


def test_el_fan_out_de_saludos_no_retiene_el_lock_de_start_game(client, monkeypatch):
    """El fan-out se awaiteaba dentro del `async with self.lock(game_id)` de
    start_game (emit -> _after_emit), asi que los ocho INSERT + broadcast de
    saludos retenian la partida entera justo cuando los ocho clientes estan
    renderizando el mapa.

    Se mide sobre el hecho observable: con un saludo artificialmente lento,
    el POST /start tiene que volver igual de rapido. Si el fan-out siguiera
    adentro del lock, la respuesta tardaria 8 * DEMORA.
    """
    DEMORA = 0.3
    game, invs = _partida_de_ocho_con_perfiles(client)
    service = client.app.state.service
    original = service._fire_taunt
    llamadas: list[tuple[str, str]] = []

    async def _lento(game_id, players, actor_id, target_id, event_type, source_event_id):
        if str(event_type) == "game.started":
            llamadas.append((actor_id, target_id))
            await asyncio.sleep(DEMORA)
        return await original(game_id, players, actor_id, target_id, event_type, source_event_id)

    monkeypatch.setattr(service, "_fire_taunt", _lento)

    with client.websocket_connect(f"/ws/{game['code']}?token={invs[0]['token']}") as ws:
        recv_until(ws, "game.snapshot")
        for inv in invs[1:]:
            with client.websocket_connect(f"/ws/{game['code']}?token={inv['token']}") as w:
                recv_until(w, "game.snapshot")
                w.send_json({"type": "ready.set", "payload": {"ready": True}})
        ws.send_json({"type": "ready.set", "payload": {"ready": True}})

        t0 = time.monotonic()
        resp = client.post(f"/api/admin/games/{game['id']}/start", headers=ADMIN)
        demora = time.monotonic() - t0
        assert resp.status_code == 200, resp.text

    assert demora < 8 * DEMORA / 2, (
        f"start_game tardo {demora:.2f}s con saludos de {DEMORA}s: el fan-out "
        f"sigue corriendo adentro del lock de la partida"
    )
    # y los saludos igual salen, solo que despues y sin frenar a nadie
    limite = time.monotonic() + 8.0
    while len(llamadas) < 8 and time.monotonic() < limite:
        time.sleep(0.02)
    assert len(llamadas) == 8
