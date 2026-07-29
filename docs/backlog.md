# Backlog y deudas técnicas

Última actualización: 2026-07-29, al cerrar la Fase 0 de estabilidad (merge `67b4e58`).

Este documento es curado a mano. El archivo `docs/playtest/backlog.md` se genera
automáticamente desde `data/playtest.db` y refleja incidentes crudos, no decisiones.

---

## Incidentes del playtest del 27/07 — todos resueltos

Los seis incidentes registrados en `data/playtest.db` durante la partida `wfqrwfrf`
quedaron cerrados por la Fase 0. Se dejan acá con su causa raíz real, porque el
título auto-generado no la refleja.

| Incidente | Causa raíz real | Resuelto en |
|---|---|---|
| PLAY-003 · Salto de sequence_number (CRITICAL) | `objective.assigned` se emitía persistido y privado; el `sequence_number` era global, así que consumía numeración que los demás jugadores nunca recibían y el cliente lo leía como pérdida de eventos | `e9d103f` — se separó `public_sequence` (densa solo sobre eventos públicos) de `sequence_number` (almacenamiento y replay) |
| PLAY-005 · WebSocket cerrado 1005 | Consecuencia de PLAY-003: al detectar el hueco, el cliente llamaba a `resync()` y cerraba el socket él mismo | `e9d103f` |
| PLAY-001 · Acción pendiente sin resolución: ping (frec. 41) | El `pong` no cancelaba el temporizador de 8 s porque `handleMessage` retornaba antes del `clearTimeout` | `ac5897c` — el clear se movió al inicio del método y cubre todos los caminos de retorno |
| PLAY-004 · Backend exception POST /api/playtest/incidents | Colisión de `fingerprint` bajo carga | Reintento agregado en `237d757`, más el throttle de `cea8a95` que baja el volumen |
| PLAY-006 · Unhandled promise rejection | El rechazo del POST se propagaba y el handler global volvía a llamar a `reportTechnical`, en cascada | `e8499bb` — `.catch()` explícito |
| PLAY-002 · WebSocket cerrado 1006 | No se pudo atribuir con la evidencia disponible (cierre anormal sin frame: túnel, proxy o servidor) | Sin causa confirmada; los mecanismos que lo hacían probable (tormenta de reconexiones, bloqueo del event loop) están mitigados |

**Causa del crecimiento de payloads** (6,9 KB → 882 KB duplicándose cada 20 s):
`reportTechnical` guardaba una copia profunda del payload completo dentro de
`recent_errors`, y ese payload ya contenía `recent_errors`. Resuelto en `e8499bb`.

---

## Pendiente: Fase 1 — las tres mejoras de jugabilidad

Diseño aprobado en `docs/superpowers/specs/2026-07-28-estabilidad-8-jugadores-y-mejoras-de-turno-design.md`.
No se empezó ninguna.

1. **Deshacer refuerzos.** Borrador local en `gameStore` con badge translúcido en el
   mapa, `Deshacer` por país, `Deshacer todo` y `CONFIRMAR`. Comando nuevo
   `turn.commit_reinforcements` validado de forma atómica. Confirmación parcial
   permitida. Se elimina `reinforceBatch` y los botones `x1/x5/Todas`, que son código
   muerto.
2. **Previsión de refuerzos con desglose.** Extraer de `calculate_reinforcements` una
   función pura `preview_reinforcements` (hoy hace `pop` de `pending_bonus`, así que no
   se puede consultar sin mutar). Bloque `forecasts` en el snapshot y en
   `turn.started` / `territory.conquered` / `wager.resolved`. Desglose propio en
   `TribunePanel`, número simple por rival en `TopHud`.
3. **Voces numeradas estilo Age of Empires.** Slots 1..42, manifiesto
   `assets/taunts/voices/manifest.json` con todos los `file: null`, flag
   `VITE_VOICES_ENABLED` **apagado por defecto**. Comando `taunt.play` con cooldown de
   3 s por jugador en el servidor. La mitad receptora (`TauntQueue`, reproducción,
   toast) ya existe y se reutiliza. **Los `.wav` los aporta el dueño.**

---

## Deudas de la Fase 0

Ordenadas por lo que más probablemente moleste jugando.

