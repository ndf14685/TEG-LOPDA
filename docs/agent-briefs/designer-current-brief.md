# Designer Current Brief - Agy

Fecha: 2026-07-25

## Objetivo

Corregir el mapamundi completo Modo 50 para que pueda pasar a integracion Frontend.

## Problema

La integracion piloto de America del Sur fue aprobada en partida real. El mapamundi completo Modo 50 entregado despues no queda aprobado: tecnicamente rompe el contrato de hitboxes y visualmente presenta solapes fuertes en varias regiones.

## Evidencia

- `test-results/world-50-labels-badges-1920x1080.png`
- `test-results/world-50-no-labels-1920x1080.png`
- `test-results/world-50-1366x768.png`
- `test-results/world-50-attackable.png`
- `assets/maps/base/map-base-tactical-50-001.svg`
- `frontend/src/components/map/MapPanel.tsx`
- `e2e/south-america-pilot.spec.ts`

## Cambio solicitado

Corregir el entregable global Modo 50. No pedir a Frontend integracion hasta que estos puntos esten resueltos.

## Arquitectura visual obligatoria

La direccion aprobada debe poder producirse en cuatro capas:

1. Base geografica no interactiva: costas, continentes, textura y atmosfera.
2. Territorios jugables: SVG independiente, un path por territorio, IDs normalizados y coloreables sin tapar la textura.
3. Hitboxes: areas invisibles independientes para hover, click, seleccion y drag.
4. Overlays: nombres, tropas, estandartes, flechas, pings, animaciones e indicadores.

## Entregables de esta iteracion

- SVG Modo 50 corregido.
- 50 territorios visibles con IDs conservados.
- 50 hitboxes con atributo `data-territory`, no `data-territory-id`, o declaracion explicita acordada con Frontend antes de cambiar contrato. Por defecto usar `data-territory`.
- 50 labels y 50 badges reposicionados para no chocar a 1920x1080 ni 1366x768.
- Correccion especifica de solapes en:
  - Mexico / Colombia / Peru / Sudamerica norte.
  - Gran Bretana / Alemania / Polonia / Francia / Espana / Italia.
  - Turquia / Arabia / Egipto / Etiopia / Iran.
  - Gobi / Mongolia / China / Siberia / Aral.
  - Sumatra / Borneo / Java / Australia.
- Capturas regeneradas: labels/badges 1920, sin etiquetas 1920, seleccionado, atacable, ataque en ejecucion, 1366.
- Manifest actualizado con el atributo real de hitbox.

## Criterios de aceptacion

- `pnpm e2e` no debe fallar por hitboxes.
- Cada hitbox debe ser detectable por selector `path.territory-hitbox[data-territory="<territory-id>"]`.
- Labels y tropas no se solapan en las regiones indicadas.
- Los seis colores de jugador preservan textura/geografia.
- Seleccion y objetivo atacable se distinguen sin tapar el mapa.
- 1366x768 sigue siendo legible.
- No incluye textos/HUD genericos de RTS ajenos a TEG-LOPDA como `GLOBAL DOMINATION`, recursos militares falsos o interfaces decorativas no funcionales.

## Limites

No definir nombres de componentes React, arquitectura frontend, persistencia backend ni contratos tecnicos no acordados. Los eventos y tablas de ledger pueden mencionarse como necesidades de producto, pero no como implementacion cerrada.

Frontend no debe integrar todavia el mapamundi completo. Despues de aprobar esta correccion, Frontend podra hacer una integracion global acotada.
