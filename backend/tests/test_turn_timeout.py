"""Un jugador ausente no debe trabar la mesa; uno presente no debe ser apurado."""

import asyncio
import time

import pytest
from fastapi.testclient import TestClient

from conftest import ADMIN, complete_placement, confirm_join, create_game, invite, recv_until
from teg_backend.config import Settings
from teg_backend.domain.engine import GameEngine
from teg_backend.main import create_app
from teg_backend.realtime.manager import Room


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


def _esperar_desconexion(ws, player_id: str):
    """Lee hasta ver a `player_id` reflejado como no-online en presence.changed.

    Sirve de sincronizacion sobre un hecho observable: cerrar el socket del
    lado del cliente no garantiza que el servidor ya haya procesado la
    desconexion (room.remove() corre en el `finally` del endpoint WS, en otra
    tarea). Sin esto, un timeout de turno corto en el test puede vencer ANTES
    de que el servidor se entere de que el jugador se fue, viendo su socket
    todavia registrado y absteniendose de saltear el turno para siempre.
    """
    for _ in range(100):
        msg = recv_until(ws, "presence.changed", max_msgs=100)
        if msg.get("actor_id") == player_id and msg["payload"].get("presence") != "online":
            return msg
    raise AssertionError(f"nunca se vio la desconexion de {player_id}")


def _ping_y_drenar(ws) -> list[str | None]:
    """Manda un ping y junta los event_type vistos hasta el pong de respuesta.

    Centinela para no bloquear leyendo mensajes que capaz no llegan nunca.
    """
    ws.send_json({"type": "ping"})
    vistos: list[str | None] = []
    while True:
        msg = ws.receive_json()
        if msg.get("type") == "pong":
            return vistos
        vistos.append(msg.get("event_type"))


def _barrera(ws) -> list[dict]:
    """Manda un ping y devuelve TODOS los mensajes (completos) vistos hasta
    el pong de respuesta.

    Cada conexion procesa sus mensajes entrantes en un `while True` estricto
    y en orden: si ya volvio el pong, todo lo que esa conexion tenia
    pendiente ANTES del ping ya se proceso por completo de punta a punta.

    Esto importa porque `complete_placement` manda el ultimo `placement.place`
    y devuelve el control apenas ve `placement.revealed` en el cliente, pero
    eso NO prueba que el server ya termino de correr el resto de la cadena
    que dispara esa revelacion (`place_initial` -> `_start_turn`, que arma el
    timeout de turno) — `emit()` encola el evento y retorna antes de que un
    worker aparte lo entregue. Si cerramos el socket de esa conexion antes de
    que su propio `_start_turn` termine, TestClient cancela de mitad de
    camino la tarea en curso (via `CancelScope.cancel()` en su `__exit__`) y
    el timeout nunca llega a armarse: la mesa queda trabada para siempre. Se
    verifico reproduciendo el cuelgue con logs granulares en cada await de
    `_start_turn`/`emit`/`_after_emit`.
    """
    ws.send_json({"type": "ping"})
    vistos: list[dict] = []
    while True:
        msg = ws.receive_json()
        if msg.get("type") == "pong":
            return vistos
        vistos.append(msg)


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
            # barrera de sincronizacion en AMBAS conexiones antes de cerrar
            # ws2: cualquiera de las dos pudo ser la que disparo la
            # transicion a "turns" (y con ella el armado del timeout); hay
            # que esperar a que esa conexion termine de procesarla de punta
            # a punta antes de tocarle el socket (ver docstring de _barrera)
            vistos1 = _barrera(ws1)
            vistos2 = _barrera(ws2)
            turn_ev = next(
                m for m in vistos1 + vistos2 if m.get("event_type") == "turn.started"
            )
        # ws2 queda cerrado al salir del `with`: el jugador "Dos" esta ausente

        # sincronizar sobre un hecho observable (el server ya vio la
        # desconexion) en vez de confiar en que el timeout de 1s alcance
        # para ganarle a la latencia de deteccion del cierre del socket
        _esperar_desconexion(ws1, p2)

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
        # del timeout de turno; nadie deberia ser salteado.
        time.sleep(2.5)
        vistos = _ping_y_drenar(ws1)
        assert "turn.skipped" not in vistos, "se salteo a un jugador conectado"


