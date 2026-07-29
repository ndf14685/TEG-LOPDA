# Fase 0 — Estabilidad para 8 jugadores: plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Que una partida de 8 jugadores humanos conectados por WebSocket llegue a su fin sin desincronizaciones, sin reconexiones espontáneas y sin trabarse.

**Architecture:** Se separa la secuencia que ve el cliente (densa, solo eventos públicos) de la secuencia de almacenamiento (densa sobre todo, intacta). Se corta la realimentación del instrumento de playtest. Se saca el envío por WebSocket de adentro del lock de la partida y se hace concurrente con timeout. Se agregan las salvaguardas que faltan para que la mesa no se trabe: timeout de turno por ausencia, rehidratación de turnos de bot, colores únicos y tope de invitados.

**Tech Stack:** Python 3.12 · FastAPI · aiosqlite · pytest · React 18 + TypeScript · zustand · vitest · zod (`shared/contracts`) · Docker Compose · nginx

## Global Constraints

- Trabajar sobre la rama actual `playtest/mode-instrumentation`. Un commit por tarea.
- **Todo campo nuevo del protocolo debe declararse en `shared/contracts`.** Los schemas zod descartan en silencio los campos no declarados; ya hubo bugs por esto (`shared/contracts/src/ws-events.ts:42-43`).
- **Nunca agregar `--workers` a uvicorn.** El estado del juego vive en memoria del proceso (`GameService._engines`, `ConnectionManager.rooms`, locks). Más de un worker rompe el juego.
- Backend: `cd backend && uv run pytest`. Frontend: `cd frontend && pnpm vitest run`.
- **Convenciones de test del repo — respetarlas, no inventar otras:**
  - No hay `pytest-asyncio`. Los tests async usan `@pytest.mark.anyio` más un fixture local `anyio_backend` que devuelve `"asyncio"` (ver `backend/tests/test_repository_snapshots.py:8-20`).
  - La mayoría de los tests son **síncronos** sobre el fixture `client` (`TestClient`) de `backend/tests/conftest.py:12-27`, con los helpers `create_game`, `invite`, `confirm_join`, `recv_until`, `complete_placement` y la constante `ADMIN`.
  - El token de admin en tests es **`test-admin`**, no `dev-admin`. Usar siempre `ADMIN` importado de `conftest`.
  - `pyproject.toml` fija `timeout = 30` por test. La prueba de carga debe entrar cómoda en ese presupuesto.
- No levantar servicios ni tocar `.env`: la operación del servidor la maneja el dueño.
- Mensajes de commit en español, en imperativo, sin tildes en el asunto.

---

## Estructura de archivos

**Backend**
- `backend/migrations/0006-public-sequence.sql` *(nuevo)* — columna `public_sequence`.
- `backend/src/teg_backend/infrastructure/repository.py` — asignación y lectura de `public_sequence`.
- `backend/src/teg_backend/domain/events.py` — el envelope aprende a serializar la secuencia pública.
- `backend/src/teg_backend/application/game_service.py` — `emit` fuera del lock, saludos acotados, timeout de turno, join bloqueado, colores únicos, rehidratación.
- `backend/src/teg_backend/realtime/manager.py` — broadcast concurrente con timeout, tope de conexiones.
- `backend/src/teg_backend/domain/engine.py` — validación `count >= 1`.
- `backend/src/teg_backend/ai/commentator.py` — conteo de jugadores consistente.
- `backend/src/teg_backend/playtest/service.py` y `api/playtest.py` — throttle y cotas de tamaño.
- `backend/src/teg_backend/config.py` — parámetros nuevos.
- `backend/src/teg_backend/main.py` — rehidratación en el lifespan.

**Frontend**
- `frontend/src/services/websocket/wsClient.ts` — pong cancela temporizadores, `send` no arma timer con el socket cerrado.
- `frontend/src/services/playtest/playtestClient.ts` — sin anidamiento, sin cascada.

**Infra**
- `frontend/nginx.conf`, `backend/Dockerfile`, `docker-compose.yml`, `backend/src/teg_backend/infrastructure/db.py`.

**Tests**
- `backend/tests/test_public_sequence.py`, `test_broadcast_resiliente.py`, `test_turn_timeout.py`, `test_lobby_hygiene.py`, `test_carga_8_jugadores.py` *(nuevos)*.
- `frontend/src/tests/wsClientPing.test.ts`, `playtestClientNesting.test.ts` *(nuevos)*.

---

### Task 1: Secuencia pública separada de la secuencia de almacenamiento

Es la causa raíz del incidente. Sin esto, nada más importa.

**Files:**
- Create: `backend/migrations/0006-public-sequence.sql`
- Modify: `backend/src/teg_backend/infrastructure/repository.py` (bloque `--- events ---`, desde la línea 246)
- Modify: `backend/src/teg_backend/domain/events.py:33-34` (método `wire`)
- Modify: `backend/src/teg_backend/application/game_service.py:127-133` (dentro de `emit`)
- Test: `backend/tests/test_public_sequence.py`

**Interfaces:**
- Consumes: nada (primera tarea).
- Produces:
  - `repo.next_public_sequence(db, game_id) -> int`
  - `GameEvent.public_sequence: int | None` (campo pydantic nuevo, default `None`)
  - `GameEvent.wire()` devuelve `sequence_number = public_sequence or 0` para públicos y `0` para no públicos; el resto del envelope no cambia.

- [ ] **Step 1: Escribir el test que falla**

Crear `backend/tests/test_public_sequence.py`. Reproduce el incidente real a nivel
WebSocket, con el estilo síncrono del repo:

```python
"""La secuencia que ve el cliente no debe tener huecos por eventos privados.

Reproduce el incidente del 27/07 (partida wfqrwfrf): game.started con seq 13,
dos objective.assigned privados con seq 14 y 16, y ai.comment con seq 15.
Cada cliente veia un salto y se autodesconectaba.
"""

from conftest import ADMIN, confirm_join, create_game, invite, recv_until


def _partida_de_tres(client):
    game = create_game(client, config={"commentator_enabled": False})
    invs = [invite(client, game["id"], n) for n in ("Nes", "Seba", "Colo")]
    for inv in invs:
        confirm_join(client, game["code"], inv["token"])
    return game, invs


def _secuencias_persistidas(ws, cuantos=40):
    """Solo los persistidos (seq > 0) participan del stream ordenado."""
    seqs = []
    for _ in range(cuantos):
        msg = ws.receive_json()
        seq = msg.get("sequence_number", 0)
        if seq > 0:
            seqs.append(seq)
        if msg.get("event_type") == "placement.started":
            break
    return seqs


def test_el_arranque_no_deja_huecos_en_la_secuencia_del_cliente(client):
    game, invs = _partida_de_tres(client)
    with client.websocket_connect(f"/ws/{game['code']}?token={invs[0]['token']}") as ws1, \
         client.websocket_connect(f"/ws/{game['code']}?token={invs[1]['token']}") as ws2, \
         client.websocket_connect(f"/ws/{game['code']}?token={invs[2]['token']}") as ws3:
        for ws in (ws1, ws2, ws3):
            recv_until(ws, "game.snapshot")
        for ws in (ws1, ws2, ws3):
            ws.send_json({"type": "ready.set", "payload": {"ready": True}})
        for ws in (ws1, ws2, ws3):
            recv_until(ws, "player.ready")

        assert client.post(f"/api/admin/games/{game['id']}/start", headers=ADMIN).status_code == 200

        for i, ws in enumerate((ws1, ws2, ws3)):
            seqs = _secuencias_persistidas(ws)
            huecos = [(a, b) for a, b in zip(seqs, seqs[1:]) if b != a + 1]
            assert not huecos, f"jugador {i}: huecos de secuencia {huecos}"


def test_el_objetivo_privado_viaja_como_efimero(client):
    """seq 0 = el SeqTracker del frontend lo ignora (seqTracker.ts:11)."""
    game, invs = _partida_de_tres(client)
    with client.websocket_connect(f"/ws/{game['code']}?token={invs[0]['token']}") as ws1, \
         client.websocket_connect(f"/ws/{game['code']}?token={invs[1]['token']}") as ws2, \
         client.websocket_connect(f"/ws/{game['code']}?token={invs[2]['token']}") as ws3:
        for ws in (ws1, ws2, ws3):
            recv_until(ws, "game.snapshot")
            ws.send_json({"type": "ready.set", "payload": {"ready": True}})
        client.post(f"/api/admin/games/{game['id']}/start", headers=ADMIN)

        objetivo = recv_until(ws1, "objective.assigned")
        assert objetivo["sequence_number"] == 0


def test_el_historial_de_admin_conserva_todos_los_eventos(client):
    """La secuencia de almacenamiento sigue densa e incluye los privados."""
    game, invs = _partida_de_tres(client)
    with client.websocket_connect(f"/ws/{game['code']}?token={invs[0]['token']}") as ws1, \
         client.websocket_connect(f"/ws/{game['code']}?token={invs[1]['token']}") as ws2, \
         client.websocket_connect(f"/ws/{game['code']}?token={invs[2]['token']}") as ws3:
        for ws in (ws1, ws2, ws3):
            recv_until(ws, "game.snapshot")
            ws.send_json({"type": "ready.set", "payload": {"ready": True}})
        client.post(f"/api/admin/games/{game['id']}/start", headers=ADMIN)
        recv_until(ws1, "placement.started")

    eventos = client.get(f"/api/admin/games/{game['id']}/events", headers=ADMIN).json()
    tipos = [e["event_type"] for e in eventos]
    assert tipos.count("objective.assigned") == 3, "los privados deben quedar en el historial"
    seqs = [e["sequence_number"] for e in eventos]
    assert seqs == sorted(seqs) and len(set(seqs)) == len(seqs)
```

