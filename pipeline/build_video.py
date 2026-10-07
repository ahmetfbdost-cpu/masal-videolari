"""Ses + sahneler + altyazı + müzik -> MP4."""
import json, re, subprocess, sys, math
import numpy as np
import render

SR = 44100
LEAD = 5.0      # açılışta müzikle başlık
PAD = 3.5       # sahne geçişlerinde nefes payı
END = 11.0      # kapanış kartı
FPS = render.FPS


def silences(path):
    out = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', path, '-af',
                          'silencedetect=noise=-40dB:d=1.4', '-f', 'null', '-'],
                         capture_output=True, text=True).stderr
    st = [float(x) for x in re.findall(r'silence_start: ([\d.]+)', out)]
    en = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', out)]
    return list(zip(st, en))


def duration(path):
    return float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                                          '-of', 'csv=p=0', path]))


def load(path):
    raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', path, '-ac', '1', '-ar', str(SR), '-f', 's16le', '-'])
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768


def chunks(text, maxlen=95):
    sents = re.findall(r'[^.!?…]+[.!?…]+["”]?|[^.!?…]+$', text)
    out, cur = [], ''
    for s in (x.strip() for x in sents if x.strip()):
        if cur and len(cur) + len(s) + 1 > maxlen:
            out.append(cur)
            cur = s
        else:
            cur = (cur + ' ' + s).strip()
    if cur:
        out.append(cur)
    return out


def plan():
    scenes_txt = json.load(open('scenes.json'))
    keys = ['title'] + list(range(1, 13))
    segs = []  # (key, audio_part, a, b, speech_a, speech_b, text)
    ti = 0
    for part, keylist in (('audio/part1.mp3', keys[:7]), ('audio/part2.mp3', keys[7:])):
        sil = silences(part)
        d = duration(part)
        cuts = [0] + [(s + e) / 2 for s, e in sil] + [d]
        assert len(cuts) - 1 == len(keylist), (part, len(cuts), keylist)
        for i, k in enumerate(keylist):
            sa = sil[i - 1][1] if i > 0 else 0.0
            sb = sil[i][0] if i < len(sil) else d
            segs.append((k, part, cuts[i], cuts[i + 1], sa, sb, None if k == 'title' else scenes_txt[k - 1]))
    # zaman çizelgesi
    tl, t = [], 0.0
    for i, (k, part, a, b, sa, sb, txt) in enumerate(segs):
        lead = LEAD if k == 'title' else 0.0
        dur = lead + (b - a) + PAD
        tl.append(dict(key=k, start=t, dur=dur, part=part, a=a, b=b, voice_at=t + lead,
                       speech=(t + lead + sa - a, t + lead + sb - a), text=txt))
        t += dur
    tl.append(dict(key='end', start=t, dur=END, text=None))
    total = t + END
    # altyazılar
    subs = []
    for s in tl:
        if not s['text']:
            continue
        cs = chunks(s['text'])
        s0, s1 = s['speech']
        L = sum(len(c) for c in cs)
        cur = s0
        for c in cs:
            dd = (s1 - s0) * len(c) / L
            subs.append((cur, cur + dd, c))
            cur += dd
    return tl, subs, total


