# ⚔️ TEG LOPDA: Arena de Combate, Explicación Transparente y Control de Tirada
> **Director Creativo & Lead Game Designer**  
> *Versión 1.1.0 — Claridad Táctica, Desglose de Dados e Historial Acumulado*

---

## 1. Principio Fundamental: Claridad Táctica por Sobre el Espectáculo

El combate en **TEG LOPDA** debe transmitir tensión, pero **NUNCA a costa de ocultar las reglas, los cálculos o el resultado**. El jugador debe comprender exactamente por qué se tiraron determinada cantidad de dados, cómo se ordenaron, por qué el empate favorece al defensor y cuántas tropas le quedan a cada bando.

---

## 2. Desglose Transparente de Batalla (UI Panel de Combate)

Cada ronda de combate exhibe un panel de desglose matemático visible en todo momento:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            ARENA DE COMBATE 3D                              │
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

## 3. Reglas de Cálculo de Dados y Asignación Transparente

1. **Atacante**:
   * Puede tirar como máximo 3 dados.
   * `dados_atacante = min(tropas_disponibles - 1, 3)`.
   * *Ejemplo visible*: "Argentina tiene 16 tropas ➔ 15 disponibles para atacar ➔ Asignados 3 dados".
2. **Defensor**:
   * Puede tirar como máximo 3 dados.
   * `dados_defensor = min(tropas_en_territorio, 3)`.
   * *Ejemplo visible*: "Brasil tiene 4 tropas ➔ Asignados 3 dados".
3. **Resolución Par a Par**:
   * Se ordenan ambos conjuntos de dados descendentemente.
   * Se comparan `Pair 1 (Max vs Max)`, `Pair 2 (Mid vs Mid)`, `Pair 3 (Min vs Min)`.
   * **Regla del Empate**: Si `dado_atacante == dado_defensor`, la tropa la pierde el Atacante.

---

## 4. Controles de Velocidad y Accesibilidad (Fast-Forward & Low-Motion)

El panel de combate incluye un selector de velocidad accesible en la esquina inferior:
* **Modo 1x (Normal)**: Animación física 3D completa de dados rodando (1.2s).
* **Modo 2x (Rápido)**: Animación acelerada de 0.4s por tirada.
* **Modo Instantáneo ⚡**: Muestra el resultado de bajas e historial de forma inmediata sin esperas de física 3D (para jugadores experimentados).
* **Modo Animaciones Reducidas**: Desactiva sacudidas de pantalla (`ScreenShake`) e impactos de chispas según preferencias de accesibilidad.
