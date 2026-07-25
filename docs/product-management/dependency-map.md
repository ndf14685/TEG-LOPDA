# Dependency Map

Fecha: 2026-07-25

## Vertical 1 - Identidad, lobby, turno y refuerzos

- Designer: mockups/prototipo de turno propio, turno ajeno, colocacion/refuerzos, error y reconexion.
- Backend: contrato sincronizado de snapshot, stage, turn, legal.actions, territory.updated y errores.
- Frontend: UI sobre mapa que consuma estado autoritativo sin inventar reglas.
- Tester: E2E multi-contexto con reconexion y 1366x768/1920x1080.

## Vertical 2 - Ataque, dados y conquista

- Designer: arena de combate completa y flujo de ataque/conquista.
- Backend: eventos deben incluir suficiente informacion para explicar tropas iniciales, dados permitidos, bajas y estado acumulado.
- Frontend: no puede construir explicaciones si el backend no provee datos auditables.
- Tester: debe validar reconstruccion de bajas y conquista en varios clientes.

## Vertical 3 - Tribuna y apuestas

- Designer: flujo Tribuna/mercado/ticket/pago/error.
- Backend: ledger SQLite transaccional, mercados, bloqueo, resolucion, reembolso, idempotencia.
- Frontend: solo consume saldo/tickets/mercados; no resuelve apuestas.
- Tester: doble pago, saldo insuficiente, reconexion y cierre de mercado.

## Bloqueos actuales

- Backend bloqueado para nuevas features por contrato JSON/TS/MD divergente.
- Frontend bloqueado para pantallas nuevas sin diseno aprobado y assets reales.
- Designer desbloqueado para entregar prototipo/manifest corregidos.
