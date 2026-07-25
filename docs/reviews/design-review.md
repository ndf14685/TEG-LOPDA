# Design Review

Fecha: 2026-07-25

## Resultado

Aprobacion parcial fuerte del prototipo de direccion UX para turno, combate y Tribuna. Actualizacion P0 mapa: el mapamundi Modo 50 queda aprobado como base jugable para integracion y playtest privado. No es arte final perfecto, pero supera el bloqueo P0: reconoce el mundo, conserva contratos, recibe clicks por hitboxes y pasa e2e en partida real.

## Evidencia

- Existe prototipo navegable standalone actualizado: `frontend/public/prototype/index.html`.
- Capturas de auditoria local inicial: `test-results/designer-prototype-home.png` y `test-results/designer-prototype-combat.png`.
- Capturas de segunda auditoria: `test-results/prototype-1366x768-turn.png`, `test-results/prototype-1366x768-combat.png`, `test-results/prototype-1920x1080-turn.png`, `test-results/prototype-1920x1080-combat.png`.
- Prueba automatizada local: 1366x768 y 1920x1080 sin errores de consola, sin overflow del body, modal cierra con Escape.
- Existen mockups ASCII en `design/high-fidelity/`.
- El inventario de assets declara READY archivos que no existen fisicamente.

## Lo aprobado

- La direccion de turno propio/ajeno con marquesina explicita es correcta.
- La arena de combate prioriza desglose matematico, empates y bajas acumuladas.
- La Tribuna esta planteada como mercado autoritativo con ledger, no como apuesta cliente.
- El prototipo usa mapa real de 50 territorios/continentes y valida lectura visual en 1366x768 y 1920x1080.
- El prototipo cubre estados de apuesta aceptada, rechazada, mercado bloqueado, pago, reembolso y reconexion como estados navegables.
- El CSV de inventario ya no marca como `ready` assets inexistentes.
- La prueba `map_hybrid_proof_without_titles_1784966918011.jpg` resuelve el criterio principal de reconocimiento: el mapamundi y los continentes se identifican sin titulos.
- La solucion de tintado suave + borde de jugador preserva mejor la geografia que el relleno plano opaco.
- Region piloto America del Sur: la separacion de capas, labels, badges, seleccion, objetivo atacable y flecha de ataque quedan aprobados como patron de interaccion.
- Region piloto America del Sur: los IDs del modo 50 se preservan para los 8 territorios declarados.
- Region piloto America del Sur corregida: la geometria encastrada de modo 26 y modo 50 queda aprobada para integracion piloto acotada en Frontend.
- Mapamundi Modo 50: IDs visibles del SVG coinciden con `TERRITORIES_50` del backend (50/50, sin faltantes ni extras); existe una hitbox por territorio y una etiqueta/badge por territorio.

## Lo rechazado

