# Designer Current Brief - Agy

Fecha: 2026-07-25

## Objetivo

Convertir la direccion visual hibrida A+B+C aprobada en una region piloto jugable del mapa.

## Problema

El mapa actual queda rechazado. La prueba hibrida A+B+C de Agy resuelve el reconocimiento del mapamundi en JPG, pero todavia no demuestra produccion tecnica real en SVG/hitboxes/overlays.

## Evidencia

- `test-results/product-1366x768-turn.png`
- `test-results/product-defender-battle.png`
- `test-results/product-spectator-battle.png`
- `artifacts/playtest/screenshots/13-game-1366x768.png`
- `artifacts/playtest/screenshots/14-game-390x844.png`

## Cambio solicitado

No generar todavia 26 ni 100 territorios completos.

Entregar una region piloto: America del Sur, basada en la direccion hibrida A+B+C aprobada.

## Arquitectura visual obligatoria

La direccion aprobada debe poder producirse en cuatro capas:

1. Base geografica no interactiva: costas, continentes, textura y atmosfera.
2. Territorios jugables: SVG independiente, un path por territorio, IDs normalizados y coloreables sin tapar la textura.
3. Hitboxes: areas invisibles independientes para hover, click, seleccion y drag.
4. Overlays: nombres, tropas, estandartes, flechas, pings, animaciones e indicadores.

## Entregables de esta iteracion

- Base geografica de America del Sur coherente con el mapamundi aprobado.
- SVG de territorios jugables de America del Sur, un path por territorio.
- IDs conservados del mapa actual cuando existan; si algun ID cambia, entregar tabla `old_id -> new_id`.
- Hitboxes invisibles independientes por territorio.
- Posiciones de etiquetas.
- Posiciones de tropas/badges.
- Estado visual de propiedad para seis colores.
- Estado seleccionado.
- Estado atacable.
- Flecha de ataque America del Sur -> Africa como prueba de overlay.
- Manifest de assets y capas generadas.
- Capturas 1920x1080 y 1366x768: sin etiquetas, con etiquetas/tropas, seleccionado, atacable y ataque en ejecucion.

## Criterios de aceptacion de region piloto

- America del Sur se reconoce sin etiquetas.
- Los territorios son visualmente coherentes con la geografia, no blobs arbitrarios.
- Cada territorio tiene path visible y hitbox independiente.
- Labels y tropas no se solapan.
- Los seis colores de jugador preservan textura/geografia.
- Seleccion y objetivo atacable se distinguen sin tapar el mapa.
- La flecha de ataque funciona como overlay, no como parte del territorio.
- 1366x768 sigue siendo legible.
- No incluye textos/HUD genericos de RTS ajenos a TEG-LOPDA como `GLOBAL DOMINATION`, recursos militares falsos o interfaces decorativas no funcionales.

## Limites

No definir nombres de componentes React, arquitectura frontend, persistencia backend ni contratos tecnicos no acordados. Los eventos y tablas de ledger pueden mencionarse como necesidades de producto, pero no como implementacion cerrada.

Frontend no debe integrar todavia un mapa completo nuevo. Despues de aprobar esta region piloto, se hara una prueba tecnica acotada de America del Sur.
