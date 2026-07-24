"""Objetivos secretos: generación por mapa, cumplimiento y mutación."""

from teg_backend.domain.map import TerritoryState, load_map
from teg_backend.domain.objectives import (
    Objective,
    generate_objectives,
    is_fulfilled,
    mutate_if_needed,
)

GMAP = load_map("tactical-26")
PLAYERS = ["p1", "p2", "p3"]
NICKS = {"p1": "Daro", "p2": "Lord", "p3": "Chan"}


def _territories_owned_by(player_id, n):
    tids = list(GMAP.territories.keys())
    return {
        tid: TerritoryState(
            territory_id=tid,
            owner_player_id=player_id if i < n else "otro",
            armies=1,
        )
        for i, tid in enumerate(tids)
    }


def test_generate_one_objective_per_player_never_self_destroy():
    for _ in range(20):  # la generación es azarosa: repetir para cubrir familias
        objs = generate_objectives(GMAP, PLAYERS, NICKS)
        assert set(objs) == set(PLAYERS)
        for pid, obj in objs.items():
            assert obj.family in ("territories", "continents", "destroy")
            assert obj.title and obj.description
            if obj.family == "destroy":
                assert obj.params["target_player_id"] != pid


def test_territories_objective_fulfillment():
    total = len(GMAP.territories)
    n = max(3, round(total * 0.55))
    obj = Objective(
        id="o1", family="territories", params={"count": n}, title="t", description="d"
    )
    assert is_fulfilled(obj, "p1", _territories_owned_by("p1", n), GMAP, {})
    assert not is_fulfilled(obj, "p1", _territories_owned_by("p1", n - 1), GMAP, {})


def test_continents_objective_fulfillment():
    cid = next(iter(GMAP.continents))
    c_tids = [t.id for t in GMAP.territories.values() if t.continent_id == cid]
    extra_pool = [t.id for t in GMAP.territories.values() if t.continent_id != cid]
    obj = Objective(
        id="o2",
        family="continents",
        params={"continent_ids": [cid], "extra_territories": 2},
        title="t",
        description="d",
    )
    terrs = {
        tid: TerritoryState(territory_id=tid, owner_player_id="otro", armies=1)
        for tid in GMAP.territories
    }
    for tid in c_tids:
        terrs[tid].owner_player_id = "p1"
    assert not is_fulfilled(obj, "p1", terrs, GMAP, {})  # faltan los 2 extra
    terrs[extra_pool[0]].owner_player_id = "p1"
    terrs[extra_pool[1]].owner_player_id = "p1"
    assert is_fulfilled(obj, "p1", terrs, GMAP, {})


def test_destroy_objective_and_mutation():
    obj = Objective(
        id="o3",
        family="destroy",
        params={"target_player_id": "p2", "fallback_count": 10},
        title="t",
        description="d",
    )
    assert is_fulfilled(obj, "p1", {}, GMAP, {"p2": "p1"})
    assert not is_fulfilled(obj, "p1", {}, GMAP, {"p2": "p3"})
    mutated = mutate_if_needed(obj, {"p2": "p3"}, "p1")
    assert mutated.family == "territories" and mutated.params["count"] == 10
    same = mutate_if_needed(obj, {}, "p1")
    assert same.family == "destroy"
