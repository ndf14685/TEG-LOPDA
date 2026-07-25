# Mini-regresión Modo 50 (Mundo) — TEG-LOPDA (2026-07-25) — PARCIAL (freeze del PO)

Detenida a pedido del PO: se congela hasta incorporar un mapamundi real. Este doc registra lo hallado hasta el corte. Black-box, sin tocar código, sin auditar backend.

- Deploy real: https://paris-penalty-clan-sellers.trycloudflare.com
- Bundle: `static/index-zmZDs9x-.js`
- Mapa: `classic_50` (Mundo — 50 países). Partida sala `9tbfry5h`. 2 contextos aislados: Nessi (rojo), Daro (azul).
- SVG: 50 territorios, `viewBox="0 0 2560 1440"`.

## Resultados por punto

| # | Punto | Resultado |
|---|---|---|
| 1 | No tropas duplicadas ni números falsos | **PASS (visible)** con nota. Badges visibles = 50, todos "1", suma 50 = HUD (25+25). **Nota:** hay 50 `<text>` numéricos **ocultos** (valores 3,2,8,4,6…; opacity 1, fill blanco, fuera de pantalla) en el DOM del SVG — no los ve el jugador, probablemente horneados en el asset base `map-base-…-50`. Conviene limpiarlos. |
| 2 | Colores de territorio = dueño real | **PASS**. 25 rojos (Nessi) + 25 azules (Daro), coincide exactamente con "25 países" de cada uno en el HUD. Sin neutrales ni mismatches. |
| 3 | Argentina/Chile no recortadas | **PARCIAL / FAIL en 1920**. En **1920x1080** la **punta sur de Argentina se recorta ~34px** (path bottom≈1114 vs viewport 1080; SVG box bottom 1072). **Chile OK** (bottom 1066). En **1366x768** Argentina entra (bottom≈763 en viewport 768, 3px bajo el box) y Chile OK. → El recorte se da en pantallas anchas (1920), no en 1366. |
| 4 | Menú radial abre en territorios del sur | **PASS**. Radial abre en Chile y Argentina (de Daro), con opciones +1 / +3 / MÁX (5). |
| 5 | Refuerzos, origen, atacables y ataque | **PARCIAL**. Refuerzos con radial: OK. Selección de origen + ATACAR: OK (se llega a modo puntería "Elegí el país enemigo resaltado", con enemigos atacables resaltados). **Ejecución del ataque en M50: NO confirmada** antes del freeze (la automatización no logró clickear de forma confiable el enemigo lindante resaltado; la mecánica de combate en sí ya fue validada en sesiones previas). |
| 6 | Reconexión vuelve con mapa correcto | **NO PROBADO** (freeze antes de ejecutarlo). |
| 7 | 1920x1080 y 1366x768 | Ambas renderizan el mapa de 50 completo sin overflow horizontal. **1366 entra Argentina; 1920 recorta la punta sur** (ver #3). |
| 8 | Consola / red | **0 errores** observados en setup, carga, colocación, radial y transiciones de fase (Nessi y Daro). Sin requests fallidos, sin errores WS, sin 404. |

## Evidencia (artifacts/playtest/screenshots/)
- `M50-01-board-nessi-1920.png` — tablero 50 en 1920.
- `M50-02-south-clip-1920.png` — sur enfocado (Argentina/Chile).
- `M50-03-radial-chile-1920.png`, `M50-03-radial-argentina-1920.png` — radial en el sur.
- `M50-04-board-1366x768.png` — tablero 50 en 1366.
- `M50-05-attack-combat-1920.png` — estado de ataque (parcial).

## Pendiente al reanudar (post-mapamundi)
- Confirmar ejecución de ataque + Arena en Modo 50 (punto 5).
- Reconexión en partida con mapa 50 (punto 6).
- Revisar el recorte de Argentina en 1920 y los `<text>` numéricos ocultos del asset base 50.
