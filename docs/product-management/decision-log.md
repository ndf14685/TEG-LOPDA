# Decision Log

## Decision 2026-07-25-01

## Decisión

Congelar implementacion productiva nueva de Backend y Frontend hasta cerrar contratos y criterios de Vertical 1.

## Problema

El repositorio compila y pasa tests, pero existe brecha entre lo declarado como terminado y lo demostrado en flujos reales.

## Evidencia

`pnpm e2e` solo valida crear/invitar/lobby/colocacion/dados de practica; no valida ataque completo, conquista, Tribuna, ledger, reconexion en combate ni resoluciones objetivo.

## Opciones consideradas

Continuar implementando features; rehacer todo; congelar solo implementacion nueva y permitir auditoria/diseño/contratos.

## Decisión elegida

Congelar implementacion nueva y habilitar solo diseno/contratos/pruebas de Vertical 1.

## Motivo

Reduce consumo de cuota y evita seguir agregando codigo sin validar experiencia.

## Impacto

Backend y Frontend quedan bloqueados para features nuevas; Designer recibe el primer brief.

## Riesgos

Puede sentirse mas lento a corto plazo, pero evita retrabajo caro.

## Criterio de revisión

Se reconsidera cuando Vertical 1 tenga diseno aceptado, contrato sincronizado y E2E multi-cliente definido.

## Decision 2026-07-25-02

## Decisión

`shared/contracts/src/*.ts` es la fuente tecnica efectiva actual; los JSON/MD de contratos quedan como desactualizados hasta conciliacion.

## Problema

El JSON `client-messages.schema.json` no representa mensajes que usa frontend/backend.

## Evidencia

`shared/contracts/src/ws-events.ts` incluye `placement.place`, `turn.place_reinforcement`, `turn.fortify`, `turn.next_phase`, `turn.wager`, `cards.trade` y pactos; el JSON solo enumera `ping`, `ready.set`, `chat.send`, `dice.roll`, `attack`, `turn.end`.

## Opciones consideradas

Usar JSON como fuente; usar TS como fuente; detener hasta generar ambos.

## Decisión elegida

Usar TS como fuente efectiva para auditoria y bloquear nuevas features hasta regenerar/alinear JSON y docs.

## Motivo

El frontend compila contra TS y el backend ya acepta esos mensajes.

## Impacto

Backend/Frontend deben sincronizar contratos antes de nueva implementacion.

## Riesgos

Herramientas externas que lean JSON recibiran contrato falso.

## Criterio de revisión

JSON, MD y TS deben coincidir en mensajes, payloads y eventos.

## Decision 2026-07-25-03

## Decisión

La apuesta de refuerzos actual no cuenta como Tribuna ni sistema de Monedas LOPDA.

## Problema

El producto requiere espectadores/espera activa con mercado, monedas, ledger y resolucion autoritativa.

## Evidencia

`GameEngine.set_wager()` descuenta refuerzos del jugador activo en memoria/state_json; no hay tabla `player_lopda_ledger` ni eventos `bet.market.*`.

## Opciones consideradas

Renombrar la feature actual como Tribuna; eliminarla; conservarla como mecanica experimental bloqueada fuera de P0/P1.

## Decisión elegida

Conservarla como mecanica experimental no aprobada para release; no usarla para declarar Vertical 3.

## Motivo

No satisface integridad transaccional ni experiencia de espera.

## Impacto

Backend necesita diseño/contrato nuevo para Vertical 3; Frontend no debe ampliar esta UI como si fuera Tribuna.

## Riesgos

Puede confundir al usuario y al equipo si sigue visible sin contexto.

## Criterio de revisión

Solo se aprueba Tribuna cuando existan ledger, mercado, tickets, bloqueo y pruebas de doble pago/reembolso.
