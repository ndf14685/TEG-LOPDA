# Estabilidad para 6-8 jugadores + mejoras de turno

Fecha: 2026-07-28
Estado: aprobado por el dueño del producto, pendiente de plan de implementación

## Contexto

El dueño reportó tres mejoras de jugabilidad y, por separado, un incidente real:
"nos conectamos 2 jugadores, un tercero no se conectó, y explotó por todos lados",
con la preocupación de que el juego no aguante 6-8 jugadores.

La investigación mostró que el incidente **no fue mala suerte ni saturación de la
máquina**: son dos defectos concretos del código, y ambos empeoran de forma no
lineal con la cantidad de jugadores. Por eso el trabajo se ordena en dos fases y
la estabilidad va primero.

Objetivo de escala: **8 jugadores humanos simultáneos** (`classic_26` declara
`max_players: 8` en `domain/modes.py:15-16`). Hoy el máximo jamás probado son
**2 conexiones WebSocket** (`backend/tests/test_game_flow.py:164-165`).

## Evidencia del incidente

Partida `wfqrwfrf` (`2f317625-384d-4224-bad8-23cd1285dc6e`), 2026-07-27 02:50.
Reconstruida cruzando `data/teg.db` (tabla `events`) con `data/playtest.db`
(tablas `playtest_incidents` / `playtest_occurrences`).

Tres jugadores invitados. **Gabi nunca completó el join** (`joined_at = NULL`) y
además recibió **el mismo color que Seba** (`red` ambos). La partida arrancó con 2.

```
02:50:00.894  seq 13  game.started          público
              seq 14  objective.assigned    PRIVADO → Seba
              seq 15  ai.comment.generated  público   ("3 valientes", eran 2)
              seq 16  objective.assigned    PRIVADO → Nes
              seq 17  placement.started     público
02:50:01.285  PLAY-003 CRÍTICO  Nes: "sequence gap at 15"
02:50:01.338  PLAY-004  backend 500: UNIQUE constraint failed: playtest_incidents.fingerprint
02:50:01.379  PLAY-005  Nes: WebSocket close:1005 (resync auto-inducido)
02:50:01.540  PLAY-006  Seba: unhandledrejection PLAYTEST_HTTP_500 (×2)
02:50:30 →    PLAY-001  pending-action-timeout cada 20 s, en ambos, indefinidamente
```

## Diagnóstico

### D1 — Desincronización garantizada en cada arranque de partida

`GameService.emit()` (`backend/src/teg_backend/application/game_service.py:129-132`)
asigna un `sequence_number` **global por partida** a todo evento con
`persisted=True`, sin mirar la visibilidad. `ConnectionManager.broadcast()`
(`backend/src/teg_backend/realtime/manager.py:78-93`) filtra los destinatarios con
`recipients_for()` (`manager.py:61-76`): un evento `PRIVATE` llega solo al actor,
al target y a los admins.

Resultado: **los eventos persistidos y privados consumen numeración que los demás
jugadores nunca reciben**. El cliente lo interpreta como pérdida de eventos.

`frontend/src/services/websocket/seqTracker.ts` documenta la invariante que el
backend viola, textualmente:

> "Trackea sequence_number de eventos PERSISTIDOS (monotónico ≥1 por partida).
> Los efímeros (snapshot, presence.changed, error) llegan con 0 y no se trackean."

Al detectar el hueco, `wsClient.handleMessage` (`wsClient.ts:129-144`) reporta
`desynchronization`, emite `sync.lost` y llama a `resync()`, que **cierra el socket**.
El `close:1005` de PLAY-005, 94 ms después del gap, es esa desconexión.

Emisiones persistidas no públicas hoy:

| Evento | Ubicación | Visibilidad | Cuándo |
|---|---|---|---|
| `objective.assigned` | `game_service.py:474-479` | PRIVATE, **uno por jugador** | al iniciar **cada** partida |
| `chat.message` privado | `game_service.py:749-753` | PRIVATE | cada susurro |
| `player.invited` | `game_service.py:348-354` | ADMIN | lobby |
| `token.regenerated` | `game_service.py:371-374` | ADMIN | admin |

Que `legal.actions` (`:512`), `placement.updated` (`:1004`) y `cards.hand` (`:1047`)
sí estén marcados efímeros confirma que la intención original era exactamente
evitar esto; estos cuatro quedaron fuera.