### Vale la pena antes de una sesión larga

- **`GET /events` trunca a 500 filas sin paginar.** Cualquier cliente que lea el log de
  una partida larga se pierde el cierre. Una partida de bots medida generó 634 eventos.
  Afecta al replay y al panel de admin, no al juego en vivo.
- **`fortify` no valida `count >= 1`.** `place_reinforcement` y `place_initial` sí lo
  hacen desde `000efef`, pero `fortify` quedó afuera: un `count` negativo mueve tropas
  al revés y puede dejar un territorio en 0. Requiere mandar un mensaje WS a mano.
  Arreglo de una línea.
- **`realtime/ws.py` no acota ninguno de sus cinco `int(payload.get(...))`.** Mismo
  vector que el anterior, un nivel más arriba.

### Trampas para el próximo que toque el código

- **`snapshot.recent_events` devuelve `sequence_number` de almacenamiento, no
  `public_sequence`.** Hoy no rompe porque el `SeqTracker` se re-ancla con el primer
  evento vivo, **pero el docstring de `seqTracker.reset()` documenta lo contrario**
  ("el último seq visto ancla el stream"). Quien implemente lo que ese docstring
  promete reintroduce el incidente del 27/07. Corregir el docstring es urgente aunque
  el fix pueda esperar.
- **El fan-out de saludos y `_vencer()` duplican la secuencia de cierre de turno.**
  `_vencer()` tiene su propia secuencia en vez de reusar `_cerrar_y_avanzar_turno`
  (decisión deliberada, para no tocar el camino normal de `end_turn`). Si se agrega un
  efecto nuevo al helper, hay que replicarlo. Hay un test de caja blanca que detecta la
  divergencia de orden, pero no la ausencia de un efecto nuevo.
- **El arreglo del salteo por ausencia depende de que el chequeo de sockets sea la
  última operación sincrónica antes de mutar el turno.** Meter un `await` ahí reabre la
  ventana. Está comentado en el código y cubierto por un test, pero no hay guardrail
  automático.
- **Docstring desactualizado** en `_cerrar_y_avanzar_turno`: dice que `_vencer` lo usa,
  y ya no.
- **Comentario desactualizado** en `shared/contracts/src/ws-events.ts:11`: dice que solo
  los eventos efímeros llevan `sequence_number` 0; ahora también los privados y de admin.

### Fugas y límites (irrelevantes en una sesión, relevantes en un proceso largo)

- `ConnectionManager.rooms` nunca se purga. `Room.is_empty()` existe y no tiene ningún
  call site.
- `_locks`, `_seq_locks`, `_engines`, `_send_queues` y `_send_workers` crecen sin límite
  por partida vista desde que arrancó el proceso. Ahora hay además un `Task` permanente
  por partida, porque se quitó el auto-apagado por inactividad del worker de envíos
  (era la causa de una carrera que perdía eventos).
- `SlidingWindowLimiter._hits` nunca llama a `cleanup()`.
- Falta `UNIQUE(game_id, public_sequence)` como defensa en profundidad. El lock ya
  impide colisiones a nivel aplicación.
- El backfill de la migración `0006` es O(n²) por partida (subconsulta correlacionada).
  Ya corrió; solo importa si se re-ejecuta sobre una base grande.

### Aristas conocidas, sin impacto verificado

- **El snapshot muestra a un jugador revocado si su rol es `ai_player`.** Echar un bot y
  sentar a alguien nuevo puede mostrar dos entradas del mismo color en la lista de
  jugadores. No afecta el mapa ni el motor.
- **`convert_seat_to_ai` durante la colocación inicial** deja una tarea de bot que
  `_restaurar_asiento_humano` no cancela (solo cancela si `stage == "turns"`). Inocua
  salvo una carrera muy fina.
- **Expulsar al jugador de turno** avanza el turno en el motor pero no emite
  `turn.started` ni `legal.actions` al nuevo jugador. Mitad preexistente, mitad
  agregada por la fase. Para un ausente se usa convertir a IA, que sí funciona bien.
- **La paleta tiene 10 colores** (`red, blue, green, yellow, purple, orange, cyan, pink,
  lime, white`), pero `classic_50` admite 10 jugadores y `mega_world_100` declara 20.
  Con `classic_26` (8 máximo) sobra margen. Con los otros modos hay que ampliarla.
