# Functional RC Status

Fecha: 2026-07-26

## Estado recuperado

- Rama actual: `frontend/canonical-50-integration`.
- Último commit local: `2762191 feat(map): actualizar integración canónica Modo 50 a map-world-canonical-50-003`.
- Cambios sin commitear al inicio: `artifacts/tester/` sin trackear.
- Backend local/desplegado: contenedor `teg-lopda-backend-1` activo y saludable en `127.0.0.1:8123`.
- Frontend local/desplegado: contenedor `teg-lopda-frontend-1` activo en `127.0.0.1:8130`.
- URL pública configurada: `https://paris-penalty-clan-sellers.trycloudflare.com`.
- Healthcheck público: `GET /health` responde `{"status":"ok","version":"0.1.0"}`.
- SHA desplegado antes de esta RC: no está embebido ni expuesto por la aplicación; la versión HTTP pública sólo reporta `0.1.0`.
- Documentación revisada sin auditoría completa: `docs/product-management/current-status.md`, `docs/product-management/release-plan.md`, `docs/reviews/playtest-review.md`, `docs/reviews/integration-review.md`, `docs/agent-briefs/tester-current-brief.md`.

## Tests ejecutados en recuperación

- Backend: `cd backend && uv run pytest -q` -> 84 passed, 1 warning.
- Frontend unit: `pnpm test` -> 33 passed.
- Typecheck contratos/frontend: `pnpm typecheck` -> passed.
- E2E local con backend real: `pnpm e2e` -> 4 passed.
- Build frontend: `pnpm build` -> passed.
- Smoke HTTP público: `/` responde 200 y `/health` responde 200.
- Smoke navegador público inicial: landing carga, muestra servidor operativo y permite crear una partida desde la URL pública.
- Smoke funcional público: passed sobre sala separada `functional-rc-001-public-verify-2` con 3 contextos aislados. Cobertura: API admin pública, links públicos, lobby, ready, inicio, colocación inicial, refuerzos, ataque, dados/arena de combate, detener ataque y recarga/reconexión.
- Smoke público de turno: passed sobre sala separada `functional-rc-001-turn-check`. Cobertura: pasar de ataque a reagrupamiento, terminar turno y ver al siguiente jugador en refuerzos.
- Deploy RC: `docker compose up -d --build backend frontend` ejecutado sin cambios de DNS, firewall, puertos públicos, reverse proxy ni seguridad.
- Post-deploy: contenedores `backend` y `frontend` activos; health local y público OK; HTML/JS/CSS/assets principales OK; WebSocket público OK luego de confirmar join; smoke navegador post-deploy sin errores críticos de consola ni requests fallidas.

## Blockers identificados para jugar

No hay blockers confirmados.

No se aplicaron cambios de backend/frontend en esta iteración porque las verificaciones no detectaron un bloqueo funcional que justifique tocar código.

## Problemas no bloqueantes conocidos

- Mapa geográfico desalineado o imperfecto.
- Polígonos y costas no finales.
- Layout QHD/4K con espacio desperdiciado.
- Estética incompleta.
- Animaciones no terminadas.
- Audio no terminado.
- Tribuna y apuestas avanzadas incompletas.
- Responsive no definitivo.
- La aplicación no expone commit SHA en `/health`; para esta RC la trazabilidad queda por Git tag/commit local.
- Warnings esperados de assets/manifiestos faltantes en tests frontend; los tests validan que no rompan el registro.

## Plan mínimo

1. No modificar reglas, mapa, UI visual ni arquitectura salvo blocker real.
2. Preparar RC desde `frontend/canonical-50-integration`.
3. Si no aparecen blockers funcionales, registrar commit/tag `functional-rc-001`.
4. Desplegar la misma fuente con Docker Compose en la URL pública existente.
5. Ejecutar verificaciones post-deploy: backend, frontend, healthcheck, WebSocket, links y al menos dos sesiones independientes.
6. Crear brief ejecutable para tester Windows en `docs/agent-briefs/tester-functional-rc-001.md`.

Estado del plan: completo para RC funcional. No continuar con mapa, animaciones, audio, Tribuna avanzada ni nuevas funcionalidades en esta iteración.
