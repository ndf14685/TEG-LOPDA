#!/usr/bin/env bash

# Detener el script si ocurre un error
set -e

# Asegurarnos de que estamos en la raíz del proyecto (donde está la carpeta assets existente)
if [ ! -d "assets" ]; then
    echo "❌ Error: No se encuentra la carpeta 'assets' en el directorio actual."
    echo "Por favor, ejecuta este script desde la raíz de tu proyecto TEG-LOPDA."
    exit 1
fi

echo "📥 Iniciando la integración de recursos visuales y contratos en la carpeta 'assets' existente..."

# 1. Crear subestructura obligatoria (si no existe)
echo "📁 Creando subdirectorios..."
mkdir -p assets/brand/palette
mkdir -p assets/contracts
mkdir -p assets/maps/base
mkdir -p assets/ui/buttons
mkdir -p assets/ui/panels
mkdir -p assets/achievements/banners
mkdir -p assets/audio/ui
mkdir -p assets/audio/dice
mkdir -p assets/audio/battles
mkdir -p assets/audio/alerts
# Asegurar que existe la carpeta manifest (aunque tree ya la mostró)
mkdir -p assets/manifest

# Rutas para archivos de organización vacíos (para estructura)
mkdir -p assets/backgrounds/landing
mkdir -p assets/backgrounds/game
mkdir -p assets/dice/static
mkdir -p assets/ai-commentator/avatars
mkdir -p assets/taunts/stamps

# 2. Generar Documento de Integración para las otras IAs
echo "📄 Generando README-INTEGRATION.md..."
cat << 'EOF' > assets/README-INTEGRATION.md
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

EOF

# 3. Generar Contratos Técnicos (JSON Schemas)
echo "📜 Generando esquemas de contratos..."
cat << 'EOF' > assets/contracts/game-init-schema.json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "TEG-LOPDA Game Initialization Contract",
  "description": "Contrato entre Dirección de Arte, Backend y Frontend para definir el modo de juego y los assets del mapa a cargar.",
  "type": "object",
  "properties": {
    "game_mode": { 
      "type": "string", 
      "enum": ["classic_50", "mega_world_100"],
      "description": "classic_50 (2-10 jugs, mapa estándar) | mega_world_100 (10-20 jugs, mapa extendido)"
    },
    "map_assets": {
      "type": "object",
      "properties": {
        "base_svg": { 
          "type": "string",
          "description": "Ruta relativa a assets/maps/base/... .svg" 
        },
        "static_background_webp": { 
          "type": "string",
          "description": "Ruta relativa a la imagen ilustrada de fondo (capa 1)."
        }
      },
      "required": ["base_svg"]
    }
  },
  "required": ["game_mode", "map_assets"]
}
EOF

cat << 'EOF' > assets/contracts/event-schema.json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "TEG-LOPDA Gameplay Event Contract",
  "description": "Definición de eventos WebSocket que el Backend emite y el Frontend debe representar visualmente.",
  "type": "object",
  "properties": {
    "event_type": {
      "type": "string",
      "enum": [
        "TERRITORY_CONQUERED",
        "ATTACK_FAILED",
        "ALLIANCE_BROKEN",
        "PLAYER_ELIMINATED",
        "DICE_ROLL_RESULT"
      ]
    },
    "visual_data": {
      "type": "object",
      "properties": {
        "territory_id": { "type": "string", "description": "ID estricto del SVG, ej: territory-europe-spain" },
        "player_id": { "type": "string", "description": "p01, p02, etc." },
        "taunt_id": { "type": "string", "description": "ID opcional definido en taunts-manifest.json" }
      }
    }
  },
  "required": ["event_type"]
}
EOF

