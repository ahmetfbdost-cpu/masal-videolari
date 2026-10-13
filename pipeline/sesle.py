"""Ücretsiz seslendirme — üç motor, sırayla denenir:

  gemini : Google Gemini TTS (ücretsiz katman, en doğal anlatım; GEMINI_API_KEY gerekir)
  edge   : Microsoft Edge nöral sesleri (edge-tts; anahtar gerekmez ama Microsoft zaman zaman kapatıyor)
  piper  : Piper açık kaynak TTS (tamamen çevrimdışı, her zaman çalışır; ses daha düz)

Kullanım:  python3 sesle.py <masal_klasoru>
Okur:      scenes.json (12 sahne metni), sahne_plani.json veya meta.json (başlık)
Yazar:     audio/part1.mp3 (başlık + sahne 1–6), audio/part2.mp3 (sahne 7–12), audio/segments.json, audio/motor.txt

Ortam: TTS_MOTORLAR (sıra, varsayılan "gemini,edge,piper"; anahtar yoksa gemini atlanır)
       TTS_SES / TTS_HIZ (Edge: tr-TR-EmelNeural, -8%) · GEMINI_SES (Sulafat) · PIPER_SES (tr_TR-dfki-medium)
"""
import asyncio, base64, json, os, subprocess, sys, tempfile, time, urllib.request
import numpy as np

SR = 44100
VOICE = os.environ.get('TTS_SES') or 'tr-TR-EmelNeural'
RATE = os.environ.get('TTS_HIZ') or '-8%'
PITCH = os.environ.get('TTS_PERDE') or '+0Hz'
GEMINI_VOICE = os.environ.get('GEMINI_SES') or 'Sulafat'
GEMINI_TTS_MODEL = os.environ.get('GEMINI_TTS_MODEL') or 'gemini-2.5-flash-preview-tts'
PIPER_VOICE = os.environ.get('PIPER_SES') or 'tr_TR-dfki-medium'
PIPER_DIR = os.environ.get('PIPER_DIZIN') or os.path.expanduser('~/.cache/piper')
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


async def speak_edge(text, out):
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


def speak_gemini(text, out_wav):
    key = os.environ['GEMINI_API_KEY']
    prompt = ('Sıcacık, sakin ve sevecen bir masal anlatıcısı gibi, 3-9 yaş çocuklara uyku öncesi masal okur '
              'gibi yavaşça ve duygulu oku. Diyaloglarda karakterlerin sesini hafifçe canlandır:\n\n' + text)
    body = json.dumps(dict(contents=[dict(parts=[dict(text=prompt)])],
                           generationConfig=dict(responseModalities=['AUDIO'], speechConfig=dict(
                               voiceConfig=dict(prebuiltVoiceConfig=dict(voiceName=GEMINI_VOICE)))))).encode()
    url = f'https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_TTS_MODEL}:generateContent'
    last = None
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, body, {'x-goog-api-key': key, 'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=300) as r:
                j = json.load(r)
            part = j['candidates'][0]['content']['parts'][0]['inlineData']
            pcm = base64.b64decode(part['data'])
            rate = 24000
            mt = part.get('mimeType', '')
            if 'rate=' in mt:
                rate = int(mt.split('rate=')[1].split(';')[0])
            subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 's16le', '-ar', str(rate), '-ac', '1', '-i', '-', out_wav],
                           input=pcm, check=True)
            return
        except urllib.error.HTTPError as e:
            last = f'HTTP {e.code} {e.read()[:200]!r}'
            if e.code in (400, 401, 403, 404):
                break
            time.sleep(40 if e.code == 429 else 5)
        except Exception as e:
            last = e
            time.sleep(5)
    raise RuntimeError(f'Gemini TTS başarısız: {last}')


def piper_model():
    os.makedirs(PIPER_DIR, exist_ok=True)
    onnx = os.path.join(PIPER_DIR, PIPER_VOICE + '.onnx')
    if not os.path.exists(onnx):
        lang, name, q = PIPER_VOICE.split('-')
        base = f'https://huggingface.co/rhasspy/piper-voices/resolve/main/{lang.split("_")[0]}/{lang}/{name}/{q}/'
        for ext in ('.onnx', '.onnx.json'):
            urllib.request.urlretrieve(base + PIPER_VOICE + ext, os.path.join(PIPER_DIR, PIPER_VOICE + ext))
    return onnx


def speak_piper(text, out_wav):
    model = piper_model()
    scale = os.environ.get('PIPER_HIZ') or '1.12'  # >1 daha yavaş
    for cmd in ([sys.executable, '-m', 'piper', '-m', model, '-f', out_wav, '--length-scale', scale,
                 '--sentence-silence', '0.35'],
                ['piper', '--model', model, '--output_file', out_wav, '--length_scale', scale,
                 '--sentence_silence', '0.35']):
        try:
            subprocess.run(cmd, input=text.encode('utf-8'), check=True, capture_output=True)
            if os.path.exists(out_wav) and os.path.getsize(out_wav) > 1000:
                return
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            err = getattr(e, 'stderr', b'') or b''
            print('piper denemesi başarısız:', str(e)[:200], err[-300:], flush=True)
    raise RuntimeError('Piper başarısız')


def engines():
    order = [m.strip() for m in (os.environ.get('TTS_MOTORLAR') or 'gemini,edge,piper').split(',') if m.strip()]
    if not os.environ.get('GEMINI_API_KEY'):
        order = [m for m in order if m != 'gemini']
    return order


def synth(engine, text, tmp, k):
    if engine == 'edge':
        out = os.path.join(tmp, f'{k}.mp3')
        asyncio.run(speak_edge(text, out))
    elif engine == 'gemini':
        out = os.path.join(tmp, f'{k}.wav')
        speak_gemini(text, out)
    else:
        out = os.path.join(tmp, f'{k}.wav')
        speak_piper(text, out)
    return trim(load(out))


def main(d):
    scenes = json.load(open(os.path.join(d, 'scenes.json'), encoding='utf-8'))
    assert len(scenes) == 12, 'scenes.json 12 sahne içermeli'
    items = [('title', title_of(d).rstrip('.') + '.')] + [(i + 1, t) for i, t in enumerate(scenes)]
    os.makedirs(os.path.join(d, 'audio'), exist_ok=True)
    tmp = tempfile.mkdtemp()
    clips, used = {}, None
    for engine in engines():
        # bütün masal tek motorla seslendirilir (sesler karışmasın)
        try:
            for k, text in items:
                clips[k] = synth(engine, text, tmp, k)
                print(engine, 'ses', k, round(len(clips[k]) / SR, 1), 's', flush=True)
            used = engine
            break
        except Exception as e:
            print(f'{engine} motoru başarısız, sıradakine geçiliyor: {e}', flush=True)
            clips = {}
    if not used:
        raise SystemExit('Hiçbir seslendirme motoru çalışmadı')
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
    label = {'edge': f'Edge TTS {VOICE}', 'gemini': f'Gemini TTS {GEMINI_VOICE}', 'piper': f'Piper {PIPER_VOICE}'}[used]
    open(os.path.join(d, 'audio/motor.txt'), 'w').write(label)
    print('tamam', label, flush=True)


if __name__ == '__main__':
    main(sys.argv[1])
