# Defectos priorizados — TEG-LOPDA playtest (2026-07-25)

Clasificación P0/P1/P2 (fast-track) + severidad del marco (BLOCKER/CRITICAL/MAJOR/MINOR).
Evidencia en `artifacts/playtest/screenshots/`.

---

## DEF-01 — La Arena de Combate bloquea a defensor y espectador en cada ataque
- **ID:** DEF-01
- **Severidad:** MAJOR · **Prioridad:** P1
- **Contexto:** multijugador, durante un ataque
- **Jugador/es:** defensor (Nessi) y espectador (Tribu) — no solo el atacante
- **Fase:** Ataque
- **Pasos:**
  1. Daro (atacante) selecciona un país propio → ATACAR → elige país enemigo.
  2. Se abre la Arena de Combate.
  3. Observar las pantallas de Nessi (defensor) y Tribu (espectador).
- **Resultado observado:** los tres clientes reciben la Arena como **modal full-screen con backdrop** (`fixed inset-0 z-50 bg-war-950/85 backdrop-blur-sm`). Para el atacante hay "SEGUIR ATACANDO / DETENER"; para defensor y espectador el único control es "Cerrar", y **no autocierra**: quedan atrapados mirando el modal durante toda la batalla de otro, con el mapa, la tribuna, el chat y las reacciones tapados. Confirmado: tras varias rondas la Arena de Nessi seguía abierta.
- **Resultado esperado:** el jugador que NO ataca no debería quedar bloqueado por una acción ajena. Para observadores, la batalla debería mostrarse en un panel no bloqueante (p. ej. dentro de La Tribuna, que ya dice "Mirá la batalla acá abajo") o como toast/overlay con `pointer-events-none`, y autocerrarse al terminar la batalla.
- **Evidencia:** `09-combat-arena-daro-1920.png` (atacante), `10-nessi-during-battle-1920.png` (defensor), `10-tribu-during-battle-1920.png` (espectador), `11-daro-conquest-1920.png`.
- **Impacto funcional:** ninguno sobre el estado (se puede cerrar); no rompe la partida.
- **Impacto sobre comprensión:** positivo (el contenido es clarísimo), pero interrumpe.
- **Impacto sobre experiencia:** alto. En una partida con muchos ataques por turno, cada ataque secuestra la pantalla de todos. Es la misma clase de interrupción que ya se había resuelto antes con el overlay no bloqueante; la nueva Arena la reintrodujo para observadores.
- **Causa probable:** `frontend/src/components/combat/CombatArena.tsx` L99 renderiza `fixed inset-0 z-50 ... backdrop-blur` para cualquier cliente con `battle.open === true`. El estado `battle` se abre desde eventos WS que se transmiten a todos; no hay rama que, para `!iAmAttacker`, use un contenedor no bloqueante ni un autocierre al cerrar la batalla en el backend.
- **Criterio de aceptación:** con un ataque en curso, el defensor y el espectador pueden seguir viendo el mapa e interactuar con La Tribuna/chat/reacciones (los clicks fuera de la tarjeta llegan al fondo); la vista de batalla del observador se cierra sola al finalizar la batalla sin requerir "Cerrar" manual.

---

## DEF-02 — La apuesta de refuerzos arriesga 1 aunque el botón dice "Arriesgar +3"
- **ID:** DEF-02
- **Severidad:** CRITICAL (correctness de apuesta a verificar) · **Prioridad:** P1
- **Contexto:** fase de refuerzos del jugador activo
- **Jugador:** Daro (activo)
- **Fase:** Refuerzos
- **Pasos:**
  1. Turno de Daro, 9 refuerzos disponibles.
  2. Click en el botón habilitado "Arriesgar +3".
  3. Leer refuerzos disponibles y, al cerrar el turno sin conquistar, el toast de resultado.
- **Resultado observado:** el pool bajó de **9 → 8** (se arriesgó **1**, no 3). Al cerrar el turno sin conquistar: toast "💸 Daro perdió la apuesta: se fue con **1** refuerzos". La etiqueta del botón sugiere +3 pero el monto efectivo fue 1.
- **Resultado esperado:** que el monto arriesgado coincida con lo que comunica el control, y que quede explícito cuánto se está arriesgando en total (acumulado) y cuál es el pago si se gana.
- **Evidencia:** `07-daro-reinforce-wager-1920.png`; retorno de instrumentación: `before=9, afterWager=8`, toast "se fue con 1 refuerzos".
- **Impacto funcional:** la mecánica resuelve bien (se descuenta y se resuelve al cerrar turno), pero el **monto no es transparente**.
- **Impacto sobre comprensión:** alto para una mecánica de apuestas: el jugador no sabe cuánto arriesga realmente.
- **Impacto sobre experiencia:** una apuesta cuyo monto no coincide con el botón erosiona la confianza en el sistema.
- **Causa probable:** desajuste entre la etiqueta del botón de apuesta y el `amount` enviado en el mensaje `turn.wager` (o el botón incrementa de a 1 y la etiqueta "+3" es engañosa). Requiere verificación en el control de apuesta de `TurnPhaseBar` de la build desplegada.
- **Criterio de aceptación:** el control muestra el monto exacto que se arriesgará y el pool baja exactamente en ese monto; el toast de resultado reporta el mismo número; caso de victoria paga el doble de ese mismo monto.

