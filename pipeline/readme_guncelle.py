"""README.md'deki masal tablosunu masallar/*/meta.json dosyalarından yeniden oluşturur."""
import glob, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rows = ['| No | Masal | Süre | Ses | Yazar | Durum |', '|----|-------|------|-----|-------|-------|']
DURUM = {'yazildi': 'yazıldı, video bekliyor', 'video_hazir': 'video hazır, yayın bekliyor', 'yayinlandi': 'yayında'}
for p in sorted(glob.glob(os.path.join(ROOT, 'masallar', '*', 'meta.json'))):
    m = json.load(open(p, encoding='utf-8'))
    name = f"{m.get('baslik', '')} {m.get('alt_baslik', '')}".strip()
    link = m.get('youtube_url') or m.get('video_url')
    cell = f'[{name}]({link})' if link else name
    rows.append(f"| {m.get('no', 0):03d} | {cell} | {m.get('sure', '–')} | {m.get('ses', '–')} | "
                f"{m.get('yazar', '–')} | {DURUM.get(m.get('durum'), m.get('durum', '–'))} |")
p = os.path.join(ROOT, 'README.md')
s = open(p, encoding='utf-8').read()
table = '<!-- MASAL_TABLOSU -->\n' + '\n'.join(rows) + '\n<!-- /MASAL_TABLOSU -->'
if '<!-- MASAL_TABLOSU -->' in s:
    s = re.sub(r'<!-- MASAL_TABLOSU -->.*?<!-- /MASAL_TABLOSU -->', lambda _: table, s, flags=re.S)
else:
    s = re.sub(r'\| No \| Masal \| Süre \|.*?(?=\n\n|\Z)', lambda _: table, s, flags=re.S)
open(p, 'w', encoding='utf-8').write(s.rstrip() + '\n')
print('README güncellendi')
