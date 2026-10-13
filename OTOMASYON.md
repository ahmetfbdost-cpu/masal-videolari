# Masal Videosu Otomasyonu — çalışma talimatı

Hedef: 3–9 yaş için ~9–10 dakikalık, özgün, Türkçe, seslendirmeli, animasyonlu bir masal videosu üretip
**ZihinByte** YouTube kanalında yayınlamak. Hattın tamamı ücretsiz araçlarla çalışır.

## Akış (her gün)

| Saat (TR) | Kim | Ne yapar | Maliyet |
|---|---|---|---|
| 17:47 | Claude zamanlanmış görevi "Masal yazarı" | Masalı yazar: `masal.md`, `scenes.json`, `sahne_plani.json`, `meta.json` (durum `yazildi`) → push | Claude aboneliği |
| push sonrası | GitHub Actions `masal.yml` | Seslendirir (Gemini TTS → Edge TTS → Piper), animasyonu çizer, `video.mp4` üretir, GitHub Releases'a koyar (durum `video_hazir`) | ücretsiz |
| 19:17 | GitHub Actions (zamanlı) | O gün masal yazılmamışsa **Gemini API** (ücretsiz katman) masalı yazar, sonra aynı üretim | ücretsiz |
| 21:47 | Claude zamanlanmış görevi "Masal yayıncı" | `video_hazir` masalları Zapier ile YouTube'a yükler (yedek: Metricool) → durum `yayinlandi` | Zapier ücretsiz planı |
| — | GitHub Actions | YouTube API denetimi onaylanınca (`YOUTUBE_API_YUKLE=evet`) yüklemeyi kendisi yapar | ücretsiz |

Durum takibi `masallar/NNN-ad/meta.json` içindeki `durum` alanıyla yapılır: `yazildi → video_hazir → yayinlandi`.
Son Actions çalışmasının özeti ve hata günlüğü: `durum/son_calisma.json`.

## 1. Masalı yazmak (Claude veya Gemini)
Yeni klasör: `masallar/NNN-kisa-ad/` (NNN = son numara + 1). Önce önceki masalların `meta.json`/`masal.md`
dosyalarına bak; konu, değer, karakter ve başlığı tekrar etme.

- **scenes.json**: 12 sahnenin anlatım metni (liste). Her sahne 450–580 karakter, toplam ~5.800–6.500.
  1. sahne "Bir varmış, bir yokmuş." ile başlar; son sahne "Gökten üç elma düşmüş" cümlesiyle biter.
  Geleneksel -mış'lı masal dili, yansımalar, kısa diyaloglar. Şiddet/korku yok, yumuşak gerilim, net bir değer.
- **sahne_plani.json**: animasyon planı (kod yazmaya gerek yok; `pipeline/scenes_auto.py` çizer):
  ```json
  {"baslik": "Sabırsız Sincap Pıtır", "alt_baslik": "ve Minik Fidan",
   "karakterler": {"Pıtır": "sincap", "Cıvıl": "kus"}, "ana_karakter": "Pıtır",
   "sahneler": [ {"mekan": "tepe", "zaman": "gunduz",
                  "karakterler": [{"ad": "Pıtır", "duygu": "korkmus>mutlu"}],
                  "efektler": ["kelebekler"], "hareket": "dur"}, ... 12 sahne ] }
  ```
  - türler: `kirpi, tavsan, ates_bocegi, kaplumbaga, baykus, sincap, kurbaga, kus, kelebek`
    (kirpi, tavşan, ateşböceği ve kaplumbağanın yüz ifadesi değişir; diğerleri sabittir)
  - mekan: `yuva, cayir, orman, dere, tepe, gol` · zaman: `gunduz, aksam, gece`
  - duygu: `normal, mutlu, korkmus, uzgun, saskin` (sahne içinde değişim: `"korkmus>mutlu"`)
  - efektler (0–2): `ay, ay_bulutlu, ates_bocekleri, muzik, kelebekler, kuslar, bulutlar, yildiz_kaymasi`
  - hareket: `dur` veya `yuru`; sahnede en fazla 4 karakter
