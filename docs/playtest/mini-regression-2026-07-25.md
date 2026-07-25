# Mini-regresión — TEG-LOPDA (2026-07-25)

- Deploy real: https://paris-penalty-clan-sellers.trycloudflare.com
- Bundle: `static/index-B-E0RDsg.js` (nuevo; antes `index-BLdEJnCn.js` → fixes desplegados)
- Contextos aislados: Nessi (organizador+jugador, atacante), Daro (jugador, defensor), Tribu (espectador)
- Sin tocar código, sin commits/push/deploy. Solo escritura en docs/playtest y artifacts/playtest.

## Resultado: 6/6 PASS

| # | Punto | Resultado | Evidencia |
|---|---|---|---|
| 1 | Atacante abre combate y puede seguir/detener | **PASS** — Arena con "SEGUIR ATACANDO" y "DETENER" | `R-01-attacker-arena.png` |
| 2 | Defensor ve batalla sin bloquearse, usa chat/Tribuna | **PASS** — batalla en panel chico abajo-izq ("BATALLA EN CURSO"), mapa visible, chat+reacciones+toggle Tribuna usables (`coversScreen:false`, centro=mapa) | `R-23-daro-during-battle.png` |
| 3 | Espectador ve batalla sin bloquearse, usa chat/Tribuna | **PASS** — idéntico al defensor: no bloqueado, chat/reacciones/Tribuna usables | `R-23-tribu-during-battle.png` |
| 4 | Apuesta +3: "Pedido +3 → aceptado +3" | **PASS** — "Pedido +3 enviado — esperando confirmación" → "Pedido +3 → aceptado +3", "Aceptado por el server: 3 tropas en juego → paga 6"; pool bajó exactamente 3 (11→8) | `R-04-wager-plus3.png` |
| 5 | Colocación inicial: sin JUEGA falso | **PASS** — durante "COLOCACIÓN I" no aparece badge JUEGA en ningún cliente | `R-05-placement-hud-nessi.png` |
| 6 | Recargar durante partida vuelve bien | **PASS** — Daro recargó en T1·ATAQUE → recuperó en ~4.5s: /game, 26 territorios, "Daro (vos)", jugador activo Nessi, fase T1·ATAQUE, 13 países; 0 errores | `R-06-reload-daro.png` |

## Estado de los defectos previos
- **DEF-01** (Arena bloqueaba a defensor/espectador): **CORREGIDO**. La batalla para no-atacantes es un panel no bloqueante; el mapa y La Tribuna quedan usables.
- **DEF-02** (monto de apuesta no transparente): **CORREGIDO**. Flujo pedido→aceptado explícito con monto y pago; el pool baja el monto exacto.
- **DEF-03** (JUEGA falso en colocación): **CORREGIDO**. No hay badge de turno durante la colocación simultánea.

## Notas
- Consola/red: **0 errores** en toda la mini-regresión.
- No se volvió a auditar el resto (mercado de monedas sigue BLOQUEADO por diseño; mobile/labels sin cambios evaluados).
