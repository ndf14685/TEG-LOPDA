# Betting / Tribuna audit

## Modelos presentes
1. **Apuesta de refuerzos (por recursos, jugador activo)** — ACTIVA.
2. **Mercado de espectadores (monedas LOPDA)** — **BLOQUEADO a propósito**.

## Apuesta de refuerzos
- Ubicación: panel "APUESTA DE REFUERZOS" en La Tribuna + botón "Arriesgar" en la fase de refuerzos.
- Texto: "Arriesgá refuerzos: si conquistás al menos un país este turno, vuelven al doble el próximo. Solo el jugador de turno arriesga refuerzos."
- Prueba end-to-end: Daro arriesgó, cerró turno sin conquistar → toast "💸 Daro perdió la apuesta: se fue con 1 refuerzos". La resolución al cierre de turno funciona y es visible para todos.
- Elegibilidad correcta: solo el jugador activo puede arriesgar (los demás no ven el control).
- **Defecto DEF-02**: el botón decía "Arriesgar +3" pero el pool bajó solo 1 y el toast reportó 1. Monto no transparente / etiqueta no coincide.

## Mercado de espectadores (monedas)
- Estado: **BLOQUEADO** con etiqueta roja "BLOQUEADO" y explicación honesta:
  "Las apuestas entre espectadores con Monedas LOPDA (virtuales, sin valor real) se habilitan cuando el ledger autoritativo del backend esté desplegado. Hasta entonces no hay nada que apostar acá — la única apuesta activa es la de refuerzos de arriba."
- Evaluación: **correcto y prudente**. No expone saldo falsificable ni pagos sin ledger autoritativo. La restricción de "sin mecanismo de compra / odds visibles / resultado auditable" no puede evaluarse porque el mercado no está habilitado; el bloqueo con motivo es la respuesta adecuada por ahora.

## Checklist del brief (mercado de monedas) — no aplicable aún
- Saldo inicial / ganancia / pérdida / payout / reembolso / doble click / recarga en pago / desconexión / mercado cancelado / saldo insuficiente / doble request / historial / ranking → **N/A: mercado bloqueado**. Recomendado testear cuando se despliegue el ledger.

## Tribuna como experiencia de espera (resumen)
Ver `waiting-experience-audit.md`.

## Evidencia
`05-game-start-*`, `07-daro-reinforce-wager-1920.png`, `13-game-1366x768.png` (panel de tribuna con mercado bloqueado), toast de resolución en la instrumentación del cierre de turno.
