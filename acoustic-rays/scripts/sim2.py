import sys, math, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import render

M = render.load(os.path.join(render.HERE, 'base.json'))
S = np.array(M['S'])
ROWS = np.array(M['rows'])
G = '{0;3}'
LOWER = ROWS[:18]; BALC = ROWS[18:]


def base_panel():
    rays = sorted([r for r in M['rays'] if r['g'] == G], key=lambda r: r['R'][0])
    R = np.array([r['R'] for r in rays])
    N = []
    for r in rays:
        Rp = np.array(r['R']); L = np.array(r['L'])
        i1 = (S - Rp) / np.linalg.norm(S - Rp); i2 = (L - Rp) / np.linalg.norm(L - Rp)
        b = i1 + i2; N.append(b / np.linalg.norm(b))
    R = np.array(R); N = np.array(N)
    keep = np.r_[True, np.linalg.norm(np.diff(R, axis=0), axis=1) > 1e-3]
    return R[keep], N[keep]


R0, N0 = base_panel()


def dense(R, N, k=60):
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(R, axis=0), axis=1))]
    u = np.linspace(0, s[-1], k)
    Rx = np.interp(u, s, R[:, 0]); Rz = np.interp(u, s, R[:, 1])
    ang = np.unwrap(np.arctan2(N[:, 1], N[:, 0]))
    a = np.interp(u, s, ang)
    return np.c_[Rx, Rz], np.c_[np.cos(a), np.sin(a)]


def transform(R, N, dx=0.0, dz=0.0, rot=0.0, scale=1.0, bend=0.0):
    c = R.mean(0)
    r = math.radians(rot)
    Q = np.array([[math.cos(r), -math.sin(r)], [math.sin(r), math.cos(r)]])
    R2 = (R - c) * scale @ Q.T + c + np.array([dx, dz])
    t = np.linspace(-1, 1, len(N))
    ang = np.arctan2(N[:, 1], N[:, 0]) + r + np.radians(bend) * t
    return R2, np.c_[np.cos(ang), np.sin(ang)]


SEGS = []
for p in M['sec']:
    p = np.array(p)
    for a, b in zip(p[:-1], p[1:]):
        SEGS.append((a, b, 'wall'))
for tier, pts in (('aud', LOWER), ('aud', BALC)):
    for a, b in zip(pts[:-1], pts[1:]):
        SEGS.append((a, b, tier))


def cast(p, d, maxlen=80):
    best = (maxlen, None, None)
    for a, b, kind in SEGS:
        e = b - a
        den = d[0] * e[1] - d[1] * e[0]
        if abs(den) < 1e-12: continue
        t = ((a - p)[0] * e[1] - (a - p)[1] * e[0]) / den
        u = ((a - p)[0] * d[1] - (a - p)[1] * d[0]) / den
        if 1e-3 < t < best[0] and 0 <= u <= 1:
            best = (t, kind, p + t * d)
    return best


def row_of(X):
    dd = np.linalg.norm(ROWS - X, axis=1)
    k = int(np.argmin(dd))
    return k + 1 if dd[k] < 0.7 else None


def simulate(R, N, k=60):
    Rd, Nd = dense(R, N, k)
    out = []
    for P, n in zip(Rd, Nd):
        v = P - S; L0 = np.linalg.norm(v); v = v / L0
        t, kind, _ = cast(S, v)
        if t < L0 - 1e-3:
            out.append(dict(R=P, S=S, kind='blocked_in', end=S + v * t)); continue
        if np.dot(-v, n) <= 0:
            out.append(dict(R=P, S=S, kind='back', end=P)); continue
        w = v - 2 * np.dot(v, n) * n
        t, kind, X = cast(P, w)
        if kind != 'aud':
            out.append(dict(R=P, S=S, kind='lost', end=P + w * min(t, 30))); continue
        dl = L0 + t - np.linalg.norm(X - S)
        out.append(dict(R=P, S=S, kind='hit', end=X, dl=dl, ms=dl / 343 * 1000, row=row_of(X)))
    return out


if __name__ == '__main__':
    for kw in [{}, dict(dx=4, dz=1.7), dict(dx=8, dz=3.4), dict(rot=10), dict(rot=-10), dict(rot=20), dict(dz=-4), dict(bend=30), dict(dx=-4, dz=-1.7), dict(dx=6, dz=2.5, rot=-20)]:
        o = simulate(*transform(R0, N0, **kw))
        h = [x for x in o if x['kind'] == 'hit']
        rows = sorted(set(x['row'] for x in h if x['row']))
        print(kw, 'hit', len(h), 'lost', sum(x['kind'] == 'lost' for x in o), 'rows', rows[:3], '..', rows[-2:], len(rows), 'max ms', round(max((x['ms'] for x in h), default=0), 1), 'viol', sum(x['ms'] > 50 for x in h))
