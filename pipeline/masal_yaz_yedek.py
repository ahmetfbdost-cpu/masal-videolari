"""Ücretsiz yedek yazar: Google Gemini API (AI Studio ücretsiz katmanı) ile yeni bir masal yazar.

(Önceden GitHub Models kullanılması planlanmıştı; GitHub Models 30 Temmuz 2026'da kapatıldı.)
Kullanım:
  python3 pipeline/masal_yaz_yedek.py              # her durumda yeni masal yaz
  python3 pipeline/masal_yaz_yedek.py --gerekirse  # bugün (Europe/Istanbul) yazılmış masal yoksa yaz
Ortam: GEMINI_API_KEY (GitHub secret), MODELLER (virgülle; varsayılan gemini-2.5-flash,gemini-2.5-flash-lite)
Yazar: masallar/NNN-ad/{masal.md, scenes.json, sahne_plani.json, meta.json(durum=yazildi)}
"""
import glob, json, os, re, sys, time, unicodedata
import urllib.request, urllib.error
from datetime import datetime, timezone, timedelta

PIPE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(PIPE)
sys.path.insert(0, PIPE)
TR = timezone(timedelta(hours=3))
MODELS = [m.strip() for m in (os.environ.get('MODELLER') or 'gemini-2.5-flash,gemini-2.5-flash-lite').split(',')
          if m.strip()]

# scenes_auto ile aynı sözlük (Pillow gerektirmeden kullanmak için burada da tanımlı)
MEKANLAR = ['yuva', 'cayir', 'orman', 'dere', 'tepe', 'gol']
ZAMANLAR = ['gunduz', 'aksam', 'gece']
TURLER = ['kirpi', 'tavsan', 'ates_bocegi', 'kaplumbaga', 'baykus', 'sincap', 'kurbaga', 'kus', 'kelebek']
DUYGULAR = ['normal', 'mutlu', 'korkmus', 'uzgun', 'saskin']
EFEKTLER = ['ay', 'ay_bulutlu', 'ates_bocekleri', 'muzik', 'kelebekler', 'kuslar', 'bulutlar', 'yildiz_kaymasi']

KURALLAR = f"""Sen 3–9 yaş çocuklar için özgün Türkçe masallar yazan deneyimli bir masal yazarısın.
Masal, YouTube'da yayınlanacak ~9–10 dakikalık sesli ve animasyonlu bir videoya dönüşecek.

KURALLAR
- 12 sahne. Her sahne 480–580 karakter (toplam ~6.000–6.500 karakter). Sesli okunacak akıcı, sıcak, ritmik bir dil.
- 1. sahne tam olarak "Bir varmış, bir yokmuş." ile başlar. 12. sahne tam olarak "Gökten üç elma düşmüş." ile biter.
- Geleneksel masal dili: -mış'lı geçmiş zaman, tekrarlar, yansımalar (şırıl şırıl, pıtır pıtır), kısa diyaloglar.
- Tek bir net değer işlenir (ör. paylaşma, sabır, dürüstlük, farklılıklara saygı, doğayı koruma, özür dilemek,
  yardımlaşma, sırasını beklemek, hata yapmaktan korkmamak). Değer vaaz edilmez, olaylarla gösterilir.
- Şiddet, korkutucu yaratık, tehlikeli davranış, ölüm, kötü söz yok. Gerilim yumuşaktır ve iyi biter.
- Karakterler YALNIZCA şu türlerden seçilir (animasyonda çizilebilen hayvanlar): {', '.join(TURLER)}.
  2–5 karakter; her birine Türkçe, sevimli, kısa bir isim ver. Gerçek marka/çizgi film karakteri kullanma.
- Her sahne için görsel plan: mekan ∈ {MEKANLAR}, zaman ∈ {ZAMANLAR}, sahnede görünen karakterler (en fazla 4)
  ve her birinin duygusu ∈ {DUYGULAR} (sahne içinde değişirse "korkmus>mutlu" gibi yaz),
  efektler ⊂ {EFEKTLER} (0–2 tane, hikâyeye uygun), hareket ∈ ["dur", "yuru"].
- Mekan ve zaman hikâyenin akışıyla tutarlı olsun; aynı mekanı arka arkaya 3'ten fazla kullanma.
- Yanıtı YALNIZCA geçerli JSON olarak ver, başka hiçbir şey yazma."""


