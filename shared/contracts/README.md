# Contratos compartidos backend ↔ frontend

Versión actual de contratos: **1.0.0** (campo `schema_version` en cada evento).

## Versionado

- Cambios compatibles (agregar campos opcionales): bump menor (1.1.0). El
  frontend debe ignorar campos desconocidos.
- Cambios incompatibles (renombrar/quitar campos, cambiar semántica): bump
  mayor (2.0.0) y se anuncia en este archivo con guía de migración.
- El backend siempre emite `schema_version` en cada evento WebSocket.

## Índice

| Archivo | Contenido |
|---|---|
| `api/rest-api.md` | Contrato REST completo con ejemplos |
| `api/error-codes.json` | Códigos de error estables |
| `websocket/event-envelope.schema.json` | Sobre de todo evento servidor→cliente |
| `websocket/client-messages.schema.json` | Mensajes cliente→servidor |
| `websocket/events.md` | Catálogo de eventos con ejemplos JSON |
| `schemas/game.schema.json` | Entidad partida |
| `schemas/player.schema.json` | Entidad jugador (vista pública) |
| `schemas/ai-commentator-io.schema.json` | Entrada/salida del comentarista IA |
| `schemas/ai-player-io.schema.json` | Solicitud/respuesta del jugador IA |
| `assets/asset-manifest.schema.json` | Manifiesto de assets (audios, avatares) |
