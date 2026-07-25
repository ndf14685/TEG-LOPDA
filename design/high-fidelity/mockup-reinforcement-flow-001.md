# 🎨 Mockup y Flujo Completo: Fase de Refuerzos (`mockup-reinforcement-flow-001`)
> **Director Creativo & Lead Game UI/UX Designer**  
> *Versión 1.0.0 — Flujo de Selección, Colocación y Confirmación de Tropas*

---

## 1. Diagrama de Flujo del Proceso

```
┌─────────────────┐    ┌──────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ 1. INICIO FASE  │───►│ 2. SELECCIÓN PAÍS│───►│ 3. SUMA TROPAS   │───►│ 4. CONFIRMACIÓN │
│ Refuerzos: 5    │    │ Click en Argentina│   │ +1, +3 o Máximo  │    │ Actualiza Mapa  │
└─────────────────┘    └──────────────────┘    └──────────────────┘    └─────────────────┘
```

---

## 2. Maquetación Visual del Flujo

```
PASO 1: Inicio Fase
  Banner: "🪖 FASE DE REFUERZOS: Te quedan 5 ejércitos por colocar"
  Visual: Todos los países propios parpadean en resplandor verde.

PASO 2: Selección de País
  Click sobre Argentina (16)
  Pop-up Radial flotante: [ 🪖 +1 ]  [ 🪖 +3 ]  [ 🪖 MÁX (5) ]

PASO 3: Suma de Tropas
  El jugador presiona "+3"
  Sonido Háptico: "Clank" de bronce.
  Efecto Visual: Animación de moneda/escudo cayendo en la insignia (16 ➔ 19).

PASO 4: Confirmación & Actualización
  El contador de refuerzos pendientes disminuye a 2.
  Cuando pendientes == 0, avanza automáticamente a Fase de Ataque.
