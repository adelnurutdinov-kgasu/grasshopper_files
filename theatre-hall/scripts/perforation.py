import json, os, sys, textwrap, numpy as np
from frame import *
PF = [json.load(open(os.path.join(HERE, 'perf', f'perf_{k}.json'))) for k in range(5)]
NH = sum(len(p['holes']) for p in PF)
CHAP[4] = ('04', 'ПЕРФОРАЦИЯ ПОТОЛКА · ПЯТНА',
           'Полосы — Loft между рёбрами. На полосе регулярная сетка 0,25 м, центры пятен у кромок. '
           'Диаметр отверстия падает от центра пятна к краю (Graph Mapper), пятно вытянуто вдоль ребра.')
def circ(h, n=10, scale=1.0):
    c = np.array(h[:3]); nn = np.array(h[3:6]); r = h[6] * scale
    a = np.cross(nn, [0, 0, 1.0]); a = a / np.linalg.norm(a) if np.linalg.norm(a) > 1e-6 else np.array([1.0, 0, 0]); b = np.cross(nn, a)
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    return c + r * (np.cos(t)[:, None] * a + np.sin(t)[:, None] * b)
def hole_order(p):
    C = np.array(p['centers']); H = np.array([h[:3] for h in p['holes']])
    d = np.min(np.linalg.norm(H[:, None, :] - C[None], axis=2), axis=1)
    return d / (d.max() + 1e-9)
ORD = [hole_order(p) for p in PF]
def draw_perf(ax, prog=1.0):
    polys, cols, dep = [], [], []
    for k, p in enumerate(PF):
        a = np.clip(prog * 5 - k, 0, 1)
        if a <= 0: continue
        V = np.array(p['strip']['v']); F = np.array(p['strip']['f']); q, w = iso(V); fc = shade(V, F, '#E6DFD4')
        for j, f in enumerate(F): polys.append(q[f]); cols.append((*fc[j], 0.92 * a)); dep.append(w[f].mean())
    if polys:
        o = np.argsort(dep)[::-1]
        ax.add_collection(PolyCollection([polys[i] for i in o], facecolors=[cols[i] for i in o], edgecolors='none', zorder=5))
    for k, p in enumerate(PF):
        a = np.clip(prog * 5 - k, 0, 1)
        if a <= 0: continue
        hp = [iso(circ(h))[0] for h, t in zip(p['holes'], ORD[k]) if t <= a]
        if hp: ax.add_collection(PolyCollection(hp, facecolors=ACC, edgecolors='none', zorder=6))
def plan_perf(ax, prog=1.0):
    for k, p in enumerate(PF):
        a = np.clip(prog * 5 - k, 0, 1)
        if a <= 0: continue
        V = np.array(p['strip']['v']); ax.add_collection(PolyCollection([V[f][:, :2] for f in p['strip']['f']], facecolors='#E6DFD4', edgecolors='none'))
        hp = [circ(h)[:, :2] for h, t in zip(p['holes'], ORD[k]) if t <= a]
        if hp: ax.add_collection(PolyCollection(hp, facecolors=ACC, edgecolors='none'))
def closeup(ax, k=2, j=2):
    p = PF[k]; c = np.array(p['centers'][j])
    H = [h for h in p['holes'] if np.linalg.norm(np.array(h[:3]) - c) < 5.5]
    nn = np.mean([h[3:6] for h in H], axis=0); nn /= np.linalg.norm(nn)
    a = np.cross(nn, [0, 0, 1.0]); a /= np.linalg.norm(a); b = np.cross(nn, a)
    for h in H:
        d = np.array(h[:3]) - c
        ax.add_patch(plt.Circle((d @ a, d @ b), h[6], color=ACC, lw=0))
    ax.set_xlim(-5, 5); ax.set_ylim(-3.2, 3.2); ax.set_aspect('equal')
    ax.set_facecolor('#E6DFD4'); ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values(): s.set_visible(False)
    ax.plot([-4.6, -3.6], [-2.9, -2.9], color=INK, lw=1.5); ax.text(-4.1, -2.75, '1 м', ha='center', color=INK, family=MONO, fontsize=8)
def frame4(out, prog=1.0, W=1920, H=1080):
    S = st('u00'); S2 = dict(S); S2['ceiling'] = []
    fig = plt.figure(figsize=(W / 100, H / 100), dpi=100, facecolor=PAPER)
    left(fig, S, 4)
    ax = fig.add_axes([0.25, 0.04, 0.53, 0.92]); ax.axis('off')
    draw_model(ax, S2); draw_perf(ax, prog)
    for c in S['ribs']:
        q, _ = iso(np.array(c)); ax.plot(q[:, 0], q[:, 1], color='#8E3B2C', lw=1.3, zorder=7)
    ax.set_xlim(*LIM[0]); ax.set_ylim(*LIM[1]); ax.set_aspect('equal')
    ap = fig.add_axes([0.80, 0.45, 0.17, 0.45]); ap.axis('off'); plan_perf(ap, prog); ap.set_xlim(-27, 19); ap.set_ylim(-17, 19.5); ap.set_aspect('equal')
    fig.text(0.80, 0.905, 'ПОТОЛОК · ПРОЕКЦИЯ НА ПЛАН', color=GREY, family=MONO, fontsize=9.5)
    fig.add_artist(plt.Line2D([0.80, 0.97], [0.43, 0.43], color=LIGHT, lw=0.8))
    fig.text(0.80, 0.375, 'ОДНО ПЯТНО · В ПЛОСКОСТИ ПОЛОСЫ', color=GREY, family=MONO, fontsize=9.5)
    ac = fig.add_axes([0.80, 0.10, 0.17, 0.25]); closeup(ac)
    n = int(round(NH * prog))
    fig.text(0.80, 0.07, f'{NH} отверстий · Ø 40–240 мм', color=INK, family=SANS, fontsize=11)
    fig.savefig(out, dpi=100, facecolor=PAPER); plt.close(fig)
if __name__ == '__main__':
    frame4(sys.argv[1], float(sys.argv[2]) if len(sys.argv) > 2 else 1.0)