- **La rehidratación al arrancar cubre `stage == "turns"`**, no un bot a mitad de
  colocación inicial.
- **`close()` del socket lento no tiene timeout** en el broadcast, a diferencia del
  `send_json`. Acotado en la práctica por el handshake de cierre de la librería.
- **`onStatus` replaya el estado sin el close code**, así que un suscriptor que se ate
  después de un cierre 4009 vería el mensaje de "revocado por el administrador". Hoy no
  se dispara porque hay un solo suscriptor real.
- **`websocket.reconnected` nunca se emite**: `onopen` hace `this.retries = 0` antes de
  leer `retries > 0`. Las reconexiones son invisibles en la instrumentación.
- **`send_to_player` no tiene callers.**
- **`MAX_SOCKETS_POR_JUGADOR`** es una constante fija, no configurable por `Settings`.
- **Al pasar `Room.sockets` de `set` a `list`** se perdió la unicidad por construcción.
  Hoy no es explotable (un solo call site), pero quedó sin guarda ni test.
- **`detener_gracias_de_reconexion` no limpia `room._offline_tasks`**, a diferencia de
  sus hermanas. Sin impacto: el proceso se está apagando.
- **El test de arranque de 8 jugadores no espera los `player.ready`** antes de arrancar
  la partida. Un `ready.set` que llegue después del `/start` genera un error que queda
  flotando en la cola de ese cliente. El test de partida completa sí espera.
- **`attack` sin `source_territory_id`/`target_territory_id` es aceptado en cualquier
  fase del turno**, no solo en `attack`.

---

## Operación e infraestructura

- **El túnel de Cloudflare es efímero por diseño.** Cada sesión de juego: levantar el
  túnel, poner la URL nueva en `.env` (`TEG_PUBLIC_BASE_URL` y `TEG_CORS_ORIGINS`) y
  reiniciar el backend. Vale automatizarlo en un script; hoy es manual y si el túnel se
  cae a mitad de sesión, todos los links de invitación mueren.
- **Nunca agregar `--workers` a uvicorn.** El estado del juego vive en memoria del
  proceso. Está comentado en el `Dockerfile` desde `6c3a666`.
- **`--forwarded-allow-ips '*'`** es correcto mientras el backend solo escuche detrás de
  nginx dentro de la red de Compose. Si algún día se expone directo, hay que
  restringirlo o cualquiera puede falsificar su IP y evadir el rate limit.
- **`PLAYTEST_MODE` y `PLAYTEST_UNTIL`** en `.env`: la ventana venció el 2026-07-28.
  Decidir si se reactiva para la próxima sesión.
- **`TEG_DEBUG_PAGE=true`** en producción expone `/dev`.
- **`TEG_DOMAIN`** en `.env` sigue con el placeholder `teg.example.com`.
- **Ambigüedad de ruta de base**: en Docker es `./data/teg.db`; por systemd sería
  `backend/data/teg.db`, que no existe. Arrancar por systemd después de haber usado
  Docker significa empezar con una base vacía.
- **El healthcheck del contenedor no reinicia nada.** El backend puede quedar
  `unhealthy` indefinidamente sin que nadie lo levante.

## Fuera del repo (máquina de despliegue)

- **Driver NVIDIA con mismatch**: módulo del kernel `580.159.03` contra librerías
  `580.173.02`. Consecuencia medida: **Ollama corriendo 100 % en CPU**. Se arregla
  reiniciando. Afecta a todo el stack local de IA, no solo al TEG.
- **Dos drivers instalados a la vez**, `nvidia-driver-550` y `nvidia-driver-580`.
  Conviene purgar el 550.
- **Unificar Whisper**: `whisper-venv-cuda` (5,8 GB) es superconjunto de `whisper-venv`
  (1,8 GB) — tiene `openai-whisper`, `faster-whisper` y `ctranslate2`, y su binario
  funciona sin GPU. Tras confirmar que CUDA levanta, borrar el de CPU y dejar
  `transcribe-audio-local.sh` siempre en el de CUDA, alternando solo `DEVICE`/`FP16`.
