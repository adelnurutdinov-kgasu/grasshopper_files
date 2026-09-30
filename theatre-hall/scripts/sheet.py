import sys, textwrap
from frame import *
def sheet(out):
    S = st('u00')
    fig = plt.figure(figsize=(19.2, 10.8), dpi=100, facecolor=PAPER)
    tx = fig.text
    tx(0.0375, 0.935, 'ТЕАТР · ЗРИТЕЛЬНЫЙ ЗАЛ', color=ACC, family=MONO, fontsize=12, weight=500)
    tx(0.0375, 0.905, 'Grasshopper + Rhino · параметрическая модель', color=GREY, family=MONO, fontsize=11)
    tx(0.0375, 0.80, '909', color=INK, family=SANS, fontsize=64, weight=600)
    tx(0.0375, 0.765, 'мест: партер 683 · балкон 226', color=GREY, family=MONO, fontsize=10.5)
    y = 0.69
    for num, title, body in (CHAP[1], CHAP[2], CHAP[3]):
        tx(0.0375, y, num, color=ACC, family=MONO, fontsize=16, weight=600)
        tx(0.065, y + 0.003, title, color=INK, family=MONO, fontsize=9.5, weight=600)
        tx(0.0375, y - 0.022, '\n'.join(textwrap.wrap(body, 50)), color=INK, family=SANS, fontsize=10.5, va='top', linespacing=1.4)
        y -= 0.2
    for i, (k, c) in enumerate([('кривые Rhino (вход)', BLUE), ('рёбра потолка', ACC), ('партер', '#3A3A3A'), ('балкон', BALC)]):
        yy = 0.105 - (i % 2) * 0.025; xx = 0.0375 + (i // 2) * 0.1
        fig.patches.append(plt.Rectangle((xx, yy), 0.01, 0.012, transform=fig.transFigure, color=c))
        tx(xx + 0.015, yy, k, color=GREY, family=MONO, fontsize=9)
    tx(0.0375, 0.045, 'theatre_hall.gh + theatre_hall.3dm · все варианты посчитаны в Grasshopper', color=GREY, family=MONO, fontsize=9)
    ax = fig.add_axes([0.25, 0.04, 0.50, 0.92]); ax.axis('off')
    draw_model(ax, S); ax.set_xlim(*LIM[0]); ax.set_ylim(*LIM[1]); ax.set_aspect('equal')
    tx(0.78, 0.935, 'ШИРИНА ЗАЛА ПО КРИВЫМ RHINO', color=GREY, family=MONO, fontsize=9.5)
    for j, t in enumerate(['u06', 'u00', 'u16']):
        T = st(t); a = fig.add_axes([0.775 + j * 0.068, 0.70, 0.064, 0.22]); draw_plan(a, T, hl='walls'); a.set_xlim(-27, 19); a.set_ylim(-17, 19.5)
        tx(0.775 + j * 0.068 + 0.032, 0.69, f'{width(T):.1f} м'.replace('.', ','), color=GREY, family=MONO, fontsize=9, ha='center')
        tx(0.775 + j * 0.068 + 0.032, 0.665, f'{total(T)} мест', color=INK if t != 'u00' else ACC, family=SANS, fontsize=12, ha='center', weight=600)
    def small(rect, xs, ys, cur, xl, ttl):
        a = fig.add_axes(rect); a.set_facecolor(PAPER)
        for s in a.spines.values(): s.set_color(LIGHT)
        a.tick_params(colors=GREY, labelsize=8)
        o = np.argsort(xs); a.plot(np.array(xs)[o], np.array(ys)[o], color=GREY, lw=1, marker='o', ms=2.5)
        a.plot([cur[0]], [cur[1]], 'o', color=ACC, ms=6); a.set_xlabel(xl, color=GREY, family=MONO, fontsize=8.5)
        fig.text(rect[0], rect[1] + rect[3] + 0.012, ttl, color=GREY, family=MONO, fontsize=9.5)
    small([0.79, 0.37, 0.18, 0.2], [width(st(t)) for t in CH1], [total(st(t)) for t in CH1], (width(S), 909), 'ширина зала, м', 'МЕСТА ПРИ ИЗМЕНЕНИИ ШИРИНЫ')
    small([0.79, 0.08, 0.18, 0.2], [st(t)['ead2bece']['w'] for t in CH3], [total(st(t)) for t in CH3], (0.56, 909), 'ширина места b, м', 'МЕСТА ПРИ ИЗМЕНЕНИИ b')
    fig.savefig(out + '.png', dpi=100, facecolor=PAPER); fig.savefig(out + '.svg', facecolor=PAPER)
sheet(sys.argv[1])