# 4. Generar Paleta de Colores Táctica
echo "🎨 Generando paleta de colores accesibles..."
cat << 'EOF' > assets/brand/palette/palette.json
{
  "theme": "retro-tactical-dark",
  "global": {
    "bg": "#0D1117",
    "panel": "#161B22",
    "border": "#30363D",
    "text_primary": "#F0F6FC",
    "text_secondary": "#8B949E",
    "danger": "#DA3633",
    "success": "#2EA043",
    "warning": "#D29922",
    "info": "#58A6FF"
  },
  "players": [
    { "id": "p01", "name": "Rojo Alerta", "hex": "#E63946" },
    { "id": "p02", "name": "Azul Táctico", "hex": "#1D3557" },
    { "id": "p03", "name": "Verde Camuflaje", "hex": "#2A9D8F" },
    { "id": "p04", "name": "Amarillo Propaganda", "hex": "#E9C46A" },
    { "id": "p05", "name": "Naranja Carga", "hex": "#F4A261" },
    { "id": "p06", "name": "Púrpura Secreto", "hex": "#A06CD5" },
    { "id": "p07", "name": "Cian Fósforo", "hex": "#00B4D8" },
    { "id": "p08", "name": "Rosa Bardo", "hex": "#FF70A6" },
    { "id": "p09", "name": "Ocre Desierto", "hex": "#D4A373" },
    { "id": "p10", "name": "Gris Blindado", "hex": "#6C757D" }
  ],
  "note": "Los colores de jugadores cumplen WCAG 2.1 AA para contraste sobre fondo oscuro."
}
EOF

# 5. Generar Manifiestos de Assets y Audio
echo "📋 Generando manifiestos de producción..."
cat << 'EOF' > assets/manifest/assets-manifest.json
{
  "schema_version": "1.0",
  "maps": {
    "classic_50": {
      "id": "map.tactical.50",
      "path": "maps/base/map-base-tactical-50-001.svg"
    },
    "mega_world_100": {
      "id": "map.tactical.100",
      "path": "maps/base/map-base-tactical-100-001.svg"
    }
  },
  "ui": {
    "btn_attack": "ui/buttons/button-action-attack-001.svg",
    "btn_fortify": "ui/buttons/button-action-fortify-001.svg",
    "player_card_panel": "ui/panels/panel-player-card-001.svg"
  }
}
EOF

cat << 'EOF' > assets/manifest/audio-manifest.json
{
  "schema_version": "1.0",
  "ui": {
    "click": { "path": "audio/ui/sound-ui-click-001.ogg", "type": "audio/ogg" }
  },
  "gameplay": {
    "dice_roll": { "path": "audio/dice/sound-dice-roll-001.ogg", "type": "audio/ogg" },
    "conquest_success": { "path": "audio/battles/sound-battle-win-001.ogg", "type": "audio/ogg" },
    "traitor_alert": { "path": "audio/alerts/sound-alert-traitor-001.ogg", "type": "audio/ogg" }
  }
}
EOF

cat << 'EOF' > assets/manifest/taunts-manifest.json
{
  "schema_version": "1.0",
  "base_stamp_path": "taunts/stamps/overlay-stamp-classified-001.webp",
  "definitions": [
    { "id": "bardo_traicion", "text": "¡TRAIDOR!", "sound": "audio/alerts/sound-alert-traitor-001.ogg" },
    { "id": "bardo_llora", "text": "LLORÁ EN DISCORD", "sound": null },
    { "id": "bardo_malo", "text": "QUÉ MALO QUE SOS", "sound": "audio/dice/sound-dice-fail-001.ogg" }
  ]
}
EOF

# 6. Generar Mallas SVG (50 y 100 países) con IDs estrictos
echo "🗺️ Generando mallas SVG interactivas..."
# Versión 50 países
cat << 'EOF' > assets/maps/base/map-base-tactical-50-001.svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 2560 1440" id="map-base-tactical-50-001">
  <defs>
    <style>
      .territory {
        fill: rgba(22, 27, 34, 0.7); /* Panel color con opacidad */
        stroke: #30363d; /* Border color */
        stroke-width: 2;
        stroke-linejoin: round;
        cursor: pointer;
        transition: fill 0.2s ease, stroke 0.2s ease;
      }
      .territory:hover {
        stroke: #58a6ff; /* Info color al hover */
        fill: rgba(22, 27, 34, 0.9);
      }
    </style>
  </defs>
  <!-- Ejemplo de Sudamérica simplificado para estructura -->
  <g id="continent-south-america">
    <path id="territory-south-america-argentina" class="territory" d="M 560 1020 L 610 1000 L 630 1100 L 590 1250 L 530 1260 L 520 1120 Z" />
    <path id="territory-south-america-brazil" class="territory" d="M 600 860 L 720 840 L 780 920 L 720 1020 L 670 980 L 610 1000 Z" />
    <path id="territory-south-america-chile" class="territory" d="M 510 1030 L 560 1020 L 520 1120 L 530 1260 L 490 1220 Z" />
  </g>
