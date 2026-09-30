import sys,collections,copy,uuid,struct
import ghparse  # tools/gh_io должен быть в sys.path (см. tools/tidy_*.py)
from ghparse import wstr
def getv(c,k):
    for x in c['items']:
        if x[0]==k: return x[4]
def items_of(c,k): return [x for x in c['items'] if x[0]==k]
def sub(c,k): return [x for x in c['ch'] if x['n']==k]
class Doc:
    def __init__(s,fn):
        s.t,_=ghparse.loadraw(open(fn,'rb').read())
        s.defn=s.t['ch'][0]
        s.objs=sub(s.defn,'DefinitionObjects')[0]
        s.reindex()
    def reindex(s):
        s.O=[]  # list of objects
        s.byg={}; s.owner={}; s.params={}
        for ob in s.objs['ch']:
            cont=sub(ob,'Container')[0]
            g=getv(cont,'InstanceGuid'); s.O.append(ob); s.byg[g]=ob; s.owner[g]=g
            def walk(c,top):
                pg=getv(c,'InstanceGuid')
                if pg and not top: s.owner[pg]=g; s.params[pg]=c
                for x in c['ch']: walk(x,False)
            walk(cont,True)
            s.params.setdefault(g,cont)
    def typ(s,ob): return getv(ob,'Name')
    def cont(s,ob): return sub(ob,'Container')[0]
    def guid(s,ob): return getv(s.cont(ob),'InstanceGuid')
    def is_group(s,ob): return bool(items_of(s.cont(ob),'ID'))
    def attrs(s,ob): 
        a=sub(s.cont(ob),'Attributes'); return a[0] if a else None
    def bounds(s,ob):
        a=s.attrs(ob); return getv(a,'Bounds') if a else None
    def all_source_holders(s):
        # every chunk holding Source items: (chunk, list of item refs)
        res=[]
        for ob in s.O:
            def walk(c):
                src=items_of(c,'Source')
                if src: res.append((ob,c))
                for x in c['ch']: walk(x)
            walk(s.cont(ob))
        return res
    def edges(s):
        E=[]
        for ob,c in s.all_source_holders():
            for x in items_of(c,'Source'):
                E.append((x[4],c,ob))   # source param guid, consumer chunk, consumer object
        return E
def setguid_item(itm,g):
    itm[3]=uuid.UUID(g).bytes_le; itm[4]=g
def set_int(itm,v): itm[3]=struct.pack('<i',v); itm[4]=v
def set_str(itm,v): itm[3]=wstr(v); itm[4]=v
def set_rectf(itm,r): itm[3]=struct.pack('<4f',*r); itm[4]=tuple(r)
def set_pointf(itm,p): itm[3]=struct.pack('<2f',*p); itm[4]=tuple(p)
def mk_item(name,idx,typ,raw,v): return [name,idx,typ,raw,v]
def set_sources(c,guids):
    # rewrite Source items (index 0..n-1) and SourceCount
    c['items']=[x for x in c['items'] if x[0]!='Source']
    new=[]
    for k,g in enumerate(guids):
        new.append(['Source',k,9,uuid.UUID(g).bytes_le,g])
    # insert keeping alphabetical-ish order: before SourceCount
    idx=next((k for k,x in enumerate(c['items']) if x[0]=='SourceCount'),len(c['items']))
    c['items'][idx:idx]=new
    sc=[x for x in c['items'] if x[0]=='SourceCount']
    if sc: set_int(sc[0],len(guids))
    else: c['items'].insert(idx+len(new),['SourceCount',-1,3,struct.pack('<i',len(guids)),len(guids)])
