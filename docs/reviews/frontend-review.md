# Frontend Review

Fecha: 2026-07-25

## Resultado

Aprobado para esta tanda fast-track posterior al hotfix Windows, mini-regresion y mapa Modo 50. No es cierre final del producto, pero los defectos DEF-01, DEF-02, DEF-03 y el bloqueo P0 del mapa quedaron corregidos o saneados para playtest privado.

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
- Integracion de mapa Modo 50: `b5284b4 feat(map): saneo de exports en la carga`.
- Verificacion local posterior a `b5284b4`: `pnpm test` 33 passed, `pnpm typecheck` passed, `pnpm build` passed, `pnpm e2e` 4 passed.
- Diagnostico e2e posterior a `b5284b4`: centro/borde reciben `path.territory-hitbox` del territorio correcto; `badge_pointer_events` = `none`.

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
- Piloto P0 America del Sur integrado en modo 50 productivo: e2e real valida IDs, hitboxes, labels/tropas, seis colores, seleccion, atacable y ataque en ejecucion.
- Mapamundi Modo 50 integrado en deploy con saneo runtime acotado: oculta badges demo, remueve clases demo `p-*` y ajusta `viewBox` para evitar recorte de Argentina/Chile y menu radial fuera de vista.

## Correcciones pendientes

- P1 post-playtest: nombres largos del HUD pueden quedar truncados; aceptable para candidata, revisar si molesta jugando.
- P1 post-playtest: mercado de espectadores sigue bloqueado hasta ledger Backend; no tratar como bug de Frontend.
- P2: banner central de turno puede tapar temporalmente parte del mapa en capturas de espera; no bloquea flujo.
- P2: mobile 390x844 queda diferido si no es objetivo real del grupo.
- P2: flecha por arrastre, pings, planes privados, set de iconos SVG y assets de Arte quedan para iteracion.
- P2 mapa/export: Agy deberia entregar futuro SVG sin badges demo horneados, sin clases demo `p-*` y con `viewBox` correcto. No bloquea porque Frontend lo sanea al cargar.
- P2 mapa/export: hitboxes con geometria propia pueden solaparse entre vecinos; jugable hoy, pero el export ideal deberia usar hitbox = geometria visible o justificar ampliaciones por territorio.

## Proxima accion

Frontend aprobado para playtest privado con Modo 50. Siguiente agente activo: tester Windows debe ejecutar mini-regresion sobre URL real enfocada en mapa, refuerzo, ataque, reconexion y legibilidad. Backend no entra por esta entrega.
