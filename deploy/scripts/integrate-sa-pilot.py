#!/usr/bin/env python3
"""P0 Mapa — integra la geometría realista aprobada de América del Sur
(frontend/public/prototype/south-america-pilot.html) en el mapa productivo
del modo 50, conservando IDs y sin tocar el resto del mundo.

- Transforma las coordenadas del piloto al hueco actual de Sudamérica.
- Capa visible (.territory) + capa de hitboxes (.territory-hitbox) separadas.
- Labels en el tercio superior según el piloto.
Reproducible: correr de nuevo regenera la sección completa.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PILOT = ROOT / "frontend/public/prototype/south-america-pilot.html"
TARGET = ROOT / "assets/maps/base/map-base-tactical-50-001.svg"

# hueco actual de Sudamérica en el mapa productivo (bbox del grupo viejo)
DST = {"x0": 273.0, "y0": 734.0, "x1": 761.0, "y1": 1315.0}

SA_LABELS = {
    "territory-south-america-colombia": "Colombia",
    "territory-south-america-venezuela": "Venezuela",
    "territory-south-america-peru": "Perú",
    "territory-south-america-brazil": "Brasil",
    "territory-south-america-bolivia": "Bolivia",
    "territory-south-america-chile": "Chile",
    "territory-south-america-argentina": "Argentina",
    "territory-south-america-uruguay": "Uruguay",
}


def extract_pilot() -> tuple[dict[str, str], dict[str, tuple[float, float]]]:
    html = PILOT.read_text(encoding="utf-8")
    paths: dict[str, str] = {}
    for tid in SA_LABELS:
        m = re.search(rf'id="{tid}" class="[^"]*" d="([^"]+)"', html)
        if not m:
            raise SystemExit(f"falta el path del piloto: {tid}")
        paths[tid] = m.group(1)
    labels: dict[str, tuple[float, float]] = {}
    for x, y, text in re.findall(
        r'<text x="(\d+)" y="(\d+)" class="territory-label[^"]*">([^<]+)</text>', html
    ):
        for tid, name in SA_LABELS.items():
            if name == text:
                labels[tid] = (float(x), float(y))
    return paths, labels


def affine(paths: dict[str, str]) -> tuple[float, float, float]:
    nums = [
        (float(a), float(b))
        for d in paths.values()
        for a, b in re.findall(r"([-\d.]+)[ ,]([-\d.]+)", d)
    ]
    x0, x1 = min(p[0] for p in nums), max(p[0] for p in nums)
    y0, y1 = min(p[1] for p in nums), max(p[1] for p in nums)
    # encaje uniforme centrado en el hueco de destino
    s = min((DST["x1"] - DST["x0"]) / (x1 - x0), (DST["y1"] - DST["y0"]) / (y1 - y0))
    tx = DST["x0"] + ((DST["x1"] - DST["x0"]) - (x1 - x0) * s) / 2 - x0 * s
    ty = DST["y0"] + ((DST["y1"] - DST["y0"]) - (y1 - y0) * s) / 2 - y0 * s
    return s, tx, ty


def transform_d(d: str, s: float, tx: float, ty: float) -> str:
    def repl(m: re.Match) -> str:
        x, y = float(m.group(1)), float(m.group(2))
        return f"{x * s + tx:.1f} {y * s + ty:.1f}"

    return re.sub(r"([-\d.]+)[ ,]([-\d.]+)", repl, d)


def main() -> None:
    paths, labels = extract_pilot()
    s, tx, ty = affine(paths)
    print(f"transformación: escala {s:.4f}, traslación ({tx:.1f}, {ty:.1f})")

    visible = ["  <g id=\"continent-south-america\">"]
    hitboxes = ["  <g id=\"layer-hitboxes-south-america\">"]
    label_lines: dict[str, str] = {}
    for tid, d in paths.items():
        td = transform_d(d, s, tx, ty)
        visible.append(f'    <path id="{tid}" class="territory" d="{td}" />')
        # hitbox: misma geometría, capa independiente no visible (interacción)
        hitboxes.append(
            f'    <path class="territory-hitbox" data-territory="{tid}" d="{td}" />'
        )
        lx, ly = labels[tid]
        label_lines[SA_LABELS[tid]] = (
            f'    <text x="{lx * s + tx:.0f}" y="{ly * s + ty:.0f}"'
            f' class="territory-label" font-size="26">{SA_LABELS[tid]}</text>'
        )
    visible.append("  </g>")
    hitboxes.append("  </g>")

    svg = TARGET.read_text(encoding="utf-8")
    svg = re.sub(
        r'  <g id="continent-south-america">.*?</g>',
        "\n".join(visible),
        svg,
        count=1,
        flags=re.S,
    )
    # capa de hitboxes: después de los territorios, antes de las etiquetas
    svg = re.sub(r'\n?  <g id="layer-hitboxes-south-america">.*?</g>', "", svg, flags=re.S)
    svg = svg.replace('  <g id="territory-labels">', "\n".join(hitboxes) + '\n  <g id="territory-labels">')
    # reposicionar las 8 etiquetas de Sudamérica (tercio superior del polígono)
    for name, line in label_lines.items():
        svg = re.sub(
            rf'    <text x="[\d.]+" y="[\d.]+" class="territory-label"[^>]*>{name}</text>',
            line,
            svg,
            count=1,
        )
    # estilo del hitbox (una sola vez)
    if ".territory-hitbox" not in svg:
        svg = svg.replace(
            "      .territory-label {",
            "      .territory-hitbox { fill: transparent; stroke: transparent; pointer-events: all; cursor: pointer; }\n      .territory-label {",
        )
    TARGET.write_text(svg, encoding="utf-8")
    print(f"✅ integrado en {TARGET.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
