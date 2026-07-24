# Etapa 0 + Etapa 1: Infra + Motor TEG Canónico — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Dejar el juego con reglas TEG canónicas completas (colocación inicial 5+3 simultánea y oculta, tarjetas con canje escalonado, objetivos secretos con victoria automática, acciones legales, snapshots por turno) y la infraestructura saneada — jugable de punta a punta al terminar.

**Architecture:** Evolución incremental del backend FastAPI+SQLite existente (spec: `docs/superpowers/specs/2026-07-23-teg-lopda-juego-completo-design.md`). El estado del motor sigue viviendo en `games.state_json`; tarjetas/objetivos/colocación son campos nuevos de ese estado. Única tabla nueva: `turn_snapshots`. Eventos nuevos viajan por el envelope WS existente con visibilidad public/private.

**Tech Stack:** Python 3.12, FastAPI, aiosqlite, pytest; TypeScript, React 19, Zustand, zod, Vite, Playwright.

## Global Constraints

- Cero dependencias nuevas (backend y frontend).
- Todo azar del juego sale de `_rng = secrets.SystemRandom()` (nunca `random`).
- Comentarios, mensajes de error y textos de UI en castellano.
- `GameEngine.from_dict` debe cargar partidas guardadas viejas sin romper (defaults para todos los campos nuevos; partidas en curso viejas arrancan con `stage="turns"`).
- El envelope de eventos (`domain/events.py`) no se modifica; solo se agregan `EventType` nuevos.
- Ejecutar tests backend: `cd backend && python -m pytest -q` (deben pasar todos, los viejos incluidos).
- Ejecutar tests frontend: `cd frontend && pnpm vitest run`.
- Commits frecuentes con prefijos `feat(engine):`, `feat(backend):`, `feat(frontend):`, `fix(deploy):`, `test:`.

---

### Task 1: Etapa 0 — Caddy sirve el frontend y backup diario

**Files:**
- Modify: `deploy/caddy/Caddyfile`
- Modify: `docker-compose.yml` (servicio `caddy`: depends_on)
- Create: `deploy/scripts/install-backup-cron.sh`

**Interfaces:**
- Produces: edge HTTPS → frontend nginx (que ya proxya `/api`, `/ws`, `/health` al backend). Cron diario de backup.

- [ ] **Step 1: Reescribir el Caddyfile para apuntar al frontend**

Reemplazar la línea `reverse_proxy backend:8123` de `deploy/caddy/Caddyfile` por:

```caddyfile
    # el frontend nginx sirve la SPA y proxya /api, /ws y /health al backend
    reverse_proxy frontend:80
```

y actualizar el comentario de cabecera (`backend:8123` → `frontend:80` para el caso host).

- [ ] **Step 2: Declarar la dependencia en compose**

En `docker-compose.yml`, servicio `caddy`, agregar:

```yaml
    depends_on: [frontend]
```

- [ ] **Step 3: Crear el instalador del cron de backup**

Crear `deploy/scripts/install-backup-cron.sh`:

```bash
#!/usr/bin/env bash
# Instala el cron diario de backup de la DB (05:00) si no está ya instalado.
set -e
REPO_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
LINE="0 5 * * * $REPO_DIR/deploy/scripts/backup.sh >> $REPO_DIR/backups/backup.log 2>&1"
( crontab -l 2>/dev/null | grep -vF "deploy/scripts/backup.sh"; echo "$LINE" ) | crontab -
echo "✅ cron instalado: $LINE"
```

- [ ] **Step 4: Verificar**

Run: `bash -n deploy/scripts/install-backup-cron.sh && chmod +x deploy/scripts/install-backup-cron.sh && bash deploy/scripts/install-backup-cron.sh && crontab -l | grep backup.sh`
Expected: línea de cron presente. Además `docker compose config --quiet` sin errores.

- [ ] **Step 5: Commit**

```bash
git add deploy/caddy/Caddyfile docker-compose.yml deploy/scripts/install-backup-cron.sh
git commit -m "fix(deploy): edge Caddy sirve el frontend y backup diario por cron"
```

---

### Task 2: Migración `turn_snapshots` + repositorio

**Files:**
- Create: `backend/migrations/0002-turn-snapshots.sql`
- Modify: `backend/src/teg_backend/infrastructure/repository.py` (agregar al final)
- Test: `backend/tests/test_repository_snapshots.py`

**Interfaces:**
- Produces: `repo.save_turn_snapshot(db, game_id, turn_number, state: dict) -> None`, `repo.get_turn_snapshot(db, game_id, turn_number) -> dict | None`, `repo.list_snapshot_turns(db, game_id) -> list[int]`.

- [ ] **Step 1: Escribir el test que falla**

```python
"""Snapshots por turno: base del replay (Etapa 8)."""
import pytest

from teg_backend.infrastructure import repository as repo
from teg_backend.infrastructure.db import Database


@pytest.fixture()
async def db(tmp_path):
    database = Database(str(tmp_path / "t.db"))
    await database.connect()
    yield database
    await database.close()


async def _make_game(db):
    return await repo.create_game(db, "ABC123", "test", {})


@pytest.mark.anyio
async def test_save_and_get_turn_snapshot(db):
    game = await _make_game(db)
    state = {"turn": {"turn_number": 1}, "territories": {}}
    await repo.save_turn_snapshot(db, game["id"], 1, state)
    await repo.save_turn_snapshot(db, game["id"], 1, {"turn": {"turn_number": 1}, "x": 2})  # reemplaza
    await repo.save_turn_snapshot(db, game["id"], 2, state)
    got = await repo.get_turn_snapshot(db, game["id"], 1)
    assert got is not None and got["x"] == 2
    assert await repo.get_turn_snapshot(db, game["id"], 99) is None
    assert await repo.list_snapshot_turns(db, game["id"]) == [1, 2]
```

Nota: si `pytest.mark.anyio` no está configurado en el proyecto, usar el mismo patrón async que ya usen los tests existentes de repositorio; si no existe ninguno, agregar `anyio_backend` fixture: `@pytest.fixture def anyio_backend(): return "asyncio"`.

- [ ] **Step 2: Correr y ver el fallo**

Run: `cd backend && python -m pytest tests/test_repository_snapshots.py -q`
Expected: FAIL (`AttributeError: module ... has no attribute 'save_turn_snapshot'` o tabla inexistente).

- [ ] **Step 3: Crear la migración**

`backend/migrations/0002-turn-snapshots.sql`:

```sql
-- Snapshot del estado del motor al inicio de cada turno (base del replay).
CREATE TABLE IF NOT EXISTS turn_snapshots (
    game_id TEXT NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    turn_number INTEGER NOT NULL,
    state_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (game_id, turn_number)
);
```

- [ ] **Step 4: Implementar las funciones de repositorio**

Agregar al final de `repository.py` (usar el mismo estilo `json.dumps`/`json.loads` del archivo):

```python
# --- snapshots por turno (replay) ------------------------------------------

async def save_turn_snapshot(db: Database, game_id: str, turn_number: int, state: dict) -> None:
    await db.execute(
        "INSERT OR REPLACE INTO turn_snapshots (game_id, turn_number, state_json)"
        " VALUES (?, ?, ?)",
        (game_id, int(turn_number), json.dumps(state, ensure_ascii=False)),
    )


async def get_turn_snapshot(db: Database, game_id: str, turn_number: int) -> dict | None:
    row = await db.fetchone(
        "SELECT state_json FROM turn_snapshots WHERE game_id = ? AND turn_number = ?",
        (game_id, int(turn_number)),
    )
    return json.loads(row["state_json"]) if row else None


async def list_snapshot_turns(db: Database, game_id: str) -> list[int]:
    rows = await db.fetchall(
        "SELECT turn_number FROM turn_snapshots WHERE game_id = ? ORDER BY turn_number",
        (game_id,),
    )
    return [int(r["turn_number"]) for r in rows]
```

- [ ] **Step 5: Verificar y commitear**

Run: `cd backend && python -m pytest tests/test_repository_snapshots.py -q` → PASS; luego `python -m pytest -q` → todo verde.

```bash
git add backend/migrations/0002-turn-snapshots.sql backend/src/teg_backend/infrastructure/repository.py backend/tests/test_repository_snapshots.py
git commit -m "feat(backend): tabla turn_snapshots y acceso de repositorio"
```

---

### Task 3: Dominio de tarjetas (`domain/cards.py`)

**Files:**
- Create: `backend/src/teg_backend/domain/cards.py`
- Test: `backend/tests/test_cards.py`

**Interfaces:**
- Produces:
  - `Card(id: str, territory_id: str, symbol: str)` con `to_dict() -> dict` / `Card.from_dict(d) -> Card`. `symbol ∈ {"ship","cannon","balloon","joker"}` (nombres del contrato TS `CardSymbol`).
  - `CardsState(deck: list[Card], hands: dict[str, list[Card]], discard: list[Card], trades_done: dict[str, int], bonus_uses: dict[str, int])` con `to_dict()`/`from_dict()`.
  - `build_deck(territory_ids: list[str], jokers: int = 2) -> list[Card]` (barajado, símbolos repartidos parejo).
  - `trade_value(trades_done: int) -> int` — 4, 7, 10, luego +5 acumulativo.
  - `is_valid_trio(cards: list[Card]) -> bool` — 3 iguales o 3 distintas; el comodín completa cualquier trío.
  - `CardsError(Exception)`.

