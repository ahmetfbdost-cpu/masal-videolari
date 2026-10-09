#!/usr/bin/env python3
"""
trpulseit LinkedIn görsel üretici.
Kullanım:  python3 render_post_image.py spec.json cikti.png
spec.json örnekleri:
  {"template":"hook","kicker":"SİBER GÜVENLİK","title":"Şifreniz sızdı mı? Muhtemelen haberiniz bile yok.","subtitle":"İşletmeler için 3 dakikalık kontrol"}
  {"template":"checklist","kicker":"KONTROL LİSTESİ","title":"Yedekleriniz gerçekten işe yarar mı?","items":["...","..."],"numbered":false}
  {"template":"question","kicker":"SİZE SORUYORUZ","title":"Şirketinizde BT sorunu çıkınca ilk kimi arıyorsunuz?","subtitle":"Cevabınızı yorumlarda paylaşın"}
  {"template":"compare","kicker":"MALİYET","title":"Reaktif mi, proaktif mi?","left_title":"Arıza olunca","left_items":["..."],"right_title":"Önceden önlem","right_items":["..."]}
Boyut: 1080x1350 (LinkedIn için 4:5 dikey).
Logo: linkedin/arac/logo.png (veya .svg/.jpg) varsa otomatik kullanılır; yoksa "TrPulseIT" yazı logosu.
Alt sağ köşe: "footer" alanı (varsayılan www.trpulseit.com).
"""
import json, sys, html, base64, os
from playwright.sync_api import sync_playwright

W, H = 1080, 1350
NAVY, NAVY2, CYAN, WHITE, MUTED = "#0A1428", "#12244A", "#22D3EE", "#F5F8FC", "#9FB3CF"

PULSE = f"""<svg class="pulse" viewBox="0 0 1080 120" preserveAspectRatio="none">
<polyline points="0,60 360,60 400,60 425,20 455,105 485,8 515,95 540,60 1080,60"
 fill="none" stroke="{CYAN}" stroke-width="5" stroke-linejoin="round" stroke-linecap="round"/></svg>"""

CHECK = f"""<svg viewBox="0 0 24 24" width="44" height="44"><circle cx="12" cy="12" r="11" fill="{CYAN}"/>
<path d="M7 12.5l3.2 3.2L17 9" fill="none" stroke="{NAVY}" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></svg>"""

def e(s): return html.escape(str(s or ""))

def body(spec):
    t = spec.get("template", "hook")
    kicker = f'<div class="kicker">{e(spec.get("kicker"))}</div>' if spec.get("kicker") else ""
    if t == "checklist":
        num = spec.get("numbered")
        lis = "".join(
            f'<li><span class="ic">{(f"<b class=n>{i+1}</b>") if num else CHECK}</span><span>{e(x)}</span></li>'
            for i, x in enumerate(spec.get("items", [])[:7]))
        return f'{kicker}<h1 class="fit mid">{e(spec.get("title"))}</h1><ul class="list">{lis}</ul>'
    if t == "question":
        sub = f'<p class="sub">{e(spec.get("subtitle"))}</p>' if spec.get("subtitle") else ""
        return f'{kicker}<div class="q">?</div><h1 class="fit big">{e(spec.get("title"))}</h1>{sub}'
    if t == "compare":
        def col(title, items, cls):
            return f'<div class="col {cls}"><h3>{e(title)}</h3><ul>' + "".join(f"<li>{e(x)}</li>" for x in items[:5]) + "</ul></div>"
        return (f'{kicker}<h1 class="fit mid">{e(spec.get("title"))}</h1><div class="cmp">'
                + col(spec.get("left_title"), spec.get("left_items", []), "bad")
                + col(spec.get("right_title"), spec.get("right_items", []), "good") + "</div>")
    sub = f'<p class="sub">{e(spec.get("subtitle"))}</p>' if spec.get("subtitle") else ""
    return f'{kicker}<h1 class="fit big">{e(spec.get("title"))}</h1>{sub}'