**Escala:** con N jugadores, cada cliente se saltea N-1 secuencias al arrancar.
Con 2 el hueco es de 2 y reconecta 1 cliente. **Con 8 el hueco es de 8 y los 8
clientes reconectan simultáneamente**, cada uno pidiendo un snapshot completo
(territorios + `map_adjacency` del mapa entero), mientras `start_game` todavía
retiene el lock de la partida. Cada susurro privado durante el juego repite el
patrón sobre los 6-7 no involucrados.

### D2 — El instrumento de playtest se realimenta hasta saturar

Tres defectos encadenados:

**a) El `pong` no cancela el temporizador de acción pendiente.**
`wsClient.send()` (`wsClient.ts:174-189`) arma un `setTimeout` de 8 s por **cada**
mensaje enviado, incluido el `ping` automático cada 20 s (`wsClient.ts:11,210`).
El servidor responde `{"type":"pong"}` (`realtime/ws.py:150-151`), pero
`handleMessage` retorna en `wsClient.ts:111` **antes** del `clearTimeout` de las
líneas 126-127, que solo corre tras validar un envelope de evento real.
⇒ en una partida por turnos, cada cliente inactivo genera un incidente falso cada
20 segundos. Registrado: `PLAY-001`, frecuencia **41**, todas con `"action": "ping"`
y `"connection": {"ws":"open","sync":"synced"}` — la conexión estaba sana.

**b) Anidamiento exponencial del payload.**
`playtestClient.reportTechnical()` (`playtestClient.ts:124-135`) arma un payload que
incluye `recent_errors`, y acto seguido **empuja una copia profunda de ese mismo
payload dentro de `this.errors`**. Cada incidente contiene a sus predecesores, que
ya contenían a los suyos. Tamaños reales de `payload_json`, duplicándose cada 20 s
(el intervalo del ping):

```
6.965 B → 13.951 → 27.923 → 55.867 → 116.225 → 232.471 → … → 882.851 B
```

Promedio medido en la base: **135.182 bytes por ocurrencia**; máximo **882.851**.
Correlato en disco: `data/playtest.db-wal` = 4,2 MB para 48 ocurrencias.

**c) Sin freno del lado servidor y con cascada de autorreporte.**
`playtest/service.py:212-218` aplica rate limit **solo** cuando
`error_type == "manual-report"`; los incidentes técnicos automáticos no tienen
throttle. `api/playtest.py:56-57` acota `screenshot_data_url` a 3 MB pero deja
`action_trail` y `recent_errors` como `list[dict]` sin límite. Y cuando el POST
falla, `playtestClient.ts:201` lanza dentro de un `void this.post(...)` sin
`.catch` ⇒ `unhandledrejection` ⇒ el handler vuelve a llamar `reportTechnical()`
⇒ otro POST. Eso es PLAY-006.

El commit `237d757` ("evitar saturacion durante partidas") eliminó el POST por
acción y agregó reintento ante `IntegrityError`, pero **no tocó ninguno de estos
tres caminos**: `PLAY-001` tiene `last_build = 237d757` y siguió duplicando
después del fix (4.857 → 9.735 → 19.491 → 39.003 B).

### D3 — El broadcast bloquea la partida entera

`manager.broadcast()` (`manager.py:88-90`) recorre los sockets con
`for ws in targets: await ws.send_json(payload)`: **secuencial, sin timeout, sin
backpressure**. Si el buffer de escritura de un socket se llena (red móvil, pestaña
suspendida, túnel lento), el `await` se suspende hasta que ese cliente drene.

Y `broadcast` se invoca desde `emit` (`game_service.py:135`), que corre **dentro
del lock de la partida** en prácticamente toda acción (`attack` `:833`,
`place_reinforcement` `:1051`, `fortify` `:1067`, `next_phase` `:1113`,
`end_turn` `:1133`, `place_initial` `:989`).

⇒ **el jugador con peor conexión marca el ritmo de los otros siete**, y como el
lock es FIFO, el octavo en la cola espera la suma de los siete anteriores. Nada
desconecta al cliente lento antes de los ~40 s del ping de uvicorn.

### D4 — Taunts de bienvenida O(n²) dentro del lock de arranque

`_after_emit` de `game.started` (`game_service.py:166-176`) recorre **todos los
pares ordenados** de jugadores sentados, y cada par hace un `find_profile_taunt` y,
si hay audio, un `emit()` persistido completo.

