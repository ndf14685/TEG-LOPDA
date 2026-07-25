# Design Review

Fecha: 2026-07-25

## Resultado

Aprobacion parcial fuerte del prototipo de direccion UX para turno, combate y Tribuna. Actualizacion P0 mapa: la direccion visual hibrida A+B+C queda aprobada como direccion estetica, pero no queda aprobado saltar directo a generar 26/100 territorios completos.

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

## Lo rechazado

- `assets/manifests/assets-manifest.json` todavia referencia `assets/ui/icons/icon-betting-lopda-coin-001.svg`, que no existe.
- Algunas marcas/emoji se renderizan como cuadros en el entorno de prueba; la implementacion debe usar iconografia controlada.
- La arena se llama "3D", pero la evidencia actual es un panel 2D explicativo con dados estilizados. Se acepta para claridad; 3D queda P2.
- El estado `sync-state` en prototipo muestra toast de reconexion, pero no cambia panel persistente del estado de turno; debe definirse mejor antes de implementarlo.
- Los mockups MD siguen siendo ASCII; el handoff visual real pasa a ser el prototipo y capturas, no esos documentos.
- La pagina `frontend/public/prototype/map-hybrid-proof.html` no reproduce todavia la calidad de las JPG: usa seis blobs simplificados y no demuestra territorios reales ni siluetas continentales finales.
- No se acepta pasar directo a "generacion final de 26 y 100 territorios SVG". Primero debe entregarse y validarse una region piloto en capas.
- La direccion debe limpiar textos/HUD genericos de RTS como `GLOBAL DOMINATION`, recursos militares y UI falsa que no pertenece a TEG-LOPDA.

## Proxima accion

Agy debe producir una region piloto, preferentemente America del Sur, con base geografica, territorios SVG reales, hitboxes invisibles, posiciones de etiquetas/tropas y manifest. Frontend solo entra despues para integrar esa region piloto y validar interaccion.
