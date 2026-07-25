# 🎨 Mockup y Flujo Completo: La Tribuna & Apuestas (`mockup-tribune-flow-001`)
> **Director Creativo & Lead Game UI/UX Designer**  
> *Versión 1.0.0 — Flujo Autoritativo de Mercado, Solicitud, Ledger SQLite y Reembolso*

---

## 1. Diagrama de Flujo del Proceso

```
┌─────────────────┐    ┌──────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ 1. APERTURA     │───►│ 2. SOLICITUD     │───►│ 3. REGISTRO      │───►│ 4. BLOQUEO     │
│ Mercado Abierto │    │ Apostar 50 Moned.│    │ Ledger SQLite    │    │ Cierre Mercado  │
└─────────────────┘    └──────────────────┘    └──────────────────┘    └─────────────────┘
                                                                                │
┌─────────────────┐    ┌──────────────────┐                                     │
│ 6. GANANCIA /   │◄───│ 5. RESOLUCIÓN    │◄──────────────────────────────────────┘
│    REEMBOLSO    │    │ Resultado Tirada │
└─────────────────┘    └──────────────────┘
```

---

## 2. Maquetación Visual del Flujo de Apuestas

```
PASO 1: Mercado Abierto (bet.market.opened)
  Pop-up en La Tribuna: "¿Argentina (16) conquista Brasil (4)?"
  Opciones: [ SÍ (1.6x) ]  [ NO (2.4x) ] | Timer: 00:08s (Configurable)

PASO 2: Solicitud del Cliente (bet.request)
  El espectador presiona "APOSTAR SÍ (50 LOPDA)".

PASO 3: Validación Autoritativa & Registro en Ledger SQLite (bet.accepted)
  El servidor verifica saldo en Ledger SQLite, descuenta 50 Monedas y emite ticket:
  "✅ Apuesta Aceptada en Ledger SQLite | Saldo: 400 LOPDA"

PASO 4: Bloqueo de Mercado (bet.market.locked)
  Al expirar el tiempo o iniciar el rodado de dados, el mercado se bloquea.

PASO 5 & 6: Resolución o Reembolso (bet.market.resolved / cancelled)
  - Ganancia: Acredita +130 Monedas LOPDA en Ledger SQLite con sonido de victoria.
  - Reembolso: Si el combate se cancela, liquida `bet_refunded` reembolsando el 100% de las Monedas.
