# Diplomacy audit

## Estado en la sesión
El panel **DIPLOMACIA** existe en La Tribuna (colapsable) y en el lobby se probó **chat privado** con visibilidad correcta:
- Nessi ve canal "privado: Daro".
- Daro ve canal "privado: Nessi".
- Tribu (espectador) ve ambos privados listados.

## No ejercitado a fondo (pendiente pasada extendida)
- Proponer pacto / aceptar / rechazar (existe UI de propuesta entrante: `pact-proposal` con Aceptar/Rechazar en GamePage).
- Vencimiento / ruptura / traición y su notificación.
- Comentario del relator ante traición.
- Apuestas relacionadas a pactos.

## Recomendación
Ejecutar en una pasada con 3+ jugadores activos: proponer pacto Nessi↔Daro, romperlo (traición) y verificar notificación + comentario del relator + visibilidad correcta (que el tercero no vea lo privado). No se detectaron problemas en lo probado (chat privado), pero el flujo de pactos queda por auditar.
