# Designer Current Brief - Agy

Fecha: 2026-07-25

## Estado

Asset cartografico V3 aprobado como capa base para integracion Frontend. No producir nuevas variantes salvo pedido puntual despues de revisar capturas integradas del producto real.

## Problema

El producto muestra territorios/blobs sobre fondo azul con grilla, rutas y una brujula. No hay costas continuas, masas continentales reconocibles ni lectura inmediata de mapamundi cuando se ocultan labels.

## Evidencia

- Captura integrada `test-results/sa-pilot-1920x1080.png`: los territorios siguen dominando la lectura visual.
- `assets/maps/base/map-world-geographic-base-50-001.svg`: existe, pero contiene paths continentales simplificados tipo blob (`continent-group-*`), no costas cartograficas.
- `assets/maps/base/map-world-geographic-base-50-002.svg`: rechazado. Sus seis `path.continent-mass` son identicos a V1; solo agrega `continent-shelf`/glow y mantiene la silueta blob.
- `test-results/geo-base-002-overlay-32pct-1920x1080.png`: no valida "sin labels"; la captura muestra nombres de territorios.
- `assets/maps/base/map-world-geographic-base-50-003.svg`: aprobado como asset base. Capturas `test-results/geo-base-003-pure-1920x1080.png` y `test-results/geo-base-003-pure-1366x768.png` se leen como mapamundi sin labels; overlay `test-results/geo-base-003-overlay-32pct-1920x1080.png` mantiene costas visibles con seis colores.
- Tester Windows sobre bundle `DlvZXums`: 50 territorios e hitboxes correctas, pero no se ve mapamundi real.
- `docs/product-management/decision-log.md`, Decision 2026-07-25-17, Decision 2026-07-25-18 y Decision 2026-07-25-19.

## Cambio solicitado

Quedar en espera. La proxima accion corresponde a Frontend: integrar V3 en producto real y generar capturas. Arte solo ajusta si esas capturas muestran desalineacion o una silueta puntual confusa.

## Asset aprobado

- `assets/maps/base/map-world-geographic-base-50-003.svg`
- `design/tools/gen-map-geo-base-v3.py`
- `docs/design/map-geo-base-v3-changelog.md`

## Criterios de aceptacion visual

- Una persona reconoce el mapamundi en menos de un segundo sin leer labels.
- Hay costas continuas y siluetas continentales, no manchas aisladas.
- Europa y Asia se leen como regiones continentales conectadas, no como piezas sueltas.
- America del Sur mantiene silueta continental completa aunque los territorios encima esten coloreados.
- Los elementos decorativos (rutas, brujula, reticula) no reemplazan ni tapan la geografia.

## Limites

No definir componentes React, logica de hitboxes, reglas de juego, backend ni nombres de eventos. No retocar los territorios jugables actuales como solucion principal: el bloqueo es ausencia/calidad de la capa geografica base.
