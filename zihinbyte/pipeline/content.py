from engine import *

def T(text, size=100, f="B", color=WHITE, delay=0.0, gap=36):
    return dict(t="text", text=text, size=size, f=f, color=color, delay=delay, gap=gap)

def BAD(n, delay=0.0, gap=40):
    return dict(t="badge", text=str(n), delay=delay, gap=gap)

def CHIP(text, delay=0.0, gap=40):
    return dict(t="chip", text=text, delay=delay, gap=gap)

def CODE(lines, label="", delay=0.3, typing=1.5, size=44, gap=36):
    return dict(t="code", lines=lines, label=label, delay=delay, typing=typing, size=size, gap=gap)

def S(dur, *els):
    return dict(dur=dur, els=list(els))

def step(n, title, sub):
    return S(3.2, BAD(n), T(title, 104), T(sub, 54, "M", MUTED, delay=0.35))

def cta(line1, line2="Takip et: @zihinbyte.tr"):
    return S(3.6, T(line1, 96, gap=44), T(line2, 62, "B", ACCENT, delay=0.3, gap=24),
             T("Yapay zeka • Yazılım • Teknoloji", 42, "M", MUTED, delay=0.5))

K, ST, FN, PL, NM = C_KEY, C_STR, C_FUN, C_PLAIN, C_NUM

# ---------------------------------------------------------------- videos
VIDEOS = {}

VIDEOS["gun1_reels_prompt"] = dict(seed=1, bpm=88, scenes=[
    S(3.2, T("AI'dan kötü cevap mı alıyorsun?", 96, gap=50), T("Sorun AI'da değil, prompt'ta.", 62, "M", ACCENT, delay=0.5)),
    step(1, "Rol ver", "\"Sen deneyimli bir yazılım mentorusun.\""),
    step(2, "Bağlam ver", "Kim için, ne amaçla, hangi seviyede?"),
    step(3, "Format iste", "Madde madde, 5 adım, tablo..."),
    step(4, "Örnek göster", "İstediğin çıktının bir örneğini ekle."),
    S(4.6, CHIP("Hepsi bir arada"), T("Örnek prompt", 70, gap=30),
      T("Sen deneyimli bir Python mentorusun. Hiç kod bilmeyen birine döngüleri anlat. 5 madde, her biri örnekli olsun.", 50, "M", PL, delay=0.4)),
    cta("Kaydet, lazım olacak."),
])

# Gun 1 Reels, sesli surum: sahneler content_2.mp3 duraklamalarina gore zamanlandi (toplam 24.6 sn)
VIDEOS["gun1_reels_prompt_sesli"] = dict(seed=1, bpm=88,
    voice="/root/.claude/uploads/67b22a19-53a7-5d6d-8ef7-b65e19227de5/1aa65f71-content_2.mp3",
    scenes=[
    S(3.30, T("AI'dan kötü cevap mı alıyorsun?", 96, gap=50), T("Sorun AI'da değil, prompt'ta.", 62, "M", ACCENT, delay=1.7)),
    S(3.05, BAD(1, 0.0), T("Rol ver", 104, delay=0.1), T("\"Sen deneyimli bir yazılım mentorusun.\"", 54, "M", MUTED, delay=1.1)),
    S(4.00, BAD(2, 0.0), T("Bağlam ver", 104, delay=0.18), T("Kim için, ne amaçla, hangi seviyede?", 54, "M", MUTED, delay=1.0)),
    S(2.60, BAD(3, 0.0), T("Format iste", 104, delay=0.17), T("Madde madde, 5 adım, tablo...", 54, "M", MUTED, delay=1.05)),
    S(2.00, BAD(4, 0.0), T("Örnek göster", 104, delay=0.16), T("İstediğin çıktının örneğini ekle.", 54, "M", MUTED, delay=0.8)),
    S(6.00, CHIP("Hepsi bir arada", 0.0), T("Örnek prompt", 70, delay=0.1, gap=30),
      T("Sen deneyimli bir Python mentorusun. Hiç kod bilmeyen birine döngüleri anlat. 5 madde, her biri örnekli olsun.", 50, "M", PL, delay=0.35)),
    S(3.65, T("Kaydet, lazım olacak.", 96, delay=0.18, gap=44), T("Takip et: @zihinbyte.tr", 62, "B", ACCENT, delay=2.0, gap=24),
      T("Yapay zeka • Yazılım • Teknoloji", 42, "M", MUTED, delay=2.2)),
])