| Jugadores | Pares | Eventos | `send_json` |
|---|---|---|---|
| 3 | 6 | 6 | 18 |
| 8 | **56** | 56 | **448** |

Es O(n²) en pares × O(n) en destinatarios. Ocurre dentro del lock de `start_game`,
en el mismo instante en que los 8 clientes están reconectando por D1.

### D5 — La partida se traba si le toca a alguien ausente

No existe timeout de turno, detección de AFK ni skip: `grep -rniE
"turn_timeout|afk|idle_timeout|skip_turn|auto_skip"` sobre `backend/` devuelve cero.
`on_disconnect` (`game_service.py:685-712`) solo marca presencia y emite
`player.disconnected` tras 30 s de gracia; **no avanza el turno**. Con 8 personas
esto pasa seguro.

Agravante: un jugador que nunca hizo join queda "fantasma" (caso Gabi) y, como
`ACTIVE_STATUSES` incluye `RUNNING` (`game_service.py:34`), puede confirmar el join
con la partida ya empezada y quedar conectado sin territorios, sin objetivo y fuera
de `turn.order`, sin ningún evento que lo explique.

### D6 — Defectos menores confirmados

- **Colores duplicados**: `invite_player` (`game_service.py:305-343`) acepta el color
  del body sin validar unicidad. Con 8 jugadores la colisión es casi segura.
- **Sin tope de invitaciones**: el `max_players` se valida recién en `start_game`
  (`game_service.py:444-453`). Se pueden repartir 15 links y descubrirlo al arrancar.
- **Conteo de jugadores inconsistente**: `ai/commentator.py:205` no filtra por
  `joined_at`, a diferencia de `start_game`. De ahí el "3 valientes" con 2 jugadores.
- **`count` sin cota inferior**: `place_reinforcement` (`domain/engine.py:246-256`) no
  valida `count >= 1`; `realtime/ws.py:176` hace `int(payload.get("count", 1))` sin
  mínimo. Un `count` negativo restaría ejércitos y **sumaría** refuerzos.
- **`send()` arma el timer aunque el socket esté cerrado** (`wsClient.ts:176-189`):
  el mensaje se descarta en silencio y el incidente se genera igual.
- **Fugas**: `ConnectionManager.rooms` nunca se purga (`Room.is_empty()` existe en
  `manager.py:45` y no se llama desde ningún lado); `_locks`, `_seq_locks`,
  `_engines` y `_ai_tasks` crecen sin límite.

### D7 — Infraestructura

Verificado el 2026-07-28 sobre la máquina de despliegue:

- **El backend está caído hace 43 horas**: `Exited (137)` (SIGKILL), healthcheck en
  `unhealthy`. `OOMKilled: false` ⇒ agotó el grace period por defecto de 10 s de
  Docker; el `lifespan` (`main.py:72-75`) no alcanzó a cerrar las dos conexiones
  SQLite. Evidencia física: `teg.db-wal` = 4,1 MB y `playtest.db-wal` = 4,2 MB sin
  checkpoint desde el 27/07.
- **Disco al 98 %** (5,7 GB libres), **swap al 79 %**, 1,4 GB de RAM libre.
- **Contenedores sin límites** de memoria, CPU ni pids (`docker-compose.yml:8-29`).
- **La GPU está caída y nadie lo notó.** El módulo del kernel cargado es `580.159.03`
  y las librerías instaladas son `580.173.02`: un `apt upgrade` del driver sin
  reiniciar. Consecuencia medida: **Ollama corre 100 % en CPU** (`size_vram: 0` para
  `llama3.2:3b` y `qwen2.5:7b`). Afecta al proveedor `ollama` del relator, aunque en
  producción `.env` usa `mock`. Se arregla reiniciando; queda a cargo del dueño.
- **`frontend/nginx.conf:31-36`** —el nginx que realmente está en producción— hace el
  upgrade de WebSocket pero **no define `proxy_read_timeout`** ⇒ default 60 s. Solo
  el ping de 20 s lo mantiene vivo; con 3 pings de margen, cualquier bloqueo del
  event loop >60 s corta las 8 conexiones a la vez. El archivo que sí lo configura
  (`deploy/nginx/teg.conf.example:35`, 3600 s) no está en el camino de producción.