- [ ] **Step 1: Escribir los tests que fallan**

```python
"""Reglas de tarjetas de país: mazo, tríos y valor de canje escalonado."""
import pytest

from teg_backend.domain.cards import (
    Card, CardsError, CardsState, build_deck, is_valid_trio, trade_value,
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
    state = CardsState(deck=deck, hands={"p1": [deck[0]]}, discard=[],
                       trades_done={"p1": 2}, bonus_uses={deck[0].id: 1})
    loaded = CardsState.from_dict(state.to_dict())
    assert loaded.trades_done == {"p1": 2}
    assert loaded.hands["p1"][0].id == deck[0].id
    assert loaded.bonus_uses[deck[0].id] == 1
```

- [ ] **Step 2: Correr y ver el fallo**

Run: `cd backend && python -m pytest tests/test_cards.py -q`
Expected: FAIL con `ModuleNotFoundError: teg_backend.domain.cards`.

- [ ] **Step 3: Implementar `cards.py`**

```python
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
        return cls(id=str(data["id"]), territory_id=str(data.get("territory_id", "")),
                   symbol=str(data.get("symbol", "ship")))


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
    # el comodín completa cualquier trío
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
            hands={pid: [Card.from_dict(c) for c in cards]
                   for pid, cards in data.get("hands", {}).items()},
            discard=[Card.from_dict(c) for c in data.get("discard", [])],
            trades_done={k: int(v) for k, v in data.get("trades_done", {}).items()},
            bonus_uses={k: int(v) for k, v in data.get("bonus_uses", {}).items()},
        )
```

Ojo con `is_valid_trio`: con 3 símbolos sin comodín, `len(set(plain)) == len(plain)` solo es cierto si son las 3 distintas; `len(set(plain)) in (0, 1)` cubre todos comodines o resto igual. Verificar contra los casos del test (2 iguales + 1 distinta debe dar `False`: `set` tiene 2 elementos y `plain` 3 → False ✓).

- [ ] **Step 4: Verificar y commitear**

Run: `cd backend && python -m pytest tests/test_cards.py -q` → PASS.

```bash
git add backend/src/teg_backend/domain/cards.py backend/tests/test_cards.py
git commit -m "feat(engine): dominio de tarjetas de país con canje escalonado"
```

---

### Task 4: Dominio de objetivos secretos (`domain/objectives.py`)

**Files:**
- Create: `backend/src/teg_backend/domain/objectives.py`
- Test: `backend/tests/test_objectives.py`

**Interfaces:**
- Consumes: `GameMap` de `domain/map.py`, `TerritoryState`.
- Produces:
  - `Objective(id: str, family: str, params: dict, title: str, description: str)` con `to_dict()`/`from_dict()` y `public_view() -> dict` (`{id, title, description}` — coincide con el contrato TS `SecretObjective`).
  - `generate_objectives(gmap: GameMap, player_ids: list[str], nicknames: dict[str, str]) -> dict[str, Objective]` — uno por jugador, familias `"territories" | "continents" | "destroy"`.
  - `is_fulfilled(obj: Objective, player_id: str, territories: dict[str, TerritoryState], gmap: GameMap, eliminated_by: dict[str, str]) -> bool`
  - `mutate_if_needed(obj: Objective, eliminated_by: dict[str, str], player_id: str) -> Objective` — si el objetivo es `destroy` y al target lo eliminó otro, muta a `territories` con el N de fallback.

- [ ] **Step 1: Tests que fallan**

```python
"""Objetivos secretos: generación por mapa, cumplimiento y mutación."""
from teg_backend.domain.map import TerritoryState, load_map
from teg_backend.domain.objectives import (
    Objective, generate_objectives, is_fulfilled, mutate_if_needed,
)

GMAP = load_map("tactical-26")
PLAYERS = ["p1", "p2", "p3"]
NICKS = {"p1": "Daro", "p2": "Lord", "p3": "Chan"}


def _territories_owned_by(player_id, n):
    tids = list(GMAP.territories.keys())
    return {
        tid: TerritoryState(territory_id=tid,
                            owner_player_id=player_id if i < n else "otro", armies=1)
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
    obj = Objective(id="o1", family="territories", params={"count": n},
                    title="t", description="d")
    assert is_fulfilled(obj, "p1", _territories_owned_by("p1", n), GMAP, {})
    assert not is_fulfilled(obj, "p1", _territories_owned_by("p1", n - 1), GMAP, {})


def test_continents_objective_fulfillment():
    cid = next(iter(GMAP.continents))
    c_tids = [t.id for t in GMAP.territories.values() if t.continent_id == cid]
    extra_pool = [t.id for t in GMAP.territories.values() if t.continent_id != cid]
    obj = Objective(id="o2", family="continents",
                    params={"continent_ids": [cid], "extra_territories": 2},
                    title="t", description="d")
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
    obj = Objective(id="o3", family="destroy",
                    params={"target_player_id": "p2", "fallback_count": 10},
                    title="t", description="d")
    assert is_fulfilled(obj, "p1", {}, GMAP, {"p2": "p1"})
    assert not is_fulfilled(obj, "p1", {}, GMAP, {"p2": "p3"})
    mutated = mutate_if_needed(obj, {"p2": "p3"}, "p1")
    assert mutated.family == "territories" and mutated.params["count"] == 10
    same = mutate_if_needed(obj, {}, "p1")
    assert same.family == "destroy"
```

- [ ] **Step 2: Correr y ver el fallo**

Run: `cd backend && python -m pytest tests/test_objectives.py -q` → FAIL (módulo inexistente).

- [ ] **Step 3: Implementar `objectives.py`**

```python
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
        return {"id": self.id, "family": self.family, "params": dict(self.params),
                "title": self.title, "description": self.description}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Objective":
        return cls(id=str(data["id"]), family=str(data["family"]),
                   params=dict(data.get("params", {})),
                   title=str(data.get("title", "")), description=str(data.get("description", "")))

    def public_view(self) -> dict[str, str]:
        return {"id": self.id, "title": self.title, "description": self.description}


def _target_count(gmap: GameMap) -> int:
    return max(3, round(len(gmap.territories) * 0.55))


def _territories_objective(gmap: GameMap, n: int) -> Objective:
    count = _target_count(gmap)
    return Objective(
        id=f"obj-terr-{n}", family="territories", params={"count": count},
        title=f"Conquistador de {count} territorios",
        description=f"Ocupá {count} territorios del mapa al mismo tiempo.",
    )


def _continents_objective(gmap: GameMap, n: int) -> Objective:
    cids = list(gmap.continents.keys())
    picked = _rng.sample(cids, k=min(2, len(cids)))
    extra = 2
    names = " y ".join(gmap.continents[c].name for c in picked)
    return Objective(
        id=f"obj-cont-{n}", family="continents",
        params={"continent_ids": picked, "extra_territories": extra},
        title=f"Dominio de {names}",
        description=f"Ocupá {names} completos más {extra} territorios de cualquier otro lado.",
    )


def _destroy_objective(gmap: GameMap, player_id: str, others: list[str],
                       nicknames: dict[str, str], n: int) -> Objective:
    target = _rng.choice(others)
    return Objective(
        id=f"obj-destroy-{n}", family="destroy",
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
    obj: Objective, player_id: str, territories: dict[str, TerritoryState],
    gmap: GameMap, eliminated_by: dict[str, str],
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
            1 for t in territories.values()
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
        id=obj.id + "-mutado", family="territories", params={"count": count},
        title=f"Conquistador de {count} territorios",
        description=(
            "A tu víctima la eliminó otro. Nuevo objetivo: "
            f"ocupá {count} territorios al mismo tiempo."
        ),
    )
```

- [ ] **Step 4: Verificar y commitear**

Run: `cd backend && python -m pytest tests/test_objectives.py -q` → PASS.

```bash
git add backend/src/teg_backend/domain/objectives.py backend/tests/test_objectives.py
git commit -m "feat(engine): objetivos secretos por familias con mutación de destroy"
```

---

### Task 5: Motor — colocación inicial simultánea y oculta

**Files:**
- Modify: `backend/src/teg_backend/domain/engine.py`
- Test: `backend/tests/test_engine_placement.py`

**Interfaces:**
- Consumes: nada nuevo.
- Produces (en `GameEngine`):
  - Campo `stage: str` — `"placement_1" | "placement_2" | "turns"`. Campo `placement_pools: dict[str, int]`, `placement_pending: dict[str, dict[str, int]]`.
  - `start(player_ids)` ahora reparte territorios con **1 ejército** cada uno y arranca en `stage="placement_1"` con pools de 5.
  - `place_initial(player_id, territory_id, count=1) -> dict` con claves `remaining: int` y `revealed: dict | None`; al completarse todos, `revealed = {"stage_completed": str, "territories": {tid: dict}, "next_stage": str}` (aplica pendientes y pasa a `placement_2` con pools de 3, o a `turns` calculando refuerzos del primer jugador).
  - `require_turn` ahora también exige `stage == "turns"`.
  - Constantes `PLACEMENT_ROUNDS = (5, 3)`.
  - `to_dict`/`from_dict` serializan `stage`, `placement_pools`, `placement_pending` (default `stage="turns"` para partidas viejas).

