import json, math, os, sys, glob
import numpy as np
import matplotlib; matplotlib.use('Agg'); matplotlib.rcParams['svg.fonttype'] = 'none'
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection, LineCollection
from matplotlib import font_manager as fm
HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, '..', 'fonts')  # IBM Plex, SIL OFL (fonts/OFL.txt)
for w in ('400', '500', '600'):
    fm.fontManager.addfont(os.path.join(FONTS, f'ibm-plex-mono-{w}.ttf')); fm.fontManager.addfont(os.path.join(FONTS, f'ibm-plex-sans-{w}.ttf'))
PAPER = '#F7F5F0'; INK = '#1B1B1B'; GREY = '#8A8780'; LIGHT = '#CFCBC2'; ACC = '#E0513A'; BLUE = '#2F5D8C'; BALC = '#B58A4C'
MONO = 'IBM Plex Mono'; SANS = 'IBM Plex Sans'
MOVE = np.array([0, -20, 0.19])
ANG = math.radians(-32)
STDIR = os.path.join(HERE, 'states')

def load(tag):
    return json.load(open(os.path.join(STDIR, f'theatre_st_{tag}.json')))

def iso(P):
    P = np.asarray(P, float)
    ca, sa = math.cos(ANG), math.sin(ANG)
    u = P[:, 0] * ca - P[:, 1] * sa
    w = P[:, 0] * sa + P[:, 1] * ca
    return np.c_[u, w * 0.55 + P[:, 2] * 0.85], w

def seats(S, ck):
    F = np.array(S[ck]['f']); O = F[:, :3] + MOVE; X = F[:, 3:6]
    X[:, 2] = 0; X /= np.linalg.norm(X, axis=1)[:, None] + 1e-9
    T = np.c_[-X[:, 1], X[:, 0], 0 * X[:, 0]]
    hw, d0, d1 = 0.25, -0.05, 0.45
    corners = np.stack([O - T * hw + X * d0, O + T * hw + X * d0, O + T * hw + X * d1, O - T * hw + X * d1], 1)
    return O, corners

def width(S):
    W = np.array([p for c in S['wall_crv'] for p in c]); return W[:, 0].max() - W[:, 0].min()

def mesh_polys(m, zoff=0.0):
    V = np.array(m['v']); V = V + [0, 0, zoff]; F = np.array(m['f'])
    return V, F

def shade(V, F, base, light=np.array([-0.4, -0.7, 0.6])):
    p = V[F]; n = np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0]); n /= np.linalg.norm(n, axis=1)[:, None] + 1e-9
    l = light / np.linalg.norm(light); s = np.abs(n @ l)
    c = np.array(matplotlib.colors.to_rgb(base))
    return np.clip(c[None] * (0.72 + 0.35 * s[:, None]), 0, 1)

def draw_model(ax, S, hl=None, rib_alpha=1.0):
    polys, cols, dep = [], [], []
    def add(P2, c, d):
        polys.append(P2); cols.append(c); dep.append(d)
    for m in S['floor']:
        V, F = mesh_polys(m); q, w = iso(V)
        for f in F: add(q[f], matplotlib.colors.to_rgba('#E9E5DC'), 1e9)
    for ck, col in (('ead2bece', '#3A3A3A'), ('521ebb6c', BALC)):
        O, C = seats(S, ck)
        for c in C:
            q, w = iso(c); add(q, matplotlib.colors.to_rgba(col), w.mean() - c[:, 2].mean() * 0.01)
    order = np.argsort(dep)[::-1]
    ax.add_collection(PolyCollection([polys[i] for i in order], facecolors=[cols[i] for i in order], edgecolors='none', zorder=2))
    # walls: translucent inner (h8) with outlines
    for m in S['walls_h8']:
        V, F = mesh_polys(m); q, w = iso(V)
        fc = shade(V, F, '#FFFFFF')
        d = w[F].mean(1); o = np.argsort(d)[::-1]
        ax.add_collection(PolyCollection([q[F[i]] for i in o], facecolors=[(*fc[i], 0.42) for i in o], edgecolors=(0.55, 0.53, 0.5, 0.35), lw=0.3, zorder=3))
    # rhino control curves
    for c in S['wall_crv']:
        q, _ = iso(np.array(c)); ax.plot(q[:, 0], q[:, 1], color=BLUE, lw=2.6 if hl == 'walls' else 1.5, zorder=6, solid_capstyle='round')
        ax.plot(q[:1, 0], q[:1, 1], 'o', ms=5 if hl == 'walls' else 3.5, color=BLUE, zorder=7)
    # ceiling ghost + ribs
    for m in S['ceiling']:
        V, F = mesh_polys(m); q, w = iso(V)
        d = w[F].mean(1); o = np.argsort(d)[::-1]
        fc = shade(V, F, '#DCE4EA')
        ax.add_collection(PolyCollection([q[F[i]] for i in o], facecolors=[(*fc[i], 0.07) for i in o], edgecolors='none', zorder=4))
    for c in S['rib_guides']:
        q, _ = iso(np.array(c)); ax.plot(q[:, 0], q[:, 1], color=GREY, lw=0.8, ls=(0, (3, 2)), zorder=5)
    for c in S['ribs']:
        q, _ = iso(np.array(c)); ax.plot(q[:, 0], q[:, 1], color=ACC, lw=2.0 if hl == 'ribs' else 1.3, alpha=rib_alpha, zorder=6)

def draw_plan(ax, S, hl=None):
    for m in S['floor']:
        V, F = mesh_polys(m); ax.add_collection(PolyCollection([V[f][:, :2] for f in F], facecolors='#E9E5DC', edgecolors='none'))
    for m in S['walls_h8']:
        V, F = mesh_polys(m); ax.add_collection(PolyCollection([V[f][:, :2] for f in F], facecolors='#BDB8AE', edgecolors='none'))
    for ck, col in (('ead2bece', '#3A3A3A'), ('521ebb6c', BALC)):
        O, C = seats(S, ck)
        ax.add_collection(PolyCollection(C[:, :, :2], facecolors=col, edgecolors='none'))
    for c in S['ribs']:
        P = np.array(c); ax.plot(P[:, 0], P[:, 1], color=ACC, lw=1.4 if hl == 'ribs' else 0.9)
    for c in S['wall_crv']:
        P = np.array(c); ax.plot(P[:, 0], P[:, 1], color=BLUE, lw=1.8 if hl == 'walls' else 1.2)
        ax.plot(P[:1, 0], P[:1, 1], 'o', ms=3, color=BLUE)
    ax.set_aspect('equal'); ax.axis('off')
