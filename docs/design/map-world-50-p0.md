# 🗺️ P0 MAPA: Entregable Mapamundi Completo (Modo 50 — 50 Territorios en 4 Capas)
> **Director Creativo, Lead Game UI/UX Designer & Director de Arte**  
> *Versión 3.1.0 — Geometría Realista Encastada Completa del Mundo (Contrato Técnico `data-territory` y Deslinde Total de Choques)*

---

## 1. Desglose Geográfico por Continente (Modo 50 — 50 Territorios)

Toda la masa terrestre global se compone de **50 territorios encastados** respetando sus bordes naturales, costas y topografía:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DISTRIBUCIÓN GLOBAL (50 TERRITORIOS)                     │
├─────────────────────────────────────────────────────────────────────────────┤
│ 🌎 AMÉRICA DEL SUR (8): Colombia, Venezuela, Perú, Brasil, Bolivia,         │
│                         Chile, Argentina, Uruguay.                          │
│ 🌎 AMÉRICA DEL NORTE (9): Alaska, Yukón, Canadá, Groenlandia, Terranova,     │
│                         Oregón, California, Nueva York, México.             │
│ 🌍 EUROPA (9): Islandia, Gran Bretaña, Suecia, España, Francia,             │
│                Alemania, Italia, Polonia, Rusia.                            │
│ 🌍 ÁFRICA (8): Sáhara, Egipto, Nigeria, Etiopía, Zaire, Kenia,              │
│                Sudáfrica, Madagascar.                                       │
│ 🌏 ASIA (12): Turquía, Arabia, Irán, Aral, Gobi, Siberia, Kamchatka,        │
│               Japón, India, China, Mongolia, Malasia.                       │
│ 🌏 OCEANÍA (4): Sumatra, Borneo, Java, Australia.                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

*Estado de IDs*: **100% de IDs conservados sin renombrar ni modificar** en los 50 territorios.

---

## 🏗️ 2. Especificación de las 4 Capas del Mapamundi

1. **Capa 1 (Base Geográfica y Océano No Interactivo)**: `<g id="layer-1-geo-base">`  
   Océano `#091b30`, retícula táctica submarina sutil y líneas de ruta marítima intercontinentales (`.sea-route`). `pointer-events: none`.
2. **Capa 2 (Territorios Jugables SVG)**: `<g id="layer-2-playable-territories">`  
   Exactamente **un `<path id="territory-<id>">` por cada uno de los 50 países**. Color de jugador con `fill-opacity: 0.22` + `stroke` brillante por jugador (`stroke-width: 6px`).
3. **Capa 3 (Hitboxes Invisibles Independientes con Contrato Técnico `data-territory`)**: `<g id="layer-3-hitboxes">`  
   Trazados independientes `<path class="territory-hitbox" data-territory="<territory-id>">` con `fill: transparent` y `stroke: transparent` con `pointer-events: all` para hovers, clicks y drag-and-drop con precisión de píxel. Firma estricta requerida por el contrato del Frontend.
4. **Capa 4 (Overlays de Etiquetas, Badges y Flechas Deslindados)**: `<g id="layer-4-overlays">`  
   Etiquetas de nombre (`.territory-label`) en tercio superior, insignias circulares con números gigantes de ejércitos (`.badge-group`) en tercio inferior y flechas vectoriales de ataque (`.vector-arrow`).

---

## 📱 3. Prototipo Interactivo Standalone del Mundo Completo

Acceso directo a la prueba interactiva del mapamundi completo de 50 territorios:
👉 **Prototipo Completo**: [`frontend/public/prototype/world-50-pilot.html`](file:///home/ndf/workspace/TEG-LOPDA/frontend/public/prototype/world-50-pilot.html)
👉 **Archivo SVG Base de Producción**: [`assets/maps/base/map-base-tactical-50-001.svg`](file:///home/ndf/workspace/TEG-LOPDA/assets/maps/base/map-base-tactical-50-001.svg)
👉 **Manifiesto JSON**: [`assets/manifests/map-world-50-manifest.json`](file:///home/ndf/workspace/TEG-LOPDA/assets/manifests/map-world-50-manifest.json)

**Funcionalidades de Validación**:
* Botón `🙈 Sin Etiquetas (<1s)`: Verificación de reconocibilidad geográfica instantánea de todos los continentes del mundo sin leer.
* Botones `🖥️ 1920x1080` vs `💻 1366x768`: Demostración de legibilidad responsive sin sobrecarga de marcos.