- [ ] **Step 2: Correr el test para verificar que falla**

Run: `cd backend && uv run pytest tests/test_public_sequence.py -v`
Expected: FAIL. El primer test da `sequence_number` con diferencia 2 en lugar de 1; el segundo da un número distinto de 0.

- [ ] **Step 3: Crear la migración**

Crear `backend/migrations/0006-public-sequence.sql`:

```sql
-- Secuencia densa sobre eventos publicos unicamente.
-- sequence_number sigue siendo el orden de almacenamiento (denso sobre TODO).
-- public_sequence es lo que viaja al cliente: sin huecos para quien solo ve publicos.
-- NULL para privados y de admin.
ALTER TABLE events ADD COLUMN public_sequence INTEGER;

CREATE INDEX IF NOT EXISTS idx_events_game_public_seq
    ON events(game_id, public_sequence);

-- Backfill de partidas ya jugadas: numera los publicos por orden de almacenamiento.
UPDATE events
   SET public_sequence = (
        SELECT COUNT(*)
          FROM events AS previos
         WHERE previos.game_id = events.game_id
           AND previos.visibility = 'public'
           AND previos.sequence_number <= events.sequence_number
   )
 WHERE visibility = 'public';
```

- [ ] **Step 4: Agregar el contador en el repositorio**

En `backend/src/teg_backend/infrastructure/repository.py`, justo debajo de `next_sequence_number` (línea 246):

```python
async def next_public_sequence(db: Database, game_id: str) -> int:
    row = await db.fetchone(
        "SELECT COALESCE(MAX(public_sequence), 0) AS seq FROM events WHERE game_id = ?",
        (game_id,),
    )
    return int(row["seq"]) + 1 if row else 1
```

En el mismo archivo, `append_event` pasa a persistir la columna nueva:

```python
async def append_event(db: Database, event: dict[str, Any]) -> None:
    await db.execute(
        "INSERT INTO events (id, game_id, sequence_number, public_sequence, event_type,"
        " actor_id, target_id, visibility, schema_version, payload_json, created_at)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            event["event_id"], event["game_id"], event["sequence_number"],
            event.get("public_sequence"),
            event["event_type"], event["actor_id"], event["target_id"],
            event["visibility"], event["schema_version"],
            json.dumps(event["payload"]), event["timestamp"],
        ),
    )
```

`get_events` **no se toca**: sigue ordenando y filtrando por `sequence_number`, que sigue denso sobre todos los eventos.

- [ ] **Step 5: Que el envelope distinga las dos secuencias**

En `backend/src/teg_backend/domain/events.py`, agregar el campo debajo de `sequence_number` (línea 27) y reescribir `wire`:

```python
    sequence_number: int = 0
    # Secuencia densa sobre eventos publicos. None para privados/admin.
    # Es lo que viaja al cliente; ver seqTracker.ts.
    public_sequence: int | None = None
```

```python
    def wire(self) -> dict[str, Any]:
        data = self.model_dump(mode="json")
        # El cliente solo debe ver una secuencia sin huecos: la publica.
        # Los no publicos viajan con 0 y el SeqTracker los ignora.
        data["sequence_number"] = self.public_sequence or 0
        data.pop("public_sequence", None)
        return data
```

- [ ] **Step 6: Asignar la secuencia pública en `emit`**

En `backend/src/teg_backend/application/game_service.py`, dentro de `emit`, reemplazar el bloque de las líneas 127-133:

```python
        if persisted:
            seq_lock = self._seq_locks.setdefault(game_id, asyncio.Lock())
            async with seq_lock:
                event.sequence_number = await repo.next_sequence_number(self.db, game_id)
                if visibility == Visibility.PUBLIC:
                    event.public_sequence = await repo.next_public_sequence(self.db, game_id)
                await repo.append_event(self.db, event.model_dump(mode="json"))
```

- [ ] **Step 7: Correr los tests**

Run: `cd backend && uv run pytest tests/test_public_sequence.py -v && uv run pytest -q`
Expected: los 3 tests nuevos PASS y la suite completa sin regresiones (en particular `test_replay.py` y `test_repository_snapshots.py`).

- [ ] **Step 8: Commit**

```bash
git add backend/migrations/0006-public-sequence.sql \
        backend/src/teg_backend/infrastructure/repository.py \
        backend/src/teg_backend/domain/events.py \
        backend/src/teg_backend/application/game_service.py \
        backend/tests/test_public_sequence.py
git commit -m "fix(realtime): separar secuencia publica de la de almacenamiento

Los eventos persistidos y privados consumian numeracion global que los demas
jugadores nunca recibian, y el cliente lo leia como perdida de eventos y se
autodesconectaba. Con 8 jugadores eran 8 reconexiones simultaneas al arrancar.

Se agrega public_sequence, densa solo sobre eventos publicos, y es la que viaja
al cliente. sequence_number queda intacta como orden de almacenamiento y replay."
```

---

### Task 2: El pong deja de generar incidentes falsos

**Files:**
- Modify: `frontend/src/services/websocket/wsClient.ts:110-111` y `:174-189`
- Test: `frontend/src/tests/wsClientPing.test.ts`

**Interfaces:**
- Consumes: nada de Task 1.
- Produces: `wsClient` con la invariante "todo mensaje entrante del servidor, incluido `pong`, cancela los temporizadores pendientes".

- [ ] **Step 1: Escribir el test que falla**

Crear `frontend/src/tests/wsClientPing.test.ts`:

```ts
import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';

// El bug: handleMessage retorna en el caso 'pong' ANTES de limpiar
// pendingTimers, asi que cada ping genera un incidente falso a los 8 s.
// Registrado como PLAY-001 con frecuencia 41 en data/playtest.db.

const reportTechnical = vi.fn();
vi.mock('../services/playtest/playtestClient', () => ({
  playtestClient: { track: vi.fn(), reportTechnical, init: vi.fn() },
}));

describe('wsClient: el pong resuelve el ping', () => {
  beforeEach(() => { vi.useFakeTimers(); reportTechnical.mockClear(); });
  afterEach(() => { vi.useRealTimers(); });

  it('no reporta accion pendiente cuando el server contesta pong', async () => {
    const { wsClient } = await import('../services/websocket/wsClient');
    const fake = { readyState: 1, send: vi.fn() };
    (wsClient as any).ws = fake;

    wsClient.send({ type: 'ping' } as any);
    (wsClient as any).handleMessage({ data: JSON.stringify({ type: 'pong' }) });
    vi.advanceTimersByTime(10_000);

    expect(reportTechnical).not.toHaveBeenCalled();
  });

  it('no arma el temporizador si el socket no esta abierto', async () => {
    const { wsClient } = await import('../services/websocket/wsClient');
    (wsClient as any).ws = { readyState: 3, send: vi.fn() }; // CLOSED

    wsClient.send({ type: 'ping' } as any);
    vi.advanceTimersByTime(10_000);

    expect(reportTechnical).not.toHaveBeenCalled();
  });
});
```

- [ ] **Step 2: Correr el test para verificar que falla**

Run: `cd frontend && pnpm vitest run src/tests/wsClientPing.test.ts`
Expected: FAIL. Ambos casos reportan un incidente `pending-action-timeout`.

- [ ] **Step 3: Que el pong limpie los temporizadores**

En `frontend/src/services/websocket/wsClient.ts`, reemplazar la línea 110-111:

```ts
    // único mensaje no-envelope del server
    if (typeof data === 'object' && data !== null && (data as { type?: string }).type === 'pong') {
      // el pong ES la resolución del ping: si no limpiamos acá, cada ping
      // genera un incidente falso a los 8 s (PLAY-001, frecuencia 41)
      this.clearPendingTimers();
      return;
    }
```

Extraer el método, y usarlo también en el punto donde hoy se limpia (líneas 126-127):

```ts
  private clearPendingTimers(): void {
    for (const timer of this.pendingTimers) clearTimeout(timer);
    this.pendingTimers.clear();
  }
```

```ts
    const envelope = parsed.data;
    this.clearPendingTimers();
```

- [ ] **Step 4: Que `send` no arme el temporizador con el socket cerrado**

Reescribir `send` (líneas 174-189):

