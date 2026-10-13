"""Şablon tabanlı sahne üretici.

Her masal için `scenes.py` dosyasını elle yeniden yazmak yerine, masal klasöründeki
`sahne_plani.json` dosyasından sahneleri otomatik kurar. Bu sayede masalı yazan model
(Claude veya GitHub Models) yalnızca kısıtlı bir sözlükten seçim yapar, kod yazmaz.

sahne_plani.json biçimi:
{
  "baslik": "Minik Kirpi Fındık", "alt_baslik": "ve Kayıp Ay Işığı",
  "karakterler": {"Fındık": "kirpi", "Pamuk": "tavsan", "Işıl": "ates_bocegi"},
  "ana_karakter": "Fındık",
  "sahneler": [   # tam 12 sahne
    {"mekan": "yuva", "zaman": "gunduz",
     "karakterler": [{"ad": "Fındık", "duygu": "normal>mutlu"}],
     "efektler": ["kelebekler"], "hareket": "dur"},
    ...
  ]
}
Sözlük: MEKANLAR, ZAMANLAR, TURLER, DUYGULAR, EFEKTLER (aşağıda).
"""
import json, random
from PIL import Image, ImageOps
import art
from art import BG, hexc

W, H = 2040, 1148

MEKANLAR = {
    'yuva': 'büyük meşe ağacının dibindeki yuva',
    'cayir': 'çiçekli açık çayır',
    'orman': 'sık ağaçlı orman patikası',
    'dere': 'üzerinde kütük köprü olan dere',
    'tepe': 'büyük çınar ağaçlı tepe',
    'gol': 'nilüferli küçük göl kıyısı',
}
ZAMANLAR = ('gunduz', 'aksam', 'gece')
TURLER = {
    'kirpi': 'hedgehog', 'tavsan': 'rabbit', 'ates_bocegi': 'firefly', 'kaplumbaga': 'turtle',
    'baykus': 'owl', 'sincap': 'squirrel', 'kurbaga': 'frog', 'kus': 'bird', 'kelebek': 'butterfly',
}
MOODY = {'hedgehog', 'rabbit', 'firefly', 'turtle'}
DUYGULAR = {'normal': 'normal', 'mutlu': 'happy', 'korkmus': 'scared', 'uzgun': 'scared', 'saskin': 'scared'}
EFEKTLER = ('ay', 'ay_bulutlu', 'gunes', 'ates_bocekleri', 'muzik', 'kelebekler', 'kuslar', 'bulutlar', 'elmalar',
            'yildiz_kaymasi')
FLYERS = {'firefly', 'bird', 'butterfly'}
SCALE = {'hedgehog': 0.85, 'rabbit': 0.8, 'turtle': 0.72, 'owl': 0.8, 'squirrel': 0.75, 'frog': 0.75,
         'bird': 0.7, 'butterfly': 1.0, 'firefly': 0.85}
BIRD_COLORS = ['#5DA9E9', '#F2B544', '#E9736B', '#8BC48A']
BUTTERFLY_COLORS = ['#F28FB2', '#B79CED', '#F7C548', '#7FD1C7']

PAL = {
    'gunduz': dict(sky=[(0, '#8FD3F4'), (0.55, '#CDEBF5'), (1, '#FFE6B8')], far='#9ED38A', mid='#7CC36B',
                   near='#6AB35A', grass='#4F9A45', leaves=('#4E9A51', '#5FB15E', '#3F8445'), pine='#2F6B4F',
                   water='#5BB2E0', ripple='#D6F0FF', path='#C9B48A', flowers=('#FFFFFF', '#FFD84D', '#F7A1C4')),
    'aksam': dict(sky=[(0, '#2E2B6B'), (0.45, '#7D5BA6'), (0.8, '#F2A07B'), (1, '#F7C98B')], far='#4E6E8E',
                  mid='#46705E', near='#3F6E58', grass='#2F5A45', leaves=('#3E6F5C', '#4A7F67', '#365F50'),
                  pine='#26483D', water='#5A6FA8', ripple='#F2C1A0', path='#7D6E78',
                  flowers=('#F3D9E6', '#F7C98B', '#E7A3C3')),
    'gece': dict(sky=[(0, '#0E1233'), (0.6, '#24305E'), (1, '#33406F')], far='#1E2C48', mid='#22403A',
                 near='#1F3A33', grass='#2A4C40', leaves=('#2F5E45', '#386B52', '#264F3B'), pine='#16302D',
                 water='#2E5C8A', ripple='#7FB3E0', path='#4A4A5E', flowers=('#D8D8F0', '#C8C0E8', '#B8C8E8')),
}

