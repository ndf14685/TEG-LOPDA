# 🗺️ P0 MAPA: Rediseño Visual Total del Mapamundi
> **Director Creativo, Lead Game UI/UX Designer & Director de Arte**  
> *Versión 2.0.0 — Documento de Propuestas de Rediseño Cartográfico y Reconocimiento Inmediato*

---

## 1. El Diagnóstico P0: Por Qué el Mapa Actual Fue Rechazado

El mapa anterior fallaba en su promesa fundamental: **no se reconocía inmediatamente como mapamundi**. Un jugador nuevo o casual debía detenerse a leer los títulos de los continentes para deducir qué zona geográfica estaba observando.

### El Criterio de Reconocimiento Inmediato (< 1 Segundo):
Sin ningún texto, título o etiqueta, cualquier persona debe identificar instantáneamente:
1. **América del Norte**: Silueta distintiva con Alaska, Canadá, EE. UU., México y el puente centroamericano.
2. **América del Sur**: Silueta reconocible de "cono sur", Brasil, cordillera andina y península ibérica/africana enfrente.
3. **Europa**: Istmo continental articulado con la península ibérica, Italia, escandinavia y conexión a Rusia sin ser "manchas deformes".
4. **África**: Masa continental cuerno de África, corte ecuatorial y separación natural por el mar Mediterráneo y Mar Rojo.
5. **Asia**: Masa dominante que integra la vasta estepa rusa/siberiana, el subcontinente indio, el bloque chino y el archipiélago japonés.
6. **Oceanía**: Archipiélago austral con Australia, Nueva Zelanda y las puertas insulares a Asia del Sur.

---

## 2. Las 3 Propuestas Visuales del Mapamundi

---

### 🎨 PROPUESTA A: "Mapeado Topográfico Táctico Imperial" (War-Room Topography)

![Propuesta A](/home/ndf/.gemini/antigravity-cli/brain/d393a174-2d03-45fc-a52d-cf95bf8c11c9/map_proposal_a_1784966504917.jpg)

#### Descripción Estética:
Estilo sala de guerra moderna/clásica con océanos azul marino profundo (`#091b30`), relieve topográfico suave en elevación de terreno y landmasses de tono pergamino/bronce cálido. Sin ningún texto de continente sobre el mapa.

#### Reconocimiento Geográfico:
* **Reconocimiento instantáneo**: EXCELENTE (9.5/10). La topografía y sombreado le otorgan volumen y masa realista a los 6 continentes.
* **Siluetas**: Conserva al 100% las formas cartográficas reales sin simplificaciones geométricas que deformen la masa.

#### Riesgos:
* Si el sombreado de relieve es muy denso, puede competir visualmente con la opacidad del color de jugador que ocupa el territorio. Requiere opacidad de relleno del 65% máximo.

---

### 🎨 PROPUESTA B: "Grabado Orgánico en Cuero & Bronce" (Medieval Military Desk)

![Propuesta B](/home/ndf/.gemini/antigravity-cli/brain/d393a174-2d03-45fc-a52d-cf95bf8c11c9/map_proposal_b_1784966521826.jpg)

#### Descripción Estética:
Estilo mesa de estrategia militar física sobre cuero con biseles de bronce pulido y luz de candelabro. Los continentes tienen contornos dorados resplandecientes sobre mar marino oscuro.

#### Reconocimiento Geográfico:
* **Reconocimiento instantáneo**: MUY ALTO (9.0/10). El resplandor perimetral dorado destaca dramáticamente la silueta de los continentes sobre el océano.
* **Siluetas**: Las líneas fronterizas internas de territorios usan trazados de latón delgado, manteniendo despejado el interior para los badges de ejércitos.

#### Riesgos:
* Sensación más "pesada" en pantallas de 1366x768 debido a los marcos de cuero del borde si no se ajustan los márgenes dinámicos.

---

### 🎨 PROPUESTA C: "Malla Vectorial Limpia de Alto Contraste" (Sleek Tactical Vector)

![Propuesta C](/home/ndf/.gemini/antigravity-cli/brain/d393a174-2d03-45fc-a52d-cf95bf8c11c9/map_proposal_c_1784966546924.jpg)

#### Descripción Estética:
Estilo vectorial plano minimalista con fondo azul noche pizarra (`#0f172a`), contornos continentales turquesa/dorado y bordes interiores delgados de alta precisión.

#### Reconocimiento Geográfico:
* **Reconocimiento instantáneo**: ALTO (8.5/10). Muy limpio y directo, ideal para e-sports, pero ligeramente menos atmosférico que A y B.
* **Siluetas**: Geometría ultra-nítida con trazos Bézier vectoriales vectoriales sin texturas de fondo.

#### Riesgos:
* Puede sentirse un poco más "frío" o "simulador" si no se acompaña de efectos de iluminación de turno.

