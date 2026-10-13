# Kurulum — bir kez yapılacaklar

Video üretimi (Piper seslendirme + animasyon + GitHub Actions) hiçbir kurulum gerektirmez; depo herkese açık olduğu sürece çalışır.
Aşağıdakiler isteğe bağlı iki ücretsiz parçayı açar.

## A) Gemini anahtarı (5 dakika) — doğal anlatıcı sesi + yedek yazar
Tek anahtar iki şeyi açar: masallar Piper yerine çok daha doğal **Gemini TTS** sesiyle seslendirilir, ve Claude'un
yazar görevi bir gün çalışmazsa 19:17'de masalı Gemini yazar.

1. https://aistudio.google.com/apikey adresine Google hesabınla gir → **Create API key** (kredi kartı istemez).
2. GitHub'da depo → **Settings → Secrets and variables → Actions → New repository secret**
   - Name: `GEMINI_API_KEY`  ·  Secret: kopyaladığın anahtar
3. Deneme: depo → **Actions → Masal videosu → Run workflow → islem: yedek-yeni-masal**.

Not: Ücretsiz katmanda gönderilen içerik Google'ın ürün geliştirmesinde kullanılabilir (masal metinleri için sorun değil).
Model değiştirmek için Variables'a `MODELLER` ekle (ör. `gemini-2.5-flash,gemini-2.5-flash-lite`).

## B) YouTube API ile doğrudan yükleme (ücretsiz, ama Google denetimi gerekir)
Denetimden geçmemiş projelerin API ile yüklediği videolar **kilitli özel** kalır ve herkese açık yapılamaz.
Bu yüzden önce kimlik bilgileri hazırlanır, denetim başvurusu yapılır, onay gelince açılır.
O zamana kadar yayın Claude'un "Masal yayıncı" görevi ile Zapier üzerinden yapılır.

1. **Proje:** https://console.cloud.google.com → yeni proje (ör. `zihinbyte-masal`).
2. **API:** APIs & Services → Library → **YouTube Data API v3** → Enable.
3. **OAuth izin ekranı:** APIs & Services → OAuth consent screen → External → uygulama adı, e-posta.
   Scopes'a `https://www.googleapis.com/auth/youtube.upload` ekle.
   Yayın durumunu **In production** yap (Testing'de kalırsa izin 7 günde sona erer; "doğrulanmamış uygulama"
   uyarısı yalnızca senin hesabın için çıkar, devam edebilirsin).
4. **İstemci:** Credentials → Create credentials → OAuth client ID → **Web application**.
   Authorized redirect URI: `https://developers.google.com/oauthplayground`. Client ID ve Client secret'ı not et.
5. **Yenileme anahtarı:** https://developers.google.com/oauthplayground → sağ üstte ⚙️ →
   "Use your own OAuth credentials" → Client ID/secret'ı gir. Sol kutuya
   `https://www.googleapis.com/auth/youtube.upload` yaz → **Authorize APIs** → ZihinByte kanalının bağlı olduğu
   hesapla giriş yap ve izin ver → **Exchange authorization code for tokens** → **Refresh token**'ı kopyala.
6. **GitHub secret'ları:** `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN`.
7. **Denetim başvurusu:** https://support.google.com/youtube/contact/yt_api_form
   ("YouTube API Services - Audit and Quota Extension Form"). Kullanım amacı: kendi kanalına günde 1 çocuk masalı
   videosu yükleyen kişisel otomasyon. Onay birkaç hafta sürebilir.
8. **Onay gelince:** Variables → `YOUTUBE_API_YUKLE` = `evet`. Bundan sonra Actions videoyu kendisi yükler;
   Claude'un yayıncı görevi yüklenecek bir şey bulamaz ve durur (istersen kapatılabilir).

## Elle tetikleme
- Actions sekmesi → **Masal videosu** → **Run workflow**:
  `bekleyenleri-uret` (yazılmış ama videosu olmayanları üret), `gerekirse-yedek`, `yedek-yeni-masal`.
- Ya da `.github/tetik` dosyasındaki `islem=` satırını değiştirip push et.
