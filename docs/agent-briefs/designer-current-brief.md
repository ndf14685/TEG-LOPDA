# Designer Current Brief - Agy

Fecha: 2026-07-25

## Objetivo

Corregir el mapamundi completo Modo 50 para que pueda pasar a integracion productiva.

## Problema

La integracion piloto de America del Sur fue aprobada en partida real. El mapamundi completo Modo 50 entregado despues corrigio el contrato estatico de hitboxes, pero sigue sin pasar e2e de partida real y mantiene solapes visuales.

## Evidencia

- `test-results/world-50-labels-badges-1920x1080.png`
- `test-results/world-50-no-labels-1920x1080.png`
- `test-results/world-50-1366x768.png`
- `test-results/world-50-attackable.png`
- `assets/maps/base/map-base-tactical-50-001.svg`
- `frontend/src/components/map/MapPanel.tsx`
- `e2e/south-america-pilot.spec.ts`
- Resultado `pnpm e2e` 2026-07-25: falla en `placeAllViaRadial`, esperando boton radial `+1`; el click sobre el territorio/hitbox no abre menu radial.

## Cambio solicitado

Corregir el entregable global Modo 50. No pedir integracion global hasta que estos puntos esten resueltos.

## Arquitectura visual obligatoria

La direccion aprobada debe poder producirse en cuatro capas:

1. Base geografica no interactiva: costas, continentes, textura y atmosfera.
2. Territorios jugables: SVG independiente, un path por territorio, IDs normalizados y coloreables sin tapar la textura.
3. Hitboxes: areas invisibles independientes para hover, click, seleccion y drag.
4. Overlays: nombres, tropas, estandartes, flechas, pings, animaciones e indicadores.

## Entregables de esta iteracion

- SVG Modo 50 corregido y probado en partida real.
- 50 territorios visibles con IDs conservados.
- 50 hitboxes con atributo `data-territory`.
- Documento `map-world-50-p0.md` corregido para no mencionar `data-territory-id`.
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

- `pnpm e2e` no debe fallar.
- Cada hitbox debe ser detectable por selector `path.territory-hitbox[data-territory="<territory-id>"]`.
- En partida real, click sobre hitbox/territorio propio durante colocacion y refuerzo debe abrir menu radial.
- Labels y tropas no se solapan en las regiones indicadas.
- Los seis colores de jugador preservan textura/geografia.
- Seleccion y objetivo atacable se distinguen sin tapar el mapa.
- 1366x768 sigue siendo legible.
- No incluye textos/HUD genericos de RTS ajenos a TEG-LOPDA como `GLOBAL DOMINATION`, recursos militares falsos o interfaces decorativas no funcionales.

## Limites

No definir nombres de componentes React, arquitectura frontend, persistencia backend ni contratos tecnicos no acordados. Los eventos y tablas de ledger pueden mencionarse como necesidades de producto, pero no como implementacion cerrada.

Frontend no debe integrar todavia el mapamundi completo. Despues de aprobar esta correccion, Frontend podra hacer una integracion global acotada.
