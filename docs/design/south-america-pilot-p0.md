# 🗺️ P0 MAPA: Entregable Región Piloto América del Sur
> **Director Creativo, Lead Game UI/UX Designer & Director de Arte**  
> *Versión 2.2.0 — Especificación Técnica y Demostración en 4 Capas de América del Sur*

---

## 1. Tabla de Preservación de IDs de América del Sur (100% IDs Conservados)

Todos los IDs de territorio del contrato original de TEG-LOPDA han sido **100% conservados sin modificaciones ni reescrituras**:

| Nombre del País | ID Técnico Original Conservado | Antiguo ID | Nuevo ID | Estado |
| :--- | :--- | :--- | :--- | :--- |
| **Argentina** | `territory-south-america-argentina` | `territory-south-america-argentina` | `territory-south-america-argentina` | ✅ SIN CAMBIOS |
| **Brasil** | `territory-south-america-brazil` | `territory-south-america-brazil` | `territory-south-america-brazil` | ✅ SIN CAMBIOS |
| **Chile** | `territory-south-america-chile` | `territory-south-america-chile` | `territory-south-america-chile` | ✅ SIN CAMBIOS |
| **Colombia** | `territory-south-america-colombia` | `territory-south-america-colombia` | `territory-south-america-colombia` | ✅ SIN CAMBIOS |
| **Perú** | `territory-south-america-peru` | `territory-south-america-peru` | `territory-south-america-peru` | ✅ SIN CAMBIOS |
| **Bolivia** | `territory-south-america-bolivia` | `territory-south-america-bolivia` | `territory-south-america-bolivia` | ✅ SIN CAMBIOS |
| **Uruguay** | `territory-south-america-uruguay` | `territory-south-america-uruguay` | `territory-south-america-uruguay` | ✅ SIN CAMBIOS |
| **Venezuela** | `territory-south-america-venezuela` | `territory-south-america-venezuela` | `territory-south-america-venezuela` | ✅ SIN CAMBIOS |

*Total de IDs modificados*: **0**. Se preserva la compatibilidad programática absoluta con el motor backend y el estado del juego.

---

## 2. Definición del Sistema de 4 Capas Independientes

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       ARQUITECTURA DE LAS 4 CAPAS                           │
├─────────────────────────────────────────────────────────────────────────────┤
│ CAPA 4: OVERLAYS DE ETIQUETAS, BADGES Y FLECHA DE ATAQUE                    │
│ - <text class="territory-label"> en tercio superior de territorio           │
│ - <g class="army-badge"> con número gigante en tercio inferior              │
│ - <path class="vector-arrow"> para flecha animada América del Sur ➔ África  │
├─────────────────────────────────────────────────────────────────────────────┤
│ CAPA 3: HITBOXES INVISIBLES DE INTERACCIÓN                                  │
│ - <path class="hitbox-path"> fill: transparent, stroke: transparent         │
│ - pointer-events: all para capturar hovers y drag-and-drop                  │
├─────────────────────────────────────────────────────────────────────────────┤
│ CAPA 2: TERRITORIOS SVG JUGABLES ILUMINADOS                                 │
│ - Un <path class="territory"> por país con stroke brillante por jugador     │
│ - Relleno interior sutil (fill-opacity: 0.22) sin manchas planas            │
├─────────────────────────────────────────────────────────────────────────────┤
│ CAPA 1: BASE GEOGRÁFICA Y OCÉANO NO INTERACTIVO                             │
│ - Fondo marino (#091b30), relieve topográfico y retícula submarina sutil    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Disposición de Etiquetas vs Badges de Tropas (Sin Colisiones)

* **Etiquetas de Nombre (`.territory-label`)**: Ubicadas estrictamente en el **tercio superior** del polígono territorial.
* **Badges de Ejércitos (`.badge-circle` + `.badge-text`)**: Ubicados estrictamente en el **tercio inferior** del territorio.
* **Resultado**: Distancia vertical mínima de 50px entre el texto de nombre y la ficha de ejércitos, impidiendo cualquier solapamiento o choque en pantallas 1920x1080 o 1366x768.

---

## 4. Estado de Propiedad de 6 Jugadores Simultáneos en América del Sur

| Territorio | Jugador Ocupante | Color Hex | Borde (`stroke`) | Opacidad Relleno |
| :--- | :--- | :--- | :--- | :--- |
| **Argentina** | Jugador León (Rojo) | `#ef4444` | Stroke 8px + Pulse Dorado | 22% (Topografía visible) |
| **Brasil** | Jugador Águila (Azul) | `#3b82f6` | Stroke 6px + Resplandor | 22% (Topografía visible) |
| **Perú / Uruguay** | Jugador Elefante (Verde) | `#10b981` | Stroke 6px + Resplandor | 22% (Topografía visible) |
| **Colombia / Chile**| Jugador Sol (Amarillo) | `#eab308` | Stroke 6px + Resplandor | 22% (Topografía visible) |
| **Bolivia** | Jugador Dragón (Púrpura) | `#a855f7` | Stroke 6px + Resplandor | 22% (Topografía visible) |
| **Venezuela** | Jugador Tridente (Cian) | `#06b6d4` | Stroke 6px + Resplandor | 22% (Topografía visible) |

---

## 5. Prototipo de Validación Navegable

Acceso directo a la prueba interactiva del piloto:
👉 [`frontend/public/prototype/south-america-pilot.html`](file:///home/ndf/workspace/TEG-LOPDA/frontend/public/prototype/south-america-pilot.html)
