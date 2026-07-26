# Playtest Mode Guide

Fecha: 2026-07-26

## Objetivo

Modo liviano para playtest real de TEG-LOPDA. Registra errores técnicos, reportes manuales, trail de acciones e incidentes deduplicados en `data/playtest.db`.

No cambia reglas, dados, mapa, balance ni contratos de juego existentes.

## Activar

Variables:

```bash
PLAYTEST_MODE=true
PLAYTEST_UNTIL=2026-07-28T23:59:59-03:00
PLAYTEST_BUILD=<commit-sha-o-tag>
PLAYTEST_RETENTION_DAYS=14
```

Luego:

```bash
docker compose up -d --build backend frontend
```

## Desactivar

```bash
PLAYTEST_MODE=false
docker compose up -d --build backend frontend
```

Cuando está inactivo, el botón visual y la captura frontend quedan desactivados.

## Panel

URL:

```text
https://paris-penalty-clan-sellers.trycloudflare.com/admin/playtest
```

Usa el mismo `TEG_ADMIN_TOKEN` del administrador.

Permite ver estado, sesiones, partidas, incidentes, ocurrencias, action trail, adjuntos, cambiar estado/severidad, agregar nota, exportar backlog y purgar datos antiguos bajo comando explícito.

## Reporte manual

Los jugadores ven `🐞 Reportar problema` sólo si el modo está activo.

El formulario pide categoría, descripción, resultado esperado, severidad percibida y captura opcional. Adjunta automáticamente build, URL, viewport, navegador, partida, jugador, turno, fase, activo, conexión, último combate, últimas 50 acciones y errores recientes.

## Captura automática

Frontend:

- `window.onerror`.
- `unhandledrejection`.
- React Error Boundary.
- Errores HTTP.
- 4xx/5xx relevantes.
- Fallos de contrato REST/WS.
- Errores y cierres WebSocket.
- Reconexiones.
- Saltos de `sequence_number`.
- Assets/manifiestos faltantes.
- Acciones pendientes sin resolución.
- Recargas durante acción activa.
- Eventos `error` del backend.

Backend:

- Excepciones no controladas y 5xx.
- Rechazos de acciones WebSocket.
- Errores WebSocket.
- Conexiones, reconexiones y desconexiones.

## Privacidad

No se guarda audio ni Discord.

Se enmascaran tokens, admin tokens, passwords/secrets y objetivos secretos. Las capturas opcionales se guardan fuera de rutas públicas predecibles en `data/playtest-attachments`.

## Exportar

Desde el panel: botón `Exportar backlog`.

Genera:

```text
docs/playtest/backlog.md
docs/playtest/session-summary.md
docs/playtest/incidents.json
docs/playtest/incidents.csv
```

## Purgar

Desde el panel: botón `Purgar antiguos`.

Por defecto conserva incidentes confirmados/en investigación/retest y no borra adjuntos salvo orden explícita en API.

No ejecutar purgas durante el playtest salvo decisión explícita.

## API mínima

Pública:

- `GET /api/playtest/status`
- `POST /api/playtest/sessions`
- `POST /api/playtest/actions`
- `POST /api/playtest/incidents`

Admin:

- `GET /api/admin/playtest`
- `GET /api/admin/playtest/incidents/{code}`
- `PATCH /api/admin/playtest/incidents/{code}`
- `POST /api/admin/playtest/export`
- `POST /api/admin/playtest/purge`

## Problemas conocidos

- No crea issues de GitHub automáticamente.
- La captura de pantalla es manual/opcional.
- El action trail guarda datos mínimos; no es replay completo.
- La detección de acciones pendientes usa heurística por falta de correlación request-response en el protocolo WS actual.
