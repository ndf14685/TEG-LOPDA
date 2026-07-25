# Playtest Review

Fecha: 2026-07-25

## Resultado

Playtest Windows recibido por reporte del tester. Resultado general: apto como base jugable privada.

Hotfix post-playtest `bf4e6fe` verificado el 2026-07-25: DEF-01, DEF-02, DEF-03 y DEF-04 quedan aceptados como corregidos para desktop. DEF-05 mobile queda diferido.

## Evidencia disponible

- Reporte pegado por el owner humano el 2026-07-25.
- Entregables presentes en `docs/playtest/`, `artifacts/playtest/screenshots/`, `artifacts/playtest/console/summary.txt` y `artifacts/playtest/network/summary.txt`.
- El tester reporta 0 errores de consola/red, reconexion solida y ausencia de P0.
- Commit verificado: `bf4e6fe fix(frontend): hotfix post-playtest DEF-01..04`.
- Verificacion local: `pnpm test` 33 passed, `pnpm typecheck` passed, `pnpm build` passed, `pnpm e2e` 2 passed.
- Verificacion backend: primera corrida completa tuvo un fallo intermitente en `tests/test_bot.py::test_full_game_between_bots_reaches_victory` por evento `game.finished` no observado; el test paso aislado y la suite completa paso al repetir con 84 passed. Se registra como riesgo de flakiness, no como bloqueo de este hotfix.
- Capturas revisadas: `test-results/product-combat-arena.png`, `test-results/product-defender-battle.png`, `test-results/product-spectator-battle.png`, `test-results/product-1366x768-turn.png`.

## Defectos aceptados

1. DEF-01, P1: corregido. Atacante conserva arena accionable; defensor y espectador reciben tarjeta de batalla no bloqueante y mantienen mapa/Tribuna/chat.
2. DEF-02, P1: corregido desde Frontend. Causa raiz declarada y aceptada: controles duplicados confundian el monto. El backend fue verificado con `backend/tests/test_wager_amount.py`: `amount=3` se acepta como 3.
3. DEF-03, P2: corregido. En colocacion simultanea se muestran chips `COLOCANDO`/`LISTO` en lugar de `JUEGA`.
4. DEF-04, P2: mitigado. Insignias reducidas y desplazadas. Solapamiento residual entre nombres propios del SVG queda para Arte.
5. DEF-05, P2: diferido. Mobile 390x844 no bloquea el playtest desktop con amigos.

## Lo que queda aprobado

- Claridad de turno/fase/accion en desktop.
- Combate auditable: dados, empates, bajas y resumen acumulado.
- Refuerzos con menu radial.
- Reconexión por recarga en lobby y mid-game.
- Estado multiplayer consistente.
- Chat/bardeo cross-cliente.
- Mercado de espectadores bloqueado con explicacion honesta.

## Decisiones

- No entra Backend por DEF-01 ni DEF-02: ambos quedaron resueltos sin cambio productivo backend, salvo test de evidencia.
- DEF-02 no se escala a Backend mientras `backend/tests/test_wager_amount.py` siga demostrando que el monto aceptado coincide con el solicitado.
- Mobile no bloquea el playtest de escritorio con amigos.

## Proxima correccion

Ejecutar mini-playtest de regresion, no auditoria completa: atacante, defensor, espectador, combate, apuesta +3, chat durante batalla y reconexion por recarga.

Despues del mini-playtest, priorizar solo defectos P0/P1 encontrados jugando. Mobile y assets quedan fuera salvo decision explicita del owner.
