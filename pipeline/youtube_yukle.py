"""Ücretsiz yayın: YouTube Data API v3 ile doğrudan yükleme.

Not: Google denetiminden (YouTube API Services Audit) geçmemiş projelerin yüklediği videolar
kilitli "özel" kalır. Bu yüzden workflow bu adımı yalnızca YOUTUBE_API_YUKLE=evet değişkeni varsa çalıştırır.

Kullanım:  python3 pipeline/youtube_yukle.py masallar/002-ornek   |   --bekleyenler (durum == video_hazir)
Ortam:     YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN, YOUTUBE_GIZLILIK (public|unlisted|private)
"""
import glob, json, os, sys, urllib.parse, urllib.request
from datetime import datetime, timezone, timedelta

PIPE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(PIPE)
TR = timezone(timedelta(hours=3))


def token():
    data = urllib.parse.urlencode(dict(client_id=os.environ['YT_CLIENT_ID'], client_secret=os.environ['YT_CLIENT_SECRET'],
                                       refresh_token=os.environ['YT_REFRESH_TOKEN'],
                                       grant_type='refresh_token')).encode()
    with urllib.request.urlopen('https://oauth2.googleapis.com/token', data, timeout=60) as r:
        return json.load(r)['access_token']


def description(m):
    base = m.get('aciklama') or m.get('ozet') or ''
    lines = [f"{m.get('baslik', '')} {m.get('alt_baslik', '')}".strip(), '', base, '']
    if m.get('deger'):
        lines.append(f"Bu masalın teması: {m['deger']}")
    lines += ['3–9 yaş için özgün, Türkçe, sesli ve animasyonlu masallar. Uyku öncesi dinlemek için idealdir.', '',
              'Masal ve animasyon yapay zekâ desteğiyle üretilmiştir. Seslendirme yapay zekâ ile üretilmiştir.', '',
              '#masal #çocukmasalları #uykumasalı']
    return '\n'.join(lines)[:4900]


def upload(d):
    d = os.path.abspath(d)
    mp = os.path.join(d, 'meta.json')
    m = json.load(open(mp, encoding='utf-8'))
    if m.get('youtube_url'):
        print('zaten yüklenmiş:', m['youtube_url'])
        return
    title = f"{m.get('baslik', '')} {m.get('alt_baslik', '')}".strip()
    title = (title + ' | Çocuk Masalı')[:100]
    tags = list(dict.fromkeys((m.get('etiketler') or []) + ['masal', 'çocuk masalları', 'uyku masalı',
                                                             'masal dinle', 'türkçe masal']))[:15]
    body = dict(snippet=dict(title=title, description=description(m), tags=tags, categoryId='1',
                             defaultLanguage='tr', defaultAudioLanguage='tr'),
                status=dict(privacyStatus=os.environ.get('YOUTUBE_GIZLILIK', 'public'), selfDeclaredMadeForKids=True,
                            containsSyntheticMedia=True, embeddable=True))
    video = os.path.join(d, 'video.mp4')
    size = os.path.getsize(video)
    at = token()
    req = urllib.request.Request(
        'https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status',
        json.dumps(body).encode(), {'Authorization': f'Bearer {at}', 'Content-Type': 'application/json; charset=UTF-8',
                                    'X-Upload-Content-Type': 'video/mp4', 'X-Upload-Content-Length': str(size)})
    with urllib.request.urlopen(req, timeout=60) as r:
        loc = r.headers['Location']
    with open(video, 'rb') as f:
        req = urllib.request.Request(loc, f.read(), {'Authorization': f'Bearer {at}', 'Content-Type': 'video/mp4'},
                                     method='PUT')
    with urllib.request.urlopen(req, timeout=1800) as r:
        res = json.load(r)
    vid = res['id']
    # önizleme görselini küçük resim yap (kanal doğrulanmamışsa sessizce atla)
    thumb = os.path.join(d, 'onizleme.jpg')
    if os.path.exists(thumb):
        try:
            req = urllib.request.Request(
                f'https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={vid}',
                open(thumb, 'rb').read(), {'Authorization': f'Bearer {at}', 'Content-Type': 'image/jpeg'})
            urllib.request.urlopen(req, timeout=120).read()
        except Exception as e:
            print('küçük resim atlandı:', e)
    m.update(durum='yayinlandi', youtube_url=f'https://www.youtube.com/watch?v={vid}', yayin_yolu='YouTube API',
             yayin_tarihi=datetime.now(TR).isoformat(timespec='minutes'),
             youtube_gizlilik=res.get('status', {}).get('privacyStatus'))
    json.dump(m, open(mp, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print('YÜKLENDİ', m['youtube_url'], m['youtube_gizlilik'])


if __name__ == '__main__':
    if sys.argv[1:] == ['--bekleyenler']:
        for p in sorted(glob.glob(os.path.join(ROOT, 'masallar', '*', 'meta.json'))):
            if json.load(open(p, encoding='utf-8')).get('durum') == 'video_hazir' and \
                    os.path.exists(os.path.join(os.path.dirname(p), 'video.mp4')):
                upload(os.path.dirname(p))
    else:
        upload(sys.argv[1])
