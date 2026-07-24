"""Heurísticas del jugador IA: decide jugadas legales mirando el motor.

Funciones puras (motor entra, decisión sale): fáciles de testear y de
razonar. El bot no es un genio: es un rival digno que nunca traba la partida.
"""

from __future__ import annotations

import secrets

from ..domain.engine import GameEngine

_rng = secrets.SystemRandom()


def _own_territories(engine: GameEngine, player_id: str) -> list[str]:
    return [t.territory_id for t in engine.territories.values()
            if t.owner_player_id == player_id]


def _enemy_neighbors(engine: GameEngine, tid: str, player_id: str) -> list[str]:
    return [
        n for n in engine.map.territories[tid].neighbor_ids
        if engine.territories[n].owner_player_id != player_id
    ]


def _objective_priority(engine: GameEngine, player_id: str, target_tid: str) -> int:
    """Cuánto acerca este territorio al objetivo secreto (mayor = mejor)."""
    obj = engine.objectives.get(player_id)
    if obj is None:
        return 0
    if obj.family == "continents":
        cids = set(obj.params.get("continent_ids", []))
        if engine.map.territories[target_tid].continent_id in cids:
            return 2
    if obj.family == "destroy":
        owner = engine.territories[target_tid].owner_player_id
        if owner == obj.params.get("target_player_id"):
            return 2
    return 0


def threat_level(engine: GameEngine, tid: str, player_id: str) -> int:
    """Presión enemiga sobre un territorio propio: tropas enemigas vecinas - propias."""
    enemy_armies = sum(
        engine.territories[n].armies
        for n in _enemy_neighbors(engine, tid, player_id)
    )
    return enemy_armies - engine.territories[tid].armies


def choose_placement(engine: GameEngine, player_id: str) -> str:
    """Colocación inicial: reforzar el territorio propio más amenazado."""
    own = _own_territories(engine, player_id)
    borders = [t for t in own if _enemy_neighbors(engine, t, player_id)]
    pool = borders or own
    return max(pool, key=lambda t: threat_level(engine, t, player_id))


def choose_reinforcement(engine: GameEngine, player_id: str) -> str:
    """Refuerzos: frontera más caliente, con sesgo hacia el objetivo."""
    own = _own_territories(engine, player_id)
    borders = [t for t in own if _enemy_neighbors(engine, t, player_id)]
    pool = borders or own

    def score(tid: str) -> tuple[int, int]:
        near_objective = max(
            (_objective_priority(engine, player_id, n)
             for n in _enemy_neighbors(engine, tid, player_id)),
            default=0,
        )
        return (near_objective, threat_level(engine, tid, player_id))

    return max(pool, key=score)


def choose_attack(engine: GameEngine, player_id: str) -> tuple[str, str] | None:
    """Mejor ataque con ventaja razonable, o None si no conviene atacar."""
    options: list[tuple[int, int, str, str]] = []
    for tid in _own_territories(engine, player_id):
        armies = engine.territories[tid].armies
        if armies < 2:
            continue
        for n in _enemy_neighbors(engine, tid, player_id):
            defender = engine.territories[n].armies
            advantage = (armies - 1) - defender
            # ataca con ventaja; con mucha tropa acepta hasta paridad
            if advantage >= 1 or (advantage == 0 and armies >= 4):
                options.append((
                    _objective_priority(engine, player_id, n), advantage, tid, n,
                ))
    if not options:
        return None
    options.sort(key=lambda o: (o[0], o[1]), reverse=True)
    _, _, src, tgt = options[0]
    return src, tgt


def choose_fortify(engine: GameEngine, player_id: str) -> tuple[str, str, int] | None:
    """Mueve tropas ociosas del interior hacia una frontera vecina."""
    best: tuple[int, str, str, int] | None = None
    for tid in _own_territories(engine, player_id):
        terr = engine.territories[tid]
        if terr.armies < 2 or _enemy_neighbors(engine, tid, player_id):
            continue  # solo interiores con tropas de sobra
        for n in engine.map.territories[tid].neighbor_ids:
            if engine.territories[n].owner_player_id != player_id:
                continue
            pressure = threat_level(engine, n, player_id)
            if not _enemy_neighbors(engine, n, player_id):
                continue  # el destino también es interior: no aporta
            count = terr.armies - 1
            if best is None or pressure > best[0]:
                best = (pressure, tid, n, count)
    if best is None:
        return None
    _, src, tgt, count = best
    return src, tgt, count
