# TEG LOPDA — Diseño del juego completo

**Fecha:** 2026-07-23
**Estado:** aprobado por secciones en sesión de brainstorming
**Objetivo:** juego web tipo TEG completamente funcional para 6–10 amigos por Discord, divertido desde la primera partida. Sin MVP, sin mocks, sin placeholders: cada sistema se termina antes de pasar al siguiente.

## Contexto: qué existe y qué no

Base sólida ya implementada y testeada (~3.2k LOC backend FastAPI + ~3.8k LOC frontend React 19):
lobby/salas, invitaciones por token (hash SHA-256, link único), turnos con fases
refuerzo→ataque→reagrupamiento, dados y combate server-side (empate favorece al defensor),
bonus de continente, conquista, eliminación automática, victoria por dominación, WS con
snapshot + `sequence_number` + reconexión con gracia de 30s, persistencia SQLite (WAL,
migraciones), taunts backend (`taunt_assets` + `TAUNT_TRIGGERED`), comentarista con
plantillas + integración Ollama opcional, 3 mapas validados (25/50/100 territorios).

Fachada o inexistente: objetivos secretos (modal con dato falso), tarjetas de país (modal
desconectado), estadísticas (trofeos asignados por índice de array), chat privado (backend
listo, sin UI), bot IA (solo tira dados y pasa), replay, assets de audio (directorios
vacíos → tonos sintéticos), perfiles persistentes.

Servidor: 12 cores, 19GB RAM, GPU NVIDIA, Ollama (qwen2.5:7b y otros), Claude CLI 2.1.218
con suscripción OAuth. **Disco al 96% (11GB libres)** — requiere límites de media y limpieza.

## Decisiones tomadas

| Tema | Decisión |
|---|---|
| Enfoque | **A: evolución incremental** sobre FastAPI+SQLite+WS actual. Nada de reescritura. |
| Reglas | **TEG canónico completo** adaptado a los mapas propios. |
| Comentarista | Cadena **Claude CLI (suscripción) → Ollama → plantillas**. Sin API paga. Nunca bloquea. |
| Identidad | **Perfiles persistentes** con link personal permanente, sin contraseña. |
| Replay | **Mapa paso a paso** sobre snapshots por turno + event log. |
| Pactos | Sistema liviano no vinculante; romperlos es evento público (drama + stats). |
| Colocación inicial | Simultánea y oculta (mejora sobre el TEG físico). |

## Arquitectura

Se mantiene: server autoritativo, azar solo server-side (`secrets.SystemRandom`), eventos
con envelope estable y `sequence_number` monotónico por partida, ruteo por visibilidad
(public/private/admin), snapshot completo al conectar, SQLite con migraciones versionadas.

Se agrega:

- **Patrón comando→eventos en el motor:** cada acción valida contra el estado, emite
  eventos con payload completo (suficiente para replay y stats) y actualiza el estado.
- **`legal_actions(jugador)`:** el motor expone las acciones válidas con parámetros
  (orígenes/destinos de ataque, canjes posibles, movimientos de fortify). Consumidores:
  UI (iluminar mapa, habilitar botones) y bot. Viaja como evento privado al jugador de turno.
- **`turn_snapshots(game_id, turn_number, state_json)`:** snapshot al inicio de cada
  turno. Base del replay; desacoplado del estado vivo (`games.state_json` sigue igual).
- **Media storage:** `data/media/` para audios grabados, con límites duros.

## Etapas de construcción

El juego queda jugable al final de cada etapa. No se avanza con una etapa incompleta.

### Etapa 0 — Saneamiento de infra
- Caddyfile: el edge debe servir el frontend nginx y dejar que éste proxee `/api`, `/ws`,
  `/health` (hoy proxya todo al backend y el frontend queda fuera).
- Cron de backup diario de `data/teg.db` (script `deploy/scripts/backup.sh` existe) con retención.
- Alerta/registro de espacio en disco; liberar espacio (el host está al 96%).

### Etapa 1 — Motor canónico completo
Máquina de estados: `LOBBY → READY → COLOCACION_1 (5 ejércitos) → COLOCACION_2 (3) →
TURNOS → TERMINADA`. Países repartidos al azar al iniciar. Colocación simultánea y oculta
con "listo" por jugador; se revela al completarse.

- **Refuerzos:** `max(3, países//2)` + bonus de continente completo + canje.
- **Tarjetas:** país + símbolo (barco/cañón/globo, comodines). 1 tarjeta por turno si se
  conquistó ≥1 país. Canje de 3 (iguales o las tres distintas; comodín libre): 4, 7, 10,
  luego +5 acumulativo. Tarjeta de país propio: +2 ejércitos en ese país (máx. 2 veces por
  tarjeta). Canje obligatorio con 5 en mano. Al eliminar un jugador se heredan sus tarjetas.
- **Objetivos secretos:** generador por mapa, tres familias: (a) conquistar N territorios,
  (b) dominar continentes específicos + países extra, (c) destruir a un jugador concreto
  (si lo elimina otro, muta a conquistar N territorios). Visibilidad privada. Verificación
  automática de todos los objetivos tras cada acción; al cumplirse: victoria + revelación.
  Dominación total sigue siendo victoria universal.
- **Acciones legales y snapshots por turno** (ver Arquitectura).
- **Errores:** acción inválida → evento `error` solo al actor; el motor nunca filtra
  excepciones al WS.
- **WS nuevo:** `placement.place`, `cards.trade`, `pact.propose/accept/break` (etapa 6),
  objetivo y mano de tarjetas en snapshot privado, evento de victoria con objetivo revelado.