CSS = f"""
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{W}px;height:{H}px}}
body{{font-family:Inter,'Inter Display','DejaVu Sans',Arial,sans-serif;color:{WHITE};
 background:radial-gradient(1200px 900px at 85% -10%,{NAVY2} 0%,{NAVY} 60%);overflow:hidden;position:relative}}
.grid{{position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,.035) 1px,transparent 1px),
 linear-gradient(90deg,rgba(255,255,255,.035) 1px,transparent 1px);background-size:54px 54px}}
.wrap{{position:absolute;left:96px;right:96px;top:120px;bottom:250px;display:flex;flex-direction:column;justify-content:center}}
.kicker{{display:inline-block;align-self:flex-start;font-weight:700;font-size:28px;letter-spacing:.14em;color:{CYAN};
 border:2px solid {CYAN};border-radius:999px;padding:12px 26px;margin-bottom:44px}}
h1{{font-weight:800;line-height:1.12;letter-spacing:-.02em}}
h1.big{{font-size:92px}} h1.mid{{font-size:66px;margin-bottom:46px}}
.sub{{margin-top:40px;font-size:38px;color:{MUTED};line-height:1.35;font-weight:500}}
.q{{font-size:220px;font-weight:900;color:{CYAN};line-height:.9;margin-bottom:20px}}
.list{{list-style:none;display:flex;flex-direction:column;gap:26px}}
.list li{{display:flex;gap:26px;align-items:flex-start;font-size:38px;line-height:1.3;font-weight:500}}
.ic{{flex:0 0 44px;margin-top:2px}}
.n{{display:inline-flex;width:44px;height:44px;border-radius:50%;background:{CYAN};color:{NAVY};font-size:26px;
 align-items:center;justify-content:center;font-weight:800}}
.cmp{{display:flex;gap:28px}}
.col{{flex:1;border-radius:24px;padding:36px 34px;background:rgba(255,255,255,.05);border:2px solid rgba(255,255,255,.12)}}
.col.good{{border-color:{CYAN};background:rgba(34,211,238,.08)}}
.col h3{{font-size:36px;margin-bottom:22px}} .col.good h3{{color:{CYAN}}} .col.bad h3{{color:#FCA5A5}}
.col ul{{list-style:none;display:flex;flex-direction:column;gap:18px}} .col li{{font-size:31px;line-height:1.3;color:#DCE6F2}}
.pulse{{position:absolute;left:0;right:0;bottom:150px;width:100%;height:120px;opacity:.9}}
.foot{{position:absolute;left:96px;right:96px;bottom:62px;display:flex;justify-content:space-between;align-items:center}}
.brand{{font-weight:800;font-size:44px;letter-spacing:-.01em;display:flex;align-items:center}} .brand b{{color:{CYAN}}}
.brand img{{max-height:84px;max-width:420px;object-fit:contain}}
.tag{{font-size:26px;color:{MUTED};font-weight:500}}
"""

FIT_JS = """
() => { const w=document.querySelector('.wrap');
  for(const h of document.querySelectorAll('h1.fit')){ let s=parseFloat(getComputedStyle(h).fontSize);
    while(w.scrollHeight>w.clientHeight+2 && s>34){ s-=2; h.style.fontSize=s+'px'; } }
  const lis=document.querySelectorAll('.list li, .col li'); let f=lis.length?parseFloat(getComputedStyle(lis[0]).fontSize):0;
  while(lis.length && w.scrollHeight>w.clientHeight+2 && f>22){ f-=1; lis.forEach(l=>l.style.fontSize=f+'px'); }
  return w.scrollHeight<=w.clientHeight+2; }
"""

HERE = os.path.dirname(os.path.abspath(__file__))
def brand_html():
    """linkedin/arac/ altında logo.png / logo.svg / logo.jpg varsa onu kullan, yoksa yazı logosu."""
    for name, mime in (("logo.png","image/png"),("logo.svg","image/svg+xml"),("logo.jpg","image/jpeg")):
        f = os.path.join(HERE, name)
        if os.path.exists(f):
            data = base64.b64encode(open(f,"rb").read()).decode()
            return f'<img src="data:{mime};base64,{data}" alt="TrPulseIT">'
    return "Tr<b>Pulse</b>IT"

def render(spec, out):
    page_html = f"""<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head>
<body><div class="grid"></div><div class="wrap">{body(spec)}</div>{PULSE}
<div class="foot"><div class="brand">{brand_html()}</div><div class="tag">{e(spec.get("footer","www.trpulseit.com"))}</div></div></body></html>"""
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": W, "height": H})
        pg.set_content(page_html, wait_until="load")
        fits = pg.evaluate(FIT_JS)
        pg.screenshot(path=out, type="png")
        b.close()
    print("OK" if fits else "WARN: metin alana tam sığmadı, kısaltın", out)

if __name__ == "__main__":
    render(json.load(open(sys.argv[1], encoding="utf-8")), sys.argv[2])
