# Playtest Review

Fecha: 2026-07-25

## Resultado

Playtest Windows recibido por reporte del tester. Resultado general: apto como base jugable privada.

Hotfix post-playtest `bf4e6fe` verificado el 2026-07-25: DEF-01, DEF-02, DEF-03 y DEF-04 quedan aceptados como corregidos para desktop. DEF-05 mobile queda diferido.

Mini-regresion Windows 2026-07-25: 6/6 PASS sobre deploy real. Frontend queda aprobado para esta tanda; el siguiente bloqueo P0 es el mapa visual.

## Evidencia disponible

- Reporte pegado por el owner humano el 2026-07-25.
- Entregables presentes en `docs/playtest/`, `artifacts/playtest/screenshots/`, `artifacts/playtest/console/summary.txt` y `artifacts/playtest/network/summary.txt`.
- El tester reporta 0 errores de consola/red, reconexion solida y ausencia de P0.
- Commit verificado: `bf4e6fe fix(frontend): hotfix post-playtest DEF-01..04`.
- Verificacion local: `pnpm test` 33 passed, `pnpm typecheck` passed, `pnpm build` passed, `pnpm e2e` 2 passed.
- Verificacion backend: primera corrida completa tuvo un fallo intermitente en `tests/test_bot.py::test_full_game_between_bots_reaches_victory` por evento `game.finished` no observado; el test paso aislado y la suite completa paso al repetir con 84 passed. Se registra como riesgo de flakiness, no como bloqueo de este hotfix.
- Capturas revisadas: `test-results/product-combat-arena.png`, `test-results/product-defender-battle.png`, `test-results/product-spectator-battle.png`, `test-results/product-1366x768-turn.png`.
- Mini-regresion: `docs/playtest/mini-regression-2026-07-25.md`.
- Capturas de mini-regresion: `artifacts/playtest/screenshots/R-01-attacker-arena.png`, `R-23-daro-during-battle.png`, `R-23-tribu-during-battle.png`, `R-04-wager-plus3.png`, `R-05-placement-hud-nessi.png`, `R-06-reload-daro.png`.

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

Mini-playtest de regresion completado y aprobado. No abrir mas correcciones de Frontend por esta tanda.

Siguiente foco: Agy debe resolver el P0 de mapa reconocible. Frontend solo vuelve cuando exista direccion visual aprobada para integrar una region piloto.
