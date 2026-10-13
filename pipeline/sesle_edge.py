"""Ücretsiz seslendirme: Microsoft Edge nöral sesleri (edge-tts paketi, API anahtarı gerekmez).

Kullanım:  python3 sesle_edge.py <masal_klasoru>
Okur:      scenes.json (12 sahne metni), sahne_plani.json veya meta.json (başlık)
Yazar:     audio/part1.mp3 (başlık + sahne 1–6), audio/part2.mp3 (sahne 7–12), audio/segments.json

Ortam değişkenleri: TTS_SES (varsayılan tr-TR-EmelNeural), TTS_HIZ (-8%), TTS_PERDE (+0Hz)
"""
import asyncio, json, os, subprocess, sys, tempfile
import numpy as np

SR = 44100
VOICE = os.environ.get('TTS_SES', 'tr-TR-EmelNeural')
RATE = os.environ.get('TTS_HIZ', '-8%')
PITCH = os.environ.get('TTS_PERDE', '+0Hz')
GAP_TITLE = 2.0
GAP = 2.5


def load(path):
    raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', path, '-ac', '1', '-ar', str(SR), '-f', 's16le', '-'])
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768


def trim(x, thr=0.004):
    idx = np.where(np.abs(x) > thr)[0]
    if not len(idx):
        return x
    a, b = max(0, idx[0] - int(0.05 * SR)), min(len(x), idx[-1] + int(0.15 * SR))
    return x[a:b]


async def speak(text, out):
    import edge_tts
    last = None
    for attempt in range(4):
        try:
            await edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH).save(out)
            if os.path.getsize(out) > 1000:
                return
        except Exception as e:  # ağ hatalarında tekrar dene
            last = e
        await asyncio.sleep(3 * (attempt + 1))
    raise RuntimeError(f'Edge TTS başarısız: {last}')


def title_of(d):
    for fn in ('sahne_plani.json', 'meta.json'):
        p = os.path.join(d, fn)
        if os.path.exists(p):
            j = json.load(open(p, encoding='utf-8'))
            t = j.get('baslik', '')
            st = j.get('alt_baslik', '')
            if t:
                return (t + ' ' + st).strip()
    import re
    m = re.search(r'^#\s+(.+)$', open(os.path.join(d, 'masal.md'), encoding='utf-8').read(), re.M)
    return m.group(1).strip() if m else 'Masal'


def main(d):
    scenes = json.load(open(os.path.join(d, 'scenes.json'), encoding='utf-8'))
    assert len(scenes) == 12, 'scenes.json 12 sahne içermeli'
    items = [('title', title_of(d).rstrip('.') + '.')] + [(i + 1, t) for i, t in enumerate(scenes)]
    os.makedirs(os.path.join(d, 'audio'), exist_ok=True)
    tmp = tempfile.mkdtemp()
    clips = {}
    for k, text in items:
        out = os.path.join(tmp, f'{k}.mp3')
        asyncio.run(speak(text, out))
        clips[k] = trim(load(out))
        print('ses', k, round(len(clips[k]) / SR, 1), 's', flush=True)
    segs = []
    for part, keys in (('audio/part1.mp3', ['title'] + list(range(1, 7))), ('audio/part2.mp3', list(range(7, 13)))):
        buf, pos, spans = [], 0, []
        for i, k in enumerate(keys):
            if i:
                g = GAP_TITLE if keys[i - 1] == 'title' else GAP
                buf.append(np.zeros(int(g * SR), np.float32))
                pos += int(g * SR)
            spans.append((k, pos, pos + len(clips[k])))
            buf.append(clips[k])
            pos += len(clips[k])
        x = np.concatenate(buf)
        total = len(x) / SR
        for i, (k, s0, s1) in enumerate(spans):
            a = 0.0 if i == 0 else (spans[i - 1][2] + s0) / 2 / SR
            b = total if i == len(spans) - 1 else (s1 + spans[i + 1][1]) / 2 / SR
            segs.append(dict(key=k, part=part, a=a, b=b, sa=s0 / SR, sb=s1 / SR))
        pcm = (np.clip(x, -1, 1) * 32767).astype(np.int16)
        subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 's16le', '-ar', str(SR), '-ac', '1', '-i', '-',
                        '-c:a', 'libmp3lame', '-b:a', '128k', os.path.join(d, part)], input=pcm.tobytes(), check=True)
    json.dump(segs, open(os.path.join(d, 'audio/segments.json'), 'w'), indent=1)
    print('tamam', VOICE, flush=True)


if __name__ == '__main__':
    main(sys.argv[1])
