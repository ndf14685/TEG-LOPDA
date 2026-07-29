"""Tope de conexiones por jugador y saludos de bienvenida lineales."""

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


def test_saludos_de_bienvenida_no_son_cuadraticos(client):
    """El doble bucle daba 56 emisiones con 8 jugadores, dentro del lock de
    start_game y justo cuando los clientes estan renderizando el mapa."""
    game = create_game(client, config={"commentator_enabled": False})
    invs = [invite(client, game["id"], f"j{i}") for i in range(8)]
    for inv in invs:
        confirm_join(client, game["code"], inv["token"])

    with client.websocket_connect(f"/ws/{game['code']}?token={invs[0]['token']}") as ws:
        recv_until(ws, "game.snapshot")
        for inv in invs:
            with client.websocket_connect(f"/ws/{game['code']}?token={inv['token']}") as w:
                recv_until(w, "game.snapshot")
                w.send_json({"type": "ready.set", "payload": {"ready": True}})
        client.post(f"/api/admin/games/{game['id']}/start", headers=ADMIN)

        saludos = 0
        for _ in range(120):
            msg = ws.receive_json()
            if msg.get("event_type") == "taunt.triggered":
                saludos += 1
            if msg.get("event_type") == "placement.started":
                break
        assert saludos <= 8, f"se dispararon {saludos} saludos, esperabamos <= 8"


def test_saludos_de_bienvenida_invocan_fire_taunt_linealmente(client, monkeypatch):
    """Prueba de precisión: cuenta invocaciones reales de _fire_taunt para el
    evento GAME_STARTED, sin depender de que los perfiles tengan audio.

    El doble bucle original invocaba _fire_taunt una vez por PAR ordenado
    (n*(n-1), 56 con 8 jugadores). El arreglo debe invocarlo a lo sumo una vez
    por jugador sentado (<= 8). Los jugadores necesitan profile_id (perfil
    asociado) para entrar en el filtro `seated` de _after_emit; si no, tanto
    el bucle viejo como el nuevo disparan 0 llamadas y el test no distingue
    nada."""
    game = create_game(client, config={"commentator_enabled": False})
    profiles = [
        client.post("/api/admin/profiles", json={"nickname": f"perfil{i}"}, headers=ADMIN).json()["profile"]
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

    service = client.app.state.service
    original = service._fire_taunt
    llamadas_game_started = []

    async def _contador(game_id, players, actor_id, target_id, event_type, source_event_id):
        if str(event_type) == "game.started" or getattr(event_type, "value", None) == "game.started":
            llamadas_game_started.append((actor_id, target_id))
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

    assert len(llamadas_game_started) <= 8, (
        f"_fire_taunt se invoco {len(llamadas_game_started)} veces para "
        f"game.started, esperabamos <= 8 (antes eran 56 con 8 jugadores)"
    )
