"""Modelo de mapa (países, continentes, fronteras, ejércitos).

Todavía sin datos: el MVP juega turnos y dados sin tablero. Este módulo fija
el contrato para incorporar el mapa real sin tocar el resto del dominio.
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


def load_default_map() -> GameMap:
    continents = {
        "south-america": Continent("south-america", "América del Sur", 3),
        "north-america": Continent("north-america", "América del Norte", 5),
        "europe": Continent("europe", "Europa", 5),
        "africa": Continent("africa", "África", 3),
        "asia": Continent("asia", "Asia", 7),
        "oceania": Continent("oceania", "Oceanía", 2),
    }

    t_data = [
        # América del Sur
        ("territory-south-america-colombia", "Colombia", "south-america", {"territory-south-america-brazil", "territory-south-america-peru", "territory-north-america-mexico"}),
        ("territory-south-america-peru", "Perú", "south-america", {"territory-south-america-argentina", "territory-south-america-brazil", "territory-south-america-chile", "territory-south-america-colombia"}),
        ("territory-south-america-brazil", "Brasil", "south-america", {"territory-south-america-argentina", "territory-south-america-colombia", "territory-south-america-peru"}),
        ("territory-south-america-chile", "Chile", "south-america", {"territory-south-america-argentina", "territory-south-america-peru"}),
        ("territory-south-america-argentina", "Argentina", "south-america", {"territory-south-america-brazil", "territory-south-america-chile", "territory-south-america-peru"}),
        # América del Norte
        ("territory-north-america-mexico", "México", "north-america", {"territory-south-america-colombia", "territory-north-america-usa"}),
        ("territory-north-america-usa", "EE. UU.", "north-america", {"territory-north-america-mexico", "territory-north-america-canada"}),
        ("territory-north-america-canada", "Canadá", "north-america", {"territory-north-america-usa", "territory-north-america-alaska", "territory-europe-uk"}),
        ("territory-north-america-alaska", "Alaska", "north-america", {"territory-north-america-canada", "territory-asia-kamchatka"}),
        # Europa
        ("territory-europe-uk", "Reino Unido", "europe", {"territory-north-america-canada", "territory-europe-france", "territory-europe-germany"}),
        ("territory-europe-france", "Francia", "europe", {"territory-europe-uk", "territory-europe-spain", "territory-europe-germany"}),
        ("territory-europe-spain", "España", "europe", {"territory-europe-france", "territory-africa-sahara"}),
        ("territory-europe-germany", "Alemania", "europe", {"territory-europe-france", "territory-europe-uk", "territory-europe-russia"}),
        ("territory-europe-russia", "Rusia", "europe", {"territory-europe-germany", "territory-asia-middle-east", "territory-asia-siberia"}),
        # África
        ("territory-africa-sahara", "Sáhara", "africa", {"territory-europe-spain", "territory-africa-egypt", "territory-africa-congo"}),
        ("territory-africa-egypt", "Egipto", "africa", {"territory-africa-sahara", "territory-africa-congo", "territory-asia-middle-east"}),
        ("territory-africa-congo", "Congo", "africa", {"territory-africa-sahara", "territory-africa-egypt", "territory-africa-south-africa"}),
        ("territory-africa-south-africa", "Sudáfrica", "africa", {"territory-africa-congo"}),
        # Asia
        ("territory-asia-middle-east", "Oriente Medio", "asia", {"territory-europe-russia", "territory-africa-egypt", "territory-asia-india"}),
        ("territory-asia-india", "India", "asia", {"territory-asia-middle-east", "territory-asia-china"}),
        ("territory-asia-china", "China", "asia", {"territory-asia-india", "territory-asia-siberia", "territory-asia-japan", "territory-australia-western"}),
        ("territory-asia-siberia", "Siberia", "asia", {"territory-europe-russia", "territory-asia-china", "territory-asia-kamchatka"}),
        ("territory-asia-kamchatka", "Kamchatka", "asia", {"territory-asia-siberia", "territory-asia-japan", "territory-north-america-alaska"}),
        ("territory-asia-japan", "Japón", "asia", {"territory-asia-china", "territory-asia-kamchatka"}),
        # Oceanía
        ("territory-australia-western", "Australia Occidental", "oceania", {"territory-australia-eastern", "territory-asia-china"}),
        ("territory-australia-eastern", "Australia Oriental", "oceania", {"territory-australia-western"}),
    ]

    territories = {
        tid: Territory(tid, name, cid, frozenset(neighbors))
        for tid, name, cid, neighbors in t_data
    }

    game_map = GameMap(continents=continents, territories=territories)
    game_map.validate()
    return game_map

