"""Un jugador ausente no debe trabar la mesa; uno presente no debe ser apurado."""

import time

import pytest
from fastapi.testclient import TestClient

from conftest import ADMIN, complete_placement, confirm_join, create_game, invite, recv_until
from teg_backend.config import Settings
from teg_backend.main import create_app


@pytest.fixture()
def client_turno_corto(tmp_path):
    """Igual al fixture client pero con el timeout de turno en 1 s."""
    settings = Settings(
        env="dev",
        db_path=str(tmp_path / "test.db"),
        admin_token="test-admin",
        commentator_provider="mock",
        commentator_cooldown_seconds=0.0,
        reconnect_grace_seconds=0.05,
        ai_player_think_seconds=0.01,
        turn_timeout_seconds=1.0,
        public_base_url="http://testserver",
    )
    with TestClient(create_app(settings)) as c:
        yield c


def _arrancar(client):
    game = create_game(client, config={"commentator_enabled": False})
    inv1 = invite(client, game["id"], "Uno")
    inv2 = invite(client, game["id"], "Dos")
    confirm_join(client, game["code"], inv1["token"])
    confirm_join(client, game["code"], inv2["token"])
    return game, inv1, inv2


def test_se_saltea_el_turno_de_un_jugador_desconectado(client_turno_corto):
    """Sin esto, si le toca a alguien que no esta, la mesa espera para siempre."""
    client = client_turno_corto
    game, inv1, inv2 = _arrancar(client)
    p1, p2 = inv1["player"]["id"], inv2["player"]["id"]

    with client.websocket_connect(f"/ws/{game['code']}?token={inv1['token']}") as ws1:
        recv_until(ws1, "game.snapshot")
        ws1.send_json({"type": "ready.set", "payload": {"ready": True}})
        recv_until(ws1, "player.ready")
        with client.websocket_connect(f"/ws/{game['code']}?token={inv2['token']}") as ws2:
            recv_until(ws2, "game.snapshot")
            ws2.send_json({"type": "ready.set", "payload": {"ready": True}})
            recv_until(ws1, "player.ready")
            recv_until(ws2, "player.ready")
            client.post(f"/api/admin/games/{game['id']}/start", headers=ADMIN)
            started = recv_until(ws1, "game.started")["payload"]
            recv_until(ws2, "game.started")
            complete_placement({p1: ws1, p2: ws2}, started)
            turn_ev = recv_until(ws1, "turn.started")
        # ws2 queda cerrado al salir del `with`: el jugador "Dos" esta ausente

        if turn_ev["actor_id"] == p1:
            # le toca al presente: cede el turno para que le llegue al ausente
            ws1.send_json({"type": "turn.end", "payload": {}})

        # si el turno le toca (o pasa a) al ausente, debe llegar turn.skipped
        evento = recv_until(ws1, "turn.skipped", max_msgs=80)
        assert evento["payload"]["player_id"] == p2
        assert evento["payload"]["reason"] == "offline"


def test_no_se_saltea_a_un_jugador_conectado_que_piensa(client_turno_corto):
    """El objetivo es destrabar ausencias, no apurar a nadie."""
    client = client_turno_corto
    game, inv1, inv2 = _arrancar(client)
    p1, p2 = inv1["player"]["id"], inv2["player"]["id"]

    with client.websocket_connect(f"/ws/{game['code']}?token={inv1['token']}") as ws1, \
         client.websocket_connect(f"/ws/{game['code']}?token={inv2['token']}") as ws2:
        recv_until(ws1, "game.snapshot")
        recv_until(ws2, "game.snapshot")
        ws1.send_json({"type": "ready.set", "payload": {"ready": True}})
        recv_until(ws1, "player.ready")
        recv_until(ws2, "player.ready")
        ws2.send_json({"type": "ready.set", "payload": {"ready": True}})
        recv_until(ws1, "player.ready")
        recv_until(ws2, "player.ready")
        client.post(f"/api/admin/games/{game['id']}/start", headers=ADMIN)
        started = recv_until(ws1, "game.started")["payload"]
        recv_until(ws2, "game.started")
        complete_placement({p1: ws1, p2: ws2}, started)
        recv_until(ws1, "turn.started")

        # ambos siguen conectados y no hacen nada: dejamos pasar mas del doble
        # del timeout de turno; nadie deberia ser salteado. Un ping al final
        # sirve de centinela para no bloquear leyendo mensajes que no llegan.
        time.sleep(2.5)
        ws1.send_json({"type": "ping"})
        vistos = []
        while True:
            msg = ws1.receive_json()
            if msg.get("type") == "pong":
                break
            vistos.append(msg.get("event_type"))
        assert "turn.skipped" not in vistos, "se salteo a un jugador conectado"