VIDEOS["gun1_story_python"] = dict(seed=2, bpm=92, key_shift=2, scenes=[
    S(2.8, CHIP("Python 🐍".replace(" 🐍", "")), T("Günün ipucu", 110, gap=30), T("Listeyi tek satırda ters çevir", 58, "M", MUTED, delay=0.35)),
    S(4.0, T("Döngü yazma.", 84, gap=30),
      CODE([[("liste", PL), ("[::-1]", FN)]], "python", delay=0.4, typing=1.0, size=64)),
    S(4.2, T("Örnek", 60, "SB", MUTED, gap=24),
      CODE([[("print", FN), ("([", PL), ("1", NM), (", ", PL), ("2", NM), (", ", PL), ("3", NM), ("][::-1])", PL)],
            [("# ", MUTED), ("[3, 2, 1]", ST)]], "python", delay=0.3, typing=1.6, size=46)),
    S(3.0, T("Daha fazlası için", 70, gap=20), T("@zihinbyte.tr", 80, "B", ACCENT, delay=0.3)),
])

VIDEOS["gun2_reels_git"] = dict(seed=3, bpm=86, scenes=[
    S(3.2, T("Git'te bu 5 komutu biliyor musun?", 96, gap=50), T("Her yazılımcının işine yarar.", 58, "M", ACCENT, delay=0.5)),
    S(3.6, BAD(1), CODE([[("git status", FN)]], "terminal", delay=0.3, typing=0.9, size=56), T("Neyin değiştiğini gör.", 56, "M", MUTED, delay=1.2)),
    S(3.6, BAD(2), CODE([[("git switch -c ", FN), ("yeni-dal", ST)]], "terminal", delay=0.3, typing=1.2, size=50), T("Yeni bir dal aç.", 56, "M", MUTED, delay=1.5)),
    S(3.6, BAD(3), CODE([[("git stash", FN)]], "terminal", delay=0.3, typing=0.9, size=56), T("Yarım işi rafa kaldır.", 56, "M", MUTED, delay=1.2)),
    S(3.8, BAD(4), CODE([[("git restore ", FN), ("dosya.py", ST)]], "terminal", delay=0.3, typing=1.2, size=52), T("Dosyadaki değişikliği geri al.", 56, "M", MUTED, delay=1.5)),
    S(3.8, BAD(5), CODE([[("git log --oneline", FN)]], "terminal", delay=0.3, typing=1.3, size=50), T("Geçmişi tek satırda gör.", 56, "M", MUTED, delay=1.6)),
    cta("Kaydet, terminalde lazım olur."),
])

VIDEOS["gun3_reels_python"] = dict(seed=4, bpm=90, key_shift=-2, scenes=[
    S(3.2, T("Bu 4 Python numarasını biliyor muydun?", 92, gap=50), T("Kodunu kısalt, okunur yap.", 58, "M", ACCENT, delay=0.5)),
    S(4.0, BAD(1), T("f-string", 80, gap=24),
      CODE([[("print", FN), ("(", PL), ("f", K), ("\"Merhaba {isim}\"", ST), (")", PL)]], "python", delay=0.4, typing=1.4, size=44)),
    S(4.0, BAD(2), T("enumerate", 80, gap=24),
      CODE([[("for ", K), ("i, x ", PL), ("in ", K), ("enumerate", FN), ("(liste):", PL)]], "python", delay=0.4, typing=1.6, size=40)),
    S(4.0, BAD(3), T("List comprehension", 76, gap=24),
      CODE([[("[x * ", PL), ("2 ", NM), ("for ", K), ("x ", PL), ("in ", K), ("range", FN), ("(", PL), ("5", NM), (")]", PL)]], "python", delay=0.4, typing=1.6, size=40)),
    S(4.0, BAD(4), T("zip", 80, gap=24),
      CODE([[("for ", K), ("a, b ", PL), ("in ", K), ("zip", FN), ("(l1, l2):", PL)]], "python", delay=0.4, typing=1.4, size=44)),
    cta("Kaydet, sonra dene.", "Daha fazlası: @zihinbyte.tr"),
])

