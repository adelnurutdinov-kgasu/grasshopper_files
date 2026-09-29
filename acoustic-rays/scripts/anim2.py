import sys, os, math, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection, PolyCollection
import render as R_
from render import PAPER, INK, GREY, LIGHT, ACC, MONO, SANS
import sim2
from multiprocessing import Pool

LAY = R_.LAY
OK = LAY['ok']; BAD = LAY['bad']; LOST = LAY['lost']; PANEL = LAY['panel']
M = sim2.M
R0, N0 = sim2.R0, sim2.N0
TMIN, TMAX = LAY['tilt']['range_deg']


def rng(rows):
    rows = sorted(rows)
    if not rows: return '—'
    parts = []; s = p = rows[0]
    for r in rows[1:]:
        if r == p + 1: p = r; continue
        parts.append(f'{s}–{p}' if p > s else f'{s}'); s = p = r
    parts.append(f'{s}–{p}' if p > s else f'{s}')
    return ', '.join(parts)


def frame(rot, out, W=1920, H=1080):
    Rt, Nt = sim2.transform(R0, N0, rot=rot)
    res = sim2.simulate(Rt, Nt, 60)
    hits = [r for r in res if r['kind'] == 'hit']
    rows_ok = set(); rows_bad = set()
    for h in hits:
        if h['row'] is None: continue
        (rows_bad if h['ms'] > 50 else rows_ok).add(h['row'])
    rows_ok -= rows_bad
    lost = sum(r['kind'] != 'hit' for r in res)
    mx = max((h['ms'] for h in hits), default=0)
    mxd = max((h['dl'] for h in hits), default=0)

    fig = plt.figure(figsize=(W / 100, H / 100), dpi=100, facecolor=PAPER)
    tx = fig.text
    tx(0.0375, 0.935, 'АКУСТИКА ЗАЛА · ПАРАМЕТРИЧЕСКИЙ ЛИСТ', color=ACC, family=MONO, fontsize=12, weight=500)
    tx(0.0375, 0.905, 'наклон отражателя О3 · первые отражения', color=GREY, family=MONO, fontsize=11)
    tx(0.0375, 0.815, f'Наклон {rot:+.0f}°'.replace('-', '−'), color=INK, family=SANS, fontsize=40, weight=600)
    stats = [('РЯДОВ С ОТРАЖЕНИЕМ', f'{len(rows_ok | rows_bad)} из 24'),
             ('РЯДЫ С НАРУШЕНИЕМ', rng(rows_bad)),
             ('МАКС. РАЗНОСТЬ ХОДА', f'{mxd:.1f} м'),
             ('МАКС. ЗАПАЗДЫВАНИЕ', f'{mx:.0f} мс'),
             ('ЛУЧЕЙ МИМО ЗРИТЕЛЕЙ', f'{lost} из {len(res)}')]
    y = 0.745
    for k, v in stats:
        tx(0.0375, y, k, color=GREY, family=MONO, fontsize=10.5)
        c = BAD if (k.startswith('РЯДЫ С') and rows_bad) or (k.startswith('МАКС. З') and mx > 50) or (k.startswith('МАКС. Р') and mxd > 17) else INK
        tx(0.0375, y - 0.032, v, color=c, family=SANS, fontsize=19, weight=500)
        y -= 0.083
    tx(0.0375, y - 0.005, 'НОРМА', color=GREY, family=MONO, fontsize=10.5)
    tx(0.0375, y - 0.037, 'разность хода до 17 м (50 мс)', color=INK, family=SANS, fontsize=15)
    tx(0.0375, y - 0.068, 'нарушена — риск эха' if rows_bad else 'выполняется', color=BAD if rows_bad else OK, family=MONO, fontsize=11, weight=500)
    # slider
    sx0, sx1, sy = 0.0375, 0.245, 0.17
    fig.add_artist(plt.Line2D([sx0, sx1], [sy, sy], color=LIGHT, lw=3, solid_capstyle='round'))
    f0 = sx0 + (0 - TMIN) / (TMAX - TMIN) * (sx1 - sx0)
    fr = sx0 + (rot - TMIN) / (TMAX - TMIN) * (sx1 - sx0)
    fig.add_artist(plt.Line2D([f0, fr], [sy, sy], color=PANEL, lw=3, solid_capstyle='round'))
    fig.add_artist(plt.Line2D([f0, f0], [sy - 0.008, sy + 0.008], color=GREY, lw=1))
    fig.add_artist(plt.Line2D([fr], [sy], marker='o', ms=11, color=PANEL, markeredgecolor=PAPER, mew=2))
    tx(sx0, sy - 0.035, f'{TMIN}°'.replace('-', '−'), color=GREY, family=MONO, fontsize=9.5)
    tx(f0, sy - 0.035, '0° проект', color=GREY, family=MONO, fontsize=9.5, ha='center')
    tx(sx1, sy - 0.035, f'+{TMAX}°', color=GREY, family=MONO, fontsize=9.5, ha='right')
    tx(sx0, sy + 0.022, 'НАКЛОН ЭКРАНА', color=GREY, family=MONO, fontsize=10)
    tx(0.0375, 0.07, 'Grasshopper · Rhino 8 · расчёт отражений по геометрии модели', color=GREY, family=MONO, fontsize=10)

    ax = fig.add_axes(LAY['tilt']['section']); ax.set_facecolor(PAPER); ax.axis('off')
    for g, polys in M['refl'].items():
        if g == sim2.G: continue
        ax.add_collection(PolyCollection(polys, facecolors='#CFCBC2', edgecolors='#B9B4AA', lw=2.0, zorder=5))
    ax.add_collection(LineCollection(M['sec'], colors=INK, lw=0.9, zorder=4))
    ax.plot(R0[:, 0], R0[:, 1], color=GREY, lw=1.2, ls=(0, (3, 2)), zorder=5)
    inc = [[r['S'], r['R']] for r in res if r['kind'] != 'blocked_in']
    ax.add_collection(LineCollection(inc, colors='#9FB7D8', lw=0.5, alpha=0.8, zorder=2))
    ok_s = [[r['R'], r['end']] for r in hits if r['ms'] <= 50]
    bad_s = [[r['R'], r['end']] for r in hits if r['ms'] > 50]
    lost_s = [[r['R'], r['end']] for r in res if r['kind'] == 'lost']
    ax.add_collection(LineCollection(lost_s, colors=LOST, lw=0.6, ls=(0, (2, 2)), zorder=2))
    ax.add_collection(LineCollection(ok_s, colors=OK, lw=0.9, zorder=3))
    ax.add_collection(LineCollection(bad_s, colors=BAD, lw=1.1, zorder=3))
    Rd, _ = sim2.dense(Rt, Nt, 60)
    ax.plot(Rd[:, 0], Rd[:, 1], color=PANEL, lw=4, solid_capstyle='round', zorder=6)
    rx = sim2.ROWS
    cols = [BAD if k + 1 in rows_bad else OK if k + 1 in rows_ok else PAPER for k in range(24)]
    ax.scatter(rx[:, 0], rx[:, 1], s=26, facecolor=cols, edgecolor=INK, lw=0.8, zorder=7)
    for n, (x, z) in enumerate(rx):
        ax.text(x + 0.45, z - 0.55, str(n + 1), family=MONO, fontsize=8, color=INK if (n + 1) in rows_ok | rows_bad else GREY, ha='center', va='top')
    ax.scatter([sim2.S[0]], [sim2.S[1]], s=60, color=ACC, zorder=8)
    ax.text(sim2.S[0] - 0.5, sim2.S[1] + 0.35, 'источник', family=MONO, fontsize=9, color=ACC, ha='right')
    c = Rt.mean(0)
    ax.text(c[0], c[1] + 1.0, 'О3', family=SANS, fontsize=13, weight=600, color=PANEL, ha='center')
    ax.set_xlim(-8.5, 26.5); ax.set_ylim(-2.2, 17.2); ax.set_aspect('equal')
    fig.add_artist(plt.Line2D([0.29, 0.72], [0.255, 0.255], color=LIGHT, lw=0.8))
    tx(0.29, 0.228, 'РАЗРЕЗ · ОТРАЖЕНИЯ ОТ ЭКРАНА О3 (пунктир — проектное положение)', color=GREY, family=MONO, fontsize=10.5)
    lg = [(OK, 'до 50 мс — полезное'), (BAD, 'больше 50 мс — эхо'), (LOST, 'мимо зрителей')]
    for i, (c_, t_) in enumerate(lg):
        fig.add_artist(plt.Line2D([0.29 + i * 0.14, 0.305 + i * 0.14], [0.195, 0.195], color=c_, lw=2.5))
        tx(0.31 + i * 0.14, 0.19, t_, color=INK, family=MONO, fontsize=9.5)

    ac = fig.add_axes(LAY['tilt']['chart']); ac.set_facecolor(PAPER)
    for s in ('top', 'right'): ac.spines[s].set_visible(False)
    for s in ('left', 'bottom'): ac.spines[s].set_color(GREY); ac.spines[s].set_linewidth(0.7)
    ac.axhspan(50, 90, color=BAD, alpha=0.07, lw=0)
    ac.axhline(50, color=BAD, lw=0.9, ls=(0, (4, 3)))
    ac.text(24.6, 51.5, '50 мс', color=BAD, family=MONO, fontsize=9, ha='right', va='bottom')
    hh = [h for h in hits if h['row']]
    ac.scatter([h['row'] for h in hh], [h['ms'] for h in hh], s=18, lw=0, color=[BAD if h['ms'] > 50 else OK for h in hh], zorder=3)
    ac.set_xlim(0.3, 24.7); ac.set_ylim(0, 90)
    ac.set_xticks([1, 6, 12, 18, 24]); ac.set_yticks([0, 25, 50, 75])
    ac.tick_params(colors=GREY, labelsize=9, length=3, width=0.6)
    for lab in ac.get_xticklabels() + ac.get_yticklabels(): lab.set_family(MONO)
    ac.set_xlabel('ряд', family=MONO, fontsize=9, color=GREY); ac.set_ylabel('запаздывание, мс', family=MONO, fontsize=9, color=GREY)
    fig.add_artist(plt.Line2D([0.75, 0.96], [0.37, 0.37], color=LIGHT, lw=0.8))
    tx(0.75, 0.343, 'ЗАПАЗДЫВАНИЕ ПО РЯДАМ', color=GREY, family=MONO, fontsize=10.5)
    # coverage strip
    for k in range(24):
        c_ = BAD if k + 1 in rows_bad else OK if k + 1 in rows_ok else '#E4E0D8'
        fig.patches.append(plt.Rectangle((0.75 + k * 0.00875, 0.27), 0.0078, 0.03, transform=fig.transFigure, color=c_))
    tx(0.75, 0.245, '1', color=GREY, family=MONO, fontsize=9); tx(0.96, 0.245, '24', color=GREY, family=MONO, fontsize=9, ha='right')
    tx(0.75, 0.2, 'ОХВАТ РЯДОВ ЭКРАНОМ О3', color=GREY, family=MONO, fontsize=10.5)
    fig.savefig(out, dpi=100, facecolor=PAPER)
    plt.close(fig)


def ease(a, b, n):
    t = np.linspace(0, 1, n)
    return list(a + (b - a) * t * t * (3 - 2 * t))


SEQ = [0.0] * 12 + ease(0, TMIN, 40) + [TMIN] * 18 + ease(TMIN, TMAX, 60) + [TMAX] * 18 + ease(TMAX, 0, 40) + [0.0] * 12


def job(a):
    i, r = a
    frame(r, f'fr2/{i:04d}.png')


if __name__ == '__main__':
    os.makedirs('fr2', exist_ok=True)
    if len(sys.argv) > 1:
        frame(float(sys.argv[1]), 'test2.png')
    else:
        with Pool(2) as P:
            P.map(job, list(enumerate(SEQ)))
        print(len(SEQ))