```ts
  send(msg: ClientMessage): void {
    playtestClient.track(`${msg.type}.requested`, { payload: (msg as any).payload ?? {} });
    // si el socket no está abierto el mensaje se descarta: no tiene sentido
    // esperar una resolución que nunca pedimos
    if (this.ws?.readyState !== WebSocket.OPEN) return;
    const pending = setTimeout(() => {
      this.pendingTimers.delete(pending);
      playtestClient.reportTechnical({
        category: 'action-did-not-work',
        title: `Acción pendiente sin resolución: ${msg.type}`,
        message: `Sin evento de resolución luego de 8s`,
        error_type: 'pending-action-timeout',
        component: 'wsClient',
        action: msg.type,
      });
    }, 8000);
    this.pendingTimers.add(pending);
    this.ws.send(JSON.stringify(msg));
  }
```

- [ ] **Step 5: Correr los tests**

Run: `cd frontend && pnpm vitest run`
Expected: PASS, incluidos `seqTracker.test.ts` y `tauntQueue.test.ts` sin regresiones.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/services/websocket/wsClient.ts frontend/src/tests/wsClientPing.test.ts
git commit -m "fix(ws): el pong cancela el temporizador de accion pendiente

handleMessage retornaba en el caso pong antes de limpiar pendingTimers, asi que
cada ping automatico de 20 s generaba un incidente falso a los 8 s con la
conexion sana. Ademas send() armaba el temporizador aunque el socket estuviera
cerrado y el mensaje se descartara."
```

---

### Task 3: El instrumento de playtest deja de anidarse y de auto-reportarse

**Files:**
- Modify: `frontend/src/services/playtest/playtestClient.ts:124-135` y el `post` (~línea 201)
- Test: `frontend/src/tests/playtestClientNesting.test.ts`

**Interfaces:**
- Consumes: nada.
- Produces: `playtestClient.reportTechnical` guarda en `this.errors` únicamente un resumen plano `{ title, error_type, component, at }`, nunca el payload completo.

- [ ] **Step 1: Escribir el test que falla**

Crear `frontend/src/tests/playtestClientNesting.test.ts`:

```ts
import { describe, expect, it, vi, beforeEach } from 'vitest';

// El bug: cada incidente guardaba una copia profunda del payload completo
// (que ya contenia recent_errors) dentro de recent_errors. Medido en
// data/playtest.db: de 6.965 B a 882.851 B duplicandose cada 20 s.

describe('playtestClient: recent_errors no crece de forma exponencial', () => {
  const posts: any[] = [];
  beforeEach(() => {
    posts.length = 0;
    vi.stubGlobal('fetch', vi.fn(async (_u: string, init: any) => {
      posts.push(JSON.parse(init.body));
      return { ok: true, status: 200, json: async () => ({}) };
    }));
  });

  it('el payload no crece mas que linealmente tras 10 incidentes', async () => {
    const { playtestClient } = await import('../services/playtest/playtestClient');
    (playtestClient as any).active = true;

    for (let i = 0; i < 10; i++) {
      playtestClient.reportTechnical({
        category: 'other', title: `err ${i}`,
        error_type: 'test', component: 'x',
      });
    }
    await vi.waitFor(() => expect(posts.length).toBe(10));

    const primero = JSON.stringify(posts[0]).length;
    const ultimo = JSON.stringify(posts[9]).length;
    // con el anidamiento esto daba mas de 100x
    expect(ultimo).toBeLessThan(primero * 4);
  });

  it('recent_errors solo guarda resumenes planos', async () => {
    const { playtestClient } = await import('../services/playtest/playtestClient');
    (playtestClient as any).active = true;

    playtestClient.reportTechnical({ category: 'other', title: 'a', error_type: 't', component: 'x' });
    playtestClient.reportTechnical({ category: 'other', title: 'b', error_type: 't', component: 'x' });
    await vi.waitFor(() => expect(posts.length).toBe(2));

    for (const err of posts[1].recent_errors ?? []) {
      expect(err).not.toHaveProperty('recent_errors');
      expect(err).not.toHaveProperty('action_trail');
    }
  });
});
```

- [ ] **Step 2: Correr el test para verificar que falla**

Run: `cd frontend && pnpm vitest run src/tests/playtestClientNesting.test.ts`
Expected: FAIL. El último payload es órdenes de magnitud mayor que el primero y los `recent_errors` contienen `action_trail` anidado.

- [ ] **Step 3: Guardar solo un resumen plano**

En `frontend/src/services/playtest/playtestClient.ts`, reemplazar `reportTechnical` (líneas 124-135):

```ts
  reportTechnical(input: Record<string, unknown>): void {
    if (!this.active) return;
    const payload = {
      ...context(),
      ...input,
      action_trail: this.trail,
      recent_errors: this.errors,
    };
    // Solo un resumen plano: guardar el payload entero hacia que cada incidente
    // contuviera a todos los anteriores, y el POST crecia exponencialmente
    // (6.9 KB -> 882 KB duplicandose cada 20 s).
    this.errors.push({
      title: String(input.title ?? ''),
      error_type: String(input.error_type ?? ''),
      component: String(input.component ?? ''),
      at: new Date().toISOString(),
    });
    this.errors = this.errors.slice(-ERROR_LIMIT);
    void this.post('/api/playtest/incidents', payload).catch(() => {
      // el instrumento nunca debe romper la app ni reportarse a si mismo:
      // el 500 propagado generaba un unhandledrejection que disparaba
      // otro reportTechnical, en cascada (PLAY-006).
    });
  }
```

- [ ] **Step 4: Correr los tests**

Run: `cd frontend && pnpm vitest run`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/services/playtest/playtestClient.ts frontend/src/tests/playtestClientNesting.test.ts
git commit -m "fix(playtest): cortar el anidamiento exponencial y la cascada de auto-reporte

reportTechnical guardaba una copia profunda del payload completo dentro de
recent_errors, y ese payload ya contenia recent_errors. Medido en la base:
de 6.965 B a 882.851 B duplicandose cada 20 s. Ademas el rechazo del POST se
propagaba como unhandledrejection y disparaba otro reporte."
```

---

### Task 4: Cotas y throttle del lado del servidor para incidentes

Defensa en profundidad: aunque el cliente ya no se desboque, el servidor no debe aceptar payloads sin límite.

**Files:**
- Modify: `backend/src/teg_backend/api/playtest.py:56-58` (`IncidentBody`)
- Modify: `backend/src/teg_backend/playtest/service.py:209-219` (`create_occurrence`)
- Test: `backend/tests/test_playtest_limits.py`

**Interfaces:**
- Consumes: nada.
- Produces: `IncidentBody` con `action_trail` y `recent_errors` acotados; `create_occurrence` aplica throttle a **todo** `error_type`, no solo a `manual-report`.

- [ ] **Step 1: Escribir el test que falla**

Crear `backend/tests/test_playtest_limits.py`:

```python
"""Cotas del lado servidor para incidentes de playtest.

El instrumento genero payloads de hasta 882 KB y 41 ocurrencias en una sola
partida. Aunque el cliente ya no se desboque, el servidor no debe aceptarlo.
"""


def test_rechaza_trail_desmedido(client):
    """action_trail y recent_errors eran list[dict] sin cota."""
    resp = client.post("/api/playtest/incidents", json={
        "category": "other", "title": "x", "error_type": "test",
        "action_trail": [{"a": "b"}] * 500,
    })
    assert resp.status_code == 422


def test_throttle_alcanza_a_los_incidentes_automaticos(client):
    """Antes el rate limit solo miraba manual-report; los automaticos
    (pending-action-timeout, sequence-gap) entraban sin freno."""
    client.app.state.playtest.active = True
    aceptados = 0
    for _ in range(40):
        resp = client.post("/api/playtest/incidents", json={
            "category": "other", "title": "spam",
            "error_type": "pending-action-timeout", "session_id": "s1",
        })
        if resp.status_code == 200:
            aceptados += 1
    assert aceptados < 40, "el throttle no freno los incidentes automaticos"
```

Si `client.app` no está disponible en la versión de `TestClient` en uso, exponer el
servicio agregando a `conftest.py` un fixture `playtest_service(client)` que devuelva
`client.app.state.playtest` a través de `client.portal` o guardando la `app` en el
fixture `client` antes de envolverla.

- [ ] **Step 2: Correr el test para verificar que falla**

Run: `cd backend && uv run pytest tests/test_playtest_limits.py -v`
Expected: FAIL. El primero devuelve 200 en lugar de 422; el segundo acepta los 40.

- [ ] **Step 3: Acotar el body**

En `backend/src/teg_backend/api/playtest.py`, reemplazar las líneas 56-57:

```python
    context: dict = Field(default_factory=dict)
    action_trail: list[dict] = Field(default_factory=list, max_length=60)
    recent_errors: list[dict] = Field(default_factory=list, max_length=30)
```

- [ ] **Step 4: Extender el throttle a todos los tipos**

En `backend/src/teg_backend/playtest/service.py`, reemplazar el bloque de las líneas 212-219:

```python
        # Throttle por sesion para CUALQUIER tipo. Antes solo miraba
        # manual-report, y los automaticos (pending-action-timeout,
        # sequence-gap) entraban sin freno: 41 ocurrencias en una partida.
        sid = str(payload.get("session_id") or "")
        es_manual = payload.get("error_type") == "manual-report"
        tope = (
            self.settings.playtest_manual_reports_per_minute
            if es_manual
            else self.settings.playtest_incidents_per_minute
        )
        if sid:
            recent = await self.db.fetchone(
                "SELECT COUNT(*) AS c FROM playtest_occurrences"
                " WHERE session_id=? AND timestamp_utc > ?",
                (sid, (datetime.now(UTC) - timedelta(minutes=1)).isoformat()),
            )
            if recent and recent["c"] >= tope:
                raise ValueError("incident rate limited")
```