- **masal.md**: başlık, yaş grubu/konu, karakter listesi, sahne başlıklarıyla tam metin.
- **meta.json**: `no, baslik, alt_baslik, tarih (YYYY-MM-DD, TR), deger, karakterler, ozet,
  aciklama (YouTube açıklaması, 2-3 cümle), etiketler, yazar, durum: "yazildi"`.

Yerelde kontrol (isteğe bağlı): `cd pipeline && SAHNE_PLANI=<tam yol>/sahne_plani.json python3 -c "import render; ..."`
ile birkaç kare çizip bakmak. Sonra commit + push (`git fetch origin main && git rebase origin/main` önce).
Push edilen `sahne_plani.json`, Actions'ı otomatik başlatır.

## 2. Ses ve video (GitHub Actions, otomatik)
- `pipeline/sesle.py`: motorları sırayla dener, bütün masal tek motorla seslendirilir:
  1. **Gemini TTS** (ücretsiz katman, en doğal anlatıcı sesi; `GEMINI_API_KEY` varsa) — ses: `GEMINI_SES` (varsayılan Sulafat)
  2. **Edge TTS** (`tr-TR-EmelNeural`; Ekim 2026 itibarıyla Microsoft tarafında 403 hatası veriyor, düzelirse kendiliğinden devreye girer)
  3. **Piper** (açık kaynak, çevrimdışı, her zaman çalışır; `PIPER_SES` varsayılan `tr_TR-dfki-medium`)
  Sıra ve sesler depo değişkenleriyle değişir: Settings → Secrets and variables → Actions → Variables →
  `TTS_MOTORLAR`, `GEMINI_SES`, `TTS_SES`, `PIPER_SES`, `PIPER_HIZ`. Kullanılan motor `meta.json` → `ses` alanına yazılır.
- **Premium ses (isteğe bağlı):** ElevenLabs ile üretilmiş `audio/part1.mp3` (başlık + sahne 1–6) ve
  `audio/part2.mp3` (sahne 7–12, sahneler arasında 2,5 sn sessizlik) `git add -f` ile eklenirse Edge TTS atlanır.
- `pipeline/uret.py --bekleyenler`: animasyon + müzik + altyazı → `video.mp4` (< 30 MB), `onizleme.jpg`.
- Video depoya değil **GitHub Releases**'a (`masal-NNN` etiketi) yüklenir; bağlantı `meta.json` → `video_url`.

## 3. Yayın
**Zapier (şimdiki ana yol):** `execute_zapier_write_action`, `selected_api: "YouTubeV4CLIAPI"`,
`action: "upload_video"`, `tool_name: "youtube_upload_video"`; params: `title` ("<başlık> <alt başlık> | Çocuk Masalı"),
`description` (meta `aciklama` + "Seslendirme yapay zekâ ile üretilmiştir."), `video` = `meta.video_url`,
`privacy_status: "public"`, `tags`, `default_language: "tr"`, `default_audio_language: "tr"`, `category_id: "1"`,
`made_for_kids: "true"`, `notify_subscribers: "true"`. `channelTitle == "ZihinByte"` ve `play_url`'yi doğrula.
**Yedek:** Metricool `createScheduledPost`, `blogId: 7246301`, ağ `youtube`, media = `video_url`,
`youtubeData: {title, type: "video", privacy: "public", madeForKids: true, category: "FILM_ANIMATION",
isAiGeneratedContent: true, tags}`, 15 dakika sonrası.
**YouTube API (denetim onayından sonra):** Actions `pipeline/youtube_yukle.py` ile kendisi yükler — bkz. `KURULUM.md`.
Yayından sonra `meta.json`: `durum: "yayinlandi"`, `youtube_url`, `yayin_yolu`; `python3 pipeline/readme_guncelle.py`; push.
Aynı masalı iki kez yayınlama (`youtube_url` doluysa dokunma).

## Notlar
- 001 numaralı masal eski yöntemle (ElevenLabs + elle çizilmiş `pipeline/scenes.py`) üretildi:
  https://www.youtube.com/watch?v=CM0lm6RBsjg — `scenes.py` hâlâ çalışır (SAHNE_PLANI verilmezse kullanılır).
- GitHub Models 30 Temmuz 2026'da kapatıldı; yedek yazar Gemini'dir.
- Depo herkese açık olduğu için GitHub Actions dakikaları ücretsizdir.
