# Designer Current Brief - Agy

Fecha: 2026-07-25

## Objetivo

Mapa Modo 50 aprobado para playtest privado con base geografica continua integrada. No iterar mas formas ni base salvo defectos P0/P1 de tester.

## Estado

La entrega `25ea8c5` creo `map-world-geographic-base-50-001.svg` y Frontend la integro en `fc8e5d7`. La captura integrada de Modo 50 ya muestra masas continentales continuas debajo de los territorios, y `pnpm e2e` pasa 4/4. Modo 26 sigue fuera de alcance.

## Evidencia

- `test-results/world-50-labels-badges-1920x1080.png`
- `test-results/world-50-no-labels-1920x1080.png`
- `test-results/world-50-1366x768.png`
- `test-results/world-50-attackable.png`
- `assets/maps/base/map-base-tactical-50-001.svg`
- `assets/maps/base/map-world-geographic-base-50-001.svg`
- `frontend/public/prototype/geo-base-pilot.html`
- `test-results/geo-base-pure-1920x1080.png`
- `test-results/geo-base-overlay-1920x1080.png`
- `frontend/src/components/map/MapPanel.tsx`
- `e2e/south-america-pilot.spec.ts`
- `fc8e5d7 feat(map): base geográfica continua debajo de la capa jugable (Modo 50)`.
- Verificacion local posterior: `pnpm test`, `pnpm typecheck`, `pnpm build`, `pnpm e2e` verde.

## Cambio solicitado

No producir nuevas variantes. Esperar mini-regresion Windows. Solo intervenir si el tester demuestra que el mapa integrado no se reconoce, pierde clicks, tapa tropas/labels o rompe legibilidad a 1366x768.

## Arquitectura visual obligatoria

La direccion aprobada debe poder producirse en cuatro capas:

1. Base geografica no interactiva: costas, continentes, textura y atmosfera.
2. Territorios jugables: SVG independiente, un path por territorio, IDs normalizados y coloreables sin tapar la textura.
3. Hitboxes: areas invisibles independientes para hover, click, seleccion y drag.
4. Overlays: nombres, tropas, estandartes, flechas, pings, animaciones e indicadores.

## Entregables aceptados como insumo

- `assets/maps/base/map-world-geographic-base-50-001.svg`: base geografica continua no interactiva.
- Registro en `assets/manifests/assets-manifest.json`.
- Registro en `assets/manifests/assets-inventory.csv`.
- Prototipo `frontend/public/prototype/geo-base-pilot.html`.

## Criterios cumplidos para playtest

- La base se ve en producto real Modo 50.
- Con seis colores de jugadores, masas continentales y rutas/relieves siguen visibles.
- Los territorios se apoyan sobre un mundo continuo.
- Capturas 1920x1080 y 1366x768 son aceptables para playtest privado.

## Limites

No definir nombres de componentes React, arquitectura frontend, persistencia backend ni contratos tecnicos no acordados. Los eventos y tablas de ledger pueden mencionarse como necesidades de producto, pero no como implementacion cerrada.

Modo 26 queda fuera de alcance y conserva arte anterior hasta nuevo brief. Ajustes finos de labels en Europa/Oriente Medio/Oceania quedan como polish P2, no como bloqueo P0.

## Deuda no bloqueante de Arte

El export ideal del mapa tactico deberia venir sin badges demo horneados, sin clases demo `p-*` y con `viewBox` que contenga toda la geometria. Hoy Frontend lo sanea de forma segura en carga.
