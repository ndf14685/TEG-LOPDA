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

## Decision 2026-07-25-08

## Decisión

Aprobar la geometria corregida de America del Sur para integracion piloto acotada en Frontend.

## Problema

La iteracion anterior resolvia capas/interaccion, pero mantenia blobs. La nueva entrega reconstruye la region con piezas encastradas y aclara alcance modo 26 vs modo 50.

## Evidencia

Capturas revisadas: `test-results/south-america-real-geo-mode50-1920x1080.png`, `test-results/south-america-real-geo-mode26-1920x1080.png`, `test-results/south-america-real-geo-no-labels.png`, `test-results/south-america-real-geo-executing.png`, `test-results/south-america-real-geo-1366x768.png`. Documento: `docs/design/south-america-pilot-p0.md`. Prototipo: `frontend/public/prototype/south-america-pilot.html`.

## Opciones consideradas

1. Pedir otra iteracion visual de Agy.
2. Aprobar y generar todo el mundo.
3. Aprobar solo para integracion piloto de America del Sur.

## Decisión elegida

Aprobar solo para integracion piloto de America del Sur.

## Motivo

La region supera el umbral P0 visual: se reconoce como America del Sur, los territorios son plausibles y los estados de seleccion/ataque son legibles. Todavia falta prueba productiva de hitboxes, labels y ataque antes de escalar al resto del mundo.

## Impacto

Frontend queda habilitado para integrar America del Sur de forma acotada. Agy debe corregir el manifest para declarar alcance modo 26/50. Backend no entra salvo ruptura real de IDs o adyacencias.

## Riesgos

El manifest `south-america-pilot-manifest.json` no refleja todavia el alcance separado modo 26/modo 50 ni timestamp 2.3.0. La integracion puede descubrir problemas de posicion al mezclar esta region con el resto del mapa viejo.

## Criterio de revisión

Se habilita extender al resto del mapa solo despues de que Frontend demuestre en flujo real seleccion, propiedad, tropas, hitboxes, ataque y reconexion usando America del Sur en 1920x1080 y 1366x768.

## Decision 2026-07-25-09

## Decisión

Aprobar la integracion piloto de America del Sur en el mapa productivo modo 50 y devolver el foco a Agy para completar el resto del mundo.

## Problema

Frontend ya demostro que la region aprobada puede integrarse sin romper IDs, hitboxes ni flujo de ataque. El riesgo restante no es tecnico de Frontend sino de consistencia visual: el resto del mundo conserva la geometria vieja.

## Evidencia

Commit `d980385 feat(map): piloto P0 América del Sur — geometría realista integrada al modo 50`. Review `docs/reviews/sa-pilot-integration.md`. E2E `e2e/south-america-pilot.spec.ts` paso junto con la suite completa: `pnpm test`, `pnpm typecheck`, `pnpm build`, `pnpm e2e`. Capturas: `test-results/sa-pilot-1920x1080.png`, `test-results/sa-pilot-1366x768.png`, `test-results/sa-pilot-no-labels.png`, `test-results/sa-pilot-selected.png`, `test-results/sa-pilot-attackable.png`, `test-results/sa-pilot-executing.png`.

## Opciones consideradas

1. Pedir a Frontend que extrapole el resto del mundo.
2. Volver a Agy para generar el resto de continentes con el patron aprobado.
3. Detener mapa y volver a pulido secundario.

## Decisión elegida

Volver a Agy. Frontend queda en pausa hasta recibir geometria/capas aprobadas del resto del mundo.

## Motivo

La calidad visual del mapa depende de geometria, no de integracion. Frontend ya probo el pipeline; ahora Arte debe producir assets consistentes para el resto.

## Impacto

Agy: producir continentes restantes. Frontend: no avanzar salvo correccion P0/P1 o integracion de assets aprobados. Backend: no entra.

## Riesgos

El contraste entre America del Sur nueva y el resto del mundo viejo queda visible hasta completar la malla. Modo 26 conserva arte viejo porque el piloto valido solo modo 50.

## Criterio de revisión

Se habilita nueva integracion Frontend cuando Agy entregue America del Norte, Europa, Africa, Asia y Oceania con geometria encastrada, hitboxes, labels, posiciones de tropas, estados de seleccion/ataque y manifest por modo.

## Decision 2026-07-25-10

## Decisión

Rechazar el mapamundi completo Modo 50 como handoff productivo.

## Problema

Aunque el SVG conserva 50 IDs visibles y una hitbox por territorio, no respeta el contrato vigente de Frontend para hitboxes y presenta solapes visuales que rompen legibilidad.

## Evidencia

`pnpm test`, `pnpm typecheck` y `pnpm build` pasan. `pnpm e2e` falla en `e2e/south-america-pilot.spec.ts` porque busca `path.territory-hitbox[data-territory="territory-south-america-argentina"]`, pero el SVG global usa `data-territory-id`. Capturas revisadas: `test-results/world-50-labels-badges-1920x1080.png`, `test-results/world-50-no-labels-1920x1080.png`, `test-results/world-50-1366x768.png`, `test-results/world-50-attackable.png`.

