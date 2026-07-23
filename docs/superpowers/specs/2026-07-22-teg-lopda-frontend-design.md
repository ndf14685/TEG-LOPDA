# TEG LOPDA — Diseño de frontend (vertical slice)

Fecha: 2026-07-22. Spec de origen: prompt del usuario (completa, tratada como diseño aprobado con instrucción explícita de avanzar).

## Decisión de stack

**Elegido: Vite + React 19 + TypeScript, Zustand, Tailwind CSS v4, zod, WebSocket nativo, Vitest + Playwright, pnpm workspaces.**

Alternativas consideradas:

1. **Next.js** — descartado: no hay SEO ni SSR (juego privado por link), y el App Router agrega complejidad sin beneficio para una SPA 100% dirigida por WebSocket.
2. **Vite SPA (elegido)** — build simple, HMR rápido, proxy dev para `/api` y `/ws`, deploy como estáticos detrás de cualquier CDN/reverse-proxy.
3. **Phaser/canvas** — descartado según spec: el mapa es UI estratégica SVG, no físicas.

Estado global: **Zustand** (liviano, sin boilerplate, selectores finos para no re-renderizar el mapa entero por cada evento). Estilos: **Tailwind v4** + tokens CSS para colores de jugador. Contratos: **zod** en `shared/contracts` como única fuente de tipos, consumida por frontend y por el mock server.

## Arquitectura

```
shared/contracts/   # zod schemas + tipos: API, eventos WS, game, player, assets, errores, IA, versión
frontend/           # SPA Vite React TS
server-mock/        # backend mock = fuente de verdad del slice (express + ws), consume los mismos contratos
e2e/                # Playwright, dos contextos de navegador
```

- **Protocolo WS**: sobre `{ v, seq, type, payload, ts }`. El cliente valida cada evento con zod, trackea `seq`, detecta huecos y pide snapshot (`sync.request` → `game.snapshot`). Reconexión con backoff exponencial + jitter, acciones bloqueadas mientras `syncState !== 'synced'`.
- **Tokens**: la URL lleva sólo un token opaco (`/join/:gameId/:token`). El perfil (nombre, apodo, color, avatar, audios, relaciones) vive en el servidor. El token se canjea por una sesión vía `POST /api/session`; la sesión se guarda en `sessionStorage` (no `localStorage`); con backend real se migrará a cookie HttpOnly.
- **AssetRegistry**: singleton que carga `assets/manifests/assets-manifest.json`, resuelve IDs dot-notation (`background.lobby.war-room.001`), valida faltantes, aplica fallback, precarga críticos y loguea errores sólo en dev.
- **Audio**: `AudioService` con desbloqueo en primer gesto del usuario, cola de reproducción (sin superposición de taunts), volúmenes por canal (master/música/sfx/taunts/IA) y cooldown de soundboard. Textos del soundboard vienen de configuración.
- **Mapa**: SVG data-driven (slice: 8 territorios, 2 continentes). Colores por CSS variables según owner; estados hover/selected/attack-source/attack-target por clases.

## Pantallas del slice

Landing → Admin (crear partida, crear jugadores, links copiar/revocar/regenerar) → Join (validar token, identidad, confirmar apodo, probar audio) → Lobby (conectados, listos, chat, countdown, inicio) → Tablero inicial (mapa SVG, paneles, comentarista IA con evento mock `ai.comment.typing`/`generated`).

## Errores

Códigos compartidos (`TOKEN_INVALID`, `TOKEN_REVOKED`, `TOKEN_EXPIRED`, `GAME_NOT_FOUND`, `NOT_ADMIN`, `VERSION_MISMATCH`, …). El join muestra mensajes claros por código. Eventos WS inválidos se descartan y se loguean en dev.

## Testing

- **Vitest**: contratos, AssetRegistry (fallback/faltantes), cola de audio y cooldown, detección de huecos de `seq`.
- **Playwright**: el vertical slice completo con dos `browser.newContext()` independientes (admin + jugador), verificando estado compartido y comentario IA visible en ambos.

## Etapas posteriores (fuera del slice)

Tablero completo (turnos/dados/ataques), negociaciones, audios personalizados reales, pantalla final, responsive/accesibilidad profunda, integración backend real. La estructura de carpetas ya deja el lugar de cada cosa.
