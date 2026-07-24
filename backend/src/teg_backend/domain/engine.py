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
PLACEMENT_ROUNDS = (5, 3)  # colocación inicial TEG: 5 ejércitos y luego 3


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


from teg_backend.domain.cards import (
    Card, CardsState, build_deck, is_valid_trio, trade_value,
)
from teg_backend.domain.map import GameMap, TerritoryState, load_map
from teg_backend.domain.objectives import (
    Objective, generate_objectives, is_fulfilled, mutate_if_needed,
)

DEFAULT_MAP_ID = "tactical-26"


class GameEngine:
    """Estado de partida en memoria. Se serializa a games.state_json en cada
    cambio de turno para sobrevivir reinicios del proceso."""

    def __init__(
        self,
        turn: TurnState | None = None,
        territories: dict[str, TerritoryState] | None = None,
        map_id: str = DEFAULT_MAP_ID,
        stage: str = "turns",
        placement_pools: dict[str, int] | None = None,
        placement_pending: dict[str, dict[str, int]] | None = None,
    ) -> None:
        self.turn = turn or TurnState()
        self.territories = territories or {}
        self.map_id = map_id
        self.stage = stage
        self.placement_pools = placement_pools or {}
        self.placement_pending = placement_pending or {}
        self.cards = CardsState()
        self.objectives: dict[str, Objective] = {}
        self.eliminated_by: dict[str, str] = {}
        self.conquered_this_turn = False

    @property
    def map(self) -> GameMap:
        return load_map(self.map_id)

    def are_neighbors(self, a: str, b: str) -> bool:
        terr = self.map.territories.get(a)
        return terr is not None and b in terr.neighbor_ids

    def calculate_reinforcements(self, player_id: str | None) -> int:
        if not player_id or not self.territories:
            return 3
        owned = [t for t in self.territories.values() if t.owner_player_id == player_id]
        base = max(3, len(owned) // 2)

        # Bonus por continentes completos
        try:
            gmap = self.map
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
        t_ids = list(self.map.territories.keys())
        _rng.shuffle(t_ids)
        self.territories = {}
        for idx, tid in enumerate(t_ids):
            owner = order[idx % len(order)]
            # reparto TEG: 1 ejército por país; el resto se coloca en 5+3
            self.territories[tid] = TerritoryState(
                territory_id=tid, owner_player_id=owner, armies=1
            )

        self.stage = "placement_1"
        self.placement_pools = {pid: PLACEMENT_ROUNDS[0] for pid in order}
        self.placement_pending = {}
        self.cards = CardsState(
            deck=build_deck(list(self.map.territories.keys())),
            hands={pid: [] for pid in order},
        )
        self.objectives = {}
        self.eliminated_by = {}
        self.conquered_this_turn = False
        self.turn.reinforcements_available = 0  # se calcula al entrar a "turns"
        return self.turn

    def place_initial(self, player_id: str, territory_id: str, count: int = 1) -> dict:
        if self.stage not in ("placement_1", "placement_2"):
            raise EngineError("no estás en colocación inicial")
        pool = self.placement_pools.get(player_id)
        if pool is None:
            raise EngineError("no participás de la colocación")
        if count < 1 or count > pool:
            raise EngineError(f"tenés {pool} ejércitos por colocar")
        terr = self.territories.get(territory_id)
        if terr is None or terr.owner_player_id != player_id:
            raise EngineError("el territorio no te pertenece")
        pending = self.placement_pending.setdefault(player_id, {})
        pending[territory_id] = pending.get(territory_id, 0) + count
        self.placement_pools[player_id] = pool - count
        revealed = None
        if all(p == 0 for p in self.placement_pools.values()):
            revealed = self._reveal_placement()
        return {"remaining": self.placement_pools.get(player_id, 0), "revealed": revealed}

    def _reveal_placement(self) -> dict:
        for pid, pending in self.placement_pending.items():
            for tid, n in pending.items():
                self.territories[tid].armies += n
        stage_completed = self.stage
        self.placement_pending = {}
        if self.stage == "placement_1":
            self.stage = "placement_2"
            self.placement_pools = {pid: PLACEMENT_ROUNDS[1] for pid in self.placement_pools}
        else:
            self.stage = "turns"
            self.placement_pools = {}
            self.turn.reinforcements_available = self.calculate_reinforcements(
                self.turn.current_player_id
            )
        return {
            "stage_completed": stage_completed,
            "territories": {tid: t.to_dict() for tid, t in self.territories.items()},
            "next_stage": self.stage,
        }

    def require_turn(self, player_id: str) -> None:
        if self.stage != "turns":
            raise EngineError("la partida está en colocación inicial")
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
        if not self.are_neighbors(source_id, target_id):
            raise EngineError("solo se reagrupa entre territorios limítrofes")
        if count >= src.armies:
            raise EngineError("debes dejar al menos 1 ejército en el origen")

        src.armies -= count
        tgt.armies += count
        return src, tgt

    def assign_objectives(self, nicknames: dict[str, str]) -> dict[str, Objective]:
        self.objectives = generate_objectives(self.map, list(self.turn.order), nicknames)
        return self.objectives

    def trade_cards(self, player_id: str, card_ids: list[str]) -> dict:
        self.require_turn(player_id)
        if self.turn.phase != "reinforcement":
            raise EngineError("el canje se hace en la fase de refuerzos")
        hand = self.cards.hands.get(player_id, [])
        picked = [c for c in hand if c.id in set(card_ids)]
        if len(card_ids) != 3 or len(picked) != 3:
            raise EngineError("elegí exactamente 3 tarjetas de tu mano")
        if not is_valid_trio(picked):
            raise EngineError("el trío no es válido: 3 iguales o 3 distintas")
        value = trade_value(self.cards.trades_done.get(player_id, 0))
        self.cards.trades_done[player_id] = self.cards.trades_done.get(player_id, 0) + 1
        self.turn.reinforcements_available += value
        country_bonuses = []
        for c in picked:
            terr = self.territories.get(c.territory_id)
            uses = self.cards.bonus_uses.get(c.id, 0)
            if terr and terr.owner_player_id == player_id and uses < 2:
                terr.armies += 2
                self.cards.bonus_uses[c.id] = uses + 1
                country_bonuses.append({"territory_id": c.territory_id, "armies_added": 2})
        self.cards.hands[player_id] = [c for c in hand if c.id not in set(card_ids)]
        self.cards.discard.extend(picked)
        return {"value": value, "cards": [c.to_dict() for c in picked],
                "country_bonuses": country_bonuses}

    def register_conquest(self, conqueror_id: str) -> None:
        self.conquered_this_turn = True

    def award_card_if_due(self, player_id: str) -> Card | None:
        if not self.conquered_this_turn or not self.cards.deck:
            self.conquered_this_turn = False
            return None
        self.conquered_this_turn = False
        card = self.cards.deck.pop()
        self.cards.hands.setdefault(player_id, []).append(card)
        return card

    def register_elimination(self, victim_id: str, killer_id: str) -> list[Card]:
        self.eliminated_by[victim_id] = killer_id
        inherited = self.cards.hands.pop(victim_id, [])
        self.cards.hands.setdefault(killer_id, []).extend(inherited)
        return inherited

    def check_victory(self) -> tuple[str, Objective] | None:
        order = list(self.turn.order)
        current = self.turn.current_player_id
        if current in order:  # el jugador actual se evalúa primero
            order.remove(current)
            order.insert(0, current)
        for pid in order:
            obj = self.objectives.get(pid)
            if obj is None:
                continue
            obj = mutate_if_needed(obj, self.eliminated_by, pid)
            self.objectives[pid] = obj
            if is_fulfilled(obj, pid, self.territories, self.map, self.eliminated_by):
                return pid, obj
        return None

    def legal_actions(self, player_id: str) -> list[dict]:
        """Acciones válidas ahora para este jugador (para UI y bot)."""
        if self.stage in ("placement_1", "placement_2"):
            remaining = self.placement_pools.get(player_id, 0)
            if remaining <= 0:
                return []
            own = [t.territory_id for t in self.territories.values()
                   if t.owner_player_id == player_id]
            return [{"action": "placement.place",
                     "params": {"territories": own, "remaining": remaining}}]
        if self.turn.current_player_id != player_id:
            return []
        actions: list[dict] = []
        hand = self.cards.hands.get(player_id, [])
        if self.turn.phase == "reinforcement":
            own = [t.territory_id for t in self.territories.values()
                   if t.owner_player_id == player_id]
            if self.turn.reinforcements_available > 0:
                actions.append({"action": "turn.place_reinforcement",
                                "params": {"territories": own,
                                           "remaining": self.turn.reinforcements_available}})
            if len(hand) >= 3:
                actions.append({"action": "cards.trade",
                                "params": {"hand": [c.to_dict() for c in hand],
                                           "forced": len(hand) >= 5}})
            if self.turn.reinforcements_available == 0 and len(hand) < 5:
                actions.append({"action": "turn.next_phase", "params": {}})
        elif self.turn.phase == "attack":
            sources = []
            for t in self.territories.values():
                if t.owner_player_id != player_id or t.armies < 2:
                    continue
                targets = [
                    n for n in self.map.territories[t.territory_id].neighbor_ids
                    if self.territories[n].owner_player_id != player_id
                ]
                if targets:
                    sources.append({"source": t.territory_id, "targets": sorted(targets)})
            if sources:
                actions.append({"action": "attack", "params": {"sources": sources}})
            actions.append({"action": "turn.next_phase", "params": {}})
            actions.append({"action": "turn.end", "params": {}})
        elif self.turn.phase == "fortify":
            moves = []
            for t in self.territories.values():
                if t.owner_player_id != player_id or t.armies < 2:
                    continue
                dests = [
                    n for n in self.map.territories[t.territory_id].neighbor_ids
                    if self.territories[n].owner_player_id == player_id
                ]
                if dests:
                    moves.append({"source": t.territory_id, "targets": sorted(dests),
                                  "max_count": t.armies - 1})
            if moves:
                actions.append({"action": "turn.fortify", "params": {"moves": moves}})
            actions.append({"action": "turn.end", "params": {}})
        return actions

    def next_phase(self, player_id: str) -> TurnState:
        self.require_turn(player_id)
        if self.turn.phase == "reinforcement":
            if self.turn.reinforcements_available > 0:
                raise EngineError("colocá todos tus refuerzos antes de atacar")
            if len(self.cards.hands.get(player_id, [])) >= 5:
                raise EngineError("tenés 5 tarjetas: el canje es obligatorio")
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
            "map_id": self.map_id,
            "turn": self.turn.to_dict(),
            "territories": {tid: t.to_dict() for tid, t in self.territories.items()},
            "stage": self.stage,
            "placement_pools": dict(self.placement_pools),
            "placement_pending": {p: dict(t) for p, t in self.placement_pending.items()},
            "cards": self.cards.to_dict(),
            "objectives": {pid: o.to_dict() for pid, o in self.objectives.items()},
            "eliminated_by": dict(self.eliminated_by),
            "conquered_this_turn": self.conquered_this_turn,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any], default_map_id: str = DEFAULT_MAP_ID) -> "GameEngine":
        raw_terr = data.get("territories", {})
        territories = {
            tid: TerritoryState.from_dict(tdata) for tid, tdata in raw_terr.items()
        }
        map_id = data.get("map_id")
        if not map_id:
            # partidas anteriores a los modos no guardaban map_id: si ya hay
            # territorios repartidos son del mapa 26; si no, es partida nueva
            map_id = DEFAULT_MAP_ID if territories else default_map_id
        engine = cls(
            turn=TurnState.from_dict(data.get("turn", {})),
            territories=territories,
            map_id=map_id,
            # partidas guardadas antes de la colocación inicial: ya estaban en turnos
            stage=str(data.get("stage", "turns")),
            placement_pools={k: int(v) for k, v in data.get("placement_pools", {}).items()},
            placement_pending={
                p: {t: int(n) for t, n in terr.items()}
                for p, terr in data.get("placement_pending", {}).items()
            },
        )
        engine.cards = CardsState.from_dict(data.get("cards", {}))
        engine.objectives = {
            pid: Objective.from_dict(o) for pid, o in data.get("objectives", {}).items()
        }
        engine.eliminated_by = dict(data.get("eliminated_by", {}))
        engine.conquered_this_turn = bool(data.get("conquered_this_turn", False))
        return engine


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
