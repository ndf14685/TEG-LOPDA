"""Criterio de aceptacion de la Fase 0: una partida de 8 jugadores JUGADA de
verdad, no solo arrancada.

test_carga_8_jugadores.py cubre la ventana critica del incidente del 27/07
(arranque hasta placement.started) y se deja intacto: es rapido y esa ventana
sigue siendo la que disparo el incidente original.

Este test es adicional: conecta los 8 WebSocket, completa la colocacion
inicial (5+3) y juega dos rondas completas de turnos (refuerzos + un ataque +
fin de turno, para cada uno de los 8 jugadores) para estirar la cobertura mas
alla del arranque. Al final, para CADA uno de los 8 clientes, verifica:

  - cero huecos de secuencia: los `sequence_number > 0` que recibio son
    consecutivos (los que llegan en 0 son efimeros y se ignoran).
  - cero reconexiones no provocadas: ningun jugador vio nunca su propia
    presencia pasar por "reconnecting"/"offline", ni un player.disconnected.
  - cero incidentes de pending-action-timeout con la conexion sana: nunca
    aparece un turn.skipped (el auto-skip por timeout de turno).
  - que recibio los eventos que le corresponden: su objetivo privado y los
    eventos publicos de la partida (game.started, placement.revealed x2,
    turn.started en sus propios turnos).

Para que 8 jugadores jueguen 2 rondas completas entre en el timeout = 30 del
proyecto (backend/pyproject.toml), el ataque de cada turno es un "duelo de
dados" sin territorio (target_player_id + attacker_dice_count, sin
source_territory_id/target_territory_id): resuelve attack.resolved pero no
cambia tenencia ni elimina a nadie, asi la partida no se complica turno a
turno y el test sigue siendo determinista.
"""

from __future__ import annotations

import contextlib

from conftest import ADMIN, confirm_join, create_game, invite, recv_until

JUGADORES = 8
RONDAS = 2

# Eventos que, de aparecer, son en si mismos el incidente que este test
# existe para detectar: NO se relaja esta lista si algun dia falla.
EVENTOS_PROHIBIDOS = {"turn.skipped", "player.disconnected"}


def _armar_partida_de_ocho(client):
    game = create_game(client, config={"commentator_enabled": False, "mode": "classic_26"})
    invs = [invite(client, game["id"], f"j{i}") for i in range(JUGADORES)]
    for inv in invs:
        confirm_join(client, game["code"], inv["token"])
    return game, invs


def _recv_track(ws, event_type: str, bucket: list, max_msgs: int = 30) -> dict:
    """Como recv_until, pero ademas registra en `bucket` TODOS los mensajes
    vistos en el camino (matches y descartados), para poder auditar despues
    huecos de secuencia y reconexiones sobre el historial completo de cada
    cliente, no solo sobre el ultimo evento esperado."""
    for _ in range(max_msgs):
        msg = ws.receive_json()
        bucket.append(msg)
        if msg.get("event_type") == event_type:
            return msg
        if msg.get("event_type") == "error" and event_type != "error":
            raise AssertionError(
                f"error inesperado esperando {event_type}: {msg.get('payload')}"
            )
    raise AssertionError(f"no llego el evento {event_type} en {max_msgs} mensajes")


def _recv_track_n(ws, event_type: str, n: int, bucket: list, max_msgs: int = 60) -> dict:
    """Como _recv_track, pero espera la ocurrencia numero `n` del evento (no
    la primera). Se usa para esperar los 8 `player.ready` -- uno por
    jugador -- ANTES de arrancar: arrancar apenas se manda el propio
    ready.set es la carrera documentada (un ready.set que el servidor
    procesa despues del start responde con error GAME_STATE_CONFLICT)."""
    vistos = 0
    for _ in range(max_msgs):
        msg = ws.receive_json()
        bucket.append(msg)
        if msg.get("event_type") == event_type:
            vistos += 1
            if vistos == n:
                return msg
        if msg.get("event_type") == "error":
            raise AssertionError(
                f"error inesperado esperando {event_type} #{n}: {msg.get('payload')}"
            )
    raise AssertionError(f"no llegaron {n} ocurrencias de {event_type} en {max_msgs} mensajes")


