#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEG-LOPDA — map-world-canonical-50-003.svg

Reproyección de los 50 territorios jugables del Modo 50 sobre la base
cartográfica canónica. Método:

  1. Cada masa continental de la base V3 se densifica (se muestrea su curva
     Catmull-Rom) hasta obtener el polígono real de la costa.
  2. Cada territorio recibe una semilla en su posición geográfica real (lon/lat).
  3. La masa se particiona en celdas de Voronoi: cada celda se obtiene
     recortando el polígono de la costa con los semiplanos de los bisectores
     entre semillas (Sutherland-Hodgman).
  4. Las islas que son un territorio completo (Groenlandia, Islandia, Gran
     Bretaña, Japón, Madagascar, Sumatra, Borneo, Java, Australia) toman
     directamente el polígono de la isla.

Resultado: fronteras internas derivadas de la geografía y costas exteriores que
son literalmente la línea de costa de la base. Ningún territorio flota en el mar.

Contrato preservado: los 50 ids, los 50 nombres visibles, `data-territory` en las
50 hitboxes, sin territorios nuevos, sin tocar backend ni adyacencias, y un único
viewBox 0 0 2560 1720 para base, territorios, hitboxes y overlays (sin ningún
transform de escala/traslación).
"""
import importlib.util
import math
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "assets/maps/base/map-world-canonical-50-003.svg")

def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

g3 = _load("design/tools/gen-map-geo-base-v3.py", "genv3")
gc = _load("design/tools/gen-map-canonical-v1.py", "genc1")

W, H = 2560.0, 1720.0

# ---------------------------------------------------------------------------
# Nombres visibles y adyacencias: se leen del backend, no se reescriben.
# ---------------------------------------------------------------------------
def read_backend():
    src = open(os.path.join(ROOT, "backend/src/teg_backend/domain/maps_data.py")).read()
    raw = src.split("_RAW_50: dict")[1].split("def _build_50")[0]
    names, adj = {}, {}
    cont = None
    for line in raw.splitlines():
        mc = re.match(r'\s*"([a-z-]+)": \[', line)
        if mc:
            cont = mc.group(1)
            continue
        mt = re.match(r'\s*\("([a-z-]+)", "([^"]+)", \[(.*)\]\),', line)
        if mt and cont:
            slug, name, nb = mt.groups()
            tid = f"territory-{cont}-{slug}"
            names[tid] = name
            adj[tid] = {f"territory-{c}-{s}"
                        for c, s in re.findall(r'\("([a-z-]+)", "([a-z-]+)"\)', nb)}
    return names, adj

NAMES, ADJ = read_backend()

# ---------------------------------------------------------------------------
# Semillas geográficas (lon, lat) y masa de tierra donde vive cada territorio.
# Ajustadas para que la partición reproduzca las adyacencias declaradas.
# ---------------------------------------------------------------------------
SEEDS = {
    # --- América del Norte (masa continental) ---
    "territory-north-america-alaska":      (-152.0, 65.0, "north-america"),
    "territory-north-america-yukon":       (-133.0, 63.0, "north-america"),
    "territory-north-america-canada":      (-97.0, 60.0, "north-america"),
    "territory-north-america-newfoundland": (-64.0, 51.0, "north-america"),
    "territory-north-america-oregon":      (-115.0, 45.0, "north-america"),
    "territory-north-america-new-york":     (-80.0, 41.0, "north-america"),
    "territory-north-america-california":  (-112.0, 33.0, "north-america"),
    "territory-north-america-mexico":       (-97.0, 20.0, "north-america"),
    # --- América del Sur ---
    "territory-south-america-colombia":     (-72.0, 3.0, "south-america"),
    "territory-south-america-venezuela":    (-65.0, 7.0, "south-america"),
    "territory-south-america-peru":         (-76.0, -10.0, "south-america"),
    "territory-south-america-brazil":       (-50.0, -10.0, "south-america"),
    "territory-south-america-bolivia":      (-58.0, -28.0, "south-america"),
    "territory-south-america-chile":        (-71.5, -33.0, "south-america"),
    "territory-south-america-argentina":    (-64.0, -34.0, "south-america"),
    "territory-south-america-uruguay":      (-55.5, -31.0, "south-america"),
    # --- Europa (sobre la masa euroasiática) ---
    "territory-europe-spain":                (-4.0, 40.0, "eurasia"),
    "territory-europe-france":                (2.0, 46.5, "eurasia"),
    "territory-europe-italy":                (13.0, 42.5, "eurasia"),
    "territory-europe-germany":              (15.0, 48.0, "eurasia"),
    "territory-europe-sweden":               (9.0, 60.0, "eurasia"),
    "territory-europe-poland":               (21.0, 51.0, "eurasia"),
    "territory-europe-russia":               (42.0, 57.0, "eurasia"),
    # --- Asia (sobre la masa euroasiática) ---
    "territory-asia-turkey":                 (34.0, 39.0, "eurasia"),
    "territory-asia-arabia":                 (45.0, 23.0, "eurasia"),
    "territory-asia-iran":                   (58.0, 38.0, "eurasia"),
    "territory-asia-aral":                   (63.0, 46.0, "eurasia"),
    "territory-asia-india":                  (71.0, 22.0, "eurasia"),
    "territory-asia-china":                 (108.0, 30.0, "eurasia"),
    "territory-asia-gobi":                   (101.0, 43.0, "eurasia"),
    "territory-asia-mongolia":              (104.0, 47.0, "eurasia"),
    "territory-asia-siberia":                (90.0, 63.0, "eurasia"),
    "territory-asia-kamchatka":             (150.0, 62.0, "eurasia"),
    "territory-asia-malaysia":              (102.0, 8.0, "eurasia"),
    # --- África ---
    "territory-africa-sahara":                (2.0, 24.0, "africa"),
    "territory-africa-egypt":                (29.0, 25.0, "africa"),
    "territory-africa-nigeria":               (9.0, 14.0, "africa"),
    "territory-africa-ethiopia":             (40.0, 10.0, "africa"),
    "territory-africa-kenya":                (37.0, -3.0, "africa"),
    "territory-africa-zaire":                (21.0, -6.0, "africa"),
    "territory-africa-south-africa":         (25.0, -28.0, "africa"),
    # --- Territorios que son una isla completa ---
    "territory-north-america-greenland":     (None, None, "greenland"),
    "territory-europe-iceland":              (None, None, "iceland"),
    "territory-europe-great-britain":        (None, None, "britain"),
    "territory-asia-japan":                  (None, None, ("honshu", "hokkaido", "kyushu", "shikoku")),
    "territory-africa-madagascar":           (None, None, "madagascar"),
    "territory-oceania-sumatra":             (None, None, "sumatra"),
    "territory-oceania-borneo":              (None, None, "borneo"),
    "territory-oceania-java":                (None, None, "java"),
    "territory-oceania-australia":           (None, None, "australia"),
}

# Islas que además de la celda continental forman parte de un territorio
# (Terranova es una isla frente a la costa de Labrador, no decorado).
EXTRA_ISLANDS = {
    "territory-north-america-newfoundland": ["newfoundland"],
    "territory-europe-italy": ["sicilia", "cerdena"],
    "territory-europe-spain": ["baleares"],
    "territory-europe-great-britain": ["ireland"],
}

# Islas que dejan de ser decorado porque pasan a ser territorio jugable.
PLAYABLE_ISLANDS = {"greenland", "iceland", "britain", "honshu", "hokkaido",
                    "kyushu", "shikoku", "madagascar", "sumatra", "borneo",
                    "java", "australia", "newfoundland", "ireland"}

# ---------------------------------------------------------------------------
# Geometría
# ---------------------------------------------------------------------------
def densify(points_ll, samples=10):
    """Muestrea la curva Catmull-Rom de una costa -> polígono denso proyectado."""
    P = [g3.project(lo, la) for lo, la in points_ll]
    n = len(P)
    out = []
    for i in range(n):
        p0, p1, p2, p3 = P[(i - 1) % n], P[i], P[(i + 1) % n], P[(i + 2) % n]
        for s in range(samples):
            t = s / samples
            t2, t3 = t * t, t * t * t
            out.append((
                0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t
                       + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
                       + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3),
                0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t
                       + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
                       + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)))
    return out

def clip_halfplane(poly, a, b):
    """Sutherland-Hodgman: conserva la parte del polígono más cercana a `a` que a `b`."""
    mx, my = (a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0
    nx, ny = a[0] - b[0], a[1] - b[1]
    side = lambda p: (p[0] - mx) * nx + (p[1] - my) * ny
    out = []
    for i in range(len(poly)):
        cur, nxt = poly[i], poly[(i + 1) % len(poly)]
        sc, sn = side(cur), side(nxt)
        if sc >= 0:
            out.append(cur)
        if (sc >= 0) != (sn >= 0):
            t = sc / (sc - sn)
            out.append((cur[0] + t * (nxt[0] - cur[0]), cur[1] + t * (nxt[1] - cur[1])))
    return out

def area(poly):
    s = 0.0
    for i in range(len(poly)):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % len(poly)]
        s += x1 * y2 - x2 * y1
    return abs(s) / 2.0

def centroid(poly):
    cx = cy = a = 0.0
    for i in range(len(poly)):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % len(poly)]
        cr = x1 * y2 - x2 * y1
        a += cr
        cx += (x1 + x2) * cr
        cy += (y1 + y2) * cr
    if abs(a) < 1e-9:
        n = len(poly) or 1
        return sum(p[0] for p in poly) / n, sum(p[1] for p in poly) / n
    a *= 0.5
    return cx / (6 * a), cy / (6 * a)

def simplify(poly, tol=2.0):
    """Elimina vértices casi colineales o muy juntos (achica el SVG)."""
    out = [poly[0]]
    for p in poly[1:]:
        if math.hypot(p[0] - out[-1][0], p[1] - out[-1][1]) >= tol:
            out.append(p)
    if len(out) > 2 and math.hypot(out[0][0] - out[-1][0], out[0][1] - out[-1][1]) < tol:
        out.pop()
    return out

def label_anchor(poly, step=12.0):
    """Polo de inaccesibilidad: el punto interior más lejano del borde. Evita que
    la etiqueta caiga fuera del territorio en formas cóncavas o alargadas."""
    xs = [p[0] for p in poly]; ys = [p[1] for p in poly]
    n = len(poly)

    def inside(x, y):
        c = False
        for i in range(n):
            ax, ay = poly[i]; bx, by = poly[(i + 1) % n]
            if (ay > y) != (by > y) and x < ax + (y - ay) * (bx - ax) / (by - ay):
                c = not c
        return c

    def edge_dist(x, y):
        best = float("inf")
        for i in range(n):
            ax, ay = poly[i]; bx, by = poly[(i + 1) % n]
            dx, dy = bx - ax, by - ay
            L = dx * dx + dy * dy
            t = 0.0 if L == 0 else max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / L))
            best = min(best, math.hypot(x - ax - t * dx, y - ay - t * dy))
        return best

    best, bx_, by_ = -1.0, *centroid(poly)
    cur = step
    while cur >= 3.0:
        x = min(xs)
        while x <= max(xs):
            y = min(ys)
            while y <= max(ys):
                if inside(x, y):
                    d = edge_dist(x, y)
                    if d > best:
                        best, bx_, by_ = d, x, y
                y += cur
            x += cur
        # refina alrededor del mejor punto
        xs = [bx_ - cur, bx_ + cur]; ys = [by_ - cur, by_ + cur]
        cur /= 3.0
    return bx_, by_

def to_path(poly):
    d = [f"M {poly[0][0]:.1f} {poly[0][1]:.1f}"]
    d += [f"L {x:.1f} {y:.1f}" for x, y in poly[1:]]
    d.append("Z")
    return " ".join(d)

# ---------------------------------------------------------------------------
def build_territories():
    coasts = dict(g3.LANDMASSES)
    dense = {name: densify(pts) for name, pts in coasts.items() if pts}

    cells = {}
    by_mass = {}
    for tid, (lon, lat, mass) in SEEDS.items():
        if lon is None:
            continue
        by_mass.setdefault(mass, []).append((tid, g3.project(lon, lat)))

    # partición de Voronoi recortada contra la costa
    for mass, seeds in by_mass.items():
        base = dense[mass]
        for tid, s in seeds:
            poly = base
            for otid, o in seeds:
                if otid == tid:
                    continue
                poly = clip_halfplane(poly, s, o)
                if len(poly) < 3:
                    break
            if len(poly) >= 3 and area(poly) > 50:
                cells[tid] = [simplify(poly)]

    # territorios que son una isla completa
    for tid, (lon, lat, mass) in SEEDS.items():
        if lon is not None:
            continue
        parts = mass if isinstance(mass, tuple) else (mass,)
        cells[tid] = [simplify(dense[p]) for p in parts]

    # islas que se suman a un territorio ya existente
    for tid, extras in EXTRA_ISLANDS.items():
        for name in extras:
            pts = coasts.get(name) or gc.ISLANDS.get(name)
            if pts:
                cells[tid].append(simplify(densify(list(pts))))

    return cells

def touching_pairs(cells, tol=7.0):
    """Territorios que comparten borde. Hash espacial: dos territorios se tocan
    si aportan vértices a la misma celda de una retícula de `tol` px."""
    bucket = {}
    for tid, parts in cells.items():
        for part in parts:
            for x, y in part:
                for dx in (0, 1):
                    for dy in (0, 1):
                        bucket.setdefault((int(x // tol) + dx, int(y // tol) + dy), set()).add(tid)
    pairs = set()
    for tids in bucket.values():
        ts = sorted(tids)
        for i, a in enumerate(ts):
            for b in ts[i + 1:]:
                pairs.add((a, b))
    return pairs

def closest_points(cells, a, b):
    """Par de puntos más cercano entre dos territorios, considerando la vuelta
    por el antimeridiano: Alaska-Kamchatka y Chile-Australia son vecinos a través
    del Pacífico, no cruzando el mapa entero por el otro lado.
    Devuelve (p, q, shift); shift != 0 significa que el enlace envuelve el borde."""
    pa = [p for part in cells[a] for p in part]
    pb = [p for part in cells[b] for p in part]
    best = (float("inf"), None, None, 0.0)
    for shift in (0.0, W, -W):
        for x1, y1 in pa:
            for x2, y2 in pb:
                d = (x1 - (x2 + shift)) ** 2 + (y1 - y2) ** 2
                if d < best[0]:
                    best = (d, (x1, y1), (x2, y2), shift)
    return best[1], best[2], best[3]

def build_links(cells, declared, touching):
    """Enlace táctico para cada adyacencia que el backend permite pero que el
    mapa no muestra como frontera común: puentes marítimos y corredores."""
    links, listing = [], []
    for a, b in sorted(declared):
        if (a, b) in touching:
            continue
        p, q, shift = closest_points(cells, a, b)
        qx = q[0] + shift
        L = math.hypot(qx - p[0], q[1] - p[1]) or 1.0
        ends = (f'      <circle class="adj-link-end" cx="{p[0]:.0f}" cy="{p[1]:.0f}" r="5" />\n'
                f'      <circle class="adj-link-end" cx="{q[0]:.0f}" cy="{q[1]:.0f}" r="5" />')
        if shift:
            # el enlace sale por un borde y entra por el opuesto: dos tramos
            edge = W if shift > 0 else 0.0
            t = (edge - p[0]) / (qx - p[0])
            yc = p[1] + t * (q[1] - p[1])
            d1 = f'M {p[0]:.0f} {p[1]:.0f} L {edge:.0f} {yc:.0f}'
            d2 = f'M {W - edge:.0f} {yc:.0f} L {q[0]:.0f} {q[1]:.0f}'
            links.append(f'    <g class="adj-link">\n'
                         f'      <path class="adj-link-line" d="{d1}" />\n'
                         f'      <path class="adj-link-line" d="{d2}" />\n{ends}\n    </g>')
        else:
            mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
            dx, dy = q[0] - p[0], q[1] - p[1]
            bulge = min(60.0, L * 0.16)   # los tramos largos se curvan menos
            cx, cy = mx - dy / L * bulge, my + dx / L * bulge
            links.append(f'    <g class="adj-link">\n'
                         f'      <path class="adj-link-line" d="M {p[0]:.0f} {p[1]:.0f} '
                         f'Q {cx:.0f} {cy:.0f} {q[0]:.0f} {q[1]:.0f}" />\n{ends}\n    </g>')
        listing.append((a, b, L, bool(shift)))
    return links, listing

def geometric_adjacency(cells, tol=6.0):
    """Dos territorios son vecinos si sus bordes se tocan."""
    keys = list(cells)
    pts = {k: [p for part in v for p in part] for k, v in cells.items()}
    adj = {k: set() for k in keys}
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            hit = False
            for pa in pts[a]:
                for pb in pts[b]:
                    if abs(pa[0] - pb[0]) <= tol and abs(pa[1] - pb[1]) <= tol:
                        hit = True
                        break
                if hit:
                    break
            if hit:
                adj[a].add(b)
                adj[b].add(a)
    return adj

def point_in(poly, x, y):
    c = False
    n = len(poly)
    for i in range(n):
        ax, ay = poly[i]; bx, by = poly[(i + 1) % n]
        if (ay > y) != (by > y) and x < ax + (y - ay) * (bx - ax) / (by - ay):
            c = not c
    return c

def layout_labels(anchors, sizes, names, polys, rounds=260):
    """Coloca los rótulos evitando solapes.

    El badge de tropas queda SIEMPRE en el ancla, dentro del territorio: es
    información de juego y no puede migrar. El rótulo sí puede moverse; primero
    intenta acomodarse dentro del territorio y, si el racimo es muy denso
    (Europa, Insulindia), sale al mar y se conecta con una línea de conducción.
    """
    keys = list(names)
    pos = {t: (anchors[t][0], anchors[t][1] - sizes[t] * 1.25) for t in keys}
    lbox = {t: (len(names[t]) * sizes[t] * 0.58 + 16, sizes[t] * 1.5) for t in keys}
    brad = {t: max(16.0, sizes[t] * 0.92) for t in keys}

    def push(a, b, wa, ha, wb, hb, pa, pb, move_a, move_b):
        ow = (wa + wb) / 2 - abs(pa[0] - pb[0])
        oh = (ha + hb) / 2 - abs(pa[1] - pb[1])
        if ow <= 0 or oh <= 0:
            return None
        if ow < oh:
            s = 1.0 if pa[0] >= pb[0] else -1.0
            d = ow / (2 if (move_a and move_b) else 1) + 0.6
            return ((pa[0] + s * d, pa[1]) if move_a else pa,
                    (pb[0] - s * d, pb[1]) if move_b else pb)
        s = 1.0 if pa[1] >= pb[1] else -1.0
        d = oh / (2 if (move_a and move_b) else 1) + 0.6
        return ((pa[0], pa[1] + s * d) if move_a else pa,
                (pb[0], pb[1] - s * d) if move_b else pb)

    for r in range(rounds):
        # fase 1: el rótulo intenta quedarse dentro del territorio
        # fase 2 (última mitad): puede salir al mar con línea de conducción
        free = r > rounds * 0.4
        limit = 130.0 if free else 46.0
        moved = False
        for i, a in enumerate(keys):
            for b in keys[i + 1:]:
                res = push(a, b, *lbox[a], *lbox[b], pos[a], pos[b], True, True)
                if res:
                    moved = True
                    for t, np_ in zip((a, b), res):
                        ox, oy = anchors[t]
                        if math.hypot(np_[0] - ox, np_[1] - oy + sizes[t] * 1.25) > limit:
                            continue
                        if not free and not point_in(polys[t], np_[0], np_[1]):
                            continue
                        pos[t] = np_
            # el rótulo tampoco puede pisar un badge ajeno
            for b in keys:
                if b == a:
                    continue
                res = push(a, b, *lbox[a], 2 * brad[b] + 6, 2 * brad[b] + 6,
                           pos[a], anchors[b], True, False)
                if res:
                    np_ = res[0]
                    ox, oy = anchors[a]
                    if math.hypot(np_[0] - ox, np_[1] - oy + sizes[a] * 1.25) <= limit and \
                            (free or point_in(polys[a], np_[0], np_[1])):
                        pos[a] = np_
                        moved = True
        if not moved and r > rounds * 0.45:
            break
    return pos, brad

def resolve_label_overlaps(anchors, sizes, names, polys, drift=52.0, rounds=140):
    """Separa etiquetas que se pisan. Cada rótulo puede alejarse de su ancla como
    máximo `drift` px y nunca sale del territorio: si al empujarlo se saldría, se
    queda donde estaba. Corrige los solapes que el PO marcó como defecto."""
    pos = dict(anchors)
    box = {t: (len(names[t]) * sizes[t] * 0.6 + 14, sizes[t] + max(17.0, sizes[t] * 0.95) * 2 + 12)
           for t in names}
    keys = list(names)
    for _ in range(rounds):
        moved = False
        for i, a in enumerate(keys):
            for b in keys[i + 1:]:
                (ax, ay), (bx, by) = pos[a], pos[b]
                ow = (box[a][0] + box[b][0]) / 2 - abs(ax - bx)
                oh = (box[a][1] + box[b][1]) / 2 - abs(ay - by)
                if ow <= 0 or oh <= 0:
                    continue
                moved = True
                if ow < oh:                      # separar por el eje más barato
                    d = ow / 2 + 0.5
                    sx = 1.0 if ax >= bx else -1.0
                    cand = {a: (ax + sx * d, ay), b: (bx - sx * d, by)}
                else:
                    d = oh / 2 + 0.5
                    sy = 1.0 if ay >= by else -1.0
                    cand = {a: (ax, ay + sy * d), b: (bx, by - sy * d)}
                for t, (nx, ny) in cand.items():
                    ox, oy = anchors[t]
                    if math.hypot(nx - ox, ny - oy) > drift:
                        continue
                    if not point_in(polys[t], nx, ny):
                        continue
                    pos[t] = (nx, ny)
        if not moved:
            break
    return pos

def build_geo_layer(_playable_islands=None):
    """Capa 1 completa: TODAS las masas de tierra, incluidas las islas que además
    son territorio. Los continentes ya se pintan así (tierra de la base + tinte
    del territorio encima); si a las islas se les quitara la tierra de la base
    quedarían más apagadas que el resto del mundo."""
    return gc.build_geo_layer()

def main():
    cells = build_territories()
    missing = set(NAMES) - set(cells)
    assert not missing, f"territorios sin geometría: {missing}"

    geo = build_geo_layer(PLAYABLE_ISLANDS)

    terr, hits = [], []
    anchors, sizes = {}, {}
    for tid in NAMES:
        d = " ".join(to_path(p) for p in cells[tid])
        terr.append(f'    <path id="{tid}" class="territory" d="{d}" pointer-events="none" />')
        hits.append(f'    <path class="territory-hitbox" data-territory="{tid}" d="{d}" pointer-events="all" />')
        main = max(cells[tid], key=area)
        anchors[tid] = label_anchor(main)
        # la etiqueta se achica en territorios chicos para no invadir vecinos
        sizes[tid] = max(15.0, min(24.0, math.sqrt(area(main)) / 5.0))

    mains = {t: max(cells[t], key=area) for t in NAMES}
    placed, brads = layout_labels(anchors, sizes, NAMES, mains)

    over = []
    for tid in NAMES:
        lx, ly = placed[tid]
        ax, ay = anchors[tid]
        fs, br = sizes[tid], brads[tid]
        # línea de conducción sólo si el rótulo tuvo que salir del territorio
        if not point_in(mains[tid], lx, ly):
            over.append(f'    <path class="label-leader" d="M {lx:.0f} {ly + fs * 0.7:.0f} '
                        f'L {ax:.0f} {ay - br:.0f}" pointer-events="none" />')
        over.append(
            f'    <text x="{lx:.0f}" y="{ly + fs * 0.36:.0f}" class="territory-label" '
            f'font-size="{fs:.0f}" pointer-events="none">{NAMES[tid]}</text>\n'
            f'    <g class="badge-group" data-badge-id="{tid}" pointer-events="none">\n'
            f'      <circle cx="{ax:.0f}" cy="{ay:.0f}" r="{br:.0f}" class="badge-circle" pointer-events="none" />\n'
            f'      <text x="{ax:.0f}" y="{ay + br * 0.36:.0f}" class="badge-text" '
            f'font-size="{fs * 1.1:.0f}" pointer-events="none">1</text>\n'
            f'    </g>')

    # enlaces tácticos: toda adyacencia declarada que no se ve como frontera
    declared = {(a, b) for a in ADJ for b in ADJ[a] if a < b}
    touching = touching_pairs(cells)
    links, link_list = build_links(cells, declared, touching)

    tac = open(os.path.join(ROOT, "assets/maps/base/map-base-tactical-50-001.svg")).read()
    tac_css = re.search(r'<style>(.*?)</style>', tac, re.S).group(1).rstrip()

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 2560 1720" id="map-world-canonical-50-003">
  <defs>
{gc.GEO_DEFS}
    <style>
{gc.GEO_CSS}
{tac_css}
{gc.OVERLAY_CSS}
      .territory {{ stroke-linejoin: round; }}
      /* enlaces tácticos: comunican que el ataque está permitido aunque no haya
         frontera común. Tono frío y trazo fino: nunca compiten con el territorio. */
      .adj-link-line {{ fill: none; stroke: rgba(125,196,235,0.55); stroke-width: 3;
        stroke-dasharray: 13 9; stroke-linecap: round; }}
      .adj-link-end {{ fill: rgba(125,196,235,0.75); stroke: none; }}
      .label-leader {{ fill: none; stroke: rgba(203,222,240,0.45); stroke-width: 1.6; }}
    </style>
  </defs>

  <!-- CAPA 1: mundo geográfico no jugable (costas reales, Antártida, casquete
       ártico, islas secundarias). Sin ids de territorio, sin hitboxes, sin
       labels de juego, sin tropas. -->
  <g id="layer-1-geo-base" pointer-events="none">
{geo}
  </g>

  <!-- CAPA 2: 50 territorios jugables reproyectados sobre la geografía real.
       Fronteras internas = partición de Voronoi de la masa continental;
       fronteras externas = línea de costa de la capa 1. -->
  <g id="layer-2-playable-territories" pointer-events="none">
{chr(10).join(terr)}
  </g>

  <!-- CAPA 2B: enlaces tácticos. Cada adyacencia que el backend permite y que
       la geografía no muestra como frontera común (puentes marítimos y
       corredores) se dibuja explícitamente. Decorativa: pointer-events none,
       sin ids de territorio, sin hitboxes. No altera ninguna adyacencia. -->
  <g id="layer-2b-adjacency-links" pointer-events="none">
{chr(10).join(links)}
  </g>

  <!-- CAPA 3: hitboxes, una por territorio, misma geometría -->
  <g id="layer-3-hitboxes" pointer-events="all">
{chr(10).join(hits)}
  </g>

  <!-- CAPA 4: overlays -->
  <g id="layer-4-overlays" pointer-events="none">
{chr(10).join(over)}
  </g>
</svg>
'''
    open(OUT, "w").write(svg)
    print("OK", OUT, f"{len(svg)} bytes, {len(cells)} territorios")

    # --- verificación de adyacencias contra el backend ---
    geo_adj = geometric_adjacency(cells)
    mass_of = {t: (v[2] if not isinstance(v[2], tuple) else "islas") for t, v in SEEDS.items()}
    same_mass = lambda a, b: mass_of[a] == mass_of[b] and mass_of[a] != "islas"
    land_pairs = {(a, b) for a in ADJ for b in ADJ[a] if a < b and same_mass(a, b)}
    ok = {(a, b) for a, b in land_pairs if b in geo_adj[a]}
    print(f"\nAdyacencias terrestres declaradas por el backend: {len(land_pairs)}")
    print(f"  reproducidas geométricamente: {len(ok)}/{len(land_pairs)}")
    for a, b in sorted(land_pairs - ok):
        print(f"  FALTA  {a} <-> {b}")
    extra = {(a, b) for a in geo_adj for b in geo_adj[a]
             if a < b and same_mass(a, b) and b not in ADJ[a]}
    print(f"  contactos geométricos no declarados: {len(extra)}")

    # --- cobertura visual de TODAS las adyacencias declaradas ---
    all_declared = {(a, b) for a in ADJ for b in ADJ[a] if a < b}
    shown_border = {(a, b) for a, b in all_declared if (a, b) in touching}
    print(f"\nAdyacencias declaradas en total: {len(all_declared)}")
    print(f"  visibles como frontera comun : {len(shown_border)}")
    print(f"  visibles como enlace tactico : {len(link_list)}")
    print(f"  sin comunicar                : {len(all_declared) - len(shown_border) - len(link_list)}")
    with open(os.path.join(ROOT, "test-results/adjacency-links.txt"), "w") as f:
        for a, b, L, wrap in sorted(link_list, key=lambda r: -r[2]):
            same = (mass_of.get(a) == mass_of.get(b) and mass_of.get(a) != "islas")
            kind = ("paso marítimo por el antimeridiano" if wrap else
                    "corredor terrestre" if same else "paso marítimo")
            f.write(f"{a}\t{b}\t{L:.0f}\t{kind}\n")

if __name__ == "__main__":
    main()