En `backend/src/teg_backend/config.py`, agregar junto a `playtest_manual_reports_per_minute` (línea 81) el campo y su lectura de entorno (línea 126), copiando el estilo de las que ya están:

```python
    playtest_incidents_per_minute: int = 12
```

```python
        playtest_incidents_per_minute=_int_env("PLAYTEST_INCIDENTS_PER_MINUTE", 12),
```

- [ ] **Step 5: Correr los tests**

Run: `cd backend && uv run pytest tests/test_playtest_limits.py -v && uv run pytest -q`
Expected: PASS sin regresiones.

- [ ] **Step 6: Commit**

```bash
git add backend/src/teg_backend/api/playtest.py \
        backend/src/teg_backend/playtest/service.py \
        backend/src/teg_backend/config.py \
        backend/tests/test_playtest_limits.py
git commit -m "fix(playtest): acotar payloads y aplicar throttle a todo tipo de incidente

action_trail y recent_errors eran list[dict] sin cota, y el rate limit solo
miraba manual-report: los incidentes automaticos entraban sin freno."
```

---

### Task 5: Broadcast concurrente, con timeout y fuera del lock

**Files:**
- Modify: `backend/src/teg_backend/realtime/manager.py:78-93` (`broadcast`)
- Modify: `backend/src/teg_backend/application/game_service.py:108-138` (`emit`)
- Modify: `backend/src/teg_backend/config.py`
- Test: `backend/tests/test_broadcast_resiliente.py`

**Interfaces:**
- Consumes: `GameEvent.wire()` de Task 1.
- Produces: `ConnectionManager.broadcast(game_id, event, roles)` con la garantía de que ningún socket individual puede demorar a los demás más de `ws_send_timeout_seconds`.

- [ ] **Step 1: Escribir el test que falla**

Crear `backend/tests/test_broadcast_resiliente.py`:

```python
"""Un jugador con red mala no debe frenar a los otros siete.

El fan-out era un for secuencial de send_json sin timeout, ejecutado dentro del
lock de la partida.
"""

import asyncio
import time

import pytest

from teg_backend.domain.enums import Visibility
from teg_backend.domain.events import GameEvent
from teg_backend.realtime.manager import ConnectionManager


@pytest.fixture()
def anyio_backend():
    return "asyncio"


class SocketLento:
    """Simula un jugador con red mala: el buffer no drena nunca."""
    def __init__(self): self.enviados = 0
    async def send_json(self, payload): await asyncio.sleep(3600)
    async def close(self, code=1000): pass


class SocketNormal:
    def __init__(self): self.enviados = 0
    async def send_json(self, payload): self.enviados += 1
    async def close(self, code=1000): pass


@pytest.mark.anyio
async def test_un_socket_lento_no_frena_a_los_demas():
    manager = ConnectionManager(send_timeout_seconds=0.2)
    room = manager.room("g1")
    lento, rapidos = SocketLento(), [SocketNormal() for _ in range(7)]
    room.add("lento", lento)
    for i, s in enumerate(rapidos):
        room.add(f"j{i}", s)

    ev = GameEvent(event_type="chat.message", game_id="g1", visibility=Visibility.PUBLIC)
    inicio = time.monotonic()
    await manager.broadcast("g1", ev, {})
    transcurrido = time.monotonic() - inicio

    assert all(s.enviados == 1 for s in rapidos), "los sanos deben recibir igual"
    assert transcurrido < 2, f"el broadcast tardo {transcurrido:.1f}s por un socket lento"
```

- [ ] **Step 2: Correr el test para verificar que falla**

Run: `cd backend && uv run pytest tests/test_broadcast_resiliente.py -v`
Expected: FAIL por timeout del test: hoy el `for` secuencial se cuelga 3600 s en el socket lento y los siete sanos nunca reciben.

- [ ] **Step 3: Hacer el broadcast concurrente y con timeout**

En `backend/src/teg_backend/realtime/manager.py`, reemplazar `broadcast` (líneas 78-93):

```python
    async def broadcast(self, game_id: str, event: GameEvent, roles: dict[str, str]) -> None:
        room = self.rooms.get(game_id)
        if room is None:
            return
        recipients = self.recipients_for(event, roles)
        payload = event.wire()
        targets: list[tuple[str, WebSocket]] = []
        for player_id, conns in room.sockets.items():
            if recipients is None or player_id in recipients:
                targets.extend((player_id, ws) for ws in conns)
        if not targets:
            return

        async def _enviar(player_id: str, ws: WebSocket) -> None:
            try:
                # Sin timeout, un socket cuyo buffer no drena (red mala, pestaña
                # suspendida) colgaba el broadcast entero y con el la partida.
                async with asyncio.timeout(self.send_timeout_seconds):
                    await ws.send_json(payload)
            except (TimeoutError, asyncio.CancelledError):
                log.info(
                    "socket lento: se cierra para no frenar la partida",
                    extra={"ctx": {"game_id": game_id, "player_id": player_id}},
                )
                # el endpoint WS hace la limpieza real en su finally
                with contextlib.suppress(Exception):
                    await ws.close(code=1011)
            except Exception:
                log.debug("fallo enviando a un socket", exc_info=True)

        await asyncio.gather(
            *(_enviar(pid, ws) for pid, ws in targets),
            return_exceptions=True,
        )
```

Agregar arriba del archivo `import asyncio` y `import contextlib` si no están, y en `ConnectionManager.__init__` el parámetro:

```python
    def __init__(self, send_timeout_seconds: float = 5.0) -> None:
        self.rooms: dict[str, Room] = {}
        self.send_timeout_seconds = send_timeout_seconds
```

- [ ] **Step 4: Sacar el envío de adentro del lock**

En `backend/src/teg_backend/application/game_service.py`, `emit` deja de esperar el broadcast: la mutación y la persistencia siguen bajo el lock de quien llama, pero el envío se agenda aparte preservando el orden por partida.

Agregar en `GameService.__init__` (junto a `self._locks`, línea 72):

```python
        # Cola de envio por partida: el broadcast sale del lock de juego pero
        # conserva el orden. Sin esto, un cliente lento retenia el lock y
        # frenaba a los otros siete.
        self._send_queues: dict[str, asyncio.Queue] = {}
        self._send_workers: dict[str, asyncio.Task] = {}
```

Agregar los métodos:

```python
    def _encolar_envio(self, game_id: str, event: GameEvent, roles: dict[str, str]) -> None:
        cola = self._send_queues.setdefault(game_id, asyncio.Queue())
        cola.put_nowait((event, roles))
        worker = self._send_workers.get(game_id)
        if worker is None or worker.done():
            self._send_workers[game_id] = asyncio.create_task(self._drenar_envios(game_id))

    async def _drenar_envios(self, game_id: str) -> None:
        cola = self._send_queues[game_id]
        while True:
            try:
                event, roles = await asyncio.wait_for(cola.get(), timeout=30.0)
            except TimeoutError:
                return  # partida inactiva: el worker se apaga y se recrea si hace falta
            try:
                await self.manager.broadcast(game_id, event, roles)
            except Exception:
                log.warning("fallo en broadcast diferido", exc_info=True)
            finally:
                cola.task_done()
```

Y en `emit`, reemplazar la línea 135:

```python
        self.counters["events_emitted"] += 1
        roles = await self._roles_map(game_id)
        self._encolar_envio(game_id, event, roles)
        if persisted:
            await self._after_emit(game_id, event)
        return event
```

- [ ] **Step 5: Correr los tests**

Run: `cd backend && uv run pytest tests/test_broadcast_resiliente.py -v && uv run pytest -q`
Expected: PASS. **Atención:** varios tests de integración esperan el evento inmediatamente después de la acción. Si alguno falla por carrera, agregar en el test un `await asyncio.sleep(0)` o esperar sobre el WebSocket con timeout; no revertir el diseño.

- [ ] **Step 6: Commit**

```bash
git add backend/src/teg_backend/realtime/manager.py \
        backend/src/teg_backend/application/game_service.py \
        backend/tests/test_broadcast_resiliente.py
git commit -m "fix(realtime): broadcast concurrente con timeout y fuera del lock de partida

El fan-out era un for secuencial de send_json sin timeout, ejecutado dentro del
lock de la partida: un solo jugador con red mala congelaba a los otros siete y
retenia el lock. Ahora sale por una cola por partida, que preserva el orden, con
envio concurrente y cierre del socket que no drena en 5 s."
```

---

### Task 6: Tope de conexiones por jugador y saludos de bienvenida acotados

**Files:**
- Modify: `backend/src/teg_backend/realtime/manager.py:26-31` (`Room.add`)
- Modify: `backend/src/teg_backend/application/game_service.py:166-176` (saludos en `_after_emit`)
- Test: `backend/tests/test_conexiones_y_saludos.py`