_cache = {}


def sprite(name, scale=1.0, flip=False, mood='normal', color=None):
    key = (name, scale, flip, mood, color)
    if key not in _cache:
        fn = getattr(art, name)
        if name in MOODY:
            im = fn(mood)
        elif color and name in ('bird', 'butterfly'):
            im = fn(color)
        else:
            im = fn()
        if scale != 1.0:
            im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
        if flip:
            im = ImageOps.mirror(im)
        _cache[key] = im
    return _cache[key]


def L(img, x, y, **kw):
    d = dict(img=img, x=x, y=y)
    d.update(kw)
    return d


# ------------------------------------------------------------------ arka planlar
_bg_cache = {}


def background(mekan, zaman, seed=0):
    k = (mekan, zaman, seed)
    if k in _bg_cache:
        return _bg_cache[k]
    c = PAL[zaman]
    night = zaman == 'gece'
    b = BG(W, H, c['sky'])
    if zaman != 'gunduz':
        b.stars(110 if night else 40, 0.5 if night else 0.35)
    else:
        b.circ(1650, 210, 90, hexc('#FFE27A'), None)
    b.hill(760, 60, c['far'], 2 + seed, 0.8)
    if mekan == 'yuva':
        for x in (130, 1880):
            if night:
                b.pine(x, 820, 380, c['pine'])
            else:
                b.tree(x, 780, 170, leaves=c['leaves'], scale=0.85)
        b.hill(860, 40, c['mid'], 3 + seed, 1.1)
        b.oak_home(1250, 980, 470, night=night, window_light=zaman != 'gunduz')
        b.hill(1000, 25, c['near'], 5, 1.4)
        b.flowers(40, 900, 1130, c['flowers'])
        b.grass(110, 900, 1140, c['grass'])
    elif mekan == 'cayir':
        for x in (120, 520, 1560, 1950):
            b.tree(x, 760, 160, leaves=c['leaves'], scale=0.75)
        b.hill(840, 40, c['mid'], 3 + seed, 1.1)
        b.hill(980, 25, c['near'], 5 + seed, 1.4)
        b.flowers(110, 860, 1130, c['flowers'])
        b.grass(130, 860, 1140, c['grass'])
    elif mekan == 'orman':
        for i, x in enumerate(range(-40, 2100, 170)):
            b.pine(x, 760 + (i % 2) * 30, 420 + (i % 3) * 60, c['pine'])
        b.poly([(0, 1148), (0, 900), (700, 820), (1300, 840), (2040, 880), (2040, 1148)], hexc(c['near']), None)
        b.poly([(560, 1148), (900, 860), (1140, 860), (1480, 1148)], hexc(c['path']), None)
        b.grass(60, 900, 1140, c['grass'])
    elif mekan == 'dere':
        for x in range(-40, 2100, 210):
            if night:
                b.pine(x, 720, 360, c['pine'])
            else:
                b.tree(x, 740, 150, leaves=c['leaves'], scale=0.7)
        b.poly([(0, 1148), (0, 760), (2040, 760), (2040, 1148)], hexc(c['near']), None)
        b.poly([(0, 900), (2040, 880), (2040, 1040), (0, 1060)], hexc(c['water']), None)
        rng = random.Random(3 + seed)
        for _ in range(40):
            x, y = rng.uniform(0, 2000), rng.uniform(905, 1030)
            b.line([(x, y), (x + rng.uniform(30, 70), y)], hexc(c['ripple'], 160), 3)
        b.grass(60, 780, 880, c['grass'])
        b.grass(30, 1070, 1140, c['grass'])
        b.rect(380, 930, 1660, 975, hexc('#7A5034'), art.OUT, 5, r=22)
        for x in (380, 1660):
            b.ell(x, 952, 16, 24, hexc('#C9A57A'), art.OUT, 4)
        for x in range(480, 1600, 160):
            b.line([(x, 945), (x + 60, 945)], hexc('#5C3B28'), 3)
    elif mekan == 'tepe':
        b.poly([(0, 1148), (0, 900), (500, 760), (1100, 700), (1700, 760), (2040, 860), (2040, 1148)],
               hexc(c['mid']), art.OUT, 5)
        x, base = 1350, 760
        b.poly([(x - 70, base + 10), (x - 50, base - 330), (x + 50, base - 330), (x + 80, base + 10)],
               hexc('#8C7660'), art.OUT, 5)
        lv = c['leaves']
        for dx, dy, r, col in [(-260, -380, 170, lv[2]), (250, -380, 170, lv[2]), (0, -520, 220, lv[1]),
                               (-140, -430, 180, lv[0]), (140, -430, 180, lv[0]), (0, -360, 170, lv[2])]:
            b.circ(x + dx, base + dy, r, hexc(col), art.OUT, 5)
        b.grass(80, 800, 1140, c['grass'])
        b.flowers(25, 860, 1130, c['flowers'])
    elif mekan == 'gol':
        for x in (100, 400, 1700, 1980):
            if night:
                b.pine(x, 800, 360, c['pine'])
            else:
                b.tree(x, 780, 160, leaves=c['leaves'], scale=0.8)
        b.hill(840, 30, c['mid'], 4 + seed, 1.0)
        b.ell(1020, 900, 760, 120, hexc(c['water']), art.OUT, 5)
        rng = random.Random(7 + seed)
        for _ in range(26):
            x, y = rng.uniform(380, 1660), rng.uniform(830, 960)
            b.line([(x, y), (x + rng.uniform(25, 60), y)], hexc(c['ripple'], 150), 3)
        for x, y in [(700, 880), (1180, 930), (1450, 860), (900, 960)]:
            b.ell(x, y, 46, 18, hexc('#5FA35A'), art.OUT, 3)
            b.circ(x + 6, y - 10, 11, hexc('#F7A1C4'), art.OUT, 3)
        b.poly([(0, 1148), (0, 1000), (2040, 990), (2040, 1148)], hexc(c['near']), None)
        b.grass(90, 1000, 1140, c['grass'])
    out = b.done()
    _bg_cache[k] = out
    return out


