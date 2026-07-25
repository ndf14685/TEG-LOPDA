# 🎨 Mockup de Alta Fidelidad: Turno Propio (`mockup-turn-own-001`)
> **Director Creativo & Lead Game UI/UX Designer**  
> *Versión 1.0.0 — Representación Visual y Criterios de Aceptación del Turno Activo*

---

## 1. Captura de Maquetación Visual (ASCII High-Fidelity Representation)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🛡️ TEG LOPDA │ 🪖 TU TURNO (JUGADOR ROJO) │ FASE: ATAQUE ⚔️ │ 🪙 450 LOPDA   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│               [ CANADÁ (8) ] ───► ( LÍNEA MARÍTIMA ) ───► [ UK (3) ]         │
│                     │                                                       │
│                     ▼                                                       │
│            [ EE. UU. (12) ] ══════════════════════════════════╗              │
│                     │                                        ║              │
│                     ▼                                        ▼              │
│           ┌───────────────────┐               💥 [ BRASIL (4) ]             │
│           │ ARGENTINA (16) 🪖 │                  (DEFENSOR ROJO)            │
│           └─────────┬─────────┘                              ▲              │
│                     │                                        ║              │
│                     └═══════════════ VECTOR ═════════════════╝              │
│                                    TARGETING                                │
│                                 [ ⚔️ 3 DADOS vs 3 ]                         │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ 📜 CARTAS DE PAÍS | 🤝 ALIANZAS | 💬 LA TRIBUNA & APUESTAS (12 Abiertas)   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Criterios de Aceptación y Comportamiento Táctico

1. **Iluminación Ambiental (Vignette Pulse)**:
   * Al iniciar tu turno, la pantalla parpadea con un pulso dorado de 1.5 segundos.
   * Los bordes del viewport mantienen un resplandor discreto del color del jugador (`--player-red`).
2. **Resplandor de Territorios Propios**:
   * Todos los países de tu propiedad exhiben un borde con grosor aumentado de `4.5px` a `6px` y animación de elevación sutil al mover el cursor por encima.
3. **Ausencia de Formularios**:
   * No existen menús desplegables `<select>` ni cajas numéricas de input. La interacción con el mapa se realiza por menú radial o arrastre táctico directos.
