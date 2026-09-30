import sys, os, json, math
import numpy as np
from render import *

TAGS = [f'u{i:02d}' for i in range(43)]
CACHE = {}
def st(tag):
    if tag not in CACHE: CACHE[tag] = load(tag)
    return CACHE[tag]
def total(S): return S['ead2bece']['n'] + S['521ebb6c']['n']
CH1 = [f'u{i:02d}' for i in [6,5,4,3,2,1,0,7,8,9,10,11,12,13,14,15,16]]
CH3 = ['u39', 'u38', 'u37', 'u00', 'u40', 'u41', 'u42']
CHAP = {
 1: ('01', 'СТЕНЫ И РЯДЫ · КРИВЫЕ RHINO', 'Контур стен и оси рядов — кривые в Rhino. Grasshopper строит по ним стены (Offset, Boundary, Extrude) и расставляет кресла. Кривые масштабируются по ширине — модель пересобирается целиком.'),
 2: ('02', 'РЁБРА ПОТОЛКА · 6 ПОЛЗУНКОВ', 'Две опорные дуги, между ними 5 рёбер (Tween Through Curves) + 6-е за пределами (Tween Consecutive). Рёбра проецируются на поверхность потолка из Rhino.'),
 3: ('03', 'РАССАДКА · ШИРИНА МЕСТА', 'Внутри кластера: ряд минус 0,5 м с концов делится на места. n = floor((L − 1,0) / b). Меняем b — меняется число мест.'),
}
SX = {t: st(t)['st']['sx'] for t in CH1}
BASE = st('u00')