def music(total, speech_spans):
    """Sakin, telifsiz ninni: müzik kutusu melodisi + yumuşak akorlar."""
    n = int(total * SR)
    out = np.zeros(n, np.float32)
    bpm = 66
    beat = 60 / bpm
    # Fa majör: F - Dm - Bb - C (3/4)
    chords = [[53, 57, 60], [50, 53, 57], [46, 50, 53], [48, 52, 55]]
    rng = np.random.default_rng(5)
    hz = lambda m: 440 * 2 ** ((m - 69) / 12)
    # 8 ölçülük melodi kalıbı (akor tonlarından, sabit)
    scale = [65, 67, 69, 72, 74, 77, 79, 81]
    phrase = []
    for bar in range(8):
        ch = chords[bar % 4]
        tones = sorted(set([c + 12 for c in ch] + [c + 24 for c in ch]))
        tones = [x for x in tones if 64 <= x <= 84]
        for b in range(3):
            if b == 1 and bar % 2 == 1:
                phrase.append(None)
            else:
                phrase.append(int(rng.choice(tones)))

    def note(f, dur, amp, decay, harm=(1, 0.35, 0.12)):
        m = int(dur * SR)
        tt = np.arange(m) / SR
        w = sum(a * np.sin(2 * np.pi * f * h * tt) for h, a in zip((1, 2, 3), harm))
        env = np.exp(-tt / decay) * np.minimum(1, tt / 0.005)
        return (w * env * amp).astype(np.float32)

    def pad(fs, dur, amp):
        m = int(dur * SR)
        tt = np.arange(m) / SR
        w = sum(np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * f * 2 * tt + 0.3) for f in fs)
        env = np.minimum(1, tt / 0.8) * np.minimum(1, (dur - tt) / 0.8)
        return (w * env * amp / len(fs)).astype(np.float32)

    bar_len = 3 * beat
    nbars = int(total / bar_len) + 1
    for bar in range(nbars):
        t0 = bar * bar_len
        ch = chords[bar % 4]
        p = pad([hz(m) for m in ch], bar_len + 0.6, 0.05)
        i0 = int(t0 * SR)
        out[i0:i0 + len(p)] += p[:max(0, n - i0)]
        bass = note(hz(ch[0] - 12), bar_len, 0.09, 1.2, (1, 0.2, 0))
        out[i0:i0 + len(bass)] += bass[:max(0, n - i0)]
        for b in range(3):
            m = phrase[(bar % 8) * 3 + b]
            if m is None:
                continue
            nt = note(hz(m), 2.2, 0.07, 0.6)
            j = int((t0 + b * beat) * SR)
            out[j:j + len(nt)] += nt[:max(0, n - j)]
    # basit yankı
    for dly, g in ((0.23, 0.3), (0.41, 0.18)):
        k = int(dly * SR)
        out[k:] += out[:-k] * g
    # konuşma sırasında kıs
    env = np.full(n, 1.0, np.float32)
    for a, b in speech_spans:
        i, j = int(a * SR), int(b * SR)
        env[i:j] = 0.32
    kern = np.ones(int(0.6 * SR)) / int(0.6 * SR)
    env = np.convolve(env, kern, mode='same').astype(np.float32)
    out *= env
    fade = int(3 * SR)
    out[-fade:] *= np.linspace(1, 0, fade)
    out[:int(1.5 * SR)] *= np.linspace(0, 1, int(1.5 * SR))
    return out / max(1e-6, np.abs(out).max()) * 0.5


def audio_mix(tl, total):
    n = int(total * SR)
    voice = np.zeros(n, np.float32)
    srcs = {}
    for p in ('audio/part1.mp3', 'audio/part2.mp3'):
        x = load(p)
        srcs[p] = x * (0.89 / max(1e-6, np.abs(x).max()))  # ses seviyesini normalize et
    spans = []
    for s in tl:
        if 'part' not in s:
            continue
        src = srcs[s['part']][int(s['a'] * SR):int(s['b'] * SR)]
        i = int(s['voice_at'] * SR)
        voice[i:i + len(src)] += src[:n - i]
        spans.append(s['speech'])
    mus = music(total, spans)
    mix = voice * 1.0 + mus * 0.55
    mix = np.clip(mix / max(1.0, np.abs(mix).max() / 0.97), -1, 1)
    pcm = (mix * 32767).astype(np.int16)
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 's16le', '-ar', str(SR), '-ac', '1', '-i', '-',
                    '-ac', '2', '-c:a', 'aac', '-b:a', '192k', 'out/audio.m4a'], input=pcm.tobytes(), check=True)


def render_range(tl, subs, total, f0, f1, outpath):
    r = render.Renderer()
    ff = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '1920x1080',
                           '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '20',
                           '-pix_fmt', 'yuv420p', outpath], stdin=subprocess.PIPE)
    si = 0
    for f in range(f0, f1):
        t = f / FPS
        s = next(x for x in reversed(tl) if x['start'] <= t)
        idx = tl.index(s)
        p = (t - s['start']) / s['dur']
        lt = t - s['start']
        fade = min(1.0, lt / 0.6, (s['dur'] - lt) / 0.6) if idx < len(tl) - 1 else min(1.0, lt / 0.6, (s['dur'] - lt) / 1.5)
        if idx == 0:
            fade = min(1.0, lt / 1.2, (s['dur'] - lt) / 0.6)
        sub = None
        for a, b, c in subs:
            if a <= t < b:
                sub = c
                break
        im = r.frame(s['key'], p, t, subs=sub, fade=fade, pan_dir=1 if idx % 2 == 0 else -1)
        ff.stdin.write(im.convert('RGB').tobytes())
    ff.stdin.close()
    ff.wait()


if __name__ == '__main__':
    import os
    os.makedirs('out', exist_ok=True)
    tl, subs, total = plan()
    nfr = int(total * FPS)
    if sys.argv[1] == 'plan':
        for s in tl:
            print(s['key'], round(s['start'], 1), round(s['dur'], 1))
        print('total', round(total, 1), 'frames', nfr, 'subs', len(subs))
        json.dump(dict(tl=tl, subs=subs, total=total), open('out/plan.json', 'w'), ensure_ascii=False, indent=1)
    elif sys.argv[1] == 'audio':
        audio_mix(tl, total)
    elif sys.argv[1] == 'video':
        k, n = int(sys.argv[2]), int(sys.argv[3])
        step = nfr // n + 1
        render_range(tl, subs, total, k * step, min(nfr, (k + 1) * step), f'out/v{k}.mp4')
