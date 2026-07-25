# Entrega: Frontend Productivo Jugable (fast-track sobre el prototipo)

Fecha: 2026-07-25 · Rama `frontend-productivo` · Autor: Claude (frontend)

## Qué se entregó (Fases 1-4 + parte de 5-7 del brief)

- **Fase 1 — Inspección**: fuentes verificadas. Mapas SVG = ids autoritativos del backend
  (svg50 ⊆ world-50 50/50, svg26 ⊆ tactical-26). Hallazgos volcados en `missing-assets.md`.
- **Fase 2 — Layout del prototipo**: `GamePage` rehecha — HUD superior de jugadores
  (avatar, nombre, color, territorios, tropas, conexión, corona de turno, IA, pacto),
  mapa protagonista, viñeta ambiental con el color del jugador activo, La Tribuna
  como dock lateral plegable (`tribune-toggle`).
- **Fase 3 — Interacción directa**: menú radial táctico (+1/+3/MÁX para colocación y
  refuerzos; Atacar/Fortificar activan puntería con destinos resaltados; el click en el
  destino EJECUTA). Sin selects ni inputs numéricos en el flujo principal; se eliminó
  el botón de dados de práctica. Tooltips nativos por territorio (nombre/dueño/tropas).
  Banner central de turno con sonido e instrucción concreta (`TurnBanner`).
- **Fase 4 — Arena de Combate**: modal con desglose matemático transparente —
  tropas iniciales/actuales, razón de la cantidad de dados, parejas mayor-a-menor con
  regla del empate explícita, resumen acumulado por rondas reconstruible sin logs,
  velocidad 1x/2x/instantáneo + `prefers-reduced-motion`, Seguir atacando/Detener,
  banner de conquista. Los dados los tira el backend; el cliente solo anima
  (`attack.resolved` extendido con territorios y tropas antes/después — cambio aditivo).
- **Fase 5 (parcial) — Tribuna**: estado del turno con instrucción por fase (propio y
  ajeno), apuesta de refuerzos REAL (backend `turn.wager`), mercado de espectadores
  visible pero deshabilitado con motivo claro (el ledger LOPDA vive en el backend y aún
  no existe — guardrail del brief: no simular balances), relator con zócalo siempre
  visible (muted = solo voz), diplomacia (pactos), bardeo y chat privado.
- **Fase 7 (parcial)**: reconexión intacta (snapshot + seq + resync), estado
  "Sincronizando" bloqueante, `running` derivado del dato autoritativo del turno.

## Verificación

- `pnpm vitest run`: 33 pasan · backend pytest: 83 pasan · build TS: limpio.
- Playwright e2e multi-contexto (2 navegadores): lobby → colocación radial 5+3 →
  turno y fases sincronizadas → combate real con Arena en ambos → capturas.
  Corrido 2 veces consecutivas: verde.
- Capturas: `test-results/product-1366x768-turn.png`, `product-1920x1080-turn.png`,
  `product-combat-arena.png`, `product-player-view.png`.

## Pendientes reales (sin humo)

1. **Mercado de apuestas de espectadores + Monedas LOPDA**: bloqueado por el ledger
   backend (`betting-and-tribune-design.md`). La UI ya muestra el estado y el motivo.
2. **Modo Caos / recursos tácticos**: no existe en ningún lado del repo (0 menciones);
   se muestra la etiqueta MODO CLÁSICO. Requiere diseño+backend.
3. **Vector targeting por arrastre**: hoy es click-click (origen→destino); la flecha
   arrastrable queda para una iteración.
4. **Pings sobre territorios y planes privados del espectador**: no implementados.
5. **Assets faltantes** (con fallback aprobado, ver `missing-assets.md`): backgrounds,
   avatar del relator, música, stamps, iconos SVG (emoji dependen de la fuente del SO).
6. **Visual regression y tests de accesibilidad automatizados**: no montados aún.