def call(messages, model, max_tokens=8000):
    """Gemini API (Google AI Studio ücretsiz katmanı). messages: OpenAI biçiminde liste."""
    key = os.environ.get('GEMINI_API_KEY')
    if not key:
        raise SystemExit('GEMINI_API_KEY yok')
    system = '\n\n'.join(m['content'] for m in messages if m['role'] == 'system')
    contents = [dict(role='model' if m['role'] == 'assistant' else 'user', parts=[dict(text=m['content'])])
                for m in messages if m['role'] != 'system']
    gen = dict(temperature=0.9, maxOutputTokens=max_tokens, responseMimeType='application/json')
    if '2.5' in model:
        gen['thinkingConfig'] = dict(thinkingBudget=1024)
    body = json.dumps(dict(systemInstruction=dict(parts=[dict(text=system)]), contents=contents,
                           generationConfig=gen)).encode()
    url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'
    req = urllib.request.Request(url, body, {'x-goog-api-key': key, 'Content-Type': 'application/json'},
                                 method='POST')
    with urllib.request.urlopen(req, timeout=300) as r:
        raw = r.read().decode('utf-8', 'replace')
    try:
        j = json.loads(raw)
        txt = ''.join(p.get('text', '') for p in j['candidates'][0]['content']['parts'] if not p.get('thought'))
        txt = re.sub(r'^```(?:json)?|```$', '', txt.strip()).strip()
        return json.loads(txt)
    except Exception as e:
        print('ham yanıt (ilk 600):', raw[:600], flush=True)
        raise ValueError(f'yanıt çözülemedi: {e}')


def call_any(messages, max_tokens=8000):
    last = None
    for model in MODELS:
        for attempt in range(2):
            try:
                out = call(messages, model, max_tokens)
                print('model:', model, flush=True)
                return out, model
            except urllib.error.HTTPError as e:
                last = f'{model}: HTTP {e.code} {e.read()[:300]!r}'
                print(last, flush=True)
                if e.code in (400, 401, 403, 404):
                    break
                time.sleep(30 if e.code == 429 else 5)
            except Exception as e:
                last = f'{model}: {e}'
                print(last, flush=True)
                time.sleep(5)
    raise SystemExit(f'Gemini çağrısı başarısız: {last}')


def slugify(s):
    s = s.lower().replace('ı', 'i').replace('ğ', 'g').replace('ü', 'u').replace('ş', 's').replace('ö', 'o') \
        .replace('ç', 'c').replace('â', 'a').replace('î', 'i').replace('û', 'u')
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    return '-'.join(s.split('-')[:4]) or 'masal'


def previous():
    out = []
    for d in sorted(glob.glob(os.path.join(ROOT, 'masallar', '[0-9][0-9][0-9]-*'))):
        md = os.path.join(d, 'masal.md')
        meta = os.path.join(d, 'meta.json')
        title, value, chars = os.path.basename(d), '', ''
        if os.path.exists(meta):
            m = json.load(open(meta, encoding='utf-8'))
            title = (m.get('baslik', '') + ' ' + m.get('alt_baslik', '')).strip() or title
            value = m.get('deger', '')
            chars = ', '.join(f'{k} ({v})' for k, v in m.get('karakterler', {}).items())
        elif os.path.exists(md):
            t = open(md, encoding='utf-8').read()
            mm = re.search(r'^#\s+(.+)$', t, re.M)
            title = mm.group(1) if mm else title
            mv = re.search(r'\*\*Konu:\*\*\s*(.+)', t)
            value = mv.group(1).strip() if mv else ''
            chars = ', '.join(re.findall(r'^- \*\*([^*]+):\*\*', t, re.M))
        out.append(f'- {title} | değer: {value} | karakterler: {chars}')
    return out


