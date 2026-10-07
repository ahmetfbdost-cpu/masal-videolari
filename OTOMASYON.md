# Masal Videosu Otomasyonu — çalışma talimatı

Bu dosya, zamanlanmış görevin her çalışmasında Claude'un izlediği adımlardır.
Hedef: 3–9 yaş için ~9–10 dakikalık, özgün, Türkçe, seslendirmeli, animasyonlu bir masal videosu üretip
ZihinByte YouTube kanalında yayınlamak.

## Ön koşullar (bir kez)
- Oturum claude.ai/code üzerinde, ağ erişimi **Custom** olan ortamda çalışır; izinli alan adları:
  `storage.googleapis.com`, `*.elevenlabs.io` (+ varsayılan paket listesi).
- Bağlayıcılar: **ElevenLabs** (seslendirme), **Metricool** (YouTube yayını; marka "ZihinByte", blogId 7246301).
- Bu depo herkese açıktır; videolar `masallar/<no>-<ad>/video.mp4` altında barındırılır.

## Adımlar
1. **Konu seç:** `masallar/` altındaki önceki masallara bak; tekrar etmeyen bir değer seç
   (paylaşma, sabır, dürüstlük, farklılıklara saygı, doğayı koruma, yardımlaşma...). Yeni klasör: `masallar/NNN-kisa-ad/`.
2. **Masalı yaz** (`masal.md`): 12 sahne, toplam ~6.000–6.500 karakter, "Bir varmış, bir yokmuş" ile başlar,
   "Gökten üç elma düşmüş" ile biter. Özgün karakterler; şiddet/korku yok, yumuşak gerilim.
   `scenes.json` = 12 sahnenin anlatım metni (liste).
3. **Seslendir:** ElevenLabs `creative_generate_speech`, model `eleven_multilingual_v2`,
   ses **Ela – Storyteller** (`KwaeIqNikLVCR098EG82`), `generations_count: 1`.
   Metin 5.000 karakter sınırı yüzünden iki parça: parça 1 = "<Başlık>. <break time="2.0s" />" + sahne 1–6,
   parça 2 = sahne 7–12; sahneler arasına `<break time="2.5s" />`. Bitince `content_url`'leri
   `curl` ile `audio/part1.mp3`, `audio/part2.mp3` olarak indir.
4. **Sahneleri çiz:** `pipeline/scenes.py` içindeki `build()` fonksiyonunu yeni hikâyeye göre yeniden yaz
   (mevcut `art.py` karakterleri ve arka planları yeniden kullanılabilir; gerekirse yeni karakter fonksiyonu ekle).
   Anahtarlar: `'title'`, 1–12, `'end'`. `render.py` içindeki `TITLE`/`SUBTITLE`'ı güncelle.
   `python3 render.py` ile önizleme karelerini üret ve kontrol et.
5. **Videoyu üret:** `python3 build_video.py plan` → `audio` → `video 0 2` ve `video 1 2` (paralel) →
   iki parçayı birleştirip sesi ekle, `-tune animation -crf 27 -b:a 96k` ile < 30 MB `video.mp4` üret.
6. **Depoya koy:** `masallar/NNN-ad/` içine `masal.md`, `scenes.json`, `video.mp4`, `onizleme.jpg` ekle; commit + push.
7. **YouTube'da yayınla:** Metricool `createScheduledPost`, `blogId: 7246301`, ağ `youtube`,
   media = `https://github.com/ahmetfbdost-cpu/masal-videolari/raw/main/masallar/NNN-ad/video.mp4`,
   `youtubeData: {title, type: "video", privacy: "public", madeForKids: true, category: "FILM_ANIMATION",
   isAiGeneratedContent: true, tags: [...]}`; yayın saati: aynı gün 18:00 (Europe/Istanbul).
8. **Rapor:** Kullanıcıya masal adı, süre, Metricool planner bağlantısı ve kullanılan ElevenLabs kredisini bildir.

## Notlar
- Metricool medya bağlantısını kendi sunucusuna kopyalar; GitHub bağlantısı herkese açık olmalı (depo Public).
- YouTube ayarları: `madeForKids: true` (çocuk içeriği), `isAiGeneratedContent: true` (yapay zekâ seslendirmesi).
- Masal başına ElevenLabs maliyeti ~6.500 kredi.
- İlk masal (001) 7 Ekim 2026'da yayınlandı.
