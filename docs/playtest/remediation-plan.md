# Remediation plan (orden exacto de corrección)

Prioridad por impacto sobre jugabilidad/experiencia y costo estimado. No se corrigió nada en esta tarea.

## 1. DEF-01 — Arena de combate no bloqueante para observadores (MAJOR / P1)
- **Qué:** para clientes donde `!iAmAttacker`, no renderizar la Arena como `fixed inset-0` con backdrop. Mostrar la batalla dentro de La Tribuna (panel ya existe: "Mirá la batalla acá abajo") o como tarjeta con `pointer-events-none` en el wrapper. Autocerrar la vista del observador cuando el backend cierra la batalla.
- **Aceptación:** durante un ataque, defensor y espectador pueden usar mapa/tribuna/chat/reacciones; su vista de batalla se cierra sola al terminar.
- **Riesgo:** bajo; es contención de layout + condición por rol. Reusar el patrón no bloqueante ya usado antes.

## 2. DEF-02 — Transparencia del monto de la apuesta de refuerzos (CRITICAL a verificar / P1)
- **Qué:** alinear la etiqueta del control con el `amount` real enviado en `turn.wager`; mostrar el monto acumulado arriesgado y el pago potencial. Verificar que el pool baje exactamente ese monto y que el toast lo reporte.
- **Aceptación:** botón y toast reportan el mismo número; victoria paga el doble de ese número.
- **Riesgo:** bajo; corrección de UI + verificación del payload.

## 3. DEF-03 — HUD en colocación simultánea (MINOR / P2)
- **Qué:** durante `placement_*`, no marcar "JUEGA" a un solo jugador; indicar "colocación simultánea" o progreso por jugador.
- **Aceptación:** ningún jugador cree que "es turno de X" durante la colocación simultánea.
- **Riesgo:** muy bajo.

## 4. DEF-04 — Colisión nombre/insignia en el mapa (MINOR / P2)
- **Qué:** resolución de colisiones o reubicación de labels/badges en países chicos/adyacentes.
- **Aceptación:** en 1920 y 1366 ningún nombre queda tapado.
- **Riesgo:** medio (ajuste de layout SVG).

## 5. DEF-05 — Mapa en mobile (MAJOR-mobile / P2)
- **Qué:** si mobile es objetivo, agregar zoom/paneo o vista táctil dedicada.
- **Aceptación:** en 390px se selecciona cualquier país y se usa el radial cómodamente.
- **Riesgo:** medio-alto; depende de si mobile es prioridad (target actual: desktop + Discord).

## Observación de diseño (no defecto)
- Combate defensor-favorable hace fracasar muchos ataques. Si el ritmo se siente lento, considerar (con cuidado de no romper identidad TEG) incentivos de agresión o feedback de "por qué no rompiste" — pero **no** tocar la regla del empate sin decisión de diseño explícita.

## Fuera de alcance hasta desplegar el ledger
- Todo el **mercado de espectadores con monedas** (saldo, payout, odds, historial, ranking, anti-doble-pago, no-saldo-negativo, no-falsificable). Testear en profundidad cuando el backend autoritativo esté desplegado.
