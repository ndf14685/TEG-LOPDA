"""Apagado completo del proceso: nadie toca SQLite despues del cierre.

El flake "Cannot operate on a closed database" es un camino real de
produccion, no del test: reiniciar es el flujo NORMAL de este proyecto (el
tunel es efimero y hay que regenerar los links en cada sesion).
"""

from __future__ import annotations

import asyncio

import pytest
from fastapi.testclient import TestClient

from conftest import ADMIN, confirm_join, create_game, invite, recv_until
from teg_backend.config import Settings
from teg_backend.infrastructure.db import Database
from teg_backend.main import create_app


@pytest.fixture()
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_close_de_la_base_espera_a_las_consultas_en_vuelo(tmp_path):
    """Database.close() no tomaba self._lock, mientras todas las consultas si:
    una query en vuelo cuando el lifespan cierra recibe exactamente
    "Cannot operate on a closed database".

    Se prueba de forma deterministica en vez de por carrera: con el lock
    tomado a mano (una consulta simulada en vuelo), close() tiene que quedar
    esperando en lugar de cerrar la conexion abajo de esa consulta.
    """
    db = Database(str(tmp_path / "t.db"))
    await db.connect()
    try:
        async with db._lock:  # una consulta "en vuelo"
            with pytest.raises(TimeoutError):
                async with asyncio.timeout(0.3):
                    await db.close()
            assert db._conn is not None, (
                "close() cerro la base con una consulta en vuelo"
            )
    finally:
        await db.close()
    assert db._conn is None


def test_las_tareas_de_fondo_se_cancelan_antes_de_cerrar_la_base(tmp_path, monkeypatch):
    """_ai_tasks y la tarea de _schedule_ai_placements (fire-and-forget, sin
    ninguna referencia guardada) tocan SQLite y nadie las cancelaba. Empeoro
    con la fase: rehidratar_partidas_activas CREA _ai_tasks al arrancar.

    La asercion es "no quedaba ninguna viva EN EL MOMENTO de cerrar la base",
    no "terminaron alguna vez": asyncio.run() cancela todo lo que quede al
    destruir el loop, pero eso pasa DESPUES de db.close(), o sea que sin el
    arreglo las tareas sobrevivian al cierre de la base por pura casualidad.
    Por eso se instrumenta Database.close en vez de mirar el estado final.

    ai_player_think_seconds se pone alto a proposito: garantiza que la tarea
    de colocacion del bot este durmiendo -- viva -- en el momento del apagado.
    """
    vivas_al_cerrar: list = []
    original_close = Database.close
    estado: dict = {}

    async def close_instrumentado(self):
        service = estado.get("service")
        if service is not None:
            vivas_al_cerrar.extend(
                t for t in service._tareas_de_fondo if not t.done()
            )
        return await original_close(self)

    monkeypatch.setattr(Database, "close", close_instrumentado)

    settings = Settings(
        env="dev", db_path=str(tmp_path / "test.db"), admin_token="test-admin",
        commentator_provider="mock", commentator_cooldown_seconds=0.0,
        reconnect_grace_seconds=0.05, ai_player_think_seconds=5.0,
        public_base_url="http://testserver",
    )
    app = create_app(settings)
    with TestClient(app) as c:
        estado["service"] = app.state.service
        game = create_game(c, config={"commentator_enabled": False})
        bot = c.post(
            f"/api/admin/games/{game['id']}/players",
            json={"nickname": "Bot", "role": "ai_player"}, headers=ADMIN,
        )
        assert bot.status_code == 200, bot.text
        humano = invite(c, game["id"], "Humano")
        confirm_join(c, game["code"], humano["token"])
        with c.websocket_connect(f"/ws/{game['code']}?token={humano['token']}") as ws:
            recv_until(ws, "game.snapshot")
            ws.send_json({"type": "ready.set", "payload": {"ready": True}})
            recv_until(ws, "player.ready")
            assert c.post(
                f"/api/admin/games/{game['id']}/start", headers=ADMIN
            ).status_code == 200
            recv_until(ws, "placement.started")

        service = app.state.service
        assert [t for t in service._tareas_de_fondo if not t.done()], (
            "el escenario no dejo ninguna tarea de fondo viva"
        )

    assert not vivas_al_cerrar, (
        f"{len(vivas_al_cerrar)} tareas de fondo seguian vivas cuando el "
        "lifespan cerro la base"
    )
    assert not service._tareas_de_fondo
    assert not service._ai_tasks