def test_ocho_jugadores_juegan_dos_rondas_completas(client):
    game, invs = _armar_partida_de_ocho(client)
    pids = [inv["player"]["id"] for inv in invs]

    with contextlib.ExitStack() as stack:
        wss = [
            stack.enter_context(
                client.websocket_connect(f"/ws/{game['code']}?token={inv['token']}")
            )
            for inv in invs
        ]
        ws_by_pid = dict(zip(pids, wss))
        # todo lo que cada jugador recibio en su socket, en orden
        vistos: dict[str, list] = {pid: [] for pid in pids}

        for ws in wss:
            recv_until(ws, "game.snapshot")
        for ws in wss:
            ws.send_json({"type": "ready.set", "payload": {"ready": True}})

        # esperar la confirmacion de los 8 "listos" ANTES de arrancar: un
        # ready.set que el servidor procesa DESPUES del start responde con
        # GAME_STATE_CONFLICT ("la partida ya empezo"), la carrera conocida
        # de TestClient (ver docstring del modulo).
        ultimo_ready = _recv_track_n(wss[0], "player.ready", JUGADORES, vistos[pids[0]])
        assert ultimo_ready["payload"]["all_ready"] is True

        resp = client.post(f"/api/admin/games/{game['id']}/start", headers=ADMIN)
        assert resp.status_code == 200, resp.text
        order = resp.json()["turn_order"]
        assert set(order) == set(pids)

        # arranque: cada jugador recibe game.started (publico), su objetivo
        # (privado) y placement.started (publico)
        territories = None
        for pid, ws in zip(pids, wss):
            started = _recv_track(ws, "game.started", vistos[pid])
            if territories is None:
                territories = started["payload"]["territories"]
            objetivo = _recv_track(ws, "objective.assigned", vistos[pid])
            assert objetivo["payload"]["objective"]["title"], f"{pid}: sin objetivo"
            _recv_track(ws, "placement.started", vistos[pid])

        # colocacion inicial: ronda de 5 y ronda de 3, revelado sincronizado
        for pool in (5, 3):
            for pid, ws in zip(pids, wss):
                tid = next(t for t, d in territories.items() if d["owner_player_id"] == pid)
                ws.send_json({"type": "placement.place",
                              "payload": {"territory_id": tid, "count": pool}})
            reveal = None
            for pid, ws in zip(pids, wss):
                reveal = _recv_track(ws, "placement.revealed", vistos[pid])
            territories = reveal["payload"]["territories"]

        # RONDAS completas de turnos: refuerzos + un ataque + fin de turno,
        # para los 8 jugadores, dos veces (16 turnos en total)
        for turno_idx in range(RONDAS * JUGADORES):
            actor_id = order[turno_idx % JUGADORES]
            ws_actor = ws_by_pid[actor_id]
            bucket = vistos[actor_id]

            turn_ev = _recv_track(ws_actor, "turn.started", bucket)
            assert turn_ev["actor_id"] == actor_id
            reinf = turn_ev["payload"]["reinforcements_available"]
            assert reinf > 0, f"{actor_id}: sin refuerzos en su propio turno"

            legal = _recv_track(ws_actor, "legal.actions", bucket)
            reinforce_action = next(
                a for a in legal["payload"]["actions"]
                if a["action"] == "turn.place_reinforcement"
            )
            territory_id = reinforce_action["params"]["territories"][0]

            ws_actor.send_json({
                "type": "turn.place_reinforcement",
                "payload": {"territory_id": territory_id, "count": reinf},
            })
            upd = _recv_track(ws_actor, "territory.updated", bucket)
            assert upd["payload"]["turn"]["phase"] == "attack"

            # "algun ataque": duelo de dados sin territorio -- resuelve
            # attack.resolved pero no cambia tenencia ni elimina a nadie, asi
            # los 8 jugadores siguen teniendo turno en las 2 rondas
            target_id = order[(turno_idx + 1) % JUGADORES]
            ws_actor.send_json({
                "type": "attack",
                "payload": {"target_player_id": target_id, "attacker_dice_count": 3},
            })
            _recv_track(ws_actor, "attack.resolved", bucket)

            ws_actor.send_json({"type": "turn.end", "payload": {}})
            _recv_track(ws_actor, "turn.ended", bucket)

            # barrera real (bloquea hasta que llega): el resto de los 8
            # tiene que ver los mismos eventos publicos de este turno
            for other_pid, other_ws in zip(pids, wss):
                if other_pid == actor_id:
                    continue
                _recv_track(other_ws, "turn.ended", vistos[other_pid])

        # verificacion final: los 3 criterios de aceptacion, por cada uno de
        # los 8 clientes
        for pid in pids:
            mensajes = vistos[pid]

            seqs = [m.get("sequence_number", 0) for m in mensajes if m.get("sequence_number", 0) > 0]
            assert seqs, f"{pid}: no recibio ningun evento persistido"
            huecos = [(a, b) for a, b in zip(seqs, seqs[1:]) if b != a + 1]
            assert not huecos, (
                f"{pid}: huecos de secuencia {huecos}. Quedo algun evento "
                "persistido no publico consumiendo public_sequence."
            )

            incidentes = [m["event_type"] for m in mensajes if m.get("event_type") in EVENTOS_PROHIBIDOS]
            assert not incidentes, f"{pid}: incidentes inesperados {incidentes}"

            reconexiones = [
                m for m in mensajes
                if m.get("event_type") == "presence.changed"
                and m["payload"]["presence"] != "online"
            ]
            assert not reconexiones, f"{pid}: reconexion no provocada {reconexiones}"

            # eventos publicos que le corresponden
            tipos = [m["event_type"] for m in mensajes]
            assert tipos.count("placement.revealed") == 2, (
                f"{pid}: esperaba 2 placement.revealed (5 y 3), vio {tipos.count('placement.revealed')}"
            )
            propios = [m for m in mensajes if m.get("event_type") == "turn.started" and m.get("actor_id") == pid]
            assert len(propios) == RONDAS, (
                f"{pid}: esperaba {RONDAS} turnos propios, tuvo {len(propios)}"
            )
