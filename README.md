# TEG LOPDA

Juego web privado inspirado en el TEG, para jugar entre amigos desde el
navegador. Backend autoritativo en FastAPI + WebSocket + SQLite.

## Estado

MVP funcional: salas con links personalizados por jugador, lobby en tiempo
real, ready/turnos/dados/ataques autoritativos, chat público y privado,
comentarista IA (mock determinista, adaptador Ollama opcional), jugador IA
básico, taunts de audio configurables, reconexión sin perder sesión.

Las reglas completas del TEG (mapa, refuerzos, objetivos…) tienen puntos de
extensión marcados `TODO(teg-rules)` — ver `docs/architecture/overview.md`.

## Arranque rápido (desarrollo)

```bash
cd backend
uv sync
TEG_ADMIN_TOKEN=dev-admin uv run uvicorn teg_backend.main:app --port 8123
```

- Salud: http://127.0.0.1:8123/health
- Docs API (solo dev): http://127.0.0.1:8123/docs
- Página de prueba del lobby: http://127.0.0.1:8123/dev

Crear una partida y dos jugadores:

```bash
curl -s -X POST http://127.0.0.1:8123/api/admin/games \
  -H 'X-Admin-Token: dev-admin' -H 'Content-Type: application/json' \
  -d '{"name": "la-revancha"}'
# con el "id" devuelto:
curl -s -X POST http://127.0.0.1:8123/api/admin/games/<ID>/players \
  -H 'X-Admin-Token: dev-admin' -H 'Content-Type: application/json' \
  -d '{"nickname": "Nessi"}'
```

Cada respuesta trae `join_url`: pegarla en `/dev` desde dos navegadores para
ver el lobby sincronizado.

## Tests

```bash
cd backend && uv run pytest
```

## Producción

```bash
./deploy/scripts/install.sh   # Docker Compose + healthcheck
```

Despliegue, DNS, HTTPS y plan de exposición: `docs/deployment/deployment.md`.

## Estructura

```
backend/            FastAPI (src/teg_backend: api, application, domain,
                    infrastructure, realtime, ai, security) + tests + migrations
shared/contracts/   contratos REST/WS/IA/assets compartidos con el frontend
deploy/             caddy, nginx, systemd, scripts (install/update/backup/rollback)
docs/               arquitectura, api, despliegue
assets/manifest/    manifiesto de assets (ejemplo)
```

## Frontend

SPA en **Vite + React 19 + TypeScript** (Zustand, Tailwind v4, zod, WebSocket nativo), integrada al backend FastAPI real y a los assets de Dirección de Arte. No calcula reglas: consume `game.snapshot` + eventos con `sequence_number`, reconecta con backoff (reconectar = resincronizar: el server manda snapshot fresco) y bloquea acciones mientras no está sincronizada.

```bash
pnpm install
pnpm dev:backend   # FastAPI en :8123 (TEG_ADMIN_TOKEN=dev-admin por defecto)
pnpm dev           # Vite en :5173 con proxy /api, /health y /ws al :8123
pnpm test          # unit (Vitest)
pnpm e2e           # E2E Playwright contra backend real (puertos aislados 8124/5174, DB efímera)
pnpm build         # frontend/dist estáticos (bundles en /static, assets de Arte en /assets)
```

```
frontend/           SPA (pages, components, services, state, config)
shared/contracts/   src/ = schemas zod TS espejando api|websocket|schemas (docs del backend)
assets/             Dirección de Arte: manifiestos, mapas SVG, paleta, audio (frontend/public/assets → symlink)
e2e/                Playwright: slice completo con dos navegadores
```

Integración: `AssetRegistry` consume `assets/manifest/*.json` (mapas, audio, taunts) y `assets/brand/palette/palette.json` (pisa las CSS variables de colores de jugador); el mapa se inyecta como SVG dinámico desde `assets/maps/base/` según `assets/README-INTEGRATION.md`. El soundboard sale de `taunts-manifest.json` (fallback en `frontend/src/config/soundboard.config.ts`). Flujo de organizador: la clave `X-Admin-Token` crea la partida y links; el organizador juega auto-invitándose como `player` (el rol `admin` del backend no se sienta a la mesa). Deploy: `frontend/Dockerfile` (nginx proxya `/api`, `/health` y `/ws` a `backend:8123`).

## Documentación

- `docs/architecture/overview.md` — arquitectura y decisiones
- `shared/contracts/api/rest-api.md` — contrato REST
- `shared/contracts/websocket/events.md` — catálogo de eventos con ejemplos
- `docs/deployment/deployment.md` — operación y exposición a Internet
- `docs/superpowers/specs/2026-07-22-teg-lopda-frontend-design.md` — diseño del frontend
