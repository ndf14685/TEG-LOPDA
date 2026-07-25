# Release Plan

Fecha: 2026-07-25

## Estrategia

Release por verticales jugables, no por capas tecnicas. Ninguna vertical se declara terminada sin pasar: diseño, contratos, backend, frontend, integracion, playtest, correccion y aprobacion.

## Fast-track privado

Actualizacion 2026-07-25: por decision del owner humano, se habilita una version jugable acelerada para amigos. Se permite implementar Frontend antes de cerrar todos los gates formales, manteniendo guardrails P0. Las verticales siguen siendo utiles para ordenar correcciones, pero no bloquean sacar una version usable.

Actualizacion 2026-07-25: el mapa visual actual queda rechazado como P0. Se pausa pulido visual secundario (dados 3D, particulas, animaciones epicas, Tribuna visual y relator animado) hasta aprobar una direccion de mapamundi reconocible.

## Bloque P0 - Mapa

Estado: rechazado visualmente, funcional tecnicamente.

Secuencia obligatoria:

1. Agy entrega tres direcciones de mapamundi completo sin titulos de continentes.
2. Owner/Codex aprueba una direccion.
3. Agy produce capas de una region piloto, preferentemente America del Sur: base, territorios, hitboxes, overlays y manifest.
4. Frontend integra solo esa region piloto.
5. Se valida zoom, seleccion, propiedad, tropas, ataque y legibilidad en 1920x1080 y 1366x768.
6. Solo despues se completa el resto del mundo.

## Vertical 1 - Identidad, lobby, turno y refuerzos

Estado: funcional en fast-track, bloqueada visualmente por mapa P0.

Checkpoint proximo: prototipo de claridad del turno/refuerzos + contrato sincronizado + E2E ampliado.

## Vertical 2 - Ataque, dados y conquista

Estado: backend parcialmente implementado; experiencia no demostrada.

Checkpoint: contrato de combate explicativo antes de UI.

## Vertical 3 - Tribuna y apuestas

Estado: diseñado en docs, no implementado. La apuesta actual no califica.

Checkpoint: contrato ledger/mercado antes de cualquier UI.

## Vertical 4 - Reagrupamiento, diplomacia y cierre

Estado: reagrupamiento/pactos existen parcialmente; no validados en flujo real.

Checkpoint: despues de Vertical 2.

## Vertical 5 - Objetivos, eliminacion y victoria

Estado: dominio y tests backend existen; frontend/playtest no demostrado.

Checkpoint: despues de verticales 1-4.
