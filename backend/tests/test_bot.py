"""El bot juega de verdad: heurísticas y partida completa entre bots."""

import time

from conftest import ADMIN, create_game, invite

from teg_backend.ai import bot
from teg_backend.domain.engine import GameEngine


def _engine_in_turns(players=("p1", "p2")):
    e = GameEngine(map_id="tactical-26")
    e.start(list(players))
    for rnd in (5, 3):
        for pid in players:
            tid = next(t.territory_id for t in e.territories.values()
                       if t.owner_player_id == pid)
            e.place_initial(pid, tid, rnd)
    return e


def test_choose_reinforcement_prefers_borders():
    e = _engine_in_turns()
    pid = e.turn.current_player_id
    tid = bot.choose_reinforcement(e, pid)
    assert e.territories[tid].owner_player_id == pid
    # con dos jugadores en mapa repartido, todo territorio elegido tiene frontera
    assert any(
        e.territories[n].owner_player_id != pid
        for n in e.map.territories[tid].neighbor_ids
    )


def test_choose_attack_requires_advantage():
    e = _engine_in_turns()
    pid = e.turn.current_player_id
    # sin ventaja en ningún lado: igualar todas las tropas a 1
    for t in e.territories.values():
        t.armies = 1
    assert bot.choose_attack(e, pid) is None
    # una ventaja clara aparece y la elige
    mine = next(t for t in e.territories.values() if t.owner_player_id == pid
                and any(e.territories[n].owner_player_id != pid
                        for n in e.map.territories[t.territory_id].neighbor_ids))
    mine.armies = 10
    pick = bot.choose_attack(e, pid)
    assert pick is not None and pick[0] == mine.territory_id


def test_choose_fortify_moves_idle_troops():
    e = _engine_in_turns()
    pid = e.turn.current_player_id
    # armar un interior: un territorio propio rodeado solo de propios
    for t in e.territories.values():
        t.owner_player_id = pid
        t.armies = 1
    other = next(p for p in e.turn.order if p != pid)
    # un enemigo en una punta para que exista frontera
    enemy_tid = next(iter(e.map.territories))
    e.territories[enemy_tid].owner_player_id = other
    interior = next(
        tid for tid in e.map.territories
        if enemy_tid not in e.map.territories[tid].neighbor_ids and tid != enemy_tid
        and any(enemy_tid in e.map.territories[n].neighbor_ids
                for n in e.map.territories[tid].neighbor_ids)
    )
    e.territories[interior].armies = 8
    move = bot.choose_fortify(e, pid)
    assert move is not None
    src, tgt, count = move
    assert src == interior and count == 7
    assert e.territories[tgt].owner_player_id == pid


def test_full_game_between_bots_reaches_victory(client):
    game = create_game(client, config={"commentator_enabled": False})
    for name in ("BotA", "BotB", "BotC"):
        invite(client, game["id"], name, role="ai_player")
    resp = client.post(f"/api/admin/games/{game['id']}/start", headers=ADMIN)
    assert resp.status_code == 200, resp.text

    deadline = time.time() + 90
    status = "running"
    while time.time() < deadline:
        detail = client.get(f"/api/admin/games/{game['id']}", headers=ADMIN).json()
        status = detail["game"]["status"]
        if status == "finished":
            break
        time.sleep(0.3)
    assert status == "finished", f"la partida de bots no terminó (estado {status})"

    events = client.get(f"/api/admin/games/{game['id']}/events", headers=ADMIN).json()["events"]
    types = {e["event_type"] for e in events}
    assert "territory.conquered" in types
    assert "game.finished" in types
