"""Rehidratacion de turnos de bot al levantar el proceso.

_ai_tasks vive solo en memoria y el lifespan no recorria nada al arrancar: un
reinicio durante el turno de un bot dejaba la partida trabada para siempre.
Importa porque el tunel es efimero y cada sesion de juego implica reiniciar.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from conftest import ADMIN, confirm_join, create_game, invite, recv_until
from teg_backend.config import Settings
from teg_backend.domain import engine as engine_mod
from teg_backend.main import create_app


@pytest.fixture()
def anyio_backend():
    return "asyncio"


def _settings(tmp_path, think_seconds: float = 0.3) -> Settings:
    return Settings(
        env="dev", db_path=str(tmp_path / "test.db"), admin_token="test-admin",
        commentator_provider="mock", commentator_cooldown_seconds=0.0,
        reconnect_grace_seconds=0.05, ai_player_think_seconds=think_seconds,
        public_base_url="http://testserver",
    )


def test_reagenda_el_turno_del_bot_tras_reiniciar(tmp_path, monkeypatch):
    """Test fuerte: deja el turno de verdad ("stage": "turns", post
    colocacion) en manos del bot, reinicia el proceso sobre la misma base y
    verifica que el turno del bot se reagenda de verdad, no solo que el
    arranque no explota.

    Determinismo del turno inicial: engine.start() baraja turn.order con
    secrets.SystemRandom, asi que sin fijarlo no hay forma de saber de
    antemano si el primer turno es del bot o del humano (para forzarlo
    recien ahi habria que ramificar el test: "si le toca al humano, que
    termine su turno antes de reiniciar"). Se opto por neutralizar el
    shuffle (monkeypatch a no-op) e invitar al bot ANTES que al humano: el
    orden de asientos ya viene ordenado por created_at, asi que el bot queda
    determisticamente primero en turn.order. Es mas simple y mas legible que
    manejar las dos ramas.

    ai_player_think_seconds se fija en 0.3s: el bot lo necesita para
    autocolocarse en cada ronda de colocacion inicial (nadie mas lo hace por
    el), pero esa misma constante le da margen de sobra a la tarea de turno
    recien agendada (misma espera) para NO alcanzar a jugar y pisar el
    estado antes de que cerremos el proceso.
    """
    monkeypatch.setattr(engine_mod._rng, "shuffle", lambda seq: None)
    settings = _settings(tmp_path, think_seconds=0.3)

    # 1) primera vida del proceso: arranca una partida con el bot primero en
    # el orden de asientos (y por lo tanto, con el shuffle neutralizado,
    # primero en turn.order).
    with TestClient(create_app(settings)) as c:
        game = create_game(c, config={"commentator_enabled": False})
        bot_resp = c.post(
            f"/api/admin/games/{game['id']}/players",
            json={"nickname": "Bot", "role": "ai_player"}, headers=ADMIN,
        )
        assert bot_resp.status_code == 200, bot_resp.text
        bot_id = bot_resp.json()["player"]["id"]
        humano = invite(c, game["id"], "Humano")
        humano_id = humano["player"]["id"]
        confirm_join(c, game["code"], humano["token"])

        with c.websocket_connect(f"/ws/{game['code']}?token={humano['token']}") as ws:
            recv_until(ws, "game.snapshot")
            ws.send_json({"type": "ready.set", "payload": {"ready": True}})
            # esperar la confirmacion de "listo" evita la carrera contra el
            # start: sin esto, el POST puede llegar antes de que el server
            # procese el mensaje de ws y lo rechace con "ya empezó".
            recv_until(ws, "player.ready")
            start_resp = c.post(f"/api/admin/games/{game['id']}/start", headers=ADMIN)
            assert start_resp.status_code == 200, start_resp.text
            started = recv_until(ws, "game.started")
            territories = started["payload"]["territories"]
            recv_until(ws, "placement.started")

            # ronda 1 (5 ejercitos) y ronda 2 (3): el humano coloca de una;
            # el bot se autocoloca solo ~0.3s despues via _ai_placements.
            for round_pool in (5, 3):
                tid = next(
                    t for t, d in territories.items()
                    if d["owner_player_id"] == humano_id
                )
                ws.send_json({"type": "placement.place",
                              "payload": {"territory_id": tid, "count": round_pool}})
                revealed = recv_until(ws, "placement.revealed")
                territories = revealed["payload"]["territories"]

            # tras la 2da revelacion la partida paso a stage "turns"; el
            # turno le toca al bot (primero en turn.order) y el servidor ya
            # agendo su tarea de juego (que recien actuara en ~0.3s).
            turn_started = recv_until(ws, "turn.started")
            assert turn_started["actor_id"] == bot_id

        # el proceso se "reinicia" apenas confirmado el turno del bot: la
        # tarea agendada en la vida anterior todavia esta durmiendo su
        # ai_player_think_seconds y nunca llega a jugar ni a persistir nada.

    # 2) el proceso "se reinicia": app nueva sobre la misma base.
    app2 = create_app(settings)
    with TestClient(app2):
        # el lifespan ya corrio la rehidratacion antes de que esto devuelva.
        service = app2.state.service
        assert service.counters.get("ai_turns_rehydrated") == 1
        assert f"{game['id']}:{bot_id}" in service._ai_tasks
