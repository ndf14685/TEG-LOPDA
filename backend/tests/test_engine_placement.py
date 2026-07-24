"""Colocación inicial 5+3 simultánea y oculta."""

import pytest

from teg_backend.domain.engine import EngineError, GameEngine


def _engine():
    e = GameEngine(map_id="tactical-26")
    e.start(["p1", "p2"])
    return e


def _own(e, pid):
    return [t.territory_id for t in e.territories.values() if t.owner_player_id == pid]


def test_start_deals_one_army_and_enters_placement():
    e = _engine()
    assert e.stage == "placement_1"
    assert all(t.armies == 1 for t in e.territories.values())
    assert e.placement_pools == {"p1": 5, "p2": 5}


def test_placement_is_hidden_until_all_done():
    e = _engine()
    t1 = _own(e, "p1")[0]
    r = e.place_initial("p1", t1, 5)
    assert r["remaining"] == 0 and r["revealed"] is None
    assert e.territories[t1].armies == 1  # oculto: aún no se aplica
    t2 = _own(e, "p2")[0]
    r = e.place_initial("p2", t2, 5)
    assert r["revealed"] is not None
    assert r["revealed"]["stage_completed"] == "placement_1"
    assert r["revealed"]["next_stage"] == "placement_2"
    assert e.territories[t1].armies == 6  # ahora sí
    assert e.placement_pools == {"p1": 3, "p2": 3}


def test_placement_validations():
    e = _engine()
    ajeno = _own(e, "p2")[0]
    with pytest.raises(EngineError):
        e.place_initial("p1", ajeno, 1)  # no es tuyo
    mio = _own(e, "p1")[0]
    with pytest.raises(EngineError):
        e.place_initial("p1", mio, 6)  # más que el pool
    e.place_initial("p1", mio, 5)
    with pytest.raises(EngineError):
        e.place_initial("p1", mio, 1)  # pool agotado


def test_completing_both_rounds_enters_turns():
    e = _engine()
    for pid in ("p1", "p2"):
        e.place_initial(pid, _own(e, pid)[0], 5)
    for pid in ("p1", "p2"):
        r = e.place_initial(pid, _own(e, pid)[0], 3)
    assert r["revealed"]["next_stage"] == "turns"
    assert e.stage == "turns"
    assert e.turn.reinforcements_available >= 3


def test_turn_actions_blocked_during_placement():
    e = _engine()
    with pytest.raises(EngineError):
        e.require_turn(e.turn.current_player_id)


def test_from_dict_old_saves_default_to_turns():
    e = _engine()
    data = e.to_dict()
    del data["stage"]
    loaded = GameEngine.from_dict(data)
    assert loaded.stage == "turns"