def test_no_se_saltea_si_reconecta_durante_la_ventana(client_turno_corto):
    """CRITICO: reconectar en cualquier momento antes de que el turno se
    cierre de verdad tiene que evitar el salteo. La revalidacion de sockets
    ocurre bajo el MISMO lock que hace el avance de turno, sin ventana entre
    "esta ausente" y "le sacamos el turno" en el medio."""
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
            # ver _barrera: sin esto, cerrar ws2 puede cancelar de mitad de
            # camino la tarea que todavia esta armando el timeout de turno
            vistos1 = _barrera(ws1)
            vistos2 = _barrera(ws2)
            turn_ev = next(
                m for m in vistos1 + vistos2 if m.get("event_type") == "turn.started"
            )
        # ws2 cerrado: "Dos" queda ausente (por ahora)

        _esperar_desconexion(ws1, p2)

        if turn_ev["actor_id"] == p1:
            ws1.send_json({"type": "turn.end", "payload": {}})
            recv_until(ws1, "turn.started")  # ahora le toca a "Dos", ausente

        # "Dos" reconecta bien adentro de la ventana del timeout (1 s): no
        # insertamos ninguna demora deliberada antes de esto
        with client.websocket_connect(f"/ws/{game['code']}?token={inv2['token']}") as ws2b:
            recv_until(ws2b, "game.snapshot")

            # esperar bastante mas que el timeout: nadie deberia ser salteado
            time.sleep(1.5)
            vistos = _ping_y_drenar(ws1)
            assert "turn.skipped" not in vistos, "se salteo pese a estar reconectado"


def test_no_se_saltea_si_reconecta_justo_antes_de_cerrar_el_turno(client_turno_corto, monkeypatch):
    """CRITICO, version deterministica de la carrera.

    El hallazgo original: el chequeo de sockets y el cierre efectivo del
    turno tienen que ser una unica operacion atomica bajo el mismo lock, sin
    ningun await entre medio. Probar esto por temporizacion pura (dormir X
    ms y cruzar los dedos) no es confiable: la ventana insegura de la version
    vieja duraba milisegundos y la de la version arreglada deberia durar
    ~0. Para probarlo de forma reproducible, se inyecta una demora
    controlada en `get_game_or_404` -- la primera lectura que hace el
    timeout al despertar, ANTES de su chequeo final de sockets -- y se
    reconecta al jugador mientras esa demora esta en curso. Si el chequeo de
    sockets fuera anterior a esa lectura (o si se soltara el lock en el
    medio), este test fallaria porque la reconexion llegaria demasiado
    tarde; con el chequeo de sockets al final, bajo el mismo lock, la
    reconexion se ve igual sin importar cuanto se demoren las lecturas
    previas.
    """
    client = client_turno_corto
    game, inv1, inv2 = _arrancar(client)
    p1, p2 = inv1["player"]["id"], inv2["player"]["id"]
    service = client.app.state.service
    original_get_game_or_404 = service.get_game_or_404
    demora_hecha = {"valor": False}

    async def get_game_or_404_lento(game_id: str):
        # solo demora la PRIMERA lectura despues de instalado el parche: es
        # la que hace el timeout al despertar. Las siguientes (p. ej. las que
        # dispara la propia reconexion de mas abajo) pasan directo.
        if game_id == game["id"] and not demora_hecha["valor"]:
            demora_hecha["valor"] = True
            await asyncio.sleep(1.2)
        return await original_get_game_or_404(game_id)

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
            vistos1 = _barrera(ws1)
            vistos2 = _barrera(ws2)
            turn_ev = next(
                m for m in vistos1 + vistos2 if m.get("event_type") == "turn.started"
            )
        # ws2 cerrado: "Dos" queda ausente

        _esperar_desconexion(ws1, p2)

        if turn_ev["actor_id"] == p1:
            ws1.send_json({"type": "turn.end", "payload": {}})
            recv_until(ws1, "turn.started")  # ahora le toca a "Dos", ausente

        # instalar el parche recien aca: nada mas en el test llama a
        # get_game_or_404 para esta partida hasta que el timeout despierte
        monkeypatch.setattr(service, "get_game_or_404", get_game_or_404_lento)

        # dejar pasar el timeout (1 s): el _vencer() del server se despierta,
        # toma el lock, y queda parado ~1.2s adentro de la demora artificial,
        # ANTES de llegar a revisar sockets
        time.sleep(1.15)

        # reconectar mientras el timeout esta parado en la demora artificial
        with client.websocket_connect(f"/ws/{game['code']}?token={inv2['token']}") as ws2b:
            recv_until(ws2b, "game.snapshot")

            # esperar a que la demora artificial termine y el timeout resuelva
            time.sleep(1.5)
            vistos = _ping_y_drenar(ws1)
            assert "turn.skipped" not in vistos, (
                "se salteo pese a reconectar durante la ventana critica"
            )