## Opciones consideradas

1. Habilitar Frontend y pedir que adapte el contrato.
2. Corregir el contrato y solapes en Arte antes de integrar.
3. Descartar todo el mapa global.

## Decisión elegida

Corregir en Arte antes de integrar. No habilitar Frontend todavia.

## Motivo

El e2e demuestra que el handoff no es compatible. Cambiar el contrato en Frontend para acomodar un asset no acordado genera retrabajo y rompe el piloto que ya estaba validado.

## Impacto

Agy debe corregir `data-territory` y solapes. Frontend queda pausado. Backend no entra.

## Riesgos

Si solo se corrige el atributo y se ignoran solapes, el mapa puede funcionar tecnicamente pero seguir fallando como P0 visual.

## Criterio de revisión

Se habilita Frontend cuando el SVG tenga 50 hitboxes con `data-territory`, pase `pnpm e2e`, y las capturas 1920/1366 muestren labels/tropas sin choques graves en Norteamerica, Europa/Asia, Africa y Oceania.

## Decision 2026-07-25-11

## Decisión

Mantener rechazado el mapamundi completo Modo 50 despues de la correccion `data-territory`.

## Problema

El contrato estatico de hitboxes fue corregido, pero el mapa no pasa prueba productiva: en partida real el click via hitbox/territorio no abre el menu radial durante colocacion/refuerzo. Ademas persisten solapes visuales.

## Evidencia

Commit `54f33a0`. Verificacion estatica: 50 territorios visibles, 50 hitboxes con `data-territory`, sin faltantes contra `TERRITORIES_50`. `pnpm test`, `pnpm typecheck` y `pnpm build` pasan. `pnpm e2e` falla en `e2e/south-america-pilot.spec.ts` por timeout esperando `.radial-menu button +1` despues de intentar colocar via hitbox. Capturas revisadas: `world-50-labels-badges-1920x1080.png`, `world-50-1366x768.png`, `world-50-no-labels-1920x1080.png`.

## Opciones consideradas

1. Aprobar por contrato estatico y dejar que Frontend adapte.
2. Rechazar todo y volver a America del Sur.
3. Mantener rechazo productivo y pedir diagnostico acotado de interaccion + ajuste visual.

## Decisión elegida

Mantener rechazo productivo. Habilitar solo diagnostico acotado de Frontend sobre el click/hitbox y correccion de Agy sobre solapes/documento.

## Motivo

El criterio P0 exige que el mapa sea jugable, no solo que tenga paths correctos. Si no abre el radial, rompe colocacion/refuerzo.

## Impacto

Frontend puede diagnosticar la causa de interaccion sin integrar globalmente ni redisenar. Agy debe corregir solapes y documento tecnico. Backend no entra.

## Riesgos

Si Frontend parchea el handler para acomodar un SVG defectuoso, puede romper el piloto de America del Sur ya validado. El diagnostico debe identificar causa y mantener contrato `data-territory`.

## Criterio de revisión

Se reconsidera cuando `pnpm e2e` pase completo y las capturas no muestren choques graves en las zonas densas.

## Decision 2026-07-25-12

## Decisión

Rechazar nuevamente el mapamundi completo Modo 50 despues de la correccion documental final.

## Problema

El contrato estatico `data-territory` esta correcto, pero el mapa sigue sin ser jugable en partida real: los overlays horneados interceptan clicks y algunos hitboxes cubren zonas de territorios vecinos.

## Evidencia

Commits `5b16c23`, `927d636`, `fc4c56d`. Verificacion estatica: 50 territorios visibles, 50 hitboxes con `data-territory`. `pnpm test`, `pnpm typecheck`, `pnpm build` pasan. `pnpm e2e` falla en `south-america-pilot.spec.ts` esperando menu radial. Diagnostico imprime: centro recibe `circle.badge-circle`, borde recibe `path.territory-hitbox [territory-north-america-new-york]`, `badge_pointer_events` = `auto`.

## Opciones consideradas

1. Aprobar porque la documentacion ya esta corregida.
2. Pedir a Frontend que parchee clicks sobre overlays.
3. Rechazar handoff y exigir SVG productivo sin overlays interceptores ni hitboxes invasivas.

## Decisión elegida

Rechazar handoff. El SVG productivo debe corregirse antes de integracion global.

## Motivo

El mapa no puede bloquear colocacion/refuerzo. El contrato visible es correcto, pero el comportamiento real no.

## Impacto

Agy debe corregir SVG/overlays/hitboxes. Frontend solo conserva diagnostico; no debe integrar globalmente ni adaptar reglas de click para tapar un asset defectuoso. Backend no entra.

## Riesgos

Si se acepta el parche en Frontend, cada overlay futuro puede volver a romper interaccion. La capa de overlays debe ser no interactiva por diseño.

## Criterio de revisión

`pnpm e2e` completo verde; diagnostico confirma que centro/borde de territorios propios llegan al territorio/hitbox correcto; capturas 1920/1366 sin choques graves.