- [ ] **Step 1: Tests que fallan**

```python
"""Colocación inicial 5+3 simultánea y oculta."""
import pytest

from teg_backend.domain.engine import EngineError, GameEngine


def _engine():
    e = GameEngine(map_id="tactical-26")
    e.start(["p1", "p2"])
    return e


def _own(e, pid):
    return [t.territory_id for t in e.territories.values() if t.owner_player_id == pid]


def test_start_deals_one_army_and_enters_placement():
    e = _engine()
    assert e.stage == "placement_1"
    assert all(t.armies == 1 for t in e.territories.values())
    assert e.placement_pools == {"p1": 5, "p2": 5}


def test_placement_is_hidden_until_all_done():
    e = _engine()
    t1 = _own(e, "p1")[0]
    r = e.place_initial("p1", t1, 5)
    assert r["remaining"] == 0 and r["revealed"] is None
    assert e.territories[t1].armies == 1  # oculto: aún no se aplica
    t2 = _own(e, "p2")[0]
    r = e.place_initial("p2", t2, 5)
    assert r["revealed"] is not None
    assert r["revealed"]["stage_completed"] == "placement_1"
    assert r["revealed"]["next_stage"] == "placement_2"
    assert e.territories[t1].armies == 6  # ahora sí
    assert e.placement_pools == {"p1": 3, "p2": 3}


def test_placement_validations():
    e = _engine()
    ajeno = _own(e, "p2")[0]
    with pytest.raises(EngineError):
        e.place_initial("p1", ajeno, 1)  # no es tuyo
    mio = _own(e, "p1")[0]
    with pytest.raises(EngineError):
        e.place_initial("p1", mio, 6)  # más que el pool
    e.place_initial("p1", mio, 5)
    with pytest.raises(EngineError):
        e.place_initial("p1", mio, 1)  # pool agotado


def test_completing_both_rounds_enters_turns():
    e = _engine()
    for pid in ("p1", "p2"):
        e.place_initial(pid, _own(e, pid)[0], 5)
    for pid in ("p1", "p2"):
        r = e.place_initial(pid, _own(e, pid)[0], 3)
    assert r["revealed"]["next_stage"] == "turns"
    assert e.stage == "turns"
    assert e.turn.reinforcements_available >= 3


def test_turn_actions_blocked_during_placement():
    e = _engine()
    with pytest.raises(EngineError):
        e.require_turn(e.turn.current_player_id)


def test_from_dict_old_saves_default_to_turns():
    e = _engine()
    data = e.to_dict()
    del data["stage"]
    loaded = GameEngine.from_dict(data)
    assert loaded.stage == "turns"
```

- [ ] **Step 2: Correr y ver el fallo**

Run: `cd backend && python -m pytest tests/test_engine_placement.py -q` → FAIL (`stage` inexistente).

- [ ] **Step 3: Implementar en `engine.py`**

Agregar constante tras `MAX_DEFENSE_DICE`:

```python
PLACEMENT_ROUNDS = (5, 3)  # colocación inicial TEG: 5 ejércitos y luego 3
```

En `GameEngine.__init__`, agregar parámetros/campos (con defaults compatibles):

```python
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
```

Reemplazar en `start()` el reparto (`armies = _rng.randint(2, 4)`) por `armies = 1` y al final (antes del `return`):

```python
        self.stage = "placement_1"
        self.placement_pools = {pid: PLACEMENT_ROUNDS[0] for pid in order}
        self.placement_pending = {}
        self.turn.reinforcements_available = 0  # se calcula al entrar a "turns"
```

Agregar métodos:

```python
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
```

En `require_turn`, agregar al inicio:

```python
        if self.stage != "turns":
            raise EngineError("la partida está en colocación inicial")
```

En `to_dict`, agregar claves:

```python
            "stage": self.stage,
            "placement_pools": dict(self.placement_pools),
            "placement_pending": {p: dict(t) for p, t in self.placement_pending.items()},
```

En `from_dict`, pasar al constructor:

```python
            stage=str(data.get("stage", "turns")),
            placement_pools={k: int(v) for k, v in data.get("placement_pools", {}).items()},
            placement_pending={
                p: {t: int(n) for t, n in terr.items()}
                for p, terr in data.get("placement_pending", {}).items()
            },
```

- [ ] **Step 4: Verificar todo el backend**

Run: `cd backend && python -m pytest tests/test_engine_placement.py -q` → PASS.
Run: `cd backend && python -m pytest -q` → los tests viejos de flujo WS van a **fallar** porque ahora la partida arranca en colocación — es esperado y se arreglan en la Task 7 (servicio). Anotar cuáles fallan; NO commitear roto: hacer este task y los Tasks 6–7 en la misma rama de trabajo y commitear al final de Task 7 si los tests viejos no pasan antes. Si preferís commit por task, marcá los tests de flujo con `@pytest.mark.xfail(reason="colocación inicial: se rehabilita en service", strict=False)` temporalmente **dentro de este mismo task** y quitá las marcas en Task 7.

```bash
git add backend/src/teg_backend/domain/engine.py backend/tests/test_engine_placement.py backend/tests/test_game_flow.py backend/tests/test_gameplay_rules.py
git commit -m "feat(engine): colocación inicial 5+3 simultánea y oculta con stages"
```

---

### Task 6: Motor — tarjetas, objetivos y acciones legales integrados

**Files:**
- Modify: `backend/src/teg_backend/domain/engine.py`
- Test: `backend/tests/test_engine_cards_objectives.py`

**Interfaces:**
- Consumes: `cards.py` (Task 3), `objectives.py` (Task 4).
- Produces (en `GameEngine`):
  - Campos: `cards: CardsState`, `objectives: dict[str, Objective]`, `eliminated_by: dict[str, str]`, `conquered_this_turn: bool`.
  - `start()` además: construye mazo (`build_deck` con 2 comodines) y NO asigna objetivos (los asigna el servicio, que conoce los apodos — ver firma `assign_objectives`).
  - `assign_objectives(nicknames: dict[str, str]) -> dict[str, Objective]` — genera y guarda objetivos.
  - `trade_cards(player_id, card_ids: list[str]) -> dict` — valida turno propio + fase `reinforcement` + trío válido; retorna `{"value": int, "cards": [dict], "country_bonuses": [{"territory_id": str, "armies_added": 2}]}`; suma `value` a `reinforcements_available`; aplica +2 en países propios de las tarjetas canjeadas (máx. 2 usos por tarjeta, `cards.bonus_uses`); manda las tarjetas a `discard`.
  - `award_card_if_due(player_id) -> Card | None` — si `conquered_this_turn` y hay mazo, saca tarjeta al jugador y resetea el flag.
  - `register_conquest(conqueror_id)` — marca `conquered_this_turn = True`.
  - `register_elimination(victim_id, killer_id) -> list[Card]` — anota `eliminated_by`, transfiere la mano de la víctima al asesino y la retorna.
  - `check_victory() -> tuple[str, Objective] | None` — muta objetivos `destroy` si corresponde y evalúa todos (jugador actual primero).
  - `next_phase` desde `reinforcement` exige `reinforcements_available == 0` y mano < 5.
  - Serialización de todos los campos nuevos con defaults retrocompatibles.

- [ ] **Step 1: Tests que fallan**

