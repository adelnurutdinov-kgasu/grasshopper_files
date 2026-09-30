import sys, os
from frame import *
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
names = {'u06': 'width_28m', 'u00': 'base_33m', 'u16': 'width_42m', 'u32': 'ribs_shifted', 'u39': 'seat_0.50'}
for t, nm in names.items():
    S = st(t)
    fig = plt.figure(figsize=(10, 10)); ax = fig.add_axes([0, 0, 1, 1]); ax.axis('off')
    draw_model(ax, S); ax.set_xlim(*LIM[0]); ax.set_ylim(*LIM[1]); ax.set_aspect('equal')
    for ext in ('png', 'svg'): fig.savefig(os.path.join(OUT, f'axo_{nm}.{ext}'), transparent=True, dpi=150)
    plt.close(fig)
    fig = plt.figure(figsize=(6, 5)); ax = fig.add_axes([0, 0, 1, 1])
    draw_plan(ax, S); ax.set_xlim(-27, 19); ax.set_ylim(-17, 19.5)
    for ext in ('png', 'svg'): fig.savefig(os.path.join(OUT, f'plan_{nm}.{ext}'), transparent=True, dpi=200)
    plt.close(fig)
