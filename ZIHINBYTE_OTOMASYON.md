# ZihinByte Günlük Sosyal Medya Otomasyonu — çalışma talimatı

Hedef: Her gün 2 profesyonel paylaşım (Instagram @zihinbyte.tr + YouTube). Konular: yapay zekâ, yazılım, teknoloji, eğitim.
Kullanıcıya soru sorulmaz; her karar burada yazılı kurallara göre verilir. Metricool blogId: 7246301, saat dilimi Europe/Istanbul.

## Günlük düzen
| Saat | İçerik | Ağlar |
|------|--------|-------|
| 10:00 | **Seslendirmeli Reels** (20–30 sn, dikey 1080x1920) | Instagram `REEL` + YouTube `short` (tek gönderi, iki sağlayıcı) |
| 18:00 | Gün tek ise **Story** videosu (10–15 sn, metinsiz gönderilir); gün çift ise **Carousel** (6–7 slayt PNG, 1080x1350) | Instagram `STORY` / Instagram `POST` |

"Gün tek/çift" = ayın gününe göre. Haftanın her günü (hafta sonu dahil) yayın vardır.

## Adımlar
1. **Depoyu güncelle:** `ahmetfbdost-cpu/masal-videolari` (yoksa `add_repo`, push erişimiyle) klonla, `git pull origin main`.
2. **Tekrar kontrolü:** `zihinbyte/icerik_gunlugu.md` ve `zihinbyte/*/` klasörlerini oku; son 30 günde işlenmiş konuları tekrar etme.
   Çift gönderi kontrolü: Metricool `getScheduledPosts` ile bugünün (00:00–23:59) gönderilerine bak; 10:00 veya 18:00'de zaten gönderi varsa onu yeniden oluşturma.
3. **Konu seç:** Bugünün tarihi `YYYY-MM-DD` (= `GUN`). Reels için pratik ve kaydedilesi bir ipucu (prompt yazma, Git, Python, API, güvenlik, verimlilik, AI araçları, öğrenme teknikleri, yazılım kariyeri...). Story/Carousel için ilişkili ama farklı bir kısa içerik. Doğru, güncel ve abartısız olsun; sahte rakam veya sahte iddia yazma.
4. **İçeriği yaz:** `zihinbyte/pipeline/content.py` bir örnektir (yardımcı fonksiyonlar T, BAD, CHIP, CODE, S, step, cta; `VIDEOS`, `CAROUSELS`).
   Bugüne ait yeni `zihinbyte/pipeline/gunluk_<GUN>.py` dosyası aç: `from content import *` ile aynı yapıda `VIDEOS`/`CAROUSELS` sözlüklerini tanımla ve `run.py` ile aynı mantıkla çalıştır
   (`ZB_OUT` ortam değişkeni çıktı klasörüdür; `ZB_MODULE=gunluk_<GUN> python3 run.py ...` ile bu modül kullanılır; modül `VIDEOS`/`CAROUSELS` tanımlar).
   Güvenli bölge: 1080x1920'de içerik y=470–1440 arasında kalmalı. Marka: ZihinByte, `@zihinbyte.tr`.
5. **Seslendir (yalnız Reels):** ElevenLabs `creative_generate_speech`, `voice_id` = `Ec` sesi **Jx3VaTomriZgwBbv8gLz**, model `eleven_multilingual_v2`,
   Türkçe, ~55–70 kelime, doğal ve akıcı metin; **`generations_count: 1`**. Üretim çağrısını asla tekrarlama. `creative_get_flow_run_status` ile bitmesini bekle,
   `content_url`'yi `curl` ile indir (ağ izni: `storage.googleapis.com`, `*.elevenlabs.io`). İndirme başarısız olursa **sessiz (yalnız müzikli) Reels** üretip yine yayınla ve raporda belirt.
   Sahne sürelerini konuşmaya göre ayarla (`ffprobe` ile ses süresi; toplam video ≈ ses süresi + 0,6 sn). `make_video(..., voice=<mp3>)` sesi müzikle karıştırır, −16 LUFS'a normalize eder.
