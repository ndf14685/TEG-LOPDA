# 📱 TEG LOPDA: Guía Responsive y Adaptación Multi-Pantalla
> **Lead UI/UX Designer**  
> *Versión 1.0.0 — Adaptación de Layout para Escritorio, Tablet y Mobile*

---

## 1. Prioridad de Plataforma: Escritorio Primero (Desktop-First)

**TEG LOPDA** está optimizado principalmente para monitores de escritorio (1920x1080, 1366x768, 2560x1440) donde la partida transcurre junto al canal de voz de Discord.

---

## 2. Layouts por Resolución

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          RESPONSIVE BREAKPOINTS                             │
├───────────────────┬───────────────────┬─────────────────────────────────────┤
│ 2560x1440 (2K)    │ 1920x1080 (FHD)   │ Mobile / Tablet (< 1024px)          │
├───────────────────┼───────────────────┼─────────────────────────────────────┤
│ Mapa 85% área     │ Mapa 80% área     │ Mapa 100% Pantalla                  │
│ HUD Flotante 3D   │ HUD Flotante 2D   │ Paneles laterales en Drawers        │
│ La Tribuna Fija   │ La Tribuna Fija   │ La Tribuna como Modal Desplegable   │
└───────────────────┴───────────────────┴─────────────────────────────────────┘
```

---

## 3. Estrategia Mobile & Tablet (Modo Tribuna/Acompañante)

En dispositivos móviles no se intenta apretar todos los paneles simultáneamente:
1. **Mapa a Pantalla Completa**: Ocupa el 100% de la pantalla táctil con soporte multitáctil (Pinch-to-zoom).
2. **La Tribuna Desplegable**: Deslizar hacia arriba desde el borde inferior revela el mercado de apuestas y el chat de bardeo rápido.
3. **Controles Táctiles Gigantes**: Los botones del Menú Radial se escalan a 64px mínimo para evitar errores de toque.
