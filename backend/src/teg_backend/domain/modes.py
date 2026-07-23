"""Modos de juego y assets de mapa asociados.

Contrato: assets/contracts/game-init-schema.json (Dirección de Arte).
Las rutas son relativas al directorio assets/ y son IDs lógicos estables.
"""

from __future__ import annotations

DEFAULT_MODE = "classic_50"

GAME_MODES: dict[str, dict] = {
    "classic_50": {
        "min_players": 2,
        "max_players": 10,
        "map_assets": {
            "base_svg": "maps/base/map-base-tactical-50-001.svg",
            # aún no hay asset en assets/backgrounds/game/
            "static_background_webp": None,
        },
    },
    "mega_world_100": {
        # el contrato dice "10-20 jugs"; no se bloquea el mínimo hasta
        # confirmarlo con el grupo. TODO(game-modes): definir mínimo real.
        "min_players": 2,
        "max_players": 20,
        "map_assets": {
            "base_svg": "maps/base/map-base-tactical-100-001.svg",
            "static_background_webp": None,
        },
    },
}
