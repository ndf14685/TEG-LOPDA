# Accessibility audit (observaciones)

## Positivo observado
- **prefers-reduced-motion**: la Arena de combate respeta la preferencia (animación de dados en 0ms si está activa). Buen detalle.
- **Teclado**: Esc cierra la Arena de combate.
- **Audio opt-in**: comentarista ("voz OFF") y sonidos ("Sonidos: OFF") silenciados por defecto, con toggles para activar → no hay autoplay sorpresivo (respeta restricción de autoplay).
- **Texto del relator siempre visible** (no depende del audio) → sirve para usuarios que no oyen.
- **Instrucciones en texto** por fase (no solo color): "Tocá tus países…", "Tocá un país tuyo (borde dorado)…".

## A verificar / pendiente (no cubierto a fondo)
- Contraste AA/AAA de textos chicos (labels [10px] gris sobre fondo oscuro en la Arena) — revisar.
- Dependencia de color para dueño de país: el color distingue bandos; conviene un refuerzo no-cromático (patrón/inicial) para daltonismo.
- Subtítulos para audios de bardeo/relator cuando el audio esté activo.
- Navegación por teclado completa del mapa (seleccionar países sin mouse) — no verificada.
- Foco visible y orden de tabulación en paneles — no auditado en profundidad.

## Nota
Auditoría de accesibilidad superficial dentro del fast-track; recomendada una pasada dedicada con lector de pantalla y verificador de contraste.
