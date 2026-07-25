# Current Status

Fecha: 2026-07-25

## Evidencia relevada

- Git: rama `main`, sincronizada con `origin/main` en `6df790f`.
- Working tree: hay archivos no commiteados en `assets/manifests/`, `design/`, `docs/design/` y `frontend/public/prototype/`.
- Tests backend: `uv run pytest -q` en `backend/` -> 83 passed, 1 warning.
- Tests frontend: `pnpm test` -> 33 passed.
- Typecheck: `pnpm typecheck` -> passed.
- Build: `pnpm build` -> passed.
- E2E local: `pnpm e2e` -> 2 passed.
- Capturas E2E: `test-results/slice-admin-board.png`, `test-results/slice-player-board.png`, 1280x720.

## Terminado y verificado

- Backend FastAPI + SQLite + WebSocket arranca y pasa suite automatizada.
- Persistencia base de partidas, jugadores, eventos, state_json y snapshots de turno existe.
- Eventos persistidos tienen `sequence_number` monotono por partida.
- Flujo local E2E verificado: crear partida, invitar, entrar por link, lobby, ready, iniciar, colocacion inicial 5+3, comentarista, tirada de dados sincronizada en dos contextos.
- Frontend compila, typecheckea y consume contratos TS compartidos.
- Mapa SVG interactivo carga en el flujo E2E y permite colocacion/refuerzos por click.

## Implementado parcialmente

- Reglas TEG: existen mapa tactico, colocacion 5+3, refuerzos, ataque territorial, conquista, eliminacion, cartas, objetivos, pactos y reagrupamiento, pero no todo esta cubierto por E2E multi-cliente.
- Combate: backend calcula dados, comparaciones y bajas; frontend muestra resultado ultimo, pero no demuestra explicacion completa de cantidad de dados, motivos, tropas iniciales/finales ni historial acumulado.
- Reconexion: hay soporte de snapshot y tests backend, pero no hay E2E de reconexion durante combate o colocacion.
- UI tactica: hay interaccion sobre mapa, pero todavia convive con paneles densos, botones de formulario y un input numerico para reagrupamiento.
- Assets: hay mapas, botones, panel y audios WAV reales, pero varios manifiestos declaran assets inexistentes o con rutas incompatibles.

## Disenado pero no implementado

- Tribuna con Monedas LOPDA, mercado de apuestas, tickets, bloqueo, resolucion, reembolso y ledger transaccional.
- Arena de combate con desglose matematico completo, explicacion de empates y resumen acumulado.
- Prototipo navegable de alta fidelidad para todos los estados pedidos.
- Estados visuales completos para error, reconexion, victoria, pago, traicion y apuesta.
- Layout validado en 1920x1080 y 1366x768.

## Declarado pero no demostrado

- Commits y docs declaran "juego completo sin pendientes"; la evidencia E2E cubre solo un slice estrecho.
- `docs/architecture/overview.md` y comentarios en `engine.py` todavia declaran TODOs de reglas que el codigo ya implemento parcialmente.
- `shared/contracts/websocket/client-messages.schema.json` esta atrasado respecto de `shared/contracts/src/ws-events.ts` y no incluye mensajes actuales como `turn.place_reinforcement`, `turn.fortify`, `turn.next_phase`, `turn.wager`, `cards.trade`, `placement.place` y pactos.
- `assets/manifests/missing-assets.md` lista como READY archivos que no existen fisicamente.

## Estado operativo

No se habilita implementacion nueva de Backend ni Frontend hasta cerrar fuente unica de contratos y alcance de Vertical 1. Agy puede continuar primero con correccion de entregables de diseno y assets porque bloquea las demas areas.
