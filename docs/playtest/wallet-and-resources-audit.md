# Wallet & resources audit

## Estado
El sistema de **monedas LOPDA / mercado de espectadores está BLOQUEADO** en la build desplegada, con explicación en pantalla: se habilita cuando el ledger autoritativo del backend esté desplegado.

## Consecuencia para el checklist del brief
No es posible (ni corresponde) probar aún: saldo inicial, ganancia, pérdida, payout, reembolso, doble click, recarga durante pago, desconexión en pago, mercado cancelado, saldo insuficiente, doble request, historial, ranking.

## Lo que sí puede afirmarse hoy
- No hay saldo expuesto ni pagos sin ledger → **no hay superficie para saldo negativo, doble pago ni saldo falsificable** porque la mecánica no está activa.
- No se observó mecanismo de compra de monedas (correcto: deben ser virtuales sin valor real).

## Recurso "por recursos" que SÍ existe
- La **apuesta de refuerzos** (jugador activo arriesga refuerzos, paga el doble si conquista). Auditada en `betting-audit.md`. Defecto DEF-02 (monto no transparente).

## Recomendación
Repetir este audit completo cuando se despliegue el ledger: verificar no-saldo-negativo, idempotencia de pagos (doble request), odds visibles, resultado auditable e imposibilidad de falsificar saldo desde el cliente.
