# Risk Register

Fecha: 2026-07-25

| ID | Riesgo | Severidad | Evidencia | Mitigacion |
|---|---|---:|---|---|
| R1 | Contratos divergentes entre TS, JSON y docs | Alta | `client-messages.schema.json` esta atrasado | Conciliar contratos antes de nuevas features |
| R2 | "Juego completo" no demostrado en flujos reales | Alta | E2E cubre solo slice estrecho | Verticales con gates y playtest externo |
| R3 | Tribuna/Monedas no implementadas como ledger transaccional | Alta | No existe tabla ledger ni eventos `bet.market.*` | Bloquear Vertical 3 hasta contrato backend |
| R4 | Assets declarados READY faltan fisicamente | Media | Inventario declara OGG/WEBP/SVG inexistentes | Agy debe entregar manifest real auditado |
| R5 | UI actual todavia se percibe como panel denso | Media | Capturas 1280x720 muestran mapa comprimido y paneles laterales | Rediseño enfocado en Vertical 1 |
| R6 | Cobertura automatizada insuficiente para experiencia | Media | Sin reporte de coverage; E2E no cubre ataque/conquista/reconexion | Plan de E2E por vertical |
| R7 | Trabajo sin commitear en docs/assets/prototipo | Media | `git status` lista carpetas nuevas sin trackear | Rama/commit controlado antes de entregar a agentes |
| R8 | Documentacion tecnica antigua induce errores | Media | README/overview conservan TODOs falsos | Actualizar docs oficiales y marcar docs viejos como referencia |
| R9 | Mapa no reconocible como mapamundi | Alta | Capturas de playtest/e2e muestran continentes dependientes de titulos y etiquetas | Rediseño P0 en capas: base geografica, territorios, hitboxes y overlays; validar primero direccion y luego region piloto |