- **El rate limit REST es un balde único para toda la mesa**: `main.py:100` usa
  `request.client.host` y uvicorn corre sin `--proxy-headers`
  (`backend/Dockerfile:25`), con `frontend/nginx.conf:22-30` sin `X-Forwarded-For`.
  Los 240 req/min se reparten entre los 8 jugadores, no por jugador.
- **Un solo worker de uvicorn** — correcto y **obligatorio** por el estado en memoria,
  pero no está documentado en ningún lado: es una trampa para quien intente "escalar".
- Exposición pública vía **quick tunnel efímero de Cloudflare**, con la URL hardcodeada
  en `.env` (`TEG_PUBLIC_BASE_URL`, `TEG_CORS_ORIGINS`). Si `cloudflared` se reinicia,
  la URL cambia y todos los links de invitación y el CORS quedan rotos.

## Diseño — Fase 0: estabilidad (bloqueante)

### F0.1 Separar la secuencia pública de la persistencia

**Regla nueva:** el `sequence_number` que viaja al cliente numera únicamente el
stream que ese cliente **puede** recibir. Los eventos no públicos se siguen
persistiendo (el replay no se toca) pero se emiten por el cable con
`sequence_number = 0`, que es el valor que `SeqTracker` ya trata como efímero
(`seqTracker.ts:11`).

**Corrección sobre la primera redacción de este spec:** la idea inicial era dejar el
`sequence_number` en `NULL` para los eventos no públicos. Es inviable y además
dañino: la columna es `INTEGER NOT NULL` con `UNIQUE (game_id, sequence_number)`
(`backend/migrations/0001-initial.sql:38,46`), y `repo.get_events` filtra con
`sequence_number > ?` (`repository.py:274-277`), de modo que cualquier fila en NULL
desaparecería del replay en silencio.

El enfoque correcto es **dos contadores**:

- `sequence_number` — se mantiene tal cual: denso sobre **todos** los eventos
  persistidos, `NOT NULL`. Es el orden de almacenamiento y de replay. **No se toca
  nada de lo que ya existe.**
- `public_sequence` — columna nueva, denso sobre los eventos **públicos**
  únicamente, `NULL` para privados y de admin.

Lo que viaja al cliente en el campo `sequence_number` del envelope pasa a ser el
`public_sequence` cuando el evento es público, y `0` cuando no lo es. Así el stream
que ve cada cliente es denso y sin huecos, `SeqTracker` deja de disparar `gap`, y el
replay y el historial de admin siguen funcionando exactamente igual que hoy.

El objetivo secreto no se pierde con esto: además del evento privado, viaja en el
snapshot como `your_objective` (`game_service.py:628-674`), que es de donde lo toma
el cliente al (re)conectar.

Esto arregla D1 de raíz para los cuatro eventos de la tabla y para cualquier evento
privado futuro, sin tocar el cliente.

**Verificación:** test que arranca una partida de 8 jugadores por WebSocket y
comprueba que ningún cliente reporta `gap` y que ninguno reconecta.

### F0.2 Cortar la realimentación del instrumento de playtest

- `handleMessage` cancela los `pendingTimers` **también** al recibir `pong`
  (mover el `clearTimeout` antes del `return` de `wsClient.ts:111`).
- `send()` arma el temporizador **solo si el socket está `OPEN`**.
- `reportTechnical()` deja de anidar: lo que entra en `this.errors` es un resumen
  plano (`title`, `error_type`, `component`, timestamp), nunca el payload completo.
- El servidor acota: límite duro de tamaño de `action_trail` / `recent_errors` en
  `api/playtest.py`, y el rate limit de `playtest/service.py:212-218` pasa a aplicar
  a **todos** los `error_type`, no solo a `manual-report`.
- `this.post(...)` deja de propagar el rechazo (`.catch` explícito) para cortar la
  cascada `500 → unhandledrejection → nuevo reporte`.

### F0.3 Sacar el broadcast del lock y hacerlo tolerante

- `broadcast` pasa a envío **concurrente** (`asyncio.gather`) con **timeout por
  socket**. Un socket que no drena en el plazo se marca y se cierra; no frena a nadie.
- `emit` deja de hacer el broadcast dentro del lock de la partida: el lock protege
  la mutación del estado y la persistencia; el envío ocurre después de soltarlo.
