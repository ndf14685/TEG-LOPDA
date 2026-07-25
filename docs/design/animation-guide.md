# 🎬 TEG LOPDA: Guía de Animaciones y Efectos Visuales (VFX)
> **Lead Motion & VFX Designer**  
> *Versión 1.0.0 — Especificación de Animaciones y Motion Design*

---

## 1. Inventario Completo de Animaciones

Todas las animaciones de **TEG LOPDA** persiguen tres objetivos: **dar feedback táctil inmediato, crear suspenso y celebrar las victorias del jugador**.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       INVENTARIO DE ANIMACIONES REQUERIDAS                  │
├──────────────────┬──────────────────┬──────────────────┬────────────────────┤
│ Interfaz & Menú  │ Turno & Fases    │ Combate & Dados  │ Social & Apuestas  │
├──────────────────┼──────────────────┼──────────────────┼────────────────────┤
│ - Hover 3D Scale │ - Vignette Pulse │ - Tirada Dados3D │ - Lluvia Monedas   │
│ - Menú Radial Pop│ - Banner Turno   │ - Impacto Partíc.│ - Stamp de Bardeo  │
│ - Drag Targeting │ - Flujo Refuerzo │ - Flecha Fuego   │ - Fuego Racha      │
└──────────────────┴──────────────────┴──────────────────┴────────────────────┘
```

---

## 2. Definición Nomenclatura de Archivos y Eventos

| ID de Animación | Archivo | Duración | Descripción Motion |
| :--- | :--- | :--- | :--- |
| `animation.turn.banner.001` | `animation-turn-banner-001.webm` | 1500ms | Banner imperial cruza el mapa con sonido de clarín. |
| `animation.dice.roll.attack.001` | `animation-dice-roll-attack-001.webm` | 1200ms | Física de dados 3D rebotando en bandeja metálica. |
| `animation.territory.conquered.001` | `animation-territory-conquered-001.webm` | 1800ms | Estandarte clavándose en el país con destellos dorados. |
| `animation.bet.won.001` | `animation-bet-won-001.webm` | 1400ms | Lluvia de Monedas LOPDA explotando sobre La Tribuna. |
| `animation.pact.broken.001` | `animation-pact-broken-001.webm` | 2000ms | Pantalla en rojo carmesí con efecto de cristal roto. |

---

## 3. Parámetros de Performance (Motion Guidelines)

* **Curva Bezier Estándar**: `cubic-bezier(0.4, 0, 0.2, 1)` para transiciones suaves de interfaz.
* **Curva Spring / Elastic**: `cubic-bezier(0.68, -0.55, 0.265, 1.55)` para apariciones de menús y botones jugosos.
* **Target FPS**: 60 FPS garantizados mediante el uso exclusivo de `transform` y `opacity` en GPU.
