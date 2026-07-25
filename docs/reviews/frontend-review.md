# Frontend Review

Fecha: 2026-07-25

## Resultado

Aprobado para esta tanda fast-track posterior al hotfix Windows y mini-regresion. No es cierre final del producto, pero los defectos DEF-01, DEF-02 y DEF-03 quedaron corregidos en deploy real.

## Evidencia

- Commits revisados: `f440873` y `26c8204`.
- Documento de entrega: `docs/reviews/frontend-delivery-2026-07-25.md`.
- `pnpm test` -> 33 passed.
- `pnpm typecheck` -> passed.
- `pnpm build` -> passed.
- `cd backend && uv run pytest -q` -> 83 passed.
- `pnpm e2e` -> 2 passed despues de `1dfa7f8`.
- Hotfix revisado: `bf4e6fe fix(frontend): hotfix post-playtest DEF-01..04`.
- Verificacion local posterior a `bf4e6fe`: `pnpm test` 33 passed, `pnpm typecheck` passed, `pnpm build` passed, `pnpm e2e` 2 passed.
- Verificacion backend de soporte: `backend/tests/test_wager_amount.py` y tests de apuesta pasaron; suite backend completa paso al repetir con 84 passed.
- Capturas regeneradas: `test-results/product-player-view.png`, `test-results/product-combat-arena.png`, `test-results/product-1366x768-turn.png`, `test-results/product-1920x1080-turn.png`.
- Capturas post-hotfix revisadas: `test-results/product-defender-battle.png`, `test-results/product-spectator-battle.png`.
- Mini-regresion Windows: `docs/playtest/mini-regression-2026-07-25.md`, resultado 6/6 PASS sobre bundle `static/index-B-E0RDsg.js`.

## Aprobado

- Turno/fase/accion son mucho mas visibles que en la version anterior.
- Mapa domina la pantalla y ya no se siente como panel administrativo.
- Refuerzos/ataque se operan desde el mapa con menu radial y seleccion directa.
- Se elimino el boton de dados de practica.
- Captura limpia de turno muestra mercado de espectadores como `BLOQUEADO`, sin botones fantasma.
- Tribuna existe como dock de espera activa, con estado honesto para mercado de espectadores bloqueado por ledger faltante.
- Reconexión cambia estado persistente del panel.
- Fallback textual de emotes evita cuadros de glifo en el tablero principal.
- E2E determinista refuerza fronteras para asegurar origen de ataque real.
- Arena no bloqueante para defensor/espectador: mantiene batalla visible sin impedir Tribuna/chat/mapa.
- Apuesta de refuerzos ahora muestra monto pedido y aceptado; el backend queda cubierto por test especifico de `amount=3`.
- Colocacion simultanea ya no comunica un turno unico falso.

## Correcciones pendientes

- P1 post-playtest: nombres largos del HUD pueden quedar truncados; aceptable para candidata, revisar si molesta jugando.
- P1 post-playtest: mercado de espectadores sigue bloqueado hasta ledger Backend; no tratar como bug de Frontend.
- P2: banner central de turno puede tapar temporalmente parte del mapa en capturas de espera; no bloquea flujo.
- P2: mobile 390x844 queda diferido si no es objetivo real del grupo.
- P2: flecha por arrastre, pings, planes privados, set de iconos SVG y assets de Arte quedan para iteracion.

## Proxima accion

No abrir mas trabajo de Frontend hasta tener direccion de mapa aprobada o un P0/P1 nuevo del playtest. El siguiente agente activo es Agy por el rediseño P0 del mapa.