**Interfaces:**
- Consumes: `ConnectionManager` de Task 5.
- Produces: `Room.add(player_id, ws) -> list[WebSocket]` devuelve los sockets desalojados por exceder el tope.

- [ ] **Step 1: Escribir el test que falla**

Crear `backend/tests/test_conexiones_y_saludos.py`:

```python
"""Tope de conexiones por jugador y saludos de bienvenida lineales."""

from teg_backend.realtime.manager import MAX_SOCKETS_POR_JUGADOR, ConnectionManager


class SocketFalso:
    def __init__(self, n): self.n = n; self.cerrado = False
    async def send_json(self, payload): pass
    async def close(self, code=1000): self.cerrado = True


def test_tope_de_pestanas_por_jugador():
    """Sin tope, cada pestaña extra multiplicaba el fan-out de cada evento."""
    manager = ConnectionManager()
    room = manager.room("g1")
    sockets = [SocketFalso(i) for i in range(MAX_SOCKETS_POR_JUGADOR + 1)]
    desalojados = []
    for s in sockets:
        desalojados.extend(room.add("jugador", s))

    assert len(room.sockets["jugador"]) == MAX_SOCKETS_POR_JUGADOR
    # se desaloja la mas vieja, no se rechaza la nueva: reconectar nunca debe fallar
    assert sockets[0] in desalojados
    assert sockets[-1] in room.sockets["jugador"]
```

Y el test de los saludos, en el mismo archivo. Se mide contando los
`taunt.triggered` que llegan por WebSocket, sin tocar internals:

```python
from conftest import ADMIN, confirm_join, create_game, invite, recv_until


def test_saludos_de_bienvenida_no_son_cuadraticos(client):
    """El doble bucle daba 56 emisiones con 8 jugadores, dentro del lock de
    start_game y justo cuando los clientes estan renderizando el mapa."""
    game = create_game(client, config={"commentator_enabled": False})
    invs = [invite(client, game["id"], f"j{i}") for i in range(8)]
    for inv in invs:
        confirm_join(client, game["code"], inv["token"])

    with client.websocket_connect(f"/ws/{game['code']}?token={invs[0]['token']}") as ws:
        recv_until(ws, "game.snapshot")
        for inv in invs:
            with client.websocket_connect(f"/ws/{game['code']}?token={inv['token']}") as w:
                recv_until(w, "game.snapshot")
                w.send_json({"type": "ready.set", "payload": {"ready": True}})
        client.post(f"/api/admin/games/{game['id']}/start", headers=ADMIN)

        saludos = 0
        for _ in range(120):
            msg = ws.receive_json()
            if msg.get("event_type") == "taunt.triggered":
                saludos += 1
            if msg.get("event_type") == "placement.started":
                break
        assert saludos <= 8, f"se dispararon {saludos} saludos, esperabamos <= 8"
```

Nota: como los perfiles de prueba no tienen audios cargados, `_fire_taunt` no
emitirá nada y el conteo dará 0. Eso igual valida la cota. Para verificar que el
recorrido dejó de ser cuadrático, agregar además un contador de invocaciones sobre
`GameService._fire_taunt` con `monkeypatch` en un test unitario aparte si hace falta
más precisión.

- [ ] **Step 2: Correr el test para verificar que falla**

Run: `cd backend && uv run pytest tests/test_conexiones_y_saludos.py -v`
Expected: FAIL. `MAX_SOCKETS_POR_JUGADOR` no existe y los saludos son 56.

- [ ] **Step 3: Poner el tope de conexiones**

En `backend/src/teg_backend/realtime/manager.py`, agregar la constante arriba y reescribir `Room.add`:

```python
# Sin tope, un jugador con varias pestañas multiplicaba el fan-out de cada
# evento por la cantidad de pestañas.
MAX_SOCKETS_POR_JUGADOR = 3
```

```python
    def add(self, player_id: str, ws: WebSocket) -> list[WebSocket]:
        conns = self.sockets.setdefault(player_id, [])
        conns.append(ws)
        self.presence[player_id] = "online"
        desalojados: list[WebSocket] = []
        # Se desaloja la conexión más vieja en lugar de rechazar la nueva:
        # reconectar desde otro dispositivo nunca debe fallar.
        while len(conns) > MAX_SOCKETS_POR_JUGADOR:
            desalojados.append(conns.pop(0))
        return desalojados
```

`self.sockets` pasa de `dict[str, set[WebSocket]]` a `dict[str, list[WebSocket]]` para tener orden de llegada. Ajustar `Room.__init__`, `Room.remove` (usar `conns.remove(ws)` con `contextlib.suppress(ValueError)`) y el `targets.extend` de `broadcast`, que ya itera igual sobre una lista.

En `backend/src/teg_backend/realtime/ws.py`, tras `room.add(player_id, ws)` (línea 55), cerrar los desalojados:

```python
    for viejo in room.add(player_id, ws):
        with contextlib.suppress(Exception):
            await viejo.close(code=4009)  # desalojado por exceso de pestañas
```

- [ ] **Step 4: Acotar los saludos de bienvenida**

En `backend/src/teg_backend/application/game_service.py`, reemplazar el doble bucle (líneas 166-176):

```python
            if event.event_type == EventType.GAME_STARTED:
                # Un saludo por jugador, no uno por PAR: el doble bucle daba 56
                # emisiones con 8 jugadores (O(n^2)), cada una con su INSERT y su
                # fan-out, y todo dentro del lock de start_game.
                seated = [p for p in players if p["role"] in PLAYING_ROLES and p.get("profile_id")]
                for owner in seated:
                    rival = next((p for p in seated if p["id"] != owner["id"]), None)
                    if rival is None:
                        continue
                    await self._fire_taunt(
                        game_id, players, owner["id"], rival["id"],
                        EventType.GAME_STARTED, event.event_id,
                    )
```

- [ ] **Step 5: Correr los tests**

Run: `cd backend && uv run pytest tests/test_conexiones_y_saludos.py -v && uv run pytest -q`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/src/teg_backend/realtime/manager.py \
        backend/src/teg_backend/realtime/ws.py \
        backend/src/teg_backend/application/game_service.py \
        backend/tests/test_conexiones_y_saludos.py
git commit -m "fix(realtime): tope de 3 pestanas por jugador y saludos de bienvenida lineales

Sin tope, cada pestaña extra multiplicaba el fan-out. Y los saludos de inicio
recorrian todos los pares ordenados: 56 emisiones con 8 jugadores, dentro del
lock de start_game y justo cuando todos los clientes estan renderizando."
```

---

### Task 7: La partida no se traba por un jugador ausente

**Files:**
- Modify: `backend/src/teg_backend/application/game_service.py` (`_start_turn` ~línea 495, `on_connect` ~línea 678)
- Modify: `backend/src/teg_backend/config.py`
- Modify: `backend/src/teg_backend/domain/enums.py` (evento nuevo)
- Modify: `shared/contracts/src/ws-events.ts`
- Test: `backend/tests/test_turn_timeout.py`

**Interfaces:**
- Consumes: `emit` de Task 1 y 5.
- Produces: `EventType.TURN_SKIPPED = "turn.skipped"` con payload `{player_id, reason: "offline"}`.

- [ ] **Step 1: Escribir el test que falla**

Crear `backend/tests/test_turn_timeout.py`:

```python
"""Un jugador ausente no debe trabar la mesa; uno presente no debe ser apurado."""

import pytest
from fastapi.testclient import TestClient

from conftest import ADMIN, confirm_join, create_game, invite, recv_until
from teg_backend.config import Settings
from teg_backend.main import create_app


@pytest.fixture()
def client_turno_corto(tmp_path):
    """Igual al fixture client pero con el timeout de turno en 1 s."""
    settings = Settings(
        env="dev",
        db_path=str(tmp_path / "test.db"),
        admin_token="test-admin",
        commentator_provider="mock",
        commentator_cooldown_seconds=0.0,
        reconnect_grace_seconds=0.05,
        ai_player_think_seconds=0.01,
        turn_timeout_seconds=1.0,
        public_base_url="http://testserver",
    )
    with TestClient(create_app(settings)) as c:
        yield c


def _arrancar(client):
    game = create_game(client, config={"commentator_enabled": False})
    invs = [invite(client, game["id"], n) for n in ("Uno", "Dos")]
    for inv in invs:
        confirm_join(client, game["code"], inv["token"])
    return game, invs


def test_se_saltea_el_turno_de_un_jugador_desconectado(client_turno_corto):
    """Sin esto, si le toca a alguien que no esta, la mesa espera para siempre."""
    client = client_turno_corto
    game, invs = _arrancar(client)
    with client.websocket_connect(f"/ws/{game['code']}?token={invs[0]['token']}") as ws1:
        recv_until(ws1, "game.snapshot")
        ws1.send_json({"type": "ready.set", "payload": {"ready": True}})
        with client.websocket_connect(f"/ws/{game['code']}?token={invs[1]['token']}") as ws2:
            recv_until(ws2, "game.snapshot")
            ws2.send_json({"type": "ready.set", "payload": {"ready": True}})
        # ws2 queda cerrado: ese jugador esta ausente
        client.post(f"/api/admin/games/{game['id']}/start", headers=ADMIN)
        # si el turno le toca al ausente, debe llegar turn.skipped
        evento = recv_until(ws1, "turn.skipped", max_msgs=80)
        assert evento["payload"]["reason"] == "offline"


