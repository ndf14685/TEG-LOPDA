# 🤖 Guía de Integración de Assets (Dirección de Arte)

Este directorio `assets/` ha sido poblado con la identidad visual original, las mallas tácticas del mapa y, fundamentalmente, los contratos de datos que definen la interacción entre el Frontend, el Backend y estos recursos.

## ⚠️ Acciones Requeridas para las IAs de Desarrollo:

### Para la IA de Backend:
1.  **Contrato de Mapeo:** Revisa `assets/contracts/game-init-schema.json`. Debes asegurar que la inicialización de la partida envíe el campo `game_mode` (`classic_50` o `mega_world_100`) y las rutas a los assets correspondientes detallados allí.
2.  **IDs de Territorios:** Tus estados de juego (dueño de país, cantidad de tropas) **deben** usar exclusivamente los IDs detallados en las mallas SVG (ej: `territory-south-america-argentina`).
3.  **Eventos:** Al emitir eventos (conquistas, traiciones), usa los tipos definidos en `assets/contracts/event-schema.json`.

### Para la IA de Frontend:
1.  **Carga de Mapas:** No uses imágenes estáticas para el mapa interactivo. Inyecta dinámicamente los SVGs de `assets/maps/base/` en el DOM. Manipula `path.style.fill` usando la paleta definida en `assets/brand/palette/palette.json`.
2.  **Manifiestos:** Usa `assets/manifest/assets-manifest.json` y `assets/manifest/audio-manifest.json` para precargar y referenciar dinámicamente las rutas de imágenes y sonidos. No hardcodees rutas.
3.  **Bardos/Reacciones:** Revisa `assets/manifest/taunts-manifest.json`. El backend te dirá qué bardo usar; tú debes renderizar el texto dinámico sobre el stamp visual.

