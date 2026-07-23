"""Genera mallas SVG placeholder para los mapas world-50 y mega-100.

Formas orgánicas deterministas (jitter por hash del id), agrupadas por
continente en disposición de planisferio, con rutas marítimas punteadas
para las fronteras entre continentes. Cumple el contrato de
assets/maps/PROMPT-REGENERAR-MAPAS.md; pensadas para ser reemplazadas por
arte definitivo generado por IA con ese prompt.

Uso: uv run python scripts/gen_map_mesh.py
"""

from __future__ import annotations

import hashlib
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from teg_backend.domain.map import load_map  # noqa: E402

OUT_DIR = Path(__file__).resolve().parents[2] / "assets" / "maps" / "base"

# regiones (x, y, ancho, alto) por continente, disposición planisferio
REGIONS = {
    "north-america": (70, 150, 750, 500),
    "south-america": (260, 720, 500, 620),
    "europe": (930, 150, 620, 420),
    "africa": (980, 640, 540, 620),
    "asia": (1620, 150, 860, 620),
    "oceania": (1720, 870, 620, 400),
}

TITLE_POS = {
    "north-america": (445, 130),
    "south-america": (510, 700),
    "europe": (1240, 130),
    "africa": (1250, 622),
    "asia": (2050, 130),
    "oceania": (2030, 850),
}

STYLE = """
      .territory {
        fill: rgba(30, 35, 45, 0.85);
        stroke: #0b1220;
        stroke-width: 4;
        stroke-linejoin: round;
        cursor: pointer;
        transition: fill 0.2s ease, stroke 0.2s ease, filter 0.2s ease;
      }
      .territory:hover { stroke: #38bdf8; filter: brightness(1.25); }
      .territory.selected { stroke: #fbbf24; stroke-width: 8; filter: brightness(1.35); }
      .territory.attack-source { stroke: #38bdf8; stroke-width: 8; }
      .territory.attack-target { stroke: #ef4444; stroke-width: 8; stroke-dasharray: 14 8; }
      .territory.attackable { stroke: #22d3ee; stroke-width: 6; stroke-dasharray: 6 6; }
      .territory-label {
        fill: #f1f5f9;
        font-family: ui-sans-serif, system-ui, sans-serif;
        font-weight: 700;
        paint-order: stroke;
        stroke: rgba(2, 6, 23, 0.85);
        stroke-width: 6px;
        stroke-linejoin: round;
        pointer-events: none;
        text-anchor: middle;
      }
      .continent-title {
        fill: rgba(148, 163, 184, 0.5);
        font-family: ui-sans-serif, system-ui, sans-serif;
        font-size: 44px;
        font-weight: 900;
        letter-spacing: 4px;
        pointer-events: none;
        text-anchor: middle;
        text-transform: uppercase;
      }
      .sea-route {
        stroke: rgba(125, 211, 252, 0.35);
        stroke-width: 3;
        stroke-dasharray: 10 12;
        fill: none;
        pointer-events: none;
      }
"""


def _jitter(tid: str, salt: int, amplitude: float) -> float:
    digest = hashlib.sha256(f"{tid}:{salt}".encode()).digest()
    return (digest[0] / 255 - 0.5) * 2 * amplitude


def blob_path(tid: str, cx: float, cy: float, rx: float, ry: float) -> str:
    """Polígono orgánico de 8 puntos con curvas cuadráticas y jitter estable."""
    points = []
    for i in range(8):
        angle = math.tau * i / 8
        rr_x = rx * (1 + _jitter(tid, i, 0.16))
        rr_y = ry * (1 + _jitter(tid, i + 100, 0.16))
        points.append((cx + rr_x * math.cos(angle), cy + rr_y * math.sin(angle)))
    d = f"M {points[0][0]:.0f} {points[0][1]:.0f} "
    for i in range(1, len(points) + 1):
        px, py = points[i % 8]
        mx, my = points[i - 1]
        ctrl_x = (mx + px) / 2 + _jitter(tid, i + 200, rx * 0.15)
        ctrl_y = (my + py) / 2 + _jitter(tid, i + 300, ry * 0.15)
        d += f"Q {ctrl_x:.0f} {ctrl_y:.0f} {px:.0f} {py:.0f} "
    return d + "Z"


