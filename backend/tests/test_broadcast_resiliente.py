"""Un jugador con red mala no debe frenar a los otros siete.

El fan-out era un for secuencial de send_json sin timeout, ejecutado dentro del
lock de la partida.
"""

import asyncio
import time

import pytest

from teg_backend.application.game_service import GameService
from teg_backend.config import Settings
from teg_backend.domain.enums import Visibility
from teg_backend.domain.events import GameEvent
from teg_backend.realtime.manager import ConnectionManager


@pytest.fixture()
def anyio_backend():
    return "asyncio"


class SocketLento:
    """Simula un jugador con red mala: el buffer no drena nunca."""
    def __init__(self): self.enviados = 0
    async def send_json(self, payload): await asyncio.sleep(3600)
    async def close(self, code=1000): pass


class SocketNormal:
    def __init__(self): self.enviados = 0
    async def send_json(self, payload): self.enviados += 1
    async def close(self, code=1000): pass


@pytest.mark.anyio
async def test_un_socket_lento_no_frena_a_los_demas():
    manager = ConnectionManager(send_timeout_seconds=0.2)
    room = manager.room("g1")
    lento, rapidos = SocketLento(), [SocketNormal() for _ in range(7)]
    room.add("lento", lento)
    for i, s in enumerate(rapidos):
        room.add(f"j{i}", s)

    ev = GameEvent(event_type="chat.message", game_id="g1", visibility=Visibility.PUBLIC)
    inicio = time.monotonic()
    await manager.broadcast("g1", ev, {})
    transcurrido = time.monotonic() - inicio

    assert all(s.enviados == 1 for s in rapidos), "los sanos deben recibir igual"
    assert transcurrido < 2, f"el broadcast tardo {transcurrido:.1f}s por un socket lento"


class ManagerFalso:
    """Registra el orden real de salida; el primer envio tarda mas que el resto."""

    def __init__(self):
        self.vistos: list[int] = []

    async def broadcast(self, game_id, event, roles):
        n = event.payload["n"]
        # los primeros eventos son los mas lentos: con un create_task suelto por
        # evento, los ultimos llegarian antes y el orden saldria invertido
        await asyncio.sleep(0.005 * (10 - n))
        self.vistos.append(n)


class ComentaristaFalso:
    emit = None


@pytest.mark.anyio
async def test_el_envio_diferido_preserva_el_orden_por_partida():
    manager = ManagerFalso()
    svc = GameService(db=None, manager=manager, commentator=ComentaristaFalso(), settings=Settings())

    for n in range(10):
        ev = GameEvent(
            event_type="chat.message", game_id="g1",
            visibility=Visibility.PUBLIC, payload={"n": n},
        )
        svc._encolar_envio("g1", ev, {})

    await asyncio.wait_for(svc._send_queues["g1"].join(), timeout=5)
    assert manager.vistos == list(range(10)), f"orden roto: {manager.vistos}"
