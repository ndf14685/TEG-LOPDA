# 🎨 Mockup y Arena de Combate 3D (`mockup-combat-arena-001`)
> **Director Creativo & Lead Game UI/UX Designer**  
> *Versión 1.0.0 — Desglose Matemático Transparente e Historial Acumulado*

---

## 1. Captura de Maquetación Visual (ASCII High-Fidelity Representation)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ⚔️ ARENA DE COMBATE 3D (DESGLOSE MATEMÁTICO TRANSPARENTE)                  │
├───────────────────────────────┬─────────────────────────────────────────────┤
│   🇦🇷 ARGENTINA (Atacante)     │             🇧🇷 BRASIL (Defensor)            │
│   Tropas Iniciales: 16        │             Tropas Iniciales: 4             │
│   Dados Asignados: 🎲 3       │             Dados Asignados: 🎲 3           │
│   (Razón: > 3 tropas en país) │             (Razón: Defiende con hasta 3)   │
├───────────────────────────────┴─────────────────────────────────────────────┤
│                                                                             │
│                  DESGLOSE DE PAREJAS (MAYOR A MENOR)                        │
│                                                                             │
│  [PAREJA 1] Dado Atacante 6  vs  Dado Defensor 6                            │
│             ► EMPATE: Regla del TEG favorece al Defensor                    │
│             ► Baja: Atacante pierde 1 tropa (Argentina 16 ➔ 15)             │
│                                                                             │
│  [PAREJA 2] Dado Atacante 5  vs  Dado Defensor 4                            │
│             ► Gana Atacante (5 > 4)                                         │
│             ► Baja: Defensor pierde 1 tropa (Brasil 4 ➔ 3)                  │
│                                                                             │
│  [PAREJA 3] Dado Atacante 3  vs  Dado Defensor 1                            │
│             ► Gana Atacante (3 > 1)                                         │
│             ► Baja: Defensor pierde 1 tropa (Brasil 3 ➔ 2)                  │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ RESUMEN ACUMULADO DE LA BATALLA:                                            │
│ - Argentina (Atacante): Iniciales 16 | Pérdidas Acumuladas -1 | Actuales: 15│
│ - Brasil (Defensor):    Iniciales 4  | Pérdidas Acumuladas -2 | Actuales: 2 │
├─────────────────────────────────────────────────────────────────────────────┤
│ VELOCIDAD: [ 1x ] [ 2x Fast ] [ Instantáneo ⚡ ] │ ANIMACIONES: [ Normal ]  │
├─────────────────────────────────────────────────────────────────────────────┤
│ [ ⚔️ SEGUIR ATACANDO ]                                     [ 🛑 DETENER ]   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Criterios de Aceptación y Desglose Transparente

1. **Explicación Transparente de Dados**: Muestra la razón exacta del número de dados asignados (ej. `> 3 tropas disponibles ➔ 3 dados`).
2. **Explicación del Empate**: Remarca de forma clara y visible cuando un dado empata que la regla autoritativa del TEG favorece al defensor.
3. **Resumen Acumulado de Batalla**: Indica las tropas iniciales de la batalla, las pérdidas acumuladas en todas las rondas y las tropas actuales resultantes.
4. **Controles de Velocidad**: Ofrece toggles para velocidad `1x`, `2x Fast` e `Instantáneo ⚡`.