```python
"""Tarjetas y objetivos integrados al motor."""
import pytest

from teg_backend.domain.cards import Card
from teg_backend.domain.engine import EngineError, GameEngine


def _engine_in_turns():
    e = GameEngine(map_id="tactical-26")
    e.start(["p1", "p2"])
    for rnd in (5, 3):
        for pid in ("p1", "p2"):
            tid = next(t.territory_id for t in e.territories.values()
                       if t.owner_player_id == pid)
            e.place_initial(pid, tid, rnd)
    return e


def _hand(e, pid, symbols=("ship", "ship", "ship"), owned_first=False):
    tid = next(t.territory_id for t in e.territories.values()
               if t.owner_player_id == pid)
    cards = [
        Card(id=f"c{i}", territory_id=tid if (owned_first and i == 0) else "",
             symbol=s)
        for i, s in enumerate(symbols)
    ]
    e.cards.hands[pid] = cards
    return cards


def test_start_builds_deck():
    e = _engine_in_turns()
    # 25 territorios (tactical-26) + 2 comodines, menos 0 repartidas
    assert len(e.cards.deck) == len(e.map.territories) + 2


def test_trade_adds_reinforcements_and_escalates():
    e = _engine_in_turns()
    pid = e.turn.current_player_id
    base = e.turn.reinforcements_available
    cards = _hand(e, pid)
    result = e.trade_cards(pid, [c.id for c in cards])
    assert result["value"] == 4
    assert e.turn.reinforcements_available == base + 4
    assert e.cards.hands[pid] == []
    cards = _hand(e, pid)
    assert e.trade_cards(pid, [c.id for c in cards])["value"] == 7


def test_trade_own_country_bonus_max_twice():
    e = _engine_in_turns()
    pid = e.turn.current_player_id
    cards = _hand(e, pid, owned_first=True)
    tid = cards[0].territory_id
    before = e.territories[tid].armies
    result = e.trade_cards(pid, [c.id for c in cards])
    assert result["country_bonuses"] == [{"territory_id": tid, "armies_added": 2}]
    assert e.territories[tid].armies == before + 2


def test_trade_rejects_invalid_trio_and_wrong_phase():
    e = _engine_in_turns()
    pid = e.turn.current_player_id
    cards = _hand(e, pid, symbols=("ship", "ship", "cannon"))
    with pytest.raises(EngineError):
        e.trade_cards(pid, [c.id for c in cards])
    e.turn.reinforcements_available = 0
    e.cards.hands[pid] = []
    e.next_phase(pid)  # → attack
    cards = _hand(e, pid)
    with pytest.raises(EngineError):
        e.trade_cards(pid, [c.id for c in cards])


def test_next_phase_blocked_with_pending_reinforcements_or_five_cards():
    e = _engine_in_turns()
    pid = e.turn.current_player_id
    assert e.turn.reinforcements_available > 0
    with pytest.raises(EngineError):
        e.next_phase(pid)  # refuerzos sin colocar
    e.turn.reinforcements_available = 0
    _hand(e, pid, symbols=("ship",) * 5)
    with pytest.raises(EngineError):
        e.next_phase(pid)  # canje obligatorio con 5


def test_award_card_on_conquest_and_inherit_on_elimination():
    e = _engine_in_turns()
    pid = e.turn.current_player_id
    other = next(p for p in e.turn.order if p != pid)
    assert e.award_card_if_due(pid) is None
    e.register_conquest(pid)
    card = e.award_card_if_due(pid)
    assert card is not None and e.cards.hands[pid] == [card]
    assert e.award_card_if_due(pid) is None  # flag reseteado
    e.cards.hands[other] = [Card(id="x", territory_id="", symbol="ship")]
    inherited = e.register_elimination(other, pid)
    assert [c.id for c in inherited] == ["x"]
    assert e.eliminated_by == {other: pid}
    assert any(c.id == "x" for c in e.cards.hands[pid])


def test_check_victory_by_territories_objective():
    e = _engine_in_turns()
    pid = e.turn.current_player_id
    e.assign_objectives({"p1": "Daro", "p2": "Lord"})
    from teg_backend.domain.objectives import Objective
    e.objectives[pid] = Objective(id="o", family="territories",
                                  params={"count": 1}, title="t", description="d")
    winner = e.check_victory()
    assert winner is not None and winner[0] == pid
```

- [ ] **Step 2: Correr y ver el fallo**

Run: `cd backend && python -m pytest tests/test_engine_cards_objectives.py -q` → FAIL.

- [ ] **Step 3: Implementar en `engine.py`**

Imports arriba (junto al de map):

```python
from teg_backend.domain.cards import Card, CardsState, build_deck, is_valid_trio, trade_value
from teg_backend.domain.objectives import (
    Objective, generate_objectives, is_fulfilled, mutate_if_needed,
)
```

`__init__`: agregar campos (todos con default):

```python
        self.cards = CardsState()
        self.objectives: dict[str, Objective] = {}
        self.eliminated_by: dict[str, str] = {}
        self.conquered_this_turn = False
```

En `start()`, después de repartir territorios:

```python
        self.cards = CardsState(deck=build_deck(list(self.map.territories.keys())),
                                hands={pid: [] for pid in order})
        self.objectives = {}
        self.eliminated_by = {}
        self.conquered_this_turn = False
```

Métodos nuevos:

```python
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
```

En `next_phase`, reemplazar la rama `reinforcement`:

```python
        if self.turn.phase == "reinforcement":
            if self.turn.reinforcements_available > 0:
                raise EngineError("colocá todos tus refuerzos antes de atacar")
            if len(self.cards.hands.get(player_id, [])) >= 5:
                raise EngineError("tenés 5 tarjetas: el canje es obligatorio")
            self.turn.phase = "attack"
```

`to_dict` agrega:

```python
            "cards": self.cards.to_dict(),
            "objectives": {pid: o.to_dict() for pid, o in self.objectives.items()},
            "eliminated_by": dict(self.eliminated_by),
            "conquered_this_turn": self.conquered_this_turn,
```

`from_dict`: después de construir la instancia base (`engine = cls(...)`), setear:

```python
        engine.cards = CardsState.from_dict(data.get("cards", {}))
        engine.objectives = {
            pid: Objective.from_dict(o) for pid, o in data.get("objectives", {}).items()
        }
        engine.eliminated_by = dict(data.get("eliminated_by", {}))
        engine.conquered_this_turn = bool(data.get("conquered_this_turn", False))
        return engine
```

(refactorizar el `return cls(...)` actual a `engine = cls(...)` + `return engine`).

Además, en este task agregar `legal_actions` (lo consumen UI y bot):

```python
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
```

- [ ] **Step 4: Test extra de `legal_actions`** (agregar al mismo archivo de test)

```python
def test_legal_actions_by_phase():
    e = _engine_in_turns()
    pid = e.turn.current_player_id
    other = next(p for p in e.turn.order if p != pid)
    acts = {a["action"] for a in e.legal_actions(pid)}
    assert "turn.place_reinforcement" in acts and "turn.next_phase" not in acts
    assert e.legal_actions(other) == []
    e.turn.reinforcements_available = 0
    assert {a["action"] for a in e.legal_actions(pid)} == {"turn.next_phase"}
    e.next_phase(pid)
    acts = {a["action"] for a in e.legal_actions(pid)}
    assert "turn.end" in acts and "turn.next_phase" in acts
```

- [ ] **Step 5: Verificar y commitear**

Run: `cd backend && python -m pytest tests/test_engine_cards_objectives.py tests/test_cards.py tests/test_objectives.py tests/test_engine_placement.py -q` → PASS.

```bash
git add backend/src/teg_backend/domain/engine.py backend/tests/test_engine_cards_objectives.py
git commit -m "feat(engine): tarjetas, objetivos, victoria y acciones legales en el motor"
```

---

### Task 7: Servicio + WS — colocación, canje, victoria, snapshots por turno

**Files:**
- Modify: `backend/src/teg_backend/domain/enums.py`
- Modify: `backend/src/teg_backend/application/game_service.py`
- Modify: `backend/src/teg_backend/realtime/ws.py`
- Test: `backend/tests/test_canonical_flow.py` (nuevo) + arreglar `test_game_flow.py` / `test_gameplay_rules.py`

**Interfaces:**
- Consumes: todo lo del motor (Tasks 5–6), `repo.save_turn_snapshot` (Task 2).
- Produces:
  - `EventType` nuevos: `PLACEMENT_STARTED="placement.started"`, `PLACEMENT_UPDATED="placement.updated"` (privado), `PLACEMENT_PROGRESS="placement.progress"` (público), `PLACEMENT_REVEALED="placement.revealed"`, `CARDS_HAND="cards.hand"` (privado), `CARDS_TRADED="cards.traded"`, `CARD_AWARDED="card.awarded"` (público, sin detalle), `OBJECTIVE_ASSIGNED="objective.assigned"` (privado), `LEGAL_ACTIONS="legal.actions"` (privado, efímero).
  - `GameService.place_initial(game_id, player_id, territory_id, count) -> dict`
  - `GameService.trade_cards(game_id, player_id, card_ids) -> dict`
  - Mensajes WS nuevos: `placement.place {territory_id, count}`, `cards.trade {card_ids}`.
  - `snapshot()` agrega: `stage`, `placement` (privado del jugador), `your_cards`, `your_objective`.
  - `_start_turn` guarda snapshot de turno y emite `legal.actions` privado al jugador de turno.
  - `finish_game(..., winning_objective: dict | None)` incluye `objective` en el payload.

- [ ] **Step 1: Test de integración que falla**

`backend/tests/test_canonical_flow.py` (usa los helpers de `conftest.py`):

