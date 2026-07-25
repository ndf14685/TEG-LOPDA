# Performance audit (observaciones)

Medición ligera dentro del fast-track (sobre túnel Cloudflare → latencia de red incluida).

| Métrica | Observado |
|---|---|
| Carga inicial de landing | ~2.0s (`load`) |
| Reconexión mid-game a estado jugable | ~4.4s (incluye recarga + WS + snapshot sobre túnel) |
| Errores de consola | 0 en toda la sesión (landing, lobby, juego, combate, reconexión) |
| Requests fallidos (>=400) | 0 observados |
| Errores WebSocket | ninguno observado; el estado se mantuvo sincronizado |
| Assets 404 | ninguno (mapa SVG y assets cargaron) |
| Layout shift | no se observó CLS notable al cargar el juego |
| Overflow horizontal | ninguno en 1920 / 1366 / 390 |

## No medido (requiere pasada dedicada / DevTools)
- FPS reales durante animación de dados / paneo de mapa.
- Long tasks (bloqueos del main thread).
- Consumo creciente de memoria en partida larga (leak).
- Múltiples conexiones simultáneas a escala (6+ jugadores).
- Audio duplicado (audio estuvo OFF por defecto en esta sesión).

## Lectura
En los caminos probados el rendimiento es **limpio** (sin errores, sin overflow, tiempos razonables sobre túnel). Falta profundizar en FPS/long-tasks/memoria con herramientas de perfilado y en una partida larga con más jugadores.