VIDEOS["gun3_story_api"] = dict(seed=5, bpm=84, scenes=[
    S(2.8, CHIP("Teknoloji sözlüğü"), T("API nedir?", 120, gap=30)),
    S(4.2, T("İki yazılımın birbiriyle konuşma kuralları.", 74, gap=40)),
    S(4.6, CHIP("Örnek"), T("Hava durumu uygulaması, hava verisini bir API'den alır.", 60, "M", PL, delay=0.3)),
    S(3.0, T("Sıradaki terim için", 66, gap=20), T("@zihinbyte.tr", 80, "B", ACCENT, delay=0.3)),
])

VIDEOS["gun4_reels_sifre"] = dict(seed=6, bpm=88, scenes=[
    S(3.2, T("Şifren gerçekten güvende mi?", 100, gap=50), T("4 kural, 1 dakika.", 62, "M", ACCENT, delay=0.5)),
    step(1, "Uzun yap", "4 kelimelik bir cümle, kısa karmaşık şifreden güçlüdür."),
    step(2, "Her hesaba ayrı", "Biri sızarsa hepsi gitmesin."),
    step(3, "Parola yöneticisi", "Hepsini aklında tutmak zorunda değilsin."),
    step(4, "İki adımlı doğrulama", "Şifre çalınsa bile kapı kapalı kalsın."),
    cta("Bir arkadaşına gönder.", "Takip et: @zihinbyte.tr"),
])

# ---------------------------------------------------------------- carousels
def slide_cover(title, sub):
    return S(0, CHIP("Kaydırmalı rehber"), T(title, 100, gap=36), T(sub, 54, "M", MUTED))

def slide_tip(n, title, sub):
    return S(0, BAD(n), T(title, 92), T(sub, 54, "M", MUTED))

def slide_end(note=""):
    els = [T("Beğendiysen", 84, gap=16), T("kaydet ve paylaş.", 84, "B", ACCENT, gap=40),
           T("Daha fazlası için takip et:", 52, "M", MUTED, gap=12), T("@zihinbyte.tr", 70, "B", WHITE, gap=40)]
    if note:
        els.append(T(note, 40, "M", MUTED))
    return S(0, *els)

CAROUSELS = {}
CAROUSELS["gun2_carousel_ai_ogrenme"] = [
    slide_cover("AI ile daha iyi öğrenmenin 5 yolu", "Ezber değil, anlayarak çalış."),
    slide_tip(1, "Basit anlattır", "\"Bunu 12 yaşındaki birine anlat\" de."),
    slide_tip(2, "Quiz yaptırt", "10 soru iste, cevapları sonra kontrol et."),
    slide_tip(3, "Özeti önce sen yaz", "Sonra AI ile karşılaştır, eksikleri bul."),
    slide_tip(4, "Yanlışını açıklat", "\"Neden yanlış yaptım?\" diye sor."),
    slide_tip(5, "Plan çıkar", "Sınav tarihini ve günlük süreni söyle."),
    slide_end("Not: AI hata yapabilir, önemli bilgileri kaynaktan doğrula."),
]
CAROUSELS["gun4_carousel_yazilim_yolharitasi"] = [
    slide_cover("Sıfırdan yazılıma başlama yol haritası", "5 adımda net bir plan."),
    slide_tip(1, "Bir dil seç", "Yeni başlayanlar için Python iyi bir başlangıç."),
    slide_tip(2, "Temelleri öğren", "Değişken, döngü, koşul ve fonksiyon."),
    slide_tip(3, "Küçük proje yap", "Hesap makinesi, yapılacaklar listesi."),
    slide_tip(4, "Git ve GitHub", "Kodunu sakla, paylaş, geçmişi takip et."),
    slide_tip(5, "Düzenli pratik", "Kısa ve sık çalışmak, nadir uzun çalışmadan iyidir."),
    slide_end(),
]

