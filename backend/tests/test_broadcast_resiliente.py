"""Un jugador con red mala no debe frenar a los otros siete.

El fan-out era un for secuencial de send_json sin timeout, ejecutado dentro del
lock de la partida.
"""

import asyncio
import itertools
import time

import pytest

from teg_backend.application import game_service as gs
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
        self.roles_vistos: list[dict] = []

    async def broadcast(self, game_id, event, roles):
        n = event.payload["n"]
        # los primeros eventos son los mas lentos: con un create_task suelto por
        # evento, los ultimos llegarian antes y el orden saldria invertido
        await asyncio.sleep(0.005 * (10 - n))
        self.vistos.append(n)
        self.roles_vistos.append(roles)


class ComentaristaFalso:
    emit = None


def _evento(n: int) -> GameEvent:
    return GameEvent(
        event_type="chat.message", game_id="g1",
        visibility=Visibility.PUBLIC, payload={"n": n},
    )


def _servicio(manager, *, roles: dict | None = None, demora_roles: float = 0.0) -> GameService:
    """GameService con la DB fuera de juego: solo interesa la maquinaria de envio."""
    svc = GameService(
        db=None, manager=manager, commentator=ComentaristaFalso(), settings=Settings()
    )

    async def _roles_map(game_id):
        if demora_roles:
            await asyncio.sleep(demora_roles)
        return roles if roles is not None else {}

    svc._roles_map = _roles_map
    return svc


@pytest.mark.anyio
async def test_el_envio_diferido_preserva_el_orden_por_partida():
    manager = ManagerFalso()
    # _roles_map ahora corre adentro del worker y agrega un await por evento:
    # el orden tiene que aguantarlo igual
    svc = _servicio(manager, roles={"p1": "player"}, demora_roles=0.002)

    for n in range(10):
        svc._encolar_envio("g1", _evento(n))

    await asyncio.wait_for(svc._send_queues["g1"].join(), timeout=5)
    assert manager.vistos == list(range(10)), f"orden roto: {manager.vistos}"
    # y los roles llegan resueltos desde el worker, no desde emit
    assert manager.roles_vistos == [{"p1": "player"}] * 10
    await svc.detener_envios()


@pytest.mark.anyio
async def test_emit_encola_en_el_mismo_orden_en_que_numera(monkeypatch):
    """Dos emit concurrentes salen en el orden de su sequence_number.

    El encolado va adentro del lock de secuencia. Si se hace afuera, cualquier
    await intermedio (resolver roles contra la DB, por ejemplo) deja que el
    segundo evento se adelante al primero.
    """
    manager = ManagerFalso()
    svc = _servicio(manager)

    seq, pub = itertools.count(1), itertools.count(1)

    async def _next_seq(db, game_id):
        return next(seq)

    async def _next_pub(db, game_id):
        return next(pub)

    async def _append(db, payload):
        return None

    monkeypatch.setattr(gs.repo, "next_sequence_number", _next_seq)
    monkeypatch.setattr(gs.repo, "next_public_sequence", _next_pub)
    monkeypatch.setattr(gs.repo, "append_event", _append)

    async def _sin_efectos(game_id, event):
        return None

    svc._after_emit = _sin_efectos

    # el primer resolve de roles es lento y el segundo rapido: si emit espera
    # los roles antes de encolar, el segundo evento se adelanta al primero
    llamadas = itertools.count()

    async def _roles_map(game_id):
        await asyncio.sleep(0.05 if next(llamadas) == 0 else 0.001)
        return {}

    svc._roles_map = _roles_map

    await asyncio.gather(
        svc.emit("g1", "chat.message", payload={"n": 0}),
        svc.emit("g1", "chat.message", payload={"n": 1}),
    )
    await asyncio.wait_for(svc._send_queues["g1"].join(), timeout=5)
    assert manager.vistos == [0, 1], f"el envio salio en otro orden: {manager.vistos}"
    await svc.detener_envios()


@pytest.mark.anyio
async def test_el_worker_de_envios_no_se_apaga_solo_y_sigue_entregando():
    """Un evento encolado siempre se entrega: el worker no muere por su cuenta.

    Cuando el worker se apagaba por inactividad habia una ventana en la que
    estaba muriendo pero todavia no daba done(): un emit que caia ahi no creaba
    worker nuevo y el evento se quedaba encolado para siempre.
    """
    manager = ManagerFalso()
    svc = _servicio(manager)

    svc._encolar_envio("g1", _evento(0))
    await asyncio.wait_for(svc._send_queues["g1"].join(), timeout=5)
    worker = svc._send_workers["g1"]

    # cola vacia: el worker tiene que quedarse esperando, no apagarse
    for _ in range(20):
        await asyncio.sleep(0)
    await asyncio.sleep(0.05)
    assert not worker.done(), "el worker se apago con la cola vacia"

    # el evento siguiente lo toma el MISMO worker y se entrega igual
    svc._encolar_envio("g1", _evento(1))
    await asyncio.wait_for(svc._send_queues["g1"].join(), timeout=5)
    assert svc._send_workers["g1"] is worker, "se recreo el worker"
    assert manager.vistos == [0, 1], "se perdio un evento encolado"
    await svc.detener_envios()


@pytest.mark.anyio
async def test_detener_envios_cancela_los_workers_y_no_los_revive():
    manager = ManagerFalso()
    svc = _servicio(manager)

    svc._encolar_envio("g1", _evento(0))
    await asyncio.wait_for(svc._send_queues["g1"].join(), timeout=5)
    worker = svc._send_workers["g1"]
    assert not worker.done()

    await asyncio.wait_for(svc.detener_envios(), timeout=5)
    assert worker.done(), "el apagado no espero al worker"
    assert not svc._send_workers

    # un emit tardio no puede revivir una tarea justo cuando cerramos la base
    svc._encolar_envio("g1", _evento(1))
    assert not svc._send_workers, "se revivio un worker despues del apagado"
    assert manager.vistos == [0]
