"""Reglas de tarjetas de país: mazo, tríos y valor de canje escalonado."""

from teg_backend.domain.cards import (
    Card,
    CardsState,
    build_deck,
    is_valid_trio,
    trade_value,
)


def _c(symbol: str, tid: str = "t1") -> Card:
    return Card(id=f"card-{tid}-{symbol}", territory_id=tid, symbol=symbol)


def test_trade_value_escalates():
    assert [trade_value(n) for n in range(6)] == [4, 7, 10, 15, 20, 25]


def test_build_deck_covers_territories_plus_jokers():
    tids = [f"t{i}" for i in range(25)]
    deck = build_deck(tids, jokers=2)
    assert len(deck) == 27
    assert sorted(c.territory_id for c in deck if c.symbol != "joker") == sorted(tids)
    symbols = {c.symbol for c in deck}
    assert symbols == {"ship", "cannon", "balloon", "joker"}
    # reparto parejo: ningún símbolo domina (25/3 → 8 o 9 de cada uno)
    for s in ("ship", "cannon", "balloon"):
        assert 8 <= sum(1 for c in deck if c.symbol == s) <= 9


def test_valid_trios():
    assert is_valid_trio([_c("ship", "a"), _c("ship", "b"), _c("ship", "c")])
    assert is_valid_trio([_c("ship", "a"), _c("cannon", "b"), _c("balloon", "c")])
    assert is_valid_trio([_c("joker", "a"), _c("ship", "b"), _c("ship", "c")])
    assert is_valid_trio([_c("joker", "a"), _c("cannon", "b"), _c("balloon", "c")])
    assert not is_valid_trio([_c("ship", "a"), _c("ship", "b"), _c("cannon", "c")])
    assert not is_valid_trio([_c("ship", "a"), _c("ship", "b")])


def test_cards_state_roundtrip():
    deck = build_deck(["t1", "t2", "t3"], jokers=1)
    state = CardsState(
        deck=deck,
        hands={"p1": [deck[0]]},
        discard=[],
        trades_done={"p1": 2},
        bonus_uses={deck[0].id: 1},
    )
    loaded = CardsState.from_dict(state.to_dict())
    assert loaded.trades_done == {"p1": 2}
    assert loaded.hands["p1"][0].id == deck[0].id
    assert loaded.bonus_uses[deck[0].id] == 1
