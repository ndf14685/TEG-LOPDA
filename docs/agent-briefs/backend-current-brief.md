# Backend Current Brief - Claude

Fecha: 2026-07-25

## Estado

No habilitado para implementar features nuevas.

## Condiciones para habilitacion

- Contratos TS/JSON/MD conciliados para Vertical 1.
- Criterios de aceptacion de Vertical 1 cerrados.
- Lista de eventos y payloads requeridos por Frontend aprobada.
- Plan de diff previo, con archivos afectados y pruebas a ejecutar.

## Trabajo permitido ahora

- Diagnostico puntual de contratos.
- Propuesta de sincronizacion de `shared/contracts/websocket/client-messages.schema.json` con `shared/contracts/src/ws-events.ts`.
- No tocar logica productiva sin aprobacion de producto.

## Tests obligatorios al habilitar

- `uv run pytest -q`
- Tests especificos de snapshot/reconexion/acciones legales.
- E2E de Vertical 1 una vez Frontend este listo.

## Riesgos a proteger

- Servidor autoritativo.
- No dados ni reglas en cliente.
- Persistencia de estado y eventos.
- No ledger de monedas en memoria cuando se aborde Vertical 3.