- `assets/manifests/assets-manifest.json` todavia referencia `assets/ui/icons/icon-betting-lopda-coin-001.svg`, que no existe.
- Algunas marcas/emoji se renderizan como cuadros en el entorno de prueba; la implementacion debe usar iconografia controlada.
- La arena se llama "3D", pero la evidencia actual es un panel 2D explicativo con dados estilizados. Se acepta para claridad; 3D queda P2.
- El estado `sync-state` en prototipo muestra toast de reconexion, pero no cambia panel persistente del estado de turno; debe definirse mejor antes de implementarlo.
- Los mockups MD siguen siendo ASCII; el handoff visual real pasa a ser el prototipo y capturas, no esos documentos.
- La pagina `frontend/public/prototype/map-hybrid-proof.html` no reproduce todavia la calidad de las JPG: usa seis blobs simplificados y no demuestra territorios reales ni siluetas continentales finales.
- No se acepta pasar directo a "generacion final de 26 y 100 territorios SVG". Primero debe entregarse y validarse una region piloto en capas.
- La direccion debe limpiar textos/HUD genericos de RTS como `GLOBAL DOMINATION`, recursos militares y UI falsa que no pertenece a TEG-LOPDA.
- Region piloto America del Sur no queda aprobada como geometria final: los territorios siguen leyendose como capsulas/blobs superpuestos sobre una silueta tenue, no como subdivisiones geograficas coherentes del continente.
- La afirmacion "0 cambios tecnicos en el motor" solo aplica al modo 50 en esta region. El modo 26 actual no contiene todos esos IDs, por lo que debe declararse explicitamente el alcance.
- La region piloto no demuestra todavia integracion productiva ni hitboxes verificadas con Playwright; es prototipo de diseno.
- `assets/manifests/south-america-pilot-manifest.json` no quedo actualizado con el alcance separado modo 26/modo 50 ni con timestamp de la version 2.3.0. Frontend puede usar el HTML/prototipo como referencia, pero el manifest debe corregirse antes de tratarlo como contrato final de assets.
- Manifiestos principales de assets: `assets-manifest.json` y `assets-inventory.csv` quedan aprobados en existencia fisica; verificacion local de referencias `READY` encontro 21 rutas y 0 faltantes.
- `missing-assets.md` queda aceptado como inventario operativo, pero mantiene inconsistencias menores: no lista todos los nuevos READY del manifest principal y conserva observaciones antiguas de integracion frontend. No bloquea la integracion piloto del mapa.
- Mapamundi Modo 50 no queda aprobado para integracion productiva. El e2e falla porque las hitboxes usan `data-territory-id`, mientras `MapPanel.tsx` y `e2e/south-america-pilot.spec.ts` esperan `data-territory`. Resultado: `path.territory-hitbox[data-territory="territory-south-america-argentina"]` no existe.
- Mapamundi Modo 50 no pasa el gate visual: hay solapes fuertes de labels/tropas/territorios en America del Norte, Europa/Asia, Africa y enlace Mexico/Colombia/Sudamerica. A 1366x768 la lectura empeora.
- La version sin etiquetas reconoce continentes generales, pero varios territorios se perciben como piezas superpuestas, no como subdivisiones limpias.
- Correccion 2026-07-25 `54f33a0`: el contrato estatico de hitboxes queda corregido (`50` hitboxes con `data-territory`, sin faltantes contra los `50` IDs visibles y `TERRITORIES_50`), pero el handoff sigue rechazado porque `pnpm e2e` falla en partida real: durante colocacion/refuerzo el click via hitbox no abre el menu radial.
- `docs/design/map-world-50-p0.md` sigue desactualizado: describe `data-territory-id` aunque el manifest y SVG ya usan `data-territory`.
- Persisten solapes visuales relevantes: `P/Mexico`, Alemania/Polonia, Arabia/Etiopia, Sumatra/Borneo y densidad general Europa/Medio Oriente a 1366x768.
- Correccion 2026-07-25 `5b16c23`: documento tecnico y contrato estatico quedan corregidos, pero el handoff sigue rechazado. `pnpm e2e` falla en `south-america-pilot.spec.ts`; diagnostico `diagnostic-global-svg.spec.ts` muestra que los badges horneados interceptan clicks (`circle.badge-circle`, `pointer-events:auto`) y que en bordes puede recibir un hitbox vecino.
- Correccion 2026-07-25 `0afff3e`: el mapamundi Modo 50 queda aprobado para integracion/playtest. Verificacion local: 50 territorios visibles, 50 hitboxes unicas con `data-territory`, 0 faltantes contra `TERRITORIES_50`, sin `data-territory-id`, overlays con `pointer-events="none"`, y `pnpm test && pnpm typecheck && pnpm build && pnpm e2e` verde. Diagnostico e2e: centro y borde de Alaska reciben `path.territory-hitbox [territory-north-america-alaska]`; `badge_pointer_events` = `none`.
- Integracion Frontend `b5284b4`: saneo runtime aprobado para el playtest privado. Oculta badges demo horneados, remueve clases demo `p-*` y ajusta `viewBox` al contenido real para evitar recorte sur/radial fuera de vista. Esto no cambia el contrato de Arte, pero evita que defectos del export bloqueen el deploy.

## Proxima accion

Integracion piloto de America del Sur completada por Frontend en modo 50 y aprobada en e2e real. El mapamundi completo Modo 50 queda aprobado en deploy con saneo runtime. Siguiente paso: tester Windows debe ejecutar mini-regresion sobre URL real. Agy no debe seguir iterando el mapa Modo 50 salvo defectos nuevos de playtest; limpieza del export queda P2.
