# Designer Current Brief - Agy

Fecha: 2026-07-25

## Objetivo

Corregir el handoff visual para que turno, combate y Tribuna puedan pasar a evaluacion de implementacion sin ambiguedades.

## Problema

La entrega actual ya tiene prototipo navegable y direccion correcta, pero no alcanza el gate de implementacion. El prototipo usa dos territorios esquematicos, no valida mapa real, no demuestra 1920x1080/1366x768, no cubre estados de error/reconexion/pago/reembolso y declara assets inexistentes como READY.

## Evidencia

- `frontend/public/prototype/index.html`
- `test-results/designer-prototype-home.png`
- `test-results/designer-prototype-combat.png`
- `assets/manifests/missing-assets.md`
- `test-results/slice-admin-board.png`
- `test-results/slice-player-board.png`

## Cambio solicitado

Entregar una iteracion unica con:

- Prototipo navegable actualizado usando el mapa real o una version reducida visualmente equivalente del mapa real, no solo Argentina/Brasil.
- Estados navegables: turno propio, turno ajeno, refuerzos, ataque, arena de combate, Tribuna abierta, apuesta aceptada, apuesta rechazada, mercado bloqueado, pago, reembolso, error y reconexion.
- Capturas exportadas de 1920x1080 y 1366x768 para turno, combate y Tribuna.
- Correccion del header/prototipo para que no se parta ni solape a 1280px o superior.
- Cierre accesible del modal de combate con boton visible y Escape.
- Manifest/inventario corregido: solo marcar `ready` si el archivo existe fisicamente. Todo faltante debe quedar como `missing` o `planned` con fallback.

## Criterios de aceptacion

- En cada pantalla se responde en menos de 2 segundos: quien juega, fase, accion siguiente y si yo puedo actuar.
- La arena explica cantidad de dados, empate defensor, bajas por par y acumulado.
- La Tribuna explica saldo, mercado, timer, ticket, rechazo, bloqueo, pago y reembolso.
- El mapa conserva protagonismo en 1366x768 y 1920x1080.
- No hay texto cortado, solapado ni caracteres rotos.
- Ningun asset inexistente aparece como `ready`.

## Limites

No definir nombres de componentes React, arquitectura frontend, persistencia backend ni contratos tecnicos no acordados. Los eventos y tablas de ledger pueden mencionarse como necesidades de producto, pero no como implementacion cerrada.