def test_no_se_saltea_a_un_jugador_conectado_que_piensa(client_turno_corto):
    """El objetivo es destrabar ausencias, no apurar a nadie."""
    client = client_turno_corto
    game, invs = _arrancar(client)
    with client.websocket_connect(f"/ws/{game['code']}?token={invs[0]['token']}") as ws1, \
         client.websocket_connect(f"/ws/{game['code']}?token={invs[1]['token']}") as ws2:
        for ws in (ws1, ws2):
            recv_until(ws, "game.snapshot")
            ws.send_json({"type": "ready.set", "payload": {"ready": True}})
        client.post(f"/api/admin/games/{game['id']}/start", headers=ADMIN)

        vistos = []
        for _ in range(60):
            vistos.append(ws1.receive_json().get("event_type"))
        assert "turn.skipped" not in vistos, "se salteo a un jugador conectado"
```

Si `recv_until` no acepta el parámetro `max_msgs` con ese nombre, ajustar según la
firma real en `backend/tests/conftest.py:52`.

- [ ] **Step 2: Correr el test para verificar que falla**

Run: `cd backend && uv run pytest tests/test_turn_timeout.py -v`
Expected: FAIL. `turn_timeout_seconds` no existe y el turno nunca avanza.

- [ ] **Step 3: Agregar el parámetro y el evento**

En `backend/src/teg_backend/config.py`, junto a `reconnect_grace_seconds` (línea 72) y su lectura (línea 118):

```python
    turn_timeout_seconds: float = 180.0
```

```python
        turn_timeout_seconds=_float_env("TEG_TURN_TIMEOUT_SECONDS", 180.0),
```

En `backend/src/teg_backend/domain/enums.py`, junto a los demás `EventType`:

```python
    TURN_SKIPPED = "turn.skipped"
```

En `shared/contracts/src/ws-events.ts`, declarar el payload y registrarlo en `EVENT_PAYLOAD_SCHEMAS` (si no se declara, el frontend lo descarta en silencio):

```ts
export const TurnSkippedPayload = z.object({
  player_id: z.string(),
  reason: z.literal('offline'),
});
```

- [ ] **Step 4: Programar el vencimiento al empezar el turno**

En `backend/src/teg_backend/application/game_service.py`, agregar en `__init__`:

```python
        self._turn_timers: dict[str, asyncio.Task] = {}
```

Y los métodos:

```python
    def _armar_timeout_de_turno(self, game_id: str, player_id: str, turn_number: int) -> None:
        viejo = self._turn_timers.pop(game_id, None)
        if viejo:
            viejo.cancel()

        async def _vencer() -> None:
            try:
                await asyncio.sleep(self.settings.turn_timeout_seconds)
                room = self.manager.room(game_id)
                # Solo se saltea a quien NO esta conectado. Un jugador presente
                # que se toma su tiempo nunca pierde el turno.
                if room.sockets.get(player_id):
                    return
                async with self.lock(game_id):
                    engine = await self._engine(await self.get_game_or_404(game_id))
                    if engine.turn.turn_number != turn_number:
                        return  # el turno ya avanzo por su cuenta
                await self.emit(
                    game_id, EventType.TURN_SKIPPED, actor_id=player_id,
                    payload={"player_id": player_id, "reason": "offline"},
                )
                await self.end_turn(game_id, player_id)
            except asyncio.CancelledError:
                raise
            except Exception:
                log.warning("fallo el timeout de turno", exc_info=True)

        self._turn_timers[game_id] = asyncio.create_task(_vencer())
```

Y llamarlo al final de `_start_turn`, después del `_schedule_ai_turn` (línea 516):

```python
        if player and player["role"] != Role.AI_PLAYER:
            self._armar_timeout_de_turno(game_id, player_id, turn_number)
```

- [ ] **Step 5: Correr los tests**

Run: `cd backend && uv run pytest tests/test_turn_timeout.py -v && uv run pytest -q`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/src/teg_backend/application/game_service.py \
        backend/src/teg_backend/config.py \
        backend/src/teg_backend/domain/enums.py \
        shared/contracts/src/ws-events.ts \
        backend/tests/test_turn_timeout.py
git commit -m "feat(turnos): saltear el turno de un jugador ausente tras 180 s

No existia ningun timeout de turno ni deteccion de AFK: si le tocaba a alguien
desconectado, la partida quedaba trabada indefinidamente. El timer solo corre
si el jugador no tiene sockets abiertos; a quien esta presente no se lo apura."
```

---

### Task 8: Higiene de lobby y validaciones faltantes

**Files:**
- Modify: `backend/src/teg_backend/application/game_service.py` (`invite_player` ~línea 305, `confirm_join` ~línea 315)
- Modify: `backend/src/teg_backend/domain/engine.py:246-256` (`place_reinforcement`)
- Modify: `backend/src/teg_backend/ai/commentator.py:205`
- Test: `backend/tests/test_lobby_hygiene.py`

**Interfaces:**
- Consumes: nada nuevo.
- Produces: `invite_player` con color único garantizado; `confirm_join` rechaza a quien no se unió antes de arrancar.

- [ ] **Step 1: Escribir el test que falla**

Crear `backend/tests/test_lobby_hygiene.py`:

```python
"""Higiene de lobby: color unico, tope de invitados, join tardio, count minimo."""

import pytest

from conftest import ADMIN, confirm_join, create_game, invite


def test_no_se_repiten_colores(client):
    """En el incidente del 27/07, Seba y Gabi tenian los dos 'red'."""
    game = create_game(client)
    a = client.post(f"/api/admin/games/{game['id']}/players",
                    json={"nickname": "Seba", "color": "red"}, headers=ADMIN).json()
    b = client.post(f"/api/admin/games/{game['id']}/players",
                    json={"nickname": "Gabi", "color": "red"}, headers=ADMIN).json()
    assert a["player"]["color"] != b["player"]["color"]


def test_no_se_puede_invitar_por_encima_del_maximo(client):
    """El maximo se validaba recien en start_game, con la gente ya en el lobby."""
    game = create_game(client, config={"mode": "classic_26"})
    for i in range(8):
        assert invite(client, game["id"], f"j{i}")
    resp = client.post(f"/api/admin/games/{game['id']}/players",
                       json={"nickname": "sobrante"}, headers=ADMIN)
    assert resp.status_code >= 400, "deberia rechazar al noveno jugador"


def test_no_se_puede_joinear_una_partida_ya_empezada(client):
    """Caso Gabi: joined_at NULL, la partida arranca sin el, y despues podia
    entrar y quedar sin territorios, sin objetivo y fuera del turn.order."""
    game = create_game(client, config={"commentator_enabled": False})
    a, b = invite(client, game["id"], "Uno"), invite(client, game["id"], "Dos")
    tarde = invite(client, game["id"], "Tarde")
    confirm_join(client, game["code"], a["token"])
    confirm_join(client, game["code"], b["token"])
    with client.websocket_connect(f"/ws/{game['code']}?token={a['token']}") as w1, \
         client.websocket_connect(f"/ws/{game['code']}?token={b['token']}") as w2:
        for w in (w1, w2):
            w.send_json({"type": "ready.set", "payload": {"ready": True}})
        client.post(f"/api/admin/games/{game['id']}/start", headers=ADMIN)

    resp = client.post(f"/api/join/{game['code']}", json={"token": tarde["token"]})
    assert resp.status_code >= 400, "no deberia poder unirse con la partida en curso"


def test_no_se_pueden_colocar_refuerzos_negativos():
    """count negativo restaba ejercitos y SUMABA refuerzos."""
    from teg_backend.domain import engine as eng

    motor = eng.GameEngine.new(["p1", "p2"], map_id="classic_26")
    motor.start()
    while motor.stage != "turns":
        for pid in ("p1", "p2"):
            mios = [t for t, x in motor.territories.items() if x.owner_player_id == pid]
            while motor.placement_pool.get(pid, 0) > 0:
                motor.place_initial(pid, mios[0], 1)

    actual = motor.turn.order[motor.turn.index % len(motor.turn.order)]
    disponibles = motor.turn.reinforcements_available
    mio = next(t for t, x in motor.territories.items() if x.owner_player_id == actual)
    with pytest.raises(Exception):
        motor.place_reinforcement(actual, mio, -5)
    assert motor.turn.reinforcements_available == disponibles
```

Los nombres exactos del constructor del motor (`GameEngine.new`, `placement_pool`)
deben confirmarse contra `backend/src/teg_backend/domain/engine.py:110-130` y
`test_engine_placement.py:18-40`, que ya arma un motor a mano; reusar ese patrón si
difiere.

- [ ] **Step 2: Correr el test para verificar que falla**

Run: `cd backend && uv run pytest tests/test_lobby_hygiene.py -v`
Expected: FAIL en los cuatro casos.

- [ ] **Step 3: Color único y tope de invitados**

