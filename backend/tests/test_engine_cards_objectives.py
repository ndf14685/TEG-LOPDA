"""Tarjetas y objetivos integrados al motor."""

import pytest

from teg_backend.domain.cards import Card
from teg_backend.domain.engine import EngineError, GameEngine


def _engine_in_turns():
    e = GameEngine(map_id="tactical-26")
    e.start(["p1", "p2"])
    for rnd in (5, 3):
        for pid in ("p1", "p2"):
            tid = next(
                t.territory_id for t in e.territories.values()
                if t.owner_player_id == pid
            )
            e.place_initial(pid, tid, rnd)
    return e


def _hand(e, pid, symbols=("ship", "ship", "ship"), owned_first=False):
    tid = next(
        t.territory_id for t in e.territories.values() if t.owner_player_id == pid
    )
    cards = [
        Card(id=f"c{i}", territory_id=tid if (owned_first and i == 0) else "", symbol=s)
        for i, s in enumerate(symbols)
    ]
    e.cards.hands[pid] = cards
    return cards


def test_start_builds_deck():
    e = _engine_in_turns()
    # todos los territorios + 2 comodines, sin repartir ninguna
    assert len(e.cards.deck) == len(e.map.territories) + 2


def test_trade_adds_reinforcements_and_escalates():
    e = _engine_in_turns()
    pid = e.turn.current_player_id
    base = e.turn.reinforcements_available
    cards = _hand(e, pid)
    result = e.trade_cards(pid, [c.id for c in cards])
    assert result["value"] == 4
    assert e.turn.reinforcements_available == base + 4
    assert e.cards.hands[pid] == []
    cards = _hand(e, pid)
    assert e.trade_cards(pid, [c.id for c in cards])["value"] == 7


def test_trade_own_country_bonus_max_twice():
    e = _engine_in_turns()
    pid = e.turn.current_player_id
    cards = _hand(e, pid, owned_first=True)
    tid = cards[0].territory_id
    before = e.territories[tid].armies
    result = e.trade_cards(pid, [c.id for c in cards])
    assert result["country_bonuses"] == [{"territory_id": tid, "armies_added": 2}]
    assert e.territories[tid].armies == before + 2


def test_trade_rejects_invalid_trio_and_wrong_phase():
    e = _engine_in_turns()
    pid = e.turn.current_player_id
    cards = _hand(e, pid, symbols=("ship", "ship", "cannon"))
    with pytest.raises(EngineError):
        e.trade_cards(pid, [c.id for c in cards])
    e.turn.reinforcements_available = 0
    e.cards.hands[pid] = []
    e.next_phase(pid)  # → attack
    cards = _hand(e, pid)
    with pytest.raises(EngineError):
        e.trade_cards(pid, [c.id for c in cards])


def test_next_phase_blocked_with_pending_reinforcements_or_five_cards():
    e = _engine_in_turns()
    pid = e.turn.current_player_id
    assert e.turn.reinforcements_available > 0
    with pytest.raises(EngineError):
        e.next_phase(pid)  # refuerzos sin colocar
    e.turn.reinforcements_available = 0
    _hand(e, pid, symbols=("ship",) * 5)
    with pytest.raises(EngineError):
        e.next_phase(pid)  # canje obligatorio con 5


def test_award_card_on_conquest_and_inherit_on_elimination():
    e = _engine_in_turns()
    pid = e.turn.current_player_id
    other = next(p for p in e.turn.order if p != pid)
    assert e.award_card_if_due(pid) is None
    e.register_conquest(pid)
    card = e.award_card_if_due(pid)
    assert card is not None and e.cards.hands[pid] == [card]
    assert e.award_card_if_due(pid) is None  # flag reseteado
    e.cards.hands[other] = [Card(id="x", territory_id="", symbol="ship")]
    inherited = e.register_elimination(other, pid)
    assert [c.id for c in inherited] == ["x"]
    assert e.eliminated_by == {other: pid}
    assert any(c.id == "x" for c in e.cards.hands[pid])


def test_check_victory_by_territories_objective():
    e = _engine_in_turns()
    pid = e.turn.current_player_id
    e.assign_objectives({"p1": "Daro", "p2": "Lord"})
    from teg_backend.domain.objectives import Objective

    e.objectives[pid] = Objective(
        id="o", family="territories", params={"count": 1}, title="t", description="d"
    )
    winner = e.check_victory()
    assert winner is not None and winner[0] == pid


def test_legal_actions_by_phase():
    e = _engine_in_turns()
    pid = e.turn.current_player_id
    other = next(p for p in e.turn.order if p != pid)
    acts = {a["action"] for a in e.legal_actions(pid)}
    assert "turn.place_reinforcement" in acts and "turn.next_phase" not in acts
    assert e.legal_actions(other) == []
    e.turn.reinforcements_available = 0
    assert {a["action"] for a in e.legal_actions(pid)} == {"turn.next_phase"}
    e.next_phase(pid)
    acts = {a["action"] for a in e.legal_actions(pid)}
    assert "turn.end" in acts and "turn.next_phase" in acts
