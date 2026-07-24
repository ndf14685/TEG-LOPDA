"""Validación de los tres mapas jugables y del motor por modo."""

import pytest

from teg_backend.domain.engine import GameEngine
from teg_backend.domain.map import load_map


@pytest.mark.parametrize("map_id,expected_count", [
    ("tactical-26", 26),
    ("world-50", 50),
    ("mega-100", 100),
])
def test_maps_are_valid_and_sized(map_id, expected_count):
    gmap = load_map(map_id)  # validate() corre adentro: simetría de fronteras
    assert len(gmap.territories) == expected_count
    # conectividad: desde cualquier territorio se llega a todos (BFS)
    start = next(iter(gmap.territories))
    seen = {start}
    frontier = [start]
    while frontier:
        current = frontier.pop()
        for nb in gmap.territories[current].neighbor_ids:
            if nb not in seen:
                seen.add(nb)
                frontier.append(nb)
    assert seen == set(gmap.territories), f"mapa {map_id} tiene territorios inalcanzables"


def test_unknown_map_rejected():
    with pytest.raises(ValueError):
        load_map("mapa-inventado")


@pytest.mark.parametrize("map_id,count", [("tactical-26", 26), ("world-50", 50), ("mega-100", 100)])
def test_engine_distributes_full_map(map_id, count):
    engine = GameEngine(map_id=map_id)
    engine.start(["a", "b", "c"])
    assert len(engine.territories) == count
    owners = {t.owner_player_id for t in engine.territories.values()}
    assert owners == {"a", "b", "c"}


def test_engine_neighbors_and_fortify_adjacency():
    engine = GameEngine(map_id="tactical-26")
    engine.start(["a", "b"])
    assert engine.are_neighbors(
        "territory-south-america-argentina", "territory-south-america-chile"
    )
    assert not engine.are_neighbors(
        "territory-south-america-argentina", "territory-asia-japan"
    )
    # reagrupar entre no limítrofes se rechaza
    current = engine.turn.current_player_id
    engine.stage = "turns"  # el test manipula estado: saltea la colocación
    engine.turn.phase = "fortify"
    arg = engine.territories["territory-south-america-argentina"]
    jap = engine.territories["territory-asia-japan"]
    arg.owner_player_id = current
    arg.armies = 5
    jap.owner_player_id = current
    from teg_backend.domain.engine import EngineError

    with pytest.raises(EngineError, match="limítrofes"):
        engine.fortify(current, "territory-south-america-argentina", "territory-asia-japan", 1)


def test_engine_state_preserves_map_id():
    engine = GameEngine(map_id="world-50")
    engine.start(["a", "b"])
    restored = GameEngine.from_dict(engine.to_dict())
    assert restored.map_id == "world-50"
    assert len(restored.territories) == 50
    # estado legado (sin map_id) con territorios: era del mapa 26
    legacy = engine.to_dict()
    del legacy["map_id"]
    legacy_engine = GameEngine.from_dict(legacy, default_map_id="mega-100")
    assert legacy_engine.map_id == "tactical-26"
    # estado vacío (partida nueva): usa el mapa del modo
    fresh = GameEngine.from_dict({}, default_map_id="mega-100")
    assert fresh.map_id == "mega-100"
