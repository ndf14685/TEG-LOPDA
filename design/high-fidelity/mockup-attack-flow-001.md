# 🎨 Mockup y Flujo Completo: Fase de Ataque (`mockup-attack-flow-001`)
> **Director Creativo & Lead Game UI/UX Designer**  
> *Versión 1.0.0 — Flujo de Puntería Vectorial, Declaración de Ataque e Invocación de Arena*

---

## 1. Diagrama de Flujo del Proceso

```
┌─────────────────┐    ┌──────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ 1. ORIGEN (>=2) │───►│ 2. DRAG / TARGET │───►│ 3. VALIDACIÓN    │───►│ 4. DISPARO ARENA│
│ Argentina (16)  │    │ Arrastre a Brasil│    │ 3 Dados vs 3     │    │ Modal 3D Abre   │
└─────────────────┘    └──────────────────┘    └──────────────────┘    └─────────────────┘
```

---

## 2. Maquetación Visual del Flujo

```
PASO 1: Selección Origen
  Click o Drag desde Argentina (16 tropas disponibles).

PASO 2: Vector Targeting (Arrastre de Puntería)
  Flecha roja animada sigue el movimiento del cursor hacia el país enemigo Brasil.

PASO 3: Validación Visual en Vivo
  Indicador sobre la flecha: "⚔️ Argentina (3 Dados) vs Brasil (3 Dados)".

PASO 4: Confirmación & Transición
  Al soltar el mouse sobre Brasil, el mapa se desenfoca y se abre el Modal de Arena de Combate 3D.
