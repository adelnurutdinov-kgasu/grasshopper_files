import sys, os, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from tidy_gen import tidy, GH_IO  # tidy_gen подключает gh_io
exec(open(os.path.join(GH_IO, 'restruct.py')).read())
# python tidy_hall.py ../definition/original/theatre_hall.gh out.gh
SRC, DST = sys.argv[1], sys.argv[2]
D = Doc(SRC)
OBJ = {D.guid(ob): ob for ob in D.O if not D.is_group(ob)}
adj = collections.defaultdict(set)
for sp, c, ob in D.edges():
    so = D.owner.get(sp); do = D.guid(ob)
    if so and so != do: adj[so].add(do); adj[do].add(so)
seen = set(); comp = {}
for g in OBJ:
    if g in seen: continue
    st = [g]; cc = []
    while st:
        x = st.pop()
        if x in seen: continue
        seen.add(x); cc.append(x); st += list(adj[x])
    for x in cc: comp[x] = cc
KEY = {  # member guid prefix -> block
 '4f2a7a59': 'RIBS', '74753ab0': 'WALLS', 'ead2bece': 'SEAT1', '521ebb6c': 'SEAT2', 'e1446640': 'CHAIR', '60ebcf7f': 'CHAIR',
 '7eee8799': 'VOL', 'cb64cd31': 'VOL', '29b7a482': 'VOL', '9f8557d7': 'VOL', 'ad3546e3': 'VOL', 'e28c063d': 'VOL', 'bd823319': 'VOL',
 '216d1e1b': 'VOL', '80097b8e': 'VOL', 'd5220d08': 'VOL', 'fe453a0a': 'VOL', 'd239ceaf': 'VOL', '025e8d6d': 'VOL',
 'a1a1265d': 'ROOF', 'd6ad398a': 'ROOF', '64131f49': 'ROOF', 'bb1e4507': 'ROOF', '55e02c13': 'ROOF',
 '33ec170e': 'OUT',
 '84ea66ce': 'TEST', 'a640c8fa': 'TEST', '69fbd18d': 'TEST',
}
M = {}
for k, b in KEY.items():
    g = next(x for x in OBJ if x.startswith(k))
    for x in comp[g]: M[x] = b
T = {'RIBS': '1 · РЁБРА ПОТОЛКА: 2 опорные дуги > Tween ×5 (+1) > проекция на SubD потолка · 6 ползунков',
     'WALLS': '2 · СТЕНЫ, ПОЛ, ПРОХОДЫ · кривые Rhino (Join > Offset > Boundary > Extrude)',
     'SEAT1': '3 · РАССАДКА: ПАРТЕР (кластер: ряд − 0,5 м с концов, место 0,56 м)',
     'SEAT2': '4 · РАССАДКА: БАЛКОН (тот же кластер)',
     'CHAIR': '5 · КРЕСЛО-ЭТАЛОН (сетка, зеркало)',
     'VOL': '6 · ОБЪЁМЫ В ЗАЛЕ: балкон, галереи, порталы (Sweep / Extrude по кривым Rhino)',
     'ROOF': '7 · НАД ПОТОЛКОМ И КРОВЛЯ',
     'OUT': '8 · ВНЕ ЗАЛА: навес / фойе (Loft с ошибкой)',
     'TEST': 'ТЕСТЫ: Tween по шагу, линии между кривыми (ссылки частично потеряны)',
     'X': 'НЕ ПОДКЛЮЧЕНО / ПУСТЫЕ ССЫЛКИ'}
C = {'RIBS': '#FFB38A', 'WALLS': '#9FD3FF', 'SEAT1': '#B8E6A8', 'SEAT2': '#B8E6A8', 'CHAIR': '#F5B7E0', 'VOL': '#FFE08A', 'ROOF': '#FFE08A', 'OUT': '#DDDDDD', 'TEST': '#DDDDDD', 'X': '#DDDDDD'}
R = {'40dd1ac8': 'ребро 1 · фактор', '9ad8e9dd': 'ребро 2 · фактор', '03c820c6': 'ребро 3 · фактор', '5c8bb681': 'ребро 4 · фактор',
     '4654d70d': 'ребро 5 · фактор', '4f2a7a59': 'ребро 6 (за дугой) · фактор', 'ddb6c9de': 'подъём копии рёбер, м'}
print(tidy(SRC, DST, lambda g: M.get(g, 'X'), T, C, [['RIBS', 'WALLS', 'SEAT1', 'SEAT2', 'CHAIR'], ['VOL', 'ROOF', 'TEST', 'X'], ['OUT']], R, pack=('VOL', 'ROOF', 'TEST', 'X'), subof=lambda g: comp[g][0]))