# ------------------------------------------------------------------ yardımcılar

def parse_mood(s):
    """'korkmus>mutlu' -> [('scared',0), ('happy',0.5)]"""
    parts = [p.strip() for p in str(s or 'normal').split('>') if p.strip()] or ['normal']
    n = len(parts)
    return [(DUYGULAR.get(p, 'normal'), 0 if i == 0 else round(0.2 + 0.6 * i / n, 2)) for i, p in enumerate(parts)]


def char_layer(species, x, y, moods, flip, s, walk=None, idx=0):
    name = TURLER[species]
    s = s * SCALE[name]
    color = None
    if name == 'bird':
        color = BIRD_COLORS[idx % len(BIRD_COLORS)]
    if name == 'butterfly':
        color = BUTTERFLY_COLORS[idx % len(BUTTERFLY_COLORS)]
    if name in MOODY:
        imgs = [(p, sprite(name, s, flip, m), m) for m, p in moods]
    else:
        im = sprite(name, s, flip, color=color)
        imgs = [(0, im, 'normal')]
    kw = {}
    if name in FLYERS:
        kw['bob'] = (16, 1.2 + 0.2 * idx)
        kw['z'] = 12
        if name == 'firefly':
            kw['light'] = 150
        y = y - 420 - (idx % 2) * 60
        path = [(0, x - 60, y), (0.5, x + 60, y - 40), (1, x - 20, y)]
    else:
        kw['bob'] = (5, 2.2 + 0.3 * idx)
        path = None
    if walk:
        path = [(0, x + walk[0], y), (1, x + walk[1], y)]
    d = L(imgs[0][1], x, y, swaps=imgs, **kw)
    if name == 'hedgehog':
        d['blink'] = sprite(name, s, flip, 'blink')
    if path:
        d['path'] = path
    return d


