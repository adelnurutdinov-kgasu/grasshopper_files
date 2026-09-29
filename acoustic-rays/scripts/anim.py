import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render
from multiprocessing import Pool
M = render.load(os.path.join(render.HERE, 'base.json'))
O = render.ORDER
seq = []
for k, g in enumerate(O):
    for f in range(16):
        t = (f + 1) / 16
        t = t * t * (3 - 2 * t)
        p = {h: 1.0 for h in O[:k]}; p[g] = t
        seq.append((p, g))
    for f in range(8):
        p = {h: 1.0 for h in O[:k + 1]}
        seq.append((p, g))
for f in range(40):
    seq.append(({h: 1.0 for h in O}, None))
def job(a):
    i, (p, g) = a
    render.frame(M, f'fr/{i:04d}.png', p, g)
if __name__ == '__main__':
    with Pool(8) as P:
        P.map(job, list(enumerate(seq)))
    print(len(seq))
