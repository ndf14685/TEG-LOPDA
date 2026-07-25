# Integración P0 Mapa — Piloto América del Sur (modo 50)

Fecha: 2026-07-25 · Autor: Claude (frontend)

## Qué se integró
- Geometría realista aprobada del piloto transplantada al mapa productivo
  `assets/maps/base/map-base-tactical-50-001.svg` mediante transformación afín
  al hueco actual de Sudamérica (escala 0.5696). Script reproducible:
  `deploy/scripts/integrate-sa-pilot.py`.
- **IDs 100% conservados** (8/8, `id_changes_count: 0`); el resto del mundo intacto
  (50 territorios, tests de mapas del backend verdes sin tocar backend).
- **Capas separadas**: territorio visible (`.territory`, solo pinta), hitbox
  transparente (`.territory-hitbox` + `data-territory`, captura click/hover/tooltip)
  y overlays (labels tercio superior según piloto + insignias dinámicas).
- Toggle de etiquetas "Aa" en el mapa (valida reconocibilidad sin nombres).

## Validado en partida real (e2e `south-america-pilot.spec.ts`, 3 corridas verdes)
Modo 50 con 8 territorios SA · propiedad con SEIS colores (2 humanos + 4 IA) ·
labels y tropas sin choque · seleccionado · atacable · ataque en ejecución
(Arena) · colocación y refuerzos vía hitboxes.

## Declarado FUERA DE ALCANCE: modo 26 con geometría nueva
La app soporta el modo 26 (es el default), pero el piloto para modo 26 solo
**oculta** Venezuela/Bolivia/Uruguay dejando huecos en el continente: no es un
rompecabezas válido de 5 piezas. El mapa 26 conserva su arte actual hasta que
Arte entregue la geometría de 5 piezas encastadas. Agy además debe corregir el
manifest 26/50 (`assets/manifests/south-america-pilot-manifest.json`).

## Nota de bordes
Las piezas encastadas se solapan ~px en los bordes compartidos; el hitbox
superior gana en esa franja. Imperceptible al jugar; si Arte re-exporta con
bordes exactos, desaparece.
