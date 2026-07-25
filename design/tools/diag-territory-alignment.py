#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diagnóstico de alineación: distancia entre el centroide de cada territorio
jugable del Modo 50 y la posición geográfica real del lugar que nombra,
proyectada con la misma métrica del mapa canónico.

No modifica ningún asset. Produce:
  - tabla de errores por territorio (stdout)
  - test-results/canonical-alignment-diagnostic.png (vectores de corrimiento)
"""
import importlib.util
import math
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
spec = importlib.util.spec_from_file_location(
    "genv3", os.path.join(ROOT, "design/tools/gen-map-geo-base-v3.py"))
g3 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g3)

# Posición geográfica real (lon, lat) del lugar que nombra cada territorio.
TRUE_LL = {
    "north-america-alaska": (-152.0, 64.0),
    "north-america-yukon": (-135.0, 63.5),
    "north-america-canada": (-97.0, 55.0),
    "north-america-greenland": (-42.0, 72.0),
    "north-america-newfoundland": (-56.0, 48.5),
    "north-america-oregon": (-120.5, 44.0),
    "north-america-california": (-119.5, 37.0),
    "north-america-new-york": (-75.5, 42.5),
    "north-america-mexico": (-102.0, 23.5),
    "south-america-colombia": (-74.0, 4.5),
    "south-america-venezuela": (-66.5, 7.5),
    "south-america-peru": (-75.0, -10.0),
    "south-america-brazil": (-51.0, -11.0),
    "south-america-bolivia": (-64.5, -17.0),
    "south-america-chile": (-71.0, -35.0),
    "south-america-argentina": (-64.5, -35.0),
    "south-america-uruguay": (-56.0, -33.0),
    "europe-iceland": (-19.0, 65.0),
    "europe-great-britain": (-2.0, 53.5),
    "europe-sweden": (15.5, 62.5),
    "europe-spain": (-3.7, 40.3),
    "europe-france": (2.3, 46.5),
    "europe-germany": (10.5, 51.0),
    "europe-italy": (12.5, 42.5),
    "europe-poland": (19.5, 52.0),
    "europe-russia": (40.0, 56.0),
    "africa-sahara": (3.0, 23.0),
    "africa-egypt": (30.0, 26.5),
    "africa-nigeria": (8.5, 9.5),
    "africa-ethiopia": (39.5, 8.5),
    "africa-zaire": (23.0, -3.0),
    "africa-kenya": (37.5, 0.5),
    "africa-south-africa": (25.0, -29.0),
    "africa-madagascar": (46.8, -19.0),
    "asia-turkey": (35.0, 39.0),
    "asia-arabia": (45.0, 24.0),
    "asia-iran": (53.5, 32.5),
    "asia-aral": (60.0, 45.0),
    "asia-gobi": (103.0, 43.0),
    "asia-siberia": (95.0, 62.0),
    "asia-kamchatka": (159.0, 56.0),
    "asia-japan": (138.0, 36.5),
    "asia-india": (79.0, 22.0),
    "asia-china": (110.0, 32.0),
    "asia-mongolia": (100.0, 47.0),
    "asia-malaysia": (102.0, 4.5),
    "oceania-sumatra": (101.5, -0.5),
    "oceania-borneo": (114.0, 0.5),
    "oceania-java": (110.0, -7.3),
    "oceania-australia": (134.0, -25.0),
}

def centroid(d):
    n = [float(x) for x in re.findall(r'-?\d+\.?\d*', d)]
    xs, ys = n[0::2], n[1::2]
    return (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2

def main():
    tac = open(os.path.join(ROOT, "assets/maps/base/map-base-tactical-50-001.svg")).read()
    l2 = tac.split('id="layer-2-playable-territories"')[1].split('id="layer-3-hitboxes"')[0]
    blobs = dict((i, centroid(d)) for i, d in
                 re.findall(r'id="territory-([^"]+)"[^>]*?d="([^"]+)"', l2))

    rows = []
    for tid, (lon, lat) in TRUE_LL.items():
        gx, gy = g3.project(lon, lat)
        bx, by = blobs[tid]
        rows.append((math.hypot(bx - gx, by - gy), tid, bx, by, gx, gy))
    rows.sort(reverse=True)

    errs = [r[0] for r in rows]
    print(f"Territorios medidos: {len(rows)}")
    print(f"Error medio    : {sum(errs)/len(errs):7.0f} px")
    print(f"Error mediano  : {sorted(errs)[len(errs)//2]:7.0f} px")
    print(f"Error maximo   : {max(errs):7.0f} px")
    print(f"Dentro de 150px: {sum(1 for e in errs if e <= 150)}/{len(errs)}")
    print("\nPeores 12 corrimientos (px sobre lienzo 2560x1720):")
    for e, tid, bx, by, gx, gy in rows[:12]:
        print(f"  {tid:32s} {e:6.0f}   blob({bx:5.0f},{by:5.0f}) vs real({gx:5.0f},{gy:5.0f})")

    # figura diagnóstica: base + vectores de corrimiento
    geo = open(os.path.join(ROOT, "assets/maps/base/map-world-canonical-50-001.svg")).read()
    base = geo.split('<g id="layer-1-geo-base"')[1].split('<g id="layer-2-playable-territories"')[0]
    base = base[: base.rindex("</g>")]
    defs = geo.split("<defs>")[1].split("</defs>")[0]

    marks = []
    for e, tid, bx, by, gx, gy in rows:
        col = "#ef4444" if e > 250 else ("#f59e0b" if e > 150 else "#22c55e")
        marks.append(
            f'<line x1="{gx:.0f}" y1="{gy:.0f}" x2="{bx:.0f}" y2="{by:.0f}" '
            f'stroke="{col}" stroke-width="3" stroke-opacity="0.85" />'
            f'<circle cx="{gx:.0f}" cy="{gy:.0f}" r="7" fill="{col}" />'
            f'<circle cx="{bx:.0f}" cy="{by:.0f}" r="9" fill="none" stroke="{col}" stroke-width="3" />')

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 2560 1720">
  <defs>{defs}</defs>
  <g pointer-events="none">{base}</g>
  <g>{"".join(marks)}</g>
  <g font-family="system-ui,sans-serif" fill="#e2e8f0">
    <text x="40" y="60" font-size="38" font-weight="800">Diagnostico de alineacion — Modo 50 sobre geografia real</text>
    <text x="40" y="106" font-size="26" fill="#94a3b8">Punto lleno = posicion geografica real del lugar · Circulo = centroide del territorio jugable</text>
    <text x="40" y="146" font-size="26" fill="#94a3b8">verde &lt;150px · ambar 150-250px · rojo &gt;250px</text>
  </g>
</svg>'''
    out = os.path.join(ROOT, "test-results/.alignment.html")
    open(out, "w").write(
        '<!doctype html><html><head><style>html,body{margin:0;background:#050d18;'
        'height:100%;overflow:hidden}svg{display:block;width:100vw;height:100vh}'
        '</style></head><body>' + svg + '</body></html>')
    subprocess.run(["node", "design/tools/shot.mjs", out,
                    "test-results/canonical-alignment-diagnostic.png", "2560", "1720"],
                   cwd=ROOT, check=True)

if __name__ == "__main__":
    main()