- **Tests:** batería por regla (colocación, tabla de canje, herencia, mutación de objetivo,
  victoria por objetivo vs dominación) + partida completa simulada con 6 bots.

### Etapa 2 — Perfiles persistentes
- Tabla `profiles`: nickname, color favorito, avatar, token permanente (largo, aleatorio,
  regenerable). Link personal `…/p/{token}` asocia el navegador (localStorage).
- Invitar a partida = elegir perfiles del grupo; el jugador queda vinculado a su perfil.
- Stats históricas y audios cuelgan del perfil.

### Etapa 3 — Audios personalizados (feature principal)
- Config por perfil emisor → perfil rival → tipo de evento: conquista de país, eliminación,
  ataque fallido del rival, y saludo de inicio de partida (suena al arrancar cada partida).
- Grabación con micrófono desde el navegador (máx. 10 s) o subida de archivo. Formatos
  webm/opus y mp3. Límite de tamaño por archivo y cuota total por perfil (disco al 96%).
- Almacenamiento en `data/media/`, servido con auth de partida. Editable durante la partida.
- El disparo (`TAUNT_TRIGGERED`) y la cola con cooldown del frontend ya existen.
- Desbloqueo de audio del navegador integrado al flujo de entrada a la partida (gesto).

### Etapa 4 — Jugador IA razonable
- Consume `legal_actions`. Heurísticas: refuerza fronteras amenazadas, ataca con ventaja
  razonable, persigue su objetivo secreto (lo conoce), canjea cuando corresponde, reagrupa
  hacia frontera. Completa la colocación inicial.
- Asiento IA↔humano: ante abandono (offline prolongado o expulsión) el admin convierte el
  asiento a IA con un botón; si el jugador vuelve, recupera el asiento.

### Etapa 5 — Comentarista con cadena de proveedores
- `ClaudeCLICommentator` (subprocess `claude -p`, timeout corto) → `OllamaCommentator`
  (existe) → `MockCommentator` (plantillas, existe). Health-check al iniciar partida y
  degradación en caliente. La cola async existente garantiza que nunca bloquea; comentario
  que no llega a tiempo se descarta.
- Memoria de partida: hechos clave (traiciones, rachas, remontadas, eliminaciones) + últimas
  20 frases para anti-repetición, inyectados al prompt. Personalidad rioplatense, bardeo.
- Agresividad 1–4 configurable por partida (se desbloquea el nivel 4 hoy capado).
- Salida: panel + TTS del navegador (existen).

### Etapa 6 — Experiencia videojuego + pactos + chat privado
- Pack de sonidos real (CC0/generados): dados, combate, conquista, eliminación, victoria,
  clicks, notificaciones. `AudioService` con canales ya está listo.
- Efectos: partículas y transición de color al conquistar, animación de derrota, pantalla
  de victoria con confetti y objetivo revelado, dados 3D conectados al combate real,
  overlay de combate, vibración de botones, micro-transiciones.
- Zoom y paneo del mapa (rueda + arrastre + pinch).
- Mapa iluminado por `legal_actions` (desde dónde puedo atacar y hacia dónde).
- **Pactos:** proponer/aceptar/rechazar pacto de no agresión; romperlo o atacar al aliado
  es evento público → comentarista + audio + stats. No vinculante para el motor.
- **Chat privado UI:** selector de destinatario (backend ya rutea por visibilidad).

### Etapa 7 — Estadísticas reales
- Agregador al terminar la partida recorre el event log → `game_stats` (por partida) y
  `profile_stats` (acumulado histórico).
- Normales: conquistas, bajas infligidas/recibidas, países perdidos, % éxito atacando.
- Absurdas (calculadas de verdad): Rey del seis / Rey del uno (conteo de caras), Kamikaze
  (ataques perdidos atacando), Más traidor (pactos rotos + ataques a aliados), Más agresivo,
  Más defensivo, Vendehumo (pactos propuestos), Más llorón (emotes/soundboard tras perder),
  Más países perdidos, Alianzas rotas.
- Trofeos de la noche al final + ranking histórico del grupo.

### Etapa 8 — Replay paso a paso
- Página de partida terminada: mapa + línea de tiempo de turnos, avanzar/retroceder,
  auto-play con velocidad, detalle de dados por combate.
- Fuente: `turn_snapshots` + eventos. Acceso: participantes de la partida.

## Manejo de errores

- Toda acción inválida → evento `error` privado al actor (patrón existente `INVALID_ACTION`).
- Proveedores del comentarista: timeout → degradar escalón; nunca afecta el flujo del juego.
- Audio: asset faltante → fallback sintético existente; grabación que excede límites →
  rechazo con mensaje claro en la UI.
- Reconexión: snapshot completo al reconectar (existente); gap de secuencia → resync.
- Reinicio del server: engines se rehidratan de `games.state_json` on-demand (existente).

## Testing

- Motor: batería por regla canónica + partida completa 6 bots hasta victoria.
- Backend: tests de WS para mensajes nuevos (placement, cards, pactos), perfiles, media.
- Frontend: Vitest de stores y lógica (contratos zod, colas de audio, seq tracker — existen;
  se agregan los nuevos).
- e2e Playwright: partida corta real con 3 navegadores + bot, flujo de audios (config →
  disparo), retomar partida guardada, smoke de replay.

## Fuera de alcance (explícito)

- Cuentas con contraseña/OAuth de jugadores, matchmaking público, ranking entre grupos.
- Voz en vivo dentro del juego (el grupo usa Discord).
- API paga de LLM.
- Apps móviles nativas (el frontend es responsive en navegador).