# ---------------------------------------------------------------- posts (schedule + captions)
POSTS = [
    dict(key="gun1_reels_prompt", kind="REEL", date="2026-10-08T10:00:00", title="AI'dan daha iyi cevap almanın 4 yolu",
         caption="AI'dan hep ortalama cevap mı alıyorsun? Çoğu zaman sorun modelde değil, isteği nasıl yazdığında. 👇\n\n1️⃣ Rol ver\n2️⃣ Bağlam ver\n3️⃣ Format iste\n4️⃣ Örnek göster\n\nBu 4 adımı alışkanlık haline getir, cevapların kalitesi fark edilir şekilde artar. Sonra lazım olur, kaydet 🔖\n\nSen hangi AI aracını kullanıyorsun? Yorumlara yaz!\n\n#yapayzeka #ai #prompt #promptmühendisliği #teknoloji #yazılım #eğitim #zihinbyte"),
    dict(key="gun1_story_python", kind="STORY", date="2026-10-08T18:00:00", title="Günün Python ipucu: listeyi ters çevir", caption=""),
    dict(key="gun2_reels_git", kind="REEL", date="2026-10-09T10:00:00", title="Git'te 5 temel komut",
         caption="Git'te bu 5 komutu biliyor musun? 👨‍💻\n\n1️⃣ git status\n2️⃣ git switch -c yeni-dal\n3️⃣ git stash\n4️⃣ git restore dosya.py\n5️⃣ git log --oneline\n\nTerminalde her gün işine yarar. Kaydet, lazım olacak 🔖\n\nBunlardan hangisini bilmiyordun? Yorumlara yaz!\n\n#git #github #yazılım #yazılımcı #kodlama #programlama #teknoloji #zihinbyte"),
    dict(key="gun2_carousel_ai_ogrenme", kind="CAROUSEL", date="2026-10-09T18:00:00", title="AI ile daha iyi öğrenmenin 5 yolu",
         caption="AI ile ders çalışmak kopya çekmek değil, doğru kullanınca güçlü bir öğrenme aracı. 📚\n\nKaydırarak 5 yöntemi gör, sonra kaydet 🔖\n\nSen AI'ı ders çalışmak için kullanıyor musun? Yorumlara yaz!\n\n#yapayzeka #eğitim #öğrenme #dersçalışma #üniversite #teknoloji #verimlilik #zihinbyte"),
    dict(key="gun3_reels_python", kind="REEL", date="2026-10-12T10:00:00", title="4 pratik Python numarası",
         caption="Python kodunu kısalt ve okunur yap. 🐍\n\n1️⃣ f-string\n2️⃣ enumerate\n3️⃣ list comprehension\n4️⃣ zip\n\nHangisini daha önce kullandın? Yorumlara yaz, kaydet 🔖\n\n#python #pythonöğren #yazılım #kodlama #programlama #yazılımcı #eğitim #zihinbyte"),
    dict(key="gun3_story_api", kind="STORY", date="2026-10-12T18:00:00", title="Teknoloji sözlüğü: API nedir?", caption=""),
    dict(key="gun4_reels_sifre", kind="REEL", date="2026-10-14T10:00:00", title="Güvenli şifre için 4 kural",
         caption="Şifren gerçekten güvende mi? 🔐\n\n1️⃣ Uzun yap\n2️⃣ Her hesaba ayrı şifre kullan\n3️⃣ Parola yöneticisi kullan\n4️⃣ İki adımlı doğrulamayı aç\n\nBu videoyu bir arkadaşına gönder, o da güvende olsun. Kaydet 🔖\n\n#siberguvenlik #şifre #güvenlik #teknoloji #bilgigüvenliği #internet #zihinbyte"),
    dict(key="gun4_carousel_yazilim_yolharitasi", kind="CAROUSEL", date="2026-10-14T18:00:00", title="Sıfırdan yazılıma başlama yol haritası",
         caption="Yazılıma nereden başlayacağını bilmiyor musun? 👨‍💻\n\n5 adımlık net bir yol haritası hazırladım. Kaydır, kaydet 🔖\n\nŞu an hangi aşamadasın? Yorumlara yaz!\n\n#yazılım #yazılımöğren #kodlama #programlama #python #yolharitası #eğitim #zihinbyte"),
]
