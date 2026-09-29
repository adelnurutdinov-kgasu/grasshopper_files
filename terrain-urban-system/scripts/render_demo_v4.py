import json, math, sys, os, subprocess
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT/'python_packages'))

D = json.loads((ROOT/'geometry_v4.json').read_text())
W,H=1920,1080
PAPER=(247,248,244); INK=(30,45,43); MUTED=(112,132,123); ACC=(187,97,75)
COLORS=[(192,84,66),(215,151,73),(184,164,63),(49,141,139)]
FONT='C:/Windows/Fonts/arial.ttf'; BOLD='C:/Windows/Fonts/arialbd.ttf'
MONO='C:/Windows/Fonts/consola.ttf'
fonts={}
def ft(size,bold=False,mono=False):
    k=(size,bold,mono)
    if k not in fonts: fonts[k]=ImageFont.truetype(MONO if mono else BOLD if bold else FONT,size)
    return fonts[k]
def text(im,xy,s,size=26,color=INK,bold=False,mono=False):
    ImageDraw.Draw(im).text(xy,s,font=ft(size,bold,mono),fill=color)
def project(p):
    p=np.asarray(p,float);x=p[:,0]-150;y=p[:,1]-150;z=p[:,2]
    return np.c_[1235+2.86*(.7071*x+.7071*y),590+2.86*(.4056*x-.4056*y-.8192*z)]
def depth(p):
    p=np.asarray(p);return np.mean(.5792*p[:,0]-.5792*p[:,1]+.5736*p[:,2])
def shade(p,base):
    n=np.cross(p[1]-p[0],p[2]-p[0]);n/=np.linalg.norm(n)+1e-9
    if n[2]<0:n=-n
    f=.76+.24*max(0,float(n@np.array([-.35,-.4,.846])))
    return tuple(int(min(255,c*f)) for c in base)
V=np.array(D['terrain']['v']);F=D['terrain']['f']
def triangles(v,faces):
    return [v[np.array(q)] for f in faces for q in ([f[:3],[f[0],f[2],f[3]]] if len(f)==4 else [f])]
TRI=triangles(V,F)
contours=[np.array(p) for p in D['contours']]
grid=V.reshape(41,41,3)
# Grasshopper surface parameter directions can run in either XY order.
if abs(grid[1,0,0]-grid[0,0,0])<abs(grid[0,1,0]-grid[0,0,0]):grid=grid.transpose(1,0,2)
def height(x,y):
    u=np.clip((x-grid[0,0,0])/(grid[-1,0,0]-grid[0,0,0])*40,0,39.999)
    v=np.clip((y-grid[0,0,1])/(grid[0,-1,1]-grid[0,0,1])*40,0,39.999)
    i,j=int(u),int(v);a,b=u-i,v-j
    return (1-a)*(1-b)*grid[i,j,2]+a*(1-b)*grid[i+1,j,2]+(1-a)*b*grid[i,j+1,2]+a*b*grid[i+1,j+1,2]
terrain=[]
for p in TRI:
    z=p[:,2].mean()/50
    base=np.array([233,235,227])*(1-z)+np.array([174,194,183])*z
    terrain.append((depth(p),project(p),shade(p,base)))
terrain.sort(key=lambda q:q[0])
rawv=np.array(D['input_mesh']['v'])
raw=[]
for p in triangles(rawv,D['input_mesh']['f']):raw.append((depth(p),project(p),shade(p,[218,229,221])))
raw.sort(key=lambda q:q[0])
def clip_high(p,h):
    r=[]
    for a,b in zip(p,np.roll(p,-1,axis=0)):
        ai=a[2]>=h;bi=b[2]>=h
        if ai:r.append(a.copy())
        if ai!=bi:r.append(a+(b-a)*(h-a[2])/(b[2]-a[2]))
    return np.array(r)
layers=[]
for h in range(2,50,2):
    faces=[]
    for p in TRI:
        q=clip_high(p,h)
        if len(q)<3:continue
        top=q.copy();top[:,2]=h
        faces.append((top,(233-int(h*.35),237-int(h*.28),226-int(h*.34))))
        cut=q[np.abs(q[:,2]-h)<1e-7]
        if len(cut)==2 and np.linalg.norm(cut[0]-cut[1])>.001:
            a,b=cut
            wall=np.array([a,b,b-[0,0,2],a-[0,0,2]])
            faces.append((wall,(167,187,174)))
        if h>2:
            for a,b in zip(q,np.roll(q,-1,axis=0)):
                edge=any(abs(a[k]-v)<.06 and abs(b[k]-v)<.06 for k in [0,1] for v in [0,300])
                if edge:
                    aa=a.copy();bb=b.copy();aa[2]=bb[2]=h
                    faces.append((np.array([aa,bb,bb-[0,0,2],aa-[0,0,2]]),(167,187,174)))
    # Boundary of the first solid layer.
    if h==2:
        for a,b in zip([(0,0),(300,0),(300,300),(0,300)],[(300,0),(300,300),(0,300),(0,0)]):
            faces.append((np.array([[*a,2],[*b,2],[*b,0],[*a,0]],float),(167,187,174)))
    layers.append(faces)

