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

SPA en **Vite + React 19 + TypeScript** (Zustand, Tailwind v4, zod, WebSocket nativo). El frontend no calcula reglas: consume snapshots y eventos con `seq` del backend, reconecta con backoff y resincroniza pidiendo snapshot.

```bash
pnpm install
pnpm dev          # server-mock (:8790) + frontend (:5173) en paralelo
pnpm test         # unit (Vitest)
pnpm e2e          # vertical slice E2E (Playwright, 2 contextos de navegador)
pnpm build        # frontend/dist estáticos
```

```
frontend/           SPA (pages, components, services, state, config)
server-mock/        backend mock (express+ws) usado por dev y E2E
shared/contracts/   src/ = schemas zod TS (frontend + mock); api|websocket|schemas = docs del backend real
e2e/                Playwright: slice completo con dos navegadores
```

Convenciones: componentes `PascalCase.tsx`; assets `kebab-case` numerados; IDs lógicos dot-notation resueltos solo vía `AssetRegistry` + `frontend/public/assets/manifests/assets-manifest.json`; textos del soundboard en `frontend/src/config/soundboard.config.ts`. Deploy: `frontend/Dockerfile` (nginx sirve estáticos y proxya `/api` y `/ws`).

**Pendiente**: apuntar el frontend al backend FastAPI real (puerto 8123) — hoy los paths difieren del mock (`/api/admin/games` + `X-Admin-Token` global vs `/api/games` + token de admin por partida). Ver "Próximos pasos" en `docs/superpowers/specs/2026-07-22-teg-lopda-frontend-design.md`.

## Documentación

- `docs/architecture/overview.md` — arquitectura y decisiones
- `shared/contracts/api/rest-api.md` — contrato REST
- `shared/contracts/websocket/events.md` — catálogo de eventos con ejemplos
- `docs/deployment/deployment.md` — operación y exposición a Internet
- `docs/superpowers/specs/2026-07-22-teg-lopda-frontend-design.md` — diseño del frontend
