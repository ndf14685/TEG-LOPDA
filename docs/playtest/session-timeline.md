# Session timeline

Contextos aislados: Nessi (organizador+jugador), Daro (jugador), Tribu (espectador). URL deploy real.

1. Landing 1920 → captura, elementos interactivos, sin errores (`01-landing-1920.png`). Carga ~2s. Bundle `index-BLdEJnCn.js` (10 colores → build reciente).
2. Nessi funda partida (rol admin con clave), sala `z87pn8cy` → Cuartel general (`02-admin-cuartel-1920.png`).
3. Recluta Daro (Azul) y Tribu (espectador, Verde); copia links personalizados.
4. Daro y Tribu entran por link → pantalla de identidad correcta (rol/color) (`03-daro-join-1920.png`).
5. Los tres al lobby → 3/3, gating por rol, chat privado correcto (`04-lobby-*-1920.png`).
6. Daro marca listo → start "1 listos". Reconexión en lobby: Daro recarga → recupera identidad y "listo".
7. Nessi inicia → juego. Colocación inicial (5 tropas), fase/instrucción visibles (`05-game-start-*-1920.png`).
8. Menú radial de colocación (+1/+3/MÁX) (`06-radial-menu-nessi-1920.png`). Colocación 5+3 completada por ambos.
9. Audit de turno T1: los 3 coinciden en JUEGA Daro / T1 · REFUERZOS.
10. Daro: apuesta de refuerzos ("Arriesgar +3" → pool 9→8, DEF-02), coloca, pasa a Ataque (`07-daro-reinforce-wager-1920.png`).
11. Ataque desde mapa: país propio → ATACAR → enemigo (`08-daro-attack-select-1920.png`).
12. Arena de combate Brazil→Colombia: dados, regla, resumen (`09-combat-arena-daro-1920.png`).
13. Vistas de defensor y espectador durante la batalla: **también reciben la Arena como modal bloqueante**, con desglose por-dado y empate etiquetado (`10-nessi-during-battle-1920.png`, `10-tribu-during-battle-1920.png`) → DEF-01.
14. SEGUIR ATACANDO (incl. Instantáneo): math consistente 17→12→9; sin conquista (defensor-favorable) (`11-`, `12-`).
15. Daro termina turno → toast "💸 Daro perdió la apuesta: se fue con 1 refuerzos"; los 3 pasan a JUEGA Nessi / T2.
16. Chat (Nessi→Daro) y bardeo (TRAIDOR) cross-cliente OK.
17. Reconexión mid-game: Daro recarga durante turno de Nessi → recupera todo en ~4.4s, sin errores.
18. Resoluciones: 1366x768 (`13-`), mobile 390x844 (`14-`), landing mobile (`15-`). Sin overflow.
19. Segunda pasada técnica (solo lectura): `CombatArena.tsx` confirma el modal `fixed inset-0` como causa de DEF-01.

Errores de consola / red durante toda la sesión: **0** observados.
