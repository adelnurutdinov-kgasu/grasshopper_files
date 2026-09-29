import json, math, sys, collections, os
HERE = os.path.dirname(os.path.abspath(__file__))
LAY = json.load(open(os.path.join(HERE, 'layout.json'), encoding='utf-8'))
import numpy as np
import matplotlib; matplotlib.use('Agg'); matplotlib.rcParams['svg.fonttype'] = 'none'
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection, PolyCollection
from matplotlib import font_manager as fm
for w in ('400', '500', '600'):
    fm.fontManager.addfont(f'/root/fonts/ibm-plex-mono-{w}.ttf')
    fm.fontManager.addfont(f'/root/fonts/ibm-plex-sans-{w}.ttf')
PAPER = LAY['paper']; INK = LAY['ink']; GREY = '#8A8780'; LIGHT = '#CFCBC2'; ACC = LAY['accent']
MONO = 'IBM Plex Mono'; SANS = 'IBM Plex Sans'

_RC = LAY['reflector_colors']
PAL = {'{0;5}': _RC['О1'], '{0;4}': _RC['О2'], '{0;3}': _RC['О3'], '{0;2}': _RC['О4'], '{0;1}': _RC['О5'], '{0;0}': _RC['О6']}
ORDER = ['{0;5}', '{0;4}', '{0;3}', '{0;2}', '{0;1}', '{0;0}']
NAMES = {'{0;5}': 'О1', '{0;4}': 'О2', '{0;3}': 'О3', '{0;2}': 'О4', '{0;1}': 'О5', '{0;0}': 'О6'}
C = 343.0
NORM_MS = 50.0


def load(fn):
    d = json.load(open(fn))
    gh = collections.defaultdict(list)
    for i in d['gh']:
        gh[i['src']].append(i)
    rh = d['rh']
    S = (0.0, 1.5)
    xz = lambda p: [(q[0], q[2]) for q in p]
    sec = [i for i in rh if min(q[2] for q in i['p']) > -2 and i['t'] != 'pt']
    sec = [i for i in sec if not (len(i['p']) == 2 and abs(i['p'][0][0]) < 1e-3 and abs(i['p'][0][2] - 1.5) < 1e-3)]
    plan = [i for i in rh if max(q[2] for q in i['p']) < -2 and i['t'] != 'pt']
    rows = sorted([tuple(xz(i['p'])[1]) for i in gh['365da89f']], key=lambda p: (p[1] > 8, p[0]))
    rays = []
    D = lambda a, b: math.hypot(a[0] - b[0], a[1] - b[1])
    for i in gh['ac0dfd1a']:
        L, R, Sx = xz(i['p'])
        dl = D(Sx, R) + D(R, L) - D(Sx, L)
        k = min(range(len(rows)), key=lambda r: D(rows[r], L))
        rays.append(dict(g=i['path'], L=L, R=R, S=Sx, row=k + 1, dl=dl, ms=dl / C * 1000))
    fans = collections.defaultdict(list)
    for i in gh['b03bc5e8']:
        key = '{0;' + i['path'].strip('{}').split(';')[-1] + '}'
        fans[key].append(xz(i['p']))
    refl = collections.defaultdict(list)
    for i in gh['40a0e611']:
        P = np.array(xz(i['p']))
        best = min(ORDER, key=lambda g: min(np.min(np.hypot(P[:, 0] - r['R'][0], P[:, 1] - r['R'][1])) for r in rays if r['g'] == g))
        refl[best].append(xz(i['p']))
    return dict(sec=[xz(i['p']) for i in sec], plan=[xz(i['p']) for i in plan], rows=rows, rays=rays, fans=fans, refl=refl,
                direct=[xz(i['p']) for i in gh['365da89f']], S=S)


def sub_ray(r, t):
    """ray drawn from source S -> R -> L, parameter t in [0,1]"""
    S, R, L = r['S'], r['R'], r['L']
    a = math.dist(S, R); b = math.dist(R, L); tot = (a + b) * t
    if tot <= a:
        f = tot / a if a else 1
        return [S, (S[0] + (R[0] - S[0]) * f, S[1] + (R[1] - S[1]) * f)]
    f = (tot - a) / b if b else 1
    return [S, R, (R[0] + (L[0] - R[0]) * f, R[1] + (L[1] - R[1]) * f)]


