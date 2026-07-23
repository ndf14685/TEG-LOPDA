"""Modos de juego y assets de mapa asociados.

Contrato: assets/contracts/game-init-schema.json (Dirección de Arte).
Las rutas son IDs lógicos estables relativos al directorio assets/.
"""

from __future__ import annotations

DEFAULT_MODE = "classic_26"

GAME_MODES: dict[str, dict] = {
    # el mapa táctico original: rápido, 26 países
    "classic_26": {
        "map_id": "tactical-26",
        "min_players": 2,
        "max_players": 8,
        "map_assets": {
            "base_svg": "maps/base/map-base-tactical-26-001.svg",
            "static_background_webp": None,
        },
    },
    # mundo extendido de 50 países
    "classic_50": {
        "map_id": "world-50",
        "min_players": 2,
        "max_players": 10,
        "map_assets": {
            "base_svg": "maps/base/map-base-tactical-50-001.svg",
            "static_background_webp": None,
        },
    },
    # mega mundo: los 50 países divididos en norte/sur (100 territorios)
    "mega_world_100": {
        # el contrato de arte dice "10-20 jugs"; no se bloquea el mínimo
        # hasta confirmarlo con el grupo. TODO(game-modes): definir mínimo.
        "map_id": "mega-100",
        "min_players": 2,
        "max_players": 20,
        "map_assets": {
            "base_svg": "maps/base/map-base-tactical-100-001.svg",
            "static_background_webp": None,
        },
    },
}
