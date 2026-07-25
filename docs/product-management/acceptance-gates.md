# Acceptance Gates

Fecha: 2026-07-25

## Gate global

Una tarea solo se acepta si pasa flujo real, contrato, pruebas, manejo de errores, reconexion cuando aplique, evidencia visual y revision de producto.

## Gate Vertical 1

- En 2 segundos se identifica jugador activo, fase y accion siguiente.
- Refuerzos se colocan sobre mapa, sin formularios principales.
- Todos los clientes ven el mismo estado.
- Reconectar devuelve snapshot consistente.
- 1366x768 y 1920x1080 no tienen textos rotos ni solapados.
- E2E cubre dos jugadores, reconexion y bloqueo de acciones para turno ajeno.

## Gate Vertical 2

- Ataque se elige sobre mapa.
- Backend explica cantidad de dados permitida y usada.
- UI muestra comparaciones, empates, bajas por par y tropas iniciales/finales.
- Conquista y movimiento post-conquista son reconstruibles.
- E2E cubre ataque hasta conquista y reconexion durante combate.

## Gate Vertical 3

- Monedas persistidas en SQLite con ledger transaccional.
- Mercado se abre, acepta/rechaza, bloquea, resuelve y reembolsa.
- No hay doble pago ni saldo negativo.
- Frontend no calcula resultados ni pagos.

## Gate de assets

- Manifest unico.
- Cada asset `ready` existe fisicamente.
- Cada faltante tiene fallback aprobado o queda fuera de la vertical.
