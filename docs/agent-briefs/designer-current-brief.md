# Designer Current Brief - Agy

Fecha: 2026-07-25

## Objetivo

Cerrar las ultimas correcciones de handoff visual para que turno, combate y Tribuna puedan pasar a planificacion tecnica sin ambiguedades.

## Problema

La segunda entrega ya valida mapa real, estados navegables y resoluciones 1366x768/1920x1080. Quedan problemas puntuales: el manifest JSON todavia referencia un icono inexistente, algunos emoji se renderizan como cuadros y el estado de reconexion no cambia el panel persistente.

## Evidencia

- `frontend/public/prototype/index.html`
- `test-results/prototype-1366x768-turn.png`
- `test-results/prototype-1366x768-combat.png`
- `test-results/prototype-1920x1080-turn.png`
- `test-results/prototype-1920x1080-combat.png`
- `assets/manifests/missing-assets.md`
- `assets/manifests/assets-manifest.json`

## Cambio solicitado

Entregar una correccion acotada con:

- Eliminar o reemplazar en `assets/manifests/assets-manifest.json` la referencia a `assets/ui/icons/icon-betting-lopda-coin-001.svg`.
- Reemplazar emoji criticos del prototipo por texto/iconografia CSS/SVG controlada cuando hoy se rendericen como cuadros.
- Hacer que el estado `sync-state` cambie el panel persistente de turno/reconexion, no solo el toast.
- Exportar captura de Tribuna en estados aceptada, rechazada, bloqueada, pago y reembolso en 1366x768.

## Criterios de aceptacion

- Ningun manifest oficial referencia un archivo inexistente como disponible.
- Reconexión es visible como estado persistente, no solo como notificacion temporal.
- No hay cuadros de glifo en elementos criticos.
- La Tribuna explica saldo, mercado, timer, ticket, rechazo, bloqueo, pago y reembolso.

## Limites

No definir nombres de componentes React, arquitectura frontend, persistencia backend ni contratos tecnicos no acordados. Los eventos y tablas de ledger pueden mencionarse como necesidades de producto, pero no como implementacion cerrada.