def clouds_over(cx, cy, cover_p, start_dx=900):
    c1 = art.cloud(520, 260, '#7E8199', '#5F6280')
    c2 = art.cloud(440, 220, '#8A8DA6', '#6A6D8B')
    return [
        L(c1, cx + start_dx, cy + 150, path=[(0, cx + start_dx, cy + 150), (cover_p, cx - 40, cy + 150)], z=5),
        L(c2, cx + start_dx + 300, cy + 190, path=[(0, cx + start_dx + 300, cy + 190), (cover_p, cx + 120, cy + 190)],
          z=6),
    ]


def ground_y(mekan):
    return {'dere': 940, 'tepe': 1030, 'gol': 1070, 'orman': 1030}.get(mekan, 1010)


def effects(efs, zaman, mekan, sc, layers, ana_species=None):
    for e in efs:
        if e == 'ay':
            layers.append(L(art.moon_sprite(85), 520, 520, z=1))
            if zaman != 'gunduz':
                sc['moonlight'] = [(0, 0.2), (1, 0.2)]
        elif e == 'ay_bulutlu':
            layers.append(L(art.moon_sprite(85), 560, 480, z=1))
            layers.extend(clouds_over(560, 380, 0.45))
            sc['darken'] = [(0, 0), (0.25, 0), (0.55, 0.4), (1, 0.45)]
        elif e == 'gunes' and zaman == 'gunduz':
            pass  # güneş zaten arka planda
        elif e == 'ates_bocekleri':
            sc['fireflies'] = (40, 0.05)
        elif e == 'muzik':
            sc['notes'] = (0.1, 0.85)
        elif e == 'kelebekler':
            for i, (x0, x1, yy) in enumerate([(300, 1000, 700), (1800, 1300, 620)]):
                layers.append(L(sprite('butterfly', 0.9, color=BUTTERFLY_COLORS[i]), x0, yy,
                                path=[(0, x0, yy + 60), (0.5, (x0 + x1) / 2, yy - 60), (1, x1, yy + 40)],
                                bob=(30, 1.1 + i * 0.2), z=12))
        elif e == 'kuslar':
            for i in range(2):
                layers.append(L(sprite('bird', 0.6 - i * 0.08, True, color=BIRD_COLORS[i]), 2100 + i * 300, 300,
                                path=[(0, 2100 + i * 300, 300 + i * 50), (1, -100 + i * 200, 260 + i * 40)],
                                bob=(16, 0.9 + i * 0.1), z=12))
        elif e == 'bulutlar':
            cl = ('#FFFFFF', '#DDE6F0') if zaman == 'gunduz' else ('#6E7190', '#55587A')
            for i in range(3):
                layers.append(L(art.cloud(520, 260, *cl), 300 + i * 650, 330, z=5,
                                path=[(0, 300 + i * 650, 330 + (i % 2) * 40), (1, 380 + i * 650, 330 + (i % 2) * 40)]))
        elif e == 'elmalar':
            for i in range(3):
                layers.append(L(sprite('apple', 0.9), 700 + i * 300, 0, z=12,
                                path=[(0, 700 + i * 300, -100 - i * 60),
                                      (0.35 + i * 0.12, 700 + i * 300, 560 + (i % 2) * 40)]))
        elif e == 'yildiz_kaymasi' and zaman != 'gunduz':
            star = art.glow(30, (255, 250, 220), 2.2)
            layers.append(L(star, 1900, 200, z=12, path=[(0, 1900, 150), (0.3, 1300, 380)], show=(0, 0.02, 0.28, 0.32)))


