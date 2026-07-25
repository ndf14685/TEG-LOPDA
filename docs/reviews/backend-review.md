# Backend Review

Fecha: 2026-07-25

## Resultado

Base tecnica aceptable, no aprobada para avanzar sin contratos.

## Evidencia

`uv run pytest -q` -> 83 passed. Existen FastAPI, WebSocket, SQLite, eventos, state_json, snapshots, reglas parciales, ataques territoriales, objetivos, cartas y pactos.

## Hallazgos

- Contratos JSON/MD atrasados respecto del TS y codigo.
- Comentarios TODO en `engine.py` y docs antiguos contradicen implementacion parcial.
- Apuestas actuales son refuerzos en state_json, no ledger transaccional ni Tribuna.
- E2E no valida ataque/conquista/reconexion durante combate.

## Proxima accion

Conciliar contratos de Vertical 1 antes de feature work.