# Appended to the shared geometry-rendering helpers by prepare_render_v3.py.
from functools import lru_cache
PAPER=(247,248,244)
base=Image.new('RGB',(W,H),PAPER)
dr=ImageDraw.Draw(base)
dr.line((65,130,1855,130),fill=(211,219,211),width=2)
dr.line((65,965,1855,965),fill=(211,219,211),width=2)
text(base,(66,52),'РЕЛЬЕФ / ГОРОДСКАЯ СРЕДА',23,ACC,mono=True)
text(base,(1460,53),'RHINO + GRASSHOPPER',20,MUTED,mono=True)
text(base,(66,998),'Параметрическая система · демонстрационный участок',22,MUTED)
text(base,(1450,998),'300 × 300 м  /  Z × 1',20,MUTED,mono=True)
titles=[('Исходная','поверхность'),('Рельеф','по слоям'),('Четыре линии.','Дорожная сеть.'),('Полосы','озеленения'),('Посадки','по рельефу'),('Объёмы','на участке'),('Меняем','трассу'),('Расширяем','дорогу'),('Настраиваем','озеленение'),('Одна схема.','Связанная среда.')]
subs=[['Мэш задаёт форму участка.','Из него восстанавливается','рабочая поверхность.'],['Горизонтальные сечения','с шагом 2 м.','Ракурс и масштаб постоянны.'],['Оси появляются по одной.','Цвет определяет ширину.','Пересечения собираются в сеть.'],['Общая пешеходная основа.','На ней — зелёные полосы.','Покрытия следуют рельефу.'],['Точки делят линии посадки.','Три условных типа деревьев,','вариации масштаба и поворота.'],['Тестовые объёмы в кварталах.','Исходный кластер размещает','их по высоте поверхности.'],['Двигаем главную ось.','Кварталы, полосы и посадки','перестраиваются вместе.'],['Ширина меняется: 14 → 24 м.','Озеленение отступает от края.','Перекрёстки остаются связными.'],['Ширина зелёных полос','меняется: 3,2 → 5,2 м.','Поверхности пересчитываются.'],['Рельеф → сеть → кварталы.','Озеленение → посадки → объёмы.','Каждое состояние рассчитано в GH.']]

def ease(t):
    t=max(0,min(1,t));return t*t*(3-2*t)
def draw_poly(dr,pts,col,outline=None):
    xy=[tuple(p) for p in pts];dr.polygon(xy,fill=col)
    if outline:dr.line(xy+[xy[0]],fill=outline,width=1)
def meshfaces(m,col,offset=0,tag=-1):
    result=[];v=np.array(m['v']);v[:,2]+=offset
    for p in triangles(v,m['f']):result.append((depth(p),project(p),shade(p,col),tag))
    return result
terrainfaces=[(d,p,c,-1) for d,p,c in terrain]

@lru_cache(maxsize=8)
def geometry(k):
    s=D['states'][k];roads=[];greens=[];buildings=[];trees=[]
    for m in s['roads']:roads+=meshfaces(m,(60,82,89),.08)
    for m in s['greens']:greens+=meshfaces(m,(128,170,114),.14)
    for m in s.get('buildings',D['buildings']):buildings+=meshfaces(m,(224,215,191),.1)
    for i,(species,scale,angle,x,y,z) in enumerate(s['tree_records']):
        model=D['templates'][int(species)];v=np.array(model['v'])*scale
        xx=v[:,0].copy();yy=v[:,1].copy();v[:,0]=xx*math.cos(angle)-yy*math.sin(angle);v[:,1]=xx*math.sin(angle)+yy*math.cos(angle);v+=np.array([x,y,z+.17])
        # Geometry and placement records are exported from the running GH component.
        for face in model['f']:
            p=v[np.array(face)];local=np.array(model['v'])[np.array(face)]
            col=(107,96,71) if max(local[:,2])<=4.01 and max(np.linalg.norm(local[:,:2],axis=1))<.4 else [(55,111,83),(71,118,91),(93,139,92)][int(species)]
            trees.append((depth(p),project(p),shade(p,col),i))
    return roads,greens,buildings,trees

@lru_cache(maxsize=8)
def pedestrian_faces(k):
    fs=[]
    for m in D['states'][k].get('pedestrians',[]):fs+=meshfaces(m,(194,197,194),.03)
    return fs

