# 🎰 TEG LOPDA: La Tribuna & Sistema Transaccional de Monedas LOPDA
> **Director Creativo & Lead Game Designer**  
> *Versión 1.1.0 — Economía Social, Ledger Transaccional y Mercado Autoritativo*

---

## 1. Arquitectura de Monedas LOPDA: Ledger Transaccional en SQLite

Las Monedas LOPDA **no existen únicamente en memoria volatil**. Para garantizar integridad, auditoría y persistencia frente a reconexiones o reinicios del servidor, la fuente de verdad es un **Ledger Transaccional en SQLite** (`player_lopda_ledger`). La memoria RAM del servidor actúa únicamente como caché de lectura rápida.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     FLUJO TRANSACCIONAL AUTORITATIVO                        │
├───────────────────────────────┬─────────────────────────────────────────────┤
│ 1. SOLICITUD DE APUESTA       │ El cliente solicita apostar N Monedas       │
│ 2. VALIDACIÓN AUTORITATIVA    │ El servidor verifica saldo en Ledger SQLite │
│ 3. REGISTRO EN LEDGER         │ Transacción SQL idempotente (Debit / Credit)│
│ 4. EMISIÓN DE TICKET          │ Evento `bet.accepted` o `bet.rejected`      │
└───────────────────────────────┴─────────────────────────────────────────────┘
```

### Tabla de Ledger (`player_lopda_ledger`):
* `transaction_id`: UUID único monotónico.
* `game_id`: ID de la partida.
* `player_id`: ID del apostador.
* `amount`: Cantidad (+ Crédito / - Débito).
* `type`: Type (`bet_placed`, `bet_won`, `bet_refunded`, `streak_bonus`, `bounty_claimed`).
* `market_id`: ID del mercado de predicción asociado.
* `created_at`: Timestamp ISO UTC.

---

## 2. Ciclo de Vida del Mercado de Apuestas (6 Estados Autoritativos)

El mercado de apuestas no es una simple animación de cliente; es una máquina de estados estricta en el servidor:

```
  [1. APERTURA] ──► [2. SOLICITUD] ──► [3. ACEPTACIÓN / RECHAZO]
                                                   │
  [6. REEMBOLSO] ◄── [5. RESOLUCIÓN] ◄── [4. BLOQUEO]
```

1. **Apertura (`bet.market.opened`)**: Se emite al declararse una batalla. El tiempo de apuesta es **configurable por el administrador** (default: 8 segundos; rango: 3s a 30s).
2. **Solicitud (`bet.request`)**: El cliente envía una propuesta de apuesta.
3. **Aceptación / Rechazo (`bet.accepted` / `bet.rejected`)**:
   * *Aceptada*: El servidor descuenta las monedas en el Ledger SQLite y confirma el ticket.
   * *Rechazada*: Si el jugador no tiene saldo suficiente o el mercado ya cerró, el server responde con motivo claro (`INSUFFICIENT_FUNDS`, `MARKET_CLOSED`).
4. **Bloqueo (`bet.market.locked`)**: Al expirar el tiempo configurable o iniciar el primer dado, no se aceptan más solicitudes.
5. **Resolución (`bet.market.resolved`)**: Al concluir el combate, el server calcula las cuotas del pozo acumulado y acredita las ganancias en el Ledger de los ganadores.
6. **Cancelación / Reembolso (`bet.market.cancelled`)**: Si el combate se cancela por retirada rápida o error de partida, el servidor ejecuta un reembolso automático (`bet_refunded`) del 100% de las monedas a todos los participantes.

---

## 3. Modo Clásico vs Modo Caos (Configurable)

* **Modo Clásico (Por Defecto)**:
  * Las Monedas LOPDA son 100% cosméticas y sociales. Se gastan en reacciones, audios y ranking.
* **Modo Caos (Opcional - Configurable por el Admin)**:
  * Permite transformar Monedas LOPDA en **Recursos Tácticos Limitados** con límites estrictos per-capita por ronda (ej: 1 tropa mercenaria por ronda a un costo de 300 Monedas, con validación transaccional en el Ledger).
