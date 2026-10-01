#! python 3
# Скрипт для компонента Python 3 Script в definition/theatre_hall_blocks.gh.
# Читает theatre_states.json, по очереди применяет состояния (масштаб кривых Rhino по X,
# ширина места в обоих кластерах, ползунки рёбер) и после каждого пересчёта пишет theatre_st_<tag>.json.
# Счётчик хранится в scriptcontext.sticky['ti']; чтобы прогнать заново — удалить ключ 'ti'.
import Grasshopper as G, Rhino, json, System, os
import Rhino.Geometry as rg
import scriptcontext as sc
doc = ghenv.Component.OnPingDocument()
rd = Rhino.RhinoDoc.ActiveDoc
D = os.environ.get('THEATRE_DIR', r'C:\temp\theatre')  # папка с theatre_states.json; сюда же пишутся theatre_st_<tag>.json
CFG = json.load(open(os.path.join(D, 'theatre_states.json')))
STS = CFG['states']
if 'tsx' not in sc.sticky: sc.sticky['tsx'] = CFG['cur_sx']
if 'ti' not in sc.sticky: sc.sticky['ti'] = 0
MP = rg.MeshingParameters.FastRenderMesh
def byid(p): return [o for o in doc.Objects if str(o.InstanceGuid).startswith(p)][0]
def mesh(v):
    if isinstance(v, rg.Extrusion): v = v.ToBrep()
    if isinstance(v, rg.Surface): v = v.ToBrep()
    if isinstance(v, rg.SubD): v = rg.Mesh.CreateFromSubD(v, 2)
    if isinstance(v, rg.Mesh): m = v.DuplicateMesh()
    elif isinstance(v, rg.Brep):
        ms = rg.Mesh.CreateFromBrep(v, MP); m = rg.Mesh()
        for x in (ms or []): m.Append(x)
    else: return None
    m.Faces.ConvertQuadsToTriangles()
    return {'v': [[round(p.X,3),round(p.Y,3),round(p.Z,3)] for p in m.Vertices], 'f': [[f.A,f.B,f.C] for f in m.Faces]}
def crv(c, n=60):
    ts = c.DivideByCount(n, True) or []
    return [[round(c.PointAt(t).X,3), round(c.PointAt(t).Y,3), round(c.PointAt(t).Z,3)] for t in ts]
def outs(k, i=0):
    o = byid(k); return [getattr(g,'Value',None) for g in o.Params.Output[i].VolatileData.AllData(True)]
def refs(k):
    L = []
    for g in byid(k).PersistentData.AllData(True):
        ro = rd.Objects.FindId(g.ReferenceID)
        if ro: L.append(ro.Geometry)
    return L
def seat_params():
    L = []
    for ck in ('ead2bece', '521ebb6c'):
        cl = byid(ck); d = cl.Document('')
        dv = [o for o in d.Objects if str(o.InstanceGuid).startswith('8356')][0]
        L.append((ck, cl, d, dv.Params.Input[1]))
    return L
def sliders(): return {str(o.InstanceGuid)[:8]: o for o in doc.Objects if o.Name == 'Number Slider'}
def applied(st):
    if abs(sc.sticky['tsx'] - st['sx']) > 1e-9: return False
    for ck, cl, d, pb in seat_params():
        cur = [g.Value for g in pb.PersistentData.AllData(True)]
        if not cur or abs(cur[0] - st['seatw']) > 1e-9: return False
    S = sliders()
    for k, v in st['sl'].items():
        if abs(float(str(S[k].CurrentValue)) - v) > 1e-3: return False
    return True
def apply(st):
    def cb(gd):
        k = st['sx'] / sc.sticky['tsx']
        if abs(k - 1) > 1e-9:
            pl = rg.Plane(rg.Point3d(CFG['x0'], 0, 0), rg.Vector3d.ZAxis)
            T = rg.Transform.Scale(pl, k, 1.0, 1.0)
            for s in CFG['ids']: rd.Objects.Transform(System.Guid(s), T, True)
            sc.sticky['tsx'] = st['sx']
        for ck, cl, d, pb in seat_params():
            cur = [g.Value for g in pb.PersistentData.AllData(True)]
            if not cur or abs(cur[0] - st['seatw']) > 1e-9:
                pb.PersistentData.Clear(); pb.PersistentData.Append(G.Kernel.Types.GH_Number(st['seatw']))
                pb.ExpireSolution(False); cl.ExpireSolution(False)
        S = sliders()
        for kk, v in st['sl'].items():
            if abs(float(str(S[kk].CurrentValue)) - v) > 1e-4:
                S[kk].Slider.Value = System.Decimal(v); S[kk].ExpireSolution(False)
        ghenv.Component.ExpireSolution(False)
    doc.ScheduleSolution(20, G.Kernel.GH_Document.GH_ScheduleDelegate(cb))
def dump(st):
    S = {'tag': st['tag'], 'st': st}
    S['walls_h8'] = [mesh(v) for v in outs('b617e8d6')]
    S['walls_h12'] = [mesh(v) for v in outs('4617d3cf')]
    S['floor'] = [mesh(v) for v in outs('80114c4b')]
    S['wall_crv'] = [crv(c, 2) for c in refs('74753ab0')]
    S['ribs'] = [crv(c) for c in outs('cf818305') if isinstance(c, rg.Curve)]
    S['rib_guides'] = [crv(c) for c in refs('ede6b4c0')]
    S['ceiling'] = [mesh(v) for v in refs('1664ebd1')]
    for ck, cl, d, pb in seat_params():
        fr = [o for o in d.Objects if str(o.InstanceGuid).startswith('bccf')][0]
        frames = [g.Value for g in fr.Params.Output[0].VolatileData.AllData(True)]
        rc = [o for o in d.Objects if str(o.InstanceGuid).startswith('439f')][0].Params.Input[0].VolatileData.DataCount
        S[ck] = {'n': len(frames), 'rows': rc, 'w': [g.Value for g in pb.PersistentData.AllData(True)][0],
                 'f': [[round(p.Origin.X,3), round(p.Origin.Y,3), round(p.Origin.Z,3), round(p.XAxis.X,3), round(p.XAxis.Y,3), round(p.XAxis.Z,3)] for p in frames]}
    System.IO.File.WriteAllText(os.path.join(D, 'theatre_st_%s.json' % st['tag']), json.dumps(S))
    return S
i = sc.sticky['ti']
if i >= len(STS):
    out = 'done %d' % i
else:
    st = STS[i]
    if applied(st):
        S = dump(st)
        sc.sticky['ti'] = i + 1
        out = '%s ok %d+%d' % (st['tag'], S['ead2bece']['n'], S['521ebb6c']['n'])
        with open(os.path.join(D, 'theatre_log.txt'), 'a') as f: f.write(out + ' sx=%s w=%s\n' % (st['sx'], st['seatw']))
        if i + 1 < len(STS): apply(STS[i + 1])
    else:
        apply(st)
        out = 'applying %s' % st['tag']
