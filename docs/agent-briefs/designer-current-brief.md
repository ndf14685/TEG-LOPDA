# Designer Current Brief - Agy

Fecha: 2026-07-25

## Objetivo

Corregir la region piloto America del Sur para aprobar geometria final de mapa.

## Problema

La prueba hibrida A+B+C de Agy resuelve el reconocimiento del mapamundi en JPG. La region piloto America del Sur demuestra bien la arquitectura de capas, labels, badges, seleccion, ataque y flecha, pero no queda aprobada como geometria final: los territorios se perciben como capsulas/blobs superpuestos, no como subdivisiones geograficas coherentes.

## Evidencia

- `test-results/product-1366x768-turn.png`
- `test-results/product-defender-battle.png`
- `test-results/product-spectator-battle.png`
- `artifacts/playtest/screenshots/13-game-1366x768.png`
- `artifacts/playtest/screenshots/14-game-390x844.png`

## Cambio solicitado

No generar todavia 26 ni 100 territorios completos.

Entregar una iteracion corregida de America del Sur, basada en la direccion hibrida A+B+C aprobada.

## Arquitectura visual obligatoria

La direccion aprobada debe poder producirse en cuatro capas:

1. Base geografica no interactiva: costas, continentes, textura y atmosfera.
2. Territorios jugables: SVG independiente, un path por territorio, IDs normalizados y coloreables sin tapar la textura.
3. Hitboxes: areas invisibles independientes para hover, click, seleccion y drag.
4. Overlays: nombres, tropas, estandartes, flechas, pings, animaciones e indicadores.

## Entregables de esta iteracion

- Base geografica de America del Sur coherente con el mapamundi aprobado.
- SVG de territorios jugables de America del Sur, un path por territorio, con bordes internos que parezcan subdivisiones geograficas del continente.
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
- Declaracion explicita de alcance de IDs: modo 50 o modo 26. No afirmar compatibilidad absoluta con ambos si no aplica.

## Criterios de aceptacion de region piloto

- America del Sur se reconoce sin etiquetas.
- Los territorios son visualmente coherentes con la geografia, no capsulas ni blobs arbitrarios.
- Brasil debe leerse como Brasil dentro de la costa este, Argentina como cono sur, Chile como franja andina, Uruguay como pieza pequena al este de Argentina, Colombia/Venezuela al norte y Peru/Bolivia en zona andina/interior.
- Cada territorio tiene path visible y hitbox independiente.
- Labels y tropas no se solapan.
- Los seis colores de jugador preservan textura/geografia.
- Seleccion y objetivo atacable se distinguen sin tapar el mapa.
- La flecha de ataque funciona como overlay, no como parte del territorio.
- 1366x768 sigue siendo legible.
- No incluye textos/HUD genericos de RTS ajenos a TEG-LOPDA como `GLOBAL DOMINATION`, recursos militares falsos o interfaces decorativas no funcionales.

## Limites

No definir nombres de componentes React, arquitectura frontend, persistencia backend ni contratos tecnicos no acordados. Los eventos y tablas de ledger pueden mencionarse como necesidades de producto, pero no como implementacion cerrada.

Frontend no debe integrar todavia un mapa completo nuevo ni esta region piloto. Despues de aprobar la geometria corregida, se hara una prueba tecnica acotada de America del Sur.
