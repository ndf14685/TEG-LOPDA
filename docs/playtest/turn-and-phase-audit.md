# Turn & phase audit

## Señales de "de quién es el turno"
- **TopHud**: badge "JUEGA" sobre el jugador activo + tarjetas de cada jugador con "N países · N tropas".
- **hud-phase**: "T1 · REFUERZOS", "T1 · ATAQUE", "T2 · REFUERZOS", etc.
- **ESTADO DEL TURNO** (panel derecho): mensaje distinto según seas activo o no.

## Cross-check en 3 clientes (T1, turno de Daro)
| Cliente | ¿Quién juega? | Fase | Mensaje |
|---|---|---|---|
| Nessi (inactivo) | Daro | T1 · REFUERZOS | "TURNO DE DARO — Está colocando refuerzos (le quedan 9)." Sin botones de acción habilitados |
| Daro (activo) | Daro | T1 · REFUERZOS | "¡ES TU TURNO — REFUERZOS! Tenés 9 tropas — tocá tus países para el menú radial." Botones: Pasar a Ataque, Terminar turno, Arriesgar |
| Tribu (espectador) | Daro | T1 · REFUERZOS | "TURNO DE DARO — Está colocando refuerzos (le quedan 9)." |

**Los tres coinciden.** No hay ambigüedad de turno → el fallo *blocker* del brief ("un jugador no puede identificar de quién es el turno") **no se reproduce**: se identifica de inmediato.

## Traspaso de turno (Daro → Nessi)
Al terminar Daro, los 3 clientes pasaron a "JUEGA Nessi", "T2 · REFUERZOS", con Nessi viendo "¡ES TU TURNO!" y los demás "TURNO DE NESSI". Consistente.

## Instrucción por fase (clara)
- Refuerzos: "tocá tus países para el menú radial".
- Ataque: "Tocá un país tuyo (borde dorado) y elegí ATACAR" → luego "Elegí el país enemigo resaltado".
- Reagrupe: acceso desde "Pasar a Reagrupe".

## Señales visuales/sonoras
- Visual: badge JUEGA, viñeta ambiental del color del jugador activo, borde dorado en países accionables.
- Sonora: **OFF por defecto** (control "Sonidos: OFF" y relator "voz OFF"); el que quiera audio lo activa. No hubo señal sonora por defecto (esperado en esta configuración).

## Defecto asociado
- **DEF-03**: durante la colocación inicial simultánea el HUD marca "JUEGA" a un solo jugador aunque ambos colocan.