```python
"""Flujo canónico completo por WS: colocación 5+3, refuerzos, canje bloqueado."""
from conftest import ADMIN, confirm_join, create_game, invite, recv_until


def _setup_two_players(client):
    game = create_game(client, config={"commentator_enabled": False})
    inv1 = invite(client, game["id"], "Daro")
    inv2 = invite(client, game["id"], "Lord")
    confirm_join(client, game["code"], inv1["token"])
    confirm_join(client, game["code"], inv2["token"])
    return game, inv1, inv2


def _drain_ready_and_start(client, game, ws1, ws2):
    ws1.send_json({"type": "ready.set", "payload": {"ready": True}})
    recv_until(ws1, "player.ready"); recv_until(ws2, "player.ready")
    ws2.send_json({"type": "ready.set", "payload": {"ready": True}})
    recv_until(ws1, "player.ready"); recv_until(ws2, "player.ready")
    resp = client.post(f"/api/admin/games/{game['id']}/start", headers=ADMIN)
    assert resp.status_code == 200, resp.text


def _own_territory(started_payload, player_id):
    return next(tid for tid, t in started_payload["territories"].items()
                if t["owner_player_id"] == player_id)


def test_full_placement_then_first_turn(client):
    game, inv1, inv2 = _setup_two_players(client)
    with client.websocket_connect(f"/ws/{game['code']}?token={inv1['token']}") as ws1, \
         client.websocket_connect(f"/ws/{game['code']}?token={inv2['token']}") as ws2:
        recv_until(ws1, "game.snapshot"); recv_until(ws2, "game.snapshot")
        _drain_ready_and_start(client, game, ws1, ws2)
        started = recv_until(ws1, "game.started")["payload"]
        recv_until(ws2, "game.started")
        assert started["stage"] == "placement_1"
        recv_until(ws1, "objective.assigned")
        recv_until(ws2, "objective.assigned")
        recv_until(ws1, "placement.started"); recv_until(ws2, "placement.started")

        p1_id = started["turn_order"][0] if started["territories"][
            _own_territory(started, started["turn_order"][0])
        ] else started["turn_order"][0]
        p1_id, p2_id = started["turn_order"][0], started["turn_order"][1]
        # cada socket coloca en SU territorio: identificar cuál es de quién
        # por el token: ws1 es inv1; buscamos el player_id vía el snapshot "you"
        # (más simple: colocar por cada ws sobre el primer territorio propio
        #  que informe placement.updated como válido)
        # ws1 → jugador de inv1: probamos con ambos ids y usamos el que no da error
        for ws, ids in ((ws1, (p1_id, p2_id)), (ws2, (p2_id, p1_id))):
            placed = False
            for pid in ids:
                tid = _own_territory(started, pid)
                ws.send_json({"type": "placement.place",
                              "payload": {"territory_id": tid, "count": 5}})
                msg = ws.receive_json()
                if msg.get("event_type") == "placement.updated":
                    assert msg["payload"]["remaining"] == 0
                    placed = True
                    break
                assert msg.get("event_type") in ("error", "placement.progress")
            assert placed

        reveal = recv_until(ws1, "placement.revealed")
        assert reveal["payload"]["next_stage"] == "placement_2"
        recv_until(ws2, "placement.revealed")

        # ronda 2: 3 ejércitos cada uno (mismo esquema)
        territories = reveal["payload"]["territories"]
        for ws in (ws1, ws2):
            for pid in (p1_id, p2_id):
                tid = next(t for t, d in territories.items()
                           if d["owner_player_id"] == pid)
                ws.send_json({"type": "placement.place",
                              "payload": {"territory_id": tid, "count": 3}})
                msg = ws.receive_json()
                if msg.get("event_type") == "placement.updated":
                    break

        reveal2 = recv_until(ws1, "placement.revealed")
        assert reveal2["payload"]["next_stage"] == "turns"
        turn_ev = recv_until(ws1, "turn.started")
        assert turn_ev["payload"]["reinforcements_available"] >= 3
        legal = recv_until(ws1 if turn_ev["actor_id"] == p1_id else ws2, "legal.actions")
        acts = {a["action"] for a in legal["payload"]["actions"]}
        assert "turn.place_reinforcement" in acts


def test_trade_rejected_without_cards(client):
    game, inv1, inv2 = _setup_two_players(client)
    with client.websocket_connect(f"/ws/{game['code']}?token={inv1['token']}") as ws1, \
         client.websocket_connect(f"/ws/{game['code']}?token={inv2['token']}") as ws2:
        recv_until(ws1, "game.snapshot"); recv_until(ws2, "game.snapshot")
        _drain_ready_and_start(client, game, ws1, ws2)
        ws1.send_json({"type": "cards.trade", "payload": {"card_ids": ["a", "b", "c"]}})
        err = recv_until(ws1, "error")
        assert err["payload"]["code"] in ("INVALID_ACTION", "NOT_YOUR_TURN")
```

Nota para el implementador: si el emparejamiento ws↔player_id del primer test resulta frágil, simplificarlo consultando `you` del `game.snapshot` de cada socket (el snapshot lo trae) y usar ese id directamente — es la fuente limpia. Mantener la aserción de `remaining == 0` y de los dos `placement.revealed`.

- [ ] **Step 2: Correr y ver el fallo**

Run: `cd backend && python -m pytest tests/test_canonical_flow.py -q` → FAIL (`placement.place` desconocido).

- [ ] **Step 3: Agregar los `EventType` en `enums.py`**

```python
    PLACEMENT_STARTED = "placement.started"
    PLACEMENT_UPDATED = "placement.updated"    # privado: tu pool y pendientes
    PLACEMENT_PROGRESS = "placement.progress"  # público: quién terminó
    PLACEMENT_REVEALED = "placement.revealed"

    CARDS_HAND = "cards.hand"        # privado: tu mano completa
    CARDS_TRADED = "cards.traded"    # público: canje realizado
    CARD_AWARDED = "card.awarded"    # público: fulano recibió una tarjeta

    OBJECTIVE_ASSIGNED = "objective.assigned"  # privado
    LEGAL_ACTIONS = "legal.actions"            # privado y efímero
```

- [ ] **Step 4: Cablear `game_service.py`**

1. En `start_game`, tras `engine.start(...)` y antes de emitir `GAME_STARTED`: asignar objetivos y armar payload con `stage`:

```python
            nicknames = {p["id"]: p["nickname"] for p in seated}
            objectives = engine.assign_objectives(nicknames)
```

En el payload de `GAME_STARTED` agregar `"stage": engine.stage`. Después de emitirlo, reemplazar `await self._start_turn(...)` por:

```python
            for pid, obj in objectives.items():
                await self.emit(
                    game_id, EventType.OBJECTIVE_ASSIGNED, target_id=pid,
                    visibility=Visibility.PRIVATE,
                    payload={"objective": obj.public_view()},
                )
            await self.emit(
                game_id, EventType.PLACEMENT_STARTED,
                payload={"stage": engine.stage,
                         "pool_size": eng.PLACEMENT_ROUNDS[0],
                         "players": list(engine.turn.order)},
            )
            self._schedule_ai_placements(game_id)
```

(el turno arranca recién cuando la colocación revela `next_stage == "turns"`).

2. Métodos nuevos (junto a `place_reinforcement`):

```python
    async def place_initial(
        self, game_id: str, player_id: str, territory_id: str, count: int = 1
    ) -> dict:
        async with self.lock(game_id):
            game = await self.get_game_or_404(game_id)
            if game["status"] != GameStatus.RUNNING:
                raise ServiceError(ErrorCode.GAME_NOT_RUNNING, "la partida no está en curso")
            engine = await self._engine(game)
            try:
                result = engine.place_initial(player_id, territory_id, int(count))
            except EngineError as exc:
                raise ServiceError(ErrorCode.INVALID_ACTION, str(exc)) from exc
            await self._save_engine(game_id)
            await self.emit(
                game_id, EventType.PLACEMENT_UPDATED, target_id=player_id,
                visibility=Visibility.PRIVATE,
                payload={"remaining": result["remaining"],
                         "pending": engine.placement_pending.get(player_id, {})},
                persisted=False,
            )
            if result["remaining"] == 0:
                await self.emit(
                    game_id, EventType.PLACEMENT_PROGRESS, actor_id=player_id,
                    payload={"player_id": player_id, "done": True},
                )
            revealed = result["revealed"]
            if revealed:
                await self.emit(game_id, EventType.PLACEMENT_REVEALED, payload=revealed)
                if revealed["next_stage"] == "turns":
                    await self._save_engine(game_id)
                    await self._start_turn(
                        game_id, engine.turn.current_player_id, engine.turn.turn_number
                    )
                else:
                    self._schedule_ai_placements(game_id)
            return result

    async def trade_cards(self, game_id: str, player_id: str, card_ids: list[str]) -> dict:
        async with self.lock(game_id):
            engine = await self._require_running_turn(game_id, player_id)
            try:
                result = engine.trade_cards(player_id, [str(c) for c in card_ids])
            except EngineError as exc:
                raise ServiceError(ErrorCode.INVALID_ACTION, str(exc)) from exc
            await self._save_engine(game_id)
            await self.emit(
                game_id, EventType.CARDS_TRADED, actor_id=player_id,
                payload={"value": result["value"],
                         "cards": result["cards"],
                         "country_bonuses": result["country_bonuses"],
                         "turn": engine.turn.to_dict()},
            )
            await self._emit_hand(game_id, engine, player_id)
            return result

    async def _emit_hand(self, game_id: str, engine: GameEngine, player_id: str) -> None:
        await self.emit(
            game_id, EventType.CARDS_HAND, target_id=player_id,
            visibility=Visibility.PRIVATE,
            payload={"your_cards": [c.to_dict()
                                    for c in engine.cards.hands.get(player_id, [])]},
            persisted=False,
        )
```

3. En `attack()`, dentro del bloque de conquista (después de emitir `TERRITORY_CONQUERED`): agregar `engine.register_conquest(player_id)`. En el bloque de eliminación, después de `engine.remove_player(old_owner)`:

```python
                            inherited = engine.register_elimination(old_owner, player_id)
                            if inherited:
                                await self._emit_hand(game_id, engine, player_id)
```

Después del bloque de dominación total (`if len(player_terrs) == ...`), agregar el chequeo de objetivos (solo si la partida sigue):

```python
                    else:
                        winner = engine.check_victory()
                        if winner:
                            win_pid, win_obj = winner
                            await self._save_engine(game_id)
                            await self.finish_game(
                                game_id, winner_player_id=win_pid,
                                winning_objective=win_obj.public_view(),
                            )
                            return payload
```

4. `finish_game`: nueva firma `async def finish_game(self, game_id, winner_player_id=None, winning_objective=None)` y en `summary` agregar `"objective": winning_objective`. Quitar el `TODO(teg-rules)` de detección de ganador.

5. En `end_turn` y en `next_phase` (rama que rota turno): antes de `engine.advance_turn()` / `engine.next_phase(...)` que rote, otorgar tarjeta:

