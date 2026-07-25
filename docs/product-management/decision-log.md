# Decision Log

## Decision 2026-07-25-01

## Decisión

Congelar implementacion productiva nueva de Backend y Frontend hasta cerrar contratos y criterios de Vertical 1.

## Problema

El repositorio compila y pasa tests, pero existe brecha entre lo declarado como terminado y lo demostrado en flujos reales.

## Evidencia

`pnpm e2e` solo valida crear/invitar/lobby/colocacion/dados de practica; no valida ataque completo, conquista, Tribuna, ledger, reconexion en combate ni resoluciones objetivo.

## Opciones consideradas

Continuar implementando features; rehacer todo; congelar solo implementacion nueva y permitir auditoria/diseño/contratos.

## Decisión elegida

Congelar implementacion nueva y habilitar solo diseno/contratos/pruebas de Vertical 1.

## Motivo

Reduce consumo de cuota y evita seguir agregando codigo sin validar experiencia.

## Impacto

Backend y Frontend quedan bloqueados para features nuevas; Designer recibe el primer brief.

## Riesgos

Puede sentirse mas lento a corto plazo, pero evita retrabajo caro.

## Criterio de revisión

Se reconsidera cuando Vertical 1 tenga diseno aceptado, contrato sincronizado y E2E multi-cliente definido.

## Decision 2026-07-25-02

## Decisión

`shared/contracts/src/*.ts` es la fuente tecnica efectiva actual; los JSON/MD de contratos quedan como desactualizados hasta conciliacion.

## Problema

El JSON `client-messages.schema.json` no representa mensajes que usa frontend/backend.

## Evidencia

`shared/contracts/src/ws-events.ts` incluye `placement.place`, `turn.place_reinforcement`, `turn.fortify`, `turn.next_phase`, `turn.wager`, `cards.trade` y pactos; el JSON solo enumera `ping`, `ready.set`, `chat.send`, `dice.roll`, `attack`, `turn.end`.

## Opciones consideradas

Usar JSON como fuente; usar TS como fuente; detener hasta generar ambos.

## Decisión elegida

Usar TS como fuente efectiva para auditoria y bloquear nuevas features hasta regenerar/alinear JSON y docs.

## Motivo

El frontend compila contra TS y el backend ya acepta esos mensajes.

## Impacto

Backend/Frontend deben sincronizar contratos antes de nueva implementacion.

## Riesgos

Herramientas externas que lean JSON recibiran contrato falso.

## Criterio de revisión

JSON, MD y TS deben coincidir en mensajes, payloads y eventos.

## Decision 2026-07-25-03

## Decisión

La apuesta de refuerzos actual no cuenta como Tribuna ni sistema de Monedas LOPDA.

## Problema

El producto requiere espectadores/espera activa con mercado, monedas, ledger y resolucion autoritativa.

## Evidencia

`GameEngine.set_wager()` descuenta refuerzos del jugador activo en memoria/state_json; no hay tabla `player_lopda_ledger` ni eventos `bet.market.*`.

## Opciones consideradas

Renombrar la feature actual como Tribuna; eliminarla; conservarla como mecanica experimental bloqueada fuera de P0/P1.

## Decisión elegida

Conservarla como mecanica experimental no aprobada para release; no usarla para declarar Vertical 3.

## Motivo

No satisface integridad transaccional ni experiencia de espera.

## Impacto

Backend necesita diseño/contrato nuevo para Vertical 3; Frontend no debe ampliar esta UI como si fuera Tribuna.

## Riesgos

Puede confundir al usuario y al equipo si sigue visible sin contexto.

## Criterio de revisión

Solo se aprueba Tribuna cuando existan ledger, mercado, tickets, bloqueo y pruebas de doble pago/reembolso.

## Decision 2026-07-25-04

## Decisión

Activar fast-track de Frontend para version jugable privada.

## Problema

El owner humano prioriza velocidad y experiencia jugable para amigos sobre proceso formal de gates antes de implementar.

## Evidencia

Solicitud directa del owner: "no planifiquen, saquen version final y vamos corrigiendo en el camino... Aceleralo".

## Opciones consideradas

Mantener congelamiento; habilitar solo plan; habilitar implementacion frontend con guardrails P0.

## Decisión elegida

Habilitar implementacion directa de Frontend usando prototipo como referencia, con verificacion rapida y correcciones iterativas.

## Motivo

El producto es privado, no comercial ni publico; el costo principal ahora es demora, no compliance formal.

## Impacto

Frontend puede modificar UI productiva ya. Backend solo toca contratos/logica si Frontend queda bloqueado por datos faltantes. Designer queda disponible para ajustes visuales puntuales.

## Riesgos

Puede entrar deuda visual/tecnica y algunas inconsistencias de Tribuna si se simula antes del ledger real.

## Criterio de revisión

Se frena el fast-track solo si aparece P0: partida imposible de continuar, estado inconsistente, perdida de datos, reglas criticas en cliente o corrupcion de monedas/apuestas.

## Decision 2026-07-25-05

## Decisión

Rechazar el mapa visual actual y declarar P0 el rediseño total del mapamundi.

## Problema

El mapa actual es funcional tecnicamente, pero no se reconoce inmediatamente como mapamundi. El jugador depende de titulos de continentes y etiquetas para interpretar la pantalla, lo que rompe la fantasia, la claridad tactica y la presentacion basica del juego.

## Evidencia

Capturas de playtest y e2e: `test-results/product-1366x768-turn.png`, `test-results/product-defender-battle.png`, `artifacts/playtest/screenshots/13-game-1366x768.png`, `artifacts/playtest/screenshots/14-game-390x844.png`. Las siluetas continentales son organicas pero no reconocibles como America del Norte, America del Sur, Europa, Africa, Asia y Oceania sin leer textos.

