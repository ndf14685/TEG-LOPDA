# Mapeo: eventos del backend ↔ contrato de Dirección de Arte

`assets/contracts/event-schema.json` define enums en MAYÚSCULAS para la capa
visual. El contrato canónico del WebSocket usa dot-notation
(`event-envelope.schema.json`). Correspondencia:

| Dirección de Arte | Evento WebSocket canónico | Notas |
|---|---|---|
| `DICE_ROLL_RESULT` | `dice.rolled` | `payload.dice` ordenado desc |
| `TERRITORY_CONQUERED` | `territory.conquered` | pendiente de mapa (TODO teg-rules); `payload.territory_id` usará los IDs estrictos del SVG (`territory-<continente>-<pais>`) |
| `ATTACK_FAILED` | `attack.resolved` | "falló" = `defender_losses < attacker_losses` o sin conquista; el frontend deriva la representación |
| `PLAYER_ELIMINATED` | `player.eliminated` | pendiente de mapa |
| `ALLIANCE_BROKEN` | — | sin evento aún; se agregará `alliance.broken` con las alianzas (TODO teg-rules) |

Bardos visuales (`taunts-manifest.json`, ids `bardo_*`): son distintos de los
audios dirigidos de `taunt.triggered` (`audio_asset_id`). Cuando el backend
emita eventos con carga visual incluirá `payload.taunt_id` opcional
referenciando `assets/manifest/taunts-manifest.json`. TODO(art-taunts):
definir qué eventos disparan cada bardo (ej. `ALLIANCE_BROKEN` → `bardo_traicion`).

`game_mode` y `map_assets` (contrato `game-init-schema.json`) viajan en:
`game.created`, `game.snapshot`, `GET/POST /api/join/{code}/{token}`.