```python
            card = engine.award_card_if_due(player_id)
            if card is not None:
                await self.emit(game_id, EventType.CARD_AWARDED, actor_id=player_id,
                                payload={"player_id": player_id})
                await self._emit_hand(game_id, engine, player_id)
```

En `end_turn` va justo después de obtener `engine` y antes de `TURN_ENDED`. En `next_phase` solo cuando `engine.turn.phase == "fortify"` antes de llamar (es la rama que rota).

6. `_start_turn`: después de calcular `phase`/`reinf`, guardar snapshot y emitir acciones legales:

```python
        if engine is not None:
            await repo.save_turn_snapshot(self.db, game_id, engine.turn.turn_number,
                                          engine.to_dict())
```

y al final (tras el emit de `TURN_STARTED`, antes del scheduling IA):

```python
        if engine is not None and player_id:
            await self.emit(
                game_id, EventType.LEGAL_ACTIONS, target_id=player_id,
                visibility=Visibility.PRIVATE,
                payload={"actions": engine.legal_actions(player_id)},
                persisted=False,
            )
```

7. `snapshot()`: agregar al dict retornado:

```python
            "stage": engine.stage,
            "placement": (
                {"remaining": engine.placement_pools.get(for_player_id, 0),
                 "pending": engine.placement_pending.get(for_player_id, {}),
                 "players_done": [pid for pid, n in engine.placement_pools.items() if n == 0]}
                if engine.stage in ("placement_1", "placement_2") else None
            ),
            "your_cards": [c.to_dict() for c in engine.cards.hands.get(for_player_id, [])],
            "your_objective": (
                engine.objectives[for_player_id].public_view()
                if for_player_id in engine.objectives else None
            ),
```

y en la clave `"turn"` cambiar la condición a `... and engine.stage == "turns"` (durante colocación no hay turno activo que mostrar).

- [ ] **Step 5: Cablear `ws.py`**

En `_dispatch`, agregar casos:

```python
        case "placement.place":
            await service.place_initial(
                game["id"], player["id"],
                str(payload.get("territory_id", "")),
                int(payload.get("count", 1)),
            )
        case "cards.trade":
            ids = payload.get("card_ids")
            if not isinstance(ids, list):
                raise ServiceError(ErrorCode.INVALID_PAYLOAD, "card_ids debe ser lista")
            await service.trade_cards(game["id"], player["id"], [str(c) for c in ids])
```

y actualizar el docstring del módulo con los tipos nuevos.

- [ ] **Step 6: IA mínima que no bloquea (colocación + refuerzos + canje forzado)**

En `game_service.py` agregar:

```python
    def _schedule_ai_placements(self, game_id: str) -> None:
        asyncio.create_task(self._ai_placements(game_id))

    async def _ai_placements(self, game_id: str) -> None:
        """Los bots colocan su pool inicial apenas arranca cada ronda."""
        try:
            await asyncio.sleep(self.settings.ai_player_think_seconds)
            game = await repo.get_game(self.db, game_id)
            if game is None or game["status"] != GameStatus.RUNNING:
                return
            players = await repo.get_players(self.db, game_id)
            ai_ids = {p["id"] for p in players if p["role"] == Role.AI_PLAYER}
            engine = await self._engine(game)
            for pid in list(engine.placement_pools):
                if pid not in ai_ids:
                    continue
                while engine.placement_pools.get(pid, 0) > 0:
                    own = [t.territory_id for t in engine.territories.values()
                           if t.owner_player_id == pid]
                    tid = eng._rng.choice(own)
                    await self.place_initial(game_id, pid, tid, 1)
        except ServiceError as exc:
            log.info("colocación IA rechazada", extra={"ctx": {"code": exc.code}})
        except Exception:
            log.warning("fallo en colocación IA", exc_info=True)
```

y en `_ai_turn`, antes del bloque `legal = [...]`, agregar juego mínimo legal:

```python
            # refuerzos y canje forzado: la IA nunca deja el turno trabado
            hand = engine.cards.hands.get(player_id, [])
            if len(hand) >= 5:
                for a in engine.legal_actions(player_id):
                    if a["action"] == "cards.trade":
                        trio = _first_valid_trio(hand)
                        if trio:
                            await self.trade_cards(game_id, player_id, trio)
                        break
            engine = await self._engine(game)
            while engine.turn.reinforcements_available > 0 and \
                    engine.turn.current_player_id == player_id:
                own = [t.territory_id for t in engine.territories.values()
                       if t.owner_player_id == player_id]
                await self.place_reinforcement(
                    game_id, player_id, eng._rng.choice(own),
                    engine.turn.reinforcements_available,
                )
```

con el helper módulo-nivel (en `game_service.py`, junto a los imports):

```python
def _first_valid_trio(hand: list) -> list[str] | None:
    from itertools import combinations
    from ..domain.cards import is_valid_trio
    for combo in combinations(hand, 3):
        if is_valid_trio(list(combo)):
            return [c.id for c in combo]
    return None
```

- [ ] **Step 7: Arreglar los tests de flujo viejos**

`test_game_flow.py` y `test_gameplay_rules.py` asumen que tras `start` viene `turn.started`. Insertar en cada uno, tras `game.started`, la colocación completa: helper compartido en `conftest.py`:

```python
def complete_placement(ws_by_player: dict[str, object], started_payload: dict) -> dict:
    """Coloca 5+3 por jugador y retorna el payload del último placement.revealed."""
    territories = started_payload["territories"]
    reveal = None
    for round_pool in (5, 3):
        for pid, ws in ws_by_player.items():
            tid = next(t for t, d in territories.items() if d["owner_player_id"] == pid)
            ws.send_json({"type": "placement.place",
                          "payload": {"territory_id": tid, "count": round_pool}})
        for ws in ws_by_player.values():
            reveal = recv_until(ws, "placement.revealed")
        territories = reveal["payload"]["territories"]
    return reveal["payload"]
```

Adaptar los tests viejos para: (a) construir `ws_by_player` con los ids ya conocidos, (b) llamar `complete_placement`, (c) recién entonces esperar `turn.started`. Quitar los `xfail` si se pusieron en Task 5. En `test_gameplay_rules.py`, el paso a fase attack ahora exige refuerzos en 0: colocar **todos** los refuerzos disponibles (leer `reinforcements_available` del `turn.started`) antes de `turn.next_phase`.

- [ ] **Step 8: Verificar todo y commitear**

Run: `cd backend && python -m pytest -q` → TODO verde (nuevos y viejos).

```bash
git add backend/src/teg_backend backend/tests
git commit -m "feat(backend): flujo canónico completo — colocación, canje, victoria por objetivo y snapshots por turno"
```

---

### Task 8: Contratos TS (`shared/contracts`)

**Files:**
- Modify: `shared/contracts/src/game.ts`
- Modify: `shared/contracts/src/ws-events.ts`
- Test: `frontend/src/tests/contracts.test.ts` (agregar casos)

**Interfaces:**
- Produces (exports de `@teg/contracts`):
  - `SnapshotPayload` extendido: `stage`, `placement`, `your_cards`, `your_objective`.
  - Payloads zod nuevos: `PlacementStartedPayload`, `PlacementUpdatedPayload`, `PlacementProgressPayload`, `PlacementRevealedPayload`, `CardsHandPayload`, `CardsTradedPayload`, `CardAwardedPayload`, `ObjectiveAssignedPayload`, `LegalActionsPayload`.
  - `ClientMessage` con `placement.place`.
  - `GameFinishedPayload` con `objective` opcional.

- [ ] **Step 1: Test que falla** (agregar a `contracts.test.ts`)

```typescript
import {
  SnapshotPayload, PlacementRevealedPayload, CardsHandPayload,
  ObjectiveAssignedPayload, LegalActionsPayload, ClientMessage,
} from '@teg/contracts';

it('valida el snapshot con stage, colocación, mano y objetivo', () => {
  const snap = SnapshotPayload.parse({
    game: { id: 'g', code: 'ABC123', name: 'n', status: 'running' },
    you: 'p1',
    players: [],
    turn: null,
    recent_events: [],
    stage: 'placement_1',
    placement: { remaining: 5, pending: { t1: 2 }, players_done: [] },
    your_cards: [{ id: 'c1', territory_id: 't1', symbol: 'ship' }],
    your_objective: { id: 'o1', title: 'T', description: 'D' },
  });
  expect(snap.stage).toBe('placement_1');
});

it('valida placement.place como mensaje de cliente', () => {
  const msg = ClientMessage.parse({
    type: 'placement.place',
    payload: { territory_id: 't1', count: 3 },
  });
  expect(msg.type).toBe('placement.place');
});

it('valida payloads nuevos del servidor', () => {
  PlacementRevealedPayload.parse({
    stage_completed: 'placement_1', next_stage: 'placement_2',
    territories: { t1: { id: 't1', territory_id: 't1', owner_player_id: 'p1', armies: 6 } },
  });
  CardsHandPayload.parse({ your_cards: [] });
  ObjectiveAssignedPayload.parse({ objective: { id: 'o', title: 't', description: 'd' } });
  LegalActionsPayload.parse({ actions: [{ action: 'attack', params: { sources: [] } }] });
});
```

Ajustar el shape de `game`/`GameRef` del primer parse a lo que el contrato existente exija (mirar los tests actuales de `contracts.test.ts` y copiar un `game` válido de ahí).

