# Frontend Current Brief - Claude

Fecha: 2026-07-25

## Estado

Habilitado en fast-track para implementar UI jugable privada.

## Objetivo

Convertir la UI productiva en una version final jugable basada en `frontend/public/prototype/index.html`, priorizando claridad de turno, mapa protagonista, combate explicativo y Tribuna util.

## Alcance inmediato

- Rehacer pantalla de juego hacia el layout del prototipo.
- Mantener integracion con backend real donde exista contrato.
- Turno/refuerzos/ataque deben usar estado autoritativo actual.
- Combate debe mostrar desglose claro con los datos disponibles de `attack.resolved`.
- Tribuna puede iniciar como UI funcional/fallback si el ledger backend real aun no existe, pero debe rotularse como monedas virtuales de partida y no dinero real.
- Reemplazar iconos/emoji que rendericen como cuadros por texto o iconografia controlada.
- Usar assets existentes; si falta algo, usar fallback CSS.

## Guardrails P0

- No mover reglas criticas al cliente si el backend ya las valida.
- No generar dados en cliente para resultados reales.
- No resolver apuestas reales de forma definitiva si despues habra ledger backend.
- No romper reconexion ni bloqueo de acciones al desincronizar.
- No introducir dinero real ni pagos.

## Verificacion minima antes de entregar

- `pnpm test`
- `pnpm typecheck`
- `pnpm build`
- `pnpm e2e`
- Capturas manuales o automatizadas de 1366x768 y 1920x1080.

## Condicion de parada

Detener y pedir backend solo si falta dato autoritativo indispensable para turno, fase, accion legal, combate o persistencia.
