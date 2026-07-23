"""Motor autoritativo: dados, combate y turnos.

Todo azar sale de secrets.SystemRandom (no predecible, solo en servidor).
Las reglas completas del TEG (mapa, refuerzos, canje, objetivos) tienen
puntos de extensión marcados con TODO — no se inventan reglas dudosas.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from typing import Any

_rng = secrets.SystemRandom()

DICE_SIDES = 6
MAX_ATTACK_DICE = 3
MAX_DEFENSE_DICE = 3


class EngineError(Exception):
    pass


def roll_dice(count: int) -> list[int]:
    if not 1 <= count <= MAX_ATTACK_DICE:
        raise EngineError(f"cantidad de dados inválida: {count}")
    return sorted((_rng.randint(1, DICE_SIDES) for _ in range(count)), reverse=True)


@dataclass(slots=True)
class CombatResult:
    attacker_dice: list[int]
    defender_dice: list[int]
    attacker_losses: int
    defender_losses: int
    comparisons: list[dict[str, int]]


def resolve_combat(attacker_dice: list[int], defender_dice: list[int]) -> CombatResult:
    """Comparación clásica TEG: dados ordenados de mayor a menor, par a par.

    El empate favorece SIEMPRE al defensor.
    """
    a = sorted(attacker_dice, reverse=True)
    d = sorted(defender_dice, reverse=True)
    attacker_losses = 0
    defender_losses = 0
    comparisons: list[dict[str, int]] = []
    for av, dv in zip(a, d):
        if av > dv:
            defender_losses += 1
        else:
            attacker_losses += 1
        comparisons.append({"attacker": av, "defender": dv})
    return CombatResult(a, d, attacker_losses, defender_losses, comparisons)


@dataclass(slots=True)
class TurnState:
    order: list[str] = field(default_factory=list)
    index: int = 0
    turn_number: int = 0
    phase: str = "reinforcement"  # "reinforcement" | "attack" | "fortify"
    reinforcements_available: int = 3

    @property
    def current_player_id(self) -> str | None:
        if not self.order:
            return None
        return self.order[self.index]

    def to_dict(self) -> dict[str, Any]:
        return {
            "order": self.order,
            "index": self.index,
            "turn_number": self.turn_number,
            "phase": self.phase,
            "reinforcements_available": self.reinforcements_available,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TurnState":
        return cls(
            order=list(data.get("order", [])),
            index=int(data.get("index", 0)),
            turn_number=int(data.get("turn_number", 0)),
            phase=str(data.get("phase", "attack")),
            reinforcements_available=int(data.get("reinforcements_available", 0)),
        )


from teg_backend.domain.map import TerritoryState, load_default_map


class GameEngine:
    """Estado de partida en memoria. Se serializa a games.state_json en cada
    cambio de turno para sobrevivir reinicios del proceso."""

    def __init__(
        self,
        turn: TurnState | None = None,
        territories: dict[str, TerritoryState] | None = None,
    ) -> None:
        self.turn = turn or TurnState()
        self.territories = territories or {}

    def calculate_reinforcements(self, player_id: str | None) -> int:
        if not player_id or not self.territories:
            return 3
        owned = [t for t in self.territories.values() if t.owner_player_id == player_id]
        base = max(3, len(owned) // 2)

        # Bonus por continentes completos
        try:
            gmap = load_default_map()
            for cid, continent in gmap.continents.items():
                c_territories = [t for t in gmap.territories.values() if t.continent_id == cid]
                if c_territories and all(
                    self.territories.get(ct.id) and self.territories[ct.id].owner_player_id == player_id
                    for ct in c_territories
                ):
                    base += continent.bonus_armies
        except Exception:
            pass

        return base

    def start(self, player_ids: list[str]) -> TurnState:
        if len(player_ids) < 2:
            raise EngineError("se necesitan al menos 2 jugadores sentados")
        order = list(player_ids)
        _rng.shuffle(order)
        self.turn = TurnState(order=order, index=0, turn_number=1, phase="reinforcement")

        # Reparto inicial de territorios entre los jugadores sentados
        try:
            game_map = load_default_map()
            t_ids = list(game_map.territories.keys())
            _rng.shuffle(t_ids)
            self.territories = {}
            for idx, tid in enumerate(t_ids):
                owner = order[idx % len(order)]
                armies = _rng.randint(2, 4)
                self.territories[tid] = TerritoryState(
                    territory_id=tid, owner_player_id=owner, armies=armies
                )
        except Exception:
            self.territories = {}

        self.turn.reinforcements_available = self.calculate_reinforcements(self.turn.current_player_id)
        return self.turn

    def require_turn(self, player_id: str) -> None:
        if self.turn.current_player_id != player_id:
            raise EngineError("no es tu turno")

    def place_reinforcement(self, player_id: str, territory_id: str, count: int = 1) -> TerritoryState:
        self.require_turn(player_id)
        if self.turn.phase != "reinforcement":
            raise EngineError("no estás en la fase de refuerzos")
        if territory_id not in self.territories:
            raise EngineError("territorio inexistente")
        terr = self.territories[territory_id]
        if terr.owner_player_id != player_id:
            raise EngineError("el territorio no te pertenece")
        if count > self.turn.reinforcements_available:
            raise EngineError("no tenés suficientes refuerzos disponibles")

        terr.armies += count
        self.turn.reinforcements_available -= count
        if self.turn.reinforcements_available <= 0:
            self.turn.phase = "attack"
        return terr

    def fortify(self, player_id: str, source_id: str, target_id: str, count: int) -> tuple[TerritoryState, TerritoryState]:
        self.require_turn(player_id)
        if self.turn.phase != "fortify":
            raise EngineError("debes estar en la fase de reagrupamiento")
        if source_id not in self.territories or target_id not in self.territories:
            raise EngineError("territorios inválidos")
        src = self.territories[source_id]
        tgt = self.territories[target_id]
        if src.owner_player_id != player_id or tgt.owner_player_id != player_id:
            raise EngineError("ambos territorios deben ser tuyos")
        if count >= src.armies:
            raise EngineError("debes dejar al menos 1 ejército en el origen")

        src.armies -= count
        tgt.armies += count
        return src, tgt

    def next_phase(self, player_id: str) -> TurnState:
        self.require_turn(player_id)
        if self.turn.phase == "reinforcement":
            self.turn.phase = "attack"
        elif self.turn.phase == "attack":
            self.turn.phase = "fortify"
        elif self.turn.phase == "fortify":
            return self.advance_turn()
        return self.turn

    def advance_turn(self) -> TurnState:
        if not self.turn.order:
            raise EngineError("la partida no está iniciada")
        self.turn.index = (self.turn.index + 1) % len(self.turn.order)
        self.turn.turn_number += 1
        self.turn.phase = "reinforcement"
        self.turn.reinforcements_available = self.calculate_reinforcements(self.turn.current_player_id)
        return self.turn

    def remove_player(self, player_id: str) -> None:
        """Saca a un jugador del orden de turnos (kick o eliminación)."""
        if player_id not in self.turn.order:
            return
        current = self.turn.current_player_id
        self.turn.order.remove(player_id)
        if not self.turn.order:
            self.turn.index = 0
            return
        if current == player_id:
            self.turn.index %= len(self.turn.order)
        else:
            self.turn.index = self.turn.order.index(current)

    def to_dict(self) -> dict[str, Any]:
        return {
            "turn": self.turn.to_dict(),
            "territories": {tid: t.to_dict() for tid, t in self.territories.items()},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GameEngine":
        raw_terr = data.get("territories", {})
        territories = {
            tid: TerritoryState.from_dict(tdata) for tid, tdata in raw_terr.items()
        }
        return cls(
            turn=TurnState.from_dict(data.get("turn", {})),
            territories=territories,
        )


# ---------------------------------------------------------------------------
# Puntos de extensión de reglas TEG completas.
#
# TODO(teg-rules): refuerzos por ronda y por continente controlado.
# TODO(teg-rules): conquista de territorio (requiere mapa y ejércitos; ver
#   domain/map.py). attack.resolved hoy solo informa bajas de la tirada.
# TODO(teg-rules): reagrupamiento al final del turno.
# TODO(teg-rules): canje de tarjetas de país.
# TODO(teg-rules): objetivos secretos y condición de victoria automática.
# TODO(teg-rules): alianzas y su ruptura.
# TODO(teg-rules): eliminación automática al perder el último territorio.
# ---------------------------------------------------------------------------
