"""Tarjetas de país TEG: mazo, tríos y canje escalonado (4, 7, 10, +5)."""

from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from typing import Any

_rng = secrets.SystemRandom()

SYMBOLS = ("ship", "cannon", "balloon")
TRADE_VALUES = (4, 7, 10)


class CardsError(Exception):
    pass


@dataclass(slots=True)
class Card:
    id: str
    territory_id: str
    symbol: str

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "territory_id": self.territory_id, "symbol": self.symbol}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Card":
        return cls(
            id=str(data["id"]),
            territory_id=str(data.get("territory_id", "")),
            symbol=str(data.get("symbol", "ship")),
        )


def build_deck(territory_ids: list[str], jokers: int = 2) -> list[Card]:
    tids = list(territory_ids)
    _rng.shuffle(tids)
    deck = [
        Card(id=f"card-{tid}", territory_id=tid, symbol=SYMBOLS[i % len(SYMBOLS)])
        for i, tid in enumerate(tids)
    ]
    deck.extend(
        Card(id=f"card-joker-{n}", territory_id="", symbol="joker") for n in range(jokers)
    )
    _rng.shuffle(deck)
    return deck


def trade_value(trades_done: int) -> int:
    if trades_done < len(TRADE_VALUES):
        return TRADE_VALUES[trades_done]
    return TRADE_VALUES[-1] + 5 * (trades_done - len(TRADE_VALUES) + 1)


def is_valid_trio(cards: list[Card]) -> bool:
    if len(cards) != 3:
        return False
    plain = [c.symbol for c in cards if c.symbol != "joker"]
    # el comodín completa cualquier trío: sin comodines deben ser 3 iguales
    # o 3 distintas; con comodines, el resto igual o todo distinto también vale
    return len(set(plain)) in (0, 1) or len(set(plain)) == len(plain)


@dataclass(slots=True)
class CardsState:
    deck: list[Card] = field(default_factory=list)
    hands: dict[str, list[Card]] = field(default_factory=dict)
    discard: list[Card] = field(default_factory=list)
    trades_done: dict[str, int] = field(default_factory=dict)
    bonus_uses: dict[str, int] = field(default_factory=dict)  # card_id -> veces (máx 2)

    def to_dict(self) -> dict[str, Any]:
        return {
            "deck": [c.to_dict() for c in self.deck],
            "hands": {pid: [c.to_dict() for c in cards] for pid, cards in self.hands.items()},
            "discard": [c.to_dict() for c in self.discard],
            "trades_done": dict(self.trades_done),
            "bonus_uses": dict(self.bonus_uses),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CardsState":
        return cls(
            deck=[Card.from_dict(c) for c in data.get("deck", [])],
            hands={
                pid: [Card.from_dict(c) for c in cards]
                for pid, cards in data.get("hands", {}).items()
            },
            discard=[Card.from_dict(c) for c in data.get("discard", [])],
            trades_done={k: int(v) for k, v in data.get("trades_done", {}).items()},
            bonus_uses={k: int(v) for k, v in data.get("bonus_uses", {}).items()},
        )