- [ ] **Step 2: Correr y ver el fallo**

Run: `cd frontend && pnpm vitest run src/tests/contracts.test.ts` → FAIL.

- [ ] **Step 3: Implementar en `game.ts`**

Agregar antes de `SnapshotPayload`:

```typescript
export const GameStage = z.enum(['placement_1', 'placement_2', 'turns']);
export type GameStage = z.infer<typeof GameStage>;

export const PlacementView = z.object({
  remaining: z.number().int(),
  pending: z.record(z.string(), z.number().int()),
  players_done: z.array(z.string()),
});
export type PlacementView = z.infer<typeof PlacementView>;
```

y dentro de `SnapshotPayload` (campos opcionales para compatibilidad):

```typescript
  stage: GameStage.optional(),
  placement: PlacementView.nullable().optional(),
  your_cards: z.array(CountryCard).optional(),
  your_objective: SecretObjective.nullable().optional(),
```

- [ ] **Step 4: Implementar en `ws-events.ts`**

Payloads del servidor (junto a los existentes):

```typescript
export const PlacementStartedPayload = z.object({
  stage: z.string(),
  pool_size: z.number().int(),
  players: z.array(z.string()),
});
export const PlacementUpdatedPayload = z.object({
  remaining: z.number().int(),
  pending: z.record(z.string(), z.number().int()),
});
export const PlacementProgressPayload = z.object({
  player_id: z.string(),
  done: z.boolean(),
});
export const PlacementRevealedPayload = z.object({
  stage_completed: z.string(),
  next_stage: z.string(),
  territories: z.record(z.string(), TerritoryState),
});
export const CardsHandPayload = z.object({ your_cards: z.array(CountryCard) });
export const CardsTradedPayload = z.object({
  value: z.number().int(),
  cards: z.array(CountryCard),
  country_bonuses: z.array(z.object({
    territory_id: z.string(),
    armies_added: z.number().int(),
  })),
  turn: TurnState.optional(),
});
export const CardAwardedPayload = z.object({ player_id: z.string() });
export const ObjectiveAssignedPayload = z.object({ objective: SecretObjective });
export const LegalActionsPayload = z.object({
  actions: z.array(z.object({ action: z.string(), params: z.record(z.string(), z.any()) })),
});
```

(importar `TerritoryState`, `CountryCard`, `SecretObjective`, `TurnState` desde `./game` si no están ya importados; exportar los tipos con `z.infer` siguiendo el patrón del archivo).

En `ClientMessage`, agregar al union:

```typescript
  z.object({
    type: z.literal('placement.place'),
    payload: z.object({
      territory_id: z.string(),
      count: z.number().int().min(1).max(5),
    }),
  }),
```

En `GameFinishedPayload` agregar:

```typescript
  objective: SecretObjective.nullable().optional(),
```

- [ ] **Step 5: Verificar y commitear**

Run: `cd frontend && pnpm vitest run` → PASS (todos).

```bash
git add shared/contracts/src frontend/src/tests/contracts.test.ts
git commit -m "feat(contracts): stage, colocación, tarjetas, objetivos y acciones legales"
```

---

### Task 9: Frontend — store y bindStores para el flujo canónico

**Files:**
- Modify: `frontend/src/state/gameStore.ts`
- Modify: `frontend/src/services/websocket/bindStores.ts`
- Test: `frontend/src/tests/gameStoreCanonical.test.ts`

**Interfaces:**
- Consumes: contratos de Task 8.
- Produces (en `useGameStore`): `stage: GameStage | null`, `placementRemaining: number`, `placementPending: Record<string, number>`, `placementDone: string[]`, `legalActions: { action: string; params: Record<string, unknown> }[]`, `finishedObjective: SecretObjective | null`; setters `setStage`, `setPlacement`, `setPlacementDone`, `setLegalActions`, `setFinishedObjective`. `setFinished(winner, turns)` se mantiene.

- [ ] **Step 1: Test que falla**

```typescript
import { describe, expect, it } from 'vitest';
import { useGameStore } from '../state/gameStore';

describe('estado canónico', () => {
  it('maneja stage y colocación', () => {
    const s = useGameStore.getState();
    s.setStage('placement_1');
    s.setPlacement(5, { t1: 2 });
    s.setPlacementDone(['p2']);
    const after = useGameStore.getState();
    expect(after.stage).toBe('placement_1');
    expect(after.placementRemaining).toBe(5);
    expect(after.placementPending).toEqual({ t1: 2 });
    expect(after.placementDone).toEqual(['p2']);
  });

  it('guarda acciones legales y objetivo del ganador', () => {
    const s = useGameStore.getState();
    s.setLegalActions([{ action: 'attack', params: {} }]);
    s.setFinishedObjective({ id: 'o', title: 'T', description: 'D' });
    const after = useGameStore.getState();
    expect(after.legalActions[0].action).toBe('attack');
    expect(after.finishedObjective?.title).toBe('T');
  });
});
```

- [ ] **Step 2: Correr y ver el fallo**

Run: `cd frontend && pnpm vitest run src/tests/gameStoreCanonical.test.ts` → FAIL.

- [ ] **Step 3: Implementar el store**

En `gameStore.ts` — al tipo del estado agregar (junto a `cards`/`secretObjective`):

```typescript
  stage: GameStage | null;
  placementRemaining: number;
  placementPending: Record<string, number>;
  placementDone: string[];
  legalActions: { action: string; params: Record<string, unknown> }[];
  finishedObjective: SecretObjective | null;
```

acciones:

```typescript
  setStage: (stage: GameStage | null) => void;
  setPlacement: (remaining: number, pending: Record<string, number>) => void;
  setPlacementDone: (players: string[]) => void;
  setLegalActions: (actions: { action: string; params: Record<string, unknown> }[]) => void;
  setFinishedObjective: (objective: SecretObjective | null) => void;
```

defaults iniciales: `stage: null, placementRemaining: 0, placementPending: {}, placementDone: [], legalActions: [], finishedObjective: null`; implementación:

```typescript
  setStage: (stage) => set({ stage }),
  setPlacement: (placementRemaining, placementPending) =>
    set({ placementRemaining, placementPending }),
  setPlacementDone: (placementDone) => set({ placementDone }),
  setLegalActions: (legalActions) => set({ legalActions }),
  setFinishedObjective: (finishedObjective) => set({ finishedObjective }),
```

importando `GameStage` de `@teg/contracts`. Si el store tiene un `reset()`, incluir los campos nuevos ahí.

- [ ] **Step 4: Cablear `bindStores.ts`**

En el handler de `game.snapshot`, tras `applySnapshot`:

```typescript
    game().setStage(snap.stage ?? (snap.turn ? 'turns' : null));
    if (snap.placement) game().setPlacement(snap.placement.remaining, snap.placement.pending);
    game().setPlacementDone(snap.placement?.players_done ?? []);
    game().setCards(snap.your_cards ?? []);
    game().setSecretObjective(snap.your_objective ?? null);
```

En `game.started`: el payload ahora trae `stage`; reemplazar el `setTurn` incondicional por:

```typescript
    const stage = (payload as { stage?: 'placement_1' | 'placement_2' | 'turns' }).stage;
    game().setStage(stage ?? 'turns');
    if (!stage || stage === 'turns') {
      game().setTurn({ /* ...el objeto actual sin cambios... */ });
    }
```

Handlers nuevos (después de `territory.updated`):

```typescript
  wsClient.on('placement.started', (p) => {
    const payload = p as z.infer<typeof PlacementStartedPayload>;
    game().setStage(payload.stage as 'placement_1' | 'placement_2');
    game().setPlacement(payload.pool_size, {});
    game().setPlacementDone([]);
  });

  wsClient.on('placement.updated', (p) => {
    const payload = p as z.infer<typeof PlacementUpdatedPayload>;
    game().setPlacement(payload.remaining, payload.pending);
  });

  wsClient.on('placement.progress', (p) => {
    const payload = p as z.infer<typeof PlacementProgressPayload>;
    if (payload.done) {
      game().setPlacementDone([...game().placementDone, payload.player_id]);
    }
  });

  wsClient.on('placement.revealed', (p) => {
    const payload = p as z.infer<typeof PlacementRevealedPayload>;
    game().setTerritories(payload.territories);
    game().setStage(payload.next_stage as 'placement_1' | 'placement_2' | 'turns');
    game().setPlacementDone([]);
    if (payload.next_stage !== 'turns') game().setPlacement(3, {});
  });

  wsClient.on('cards.hand', (p) => {
    game().setCards((p as z.infer<typeof CardsHandPayload>).your_cards);
  });

  wsClient.on('cards.traded', (p) => {
    const payload = p as z.infer<typeof CardsTradedPayload>;
    if (payload.turn) game().setTurn(payload.turn);
  });

  wsClient.on('objective.assigned', (p) => {
    game().setSecretObjective((p as z.infer<typeof ObjectiveAssignedPayload>).objective);
  });

  wsClient.on('legal.actions', (p) => {
    game().setLegalActions((p as z.infer<typeof LegalActionsPayload>).actions);
  });
```

y en `game.finished`:

```typescript
    game().setFinishedObjective(payload.objective ?? null);
```

(agregar los imports de los payloads nuevos desde `@teg/contracts`).

