# Arquitectura — TEG LOPDA backend

## Decisión de stack

**Python 3.12 + FastAPI + SQLite (aiosqlite) + uv.** Motivos:

- El servidor ya tiene Python 3.12 y `uv`: se puede correr con Docker o directo
  con systemd sin instalar nada más.
- FastAPI: WebSocket nativo, validación Pydantic (reutilizada en contratos),
  documentación automática en dev.
- SQLite: cero operación para 10–20 jugadores; WAL activado; backups triviales.
- Migraciones: runner SQL propio (`backend/migrations/*.sql`, tabla
  `schema_migrations`). Sin Alembic: menos piezas para el mismo resultado.

## Capas

```
api/          REST (admin con X-Admin-Token, join público por token)
realtime/     WebSocket /ws/{code}?token=... + ConnectionManager (salas)
application/  GameService: ÚNICO punto que muta estado; emite eventos
domain/       enums, envelope de eventos, GameEngine (dados/combate/turnos), mapa (TODO)
infrastructure/  SQLite + repositorio + migraciones
ai/           AICommentatorProvider (mock/ollama) + AIPlayerProvider (dummy/random)
security/     tokens hasheados, rate limiting, sanitización
```

## Principios

1. **Servidor autoritativo.** Dados (`secrets.SystemRandom`), combate, turnos y
   estados viven solo en el backend. El cliente pide acciones (`dice.roll`,
   `attack`, `turn.end`) y el servidor responde con eventos.
2. **Motor de eventos.** Toda mutación produce un `GameEvent` con envelope
   estable (ver `shared/contracts/websocket/`). Los persistidos llevan
   `sequence_number` monotónico por partida y quedan en la tabla `events`
   (historial + reconstrucción). Los efímeros (`game.snapshot`,
   `presence.changed`, `error`) llevan `persisted: false`.
3. **Visibilidad.** `public` → toda la sala; `private` → actor, target y admins;
   `admin` → solo admins. El routing lo hace `ConnectionManager`.
4. **IA desacoplada.** El comentarista recibe un contexto estructurado y corre
   en un worker con cola acotada, cooldown y timeout: si falla o tarda, el juego
   sigue. El jugador IA solo *propone* jugadas; el motor las valida y ante
   cualquier problema aplica el fallback (terminar turno).
5. **Estado en memoria + snapshot.** `GameEngine` vive en memoria; el estado de
   turnos se serializa a `games.state_json` en cada cambio, así un reinicio del
   proceso no pierde la partida (los clientes reconectan con el mismo token).

## Flujo de acceso

```
admin ── POST /api/admin/games ───────────► partida (code corto)
admin ── POST .../players ────────────────► token en claro (única vez) + join_url
jugador ─ GET  /api/join/{code}/{token} ──► ve invitación, puede editar apodo
jugador ─ POST /api/join/{code}/{token} ──► confirmado (player.joined)
jugador ─ WS   /ws/{code}?token=... ──────► snapshot + eventos en vivo
```

Tokens: `secrets.token_urlsafe(24)`, guardados como SHA-256, revocables y
regenerables por el admin. Respuestas de join genéricas (404) para no filtrar
si el código o el token existen.

## Extensión a reglas TEG completas

Los puntos de extensión están marcados `TODO(teg-rules)` y `TODO(teg-map)` en
`domain/engine.py` y `domain/map.py`: mapa oficial, refuerzos, conquista,
reagrupamiento, canje, objetivos, alianzas, eliminación y victoria automática.
El envelope de eventos ya contempla `territory.conquered` y
`player.eliminated`, así el frontend no cambia cuando se implementen.
