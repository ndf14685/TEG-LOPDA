# Designer Current Brief - Agy

Fecha: 2026-07-25

## Objetivo

Resolver el bloqueo P0 del mapa: entregar una direccion visual de mapamundi reconocible, original y jugable para TEG-LOPDA.

## Problema

El mapa actual queda rechazado. Aunque funciona tecnicamente, sus formas no permiten reconocer inmediatamente un mapamundi. El jugador depende de leer titulos de continentes para entender la pantalla. Eso bloquea la presentacion basica del juego.

## Evidencia

- `test-results/product-1366x768-turn.png`
- `test-results/product-defender-battle.png`
- `test-results/product-spectator-battle.png`
- `artifacts/playtest/screenshots/13-game-1366x768.png`
- `artifacts/playtest/screenshots/14-game-390x844.png`

## Cambio solicitado

Entregar tres propuestas visuales del mapamundi completo, sin nombres de continentes, para elegir una direccion.

Cada propuesta debe mostrar:

- America del Norte reconocible.
- America del Sur reconocible.
- Europa reconocible.
- Africa reconocible.
- Asia reconocible.
- Oceania reconocible.
- Oceanos que separen regiones.
- Estetica original de mesa de guerra, sin copiar propiedad intelectual de Age of Empires ni TEG.

## Arquitectura visual obligatoria

La direccion aprobada debe poder producirse en cuatro capas:

1. Base geografica no interactiva: costas, continentes, textura y atmosfera.
2. Territorios jugables: SVG independiente, un path por territorio, IDs normalizados y coloreables sin tapar la textura.
3. Hitboxes: areas invisibles independientes para hover, click, seleccion y drag.
4. Overlays: nombres, tropas, estandartes, flechas, pings, animaciones e indicadores.

## Entregables de esta iteracion

- Tres propuestas del mapamundi completo.
- Version sin titulos de continentes para cada propuesta.
- Version con territorios aproximados para cada propuesta.
- Explicacion breve de como cada propuesta soporta territorios, hitboxes y overlays.
- Riesgos visuales de cada propuesta.
- Recomendacion de una direccion.

No producir todavia todo el set final de territorios/hitboxes del mundo. Primero se aprueba direccion.

## Criterios de aceptacion de direccion

- Se reconoce como mapamundi en menos de un segundo.
- Los seis continentes/regiones principales se reconocen sin titulos.
- America del Sur conserva silueta continental.
- America del Norte conecta visualmente con Mexico/Centroamerica.
- Europa no es un conjunto ilegible de manchas.
- Africa conserva su forma general.
- Rusia, Siberia, China, India y Japon integran visualmente Asia.
- Oceania queda ubicada geograficamente y no como capsulas aisladas.
- La propuesta permite colores de seis jugadores sin convertir continentes en manchas planas.
- La propuesta es viable para 1366x768.

## Limites

No definir nombres de componentes React, arquitectura frontend, persistencia backend ni contratos tecnicos no acordados. Los eventos y tablas de ledger pueden mencionarse como necesidades de producto, pero no como implementacion cerrada.

Frontend no debe integrar todavia un mapa completo nuevo. Despues de aprobar direccion, se hara una prueba tecnica de una unica region, preferentemente America del Sur.
