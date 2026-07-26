# Tester Brief - Functional RC 001

Fecha: 2026-07-26

## Datos de la release

- URL exacta: `https://paris-penalty-clan-sellers.trycloudflare.com`
- Commit SHA de aplicación validada: `2762191`
- Tag: `functional-rc-001`
- Rama: `frontend/canonical-50-integration`
- Versión HTTP reportada por `/health`: `0.1.0`
- Cantidad recomendada de jugadores: 3 o 4 humanos. Mínimo funcional: 2.
- Modo de la sala precreada: `classic_50`
- Estado conocido de la partida de prueba: lobby, sin iniciar.
- Game ID: `46819c9f-16e4-4618-a18e-6704d0559166`
- Código de sala: `58ae2m4z`
- Admin page: `https://paris-penalty-clan-sellers.trycloudflare.com/admin/46819c9f-16e4-4618-a18e-6704d0559166`
- Admin join link: `https://paris-penalty-clan-sellers.trycloudflare.com/join/58ae2m4z/O_myH1_fOpEfQK92EZEATRwECD5WUWpu`
- Player A: `https://paris-penalty-clan-sellers.trycloudflare.com/join/58ae2m4z/qyt3-HOnbMNgEnTurn8YWJQVterWadGt`
- Player B: `https://paris-penalty-clan-sellers.trycloudflare.com/join/58ae2m4z/nLmFGgOa17iA3kRflwOLjjuhVjlC5-TQ`
- Player C: `https://paris-penalty-clan-sellers.trycloudflare.com/join/58ae2m4z/kYEyX7GluyYfQOWWtRImd5264i0NqM8j`

## Cómo crear nuevos links si hace falta

1. Abrir `https://paris-penalty-clan-sellers.trycloudflare.com`.
2. Ingresar la clave de organizador provista por el owner. En el servidor está en `.env` como `TEG_ADMIN_TOKEN`.
3. Crear una partida nueva.
4. Desde `Cuartel general`, usar `Reclutar jugador` y `+ Generar link`.
5. Copiar cada link y abrirlo en un browser context aislado.

## Cómo reiniciar la prueba

La forma segura es crear una partida nueva desde la landing. No borrar datos de producción durante el test.

Si la sala precreada ya fue iniciada o quedó en estado no reutilizable:

1. Crear nueva partida desde la landing con la clave de organizador.
2. Generar nuevos links para admin/jugadores.
3. Repetir la prueba desde lobby.

## Alcance de la prueba

Evaluar funcionalidad, no calidad estética. No frenar por mapa, responsive o pulido visual salvo que impidan jugar.

Probar:

1. Administración.
2. Creación de perfiles.
3. Generación de links.
4. Acceso por links.
5. Lobby.
6. Inicio.
7. Colocación inicial.
8. Turnos.
9. Refuerzos.
10. Ataque.
11. Dados.
12. Bajas.
13. Conquista.
14. Movimiento posterior a conquista.
15. Reagrupamiento.
16. Finalización del turno.
17. Cambio de jugador.
18. Estado multicliente.
19. Desconexión.
20. Reconexión.
21. Recarga de página.
22. Errores.
23. Persistencia.
24. Finalización o continuidad de la partida.

## Contextos Playwright

Crear al menos cuatro browser contexts aislados:

- `admin`
- `player-a`
- `player-b`
- `player-c`

No usar pestañas que compartan cookies. Cada link debe abrirse en un contexto independiente.

## Evidencias obligatorias

Guardar:

- Capturas.
- Video.
- Trace.
- Consola.
- Requests fallidas.
- Errores WebSocket.
- Timeline de acciones.

## Clasificación

- BLOCKER: no permite continuar la partida.
- CRITICAL: produce estado incorrecto, pérdida de tropas, dados incorrectos, jugador incorrecto o desincronización.
- MAJOR: el flujo funciona, pero requiere recarga, repetición o workaround.
- MINOR: problema visual, texto, alineación o feedback que no impide jugar.

## Problemas visuales conocidos fuera de alcance

- Mapa geográfico desalineado.
- Polígonos todavía imperfectos.
- Layout QHD/4K con espacio desperdiciado.
- Estética incompleta.
- Animaciones no terminadas.
- Audio no terminado.
- Tribuna incompleta.
- Responsive no definitivo.

El tester puede documentarlos, pero no debe frenar la prueba funcional por estos puntos.

## Preguntas que debe responder el tester

1. ¿Se puede iniciar una partida?
2. ¿Todos entran con identidad correcta?
3. ¿Todos ven el mismo estado?
4. ¿Se puede completar la colocación inicial?
5. ¿Se puede ejecutar un turno completo?
6. ¿Los ataques modifican correctamente las tropas?
7. ¿Los dados coinciden en todos los clientes?
8. ¿Las bajas son consistentes?
9. ¿La conquista funciona?
10. ¿El cambio de turno funciona?
11. ¿La reconexión recupera el estado?
12. ¿Existe algún punto donde la partida queda bloqueada?
13. ¿Qué workaround fue necesario?
14. ¿Se puede seguir jugando durante al menos tres turnos completos?
15. ¿La release es funcionalmente jugable: sí o no?

## Flujo mínimo sugerido

1. Abrir `admin_join` en el contexto `admin` y entrar al lobby.
2. Abrir `Player A`, `Player B` y `Player C` en contextos separados.
3. Confirmar identidad en cada contexto.
4. Marcar jugadores listos.
5. Si el contexto admin no muestra controles de inicio, abrir también la `Admin page` en el contexto `admin` después de haber ingresado con el join link.
6. Iniciar la partida.
7. Completar colocación inicial de todos los jugadores.
8. Identificar jugador activo y fase actual.
9. Colocar refuerzos.
10. Pasar a ataque.
11. Atacar un territorio válido.
12. Verificar dados y bajas en todos los contextos.
13. Si hay conquista, mover tropas.
14. Detener ataque.
15. Reagrupar si la UI lo permite.
16. Terminar turno.
17. Confirmar siguiente jugador activo.
18. Cerrar o desconectar un contexto, reabrir el mismo link y verificar recuperación de estado.
19. Recargar todos los contextos y confirmar sincronización.
20. Continuar al menos tres turnos completos o registrar el primer bloqueo real.