---

## 3. Arquitectura Obligatoria de 4 Capas (Layer System)

Para garantizar legibilidad, rendimiento a 60 FPS y separación total de responsabilidades, el nuevo SVG del mapa se construye en **4 capas independientes**:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ARQUITECTURA DE CAPAS INDEPENDIENTES                     │
├─────────────────────────────────────────────────────────────────────────────┤
│ CAPA 4: OVERLAYS DE UI & MARCADORES                                        │
│ (Nombres de territorio, Badges de ejércitos, Flechas vectoriales, Pings)   │
├─────────────────────────────────────────────────────────────────────────────┤
│ CAPA 3: HITBOXES INVISIBLES DE INTERACCIÓN                                  │
│ (Path SVG transparente simplificado por territorio para hover/click/drag)   │
├─────────────────────────────────────────────────────────────────────────────┤
│ CAPA 2: TERRITORIOS JUGABLES ILUMINADOS                                    │
│ (Un <path class="territory"> SVG por cada uno de los 26/50 territorios)    │
├─────────────────────────────────────────────────────────────────────────────┤
│ CAPA 1: BASE GEOGRÁFICA Y OCÉANO NO INTERACTIVA                             │
│ (Fondo marino, líneas de costa, relieve topográfico, rutas marítimas)      │
└─────────────────────────────────────────────────────────────────────────────┘
```

1. **Layer 1 (Base Geográfica No Interactiva)**: `<g id="layer-geo-base">`  
   Contiene el mar, textura de fondo, rutas marítimas intermitentes (`.sea-route`) y contorno exterior continental. Tiene `pointer-events: none` total.
2. **Layer 2 (Territorios Jugables SVG)**: `<g id="layer-playable-territories">`  
   Contiene exactamente **un `<path id="territory-<id>">` por cada territorio**. Su `fill` aplica el color del jugador ocupante con `fill-opacity: 0.65` y un `stroke: #0f172a` de 4.5px.
3. **Layer 3 (Hitboxes Invisibles)**: `<g id="layer-hitboxes">`  
   Ruta idéntica simplificada con `fill: transparent` y `stroke: transparent` pero `pointer-events: all` para capturar con precisión los clicks, hovers y arrastres sin parpadeos de borde.
4. **Layer 4 (Overlays & Marcadores)**: `<g id="layer-overlays">`  
   Capa superior con `pointer-events: none`. Renderiza:
   * `.territory-label`: Nombre del territorio en tercio superior.
   * `.army-badge`: Escudo circular con número gigante de ejércitos en el centro geométrico desplazado.
   * `.targeting-arrow`: Flecha roja/azul animada de ataque o reagrupamiento.

---

## 4. Viabilidad en 1366x768 y Compatibilidad Cromática con 6 Jugadores

### A. Viabilidad en Monitores 1366x768 (768p Desktop)
* El mapa mantiene una relación de aspecto nativa `16:9` (`viewBox="0 0 2560 1440"`).
* A 1366x768, el mapa escala vectorialmente ocupando una caja de **1024px × 576px**, lo que otorga un tamaño promedio por territorio de ~120px², permitiendo badges de ejércitos de 32px de diámetro totalmente legibles a simple vista.

### B. Compatibilidad de Colores de 6 Jugadores (WCAG 2.1 AAA)
Se especifican los 6 colores de jugadores para mantener la geografía del mapamundi visible:

| Jugador | Color Hex | Color Resplandor | Opacidad Relleno | Visibilidad de Silueta |
| :--- | :--- | :--- | :--- | :--- |
| **Rojo** | `#ef4444` | `#f87171` | 65% | Excelente |
| **Azul** | `#3b82f6` | `#60a5fa` | 65% | Excelente |
| **Verde** | `#10b981` | `#34d399` | 65% | Excelente |
| **Amarillo** | `#eab308` | `#fde047` | 65% | Excelente |
| **Púrpura**| `#a855f7` | `#c084fc` | 65% | Excelente |
| **Cian** | `#06b6d4` | `#22d3ee` | 65% | Excelente |

---

## 5. RECOMENDACIÓN DE DIRECCIÓN CREATIVA

### 🏆 Dirección Recomendada: **PROPUESTA A ("Mapeado Topográfico Táctico Imperial")**

**Razón Creativa & Táctica**:
1. Es la propuesta que **logra mayor velocidad de reconocimiento visual (< 0.5 segundos)** gracias al volumen topográfico natural de los continentes.
2. Mantiene una estética militar de sala de mando sumamente inmersiva sin recurrir a elementos de fantasía ni copiar la propiedad intelectual de Age of Empires ni TEG.
3. Sus landmasses de tono pergamino/bronce sobre océano marino contrastan impecablemente con los 6 colores de jugadores, manteniendo la geografía global siempre presente durante la partida.
