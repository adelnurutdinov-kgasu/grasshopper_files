import sys, os, collections, copy, uuid, struct, json
HERE = os.path.dirname(os.path.abspath(__file__))
GH_IO = os.path.join(HERE, 'gh_io')
sys.path.insert(0, GH_IO)
import ghparse
exec(open(os.path.join(GH_IO, 'restruct.py')).read())
# Шаблон объекта «группа» (оформление групп Grasshopper) берётся из готовой схемы, где группы уже есть.
TEMPLATE = os.path.join(HERE, '..', '..', 'acoustic-rays', 'definition', 'physics_test11_blocks.gh')
def tidy(SRC, DST, assign, titles, colors, order, renames=None, cols=2, gap=260, pack=(), subof=None):
    D = Doc(SRC)
    T = Doc(TEMPLATE)
    GT = next(ob for ob in T.O if T.is_group(ob))
    OBJ = {D.guid(ob): ob for ob in D.O}
    D.objs['ch'] = [ob for ob in D.objs['ch'] if not (ob['n'] == 'Object' and D.is_group(ob))]
    OBJ = {g: ob for g, ob in OBJ.items() if not D.is_group(ob)}
    blocks = collections.defaultdict(list)
    for g in OBJ: blocks[assign(g)].append(g)
    def bbox(mem):
        bs = [D.bounds(OBJ[g]) for g in mem]
        return min(b[0] for b in bs), min(b[1] for b in bs), max(b[0] + b[2] for b in bs), max(b[1] + b[3] for b in bs)
    def translate(g, dx, dy):
        def walk(c):
            if c['n'] == 'Attributes':
                for x in c['items']:
                    if x[0] == 'Bounds':
                        r = x[4]; set_rectf(x, (r[0] + dx, r[1] + dy, r[2], r[3]))
                    if x[0] == 'Pivot':
                        p = x[4]; set_pointf(x, (p[0] + dx, p[1] + dy))
            for y in c['ch']: walk(y)
        walk(D.cont(OBJ[g]))
    # pack: stack sub-components of chosen blocks vertically
    for b in pack:
        if not blocks.get(b) or subof is None: continue
        subs = collections.defaultdict(list)
        for g in blocks[b]: subs[subof(g)].append(g)
        yy = 0
        for k, mem in sorted(subs.items(), key=lambda kv: -len(kv[1])):
            x0, y0, x1, y1 = bbox(mem)
            for g in mem: translate(g, -x0, yy - y0)
            yy += (y1 - y0) + 40
    # layout: rows of blocks, left to right
    y = 0
    for row in order:
        x = 0; hmax = 0
        for b in row:
            if not blocks.get(b): continue
            x0, y0, x1, y1 = bbox(blocks[b])
            for g in blocks[b]: translate(g, x - x0, y + 80 - y0)
            x += (x1 - x0) + gap; hmax = max(hmax, y1 - y0)
        y += hmax + gap + 80
    if renames:
        for g, nm in renames.items():
            gg = next(x for x in OBJ if x.startswith(g))
            for x in D.cont(OBJ[gg])['items']:
                if x[0] == 'NickName': set_str(x, nm)
    def new_group(name, ids, color, alpha=0x70):
        ob = copy.deepcopy(GT); c = sub(ob, 'Container')[0]; g = str(uuid.uuid4())
        for x in c['items']:
            if x[0] == 'NickName': set_str(x, name)
            if x[0] == 'InstanceGuid': setguid_item(x, g)
            if x[0] == 'Colour':
                r, gg, bb = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
                v = (alpha << 24) | (r << 16) | (gg << 8) | bb; x[3] = struct.pack('<I', v); x[4] = x[3].hex()
        c['items'] = [x for x in c['items'] if x[0] != 'ID']
        k = next(i for i, x in enumerate(c['items']) if x[0] == 'ID_Count')
        c['items'][k:k] = [['ID', i, 9, uuid.UUID(q).bytes_le, q] for i, q in enumerate(ids)]
        set_int([x for x in c['items'] if x[0] == 'ID_Count'][0], len(ids))
        return ob
    D.objs['ch'].extend(new_group(titles[b], m, colors[b]) for b, m in blocks.items() if m)
    objs = [x for x in D.objs['ch'] if x['n'] == 'Object']
    for i, ob in enumerate(objs): ob['i'] = i
    set_int([x for x in D.objs['items'] if x[0] == 'ObjectCount'][0], len(objs))
    open(DST, 'wb').write(ghparse.compress(ghparse.write(D.t)))
    return {b: len(m) for b, m in blocks.items()}
