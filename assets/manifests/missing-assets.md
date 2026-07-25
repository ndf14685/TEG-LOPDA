# 📋 Inventario Real de Assets Generados vs Assets Faltantes

Este documento detalla el inventario de activos multimedia del proyecto **TEG LOPDA**, declarando únicamente como `READY` aquellos archivos que **existen físicamente en disco**.

---

## 1. Assets REALMENTE GENERADOS Y EXISTENTES EN DISCO (Ready)

| ID de Asset | Ruta del Archivo Físico | Formato | Estado | Uso en Aplicación |
| :--- | :--- | :--- | :--- | :--- |
| `map.world.tactical-50.001` | `assets/maps/base/map-base-tactical-50-001.svg` | SVG | ✅ READY | Malla vectorial táctica real de 26 territorios con curvas orgánicas y rutas marítimas. |
| `map.world.tactical-100.001` | `assets/maps/base/map-base-tactical-100-001.svg` | SVG | ✅ READY | Malla vectorial extendida de 100 territorios. |
| `brand.palette.001` | `assets/brand/palette/palette.json` | JSON | ✅ READY | Configuración de paleta de marca y 8 colores de jugadores WCAG. |
| `ui.button.attack.001` | `assets/ui/buttons/button-action-attack-001.svg` | SVG | ✅ READY | Bandeja/botón táctico de ataque. |
| `ui.button.fortify.001` | `assets/ui/buttons/button-action-fortify-001.svg` | SVG | ✅ READY | Bandeja/botón táctico de reagrupamiento. |
| `ui.panel.card.001` | `assets/ui/panels/panel-player-card-001.svg` | SVG | ✅ READY | Panel heráldico de tarjeta de jugador. |
| `achievement.banner.traitor-king.001` | `assets/achievements/banners/banner-achievement-traitor-king-001.svg` | SVG | ✅ READY | Estandarte de logro Rey Traidor. |
| `audio.ui.click.001` | `assets/audio/ui/sound-ui-click-001.wav` | WAV | ✅ READY | Efecto sonoro de click en interfaz. |
| `audio.ui.notify.001` | `assets/audio/ui/sound-notify-001.wav` | WAV | ✅ READY | Notificación sonora de interfaz. |
| `audio.ui.reinforce.001` | `assets/audio/ui/sound-reinforce-001.wav` | WAV | ✅ READY | Sonido de colocación de refuerzos. |
| `audio.dice.roll.001` | `assets/audio/dice/sound-dice-roll-001.wav` | WAV | ✅ READY | Sonido de tirada física de dados. |
| `audio.battle.clash.001` | `assets/audio/battles/sound-battle-clash-001.wav` | WAV | ✅ READY | Sonido de choque de espadas en batalla. |
| `audio.battle.win.001` | `assets/audio/battles/sound-battle-win-001.wav` | WAV | ✅ READY | Sonido de victoria en combate. |
| `audio.battle.lose.001` | `assets/audio/battles/sound-battle-lose-001.wav` | WAV | ✅ READY | Sonido de derrota en combate. |
| `audio.alerts.traitor.001` | `assets/audio/alerts/sound-alert-traitor-001.wav` | WAV | ✅ READY | Efecto sonoro dramático de traición. |
| `audio.alerts.player-eliminated.001` | `assets/audio/alerts/sound-player-eliminated-001.wav` | WAV | ✅ READY | Efecto sonoro de eliminación de jugador. |
| `audio.victory.fanfare.001` | `assets/audio/victory/sound-victory-fanfare-001.wav` | WAV | ✅ READY | Fanfarria de victoria de partida. |
| `audio.victory.defeat-sad.001` | `assets/audio/victory/sound-defeat-sad-001.wav` | WAV | ✅ READY | Marcha fúnebre de derrota final. |

---

## 2. Assets FALTANTES / PENDIENTES DE PRODUCCIÓN VISUAL (Planned / Missing)

| ID de Asset | Ruta Futura | Formato | Fallback Temporal |
| :--- | :--- | :--- | :--- |
| `background.game.war-table.001` | `assets/backgrounds/background-game-war-table-001.webp` | WEBP | Radial gradient CSS (`#0f2b48` a `#040a14`). |
| `animation.dice.roll-attack.001` | `assets/dice/animations/animation-dice-roll-attack-001.webm` | WEBM | Dados CSS 3D con animación keyframes. |
| `animation.bet.won.001` | `assets/betting/animations/animation-bet-won-001.webm` | WEBM | Partículas CSS flotantes de Monedas. |
| `avatar.commentator.mocking.001` | `assets/ai-commentator/avatars/avatar-commentator-mocking-001.webp` | WEBP | Icono emoji dinámico (`🎙️`, `🤡`, `🔥`). |

## Detectados en integración frontend productivo (2026-07-25)
- `assets/taunts/stamps/overlay-stamp-classified-001.webp`: referenciado por `assets/manifest/taunts-manifest.json`, el directorio está vacío. Fallback actual: sin stamp visual.
- `taunts-manifest.json` referencia audios `.ogg` (`sound-alert-traitor-001.ogg`, `sound-dice-fail-001.ogg`) que existen solo como `.wav` en `assets/audio/`. Fallback actual: tonos sintéticos del AudioService.
- Iconografía emoji (🪖⚔️🏟️ etc.): en navegadores sin fuente emoji renderiza como cuadros. Pendiente de Dirección de Arte: set de iconos SVG propios (`assets/ui/icons/`).
- Música de fondo: no existe ningún track; el canal `music` del AudioService queda listo esperando assets.
