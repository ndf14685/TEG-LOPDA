# Frontend Current Brief - Claude

Fecha: 2026-07-25

## Estado

Habilitado en fast-track para implementar UI jugable privada.

## Objetivo

Convertir la UI productiva en una version final jugable basada en `frontend/public/prototype/index.html`, priorizando claridad de turno, mapa protagonista, combate explicativo y Tribuna util.

## Alcance inmediato

- Rehacer pantalla de juego hacia el layout del prototipo.
- Mantener integracion con backend real donde exista contrato.
- Turno/refuerzos/ataque deben usar estado autoritativo actual.
- Combate debe mostrar desglose claro con los datos disponibles de `attack.resolved`.
- Tribuna puede iniciar como UI funcional/fallback si el ledger backend real aun no existe, pero debe rotularse como monedas virtuales de partida y no dinero real.
- Reemplazar iconos/emoji que rendericen como cuadros por texto o iconografia controlada.
- Usar assets existentes; si falta algo, usar fallback CSS.

## Guardrails P0

- No mover reglas criticas al cliente si el backend ya las valida.
- No generar dados en cliente para resultados reales.
- No resolver apuestas reales de forma definitiva si despues habra ledger backend.
- No romper reconexion ni bloqueo de acciones al desincronizar.
- No introducir dinero real ni pagos.

## Verificacion minima antes de entregar

- `pnpm test`
- `pnpm typecheck`
- `pnpm build`
- `pnpm e2e`
- Capturas manuales o automatizadas de 1366x768 y 1920x1080.

## Condicion de parada

Detener y pedir backend solo si falta dato autoritativo indispensable para turno, fase, accion legal, combate o persistencia.

## Hotfix post-playtest Windows

Fecha: 2026-07-25

Estado: entregado y aceptado para mini-playtest en `bf4e6fe`.

### Objetivo

Corregir los P1 del playtest sin abrir rediseños grandes.

### Tareas

1. DEF-01: Arena de Combate no bloqueante para defensor y espectadores.
   - Atacante: puede mantener modal/arena accionable.
   - Defensor/espectador: deben ver batalla como panel/dock/overlay no bloqueante o con autocierre claro; no debe impedir Tribuna/chat/mapa.
   - Mantener todo el contenido explicativo actual.

2. DEF-02: apuesta de refuerzos transparente.
   - Al pulsar `Arriesgar +N`, mostrar confirmacion/estado con el monto exacto enviado.
   - Registrar en UI el monto aceptado por el servidor.
   - Si se pide +3 y el servidor acepta 1, mostrar discrepancia y dejar evidencia de payload WS/evento para determinar si es bug backend.
   - No simular ni ocultar el resultado.

3. DEF-03: colocacion simultanea.
   - Durante `placement_1`/`placement_2`, no mostrar `JUEGA` como si hubiera turno unico.
   - Mostrar `COLOCANDO`/`LISTO` por jugador.

4. DEF-04: reducir solapamiento nombre/insignia.
   - Ajuste visual pequeno; no bloquear si requiere Arte.

### Verificacion obligatoria

- `pnpm test`
- `pnpm typecheck`
- `pnpm build`
- `pnpm e2e`
- Capturas desktop: turno, arena atacante, arena defensor/espectador, Tribuna.

## Proximo alcance

No abrir nuevos cambios de Frontend hasta completar mini-playtest de regresion con tres clientes. Si aparecen P0/P1, corregir solo esos defectos. DEF-05 mobile, flecha por arrastre, pings, planes privados e iconos/assets quedan fuera del alcance inmediato.

## Piloto P0 Mapa - America del Sur

Fecha: 2026-07-25

Estado: habilitado para integracion acotada. No integrar todavia el mundo completo.

### Objetivo

Integrar la region piloto America del Sur corregida en el mapa productivo o en un modo de prueba productivo, conservando contratos de juego y validando interaccion real.

### Fuentes

- `frontend/public/prototype/south-america-pilot.html`
- `docs/design/south-america-pilot-p0.md`
- `assets/manifests/south-america-pilot-manifest.json` (referencia parcial; requiere alcance modo 26/50 actualizado antes de usarlo como contrato final)
- Capturas `test-results/south-america-real-geo-*.png`

### Alcance

- Integrar solo America del Sur.
- Mantener IDs existentes.
- Soportar modo 50 con 8 territorios.
- Soportar modo 26 con 5 territorios o dejarlo explicitamente fuera si la app actual corre solo modo 50; no mezclar modos silenciosamente.
- Separar territorio visible, hitbox y overlays.
- Mantener labels y badges sin choque.
- Validar propiedad con seis colores.
- Validar seleccionado, atacable y ataque en ejecucion.

### Fuera de alcance

- No generar ni integrar el resto del mundo.
- No redisenar HUD, Tribuna, combate ni reglas.
- No tocar backend salvo que haya ruptura real de IDs/adyacencias.

### Verificacion obligatoria

- `pnpm test`
- `pnpm typecheck`
- `pnpm build`
- `pnpm e2e`
- Capturas 1920x1080 y 1366x768 de America del Sur: normal, sin labels, seleccionado, atacable y ataque.