- [ ] **Step 5: Verificar y commitear**

Run: `cd frontend && pnpm vitest run` → PASS. `pnpm --filter @teg/frontend build` → compila sin errores TS.

```bash
git add frontend/src/state/gameStore.ts frontend/src/services/websocket/bindStores.ts frontend/src/tests/gameStoreCanonical.test.ts
git commit -m "feat(frontend): store y bindings del flujo canónico (colocación, mano, objetivo, acciones legales)"
```

---

### Task 10: Frontend — UI de colocación, modales reales y fin de partida sin fakes

**Files:**
- Modify: `frontend/src/components/map/MapPanel.tsx`
- Modify: `frontend/src/pages/GamePage.tsx`
- Modify: `frontend/src/components/cards/CountryCardsModal.tsx`
- Modify: `frontend/src/components/SecretObjectiveModal.tsx` (ruta real: buscarla con `grep -r "SecretObjectiveModal" frontend/src --include="*.tsx" -l`)
- Modify: `frontend/src/components/PostGameModal.tsx` (ídem búsqueda)

**Interfaces:**
- Consumes: store de Task 9, `wsClient.send` con `placement.place` (contrato Task 8).
- Produces: juego jugable de punta a punta en navegador con las reglas nuevas.

- [ ] **Step 1: MapPanel — click coloca durante la colocación + marca de territorios propios**

En `MapPanel.tsx`, leer del store `const stage = useGameStore((s) => s.stage);` y `const placementRemaining = useGameStore((s) => s.placementRemaining);`. En el `useEffect` táctico (deps: agregar `stage` y `placementRemaining`):

1. Al pintar cada territorio agregar `path.dataset.mine = String(tState?.owner_player_id === youId);` (lo usa el e2e y ayuda a estilos).
2. En `path.onclick`, **antes** del bloque de `currentPhase`, insertar:

```typescript
        if (stage === 'placement_1' || stage === 'placement_2') {
          if (tState && tState.owner_player_id === youId && placementRemaining > 0) {
            wsClient.send({
              type: 'placement.place',
              payload: { territory_id: id, count: 1 },
            });
          }
          return;
        }
```

3. En las insignias de ejércitos: durante la colocación, sumar los pendientes propios al número mostrado (`armies + (placementPending[id] ?? 0)` — leer `placementPending` del store) para que el jugador vea su colocación oculta en su propia pantalla.

- [ ] **Step 2: GamePage — banner de colocación y progreso**

En `GamePage.tsx`, leer `stage`, `placementRemaining`, `placementDone`, `players` del store. Donde se muestra la barra de fases, si `stage === 'placement_1' || stage === 'placement_2'` renderizar en su lugar:

```tsx
<div className="rounded-lg border border-amber-700 bg-amber-950/60 px-4 py-2 text-center">
  <p className="font-bold text-amber-300">
    {stage === 'placement_1' ? 'Colocación inicial: 5 ejércitos' : 'Segunda ronda: 3 ejércitos'}
  </p>
  <p className="text-sm text-stone-300">
    {placementRemaining > 0
      ? `Te quedan ${placementRemaining} por colocar — tocá tus países`
      : 'Listo. Esperando al resto…'}
  </p>
  <p className="text-xs text-stone-400">
    {placementDone.length}/{combatants.length} jugadores terminaron
  </p>
</div>
```

(usar la variable `combatants` que la página ya define; ocultar el panel de acciones de ataque mientras `stage !== 'turns'`).

- [ ] **Step 3: CountryCardsModal — mano real**

El modal ya envía `cards.trade` y ya lee `cards` del store (verificar con grep; si lee otra cosa, conectarlo a `useGameStore((s) => s.cards)`). Cambios:
1. Deshabilitar el botón de canje si la selección no es un trío válido, replicando la regla en TS:

```typescript
function isValidTrio(symbols: string[]): boolean {
  if (symbols.length !== 3) return false;
  const plain = symbols.filter((s) => s !== 'joker');
  return new Set(plain).size <= 1 || new Set(plain).size === plain.length;
}
```

2. Mostrar cuánto vale el próximo canje NO se puede calcular sin `trades_done`; en su lugar, tras un `cards.traded` propio el store actualiza la mano vía `cards.hand` — no mostrar valor especulativo, mostrar "Canjear trío" a secas.
3. Si la mano tiene ≥5 tarjetas, banner rojo: "Canje obligatorio: tenés 5 tarjetas".

- [ ] **Step 4: SecretObjectiveModal — objetivo real**

Eliminar el objetivo hardcodeado. Leer `const objective = useGameStore((s) => s.secretObjective);`. Si es `null`, mostrar "Tu objetivo se revela al iniciar la partida."; si no, `objective.title` + `objective.description`. Nada más.

- [ ] **Step 5: PostGameModal — sin trofeos falsos**

Eliminar los trofeos hardcodeados por índice (`combatants[1]` etc.). Mostrar: ganador (nickname + color), `finishedObjective` del store si existe ("Cumplió su objetivo secreto: …" con título y descripción; si es null, "Victoria por dominación total"), y turnos jugados. Los trofeos reales llegan en la Etapa 7 — no dejar ninguno inventado.

- [ ] **Step 6: Verificar build y vitest**

Run: `cd frontend && pnpm vitest run && pnpm --filter @teg/frontend build`
Expected: verde y build OK.

- [ ] **Step 7: Commit**

```bash
git add frontend/src
git commit -m "feat(frontend): colocación inicial jugable, tarjetas y objetivos reales, fin de partida sin fakes"
```

---

### Task 11: e2e Playwright actualizado al flujo canónico

**Files:**
- Modify: `e2e/vertical-slice.spec.ts`

**Interfaces:**
- Consumes: `path.territory[data-mine="true"]` (Task 10), flujo de colocación (Task 7).

- [ ] **Step 1: Actualizar el spec**

En el test principal, tras iniciar la partida (donde hoy espera el mapa/turno), insertar la colocación para ambas páginas:

```typescript
async function placeAll(page: Page, count: number) {
  for (let i = 0; i < count; i++) {
    await page.locator('path.territory[data-mine="true"]').first().click();
    await page.waitForTimeout(150); // el WS confirma con placement.updated
  }
}

// colocación inicial 5 + 3 en ambas pantallas
for (const pool of [5, 3]) {
  await placeAll(pageA, pool);
  await placeAll(pageB, pool);
}
await expect(pageA.getByText(/refuerzos|Colocá/i).first()).toBeVisible({ timeout: 10_000 });
```

Ajustar las aserciones siguientes del spec: donde asumía dados inmediatos, primero verificar que la fase de refuerzos del primer turno aparece (texto del banner de fases existente). El resto del flujo (dados sincronizados, link revocado) se mantiene.

- [ ] **Step 2: Correr el e2e**

Run: `pnpm exec playwright test`
Expected: PASS. Si falla por timing de `placement.revealed`, subir el `waitForTimeout` a 300ms o esperar el texto "Segunda ronda" entre pools.

- [ ] **Step 3: Commit**

```bash
git add e2e/vertical-slice.spec.ts
git commit -m "test(e2e): flujo canónico con colocación inicial en el slice vertical"
```

---

### Task 12: Verificación final de la etapa

- [ ] **Step 1: Suite completa**

Run: `cd backend && python -m pytest -q && cd ../frontend && pnpm vitest run && pnpm --filter @teg/frontend build && cd .. && pnpm exec playwright test`
Expected: todo verde.

- [ ] **Step 2: Partida manual de humo**

Run: `docker compose up -d --build backend frontend`
Con dos navegadores: crear partida (modo `classic_26`), invitar 2 jugadores + 1 bot, jugar colocación completa, verificar: objetivo secreto visible y real, refuerzos canónicos, conquista otorga tarjeta al cerrar turno, canje funciona, el bot coloca y no traba la partida. Anotar cualquier defecto como issue antes de cerrar la etapa.

- [ ] **Step 3: Commit final si hubo ajustes**

```bash
git add -A && git commit -m "fix: ajustes de la verificación manual de la etapa 1"
```

---

## Self-review del plan (hecho)

- **Cobertura vs spec Etapa 0+1:** Caddy/backup (T1), snapshots por turno (T2, escritos en T7), tarjetas canónicas con canje escalonado/bonus país/herencia/canje obligatorio (T3, T6, T7), objetivos con mutación y victoria automática (T4, T6, T7), colocación 5+3 simultánea oculta (T5, T7, T10), acciones legales para UI y bot (T6, T7, T9), IA no bloqueante en colocación/refuerzos/canje forzado (T7 — la IA "razonable" completa es Etapa 4), contratos y frontend jugable (T8–T10), e2e (T11). El test de "partida completa con 6 bots hasta victoria" queda para la Etapa 4: con el bot actual (no ataca) la partida no converge — decisión consciente, no un olvido.
- **Sin placeholders:** todos los pasos tienen código o comando concreto; las dos búsquedas con grep (rutas de modales) son acciones ejecutables, no TBDs.
- **Consistencia de tipos:** `place_initial → {"remaining", "revealed"}` usado igual en T5/T7; `legal_actions → [{"action", "params"}]` igual en T6/T7/T8/T9; `public_view() → {id,title,description}` = contrato `SecretObjective`; símbolos `ship/cannon/balloon/joker` = `CardSymbol` TS.
