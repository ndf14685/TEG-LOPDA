# Mini-regresión Modo 50 — Mapa V3 (2026-07-25)

Black-box sobre deploy real. Foco: mapa V3, sin labels, hitboxes, refuerzos, ataque, reconexión, resoluciones 1366/1920/2560/3840, consola/red.

- URL: https://paris-penalty-clan-sellers.trycloudflare.com
- Bundle: `static/index-CVjUN_Hv.js`
- Mapa: `classic_50`. Sala `a6n89f3c`. 2 contextos aislados: Nessi (rojo), Daro (azul).
- SVG: 50 territorios, `viewBox 2560x1440`, capas `layer-0-geo-world`, `geo-continental-shelf`, `geo-landmasses`, `geo-inland-waters`, `layer-1-geo-base`, `layer-2-playable-territories`, `layer-3-hitboxes`, `layer-4-overlays`, `tactical-overlay`.

## Corrección respecto a la sesión anterior
En la corrida previa reporté "no hay mapa" (blobs flotando). **Ahora sí hay mapamundi V3**: se renderiza la geografía real (landmasses/costas/continentes) como base, con los territorios jugables superpuestos. El blocker del freeze (mapamundi incorporado) está resuelto en este bundle.

## Resultados: 8/8 PASS

| Foco | Resultado | Evidencia |
|---|---|---|
| **Mapa V3** | **PASS**. Mapamundi real con continentes (capas geo-*), 173 paths, capa dedicada `layer-3-hitboxes`. | `V3-01-board-1920.png` |
| **Sin labels (Aa)** | **PASS**. El toggle oculta los 49 nombres (→0) y los restaura; mapa, territorios y tropas quedan visibles. | `V3-02-no-labels-1920.png` |
| **Hitboxes** | **PASS**. Click en el centro visual (por coordenada) abre el radial del país **correcto**: Argentina, Uruguay, Islandia, Australia, India, Madagascar — sin mis-hits. Enemigos (Chile/Japón/Alaska) no abren radial (esperado en colocación). | — |
| **Refuerzos** | **PASS**. Radial +1/+3/MÁX coloca bien (Daro colocó 12; Alaska quedó en 21). | — |
| **Ataque (origen/destino + ejecución)** | **PASS**. Origen seleccionado → ATACAR → único vecino atacable resaltado (glow rojo): Alaska→Yukón. Arena con dados, regla `min(tropas−1,3)`, resumen consistente (Alaska 21→18 −3, Yukón 9→9 −0), SEGUIR/DETENER + velocidad. Defensor (Nessi) **no bloqueado** (`coversScreen:false`, centro = mapa). | `V3-03-attack-arena-1920.png` |
| **Reconexión** | **PASS**. Recarga mid-game (T1·ATAQUE) → recupera en ~4.8s con mapa V3 intacto (50 terr, 8 capas geo), identidad "Nessi (vos)", turno (Daro) y fase correctos. 0 errores. | `V3-04-reconnect-1920.png` |
| **Resoluciones 1366/1920/2560/3840** | **PASS**. Sin overflow horizontal en ninguna; mapa+HUD+Tribuna presentes; **Argentina/Chile NO recortadas** en ninguna (el recorte de Argentina en 1920 de la sesión previa —bottom 1114— quedó corregido: ahora 1030<1080). | `V3-05-res-1366x768.png`, `-1920x1080`, `-2560x1440`, `-3840x2160` |
| **Consola / red** | **PASS**. 0 errores en setup, carga, colocación, labels, hitboxes, refuerzos, ataque, reconexión y las 4 resoluciones. |

## Detalle recorte sur por resolución (Argentina bottom vs viewport)
- 1366x768: 732 < 768 · 1920x1080: 1030 < 1080 · 2560x1440: 1373 < 1440 · 3840x2160: 2059 < 2160. Chile OK en todas.

## Clasificación
- P0: 0 · P1: 0 · P2: 0 (en el alcance probado).

## Notas
- El defensor sigue viendo la batalla en panel no bloqueante (fix DEF-01 sostenido en V3).
- Mercado de espectadores sigue BLOQUEADO por diseño (ledger no desplegado); apuesta de refuerzos disponible.
- No se auditó backend (sin estado inconsistente observado).