def generate(map_id: str, svg_id: str, label_size: int) -> str:
    gmap = load_map(map_id)
    by_continent: dict[str, list[str]] = {}
    for tid, terr in gmap.territories.items():
        by_continent.setdefault(terr.continent_id, []).append(tid)

    centers: dict[str, tuple[float, float]] = {}
    shapes: list[str] = []
    labels: list[str] = []
    titles: list[str] = []

    for cid, tids in by_continent.items():
        tids.sort()
        x, y, w, h = REGIONS[cid]
        n = len(tids)
        cols = max(2, round(math.sqrt(n * (w / h))))
        rows = math.ceil(n / cols)
        cell_w, cell_h = w / cols, h / rows
        name = gmap.continents[cid].name
        tx, ty = TITLE_POS[cid]
        titles.append(f'    <text x="{tx}" y="{ty}" class="continent-title">{name}</text>')
        for i, tid in enumerate(tids):
            col, row = i % cols, i // cols
            cx = x + cell_w * (col + 0.5)
            cy = y + cell_h * (row + 0.5)
            rx, ry = cell_w * 0.44, cell_h * 0.40
            centers[tid] = (cx, cy)
            shapes.append(
                f'    <path id="{tid}" class="territory" d="{blob_path(tid, cx, cy, rx, ry)}" />'
            )
            labels.append(
                f'    <text x="{cx:.0f}" y="{cy - ry * 0.45:.0f}" class="territory-label"'
                f' font-size="{label_size}">{gmap.territories[tid].name}</text>'
            )

    routes: list[str] = []
    seen: set[frozenset] = set()
    for tid, terr in gmap.territories.items():
        for nb in terr.neighbor_ids:
            pair = frozenset((tid, nb))
            if pair in seen:
                continue
            seen.add(pair)
            if gmap.territories[nb].continent_id != terr.continent_id:
                (x1, y1), (x2, y2) = centers[tid], centers[nb]
                routes.append(
                    f'    <line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" class="sea-route" />'
                )

    groups = "\n".join(
        f'  <g id="continent-{cid}">\n' + "\n".join(
            s for s in shapes if f'id="territory-{cid}-' in s
        ) + "\n  </g>"
        for cid in by_continent
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 2560 1440" id="{svg_id}">
  <defs>
    <style>{STYLE}    </style>
    <radialGradient id="ocean-grad" cx="50%" cy="42%" r="75%">
      <stop offset="0%" stop-color="#0e2a47" />
      <stop offset="60%" stop-color="#0a1e35" />
      <stop offset="100%" stop-color="#060f1d" />
    </radialGradient>
    <pattern id="ocean-grid" width="120" height="120" patternUnits="userSpaceOnUse">
      <path d="M 120 0 L 0 0 0 120" fill="none" stroke="rgba(96, 165, 250, 0.06)" stroke-width="1.5" />
    </pattern>
  </defs>

  <rect x="0" y="0" width="2560" height="1440" fill="url(#ocean-grad)" />
  <rect x="0" y="0" width="2560" height="1440" fill="url(#ocean-grid)" />

  <g id="sea-routes">
{chr(10).join(routes)}
  </g>

{groups}

  <g id="territory-labels">
{chr(10).join(labels)}
  </g>

  <g id="continent-titles">
{chr(10).join(titles)}
  </g>
</svg>
"""


if __name__ == "__main__":
    for map_id, filename, label_size in (
        ("world-50", "map-base-tactical-50-001.svg", 26),
        ("mega-100", "map-base-tactical-100-001.svg", 19),
    ):
        svg = generate(map_id, filename.removesuffix(".svg"), label_size)
        out = OUT_DIR / filename
        out.write_text(svg, encoding="utf-8")
        print(f"{out} ({len(svg)} bytes)")
