import sys, os
import numpy as np, ghparse, graph
from ghparse import it, items, ch
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch
from matplotlib.collections import LineCollection, PatchCollection
from matplotlib import font_manager as fm
FONTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'fonts')
for w in ('400', '500', '600'):
    fm.fontManager.addfont(f'{FONTS}/ibm-plex-mono-{w}.ttf')
    fm.fontManager.addfont(f'{FONTS}/ibm-plex-sans-{w}.ttf')
PAPER = '#F7F5F0'; INK = '#1B1B1B'

def hidden_sources(L):
    """set of (target_idx, source_guid) where the input's WireDisplay == 2"""
    hs = set()
    def walk(c, idx):
        wd = it(c, 'WireDisplay')
        srcs = [v for i, v in items(c, 'Source')]
        if wd == 2:
            for s in srcs: hs.add((idx, s))
        for x in c['ch']:
            if x['n'] != 'ClusterDocument': walk(x, idx)
    for e in L: walk(e['cont'], e['i'])
    return hs

def draw(fn, out, after, W=1920, H=1080, label=None):
    r = ghparse.load(fn); d, L, E, own, pi = graph.build(r)
    hs = hidden_sources(L)
    for e in L:
        b = e['bounds']
        if b is not None and b[0] == 0 and b[1] == 0 and e['pivot'] is not None:
            e['bounds'] = (e['pivot'][0], e['pivot'][1], b[2], b[3])
    ok = [e for e in L if e['bounds'] is not None and not items(e['cont'], 'ID')]
    xs = np.array([e['bounds'][0] for e in ok]); ys = np.array([e['bounds'][1] for e in ok])
    x0, x1 = np.percentile(xs, 0.2) - 200, np.percentile(xs, 99.8) + 400
    y0, y1 = np.percentile(ys, 0.2) - 300, np.percentile(ys, 99.8) + 300
    fig = plt.figure(figsize=(W / 100, H / 100), dpi=100, facecolor=PAPER)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_facecolor(PAPER); ax.axis('off')
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2; s = max((x1 - x0) / W, (y1 - y0) / H) * 1.04
    ax.set_xlim(cx - s * W / 2, cx + s * W / 2); ax.set_ylim(cy + s * H / 2, cy - s * H / 2)
    # groups
    for e in L:
        ids = [v for i, v in items(e['cont'], 'ID')]
        if not ids: continue
        pts = [L[own[g]]['bounds'] for g in ids if g in own and L[own[g]]['bounds'] is not None]
        if not pts: continue
        gx0 = min(p[0] for p in pts); gy0 = min(p[1] for p in pts)
        gx1 = max(p[0] + p[2] for p in pts); gy1 = max(p[1] + p[3] for p in pts)
        col = it(e['cont'], 'Colour') or 'ff888888'
        a, rgb = int(col[:2], 16), '#' + col[2:8]
        if after:
            ax.add_patch(Rectangle((gx0 - 20, gy0 - 20), gx1 - gx0 + 40, gy1 - gy0 + 40, facecolor=rgb, alpha=0.28, edgecolor=rgb, lw=0.8, zorder=0))
            nick = (e['nick'] or '').split('—')[0].split(':')[0].split(' [')[0].strip()
            if nick:
                ax.text(gx0 - 16, gy0 - 40, nick, fontsize=9, family='IBM Plex Mono', color=INK, zorder=5, va='bottom')
        else:
            ax.add_patch(Rectangle((gx0 - 20, gy0 - 20), gx1 - gx0 + 40, gy1 - gy0 + 40, facecolor=rgb, alpha=0.18, edgecolor='none', zorder=0))
    # wires
    segs = []; hidden = 0
    for a_, b_, sp, dp in E:
        if a_ is None: continue
        A, B = L[a_], L[b_]
        if A['bounds'] is None or B['bounds'] is None: continue
        src_guid = None
        if after and any(t == b_ for t, _ in hs):
            # hidden if any hidden (target, source) pair maps to A
            if any(t == b_ and own.get(sg) == a_ for t, sg in hs): hidden += 1; continue
        p0 = np.array([A['bounds'][0] + A['bounds'][2], A['bounds'][1] + A['bounds'][3] / 2])
        p1 = np.array([B['bounds'][0], B['bounds'][1] + B['bounds'][3] / 2])
        dx = max(abs(p1[0] - p0[0]) * 0.5, 40)
        t = np.linspace(0, 1, 24)[:, None]
        c0, c1 = p0 + [dx, 0], p1 - [dx, 0]
        segs.append((1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * c0 + 3 * (1 - t) * t ** 2 * c1 + t ** 3 * p1)
    ax.add_collection(LineCollection(segs, colors='#6f6a60', linewidths=0.35, alpha=0.55, zorder=1))
    rects = [Rectangle((e['bounds'][0], e['bounds'][1]), e['bounds'][2], e['bounds'][3]) for e in ok]
    ax.add_collection(PatchCollection(rects, facecolor=INK, edgecolor='none', zorder=2))
    fig.savefig(out, dpi=100, facecolor=PAPER); plt.close(fig)
    return dict(objects=len(L), wires=len(E), shown=len(segs), hidden=hidden, groups=sum(1 for e in L if items(e['cont'], 'ID')))

if __name__ == '__main__':
    # python canvasmap.py in.gh out.png [after]
    print(draw(sys.argv[1], sys.argv[2], len(sys.argv) > 3))
