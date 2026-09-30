import zlib,struct,uuid
SZ={1:1,2:1,3:4,4:8,5:4,6:8,7:16,8:8,9:16,30:8,31:8,32:8,33:8,34:16,35:16,36:4,50:16,51:24,52:32,60:16,61:32,70:48,71:48,72:72,80:12}
class R:
    def __init__(s,b): s.b=b; s.p=0; s.types=[]
    def i32(s):
        v=struct.unpack_from('<i',s.b,s.p)[0]; s.p+=4; return v
    def s7(s):
        n=0;sh=0
        while True:
            c=s.b[s.p]; s.p+=1; n|=(c&0x7f)<<sh; sh+=7
            if c<128: break
        v=s.b[s.p:s.p+n].decode('utf8','replace'); s.p+=n; return v
    def val(s,t):
        b=s.b;p=s.p
        if t==10: return s.s7()
        if t in (20,37):
            n=s.i32(); v=b[s.p:s.p+n]; s.p+=n; return bytes(v)
        if t==21:
            n=s.i32(); v=struct.unpack_from('<%dd'%n,b,s.p); s.p+=8*n; return list(v)
        n=SZ[t]; raw=b[p:p+n]; s.p+=n
        if t==1: return raw[0]!=0
        if t==3: return struct.unpack('<i',raw)[0]
        if t in (4,8): return struct.unpack('<q',raw)[0]
        if t==5: return struct.unpack('<f',raw)[0]
        if t==6: return struct.unpack('<d',raw)[0]
        if t==9: return str(uuid.UUID(bytes_le=raw))
        if t in (31,33,35): return struct.unpack('<%df'%(n//4),raw)
        if t in (30,32,34,80): return struct.unpack('<%di'%(n//4),raw)
        if t==36: return raw.hex()
        return struct.unpack('<%dd'%(n//8),raw) if n%8==0 else raw.hex()
    def chunk(s):
        name=s.s7(); idx=s.i32(); ni=s.i32(); nc=s.i32()
        items=[]
        for _ in range(ni):
            iname=s.s7(); iidx=s.i32(); t=s.i32(); st=s.p; v=s.val(t); items.append((iname,iidx,v)); s.types.append((t,s.b[st:s.p]))
        ch=[s.chunk() for _ in range(nc)]
        return {'n':name,'i':idx,'items':items,'ch':ch}
def loadbytes(b):
    try: d=zlib.decompress(b,-15)
    except Exception: d=zlib.decompress(b)
    return R(d).chunk()
def load(fn): return loadbytes(open(fn,'rb').read())
def it(c,k,default=None):
    if c is None: return default
    for n,i,v in c['items']:
        if n==k: return v
    return default
def items(c,k): return [(i,v) for n,i,v in c['items'] if n==k]
def chs(c,k): return [x for x in c['ch'] if x['n']==k]
def ch(c,k):
    if c is None: return None
    l=chs(c,k); return l[0] if l else None

# lossless: parse into tree with raw item payloads
class RR(R):
    def chunk(s):
        name=s.s7(); idx=s.i32(); ni=s.i32(); nc=s.i32()
        its=[]
        for _ in range(ni):
            iname=s.s7(); iidx=s.i32(); t=s.i32(); st=s.p; v=s.val(t)
            its.append([iname,iidx,t,s.b[st:s.p],v])
        return {'n':name,'i':idx,'items':its,'ch':[s.chunk() for _ in range(nc)]}
def w7(n):
    out=bytearray()
    while True:
        c=n&0x7f; n>>=7
        if n: out.append(c|0x80)
        else: out.append(c); return bytes(out)
def wstr(x):
    b=x.encode('utf8'); return w7(len(b))+b
def write(c):
    out=[wstr(c['n']),struct.pack('<iii',c['i'],len(c['items']),len(c['ch']))]
    for iname,iidx,t,raw,v in c['items']:
        out.append(wstr(iname)+struct.pack('<ii',iidx,t)+raw)
    for x in c['ch']: out.append(write(x))
    return b''.join(out)
def loadraw(b):
    try: d=zlib.decompress(b,-15)
    except Exception: d=zlib.decompress(b)
    r=RR(d); t=r.chunk(); return t,d
def compress(d):
    co=zlib.compressobj(9,zlib.DEFLATED,-15); return co.compress(d)+co.flush()
