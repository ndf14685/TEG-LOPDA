# Combat audit

## Flujo observado (caja negra)
1. Fase de ataque: "¡ES TU TURNO — ATAQUE! Tocá un país tuyo (borde dorado) y elegí ATACAR."
2. Click en país propio → aparece radial con **ATACAR** y ✕.
3. Click en ATACAR → "Elegí el país enemigo resaltado para atacar."
4. Click en país enemigo lindante → abre la **Arena de Combate**.
5. Rondas: "SEGUIR ATACANDO" (atacante) hasta conquistar/detener; velocidad 1x/2x/Instantáneo.

## Caso real capturado (Brazil → Colombia)
- Atacante Brazil (Daro): inició 17.
- Defensor Colombia (Nessi): inició 9.
- Regla de dados mostrada en pantalla: atacante `min(tropas − 1, 3)`, defensor `min(tropas, 3)` → 3 vs 3.
- Ronda 1 (desglose por-dado visible en la vista del defensor/espectador):
  - Pareja 1: 3 vs 6 → gana defensor (6 > 3) → atacante pierde 1
  - Pareja 2: 3 vs 2 → gana atacante (3 > 2) → defensor pierde 1
  - Pareja 3: 1 vs 1 → **EMPATE: la regla del TEG favorece al defensor → atacante pierde 1**
  - Resultado: atacante −2, defensor −1.
- Ronda 2: atacante −3, defensor −0.
- Resumen acumulado: Brazil 17 → 12 (−5), Colombia 9 → 8 (−1). **Consistente** (−2−3 = −5; −1−0 = −1).

## Respuesta a la pregunta de auditoría
"Tenía 16, ataqué a uno de 4 y terminé con 10, ¿dónde se perdieron 6?"
→ **Contestable 100% desde la UI, sin logs ni código.** La Arena muestra: tropas iniciales y actuales de ambos bandos, cuántos dados tiró cada uno y por qué (regla explícita), el resultado por pareja de dados con el caso de empate etiquetado, las bajas por ronda y el total inicial→final. **No es CRITICAL.**

## Legibilidad / animación / tensión
- Dados con caras claras, colores por bando (atacante rojo, defensor celeste), "VS" central.
- Control de **velocidad** (1x/2x/Instantáneo) — permite reducir animación. 
- Respeta **prefers-reduced-motion** (anima en 0ms si está activo) — accesible.
- **Esc** cierra la Arena.
- Banner de conquista previsto: "¡TERRITORIO CONQUISTADO! Las tropas atacantes avanzaron automáticamente a ocuparlo" (movimiento posterior automático; verificado por código, no capturado en vivo por falta de conquista en la sesión).

## Sincronización entre jugadores
- Atacante, defensor y espectador ven la misma batalla con las mismas cifras. Estado consistente.

## Defecto asociado
- **DEF-01**: la Arena es un modal full-screen que bloquea a defensor y espectador (no autocierra). El contenido es excelente; el contenedor es el problema.

## Falta explícito (menor)
- El desglose por-pareja con etiqueta de empate se vio nítido en la vista de defensor/espectador; en la vista del atacante mientras avanza "SEGUIR ATACANDO" conviene garantizar que la última tirada muestre siempre el mismo desglose por-dado (para que el atacante también lea empates por-dado, no solo el acumulado).