def plate(kind):
    im=base.copy();dr=ImageDraw.Draw(im)
    draw_poly(dr,project([[0,0,-3],[300,0,-3],[300,300,-3],[0,300,-3]]),(219,226,218))
    if kind=='layers':
        for layer in layers:
            fs=sorted([(depth(p),project(p),c) for p,c in layer],key=lambda a:a[0])
            for _,p,c in fs:draw_poly(dr,p,c)
    else:
        for _,p,c in raw if kind=='raw' else terrain:draw_poly(dr,p,c,(166,184,175) if kind=='raw' else None)
    return im
plates={k:plate(k) for k in ['raw','smooth','layers']}

def axis_points(xy,t):
    a,b=np.array(xy[0]),np.array(xy[-1]);r=[]
    for s in np.linspace(0,t,max(2,int(100*t))):
        x,y=a+(b-a)*s;r.append([x,y,height(x,y)+.25])
    return project(r)

@lru_cache(maxsize=16)
def full_scene(k,green=True,trees=True,buildings=True):
    im=plates['layers'].copy();dr=ImageDraw.Draw(im)
    roads,gs,bs,ts=geometry(k)
    for fs in [pedestrian_faces(k),roads,gs if green else [],(bs if buildings else [])+(ts if trees else [])]:
        for _,p,c,_ in sorted(fs,key=lambda a:a[0]):draw_poly(dr,p,c)
    return im

def panel(im,stage,k,p):
    dr=ImageDraw.Draw(im);s=D['states'][k]
    text(im,(66,177),f'{stage+1:02d} / 10',23,ACC,mono=True)
    for i,t in enumerate(titles[stage]):text(im,(65,237+i*64),t,47,bold=True)
    for i,t in enumerate(subs[stage]):text(im,(69,416+i*34),t,24,MUTED)
    if stage==0:
        text(im,(69,605),'300 × 300',49,bold=True);text(im,(72,680),'МЕТРОВ · УЧЕБНЫЙ УЧАСТОК',18,MUTED,mono=True)
    elif stage==1:
        text(im,(68,588),'2 м',79,bold=True);text(im,(73,686),'ШАГ СЕЧЕНИЙ',20,MUTED,mono=True)
    elif stage==2:
        q=min(4,max(0,p*4.6))
        for i,(name,w) in enumerate([('улица',8),('поперечная связь',7),('главная ось',14),('местная улица',10)]):
            col=COLORS[i] if q>i else (204,213,205);y=577+i*58
            dr.rounded_rectangle((70,y+5,92,y+27),radius=5,fill=col);text(im,(110,y),name,23);text(im,(384,y),str(w)+' м',23,mono=True)
    else:
        metric=f"{len(s['greens'])}" if stage==3 else f"{len(s['tree_records'])}" if stage==4 else '9' if stage==5 else f"{s['width']:.0f} м" if stage==7 else f"{2*s['green_width_control']:.1f} м".replace('.',',') if stage==8 else f"{len(s['greens'])} / {len(s['tree_records'])}"
        label='ПОЛОСЫ НА ПОВЕРХНОСТИ' if stage==3 else 'ДЕРЕВЬЕВ · 3 ТИПА' if stage==4 else 'ОБЪЁМОВ ПО ВЫСОТЕ РЕЛЬЕФА' if stage==5 else 'ШИРИНА ГЛАВНОЙ ДОРОГИ' if stage==7 else 'ШИРИНА ЗЕЛЁНОЙ ПОЛОСЫ' if stage==8 else 'ПОЛОСЫ / ДЕРЕВЬЯ'
        text(im,(69,551),metric,52,bold=True);text(im,(72,616),label,17,MUTED,mono=True)
        # A plan inset makes offsets, intersections and the moving route legible.
        ox,oy,sc=75,670,.77
        dr.rounded_rectangle((ox-9,oy-8,ox+250,oy+245),radius=10,fill=(234,239,232))
        def pt(v):return (ox+v[0]*sc,oy+235-v[1]*sc)
        for key,col in [('pedestrians',(194,197,194)),('roads',(74,98,103)),('greens',(133,174,118))]:
            for m in s.get(key,[]):
                for f in m['f']:dr.polygon([pt(m['v'][i]) for i in f],fill=col)
        if stage>=5:
            for m in s.get('buildings',D['buildings']):
                for f in m['f']:dr.polygon([pt(m['v'][i]) for i in f],fill=(193,182,158))
        if stage>=4:
            for _,_,_,x,y,z in s['tree_records']:
                x,y=pt((x,y,z));dr.ellipse((x-1.5,y-1.5,x+1.5,y+1.5),fill=(47,104,75))
        text(im,(347,694),'ПЛАН',16,MUTED,mono=True)
        text(im,(347,731),f"{s['blocks']:02d}",32,bold=True);text(im,(347,771),'кварталов',16,MUTED)
        text(im,(347,814),f"{s['green_area']/1000:.1f}".replace('.',','),32,bold=True);text(im,(347,856),'тыс. м² зелени',15,MUTED)
    for i in range(10):
        x=69+i*40;dr.rounded_rectangle((x,939,x+28,944),radius=2,fill=ACC if i<=stage else (213,219,213))

