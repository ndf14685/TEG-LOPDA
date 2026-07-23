# Contrato REST — TEG LOPDA v1.0.0

Base: `https://<dominio>` (interno: `http://127.0.0.1:8123`).
Errores: `{"detail": {"code": "<ERROR_CODE>", "message": "…"}}` (ver `error-codes.json`).

## Público

### GET /health
`200 {"status": "ok", "version": "0.1.0"}` — sin información sensible.

### GET /api/join/{code}/{token}
Resuelve un link personalizado sin unirse todavía.

```json
{
  "game": {"id": "…", "code": "x7k3q9mw", "name": "la-revancha", "status": "lobby"},
  "player": {"id": "…", "nickname": "Nessi", "role": "player", "color": null,
             "nickname_editable": true, "already_joined": false}
}
```

### POST /api/join/{code}/{token}
Body: `{"nickname": "opcional si nickname_editable"}`.
Confirma el ingreso (primera vez emite `player.joined`).

```json
{
  "game": {"id": "…", "code": "…", "name": "…", "status": "lobby"},
  "player": {"id": "…", "nickname": "…", "role": "player", "nickname_editable": true, "…": "…"},
  "ws_path": "/ws/x7k3q9mw"
}
```

Luego el cliente abre `wss://<dominio>/ws/{code}?token={token}`.

## Admin (header `X-Admin-Token: <TEG_ADMIN_TOKEN>`)

| Método | Ruta | Body | Resultado |
|---|---|---|---|
| POST | `/api/admin/games` | `{"name", "config"?}` | partida creada (estado `lobby`) |
| GET | `/api/admin/games` | — | listado |
| GET | `/api/admin/games/{id}` | — | partida + jugadores + presencia |
| GET | `/api/admin/games/{id}/events?after=0&limit=500` | — | historial |
| POST | `/api/admin/games/{id}/players` | `{"nickname", "role"?, "color"?, "nickname_editable"?}` | jugador + **token en claro (única vez)** + `join_url` |
| PATCH | `/api/admin/games/{id}/players/{pid}` | `{"nickname"?, "color"?, "avatar_asset_id"?}` | actualiza |
| POST | `/api/admin/games/{id}/players/{pid}/regenerate-token` | — | token nuevo + `join_url` |
| POST | `/api/admin/games/{id}/players/{pid}/kick` | — | revoca y desconecta |
| POST | `/api/admin/games/{id}/start` | — | inicia (`running`), sortea turnos |
| POST | `/api/admin/games/{id}/pause` / `resume` | — | pausa / reanuda |
| POST | `/api/admin/games/{id}/finish` | `{"winner_player_id"?}` | resumen final |
| POST | `/api/admin/games/{id}/cancel` | — | cancela |
| POST | `/api/admin/games/{id}/commentator` | `{"enabled"?, "humor_level"?, "muted"?}` | config comentarista |
| POST | `/api/admin/games/{id}/taunts` | `{"owner_player_id", "target_player_id", "event_type", "asset_id"}` | configura audio dirigido |

`config` de partida: `{"commentator_enabled": bool, "humor_level": 0-4,
"nickname_editable_default": bool}`. `humor_level` se recorta al máximo del
servidor (`TEG_HUMOR_LEVEL_MAX`, por defecto 3: el nivel 4 está deshabilitado).

Roles válidos al invitar: `admin`, `player`, `spectator`, `ai_player`
(`ai_player` no recibe link: juega el servidor).

### Ejemplo de creación completa

```bash
curl -s -X POST http://127.0.0.1:8123/api/admin/games \
  -H "X-Admin-Token: $TEG_ADMIN_TOKEN" -H "Content-Type: application/json" \
  -d '{"name": "la-revancha"}'

curl -s -X POST http://127.0.0.1:8123/api/admin/games/<GAME_ID>/players \
  -H "X-Admin-Token: $TEG_ADMIN_TOKEN" -H "Content-Type: application/json" \
  -d '{"nickname": "Nessi"}'
# => {"player": {...}, "token": "GUARDALO-AHORA", "join_url": "https://dominio/join/x7k3q9mw/GUARDALO-AHORA"}
```
