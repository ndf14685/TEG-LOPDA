#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Búsqueda exhaustiva de semillas: barre una malla de posiciones candidatas por
territorio (no un paso local) para recuperar como FRONTERA REAL las adyacencias
que el backend declara y la partición no muestra.

Restricción dura: ninguna semilla puede alejarse más de MAX_DRIFT grados de la
posición geográfica real del territorio.
"""
import importlib.util
import math
import os
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, path))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

g3 = _load("design/tools/gen-map-geo-base-v3.py", "genv3")
v2 = _load("design/tools/gen-map-canonical-v2.py", "genv2")
t1 = _load("design/tools/tune-seeds.py", "tune1") if False else None

STEP = 5.0
MAX_DRIFT = 8.0

def rasterize(poly, step=STEP):
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
    nb = np.array([(k, idx[(ix + dx, iy + dy)])
                   for k, (ix, iy) in enumerate(cells)
                   for dx, dy in ((1, 0), (0, 1))
                   if (ix + dx, iy + dy) in idx], dtype=int)
    return xy, nb

MASS_TERR = {}
for tid, (lon, lat, mass) in v2.SEEDS.items():
    if lon is not None:
        MASS_TERR.setdefault(mass, []).append(tid)

GRID = {m: rasterize(v2.densify(dict(g3.LANDMASSES)[m])) for m in MASS_TERR}

def adjacency(pos):
    adj = set()
    for mass, tids in MASS_TERR.items():
        xy, nb = GRID[mass]
        S = np.array([pos[t] for t in tids])
        own = (((xy[:, None, 0] - S[None, :, 0]) ** 2 +
                (xy[:, None, 1] - S[None, :, 1]) ** 2)).argmin(axis=1)
        oa, ob = own[nb[:, 0]], own[nb[:, 1]]
        d = np.unique(np.stack([np.minimum(oa, ob), np.maximum(oa, ob)], 1)[oa != ob], axis=0)
        for i, j in d:
            a, b = tids[i], tids[j]
            adj.add((a, b) if a < b else (b, a))
    return adj

mass_of = {t: v[2] for t, v in v2.SEEDS.items()}
TARGET = {(a, b) for a in v2.ADJ for b in v2.ADJ[a]
          if a < b and isinstance(mass_of.get(a), str) and mass_of.get(a) == mass_of.get(b)
          and mass_of[a] not in v2.PLAYABLE_ISLANDS}

dg = _load("design/tools/diag-territory-alignment.py", "diag")
# Punto geográfico real de cada territorio: su celda DEBE contenerlo. Sin esta
# restricción el optimizador gana adyacencias mandando, por ejemplo, la semilla
# de Polonia a los Balcanes o la de Uruguay adentro de Brasil.
REF = {}
for key, (lon, lat) in dg.TRUE_LL.items():
    tid = "territory-" + key
    if v2.SEEDS.get(tid, (None,))[0] is not None:
        REF[tid] = g3.project(lon, lat)

def keeps_geography(pos):
    for mass, tids in MASS_TERR.items():
        S = np.array([pos[t] for t in tids])
        for tid in tids:
            if tid not in REF:
                continue
            px, py = REF[tid]
            d = (S[:, 0] - px) ** 2 + (S[:, 1] - py) ** 2
            if tids[int(d.argmin())] != tid:
                return False
    return True

def score(pos):
    if not keeps_geography(pos):
        return -10 ** 9, 0, 0
    got = adjacency(pos)
    return len(TARGET & got) * 100 - len(got - TARGET), len(TARGET & got), len(got - TARGET)

def main():
    true_ll = {t: (v[0], v[1]) for t, v in v2.SEEDS.items() if v[0] is not None}
    cur = dict(true_ll)
    pos = {t: g3.project(*ll) for t, ll in cur.items()}
    best, hit, extra = score(pos)
    t0 = time.time()
    print(f"inicio: {hit}/{len(TARGET)} adyacencias, {extra} extra "
          f"({(time.time()-t0)*1000:.0f} ms/eval aprox)")

    order = sorted(cur)
    for sweep in range(6):
        improved = False
        for tid in order:
            base_lon, base_lat = true_ll[tid]
            cand_best = None
            for dlon in np.arange(-MAX_DRIFT, MAX_DRIFT + 0.01, 1.0):
                for dlat in np.arange(-MAX_DRIFT, MAX_DRIFT + 0.01, 1.0):
                    if math.hypot(dlon, dlat) > MAX_DRIFT:
                        continue
                    trial = dict(pos)
                    trial[tid] = g3.project(base_lon + dlon, base_lat + dlat)
                    sc, h, e = score(trial)
                    if sc > best and (cand_best is None or sc > cand_best[0]):
                        cand_best = (sc, h, e, base_lon + dlon, base_lat + dlat, trial)
            if cand_best:
                best, hit, extra, lo, la, pos = cand_best
                cur[tid] = (lo, la)
                improved = True
                print(f"  sweep{sweep} {tid:42s} -> ({lo:6.1f},{la:5.1f})  {hit}/{len(TARGET)} +{extra}")
        if not improved:
            break

    print(f"\nfinal: {hit}/{len(TARGET)} adyacencias declaradas, {extra} extra")
    got = adjacency(pos)
    for a, b in sorted(TARGET - got):
        print(f"  SIGUE SIN FRONTERA  {a} <-> {b}")
    print()
    for tid in sorted(cur):
        lo, la = cur[tid]
        print(f'    "{tid}": ({lo:.1f}, {la:.1f}, "{v2.SEEDS[tid][2]}"),')

if __name__ == "__main__":
    main()