## Opciones consideradas

1. Parchear posiciones, nombres e insignias sobre el SVG actual.
2. Mejorar solo textura/colores del mapa actual.
3. Redisenar el mapa en capas conservando IDs y adyacencias cuando sea posible.

## Decisión elegida

Redisenar el mapa completo en cuatro capas: base geografica no interactiva, territorios SVG jugables, hitboxes invisibles y overlays.

## Motivo

El mapa es el protagonista del producto. Si no se reconoce como mapamundi en menos de un segundo, el juego se percibe como prototipo tecnico aunque turno, combate y multiplayer funcionen.

## Impacto

Designer/Agy pasa primero y debe entregar tres direcciones visuales del mapamundi completo sin titulos de continentes. Frontend queda pausado para pulido visual secundario y solo dara soporte tecnico de IDs, adyacencias, hitboxes y prueba de una region. Backend no entra salvo que el cambio de IDs rompa contratos o persistencia.

## Riesgos

Puede consumir cuota si se intenta resolver todo el mundo de una vez. Puede romper adyacencias o flujos si se reemplazan IDs sin mapeo. Puede generar una imagen linda pero poco jugable si no se separan territorios e hitboxes.

## Criterio de revisión

Se reconsidera solo si una propuesta demuestra en capturas 1920x1080 y 1366x768 que el mapa se reconoce sin etiquetas, conserva interaccion por territorio, mantiene legibilidad de tropas y respeta colores de seis jugadores sin destruir la geografia.

## Decision 2026-07-25-06

## Decisión

Aprobar la direccion visual hibrida A+B+C del mapa solo como direccion estetica y exigir region piloto antes de producir el mundo completo.

## Problema

La entrega de Agy resuelve el reconocimiento visual del mapamundi en JPG, pero todavia no demuestra que esa calidad pueda convertirse en territorios SVG reales, hitboxes, posiciones de tropas y labels sin romper la jugabilidad.

## Evidencia

Capturas revisadas: `map_hybrid_proof_without_titles_1784966918011.jpg`, `map_hybrid_proof_with_titles_1784966886931.jpg`, `map_hybrid_proof_1366x768_1784966955835.jpg`. Documento: `docs/design/map-hybrid-proof-p0.md`. Prototipo: `frontend/public/prototype/map-hybrid-proof.html`.

## Opciones consideradas

1. Aprobar y pedir directamente 26 y 100 territorios completos.
2. Rechazar la direccion y pedir nuevas propuestas.
3. Aprobar direccion estetica y exigir una region piloto implementable.

## Decisión elegida

Aprobar la direccion estetica y bloquear la produccion completa hasta validar una region piloto, preferentemente America del Sur.

## Motivo

El salto de imagen de alta fidelidad a SVG jugable es el riesgo real. Una region piloto permite validar geometria, IDs, hitboxes, labels, tropas, colores, seleccion y ataque con bajo consumo de cuota.

## Impacto

Agy debe entregar America del Sur en capas. Frontend no integra el mundo completo; solo prepara prueba tecnica de esa region cuando los assets esten listos. Backend no entra.

## Riesgos

Las JPG tienen elementos de HUD generico de RTS y textos ajenos al producto; deben eliminarse. El prototipo HTML actual no reproduce la calidad de las JPG y no puede usarse como base final.

## Criterio de revisión

Se habilita completar el resto del mundo solo si America del Sur se reconoce, es clickeable, no solapa labels/tropas, conserva IDs o entrega tabla de mapeo, soporta seis colores y permite ataque/seleccion en 1920x1080 y 1366x768.

## Decision 2026-07-25-07

## Decisión

Aprobar parcialmente la region piloto de America del Sur solo como patron de capas/interaccion; rechazarla como geometria final.

## Problema

La entrega demuestra capas, labels, badges, seleccion, objetivo y flecha, pero los territorios se ven como capsulas o blobs superpuestos sobre una silueta de America del Sur, no como subdivisiones geograficas coherentes del continente.

## Evidencia

Capturas revisadas: `test-results/south-america-pilot-labels-badges-1920x1080.png`, `test-results/south-america-pilot-no-labels.png`, `test-results/south-america-pilot-1366x768.png`, `test-results/south-america-pilot-selected.png`, `test-results/south-america-pilot-attackable.png`, `test-results/south-america-pilot-executing.png`. Prototipo: `frontend/public/prototype/south-america-pilot.html`. Manifest: `assets/manifests/south-america-pilot-manifest.json`.

## Opciones consideradas

1. Aprobar region piloto y habilitar Frontend.
2. Rechazar toda la entrega.
3. Aprobar capas/interaccion y pedir una iteracion acotada sobre geometria.

## Decisión elegida

Aprobar capas/interaccion y pedir una iteracion acotada de geometria antes de habilitar Frontend.

## Motivo

La arquitectura propuesta es util y no conviene rehacerla, pero el objetivo P0 del mapa exige geografia reconocible no solo a nivel continente, tambien a nivel territorios principales.

## Impacto

Agy sigue activo. Frontend permanece pausado. Backend no entra.

## Riesgos

Si se acepta esta geometria ahora, el mapa completo puede terminar siendo otra malla visualmente arbitraria. Si se pide demasiada precision geografica, puede reducirse la clickeabilidad; por eso se mantienen hitboxes independientes.

## Criterio de revisión

Se aprueba la region piloto cuando Brasil, Argentina, Chile, Uruguay, Colombia, Venezuela, Peru y Bolivia se lean como subdivisiones plausibles de America del Sur, sin solapamiento de labels/tropas y manteniendo los estados de seleccion/ataque ya demostrados.
