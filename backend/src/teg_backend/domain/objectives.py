"""Objetivos secretos generados por mapa: N territorios, continentes o destruir."""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from typing import Any

from .map import GameMap, TerritoryState

_rng = secrets.SystemRandom()

FAMILIES = ("territories", "continents", "destroy")


@dataclass(slots=True)
class Objective:
    id: str
    family: str
    params: dict[str, Any]
    title: str
    description: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "family": self.family,
            "params": dict(self.params),
            "title": self.title,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Objective":
        return cls(
            id=str(data["id"]),
            family=str(data["family"]),
            params=dict(data.get("params", {})),
            title=str(data.get("title", "")),
            description=str(data.get("description", "")),
        )

    def public_view(self) -> dict[str, str]:
        return {"id": self.id, "title": self.title, "description": self.description}


def _target_count(gmap: GameMap) -> int:
    return max(3, round(len(gmap.territories) * 0.55))


def _territories_objective(gmap: GameMap, n: int) -> Objective:
    count = _target_count(gmap)
    return Objective(
        id=f"obj-terr-{n}",
        family="territories",
        params={"count": count},
        title=f"Conquistador de {count} territorios",
        description=f"Ocupá {count} territorios del mapa al mismo tiempo.",
    )


def _continents_objective(gmap: GameMap, n: int) -> Objective:
    cids = list(gmap.continents.keys())
    picked = _rng.sample(cids, k=min(2, len(cids)))
    extra = 2
    names = " y ".join(gmap.continents[c].name for c in picked)
    return Objective(
        id=f"obj-cont-{n}",
        family="continents",
        params={"continent_ids": picked, "extra_territories": extra},
        title=f"Dominio de {names}",
        description=f"Ocupá {names} completos más {extra} territorios de cualquier otro lado.",
    )


def _destroy_objective(
    gmap: GameMap, player_id: str, others: list[str], nicknames: dict[str, str], n: int
) -> Objective:
    target = _rng.choice(others)
    return Objective(
        id=f"obj-destroy-{n}",
        family="destroy",
        params={"target_player_id": target, "fallback_count": _target_count(gmap)},
        title=f"Destruir a {nicknames.get(target, 'tu rival')}",
        description=(
            f"Eliminá del mapa a {nicknames.get(target, 'tu rival')}. Si lo elimina otro, "
            f"tu objetivo pasa a ser ocupar {_target_count(gmap)} territorios."
        ),
    )


def generate_objectives(
    gmap: GameMap, player_ids: list[str], nicknames: dict[str, str]
) -> dict[str, Objective]:
    objectives: dict[str, Objective] = {}
    for n, pid in enumerate(player_ids):
        others = [p for p in player_ids if p != pid]
        families = list(FAMILIES) if len(others) >= 2 else ["territories", "continents"]
        family = _rng.choice(families)
        if family == "territories":
            objectives[pid] = _territories_objective(gmap, n)
        elif family == "continents":
            objectives[pid] = _continents_objective(gmap, n)
        else:
            objectives[pid] = _destroy_objective(gmap, pid, others, nicknames, n)
    return objectives


def is_fulfilled(
    obj: Objective,
    player_id: str,
    territories: dict[str, TerritoryState],
    gmap: GameMap,
    eliminated_by: dict[str, str],
) -> bool:
    if obj.family == "territories":
        owned = sum(1 for t in territories.values() if t.owner_player_id == player_id)
        return owned >= int(obj.params["count"])
    if obj.family == "continents":
        cids = set(obj.params["continent_ids"])
        in_continents = [t for t in gmap.territories.values() if t.continent_id in cids]
        if not all(
            territories.get(t.id) and territories[t.id].owner_player_id == player_id
            for t in in_continents
        ):
            return False
        extra_owned = sum(
            1
            for t in territories.values()
            if t.owner_player_id == player_id
            and gmap.territories[t.territory_id].continent_id not in cids
        )
        return extra_owned >= int(obj.params.get("extra_territories", 0))
    if obj.family == "destroy":
        target = obj.params["target_player_id"]
        return eliminated_by.get(target) == player_id
    return False


def mutate_if_needed(
    obj: Objective, eliminated_by: dict[str, str], player_id: str
) -> Objective:
    if obj.family != "destroy":
        return obj
    target = obj.params["target_player_id"]
    killer = eliminated_by.get(target)
    if killer is None or killer == player_id:
        return obj
    count = int(obj.params.get("fallback_count", 10))
    return Objective(
        id=obj.id + "-mutado",
        family="territories",
        params={"count": count},
        title=f"Conquistador de {count} territorios",
        description=(
            "A tu víctima la eliminó otro. Nuevo objetivo: "
            f"ocupá {count} territorios al mismo tiempo."
        ),
    )