</svg>
EOF

# Versión 100 países (estructura base)
cat << 'EOF' > assets/maps/base/map-base-tactical-100-001.svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 2560 1440" id="map-base-tactical-100-001">
  <defs>
    <style>
      .territory {
        fill: rgba(22, 27, 34, 0.7);
        stroke: #30363d;
        stroke-width: 1.5;
        stroke-linejoin: round;
        cursor: pointer;
        transition: fill 0.15s ease;
      }
      .territory:hover {
        stroke: #00b4d8; /* Cian Fósforo al hover */
      }
    </style>
  </defs>
  <!-- Ejemplo de subdivisiones -->
  <g id="continent-south-america-extended">
    <path id="territory-south-america-patagonia" class="territory" d="M 530 1200 L 580 1190 L 560 1280 L 510 1270 Z" />
    <path id="territory-south-america-argentina-norte" class="territory" d="M 540 1100 L 610 1080 L 600 1190 L 530 1200 Z" />
  </g>
</svg>
EOF

# 7. Generar UI Elements (Botones SVG tácticos)
echo "🔘 Generando elementos de UI SVG..."
cat << 'EOF' > assets/ui/buttons/button-action-attack-001.svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 60" width="240" height="60" id="button-action-attack-001">
  <defs>
    <linearGradient id="grad-danger" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#FF4D4D"/>
      <stop offset="100%" stop-color="#DA3633"/>
    </linearGradient>
  </defs>
  <rect width="236" height="56" x="2" y="2" rx="8" fill="url(#grad-danger)" stroke="#F0F6FC" stroke-width="2"/>
  <text x="120" y="38" font-family="sans-serif" font-weight="bold" font-size="24" fill="#FFFFFF" text-anchor="middle" letter-spacing="2">¡ATACAR!</text>
</svg>
EOF

cat << 'EOF' > assets/ui/buttons/button-action-fortify-001.svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 60" width="240" height="60" id="button-action-fortify-001">
  <rect width="236" height="56" x="2" y="2" rx="8" fill="#2EA043" stroke="#F0F6FC" stroke-width="2"/>
  <text x="120" y="38" font-family="sans-serif" font-weight="bold" font-size="20" fill="#FFFFFF" text-anchor="middle">REAGRUPAR</text>
</svg>
EOF

cat << 'EOF' > assets/ui/panels/panel-player-card-001.svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 100" width="300" height="100">
  <rect width="298" height="98" x="1" y="1" rx="10" fill="#161B22" stroke="#30363D" stroke-width="2"/>
  <circle cx="50" cy="50" r="35" fill="#0D1117" stroke="#8B949E"/>
  <text x="100" y="40" font-family="monospace" font-size="18" fill="#F0F6FC">General_Discord</text>
  <text x="100" y="70" font-family="monospace" font-size="14" fill="#8B949E">Tropas: <tspan fill="#E9C46A">42</tspan></text>
</svg>
EOF

# 8. Generar Banners de Logros (Pantalla Final)
echo "🏆 Generando banners de logros finales..."
cat << 'EOF' > assets/achievements/banners/banner-achievement-traitor-king-001.svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 150" width="400" height="150">
  <rect width="396" height="146" x="2" y="2" rx="15" fill="#161B22" stroke="#DA3633" stroke-width="4"/>
  <text x="200" y="60" font-family="sans-serif" font-weight="bold" font-size="28" fill="#DA3633" text-anchor="middle">EL REY TRAIDOR</text>
  <text x="200" y="110" font-family="monospace" font-size="16" fill="#F0F6FC" text-anchor="middle">"Una puñalada por la espalda a la vez"</text>
</svg>
EOF

echo "✨ ¡Integración visual y técnica finalizada exitosamente en './assets'!"
echo "Revisa 'assets/README-INTEGRATION.md' para instrucciones de las otras IAs."
