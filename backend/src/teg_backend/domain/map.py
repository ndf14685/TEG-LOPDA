"""Modelo de mapa (países, continentes, fronteras, ejércitos).

Los datos viven en maps_data.py; acá está el modelo y el registro de mapas
jugables (tactical-26, world-50, mega-100).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Continent:
    id: str
    name: str
    bonus_armies: int


@dataclass(slots=True)
class Territory:
    id: str
    name: str
    continent_id: str
    neighbor_ids: frozenset[str] = frozenset()


@dataclass(slots=True)
class TerritoryState:
    territory_id: str
    owner_player_id: str | None = None
    armies: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            # "id" es el nombre del contrato TS (shared/contracts/src/map.ts);
            # "territory_id" se mantiene por compatibilidad con eventos previos
            "id": self.territory_id,
            "territory_id": self.territory_id,
            "owner_player_id": self.owner_player_id,
            "armies": self.armies,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TerritoryState:
        return cls(
            territory_id=data.get("territory_id", ""),
            owner_player_id=data.get("owner_player_id"),
            armies=int(data.get("armies", 0)),
        )


@dataclass(slots=True)
class GameMap:
    continents: dict[str, Continent] = field(default_factory=dict)
    territories: dict[str, Territory] = field(default_factory=dict)

    def validate(self) -> None:
        for t in self.territories.values():
            if t.continent_id not in self.continents:
                raise ValueError(f"territorio {t.id} apunta a continente inexistente")
            for n in t.neighbor_ids:
                if n not in self.territories:
                    raise ValueError(f"frontera inválida {t.id} -> {n}")
                if t.id not in self.territories[n].neighbor_ids:
                    raise ValueError(f"frontera no simétrica {t.id} <-> {n}")


from functools import lru_cache

from .maps_data import MAPS


@lru_cache(maxsize=None)
def load_map(map_id: str) -> GameMap:
    """Construye y valida el mapa `map_id` ("tactical-26" | "world-50" | "mega-100")."""
    if map_id not in MAPS:
        raise ValueError(f"mapa desconocido: {map_id}")
    continents_raw, territories_raw = MAPS[map_id]
    continents = {cid: Continent(cid, name, bonus) for cid, (name, bonus) in continents_raw.items()}
    territories = {
        tid: Territory(tid, name, continent, frozenset(neighbors))
        for tid, (name, continent, neighbors) in territories_raw.items()
    }
    game_map = GameMap(continents=continents, territories=territories)
    game_map.validate()
    return game_map


def load_default_map() -> GameMap:
    """Compatibilidad: el mapa del MVP original."""
    return load_map("tactical-26")
