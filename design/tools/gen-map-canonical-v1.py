#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEG-LOPDA — map-world-canonical-50-001.svg

Mapa canónico Modo 50 = base cartográfica V3 (costas reales lon/lat -> Mercator)
+ masas geográficas NO jugables (Antártida, casquete ártico, islas secundarias)
+ las capas jugables del export táctico copiadas VERBATIM.

Contrato:
  - Todo lo geográfico vive en <g id="layer-1-geo-base" pointer-events="none">.
  - layer-2/3/4 se copian tal cual de map-base-tactical-50-001.svg: no se toca
    ningún id de territorio, ninguna hitbox, ninguna adyacencia.
  - viewBox 0 0 2560 1720: mismo origen y misma escala que el canónico 2560x1440,
    extendido hacia abajo porque la geometría jugable llega a y=1620 (es el mismo
    saneo que MapPanel.tsx ya calcula en runtime) y para alojar la franja antártica.
"""
import importlib.util
import math
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
V3 = os.path.join(ROOT, "design/tools/gen-map-geo-base-v3.py")
TACTICAL = os.path.join(ROOT, "assets/maps/base/map-base-tactical-50-001.svg")
OUT = os.path.join(ROOT, "assets/maps/base/map-world-canonical-50-001.svg")

spec = importlib.util.spec_from_file_location("genv3", V3)
g3 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g3)

W = 2560.0
H_MERC = 1440.0        # la banda Mercator conserva la métrica de la V3
H = 1720.0             # lienzo canónico extendido (contenido jugable llega a 1620)
POLAR_TOP = -58.0      # límite sur de la proyección Mercator
ICE_BAND_Y0 = 1500.0   # arranque de la franja antártica

def project(lon, lat):
    """Mercator de la V3 para el mundo habitado; rampa lineal bajo -58° para la
    Antártida (Mercator diverge en el polo: se comprime en la franja inferior)."""
    if lat >= POLAR_TOP:
        return g3.project(lon, lat)
    x = (lon + 180.0) / 360.0 * W
    t = (POLAR_TOP - lat) / (POLAR_TOP + 90.0)
    return (x, ICE_BAND_Y0 + t * (H - ICE_BAND_Y0))

def path_of(points, closed=True):
    """Catmull-Rom sobre puntos ya proyectados."""
    P = [project(lo, la) for lo, la in points]
    n = len(P)
    if n < 3:
        return ""
    d = [f"M {P[0][0]:.1f} {P[0][1]:.1f}"]
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        p0 = P[(i - 1) % n] if closed else P[max(i - 1, 0)]
        p1, p2 = P[i], P[(i + 1) % n] if closed else P[min(i + 1, n - 1)]
        p3 = P[(i + 2) % n] if closed else P[min(i + 2, n - 1)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6.0, p1[1] + (p2[1] - p0[1]) / 6.0)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6.0, p2[1] - (p3[1] - p1[1]) / 6.0)
        d.append(f"C {c1[0]:.1f} {c1[1]:.1f}, {c2[0]:.1f} {c2[1]:.1f}, {p2[0]:.1f} {p2[1]:.1f}")
    if closed:
        d.append("Z")
    return " ".join(d)

# ---------------------------------------------------------------------------
# ANTÁRTIDA — costa de oeste a este; se cierra contra el borde inferior del lienzo
# ---------------------------------------------------------------------------
ANTARCTICA = [
    (-180,-78.2),(-172,-78.5),(-165,-78.0),(-158,-77.0),(-150,-75.5),(-143,-74.8),
    (-136,-74.2),(-128,-74.5),(-120,-74.0),(-112,-73.4),(-104,-73.6),(-98,-72.4),
    (-92,-73.0),(-86,-72.6),(-80,-72.0),(-76,-70.6),(-72,-69.0),(-68,-67.4),
    (-64,-65.4),(-61,-63.6),(-58,-62.2),(-57,-63.6),(-59,-65.6),(-61,-67.6),
    (-60,-69.8),(-57,-71.6),(-52,-73.2),(-46,-74.8),(-40,-76.0),(-34,-77.2),
    (-28,-77.6),(-22,-76.4),(-16,-74.8),(-10,-73.4),(-4,-71.6),(2,-70.4),
    (8,-70.0),(14,-70.2),(20,-70.6),(26,-70.2),(32,-69.4),(38,-68.8),(44,-68.0),
    (50,-67.2),(56,-67.0),(62,-67.4),(68,-68.0),(72,-69.4),(76,-69.6),(80,-67.6),
    (86,-67.0),(92,-66.6),(98,-66.4),(104,-66.2),(110,-66.4),(116,-66.8),
    (122,-66.6),(128,-66.4),(134,-65.8),(140,-66.4),(146,-67.2),(152,-68.6),
    (158,-70.0),(163,-72.0),(166,-74.4),(169,-76.4),(172,-78.2),(176,-78.6),
    (180,-78.4),
]

# ---------------------------------------------------------------------------
# CASQUETE ÁRTICO — borde irregular de banquisa sobre el océano Glacial
# ---------------------------------------------------------------------------
ARCTIC_ICE = [
    (-180,74.5),(-170,73.6),(-160,73.0),(-150,73.8),(-140,74.6),(-130,75.4),
    (-120,75.0),(-110,76.0),(-100,77.2),(-90,78.0),(-80,78.6),(-70,79.0),
    (-60,79.4),(-50,79.8),(-40,79.6),(-30,79.0),(-20,78.2),(-10,77.4),
    (0,77.0),(10,77.6),(20,78.2),(30,78.8),(40,79.2),(50,79.0),(60,78.4),
    (70,77.6),(80,77.0),(90,76.6),(100,76.2),(110,75.6),(120,75.2),(130,75.6),
    (140,76.0),(150,75.4),(160,74.6),(170,74.0),(180,74.4),
]

# ---------------------------------------------------------------------------
# ISLAS Y MASAS SECUNDARIAS NO JUGABLES (continuidad geográfica)
# ---------------------------------------------------------------------------
def iso(lon, lat, rx, ry, wobble=(1.0, 0.86, 1.12, 0.9, 1.06, 0.84, 1.1, 0.92)):
    """Islote determinista: elipse de 8 vértices con radios perturbados."""
    pts = []
    for i, k in enumerate(wobble):
        a = 2 * math.pi * i / len(wobble)
        pts.append((lon + math.cos(a) * rx * k, lat + math.sin(a) * ry * k))
    return pts

ISLANDS = {
    # Ártico / subártico
    "svalbard": [(10.5,76.6),(16.0,76.5),(21.0,78.2),(19.5,79.6),(15.5,79.9),
                 (11.0,79.0),(9.5,77.9)],
    "severnaya-zemlya": [(91.0,78.2),(96.5,79.4),(99.0,79.3),(97.5,78.0),
                         (93.5,77.6)],
    "new-siberian": [(137.5,75.4),(144.0,76.1),(148.5,75.2),(145.0,74.4),
                     (139.0,74.6)],
    "faroe": iso(-7.0,62.0,0.9,0.6),
    # Atlántico
    "azores": iso(-27.5,38.6,1.4,0.5),
    "canarias": iso(-16.0,28.3,1.7,0.6),
    "cabo-verde": iso(-24.0,16.0,1.2,0.7),
    "malvinas": iso(-59.0,-51.6,1.6,0.8),
    "georgia-del-sur": iso(-36.8,-54.4,1.3,0.4),
    # Caribe
    "jamaica": iso(-77.3,18.1,1.1,0.4),
    "puerto-rico": iso(-66.5,18.2,1.0,0.4),
    "antillas-menores-n": iso(-61.6,16.6,0.4,1.9),
    "antillas-menores-s": iso(-61.3,12.4,0.4,1.4),
    "trinidad": iso(-61.2,10.4,0.6,0.4),
    # Pacífico
    "aleutianas-1": iso(-170.0,52.6,2.2,0.4),
    "aleutianas-2": iso(-163.0,54.2,2.0,0.4),
    "hawaii": iso(-155.5,19.6,1.2,0.7),
    "galapagos": iso(-90.5,-0.5,1.1,0.7),
    "chiloe": iso(-73.8,-42.7,0.6,0.9),
    # Mediterráneo
    "sicilia": iso(14.2,37.6,1.2,0.7),
    "cerdena": iso(9.1,40.1,0.8,1.3),
    "corcega": iso(9.1,42.2,0.5,0.8),
    "creta": iso(24.9,35.3,1.4,0.4),
    "chipre": iso(33.2,35.1,1.0,0.4),
    "baleares": iso(2.9,39.6,0.8,0.4),
    # Índico / sudeste asiático
    "hainan": iso(109.8,19.2,1.0,0.8),
    "shikoku": iso(133.5,33.7,0.9,0.5),
    "timor": iso(125.4,-9.0,1.9,0.6),
    "flores-sumbawa": iso(119.5,-8.6,2.3,0.4),
    "halmahera": iso(128.0,0.8,0.9,1.2),
    "seram": iso(129.5,-3.1,1.4,0.5),
    "kerguelen": iso(69.3,-49.3,0.9,0.6),
    # Oceanía insular
    "nueva-caledonia": iso(165.5,-21.4,1.6,0.8),
    "salomon": iso(159.5,-9.0,2.0,0.7),
    "vanuatu": iso(168.0,-16.3,0.7,1.6),
    "fiji": iso(178.0,-17.8,1.0,0.7),
}

def build_geo_layer():
    out = []
    add = out.append

    add('    <rect class="geo-ocean" width="2560" height="1720" />')

    # retícula
    grat = []
    for lon in range(-180, 181, 20):
        x, _ = project(lon, 0)
        grat.append(f'<line x1="{x:.0f}" y1="0" x2="{x:.0f}" y2="{H:.0f}" />')
    for lat in [75, 60, 45, 30, 15, 0, -15, -30, -45]:
        _, y = project(0, lat)
        cls = ' class="geo-equator"' if lat == 0 else ""
        grat.append(f'<line x1="0" y1="{y:.1f}" x2="{W:.0f}" y2="{y:.1f}"{cls} />')
    add('    <g class="geo-graticule">\n      ' + "\n      ".join(grat) + "\n    </g>")

    # casquete ártico: banda superior cerrada contra el borde y=0
    arc = path_of(ARCTIC_ICE, closed=False)
    arc_closed = f'{arc} L {W:.0f} 0 L 0 0 Z'
    add('    <g id="geo-arctic-cap">')
    add(f'      <path class="geo-ice" d="{arc_closed}" />')
    add(f'      <path class="geo-ice-edge" d="{arc}" />')
    add('    </g>')

    # plataforma continental (halo) + tierras
    shelf, land = [], []
    for name, pts in g3.LANDMASSES:
        if not pts:
            continue
        d = g3.catmull_path(pts)
        shelf.append(f'      <path class="geo-shelf" d="{d}" />')
        land.append(f'      <path class="geo-land" id="geo-{name}" d="{d}" />')
    for name, pts in ISLANDS.items():
        d = path_of(list(pts))
        shelf.append(f'      <path class="geo-shelf-minor" d="{d}" />')
        land.append(f'      <path class="geo-land geo-minor" id="geo-{name}" d="{d}" />')

    add('    <g id="geo-continental-shelf" filter="url(#geoShelfBlur003)">')
    out.extend(shelf)
    add('    </g>')
    add('    <g id="geo-landmasses">')
    out.extend(land)
    add('    </g>')

    lakes = []
    for name, pts in g3.LAKES:
        lakes.append(f'      <path class="geo-lake" id="geo-{name}" d="{g3.catmull_path(pts)}" />')
    add('    <g id="geo-inland-waters">')
    out.extend(lakes)
    add('    </g>')

    # Antártida: costa suavizada cerrada contra el borde inferior del lienzo
    ant = path_of(ANTARCTICA, closed=False)
    ant_closed = f'{ant} L {W:.0f} {H:.0f} L 0 {H:.0f} Z'
    add('    <g id="geo-antarctica">')
    add(f'      <path class="geo-ice" d="{ant_closed}" />')
    add(f'      <path class="geo-ice-hatch" d="{ant_closed}" />')
    add(f'      <path class="geo-ice-edge" d="{ant}" />')
    add('    </g>')

    return "\n".join(out)

GEO_DEFS = '''    <radialGradient id="geoOcean003" cx="50%" cy="42%" r="85%">
      <stop offset="0%" stop-color="#12263a" />
      <stop offset="60%" stop-color="#0b1a2c" />
      <stop offset="100%" stop-color="#050d18" />
    </radialGradient>
    <linearGradient id="geoLand003" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#33465a" />
      <stop offset="100%" stop-color="#273746" />
    </linearGradient>
    <pattern id="geoIceHatch" width="16" height="16" patternUnits="userSpaceOnUse" patternTransform="rotate(35)">
      <line x1="0" y1="0" x2="0" y2="16" stroke="rgba(190,220,245,0.05)" stroke-width="2" />
    </pattern>
    <filter id="geoShelfBlur003" x="-5%" y="-5%" width="110%" height="110%">
      <feGaussianBlur stdDeviation="7" />
    </filter>'''

GEO_CSS = '''      /* --- capa 1: mundo geográfico, decorativo, nunca interactivo --- */
      .geo-ocean { fill: url(#geoOcean003); }
      .geo-graticule line { stroke: rgba(130,170,205,0.055); stroke-width: 1; }
      .geo-graticule .geo-equator { stroke: rgba(150,185,215,0.10); stroke-dasharray: 10 8; }
      .geo-shelf { fill: none; stroke: rgba(96,156,205,0.16); stroke-width: 16; stroke-linejoin: round; }
      .geo-shelf-minor { fill: none; stroke: rgba(96,156,205,0.13); stroke-width: 9; stroke-linejoin: round; }
      .geo-land { fill: url(#geoLand003); stroke: #7ea6c8; stroke-width: 2.2; stroke-opacity: 0.75; stroke-linejoin: round; }
      .geo-minor { stroke-width: 1.6; stroke-opacity: 0.6; }
      .geo-lake { fill: #0c1c2e; stroke: rgba(126,166,200,0.45); stroke-width: 1.4; }
      /* masas polares no jugables: más apagadas que la tierra jugable para que
         nunca se lean como territorio seleccionable */
      .geo-ice { fill: #1b2c3d; fill-opacity: 0.72; stroke: none; }
      .geo-ice-hatch { fill: url(#geoIceHatch); stroke: none; }
      .geo-ice-edge { fill: none; stroke: rgba(168,200,226,0.34); stroke-width: 1.8; stroke-dasharray: 14 9; stroke-linejoin: round; }'''

# Ajuste de contraste de la capa jugable: el export táctico rellena los
# territorios al 75% opaco y tapa la geografía. Se los baja al rango 0.30-0.35
# con la propiedad leída por borde — es exactamente el tratamiento que MapPanel
# ya aplica en runtime (fillOpacity 0.34/0.35). No cambia geometría ni ids.
OVERLAY_CSS = '''
      /* --- la base geográfica debe seguir legible bajo los territorios --- */
      .territory { fill: rgba(22, 36, 56, 0.30); stroke: rgba(150, 180, 210, 0.55); stroke-width: 2.5; }
      .p-red { fill: rgba(239, 68, 68, 0.32); }
      .p-blue { fill: rgba(59, 130, 246, 0.32); }
      .p-green { fill: rgba(16, 185, 129, 0.32); }
      .p-yellow { fill: rgba(234, 179, 8, 0.32); }
      .p-purple { fill: rgba(168, 85, 247, 0.32); }
      .p-cyan { fill: rgba(6, 182, 212, 0.32); }'''

def main():
    tac = open(TACTICAL).read()
    tac_css = re.search(r'<style>(.*?)</style>', tac, re.S).group(1).rstrip() + OVERLAY_CSS

    def cut(start_marker, end_marker):
        i = tac.index(start_marker)
        j = tac.index(end_marker) if end_marker else len(tac)
        seg = tac[i:j]
        return seg[: seg.rindex("</g>") + 4]

    layer2 = cut('<g id="layer-2-playable-territories"', '<g id="layer-3-hitboxes"')
    layer3 = cut('<g id="layer-3-hitboxes"', '<g id="layer-4-overlays"')
    layer4 = cut('<g id="layer-4-overlays"', None)

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 2560 1720" id="map-world-canonical-50-001">
  <defs>
{GEO_DEFS}
    <style>
{GEO_CSS}
{tac_css}
    </style>
  </defs>

  <!-- CAPA 1: MUNDO GEOGRÁFICO NO JUGABLE (costas reales, Antártida, casquete
       ártico, islas secundarias). Decorativa: sin ids de territorio, sin
       hitboxes, sin labels de juego, sin tropas, no altera adyacencias. -->
  <g id="layer-1-geo-base" pointer-events="none">
{build_geo_layer()}
  </g>

  <!-- CAPAS 2/3/4: copia literal de map-base-tactical-50-001.svg.
       No se modifica ningún id, hitbox ni adyacencia. -->
  {layer2}

  {layer3}

  {layer4}
</svg>
'''
    open(OUT, "w").write(svg)
    print("OK", OUT, len(svg), "bytes")

if __name__ == "__main__":
    main()
