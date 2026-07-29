"""Criterio de aceptacion de la Fase 0: ocho jugadores, cero desincronizaciones.

Hasta hoy el maximo probado eran DOS conexiones WebSocket simultaneas
(test_game_flow.py:164-165), cuatro veces menos que el objetivo.

El incidente del 27/07 se disparaba en los primeros 400 ms tras game.started,
asi que la ventana critica que cubre este test es exactamente el arranque.
"""

import contextlib

from conftest import ADMIN, confirm_join, create_game, invite, recv_until

JUGADORES = 8


def _armar_partida_de_ocho(client):
    game = create_game(client, config={"commentator_enabled": False, "mode": "classic_26"})
    invs = [invite(client, game["id"], f"j{i}") for i in range(JUGADORES)]
    for inv in invs:
        confirm_join(client, game["code"], inv["token"])
    return game, invs


def test_ocho_jugadores_arrancan_sin_huecos_de_secuencia(client):
    game, invs = _armar_partida_de_ocho(client)

    with contextlib.ExitStack() as stack:
        wss = [
            stack.enter_context(
                client.websocket_connect(f"/ws/{game['code']}?token={inv['token']}")
            )
            for inv in invs
        ]
        for ws in wss:
            recv_until(ws, "game.snapshot")
            ws.send_json({"type": "ready.set", "payload": {"ready": True}})

        resp = client.post(f"/api/admin/games/{game['id']}/start", headers=ADMIN)
        assert resp.status_code == 200, resp.text

        for i, ws in enumerate(wss):
            seqs = []
            for _ in range(150):
                msg = ws.receive_json()
                seq = msg.get("sequence_number", 0)
                if seq > 0:
                    seqs.append(seq)
                if msg.get("event_type") == "placement.started":
                    break

            assert seqs, f"jugador {i}: no recibio ningun evento persistido"
            huecos = [(a, b) for a, b in zip(seqs, seqs[1:]) if b != a + 1]
            assert not huecos, (
                f"jugador {i}: huecos de secuencia {huecos}. "
                "Quedo algun evento persistido no publico consumiendo public_sequence."
            )


def test_los_ocho_reciben_el_objetivo_y_el_arranque(client):
    """Cada jugador debe recibir SU objetivo privado y los eventos publicos."""
    game, invs = _armar_partida_de_ocho(client)

    with contextlib.ExitStack() as stack:
        wss = [
            stack.enter_context(
                client.websocket_connect(f"/ws/{game['code']}?token={inv['token']}")
            )
            for inv in invs
        ]
        for ws in wss:
            recv_until(ws, "game.snapshot")
            ws.send_json({"type": "ready.set", "payload": {"ready": True}})
        client.post(f"/api/admin/games/{game['id']}/start", headers=ADMIN)

        for i, ws in enumerate(wss):
            objetivo = recv_until(ws, "objective.assigned", max_msgs=80)
            assert objetivo["payload"]["objective"]["title"], f"jugador {i} sin objetivo"
            recv_until(ws, "placement.started", max_msgs=80)
