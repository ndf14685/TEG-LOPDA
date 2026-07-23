# Catálogo de eventos WebSocket

Todo evento usa el sobre de `event-envelope.schema.json`. Ejemplos con los
payloads reales que emite el backend.

## game.snapshot (efímero, al conectar)

```json
{
  "event_id": "3f2b7c9e-…",
  "event_type": "game.snapshot",
  "game_id": "b7e1…",
  "actor_id": null,
  "target_id": "player-id-que-conecta",
  "timestamp": "2026-07-22T20:00:00+00:00",
  "sequence_number": 0,
  "visibility": "private",
  "schema_version": "1.0.0",
  "persisted": false,
  "payload": {
    "game": {"id": "b7e1…", "code": "x7k3q9mw", "name": "la-revancha", "status": "lobby"},
    "you": "player-id-que-conecta",
    "players": [
      {"id": "p1", "nickname": "Nessi", "role": "player", "color": "red",
       "avatar_asset_id": null, "is_ready": true, "eliminated": false,
       "joined": true, "presence": "online"}
    ],
    "turn": null,
    "recent_events": []
  }
}
```

## player.joined

```json
{"event_type": "player.joined", "actor_id": "p2", "visibility": "public",
 "payload": {"player": {"id": "p2", "nickname": "Daro", "role": "player",
             "is_ready": false, "eliminated": false, "joined": true}}}
```

## player.ready

```json
{"event_type": "player.ready", "actor_id": "p2",
 "payload": {"ready": true, "all_ready": true, "game_status": "ready"}}
```

## presence.changed (efímero)

```json
{"event_type": "presence.changed", "actor_id": "p2",
 "payload": {"presence": "reconnecting"}, "persisted": false}
```

`presence`: `online` | `reconnecting` (gracia de 30 s) | `offline`.
Al pasar a `offline` se persiste además `player.disconnected`.

## game.started

```json
{"event_type": "game.started",
 "payload": {"turn_order": ["p2", "p1"], "players": [{"id": "p1", "…": "…"}]}}
```

## turn.started / turn.ended

```json
{"event_type": "turn.started", "actor_id": "p2", "payload": {"turn_number": 1}}
```

## dice.rolled

Dados generados SOLO en el servidor, ordenados de mayor a menor.

```json
{"event_type": "dice.rolled", "actor_id": "p2",
 "payload": {"dice": [6, 3, 1], "count": 3}}
```

## attack.started / attack.resolved

```json
{"event_type": "attack.resolved", "actor_id": "p1", "target_id": "p2",
 "payload": {"attacker_dice": [6, 4, 2], "defender_dice": [6, 3, 3],
             "attacker_losses": 1, "defender_losses": 2,
             "comparisons": [{"attacker": 6, "defender": 6},
                              {"attacker": 4, "defender": 3},
                              {"attacker": 2, "defender": 3}]}}
```

Empate favorece al defensor. `territory.conquered` y `player.eliminated`
se emitirán cuando exista el mapa con ejércitos (TODO teg-rules).

## chat.message

```json
{"event_type": "chat.message", "actor_id": "p1", "target_id": null,
 "visibility": "public", "payload": {"text": "hola sala"}}
```

Privado: `target_id` presente y `visibility: "private"` (lo reciben actor,
destinatario y admins conectados).

## taunt.triggered

```json
{"event_type": "taunt.triggered", "actor_id": "p1", "target_id": "p2",
 "payload": {"audio_asset_id": "audio/taunts/player-nessi/to-player-daro/attack-resolved-001.ogg",
             "source_event_type": "attack.resolved",
             "source_event_id": "…"}}
```

El frontend resuelve el `audio_asset_id` contra el manifiesto de assets y
reproduce el audio solo a quien corresponda.

## ai.comment.generated

```json
{"event_type": "ai.comment.generated", "visibility": "public",
 "payload": {"text": "Daro acaba de perder con tres dados contra uno. La estrategia todavía no fue localizada.",
             "emotion": "mocking", "audio_asset": null}}
```

## game.finished

```json
{"event_type": "game.finished", "target_id": "p1-o-null",
 "payload": {"turns_played": 12, "winner_player_id": "p1", "total_events": 240}}
```

## error (efímero, solo al causante)

```json
{"event_type": "error", "visibility": "private", "persisted": false,
 "payload": {"code": "NOT_YOUR_TURN", "message": "no es tu turno"}}
```