- Tope de **3 conexiones simultáneas por jugador**, para que las pestañas duplicadas
  no multipliquen el fan-out. Al abrir la cuarta se cierra la más antigua, en lugar
  de rechazar la nueva: reconectar desde un dispositivo nuevo nunca debe fallar.

Valores concretos: timeout de envío por socket **5 s**; un socket que lo agota se
cierra con código de aplicación y el jugador entra en el flujo normal de reconexión.

### F0.4 Acotar el arranque de partida

El fan-out O(n²) de taunts de bienvenida (D4) se saca del camino crítico: deja de
correr dentro del lock de `start_game` y se limita a un único saludo por jugador en
lugar de uno por par. Con 8 jugadores pasa de 56 emisiones a 8.

### F0.5 Turno que no se traba

- Timeout de turno configurable, **default 180 s**, que corre solo mientras el
  jugador de turno está `offline`. Al vencer, el turno se salta con un evento público
  explicativo, para que la mesa entienda qué pasó. Un jugador conectado que se toma su
  tiempo **nunca** es salteado: el objetivo es destrabar ausencias, no apurar a nadie.
- Un jugador que nunca hizo join no puede confirmar el join con la partida en
  `RUNNING`: se le devuelve un error claro en lugar de dejarlo entrar como fantasma.

### F0.6 Higiene de lobby

- Color único por jugador, con asignación automática si no se especifica.
- `max_players` se valida **al invitar**, no recién al arrancar.
- `commentator.py:205` filtra por `joined_at`, igual que `start_game`.
- `place_reinforcement` valida `count >= 1` en el motor, no solo en el schema del
  cliente.

### F0.7 Configuración de despliegue

Solo edición de archivos del repo. **No se levantan servicios, no se borra nada del
disco, no se toca `.env`** — eso queda para el dueño.

- `frontend/nginx.conf`: `proxy_read_timeout` y `proxy_send_timeout` largos en
  `/ws/`; `X-Forwarded-For` / `X-Real-IP` en `/api/`.
- `backend/Dockerfile`: `--proxy-headers` y `--forwarded-allow-ips`, para que el rate
  limit REST sea por jugador y no un balde compartido. Comentario explícito de que
  **no se debe agregar `--workers`**.
- `docker-compose.yml`: `mem_limit`, `cpus`, `pids_limit` y `stop_grace_period`
  suficiente para un cierre limpio de SQLite.
- `PRAGMA synchronous=NORMAL` en `db.py` (seguro bajo WAL, elimina un fsync por commit).

### F0.8 Rehidratar los turnos de bot al arrancar

`GameService._ai_tasks` (`game_service.py:77`) vive solo en memoria y el `lifespan`
(`main.py:38-75`) no recorre las partidas activas al arrancar. Si el proceso se
reinicia mientras un bot está pensando, **nadie vuelve a agendar ese turno** y la
partida queda trabada para siempre: el estado se recupera de SQLite, pero la tarea
que debía moverlo no.

Esto importa especialmente por el flujo de trabajo real: el túnel de Cloudflare es
efímero y los links se regeneran en cada sesión de juego, lo que implica reiniciar el
backend. Al arrancar la sesión es inofensivo; **a mitad de sesión deja partidas
muertas**.

Al levantar, el backend recorre las partidas en `RUNNING` y, si el jugador de turno
es un `ai_player`, reagenda su turno.

### F0.9 La prueba que hoy no existe

Test de carga con **8 conexiones WebSocket simultáneas** que juegue una partida
completa y verifique: cero `sequence gap`, cero reconexiones no provocadas, y
latencia acotada de la acción más lenta. Es el criterio de aceptación de la Fase 0.

## Diseño — Fase 1: las tres mejoras

### F1.1 Deshacer refuerzos (borrador local + confirmar)

El borrador vive **solo en el cliente** (`gameStore`). El servidor no se entera hasta
que el jugador confirma; si se cae la conexión, el borrador se pierde y los refuerzos
siguen intactos en el servidor.

- El menú radial sigue igual (`+1 / +3 / MÁX`), pero la ficha entra al borrador y se
  pinta distinta (translúcida, contorno punteado) para que se vea que no es definitiva.
- `Deshacer` por país, `Deshacer todo`, `CONFIRMAR`.
- Comando nuevo `turn.commit_reinforcements` con `{placements: [{territory_id, count}]}`,
  validado de forma **atómica**: si un país falla, no se aplica nada.
