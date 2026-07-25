# 🎨 TEG LOPDA: Guía de Estilo Visual y Dirección de Arte
> **Director de Arte & Lead UI/UX Designer**  
> *Versión 1.0.0 — Manual de Identidad Visual y UI Tokens*

---

## 1. Identidad de Arte: "Sala de Mando Imperial"

La dirección de arte de **TEG LOPDA** evoca una mesa de guerra en la sala de mando de un estado mayor militar estilizado. Combina texturas de madera noble, cuero oscuro, herrajes de bronce y latón, pergaminos topográficos y estandartes heráldicos de alta visibilidad.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          PALETA CROMÁTICA PRINCIPAL                         │
├───────────────────┬───────────────────┬───────────────────┬─────────────────┤
│ Madera Noble      │ Cuero Militar     │ Bronce Imperial   │ Pergamino       │
│ #0f172a (Slate 900)│ #1e293b (Slate 800)│ #d97706 (Amber 600)│ #f8fafc (Slate 50)│
└───────────────────┴───────────────────┴───────────────────┴─────────────────┘
```

---

## 2. Paleta de Colores de Jugadores (Alta Visibilidad WCAG 2.1 AAA)

Cada jugador ocupa un estandarte y color distintivo de alta visibilidad militar:

| ID de Color | Nombre Visual | Hex Principal | Hex Resplandor | Banderín / Estandarte |
| :--- | :--- | :--- | :--- | :--- |
| `player-red` | Rojo Escarlata | `#ef4444` | `#f87171` | Estandarte del León |
| `player-blue` | Azul Cobalto | `#3b82f6` | `#60a5fa` | Estandarte del Águila |
| `player-green` | Verde Esmeralda | `#10b981` | `#34d399` | Estandarte del Dragón |
| `player-yellow` | Oro Imperial | `#eab308` | `#fde047` | Estandarte del Sol |
| `player-purple` | Púrpura Real | `#a855f7` | `#c084fc` | Estandarte de la Corona |
| `player-orange` | Naranja Fuego | `#f97316` | `#fb923c` | Estandarte del Fénix |
| `player-cyan` | Cian Táctico | `#06b6d4` | `#22d3ee` | Estandarte del Tridente |
| `player-magenta` | Rosa Carmesí | `#ec4899` | `#f472b6` | Estandarte de la Rosa |

---

## 3. Sistema Tipográfico

* **Titulares & Épica (Headings & Banner Titles)**: `Cinzel Decorative`, `Cinzel`, Serif de alto impacto.
* **UI Táctica & Fichas (Badges & Troops)**: `Outfit`, `Trebuchet MS`, Sans-Serif geométrica pesada (`900 Ultra-Bold`).
* **Lectura & Zócalo de Transmisión (Body & Subtitles)**: `Inter`, `system-ui`, Sans-Serif neutra de lectura rápida.

```css
/* Ejemplos de UI Tokens Tipográficos */
.font-display { font-family: 'Cinzel', serif; font-weight: 700; }
.font-tactical { font-family: 'Outfit', sans-serif; font-weight: 900; }
.font-body { font-family: 'Inter', sans-serif; font-weight: 400; }
```

---

## 4. Componentes Estilo "Mesa de Guerra"

### A. Marqués & Paneles Heráldicos
* **Fondo**: Gradient radial `#1e293b` a `#0f172a` con bisel metálico (`border: 2px solid #d97706`).
* **Sombras**: `box-shadow: 0 10px 30px -5px rgba(0, 0, 0, 0.8), inset 0 1px 0 rgba(255, 255, 255, 0.1)`.

### B. Botones de Acción Tactil (Juicy Buttons)
* **Estado Normal**: Gradiente de bronce/oro (`linear-gradient(180deg, #f59e0b, #d97706)`).
* **Estado Hover**: Resplandor exterior (`filter: drop-shadow(0 0 12px rgba(245, 158, 11, 0.6))`), elevación `translateY(-2px)`.
* **Estado Active (Click)**: Depresión `translateY(1px)`, sonido háptico de gatillo metálico.

---

## 5. Reglas Anti-Frustración Visual

1. **Prohibido el uso de selectores `<select>` en pantalla de juego.**
2. **Prohibido el uso de bordes planos monocromáticos sin relieve.**
3. **Prohibido ocultar el resultado de los combates en cajas de texto pequeñas.**
4. **Prohibido mostrar estados de error técnicos o trazas en la interfaz principal.**
