"""La secuencia que ve el cliente no debe tener huecos por eventos privados.

Reproduce el incidente del 27/07 (partida wfqrwfrf): game.started con seq 13,
dos objective.assigned privados con seq 14 y 16, y ai.comment con seq 15.
Cada cliente veia un salto y se autodesconectaba.
"""

from conftest import ADMIN, confirm_join, create_game, invite, recv_until


def _partida_de_tres(client):
    game = create_game(client, config={"commentator_enabled": False})
    invs = [invite(client, game["id"], n) for n in ("Nes", "Seba", "Colo")]
    for inv in invs:
        confirm_join(client, game["code"], inv["token"])
    return game, invs


def _secuencias_persistidas(ws, cuantos=40):
    """Solo los persistidos (seq > 0) participan del stream ordenado."""
    seqs = []
    for _ in range(cuantos):
        msg = ws.receive_json()
        seq = msg.get("sequence_number", 0)
        if seq > 0:
            seqs.append(seq)
        if msg.get("event_type") == "placement.started":
            break
    return seqs


def test_el_arranque_no_deja_huecos_en_la_secuencia_del_cliente(client):
    game, invs = _partida_de_tres(client)
    with client.websocket_connect(f"/ws/{game['code']}?token={invs[0]['token']}") as ws1, \
         client.websocket_connect(f"/ws/{game['code']}?token={invs[1]['token']}") as ws2, \
         client.websocket_connect(f"/ws/{game['code']}?token={invs[2]['token']}") as ws3:
        for ws in (ws1, ws2, ws3):
            recv_until(ws, "game.snapshot")
        for ws in (ws1, ws2, ws3):
            ws.send_json({"type": "ready.set", "payload": {"ready": True}})
        for ws in (ws1, ws2, ws3):
            recv_until(ws, "player.ready")

        assert client.post(f"/api/admin/games/{game['id']}/start", headers=ADMIN).status_code == 200

        for i, ws in enumerate((ws1, ws2, ws3)):
            seqs = _secuencias_persistidas(ws)
            huecos = [(a, b) for a, b in zip(seqs, seqs[1:]) if b != a + 1]
            assert not huecos, f"jugador {i}: huecos de secuencia {huecos}"


def test_el_objetivo_privado_viaja_como_efimero(client):
    """seq 0 = el SeqTracker del frontend lo ignora (seqTracker.ts:11)."""
    game, invs = _partida_de_tres(client)
    with client.websocket_connect(f"/ws/{game['code']}?token={invs[0]['token']}") as ws1, \
         client.websocket_connect(f"/ws/{game['code']}?token={invs[1]['token']}") as ws2, \
         client.websocket_connect(f"/ws/{game['code']}?token={invs[2]['token']}") as ws3:
        for ws in (ws1, ws2, ws3):
            recv_until(ws, "game.snapshot")
            ws.send_json({"type": "ready.set", "payload": {"ready": True}})
        client.post(f"/api/admin/games/{game['id']}/start", headers=ADMIN)

        objetivo = recv_until(ws1, "objective.assigned")
        assert objetivo["sequence_number"] == 0


def test_el_historial_de_admin_conserva_todos_los_eventos(client):
    """La secuencia de almacenamiento sigue densa e incluye los privados."""
    game, invs = _partida_de_tres(client)
    with client.websocket_connect(f"/ws/{game['code']}?token={invs[0]['token']}") as ws1, \
         client.websocket_connect(f"/ws/{game['code']}?token={invs[1]['token']}") as ws2, \
         client.websocket_connect(f"/ws/{game['code']}?token={invs[2]['token']}") as ws3:
        for ws in (ws1, ws2, ws3):
            recv_until(ws, "game.snapshot")
            ws.send_json({"type": "ready.set", "payload": {"ready": True}})
        client.post(f"/api/admin/games/{game['id']}/start", headers=ADMIN)
        recv_until(ws1, "placement.started")

    eventos = client.get(f"/api/admin/games/{game['id']}/events", headers=ADMIN).json()["events"]
    tipos = [e["event_type"] for e in eventos]
    assert tipos.count("objective.assigned") == 3, "los privados deben quedar en el historial"
    seqs = [e["sequence_number"] for e in eventos]
    assert seqs == sorted(seqs) and len(set(seqs)) == len(seqs)
