# Reconnect audit

## Casos probados
1. **Reconexión en lobby** (recarga de pestaña):
   - Daro recargó estando en el lobby con "listo" marcado.
   - Resultado: volvió a `/lobby/<code>`, identidad "Daro (vos)", 3/3 conectados, estado "listo" preservado. OK.

2. **Reconexión mid-game** (recarga durante el turno de Nessi):
   - Daro recargó la pestaña.
   - Tiempo a estado jugable: **~4.4s**.
   - Recuperó: URL `/game/<code>`, mapa con 26 territorios, jugador activo correcto (Nessi), fase "T2 · REFUERZOS", identidad "Daro (vos)", e **historial de chat persistido** ("hola desde Nessi").
   - **Cero errores de consola** en la reconexión.

## Cobertura del brief
- Recuperar identidad: OK
- Recuperar turno: OK
- Recuperar fase: OK
- Recuperar mapa: OK
- Recuperar chat/historial: OK
- Recuperar apuesta / monedas / pactos: no ejercitados en profundidad en esta sesión (apuesta ya resuelta; monedas bloqueadas; sin pactos activos). Recomendado en pasada extendida.

## Simulaciones pendientes (pasada extendida)
- Pérdida de WebSocket sin recarga (corte de red) y su reconexión automática.
- Token inválido / revocado en juego (se probó revocación en lobby por diseño del brief; en juego queda pendiente).
- Reinicio de frontend.

## Evidencia
Instrumentación de recarga (retorno `recover`), y capturas de estado consistentes pre/post recarga.

## Veredicto
Reconexión **sólida** en los caminos probados (lobby y mid-game). No se observó pérdida de estado ni divergencia entre clientes.
