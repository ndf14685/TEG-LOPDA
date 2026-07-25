#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Afinado de las semillas geográficas del mapa canónico.

Objetivo: que la partición de Voronoi reproduzca las adyacencias TERRESTRES que
declara el backend, sin que ninguna semilla se aleje de su posición geográfica
real más de un margen fijo (así los territorios siguen siendo honestos).

No escribe SVG: imprime el bloque SEEDS afinado para pegar en el generador.
"""
import importlib.util
import math
import os

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, path))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

g3 = _load("design/tools/gen-map-geo-base-v3.py", "genv3")
v2 = _load("design/tools/gen-map-canonical-v2.py", "genv2")

STEP = 5.0          # px por celda de la grilla
MAX_DRIFT = 7.0     # grados: cuánto puede alejarse una semilla de su lugar real

MASSES = sorted({m for _, _, m in v2.SEEDS.values() if isinstance(m, str)}
                - v2.PLAYABLE_ISLANDS)

def rasterize(poly, step=STEP):
    """Barrido por filas -> celdas de tierra sobre una retícula entera global."""
    ys = [p[1] for p in poly]
    n = len(poly)
    cells = []
    for iy in range(math.ceil(min(ys) / step), math.floor(max(ys) / step) + 1):
        y = iy * step
        xin = []
        for i in range(n):
            ax, ay = poly[i]; bx, by = poly[(i + 1) % n]
            if (ay > y) != (by > y):
                xin.append(ax + (y - ay) * (bx - ax) / (by - ay))
        xin.sort()
        for k in range(0, len(xin) - 1, 2):
            for ix in range(math.ceil(xin[k] / step), math.floor(xin[k + 1] / step) + 1):
                cells.append((ix, iy))
    idx = {c: k for k, c in enumerate(cells)}
    xy = np.array([[ix * step, iy * step] for ix, iy in cells], dtype=float)
    # pares de celdas vecinas (derecha y abajo), ambas de tierra
    nb = [(k, idx[(ix + dx, iy + dy)])
          for k, (ix, iy) in enumerate(cells)
          for dx, dy in ((1, 0), (0, 1))
          if (ix + dx, iy + dy) in idx]
    return xy, np.array(nb, dtype=int)

# grilla por masa continental (se calcula una sola vez)
GRID = {}
for mass in MASSES:
    coast = dict(g3.LANDMASSES)[mass]
    GRID[mass] = rasterize(v2.densify(coast))

MASS_TERR = {}
for tid, (lon, lat, mass) in v2.SEEDS.items():
    if lon is not None:
        MASS_TERR.setdefault(mass, []).append(tid)

def adjacency(seed_pos):
    """Adyacencia geométrica: celdas de tierra vecinas con dueños distintos."""
    adj = set()
    for mass, tids in MASS_TERR.items():
        xy, nb = GRID[mass]
        S = np.array([seed_pos[t] for t in tids])
        own = (((xy[:, None, 0] - S[None, :, 0]) ** 2 +
                (xy[:, None, 1] - S[None, :, 1]) ** 2)).argmin(axis=1)
        oa, ob = own[nb[:, 0]], own[nb[:, 1]]
        for i, j in set(map(tuple, np.unique(np.stack([np.minimum(oa, ob),
                                                       np.maximum(oa, ob)], 1)[oa != ob], axis=0))):
            a, b = tids[i], tids[j]
            adj.add((a, b) if a < b else (b, a))
    return adj

def land_pairs():
    mass_of = {t: v[2] for t, v in v2.SEEDS.items()}
    out = set()
    for a in v2.ADJ:
        for b in v2.ADJ[a]:
            if a < b and mass_of.get(a) == mass_of.get(b) and isinstance(mass_of.get(a), str) \
                    and mass_of[a] not in v2.PLAYABLE_ISLANDS:
                out.add((a, b))
    return out

TARGET = land_pairs()

def score(seed_pos):
    got = adjacency(seed_pos)
    hit = len(TARGET & got)
    extra = len(got - TARGET)
    return hit * 10 - extra, hit, extra

def main():
    true_ll = {t: (v[0], v[1]) for t, v in v2.SEEDS.items() if v[0] is not None}
    cur_ll = dict(true_ll)
    pos = {t: g3.project(*ll) for t, ll in cur_ll.items()}
    best, hit, extra = score(pos)
    print(f"inicio: {hit}/{len(TARGET)} adyacencias, {extra} contactos extra")

    steps = [3.0, 1.5, 0.75]
    for st in steps:
        improved = True
        while improved:
            improved = False
            for tid in sorted(cur_ll):
                for dlon, dlat in ((st, 0), (-st, 0), (0, st), (0, -st),
                                   (st, st), (-st, -st), (st, -st), (-st, st)):
                    lon, lat = cur_ll[tid][0] + dlon, cur_ll[tid][1] + dlat
                    if math.hypot(lon - true_ll[tid][0], lat - true_ll[tid][1]) > MAX_DRIFT:
                        continue
                    trial = dict(pos)
                    trial[tid] = g3.project(lon, lat)
                    sc, h, e = score(trial)
                    if sc > best:
                        best, hit, extra = sc, h, e
                        cur_ll[tid] = (lon, lat)
                        pos = trial
                        improved = True
                        print(f"  {tid:42s} -> ({lon:6.1f},{lat:5.1f})  {hit}/{len(TARGET)} +{extra}")
                        break
    print(f"\nfinal: {hit}/{len(TARGET)} adyacencias declaradas, {extra} contactos extra\n")
    for tid in sorted(cur_ll):
        lon, lat = cur_ll[tid]
        mass = v2.SEEDS[tid][2]
        print(f'    "{tid}": ({lon:.1f}, {lat:.1f}, "{mass}"),')

if __name__ == "__main__":
    main()