def frame(M, out, prog=None, title_group=None, W=1920, H=1080):
    """prog: dict group -> t in [0,1] (None = all complete)"""
    if prog is None:
        prog = {g: 1.0 for g in ORDER}
    fig = plt.figure(figsize=(W / 100, H / 100), dpi=100, facecolor=PAPER)
    # ---------- left column
    tx = fig.text
    tx(0.0375, 0.935, 'АКУСТИКА ЗАЛА · ПАРАМЕТРИЧЕСКИЙ ЛИСТ', color=ACC, family=MONO, fontsize=12, weight=500)
    tx(0.0375, 0.905, 'первые отражения · потолок и балкон', color=GREY, family=MONO, fontsize=11)
    tx(0.0375, 0.815, 'Зал на 24 ряда', color=INK, family=SANS, fontsize=40, weight=600)
    done = [r for r in M['rays'] if prog.get(r['g'], 0) >= 1]
    shown = [g for g in ORDER if prog.get(g, 0) > 0]
    cov = collections.Counter(r['row'] for r in done)
    stats = [
        ('ОТРАЖАТЕЛЕЙ', f"{len(shown)} из 6"),
        ('ЛУЧЕЙ', f"{len(done)}"),
        ('РЯДОВ С ОТРАЖЕНИЕМ', f"{len(cov)} из 24"),
        ('МАКС. РАЗНОСТЬ ХОДА', f"{max((r['dl'] for r in done), default=0):.1f} м"),
        ('МАКС. ЗАПАЗДЫВАНИЕ', f"{max((r['ms'] for r in done), default=0):.0f} мс"),
    ]
    y = 0.745
    for k, v in stats:
        tx(0.0375, y, k, color=GREY, family=MONO, fontsize=10.5)
        tx(0.0375, y - 0.032, v, color=INK, family=SANS, fontsize=19, weight=500)
        y -= 0.083
    ok = all(r['ms'] <= NORM_MS for r in done)
    tx(0.0375, y - 0.005, 'НОРМА', color=GREY, family=MONO, fontsize=10.5)
    tx(0.0375, y - 0.037, 'разность хода до 17 м', color=INK, family=SANS, fontsize=15)
    if done:
        tx(0.0375, y - 0.068, 'выполняется' if ok else 'нарушена', color=('#3E9E57' if ok else ACC), family=MONO, fontsize=11, weight=500)
    # legend chips
    ly = 0.155
    for n, g in enumerate(ORDER):
        on = prog.get(g, 0) > 0
        x0 = 0.0375 + n * 0.042
        fig.patches.append(plt.Rectangle((x0, ly), 0.034, 0.006, transform=fig.transFigure, color=PAL[g] if on else LIGHT))
        tx(x0, ly - 0.03, NAMES[g], color=INK if on else GREY, family=SANS, fontsize=10, weight=600 if g == title_group else 400)
    tx(0.0375, 0.07, 'Grasshopper · Anemone · Rhino 8  /  физика тест11.gh', color=GREY, family=MONO, fontsize=10)

    # ---------- section
    ax = fig.add_axes(LAY['sheet']['section']); ax.set_facecolor(PAPER); ax.axis('off')
    for g in ORDER:
        t = prog.get(g, 0)
        if t <= 0: continue
        a = 0.16 * min(1, t * 1.5)
        ax.add_collection(PolyCollection(M['fans'][g], facecolors=PAL[g], alpha=a, edgecolors='none', zorder=1))
    ax.add_collection(LineCollection(M['sec'], colors=INK, lw=0.9, zorder=4))
    ax.add_collection(LineCollection(M['direct'], colors=LIGHT, lw=0.5, zorder=2))
    for g in ORDER:
        t = prog.get(g, 0)
        if t <= 0: continue
        segs = [sub_ray(r, t) for r in M['rays'] if r['g'] == g]
        ax.add_collection(LineCollection(segs, colors=PAL[g], lw=1.0 if g == title_group else 0.7, alpha=0.95, zorder=3))
    for g, polys in M['refl'].items():
        on = prog.get(g, 0) > 0
        ax.add_collection(PolyCollection(polys, facecolors=PAL[g] if on else '#BDB8AE', edgecolors=PAL[g] if on else '#9C978D', lw=2.4, zorder=5))
    rx = np.array(M['rows'])
    ax.scatter(rx[:, 0], rx[:, 1], s=14, facecolor=PAPER, edgecolor=INK, lw=0.8, zorder=6)
    ax.scatter([M['S'][0]], [M['S'][1]], s=60, color=ACC, zorder=7)
    ax.text(M['S'][0] - 0.5, M['S'][1] + 0.35, 'источник', family=MONO, fontsize=9, color=ACC, ha='right')
    for n, (x, z) in enumerate(M['rows']):
        c = INK if cov.get(n + 1) else GREY
        ax.text(x + 0.45, z - 0.55, str(n + 1), family=MONO, fontsize=8, color=c, ha='center', va='top', zorder=6)
    ax.set_xlim(-8.5, 26.5); ax.set_ylim(-2.2, 17.2); ax.set_aspect('equal')
    fig.add_artist(plt.Line2D([0.29, 0.72], [0.255, 0.255], color=LIGHT, lw=0.8))
    tx(0.29, 0.228, 'РАЗРЕЗ · ВЕЕРА ПЕРВЫХ ОТРАЖЕНИЙ ПО ОТРАЖАТЕЛЯМ', color=GREY, family=MONO, fontsize=10.5)

    # ---------- plan
    ap = fig.add_axes(LAY['sheet']['plan']); ap.set_facecolor(PAPER); ap.axis('off')
    ap.add_collection(LineCollection(M['plan'], colors=INK, lw=0.35))
    pts = np.array([q for p in M['plan'] for q in p])
    ap.set_xlim(pts[:, 0].min() - 0.5, pts[:, 0].max() + 0.5); ap.set_ylim(pts[:, 1].min() - 0.5, pts[:, 1].max() + 0.5); ap.set_aspect('equal')
    fig.add_artist(plt.Line2D([0.75, 0.96], [0.535, 0.535], color=LIGHT, lw=0.8))
    tx(0.75, 0.508, 'ПЛАН · 24 РЯДА, БАЛКОН 19–24', color=GREY, family=MONO, fontsize=10.5)

    # ---------- delay chart
    ac = fig.add_axes(LAY['sheet']['chart']); ac.set_facecolor(PAPER)
    for s in ('top', 'right'): ac.spines[s].set_visible(False)
    for s in ('left', 'bottom'): ac.spines[s].set_color(GREY); ac.spines[s].set_linewidth(0.7)
    ac.axhline(NORM_MS, color=ACC, lw=0.9, ls=(0, (4, 3)))
    ac.text(24.6, NORM_MS + 1.5, '50 мс', color=ACC, family=MONO, fontsize=9, ha='right', va='bottom')
    for g in ORDER:
        rr = [r for r in done if r['g'] == g]
        if rr:
            ac.scatter([r['row'] for r in rr], [r['ms'] for r in rr], s=16, color=PAL[g], zorder=3, lw=0)
    ac.set_xlim(0.3, 24.7); ac.set_ylim(0, 60)
    ac.set_xticks([1, 6, 12, 18, 24]); ac.set_yticks([0, 20, 40, 60])
    ac.tick_params(colors=GREY, labelsize=9, length=3, width=0.6)
    for lab in ac.get_xticklabels() + ac.get_yticklabels(): lab.set_family(MONO)
    ac.set_xlabel('ряд', family=MONO, fontsize=9, color=GREY); ac.set_ylabel('задержка, мс', family=MONO, fontsize=9, color=GREY)
    fig.add_artist(plt.Line2D([0.75, 0.96], [0.155, 0.155], color=LIGHT, lw=0.8))
    tx(0.75, 0.128, 'ЗАПАЗДЫВАНИЕ ОТРАЖЁННОГО ЗВУКА', color=GREY, family=MONO, fontsize=10.5)
    fig.savefig(out, dpi=100, facecolor=PAPER)
    plt.close(fig)


if __name__ == '__main__':
    M = load(os.path.join(HERE, 'base.json'))
    frame(M, sys.argv[1] if len(sys.argv) > 1 else 'sheet.png')