def scene(stage,k=0,p=1):
    if stage==0:im=plates['raw'].copy()
    elif stage==1:
        cut=625+ease(p)*1235
        mask=np.clip((cut-np.arange(W)+22)/44,0,1);mask=Image.fromarray(np.tile((255*mask).astype('uint8'),(H,1)))
        im=Image.composite(plates['layers'],plates['raw'],mask)
    elif stage==2:
        q=min(4,max(0,p*4.6));a=ease((p-.86)/.14)
        im=Image.blend(plates['layers'],full_scene(0,False,False,False),a)
        dr=ImageDraw.Draw(im)
        for i,xy in enumerate(D['states'][0]['axes']):
            t=ease(min(1,max(0,(q-i)*1.25)))
            if t:dr.line([tuple(t) for t in axis_points(xy,t)],fill=COLORS[i],width=5)
    elif stage==3:im=Image.blend(full_scene(k,False,False,False),full_scene(k,True,False,False),ease(p))
    elif stage==4:
        im=plates['layers'].copy();dr=ImageDraw.Draw(im)
        roads,gs,bs,ts=geometry(k);n=int(ease(p)*len(D['states'][k]['tree_records']))
        for fs in [pedestrian_faces(k),roads,gs,[f for f in ts if f[3]<n]]:
            for _,xy,col,_ in sorted(fs,key=lambda a:a[0]):draw_poly(dr,xy,col)
    elif stage==5:im=Image.blend(full_scene(k,True,True,False),full_scene(k),ease(p))
    else:im=full_scene(k).copy()
    panel(im,stage,k,p);return im

def build(preview=False):
    out=ROOT/'portfolio'/'v4';out.mkdir(parents=True,exist_ok=True)
    n=len(D['states']);last=n-1
    samples=[(0,0,1),(1,0,1),(2,0,.42),(2,0,1),(3,0,1),(4,0,1),(5,0,1),(6,min(32,last),1),(7,min(56,last),1),(8,last,1),(9,last,1)]
    for i,args in enumerate(samples):scene(*args).save(out/f'check_{i+1:02d}.png')
    scene(9,last).save(out/'relief_demo_poster.png')
    if preview:return
    import imageio_ffmpeg
    fps=24;timeline=[]
    for stage,duration in [(0,2.5),(1,3.5),(2,7),(3,3.5),(4,4),(5,3),(6,4),(7,4),(8,3.5),(9,4)]:
        frames=int(duration*fps)
        for i in range(frames):
            t=i/max(1,frames-1);p=min(1,max(0,(t-.1)/.75));k=0
            if stage==6:k=round(ease(t)*32)
            elif stage==7:k=32+round(ease(t)*24)
            elif stage==8:k=56+round(ease(t)*16)
            elif stage==9:k=72
            timeline.append((stage,min(k,last),p))
    ff=imageio_ffmpeg.get_ffmpeg_exe()
    cmd=[ff,'-y','-f','rawvideo','-vcodec','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(fps),'-i','-','-an','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(out/'relief_demo_v4.mp4')]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=(out/'encode.log').open('wb'))
    old=None;previous=None;from_img=None;start=0
    for idx,args in enumerate(timeline):
        im=scene(*args)
        if old!=args[0]:from_img=previous;start=idx;old=args[0]
        transition=(idx-start)/10
        if from_img is not None and transition<1:im=Image.blend(from_img,im,ease(transition))
        proc.stdin.write(im.tobytes());previous=im
        if idx%48==0:print(f'frame {idx}/{len(timeline)}',flush=True)
    proc.stdin.close();assert proc.wait()==0
    subprocess.run([ff,'-y','-i',str(out/'relief_demo_v4.mp4'),'-filter_complex','fps=12,scale=1080:-2:flags=lanczos,split[a][b];[a]palettegen=max_colors=192[p];[b][p]paletteuse=dither=bayer:bayer_scale=3','-loop','0',str(out/'relief_demo_v4.gif')],check=True,stdout=subprocess.DEVNULL,stderr=(out/'gif_encode.log').open('wb'))
    print('DONE',flush=True)
if __name__=='__main__':build('--preview' in sys.argv)


