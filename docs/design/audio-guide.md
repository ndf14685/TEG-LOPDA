# 🔊 TEG LOPDA: Guía de Audio y Diseño Sonoro (SFX / Music)
> **Director de Audio & Sound Designer**  
> *Versión 1.0.0 — Inventario Sonoro y Reglas de Mezcla*

---

## 1. Filosofía del Diseño Sonoro

El audio en **TEG LOPDA** cumple una función táctica indispensable: **hacer que cada click se sienta pesado, informar eventos sin mirar el texto y elevar la tensión de las tiradas de dados**.

---

## 2. Inventario Maestro de Sonidos (Assets Nombra Normalizado)

| ID Sonoro | Nombre de Archivo | Categoría | Descripción Sonora |
| :--- | :--- | :--- | :--- |
| `audio.ui.hover.001` | `audio-ui-hover-001.ogg` | UI | Roce suave de papel militar / cuero. |
| `audio.ui.click.001` | `audio-ui-click-001.ogg` | UI | Choque metálico seco de gatillo / interruptor. |
| `audio.turn.start.001` | `audio-turn-start-001.ogg` | Turno | Clarín de guerra corto + toque de tambor. |
| `audio.troop.place.001` | `audio-troop-place-001.ogg` | Tropa | *Clank* pesado de ficha/escudo de bronce sobre mesa. |
| `audio.dice.roll.001` | `audio-dice-roll-001.ogg` | Combate | Dados de madera/marfil rodando en bandeja. |
| `audio.dice.impact.001` | `audio-dice-impact-001.ogg` | Combate | Impacto directo de dados al detenerse. |
| `audio.battle.clash.001` | `audio-battle-clash-001.ogg` | Combate | Choque de espadas y chispas. |
| `audio.territory.conquered.001` | `audio-territory-conquered-001.ogg` | Victoria | Corneta militar victoriosa. |
| `audio.pact.broken.001` | `audio-pact-broken-001.ogg` | Drama | Sonido dramático de daga apuñalando + cristal. |
| `audio.bet.won.001` | `audio-bet-won-001.ogg` | Tribuna | Tintineo de monedas virtuales cayendo en pozo. |

---

## 3. Canales de Control de Volumen Independientes

El reproductor de audio ofrece 4 canales independientes configurables por el usuario:
1. **SFX de Interfaz & Tablero**: Control de volumen de clicks, tropas y movimientos.
2. **Efectos de Combate & Dados**: Control de tiradas y colisiones de batalla.
3. **Soundboard & Bardeo Social**: Control de audios disparados por otros jugadores.
4. **Relator IA (Sintetizador & Subtítulos)**: Control de voz del relator.