def left(fig, S, ch, extra=None):
    tx = fig.text
    tx(0.0375, 0.935, 'ТЕАТР · ЗРИТЕЛЬНЫЙ ЗАЛ', color=ACC, family=MONO, fontsize=12, weight=500)
    tx(0.0375, 0.905, 'Grasshopper + Rhino · параметрическая модель', color=GREY, family=MONO, fontsize=11)
    n = total(S)
    tx(0.0375, 0.80, f'{n}', color=INK, family=SANS, fontsize=64, weight=600)
    d = n - total(BASE)
    tx(0.0375, 0.765, 'мест в зале' + (f'   ({d:+d} к исходным 909)' if d else '   (исходный вариант)'), color=GREY, family=MONO, fontsize=10.5)
    rows = [('партер', f"{S['ead2bece']['n']} мест · {S['ead2bece']['rows']} рядов"),
            ('балкон', f"{S['521ebb6c']['n']} мест · {S['521ebb6c']['rows']} рядов"),
            ('ширина зала', f'{width(S):.1f} м'.replace('.', ',')),
            ('ширина места', f"{S['ead2bece']['w']:.2f} м".replace('.', ',')),
            ('рёбра потолка', '5 + 1 · 6 ползунков')]
    y = 0.70
    for a, b in rows:
        tx(0.0375, y, a.upper(), color=GREY, family=MONO, fontsize=9.5)
        tx(0.0375, y - 0.024, b, color=INK, family=SANS, fontsize=14)
        y -= 0.062
    if ch:
        num, title, body = CHAP[ch]
        y0 = 0.33
        fig.add_artist(plt.Line2D([0.0375, 0.225], [y0 + 0.03, y0 + 0.03], color=LIGHT, lw=0.8))
        tx(0.0375, y0, num, color=ACC, family=MONO, fontsize=22, weight=600)
        tx(0.075, y0 + 0.004, title, color=INK, family=MONO, fontsize=10.5, weight=600)
        import textwrap
        tx(0.0375, y0 - 0.03, '\n'.join(textwrap.wrap(body, 44)), color=INK, family=SANS, fontsize=11.5, va='top', linespacing=1.45)
    for i, (k, c) in enumerate([('кривые Rhino (вход)', BLUE), ('рёбра потолка', ACC), ('партер', '#3A3A3A'), ('балкон', BALC)]):
        yy = 0.105 - (i % 2) * 0.025; xx = 0.0375 + (i // 2) * 0.1
        fig.patches.append(plt.Rectangle((xx, yy), 0.01, 0.012, transform=fig.transFigure, color=c))
        tx(xx + 0.015, yy, k, color=GREY, family=MONO, fontsize=9)
    tx(0.0375, 0.045, 'theatre_hall.gh + theatre_hall.3dm · кадры посчитаны в Grasshopper', color=GREY, family=MONO, fontsize=9)

def chart(fig, S, ch):
    ax = fig.add_axes([0.80, 0.10, 0.17, 0.25]); ax.set_facecolor(PAPER)
    for s in ax.spines.values(): s.set_color(LIGHT)
    ax.tick_params(colors=GREY, labelsize=8)
    for l in ax.get_xticklabels() + ax.get_yticklabels(): l.set_family(MONO)
    if ch == 2:
        keys = ['40dd1ac8', '9ad8e9dd', '03c820c6', '5c8bb681', '4654d70d']
        v = [S['st']['sl'][k] for k in keys]; ex = S['st']['sl']['4f2a7a59']
        ax.set_xlim(-0.05, 2.05); ax.set_ylim(-0.5, 1.5); ax.set_yticks([])
        ax.axvspan(0, 1, color='#EFEBE3', zorder=0)
        ax.plot([0, 2], [0.5, 0.5], color=LIGHT, lw=0.8)
        for x in v: ax.plot([x, x], [0.2, 0.8], color=ACC, lw=2)
        ax.plot([ex, ex], [0.2, 0.8], color=ACC, lw=2, ls=(0, (2, 1.5)))
        ax.set_xticks([0, 1, 2]); ax.set_xticklabels(['дуга А', 'дуга Б', '2'])
        fig.text(0.80, 0.375, 'ПОЛОЖЕНИЯ РЁБЕР (ФАКТОР TWEEN)', color=GREY, family=MONO, fontsize=9.5)
        return
    if ch == 3:
        xs = [st(t)['ead2bece']['w'] for t in CH3]; ys = [total(st(t)) for t in CH3]; cur = S['ead2bece']['w']; xl = 'ширина места b, м'
    else:
        xs = [width(st(t)) for t in CH1]; ys = [total(st(t)) for t in CH1]; cur = width(S); xl = 'ширина зала, м'
    o = np.argsort(xs); xs = np.array(xs)[o]; ys = np.array(ys)[o]
    ax.plot(xs, ys, color=LIGHT, lw=1.2, marker='o', ms=2.5, mfc=GREY, mec='none')
    ax.plot([cur], [total(S)], 'o', ms=7, color=ACC)
    ax.axhline(total(BASE), color=GREY, lw=0.6, ls=(0, (2, 2)))
    ax.set_xlabel(xl, color=GREY, family=MONO, fontsize=8.5)
    fig.text(0.80, 0.375, 'ЧИСЛО МЕСТ', color=GREY, family=MONO, fontsize=9.5)

LIM = None
def frame(S, ch, out, hl=None, rib_alpha=1.0, W=1920, H=1080, fmt=None):
    global LIM
    fig = plt.figure(figsize=(W / 100, H / 100), dpi=100, facecolor=PAPER)
    left(fig, S, ch)
    ax = fig.add_axes([0.25, 0.04, 0.53, 0.92]); ax.set_facecolor(PAPER); ax.axis('off')
    draw_model(ax, S, hl=hl, rib_alpha=rib_alpha)
    ax.set_xlim(*LIM[0]); ax.set_ylim(*LIM[1]); ax.set_aspect('equal')
    ap = fig.add_axes([0.80, 0.45, 0.17, 0.45]); ap.set_facecolor(PAPER)
    draw_plan(ap, S, hl=hl); ap.set_xlim(-27, 19); ap.set_ylim(-17, 19.5)
    fig.add_artist(plt.Line2D([0.80, 0.97], [0.43, 0.43], color=LIGHT, lw=0.8))
    fig.text(0.80, 0.905, 'ПЛАН', color=GREY, family=MONO, fontsize=9.5)
    chart(fig, S, ch)
    fig.savefig(out, dpi=100, facecolor=PAPER)
    plt.close(fig)

def limits():
    global LIM
    pts = []
    for t in ('u06', 'u16'):
        S = st(t)
        for k in ('walls_h12', 'ceiling'):
            for m in S[k]: pts.append(iso(np.array(m['v']))[0])
    P = np.vstack(pts); m = 1.5
    LIM = ((P[:, 0].min() - m, P[:, 0].max() + m), (P[:, 1].min() - m, P[:, 1].max() + m))
limits()
if __name__ == '__main__':
    frame(st(sys.argv[1]), int(sys.argv[2]), sys.argv[3], hl=sys.argv[4] if len(sys.argv) > 4 else None)