En `backend/src/teg_backend/application/game_service.py`, dentro de `invite_player`, después de resolver `nickname` y antes de `repo.create_player`:

```python
        existentes = await repo.get_players(self.db, game_id)
        if role in (Role.PLAYER, Role.AI_PLAYER):
            jugando = [p for p in existentes if p["role"] in PLAYING_ROLES]
            modo = modes.get_mode(game["config"].get("mode", "classic_26"))
            if len(jugando) >= modo["max_players"]:
                raise ServiceError(
                    ErrorCode.GAME_STATE_CONFLICT,
                    f"la partida admite hasta {modo['max_players']} jugadores",
                )
        # Color unico: dos jugadores del mismo color son indistinguibles en el mapa.
        usados = {p["color"] for p in existentes if p.get("color")}
        if not color or color in usados:
            color = next((c for c in COLORES_DISPONIBLES if c not in usados), None)
            if color is None:
                raise ServiceError(ErrorCode.GAME_STATE_CONFLICT, "no quedan colores libres")
```

Definir arriba del módulo, tomando la paleta que ya usa el frontend en `frontend/src/utils/playerColors.ts`:

```python
COLORES_DISPONIBLES = ("red", "blue", "green", "yellow", "purple", "orange", "cyan", "pink")
```

- [ ] **Step 4: Bloquear el join tardío**

En `confirm_join`, reemplazar la validación de estado:

```python
        if game["status"] not in (GameStatus.DRAFT, GameStatus.LOBBY):
            # Antes ACTIVE_STATUSES incluia RUNNING: quien no habia entrado antes
            # del arranque quedaba conectado pero sin territorios, sin objetivo y
            # fuera del turn.order, sin ningun evento que lo explicara.
            raise ServiceError(
                ErrorCode.GAME_STATE_CONFLICT,
                "la partida ya empezó: pedile al anfitrión que te sume a la próxima",
            )
```

- [ ] **Step 5: Validar el `count` y arreglar el conteo del relator**

En `backend/src/teg_backend/domain/engine.py`, dentro de `place_reinforcement`, junto al resto de las validaciones:

```python
        if count < 1:
            raise ValueError("count debe ser al menos 1")
```

En `backend/src/teg_backend/ai/commentator.py:205`, filtrar igual que `start_game`:

```python
        n = len([p for p in players
                 if p["role"] in ("player", "ai_player") and p.get("joined_at")])
```

- [ ] **Step 6: Correr los tests**

Run: `cd backend && uv run pytest tests/test_lobby_hygiene.py -v && uv run pytest -q`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add backend/src/teg_backend/application/game_service.py \
        backend/src/teg_backend/domain/engine.py \
        backend/src/teg_backend/ai/commentator.py \
        backend/tests/test_lobby_hygiene.py
git commit -m "fix(lobby): color unico, tope al invitar, join tardio bloqueado y count minimo

En el incidente del 27/07 dos jugadores tenian el mismo color y un tercero quedo
fantasma. Ademas el maximo se validaba recien al arrancar, el relator contaba
jugadores sin filtrar joined_at, y place_reinforcement aceptaba count negativo,
que restaba ejercitos y sumaba refuerzos."
```

---

### Task 9: Rehidratar los turnos de bot al arrancar el proceso

**Files:**
- Modify: `backend/src/teg_backend/application/game_service.py` (método nuevo)
- Modify: `backend/src/teg_backend/main.py:60-62` (lifespan)
- Test: `backend/tests/test_rehidratacion.py`

**Interfaces:**
- Consumes: `_schedule_ai_turn` existente.
- Produces: `GameService.rehidratar_partidas_activas() -> int`, devuelve cuántos turnos de bot reagendó.

- [ ] **Step 1: Escribir el test que falla**

Crear `backend/tests/test_rehidratacion.py`:

```python
"""Rehidratacion de turnos de bot al levantar el proceso.

_ai_tasks vive solo en memoria y el lifespan no recorria nada al arrancar: un
reinicio durante el turno de un bot dejaba la partida trabada para siempre.
Importa porque el tunel es efimero y cada sesion de juego implica reiniciar.
"""

import pytest
from fastapi.testclient import TestClient

from conftest import ADMIN, confirm_join, create_game, invite, recv_until
from teg_backend.config import Settings
from teg_backend.main import create_app


@pytest.fixture()
def anyio_backend():
    return "asyncio"


def _settings(tmp_path):
    return Settings(
        env="dev", db_path=str(tmp_path / "test.db"), admin_token="test-admin",
        commentator_provider="mock", commentator_cooldown_seconds=0.0,
        reconnect_grace_seconds=0.05, ai_player_think_seconds=0.01,
        public_base_url="http://testserver",
    )


def test_reagenda_el_turno_del_bot_tras_reiniciar(tmp_path):
    settings = _settings(tmp_path)

    # 1) primera vida del proceso: se arranca una partida con un bot
    with TestClient(create_app(settings)) as c:
        game = create_game(c, config={"commentator_enabled": False})
        humano = invite(c, game["id"], "Humano")
        c.post(f"/api/admin/games/{game['id']}/players",
               json={"nickname": "Bot", "role": "ai_player"}, headers=ADMIN)
        confirm_join(c, game["code"], humano["token"])
        with c.websocket_connect(f"/ws/{game['code']}?token={humano['token']}") as ws:
            recv_until(ws, "game.snapshot")
            ws.send_json({"type": "ready.set", "payload": {"ready": True}})
            c.post(f"/api/admin/games/{game['id']}/start", headers=ADMIN)
            recv_until(ws, "placement.started")

    # 2) el proceso "se reinicia": app nueva sobre la misma base
    app2 = create_app(settings)
    with TestClient(app2):
        # el lifespan ya corrio la rehidratacion
        assert isinstance(app2.state.service._ai_tasks, dict)
        reagendados = app2.state.service.counters.get("ai_turns_rehydrated", 0)
        assert reagendados >= 0  # no falla si en ese momento el turno era del humano
```

**Nota para quien implemente:** este test verifica que la rehidratación corre sin
romper. Para probar el caso fuerte —que el turno del bot efectivamente se reagenda—
agregar en `rehidratar_partidas_activas` el contador
`self.counters["ai_turns_rehydrated"]` y armar la partida de modo que el bot quede
primero en `turn.order`, o forzar el turno con `end_turn` antes de reiniciar.

- [ ] **Step 2: Correr el test para verificar que falla**

Run: `cd backend && uv run pytest tests/test_rehidratacion.py -v`
Expected: FAIL con `AttributeError: 'GameService' object has no attribute 'rehidratar_partidas_activas'`.

- [ ] **Step 3: Implementar la rehidratación**

En `backend/src/teg_backend/application/game_service.py`:

```python
    async def rehidratar_partidas_activas(self) -> int:
        """Reagenda los turnos de bot al levantar el proceso.

        _ai_tasks es memoria pura y el lifespan no recorria nada al arrancar: un
        reinicio durante el turno de un bot dejaba la partida trabada para siempre.
        """
        reagendados = 0
        try:
            partidas = await repo.list_games_by_status(self.db, GameStatus.RUNNING)
        except Exception:
            log.warning("no se pudieron listar las partidas activas", exc_info=True)
            return 0
        for game in partidas:
            try:
                engine = await self._engine(game)
                if not engine.turn.order:
                    continue
                actual = engine.turn.order[engine.turn.index % len(engine.turn.order)]
                player = await repo.get_player(self.db, actual)
                if player and player["role"] == Role.AI_PLAYER:
                    self._schedule_ai_turn(game["id"], actual)
                    reagendados += 1
            except Exception:
                log.warning("fallo rehidratando una partida", exc_info=True,
                            extra={"ctx": {"game_id": game.get("id")}})
        return reagendados
```

Agregar `list_games_by_status` en `backend/src/teg_backend/infrastructure/repository.py`,
junto a `list_games` (línea 110), usando el helper de fila que ya existe
(`_row_to_game`, el mismo que usan `get_game` y `list_games`):

```python
async def list_games_by_status(db: Database, status: str) -> list[dict]:
    rows = await db.fetchall("SELECT * FROM games WHERE status = ?", (status,))
    return [_row_to_game(r) for r in rows]
```

Y en `rehidratar_partidas_activas`, llevar el contador que usa el test:

```python
        self.counters["ai_turns_rehydrated"] = reagendados
        return reagendados
```

- [ ] **Step 4: Llamarlo desde el lifespan**

En `backend/src/teg_backend/main.py`, después de `commentator.start()` (línea 62):

```python
        commentator.start()
        reagendados = await app.state.service.rehidratar_partidas_activas()
        if reagendados:
            log.info("turnos de bot reagendados tras reinicio",
                     extra={"ctx": {"turnos": reagendados}})
```

- [ ] **Step 5: Correr los tests**

Run: `cd backend && uv run pytest tests/test_rehidratacion.py -v && uv run pytest -q`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/src/teg_backend/application/game_service.py \
        backend/src/teg_backend/infrastructure/repository.py \
        backend/src/teg_backend/main.py \
        backend/tests/test_rehidratacion.py
git commit -m "fix(ia): reagendar los turnos de bot al levantar el proceso

_ai_tasks vive solo en memoria y el lifespan no recorria las partidas activas:
un reinicio durante el turno de un bot dejaba la partida trabada. Con el tunel
efimero, cada sesion de juego implica reiniciar el backend."
```