6. **Üret:** `python3 run.py video <anahtar>` (Reels, Story) ve `python3 run.py slides <anahtar>` (carousel). Önizleme karelerini/slaytları `Read` ile bak; taşan metin, okunmayan yazı varsa düzelt. Video: H.264/AAC, 48 kHz, < 30 MB.
7. **Depoya koy:** `zihinbyte/<GUN>/reels-<ad>.mp4`, `story-<ad>.mp4` veya `carousel-<ad>/slide_1.png…`; `zihinbyte/icerik_gunlugu.md` dosyasına tarih, konu ve başlık ekle; commit + push (main). Tek seferde tek git işlemi çalıştır.
   Raw adresin açıldığını doğrula: `https://github.com/ahmetfbdost-cpu/masal-videolari/raw/main/zihinbyte/<GUN>/<dosya>`.
8. **Zamanla (Metricool `createScheduledPost`, `autoPublish: true`):**
   - Reels, `<GUN>T10:00:00`: `providers:[instagram, youtube]`, `media:[raw URL]`, `text` = Türkçe açıklama (kanca cümlesi, 3–4 madde, "kaydet" çağrısı, soru, 6–8 hashtag + `#shorts`),
     `instagramData:{type:"REEL", showReelOnFeed:true, isAiGenerated:true}`,
     `youtubeData:{title (≤ 70 karakter), type:"short", privacy:"public", madeForKids:false, category:"SCIENCE_TECHNOLOGY" (eğitim ağırlıklıysa "EDUCATION"), isAiGeneratedContent:true, tags:[...]}`.
   - Story, `<GUN>T18:00:00`: `providers:[instagram]`, `media:[raw URL]`, **`text` gönderme**, `instagramData:{type:"STORY", isAiGenerated:true}`.
   - Carousel, `<GUN>T18:00:00`: `providers:[instagram]`, `media:[slayt URL'leri sırayla]`, `text` = açıklama + hashtag, `instagramData:{type:"POST", isAiGenerated:true}`.
   - `publicationDate:{dateTime:"<GUN>T..", timezone:"Europe/Istanbul"}`. Tarih geçmişteyse (ör. 18:00 gönderisi için saat geçtiyse) en yakın gelecek dakikaya (+10 dk) ayarla.
9. **Doğrula:** `getScheduledPosts` ile iki gönderiyi gör. Hata varsa nedenini ve hangi adımda olduğunu yaz; sahte başarı bildirme.
10. **Temizle (iş bitince sil):** `getScheduledPosts` yanıtında gönderilerin `media` adresleri `static.metricool.com` ise Metricool dosyayı kendi sunucusuna almış demektir.
    O zaman `git rm -r zihinbyte/<GUN>/` ile bugünün video/slayt dosyalarını depodan sil (ve önceki günlerden kalan `zihinbyte/20*/` klasörlerini de), `icerik_gunlugu.md` ve `pipeline/` dosyalarını koru, commit + push et.
    `media` hâlâ GitHub adresiyse silme; raporda belirt.
11. **Rapor:** Kullanıcıya kısaca: bugünün konuları, Reels/Story/Carousel durumu, Metricool planner bağlantıları, kullanılan ElevenLabs kredisi, varsa sorun.

## Notlar
- Metricool medyayı kendi sunucusuna kopyalar; depo **Public** olmalıdır.
- Her Reels sonunda "Kaydet" + "Takip et: @zihinbyte.tr" çağrısı olur; açıklama bir soruyla biter (yorum artırır).
- Reels başına ElevenLabs maliyeti ≈ 300 kredi (tek varyasyon).
- Telif: müzik ve efektler `engine.py` içinde sentezlenir; dış müzik/görsel kullanma.
- Depo geçmişinde silinen dosyaların eski sürümleri kalır (git doğası); depoda çalışma dosyası bırakılmaz.
- 8 Ekim 2026 (Reels + Story) elle hazırlandı ve zamanlandı; otomasyon 9 Ekim'den başlar.