def build_scene(spec, chars, idx, ana):
    mekan = spec.get('mekan') if spec.get('mekan') in MEKANLAR else 'cayir'
    zaman = spec.get('zaman') if spec.get('zaman') in ZAMANLAR else 'gunduz'
    bg = background(mekan, zaman)
    gy = ground_y(mekan)
    cs = [c for c in spec.get('karakterler', []) if c.get('ad') in chars][:5]
    # ana karakter ortaya yakın
    cs.sort(key=lambda c: 0 if c.get('ad') == ana else 1)
    n = len(cs)
    slots = {1: [960], 2: [820, 1180], 3: [700, 1000, 1320], 4: [520, 820, 1140, 1460],
             5: [440, 740, 1040, 1340, 1640]}.get(n, [])
    if mekan == 'yuva':  # yuvanın kapısını kapatmasınlar
        slots = [x - 260 if x > 700 else x - 120 for x in slots]
    walk = spec.get('hareket') == 'yuru'
    layers = []
    ground_i = 0
    for i, c in enumerate(cs):
        species = chars[c['ad']]
        x = slots[i]
        flip = x > 1000 and i > 0  # sağdakiler sola baksın (sprite'lar sağa bakıyor)
        name = TURLER[species]
        s = 1.0 if c.get('ad') == ana else 0.92
        if mekan == 'dere' and name not in FLYERS:
            s *= 0.85
        wk = None
        if walk and name not in FLYERS:
            wk = (-220, 160) if not flip else (220, -160)
        layers.append(char_layer(species, x, gy + (i % 2) * 14, parse_mood(c.get('duygu')), flip, s, wk, i))
        ground_i += 1
    sc = dict(bg=bg, layers=layers)
    dark = {'gunduz': 0, 'aksam': 0.08, 'gece': 0.18}[zaman]
    try:
        dark = float(spec.get('karanlik', dark))
    except (TypeError, ValueError):
        pass
    if dark > 0.01:
        sc['darken'] = [(0, min(0.5, dark)), (1, min(0.5, dark))]
    effects(spec.get('efektler', []), zaman, mekan, sc, layers)
    return sc


def build(plan):
    if isinstance(plan, str):
        plan = json.load(open(plan, encoding='utf-8'))
    chars = {k: v for k, v in plan['karakterler'].items() if v in TURLER}
    ana = plan.get('ana_karakter') or next(iter(chars))
    scenes = plan['sahneler']
    assert len(scenes) == 12, 'sahne_plani.json tam 12 sahne içermeli'
    S = {}
    for i, sp in enumerate(scenes, 1):
        S[i] = build_scene(sp, chars, i, ana)
    # açılış: ilk sahnenin mekanı, ana karakter büyük ve mutlu
    first = scenes[0]
    z0 = first.get('zaman') if first.get('zaman') in ZAMANLAR else 'gunduz'
    m0 = first.get('mekan') if first.get('mekan') in MEKANLAR else 'cayir'
    t_layers = [char_layer(chars[ana], 1000, ground_y(m0), [('happy', 0)], False, 1.35)]
    if z0 != 'gunduz':
        t_layers.insert(0, L(art.moon_sprite(90), 1680, 760, z=1))
    S['title'] = dict(bg=background(m0, z0), layers=t_layers, title=True)
    # kapanış: tüm karakterler mutlu, elmalar düşer
    names = list(chars)[:5]
    end_spec = dict(mekan=scenes[-1].get('mekan', 'yuva'), zaman='gece',
                    karakterler=[{'ad': n, 'duygu': 'mutlu'} for n in names], efektler=['elmalar'], karanlik=0.1)
    S['end'] = build_scene(end_spec, chars, 13, ana)
    S['end']['end'] = True
    S['end']['layers'].insert(0, L(art.moon_sprite(90), 1680, 700, z=1))
    return S
