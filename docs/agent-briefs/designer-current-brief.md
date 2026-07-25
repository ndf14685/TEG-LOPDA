# Designer Current Brief - Agy

Fecha: 2026-07-25

## Estado

Bloqueo P0 reabierto. El mapa Modo 50 actual queda rechazado: funciona tecnicamente, pero no se lee como mapamundi terminado. No producir mejoras cosmeticas secundarias hasta resolver la capa cartografica base.

## Problema

El producto muestra territorios/blobs sobre fondo azul con grilla, rutas y una brujula. No hay costas continuas, masas continentales reconocibles ni lectura inmediata de mapamundi cuando se ocultan labels.

## Evidencia

- Captura integrada `test-results/sa-pilot-1920x1080.png`: los territorios siguen dominando la lectura visual.
- `assets/maps/base/map-world-geographic-base-50-001.svg`: existe, pero contiene paths continentales simplificados tipo blob (`continent-group-*`), no costas cartograficas.
- Tester Windows sobre bundle `DlvZXums`: 50 territorios e hitboxes correctas, pero no se ve mapamundi real.
- `docs/product-management/decision-log.md`, Decision 2026-07-25-17.

## Cambio solicitado

Entregar un asset nuevo de capa 1: mapamundi geografico completo, original, continuo y reconocible, alineado al `viewBox` del mapa Modo 50.

## Formato obligatorio

- Archivo principal: `assets/maps/base/map-world-geographic-base-50-002.svg`.
- `viewBox="0 0 2560 1440"` o nuevo viewBox justificado que contenga toda la geometria sin recortes.
- Un grupo raiz `id="layer-1-geo-base"` con `pointer-events="none"`.
- Sin labels de paises, sin labels de continentes, sin badges, sin clases de jugador `p-*`, sin hitboxes.
- Grupos internos opcionales por continente, pero solo decorativos.
- Costas y masas continentales completas: America del Norte, America del Sur, Europa, Africa, Asia y Oceania deben reconocerse sin texto.
- Estilo original de mesa de guerra: baja saturacion, topografia/cartografia sutil, oceano legible, sin copiar IP ni calcar un mapa comercial.

## Entregables

1. `assets/maps/base/map-world-geographic-base-50-002.svg`.
2. Actualizacion del manifest runtime `assets/manifest/assets-manifest.json` y del inventario de Arte si corresponde.
3. Capturas exportadas del asset solo, sin territorios ni labels: 1920x1080, 1366x768, 2560x1440 y 3840x2160.
4. Captura overlay de referencia con territorios al 30-35% de opacidad y seis colores, solo para validar que la base sigue visible.

## Criterios de aceptacion visual

- Una persona reconoce el mapamundi en menos de un segundo sin leer labels.
- Hay costas continuas y siluetas continentales, no manchas aisladas.
- Europa y Asia se leen como regiones continentales conectadas, no como piezas sueltas.
- America del Sur mantiene silueta continental completa aunque los territorios encima esten coloreados.
- Los elementos decorativos (rutas, brujula, reticula) no reemplazan ni tapan la geografia.

## Limites

No definir componentes React, logica de hitboxes, reglas de juego, backend ni nombres de eventos. No retocar los territorios jugables actuales como solucion principal: el bloqueo es ausencia/calidad de la capa geografica base.
