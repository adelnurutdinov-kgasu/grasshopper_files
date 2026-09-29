import os, sys, subprocess, shutil, json
HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
sys.path.insert(0, HERE)
import render, anim, anim2
from multiprocessing import Pool

OUT = os.path.join(HERE, 'out')
FPS = render.LAY.get('fps', 25)


def encode(frames, name):
    src = os.path.join(frames, '%04d.png')
    base = os.path.join(OUT, name)
    run = lambda *a: subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', src, *a], check=True)
    run('-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-preset', 'slow', '-movflags', '+faststart', base + '.mp4')
    run('-c:v', 'libvpx-vp9', '-pix_fmt', 'yuv420p', '-crf', '30', '-b:v', '0', '-row-mt', '1', base + '.webm')
    run('-vf', 'scale=1280:-1:flags=lanczos', '-c:v', 'libwebp_anim', '-lossless', '0', '-q:v', '80', '-loop', '0', base + '.webp')


def j1(a):
    i, (p, g) = a
    render.frame(anim.M, f'frames/sborka/{i:04d}.png', p, g)


def j2(a):
    i, r = a
    anim2.frame(r, f'frames/naklon/{i:04d}.png')


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    for d in ('frames/sborka', 'frames/naklon'):
        shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
    what = sys.argv[1:] or ['stills', 'sborka', 'naklon']
    if 'stills' in what:
        for ext in ('png', 'svg'):
            render.frame(anim.M, os.path.join(OUT, f'лучи_лист.{ext}'))
            for t in (anim2.TMIN, 0, anim2.TMAX):
                anim2.frame(t, os.path.join(OUT, f'экран_{t:+d}.{ext}'.replace('+0', '0')))
    with Pool(os.cpu_count()) as P:
        if 'sborka' in what:
            P.map(j1, list(enumerate(anim.seq))); encode('frames/sborka', 'лучи_сборка')
        if 'naklon' in what:
            P.map(j2, list(enumerate(anim2.SEQ))); encode('frames/naklon', 'экран_наклон')
    print('готово:', sorted(os.listdir(OUT)))
