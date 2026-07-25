# TEG-LOPDA — Playtest privado fast-track (caja negra)

- **Fecha:** 2026-07-25
- **Rol:** Lead Game QA / UX Researcher / Multiplayer Test Engineer
- **Entorno:** Windows, Playwright MCP, contextos de navegador aislados (cookies/localStorage/sesión independientes)
- **URL probada (deploy real):** https://paris-penalty-clan-sellers.trycloudflare.com
- **Bundle desplegado:** `static/index-BLdEJnCn.js`
- **Contextos:** `Nessi` (organizador+jugador, Rojo), `Daro` (jugador, Azul), `Tribu` (espectador, Verde)
- **Resoluciones:** 1920x1080 (principal), 1366x768, 390x844 (mobile)
- **Restricción cumplida:** no se modificó código, no se commiteó, no se pusheó, no se desplegó. Primera pasada 100% caja negra; inspección de código solo después.

## Veredicto en una línea

La build desplegada es un **salto grande de calidad**: se juega, se entiende de quién es el turno, el combate es **auditable de punta a punta** y la reconexión funciona. El problema principal ya no es "no se entiende" sino un **modal de combate que bloquea a defensor y espectador en cada ataque**. No se encontró ningún P0 (bloqueante de partida) ni estado inconsistente entre clientes.

## Qué se probó y resultado

| Área | Resultado |
|---|---|
| Landing (1920 + mobile) | OK. Carga ~2s, sin errores de consola/red, hint claro para jugadores |
| Links personalizados / identidad / color / rol | OK. Daro=player/Azul, Tribu=spectator/Verde, correctos |
| Lobby / ready / gating por rol | OK. 3/3 consistente; admin ve "Iniciar", jugador solo "listo", espectador sin acciones |
| Chat privado en lobby | OK. Visibilidad correcta (cada uno ve los canales que corresponde) |
| Colocación inicial 5+3 | OK. Fase e instrucción visibles; menú radial +1/+3/MÁX |
| Audit de turno (3 clientes) | OK. Todos coinciden en quién juega; "JUEGA X" + "TURNO DE X" / "¡ES TU TURNO!" |
| Refuerzos (menú radial) | OK y rápido |
| Apuesta de refuerzos (por recursos) | Funciona end-to-end (toast "Daro perdió la apuesta: se fue con 1 refuerzos"). **Ver DEF-02** (monto vs etiqueta) |
| Pasar a ataque / ataque desde mapa | OK. Selección país propio → ATACAR → elegir enemigo resaltado |
| Arena de combate (dados, empates, bajas, resumen) | Contenido **excelente y auditable**. **Ver DEF-01** (modal bloqueante) |
| Auditabilidad "16→10, ¿dónde fueron 6?" | **Resuelto desde la UI** (inicial→final, por-dado, regla de dados, resumen por ronda) |
| Traspaso de turno | OK. Consistente en los 3 clientes |
| Mercado de espectadores (monedas) | **Bloqueado a propósito** con explicación clara (se habilita cuando el ledger del backend esté desplegado) |
| Chat / bardeo en juego | OK cross-cliente |
| Reconexión (lobby y mid-game) | OK. Recupera identidad, turno, fase, mapa y chat en ~4.4s, sin errores |
| 1366x768 | OK. Sin overflow, layout completo y legible |
| Mobile 390x844 | Responsive sin overflow, pero **mapa muy chico para tocar** (DEF-05) |
| Consola / red | **Cero errores** observados en toda la sesión |

## Conteo de defectos

- **P0 / BLOCKER:** 0
- **P1 (confunde turno/fase/acción/combate o correctness de apuesta):** 2 (DEF-01 combate bloqueante, DEF-02 monto de apuesta)
- **P2 (visual/mobile/polish):** 3 (DEF-03, DEF-04, DEF-05)

Detalle completo con pasos, evidencia y causa probable en `prioritized-defects.md`.

## Nota de alcance

Fast-track con 3 contextos (el brief pedía "al menos 2": Nessi + Daro; se agregó un espectador para auditar tribuna/turnos). No se alcanzó una **conquista limpia** en la sesión: los ataques de Daro (17 vs 9) no rompieron la defensa por varianza defensor-favorable del TEG; el flujo post-conquista (banner "¡TERRITORIO CONQUISTADO! — las tropas avanzaron automáticamente") se verificó por código pero no se capturó en vivo. El matriz completo de 6 contextos, Modo Caos, diplomacia avanzada y performance profunda quedan para una pasada extendida.