---

## DEF-03 — Durante la colocación inicial simultánea, el HUD marca "JUEGA" a un solo jugador
- **ID:** DEF-03
- **Severidad:** MINOR · **Prioridad:** P2
- **Contexto:** colocación inicial (ambos colocan a la vez)
- **Jugador/es:** todos
- **Fase:** Colocación inicial
- **Pasos:** iniciar partida; observar el TopHud durante la ronda de colocación 5 tropas.
- **Resultado observado:** el HUD muestra el badge "JUEGA Daro" mientras Nessi también está colocando simultáneamente. El indicador "de quién es el turno" no aplica en una fase simultánea y puede confundir ("dice que juega Daro pero yo también coloco").
- **Resultado esperado:** en colocación simultánea, el HUD debería indicar la fase ("COLOCACIÓN — todos colocan") sin señalar un único jugador activo, o mostrar el progreso de cada uno.
- **Evidencia:** `05-game-start-nessi-1920.png`, `06-radial-menu-nessi-1920.png`.
- **Impacto sobre comprensión:** bajo; el panel "ESTADO DEL TURNO" aclara la colocación propia.
- **Causa probable:** el TopHud deriva el "activo" del índice de turno aun cuando el stage es `placement_1/2` (colocación simultánea).
- **Criterio de aceptación:** durante `placement_*`, el HUD no marca un único "JUEGA"; comunica que es colocación simultánea.

---

## DEF-04 — Etiquetas de países se solapan con las insignias de tropas en zonas densas
- **ID:** DEF-04
- **Severidad:** MINOR · **Prioridad:** P2
- **Contexto:** mapa, cualquier fase
- **Fase:** todas
- **Resultado observado:** en zonas apretadas (Colombia/Perú, Chile/Argentina, Oriente Medio/India) el nombre del país y el círculo con el número de tropas se pisan, dificultando leer de un vistazo cuántas tropas hay.
- **Resultado esperado:** nombre e insignia legibles sin solaparse en todos los países.
- **Evidencia:** `05-game-start-nessi-1920.png`, `13-game-1366x768.png`.
- **Impacto:** legibilidad; suma fricción al planear ataques.
- **Causa probable:** posicionamiento de labels/badges por centroide sin resolución de colisiones en países chicos o adyacentes.
- **Criterio de aceptación:** en 1920 y 1366, ningún nombre queda tapado por su insignia ni por la del vecino.

---

## DEF-05 — En mobile (390x844) el mapa queda demasiado chico para interactuar
- **ID:** DEF-05
- **Severidad:** MAJOR (para mobile) · **Prioridad:** P2 (target es desktop+Discord)
- **Contexto:** juego en viewport 390x844
- **Resultado observado:** el layout es responsive (sin scroll horizontal, HUD/mapa/tribuna presentes) pero el mapa ocupa una franja pequeña; tocar países y usar el menú radial sería muy fiddly; los números de tropa apenas se leen.
- **Resultado esperado:** si mobile es un objetivo, el mapa debería poder ampliarse (zoom/paneo) o darse una vista táctil dedicada.
- **Evidencia:** `14-game-390x844.png`, `15-landing-390x844.png`.
- **Impacto:** limita jugar desde el teléfono; en desktop no aplica.
- **Causa probable:** el mapa escala al ancho disponible sin control de zoom/paneo para pantallas chicas.
- **Criterio de aceptación:** en 390px se puede seleccionar cualquier país y usar el menú radial cómodamente (con zoom/paneo si hace falta).

---

## Observación (no defecto) — Combate defensor-favorable hace que los ataques fracasen seguido
Daro atacó Colombia (17 vs 9) y tras varias rondas no la rompió, bajando a 9 (empate favorece al defensor, regla TEG). Es diseño, no bug, pero impacta el **ritmo/tensión**: muchos ataques terminan en nada. A considerar para "sensación de progreso" (no clasificado como defecto).