def test_la_mutacion_del_turno_ocurre_antes_de_cualquier_await_posterior_al_chequeo(
    client_turno_corto, monkeypatch,
):
    """CRITICO, ventana RESIDUAL (segunda vuelta de review).

    El test anterior (`..._justo_antes_de_cerrar_el_turno`) inyecta la demora
    en `get_game_or_404`, que corre ANTES del chequeo de sockets -- no cubre
    la ventana que quedaba DESPUES: `_cerrar_y_avanzar_turno` hacia varios
    `await self.emit(...)` (incluido uno incondicional para `turn.ended`,
    con su propia escritura a SQLite) ANTES de llamar a la mutacion real
    `engine.advance_turn()`. Esa es la ventana que este test cubre.

    El arreglo mueve las tres mutaciones sincronicas del motor
    (`resolve_wager`, `award_card_if_due`, `advance_turn`) a correr
    INMEDIATAMENTE despues del chequeo de sockets, sin ningun `await` en el
    medio -- los `emit(...)` (incluido `turn.ended`) se movieron a DESPUES.
    Como consecuencia, un test que solo mire "¿aparecio turn.skipped?" ya no
    alcanza para distinguir la version vieja de la arreglada: en ambas
    aparece igual, tarde o temprano, una vez que el timeout decide saltear
    (ninguna de las dos versiones "deshace" una mutacion ya hecha). Lo que
    SI cambia entre versiones es el ORDEN relativo entre la reconexion
    (`Room.add`, sincronico, sin tomar el lock de la partida) y la mutacion
    real (`GameEngine.advance_turn`, instrumentada aca).

    - Version vieja (con el `await emit(turn.ended)` antes de
      `advance_turn`): si la reconexion ocurre durante esa demora, queda
      registrada ANTES que `advance_turn` en el orden -- pero `advance_turn`
      se llama de todos modos (nadie vuelve a chequear), o sea: el jugador
      ya estaba de vuelta y el turno se le salteo igual. Bug.
    - Version arreglada: `advance_turn` ya corrio (sincronicamente, pegado
      al chequeo de sockets) ANTES de llegar al primer `await` posterior
      (el emit de `turn.ended`, entre otros); la reconexion, si ocurre
      durante esa demora, queda registrada DESPUES de `advance_turn` --
      llego demasiado tarde para importar, que es la unica ventana
      aceptable.

    Se instrumenta con monkeypatch en vez de inferir por temporizacion pura:
    el orden se lee de una lista poblada desde el hilo unico del loop del
    server (sin condiciones de carrera de escritura), asi que la aserción es
    determinista una vez que la reconexion efectivamente ocurre durante la
    demora (lo cual sí se fuerza con tiempos generosos, no ajustados al
    milisegundo).
    """
    client = client_turno_corto
    game, inv1, inv2 = _arrancar(client)
    p1, p2 = inv1["player"]["id"], inv2["player"]["id"]
    service = client.app.state.service

    orden: list[str] = []
    # sin este flag, la PRIMERA conexion de "Dos" (al arrancar el test, mucho
    # antes de que se desconecte) tambien quedaria registrada como
    # "reconexion" y contaminaria la comparacion; solo nos interesa la
    # reconexion deliberada de mas abajo, y el advance_turn del salteo (no
    # el de un eventual turn.end de traspaso previo)
    activo = {"valor": False}

    original_advance_turn = GameEngine.advance_turn

    def advance_turn_instrumentado(self):
        if activo["valor"]:
            orden.append("advance_turn")
        return original_advance_turn(self)

    monkeypatch.setattr(GameEngine, "advance_turn", advance_turn_instrumentado)

    original_room_add = Room.add

    def add_instrumentado(self, player_id, ws):
        if activo["valor"] and player_id == p2:
            orden.append("reconexion")
        return original_room_add(self, player_id, ws)

    monkeypatch.setattr(Room, "add", add_instrumentado)

    original_emit = service.emit
    demora_hecha = {"valor": False}

    async def emit_lento(game_id_arg, event_type, **kwargs):
        # demora especificamente el emit de turn.ended: en la version vieja
        # corria ANTES de advance_turn; en la arreglada corre DESPUES. Es
        # incondicional (siempre se emite al cerrar un turno), a diferencia
        # de wager.resolved/card.awarded que dependen del estado de la
        # partida.
        if (
            game_id_arg == game["id"]
            and event_type == "turn.ended"
            and not demora_hecha["valor"]
        ):
            demora_hecha["valor"] = True
            await asyncio.sleep(1.0)
        return await original_emit(game_id_arg, event_type, **kwargs)

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
            vistos1 = _barrera(ws1)
            vistos2 = _barrera(ws2)
            turn_ev = next(
                m for m in vistos1 + vistos2 if m.get("event_type") == "turn.started"
            )
        # ws2 cerrado: "Dos" queda ausente

        _esperar_desconexion(ws1, p2)

        if turn_ev["actor_id"] == p1:
            ws1.send_json({"type": "turn.end", "payload": {}})
            recv_until(ws1, "turn.started")  # ahora le toca a "Dos", ausente

        # activar el registro de orden y el parche de demora recien aca: nada
        # mas en el test dispara un turn.ended ni reconecta a "Dos" hasta
        # este punto, asi que lo unico que se registra de aca en mas es el
        # advance_turn del propio salteo y la reconexion deliberada
        activo["valor"] = True
        monkeypatch.setattr(service, "emit", emit_lento)

        # dejar pasar el timeout (1 s): el _vencer() del server se despierta,
        # pasa el chequeo de sockets (todavia ausente), muta el turno, y
        # recien ahi queda parado ~1s en la demora artificial del emit de
        # turn.ended
        time.sleep(1.15)

        # reconectar mientras el emit de turn.ended esta demorado
        with client.websocket_connect(f"/ws/{game['code']}?token={inv2['token']}") as ws2b:
            recv_until(ws2b, "game.snapshot")

            # esperar a que la demora artificial termine y todo se asiente
            time.sleep(1.5)
            _ping_y_drenar(ws1)

        assert "advance_turn" in orden, "el timeout no llego a saltear el turno"
        assert "reconexion" in orden, "la reconexion nunca se registro"
        assert orden.index("advance_turn") < orden.index("reconexion"), (
            "la mutacion del turno ocurrio DESPUES de que la reconexion ya "
            f"estaba registrada -- ventana critica reabierta: {orden}"
        )
