# Diagnóstico: clicks muertos en el SVG global (modo 50)

Fecha: 2026-07-25 · Autor: Claude (frontend) · Alcance: SOLO diagnóstico
Evidencia reproducible: `e2e/diagnostic-global-svg.spec.ts` (partida real,
`document.elementFromPoint` sobre territorio propio en colocación).

## Resultado de la sonda en vivo

```json
{
  "territorio": "territory-south-america-colombia",
  "centro_recibe": "circle.badge-circle",             ← NO es el hitbox
  "borde_recibe": "path.territory-hitbox [territory-north-america-new-york]", ← hitbox AJENO
  "badges_demo_horneados": 50,
  "badge_pointer_events": "auto"
}
```

## Causa raíz A (primaria): insignias demo horneadas interceptan el centro

`map-base-tactical-50-001.svg` (export global de hoy 06:12) incluye en
`layer-4-overlays` **50 `badge-group` de demostración** (círculo sólido r=28 +
número) SIN `pointer-events: none`. En SVG el default es `visiblePainted`: el
círculo captura el click. El centro del territorio — donde todo jugador
clickea, porque ahí está el número — es zona muerta: el handler del hitbox
nunca se entera y el menú radial no abre. En los bordes sí funciona, lo que
explica el síntoma intermitente.

Agravante: el frontend dibuja sus PROPIAS insignias dinámicas (tropas reales),
así que las demo además duplican números en pantalla.

## Causa raíz B: hitboxes solapados ENTRE territorios distintos

La geometría de los hitboxes del export global no coincide 1:1 con la capa
visible: el hitbox de `new-york` (y 410-600, x 500-880) invade la región de
`colombia`. Al solaparse, gana el último en orden DOM (Norteamérica se declara
después de Sudamérica) y roba el click del vecino. Esto NO pasa en el piloto
SA integrado, donde hitbox = misma geometría que el territorio visible.

## Defectos secundarios detectados (mismo export)

- **viewBox recorta el mapa**: `0 0 2560 1440` pero la geometría llega a
  y=1540 → Chile/Argentina/Java pierden los ~100px inferiores.
- **Clases demo de propiedad** (`p-red`, `p-cyan`, …) horneadas en la capa
  visible: pintan dueños falsos y sus strokes pelean con los estados runtime
  (`selected`/`attackable`/`frontier`).

## Veredicto sobre el contrato

**El contrato `territory-hitbox` + `data-territory` NO necesita cambios.**
Los 50 ids coinciden 100% con el backend (`world-50`) en ambas capas, y el
cableado del frontend funciona — probado por el piloto SA validado (que sigue
intacto). El problema es del EXPORT del SVG global, no del contrato ni del
código de interacción.

## Correcciones que corresponden al export (Agy)

1. `layer-4-overlays` sin badges/labels demo interactivos: o vacío de badges
   (el frontend los dibuja con datos reales) o con `pointer-events: none`.
2. Hitboxes con la MISMA geometría que su territorio visible (o al menos sin
   invadir territorios ajenos).
3. `viewBox` que contenga toda la geometría (p. ej. `0 0 2560 1600`) o
   geometría reescalada a 1440.
4. Capa visible sin clases `p-*` de demostración.
