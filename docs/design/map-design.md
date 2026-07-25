# 🗺️ TEG LOPDA: Diseño del Mapa Táctico Tándem
> **Director de Arte & Lead UI/UX Designer**  
> *Versión 1.0.0 — Especificación Geográfica y Representación Visual*

---

## 1. El Mapa como Protagonista Táctico

El mapa es la pieza central de la experiencia y ocupa entre el **75% y 85% de la superficie útil de la pantalla**. No existen barras laterales rígidas que le resten espacio visual.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            MAPA TÁCTICO WORLD WAR                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│      [ AMÉRICA DEL NORTE ]                       [ EUROPA / ASIA ]          │
│        (Canadá: 4 tropas)                       (Rusia: 12 tropas)          │
│                 │                                      │                    │
│                 ▼                                      ▼                    │
│      [ AMÉRICA DEL SUR ] ═══════════════════► [ ÁFRICA ]                    │
│       (Argentina: 16)       Ruta Marítima     (Sáhara: 3)                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Capas Visuales del Mapa SVG

El mapa se construye en 5 capas SVG superpuestas:

1. **Capa 0: Océano y Grilla Táctica**:
   * Fondo radial `#0f2b48` a `#040a14` con retícula marina punteada.
2. **Capa 1: Rutas Marítimas (`.sea-route`)**:
   * Líneas intermitentes de alta visibilidad para conexiones marítimas (Canadá ↔ UK, Alaska ↔ Kamchatka, España ↔ Sáhara, China ↔ Japón ↔ Australia).
3. **Capa 2: Territorios (`.territory`)**:
   * Trazados orgánicos con curvas Bézier (`d="M ... C ... Z"`).
   * Relleno neutro oscuro (`rgba(30, 41, 59, 0.85)`). El color del jugador se aplica como opacidad de fill (`fill-opacity: 0.75`) manteniendo la textura de mapa militar de fondo.
   * Bordes gruesos metálicos (`stroke: #0f172a, stroke-width: 4.5px`).
4. **Capa 3: Nombres de Territorios (`.territory-label`)**:
   * Ubicados estrictamente en el **tercio superior** del país.
   * Tipografía gruesa con trazo de contorno oscuro (`paint-order: stroke`) para lectura impecable sobre cualquier color de jugador.
5. **Capa 4: Insignias de Ejércitos (`.army-badge`)**:
   * Ubicadas en el **centro geométrico desplazado hacia abajo** del territorio.
   * Escudo circular con borde del color del jugador y número gigante en alta resolución (`font-size: 46px, font-weight: 900`).

---

## 3. Estados Visuales de los Territorios

| Estado | Borde (`stroke`) | Relleno (`fill`) | Animación / Resplandor |
| :--- | :--- | :--- | :--- |
| **Normal** | `#0f172a` (4.5px) | Color de Propietario (75% opacity) | Ninguna |
| **Hover** | `#38bdf8` (5.0px) | Brillo 1.3x | Sombra brillante cian (`drop-shadow`) |
| **Seleccionado Origen** | `#0284c7` (5.5px) | Brillo 1.3x | Pulso azul táctico permanente |
| **Objetivo Ataque** | `#ef4444` (5.5px) | Brillo 1.4x | Trazo intermitente rojo (`dasharray 10 5`) |
| **En Peligro Fronterizo**| `#f97316` (5.0px) | Color Normal | Pulso naranja sutil si el vecino tiene 3x tropas |
