import sys, os, shutil
from multiprocessing import Pool
from frame import *
import perforation
seq = []
def hold(tag, ch, n, hl=None): seq.extend([(tag, ch, hl)] * n)
def run(tags, ch, n, hl=None):
    for t in tags: seq.extend([(t, ch, hl)] * n)
c1 = [f'u{i:02d}' for i in [1,2,3,4,5,6]]
c1u = [f'u{i:02d}' for i in [5,4,3,2,1,0,7,8,9,10,11,12,13,14,15,16]]
c1d = [f'u{i:02d}' for i in [15,14,13,12,11,10,9,8,7,0]]
hold('u00', 1, 30, 'walls'); run(c1, 1, 3, 'walls'); hold('u06', 1, 14, 'walls'); run(c1u, 1, 3, 'walls'); hold('u16', 1, 14, 'walls'); run(c1d, 1, 3, 'walls'); hold('u00', 1, 12, 'walls')
hold('u17', 2, 25, 'ribs'); run([f'u{i:02d}' for i in range(18, 37)], 2, 4, 'ribs'); hold('u17', 2, 14, 'ribs')
hold('u00', 3, 25); run(['u37', 'u38', 'u39'], 3, 8); hold('u39', 3, 10); run(['u38', 'u37', 'u00', 'u40', 'u41', 'u42'], 3, 8); hold('u42', 3, 10); run(['u41', 'u40', 'u00'], 3, 8); hold('u00', 3, 25)
for i in range(31): seq.extend([('P%02d' % i, 4, None)] * 2)
hold('P30', 4, 50)
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
uniq = {}
for i, s in enumerate(seq): uniq.setdefault(s, []).append(i)
def job(item):
    (tag, ch, hl), idx = item
    p = os.path.join(OUT, f'k_{tag}_{ch}_{hl}.png')
    if not os.path.exists(p):
        if ch == 4: perforation.frame4(p, int(tag[1:]) / 30.0)
        else: frame(st(tag), ch, p, hl=hl)
    return p, idx
if __name__ == '__main__':
    with Pool(2) as P: res = P.map(job, list(uniq.items()))
    for p, idx in res:
        for i in idx:
            d = os.path.join(OUT, f'f{i:04d}.png')
            if os.path.lexists(d): os.remove(d)
            try: os.symlink(os.path.abspath(p), d)
            except (OSError, NotImplementedError): shutil.copyfile(p, d)  # Windows without symlink rights
    print(len(seq), 'frames', len(uniq), 'unique')