def today_exists():
    today = datetime.now(TR).date().isoformat()
    for p in glob.glob(os.path.join(ROOT, 'masallar', '*', 'meta.json')):
        if json.load(open(p, encoding='utf-8')).get('tarih') == today:
            return True
    return False


def clean_scene(sc, chars):
    out = dict(mekan=sc.get('mekan') if sc.get('mekan') in MEKANLAR else 'cayir',
               zaman=sc.get('zaman') if sc.get('zaman') in ZAMANLAR else 'gunduz',
               hareket='yuru' if sc.get('hareket') == 'yuru' else 'dur')
    ks = []
    for c in sc.get('karakterler', [])[:4]:
        if isinstance(c, str):
            c = {'ad': c}
        if c.get('ad') in chars:
            moods = [m for m in str(c.get('duygu', 'normal')).split('>') if m.strip() in DUYGULAR] or ['normal']
            ks.append(dict(ad=c['ad'], duygu='>'.join(m.strip() for m in moods)))
    out['karakterler'] = ks
    out['efektler'] = [e for e in sc.get('efektler', []) if e in EFEKTLER][:2]
    return out


def validate(story):
    errs = []
    sc = story.get('sahneler', [])
    if len(sc) != 12:
        errs.append(f'{len(sc)} sahne var, 12 olmalı')
    total = sum(len(s.get('metin', '')) for s in sc)
    if not 5200 <= total <= 7600:
        errs.append(f'toplam {total} karakter (5.200–7.600 olmalı)')
    for i, s in enumerate(sc, 1):
        n = len(s.get('metin', ''))
        if n < 300:
            errs.append(f'sahne {i} çok kısa ({n})')
    return errs