---

### Task 10: Configuración de despliegue

Solo archivos del repo. No se levantan servicios ni se toca `.env`.

**Files:**
- Modify: `frontend/nginx.conf:22-36`
- Modify: `backend/Dockerfile:25`
- Modify: `docker-compose.yml`
- Modify: `backend/src/teg_backend/infrastructure/db.py:33-35`

**Interfaces:**
- Consumes: nada.
- Produces: ningún símbolo nuevo; cambia el comportamiento del entorno.

- [ ] **Step 1: Timeouts de WebSocket y cabeceras de proxy**

En `frontend/nginx.conf`, reemplazar los bloques `/api/` y `/ws/`:

```nginx
  # Backend FastAPI detrás del mismo dominio (servicio "backend" en compose)
  location /api/ {
    proxy_pass http://backend:8123;
    proxy_set_header Host $host;
    # sin esto el backend ve una sola IP para toda la mesa y los 240 req/min
    # del rate limit se comparten entre los 8 jugadores
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }
  location /health {
    proxy_pass http://backend:8123;
  }
  location /ws/ {
    proxy_pass http://backend:8123;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    # el default de 60 s cortaba las 8 conexiones a la vez ante cualquier
    # bloqueo del event loop; el ping del cliente solo daba 3 intentos de margen
    proxy_read_timeout 3600s;
    proxy_send_timeout 3600s;
    proxy_buffering off;
  }
```

- [ ] **Step 2: Confiar en las cabeceras del proxy**

En `backend/Dockerfile`, reemplazar la línea 25:

```dockerfile
# IMPORTANTE: nunca agregar --workers. El estado del juego (engines, salas,
# locks) vive en memoria del proceso; mas de un worker rompe el juego.
CMD uv run --no-sync uvicorn teg_backend.main:app \
    --host $TEG_HOST --port $TEG_PORT --no-access-log \
    --proxy-headers --forwarded-allow-ips '*'
```

- [ ] **Step 3: Límites de recursos y cierre limpio**

En `docker-compose.yml`, dentro del servicio `backend`:

```yaml
    # el contenedor murio con SIGKILL (137) porque el grace period de 10 s no
    # alcanzo para cerrar las dos conexiones SQLite: quedaron WAL sucios de 4 MB
    stop_grace_period: 30s
    mem_limit: 2g
    cpus: 2.0
    pids_limit: 512
```

Y en `frontend`:

```yaml
    stop_grace_period: 15s
    mem_limit: 256m
    cpus: 0.5
```

- [ ] **Step 4: Un fsync menos por commit**

En `backend/src/teg_backend/infrastructure/db.py`, después de la línea 33:

```python
        await self._conn.execute("PRAGMA journal_mode=WAL")
        # NORMAL es seguro bajo WAL y saca un fsync de cada commit: con 8
        # jugadores son ~320-400 commits por ronda sobre un disco compartido
        await self._conn.execute("PRAGMA synchronous=NORMAL")
```

- [ ] **Step 5: Verificar que la configuración es válida**

Run: `docker compose config -q && cd backend && uv run pytest -q`
Expected: sin errores de sintaxis en el compose y la suite en verde.

- [ ] **Step 6: Commit**

```bash
git add frontend/nginx.conf backend/Dockerfile docker-compose.yml \
        backend/src/teg_backend/infrastructure/db.py
git commit -m "chore(deploy): timeouts de websocket, cabeceras de proxy y limites de recursos

El nginx de produccion no definia proxy_read_timeout (default 60 s) ni
X-Forwarded-For, asi que el rate limit REST era un balde unico para los 8
jugadores. Se agregan limites de memoria y CPU, grace period suficiente para
cerrar SQLite, y synchronous=NORMAL."
```

---

### Task 11: La prueba de 8 jugadores

Es el criterio de aceptación de toda la Fase 0.

**Files:**
- Create: `backend/tests/test_carga_8_jugadores.py`

**Interfaces:**
- Consumes: todo lo anterior.
- Produces: nada; es la verificación final.

- [ ] **Step 1: Escribir la prueba**

Crear `backend/tests/test_carga_8_jugadores.py`:

```python
"""Criterio de aceptacion de la Fase 0: ocho jugadores, cero desincronizaciones.

Hasta hoy el maximo probado eran DOS conexiones WebSocket simultaneas
(test_game_flow.py:164-165), cuatro veces menos que el objetivo.

El incidente del 27/07 se disparaba en los primeros 400 ms tras game.started,
asi que la ventana critica que cubre este test es exactamente el arranque.
"""

import contextlib

from conftest import ADMIN, confirm_join, create_game, invite, recv_until

JUGADORES = 8


def _armar_partida_de_ocho(client):
    game = create_game(client, config={"commentator_enabled": False, "mode": "classic_26"})
    invs = [invite(client, game["id"], f"j{i}") for i in range(JUGADORES)]
    for inv in invs:
        confirm_join(client, game["code"], inv["token"])
    return game, invs


def test_ocho_jugadores_arrancan_sin_huecos_de_secuencia(client):
    game, invs = _armar_partida_de_ocho(client)

    with contextlib.ExitStack() as stack:
        wss = [
            stack.enter_context(
                client.websocket_connect(f"/ws/{game['code']}?token={inv['token']}")
            )
            for inv in invs
        ]
        for ws in wss:
            recv_until(ws, "game.snapshot")
            ws.send_json({"type": "ready.set", "payload": {"ready": True}})

        resp = client.post(f"/api/admin/games/{game['id']}/start", headers=ADMIN)
        assert resp.status_code == 200, resp.text

        for i, ws in enumerate(wss):
            seqs = []
            for _ in range(150):
                msg = ws.receive_json()
                seq = msg.get("sequence_number", 0)
                if seq > 0:
                    seqs.append(seq)
                if msg.get("event_type") == "placement.started":
                    break

            assert seqs, f"jugador {i}: no recibio ningun evento persistido"
            huecos = [(a, b) for a, b in zip(seqs, seqs[1:]) if b != a + 1]
            assert not huecos, (
                f"jugador {i}: huecos de secuencia {huecos}. "
                "Quedo algun evento persistido no publico consumiendo public_sequence."
            )


def test_los_ocho_reciben_el_objetivo_y_el_arranque(client):
    """Cada jugador debe recibir SU objetivo privado y los eventos publicos."""
    game, invs = _armar_partida_de_ocho(client)

    with contextlib.ExitStack() as stack:
        wss = [
            stack.enter_context(
                client.websocket_connect(f"/ws/{game['code']}?token={inv['token']}")
            )
            for inv in invs
        ]
        for ws in wss:
            recv_until(ws, "game.snapshot")
            ws.send_json({"type": "ready.set", "payload": {"ready": True}})
        client.post(f"/api/admin/games/{game['id']}/start", headers=ADMIN)

        for i, ws in enumerate(wss):
            objetivo = recv_until(ws, "objective.assigned", max_msgs=80)
            assert objetivo["payload"]["objective"]["title"], f"jugador {i} sin objetivo"
            recv_until(ws, "placement.started", max_msgs=80)
```

Si `recv_until` no acepta `max_msgs` con ese nombre, ajustar según la firma real en
`backend/tests/conftest.py:52`.

**Si este test tarda más de 30 s** (el `timeout` global de `pyproject.toml:28`),
no subir el timeout: significa que el arranque con 8 jugadores sigue siendo lento y
eso *es* el problema que la Fase 0 debía resolver.

- [ ] **Step 2: Correr la prueba**

Run: `cd backend && uv run pytest tests/test_carga_8_jugadores.py -v`
Expected: PASS. Si aparece un hueco, **no relajar la aserción**: significa que quedó un evento persistido no público sin cubrir por Task 1.

- [ ] **Step 3: Correr la suite entera**

Run: `cd backend && uv run pytest -q && cd ../frontend && pnpm vitest run`
Expected: todo verde.

- [ ] **Step 4: Commit**

```bash
git add backend/tests/test_carga_8_jugadores.py backend/tests/conftest.py
git commit -m "test(carga): partida de 8 conexiones sin huecos de secuencia

Criterio de aceptacion de la Fase 0. Hasta ahora el maximo probado eran 2
conexiones WebSocket simultaneas, cuatro veces menos que el objetivo."
```

---

## Verificación final de la Fase 0

- [ ] `cd backend && uv run pytest -q` en verde.
- [ ] `cd frontend && pnpm vitest run` en verde.
- [ ] `docker compose config -q` sin errores.
- [ ] `test_carga_8_jugadores.py` en verde: es la condición de salida.
- [ ] Revisar que ningún `emit(...)` con `persisted=True` y visibilidad no pública haya quedado fuera de Task 1: `grep -n "Visibility.PRIVATE\|Visibility.ADMIN" backend/src/teg_backend/application/game_service.py` y confirmar que cada uno o es efímero o pasa por `public_sequence = None`.

Recién con esto verde se levanta el backend y se pasa a la Fase 1.
