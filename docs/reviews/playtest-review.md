# Playtest Review

Fecha: 2026-07-25

## Resultado

Candidata habilitada para playtest privado fast-track.

## Evidencia de entrada

- Commit candidato: `1dfa7f8`.
- `pnpm test`, `pnpm typecheck`, `pnpm build`, `pnpm e2e` verdes.
- Capturas limpias regeneradas en `test-results/`.

## Alcance recomendado

- Dos jugadores humanos por links personalizados.
- Lobby, ready, colocacion 5+3, refuerzos, ataque, Arena, pasar fase, terminar turno.
- Revisar claridad de turno propio y turno ajeno.
- Revisar si Tribuna entretiene o estorba.
- Registrar cualquier confusion sobre apuestas de refuerzos vs mercado bloqueado.

## Clasificacion

- P0: no se puede continuar la partida, estado inconsistente, perdida de sesion, dados/bajas incorrectas.
- P1: se puede jugar pero hay confusion de turno/fase/accion o UI tapa informacion.
- P2: polish visual, sonidos, animacion, copy o assets.
