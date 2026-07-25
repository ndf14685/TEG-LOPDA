# 🗺️ P0 MAPA: Prueba de Alta Fidelidad del Mapa Híbrido (A+B+C)
> **Director Creativo, Lead Game UI/UX Designer & Director de Arte**  
> *Versión 2.1.0 — Demostración de Dirección Híbrida A+B+C, Reconocimiento Instantáneo y 6 Jugadores Simultáneos*

---

## 1. Composición de la Dirección Híbrida A+B+C

Siguiendo la decisión de dirección visual de producto, se ha construido la especificación y prueba de alta fidelidad del **Mapa Híbrido Controlado**:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    COMPOSICIÓN DE LA DIRECCIÓN HÍBRIDA                      │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. GEOGRAFÍA Y BASE ──► PROPUESTA A (Imperial War-Room)                     │
│    - Océano azul marino profundo (#091b30).                                 │
│    - Continentes geográficamente reconocibles en menos de 1 segundo.        │
│    - Relieve topográfico sutil sin parches planos.                          │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2. MATERIALES Y HUD  ──► PROPUESTA B (Mesa de Mando Militar)                │
│    - Bronce, cuero y madera SOLAMENTE en HUD superior, badges y botones.    │
│    - CERO marcos pesados que le resten superficie útil al mapa.             │
├─────────────────────────────────────────────────────────────────────────────┤
│ 3. INTERACCIÓN Y UI ──► PROPUESTA C (Malla Vectorial Limpia)                │
│    - Trazados SVG independientes por territorio.                            │
│    - Capa de hitboxes invisibles para hovers y drag-and-drop.               │
│    - Indicadores de alto contraste (Territorio Seleccionado / Atacable).    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Reglas de Posesión Cromática de Jugadores (No Manchas Planas)

Para evitar que los colores de los 6 jugadores transformen el mapamundi en parches planos ilegibles:
1. **Relleno sin pintura sólida**: Se utiliza una opacidad de relleno sutil (`fill-opacity: 0.25`) combinada con el sombreado topográfico de fondo.
2. **Resplandor de Borde (`stroke`)**: Cada territorio comunica su propietario mediante un borde brillante del color de estandarte (`stroke-width: 6px` + `drop-shadow`).
3. **Escudo Heráldico (Badge)**: Badge circular en el centro geométrico con número gigante de tropas y borde del color del jugador.

---

## 3. Demostración en Resoluciones Nativas (1920x1080 y 1366x768)

* **Prototipo Interactivo Standalone**: Accesible en [`frontend/public/prototype/map-hybrid-proof.html`](file:///home/ndf/workspace/TEG-LOPDA/frontend/public/prototype/map-hybrid-proof.html).
* **Controles de Prueba**:
  * Botón `🏷️ Alternar Títulos de Continente`: Demuestra el criterio excluyente (los 6 continentes son 100% reconocibles en menos de 1 segundo sin etiquetas).
  * Botones `🖥️ 1920x1080` vs `💻 1366x768`: Demuestra que el mapa ocupa el 85% de superficie útil en ambas resoluciones sin sobrecarga de marcos de cuero.
