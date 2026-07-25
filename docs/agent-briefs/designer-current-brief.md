# Designer Current Brief - Agy

Fecha: 2026-07-25

## Objetivo

Mapa Modo 50 aprobado para integracion y playtest privado. No continuar iterando el mapa salvo defectos nuevos de playtest o pedido explicito de Producto.

## Estado

La integracion piloto de America del Sur fue aprobada en partida real. El mapamundi completo Modo 50 corregido en `0afff3e` queda aprobado tecnicamente y tacticamente para avanzar. El diagnostico ya no muestra overlays capturando clicks: centro y borde de Alaska llegan a `path.territory-hitbox [territory-north-america-alaska]` y `badge_pointer_events` es `none`.

## Evidencia

- `test-results/world-50-labels-badges-1920x1080.png`
- `test-results/world-50-no-labels-1920x1080.png`
- `test-results/world-50-1366x768.png`
- `test-results/world-50-attackable.png`
- `assets/maps/base/map-base-tactical-50-001.svg`
- `frontend/src/components/map/MapPanel.tsx`
- `e2e/south-america-pilot.spec.ts`
- Resultado `pnpm e2e` 2026-07-25 posterior a `0afff3e`: 4/4 verde.
- Diagnostico `diagnostic-global-svg.spec.ts`: centro y borde reciben `path.territory-hitbox` del territorio correcto; `badge_pointer_events` es `none`.
- Integracion Frontend `b5284b4`: sanea en runtime badges demo, clases demo `p-*` y `viewBox` recortado para que el deploy use solo propiedad/tropas reales del juego.

## Cambio solicitado

No producir mas variantes del Modo 50 en esta etapa. Mantener disponibles `map-base-tactical-50-001.svg`, `world-50-pilot.html`, `map-world-50-manifest.json` y `map-world-50-p0.md` como handoff vigente.

## Arquitectura visual obligatoria

La direccion aprobada debe poder producirse en cuatro capas:

1. Base geografica no interactiva: costas, continentes, textura y atmosfera.
2. Territorios jugables: SVG independiente, un path por territorio, IDs normalizados y coloreables sin tapar la textura.
3. Hitboxes: areas invisibles independientes para hover, click, seleccion y drag.
4. Overlays: nombres, tropas, estandartes, flechas, pings, animaciones e indicadores.

## Entregables aceptados

- SVG Modo 50 corregido y probado en partida real.
- 50 territorios visibles con IDs conservados.
- 50 hitboxes con atributo `data-territory`.
- Documento `map-world-50-p0.md` sin `data-territory-id`.
- Overlays horneados transparentes a mouse (`pointer-events: none`).
- Manifest actualizado con el atributo real de hitbox.
- Capturas y e2e regenerados.

## Criterios de aceptacion cumplidos

- `pnpm test && pnpm typecheck && pnpm build && pnpm e2e` verde.
- Cada hitbox es detectable por selector `path.territory-hitbox[data-territory="<territory-id>"]`.
- En partida real, el click sobre hitbox/territorio propio abre menu radial.
- Diagnostico no reporta `circle.badge-circle` como receptor del centro de un territorio.
- Los seis colores de jugador preservan lectura general del mapamundi.
- Seleccion y objetivo atacable se distinguen sin tapar el mapa.
- 1366x768 sigue siendo jugable para desktop.
- No incluye textos/HUD genericos de RTS ajenos a TEG-LOPDA.

## Limites

No definir nombres de componentes React, arquitectura frontend, persistencia backend ni contratos tecnicos no acordados. Los eventos y tablas de ledger pueden mencionarse como necesidades de producto, pero no como implementacion cerrada.

Modo 26 queda fuera de alcance y conserva arte anterior hasta nuevo brief. Ajustes finos de labels en Europa/Oriente Medio/Oceania quedan como polish P2, no como bloqueo P0.

## Deuda no bloqueante de Arte

En una proxima pasada, el export ideal deberia venir sin badges demo horneados, sin clases demo `p-*` y con `viewBox` que contenga toda la geometria. Hoy Frontend lo sanea de forma segura en carga para acelerar el playtest privado; no se pide nueva entrega de Arte por esto.