def write_story(story, model):
    chars = {k: v for k, v in story['karakterler'].items() if v in TURLER}
    if not chars:
        raise SystemExit('geçerli karakter yok')
    ana = story.get('ana_karakter') if story.get('ana_karakter') in chars else next(iter(chars))
    sc = story['sahneler']
    texts = [re.sub(r'\s+', ' ', s['metin']).strip() for s in sc]
    if not texts[0].startswith('Bir varmış, bir yokmuş'):
        texts[0] = 'Bir varmış, bir yokmuş. ' + texts[0]
    if 'Gökten üç elma düşmüş' not in texts[-1]:
        texts[-1] = texts[-1].rstrip() + ' Gökten üç elma düşmüş.'
    nums = [int(os.path.basename(d)[:3]) for d in glob.glob(os.path.join(ROOT, 'masallar', '[0-9][0-9][0-9]-*'))]
    no = max(nums or [0]) + 1
    title, sub = story['baslik'].strip(), story.get('alt_baslik', '').strip()
    d = os.path.join(ROOT, 'masallar', f'{no:03d}-{slugify(title)}')
    os.makedirs(d, exist_ok=True)
    plan = dict(baslik=title, alt_baslik=sub, karakterler=chars, ana_karakter=ana,
                sahneler=[clean_scene(s, chars) for s in sc])
    json.dump(plan, open(os.path.join(d, 'sahne_plani.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    json.dump(texts, open(os.path.join(d, 'scenes.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    md = [f'# {title} {sub}'.strip(), '',
          f"**Yaş grubu:** 3–9 yaş · **Tahmini süre:** ~10 dakika · **Konu:** {story.get('deger', '')}", '',
          '**Karakterler**']
    for k, v in chars.items():
        md.append(f"- **{k}:** {story.get('karakter_tanimlari', {}).get(k, v.replace('_', ' '))}")
    md += ['', '---', '']
    for i, (s, t) in enumerate(zip(sc, texts), 1):
        md += [f"## Sahne {i} – {s.get('sahne_basligi', '').strip() or f'Sahne {i}'}", '', t, '']
    open(os.path.join(d, 'masal.md'), 'w', encoding='utf-8').write('\n'.join(md))
    meta = dict(no=no, baslik=title, alt_baslik=sub, tarih=datetime.now(TR).date().isoformat(),
                deger=story.get('deger', ''), karakterler=chars, ozet=story.get('ozet', ''),
                aciklama=story.get('youtube_aciklama', ''), etiketler=story.get('etiketler', [])[:12],
                yazar=f'Gemini ({model})', durum='yazildi')
    json.dump(meta, open(os.path.join(d, 'meta.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print('YAZILDI', d, sum(map(len, texts)), 'karakter', flush=True)
    return d


def main():
    if '--gerekirse' in sys.argv and today_exists():
        print('Bugünün masalı zaten yazılmış; yedek yazar çalışmadı.')
        return
    if not os.environ.get('GEMINI_API_KEY'):
        print('GEMINI_API_KEY tanımlı değil; yedek yazar atlandı (GitHub → Settings → Secrets → Actions).')
        return
    prev = previous()
    schema1 = {
        'baslik': 'Kısa ana başlık (ör. "Minik Kirpi Fındık")', 'alt_baslik': 'ikinci satır (ör. "ve Kayıp Ay Işığı")',
        'deger': 'işlenen değer', 'ozet': '2-3 cümle özet',
        'karakterler': {'İsim': 'tür'}, 'karakter_tanimlari': {'İsim': 'tek cümle tanım'}, 'ana_karakter': 'İsim',
        'hikaye_plani': ['12 maddelik kısa olay planı'],
        'sahneler': [{'sahne_basligi': '...', 'metin': '480-580 karakter anlatım', 'mekan': '...', 'zaman': '...',
                      'karakterler': [{'ad': 'İsim', 'duygu': 'normal'}], 'efektler': [], 'hareket': 'dur'}],
        'youtube_aciklama': '2-3 cümlelik, ebeveynlere hitap eden video açıklaması',
        'etiketler': ['masal', 'çocuk masalları', '...']}
    m1 = [{'role': 'system', 'content': KURALLAR},
          {'role': 'user', 'content': 'Daha önce yazılan masallar (konu, değer, karakter ve başlığı TEKRAR ETME):\n'
                                      + ('\n'.join(prev) or '- (yok)') +
                                      '\n\nYeni bir masal tasarla. Bu yanıtta yalnızca SAHNE 1–6\'yı yaz '
                                      '(sahneler listesinde 6 öğe), ama hikaye_plani 12 sahnenin tamamını kapsasın. '
                                      'JSON şeması:\n' + json.dumps(schema1, ensure_ascii=False)}]
    for attempt in range(2):
        a, model = call_any(m1)
        m2 = m1 + [{'role': 'assistant', 'content': json.dumps(a, ensure_ascii=False)},
                   {'role': 'user', 'content': 'Şimdi aynı masalın SAHNE 7–12\'sini yaz (hikaye_plani\'na uy, '
                                               'son sahne "Gökten üç elma düşmüş." ile bitsin). JSON şeması: '
                                               '{"sahneler": [6 sahne, aynı alanlarla]}'}]
        b, _ = call_any(m2)
        a['sahneler'] = a.get('sahneler', [])[:6] + b.get('sahneler', [])[:6]
        errs = validate(a)
        print('doğrulama:', errs or 'tamam', flush=True)
        if not errs or attempt == 1:
            if len(a['sahneler']) != 12:
                raise SystemExit('masal 12 sahne değil: ' + '; '.join(errs))
            return write_story(a, model)


if __name__ == '__main__':
    main()
