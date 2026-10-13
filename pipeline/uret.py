"""Masal klasöründen videoyu baştan sona üretir (ses yoksa Edge TTS ile seslendirir).

Kullanım:
  python3 pipeline/uret.py masallar/002-ornek          # tek masal
  python3 pipeline/uret.py --bekleyenler               # meta.json'da durum == "yazildi" olanların hepsi
Ortam: PARCA (paralel render süreci sayısı, varsayılan CPU sayısı), URETILENLER (üretilen klasörlerin yazılacağı dosya)
"""
import glob, json, os, shutil, subprocess, sys, tempfile, time
from datetime import datetime, timezone, timedelta

PIPE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(PIPE)
TR = timezone(timedelta(hours=3))


def sh(cmd, **kw):
    print('$', ' '.join(map(str, cmd)), flush=True)
    subprocess.run(cmd, check=True, **kw)


def dur(path):
    return float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                                          '-of', 'csv=p=0', path]))


def meta_path(d):
    return os.path.join(d, 'meta.json')


def read_meta(d):
    p = meta_path(d)
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else {}


def write_meta(d, m):
    json.dump(m, open(meta_path(d), 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    open(meta_path(d), 'a').write('\n')


def build(d, test_seconds=None):
    d = os.path.abspath(d)
    t0 = time.time()
    if not os.path.exists(os.path.join(d, 'audio', 'part1.mp3')):
        sh([sys.executable, os.path.join(PIPE, 'sesle_edge.py'), d])
    work = tempfile.mkdtemp(prefix='masal_')
    shutil.copy(os.path.join(d, 'scenes.json'), work)
    os.symlink(os.path.join(d, 'audio'), os.path.join(work, 'audio'))
    env = dict(os.environ, PYTHONPATH=PIPE)
    plan = os.path.join(d, 'sahne_plani.json')
    if os.path.exists(plan):
        env['SAHNE_PLANI'] = plan
    bv = os.path.join(PIPE, 'build_video.py')
    sh([sys.executable, bv, 'plan'], cwd=work, env=env)
    sh([sys.executable, bv, 'audio'], cwd=work, env=env)
    n = int(os.environ.get('PARCA', os.cpu_count() or 2))
    if test_seconds:
        env['TEST_SANIYE'] = str(test_seconds)
    procs = [subprocess.Popen([sys.executable, bv, 'video', str(k), str(n)], cwd=work, env=env) for k in range(n)]
    for p in procs:
        if p.wait() != 0:
            raise SystemExit('video render başarısız')
    with open(os.path.join(work, 'out', 'list.txt'), 'w') as f:
        for k in range(n):
            if os.path.exists(os.path.join(work, 'out', f'v{k}.mp4')):
                f.write(f"file 'v{k}.mp4'\n")
    sh(['ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', 'out/list.txt', '-c', 'copy', 'out/vid.mp4'],
       cwd=work)
    out = os.path.join(d, 'video.mp4')
    for crf in (27, 30, 33):
        sh(['ffmpeg', '-y', '-v', 'error', '-i', 'out/vid.mp4', '-i', 'out/audio.m4a', '-map', '0:v', '-map', '1:a',
            '-c:v', 'libx264', '-preset', 'medium', '-tune', 'animation', '-crf', str(crf), '-pix_fmt', 'yuv420p',
            '-c:a', 'aac', '-b:a', '96k', '-shortest', '-movflags', '+faststart', out], cwd=work)
        if os.path.getsize(out) < 30 * 1024 * 1024:
            break
    sh(['ffmpeg', '-y', '-v', 'error', '-ss', '3.5', '-i', out, '-frames:v', '1', '-vf', 'scale=1280:-2', '-q:v', '3',
        os.path.join(d, 'onizleme.jpg')])
    m = read_meta(d)
    sec = dur(out)
    m.update(durum='video_hazir', sure=f'{int(sec // 60)}:{int(sec % 60):02d}',
             ses=m.get('ses') or ('ElevenLabs' if not os.path.exists(os.path.join(d, 'audio', 'segments.json'))
                                  else 'Edge TTS ' + os.environ.get('TTS_SES', 'tr-TR-EmelNeural')),
             video_uretim=datetime.now(TR).isoformat(timespec='minutes'))
    write_meta(d, m)
    shutil.rmtree(work, ignore_errors=True)
    print(f'TAMAM {d} süre={m["sure"]} boyut={os.path.getsize(out) / 1e6:.1f}MB '
          f'üretim={int(time.time() - t0)}s', flush=True)
    lst = os.environ.get('URETILENLER')
    if lst:
        open(lst, 'a').write(os.path.relpath(d, ROOT) + '\n')


def pending():
    out = []
    for p in sorted(glob.glob(os.path.join(ROOT, 'masallar', '*', 'meta.json'))):
        m = json.load(open(p, encoding='utf-8'))
        if m.get('durum') == 'yazildi':
            out.append(os.path.dirname(p))
    return out


if __name__ == '__main__':
    args = sys.argv[1:]
    if args and args[0] == '--bekleyenler':
        ds = pending()
        print('bekleyen masallar:', [os.path.basename(x) for x in ds], flush=True)
        for d in ds:
            build(d)
    else:
        build(args[0])