- **Confirmación parcial permitida**: con 9 disponibles se pueden confirmar 5 y seguir.
- Se mantiene el salto automático a fase de ataque al llegar a 0, porque ahora es una
  decisión consciente y no un accidente.
- Se elimina `reinforceBatch` y los botones `x1/x5/Todas` de `TurnPhaseBar.tsx:127-149`:
  son código muerto, nadie los lee (el radial manda su propio `count`).

### F1.2 Previsión de refuerzos (de todos, con desglose)

El cálculo queda en el backend, en un solo lugar. Se extrae de
`calculate_reinforcements` (`engine.py:146-167`) una función **pura**
`preview_reinforcements(player_id)` que devuelve el desglose sin mutar nada — hoy esa
función hace `pop` de `pending_bonus` (`engine.py:148`), así que no se puede consultar
sin alterar el estado. La versión mutante pasa a apoyarse en la pura.

Viaja un bloque `forecasts` con, por jugador:
`{total, from_territories, from_continents: [{name, bonus}], from_wager}`.
Adjunto al `game.snapshot` y a los tres momentos en que cambia: `turn.started`,
`territory.conquered` y `wager.resolved`. Sin eventos nuevos ni tráfico extra.

Dónde se ve:
- Bloque fijo en `TribunePanel` con **tu** desglose completo, visible en todas las
  fases, no solo en refuerzos.
- Número simple `+N` por rival en `TopHud`, junto a `países · tropas`.

### F1.3 Voces numeradas (construido, apagado)

- Slots `1..42`, la misma cantidad y orden que los taunts de Age of Empires II, para
  poder soltar los archivos con su numeración original.
- Manifiesto nuevo `assets/taunts/voices/manifest.json`: `{slot, label, file, enabled}`.
  Se versiona con todos los `file: null`.
- **Interruptor maestro `VITE_VOICES_ENABLED`, apagado por defecto.** Con el flag
  apagado no aparece nada en la UI y el backend rechaza el comando.
- Disparo por tecla numérica o grilla. Comando nuevo `taunt.play` con `{slot}`. El
  servidor valida el slot, aplica **cooldown propio de 3 s por jugador** (hoy el único
  freno son 5 s en el cliente, evitables recargando) y reemite el `taunt.triggered`
  que ya existe.
- Toda la mitad receptora (cola secuencial `TauntQueue`, reproducción con fallback,
  toast) ya está hecha y testeada: se reutiliza sin cambios.

## Fuera de alcance

- El sistema de taunts personales por rival+evento (`TauntStudio`) no se toca.
- El manifiesto roto `assets/manifest/taunts-manifest.json` (apunta a `.ogg`
  inexistentes) queda como está; es un bug aparte.
- No se agrega deshacer a la colocación inicial 5+3, ni a ataques ni a reagrupes.
- No se generan ni se incluyen archivos de audio.
- No se ejecutan acciones sobre el servidor (levantar servicios, liberar disco,
  rotar el túnel): se documentan y las decide el dueño.

## Riesgos

- **Los contratos zod descartan campos no declarados.** Cada campo nuevo
  (`forecasts`, `placements`, `slot`) debe declararse en `shared/contracts` o el
  frontend lo tira en silencio. Ya hay comentarios en el repo sobre bugs previos por
  esto (`shared/contracts/src/ws-events.ts:42-43`).
- **Sacar el broadcast del lock cambia el orden observable de los eventos.** Hay que
  garantizar que el orden por partida se preserve, o el `SeqTracker` volverá a
  reportar huecos por otro motivo.
- **La máquina está al límite** (disco 98 %, swap 79 %). La Fase 0 reduce la carga
  del proceso, pero no libera disco; si el WAL no puede crecer, las escrituras fallan
  y el juego se detiene igual.

## Criterio de aceptación

Fase 0 se da por terminada cuando una partida de **8 conexiones WebSocket
simultáneas** llega a su fin sin un solo `sequence gap`, sin reconexiones no
provocadas y sin incidentes de `pending-action-timeout` con la conexión sana.

Fase 1 se da por terminada cuando, en esa misma partida de 8, se puede colocar y
deshacer refuerzos antes de confirmar, todos ven su previsión y la de los rivales, y
el sistema de voces sigue apagado sin afectar nada.
