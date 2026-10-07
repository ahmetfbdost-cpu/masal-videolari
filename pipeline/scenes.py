"""Sahne tanımları: arka plan + hareketli katmanlar."""
import math, random
from PIL import Image, ImageOps
import art
from art import BG, hexc

W, H = 2040, 1148  # arka plan (kaydırma payı ile)

_cache = {}


def sprite(name, scale=1.0, flip=False, mood='normal'):
    key = (name, scale, flip, mood)
    if key not in _cache:
        fn = getattr(art, name)
        im = fn(mood) if name in ('hedgehog', 'rabbit', 'firefly', 'turtle') else fn()
        if scale != 1.0:
            im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
        if flip:
            im = ImageOps.mirror(im)
        _cache[key] = im
    return _cache[key]


def L(img, x, y, **kw):
    """Katman: x,y = alt-orta nokta (bg koordinatı)."""
    d = dict(img=img, x=x, y=y)
    d.update(kw)
    return d


def hedge(x, y, flip=False, s=0.85, moods=(('normal', 0),), **kw):
    imgs = [(p, sprite('hedgehog', s, flip, m), m) for m, p in moods]
    kw.setdefault('bob', (5, 2.4))
    return L(imgs[0][1], x, y, swaps=imgs, blink=sprite('hedgehog', s, flip, 'blink'), **kw)


def rab(x, y, flip=False, s=0.8, moods=(('normal', 0),), **kw):
    imgs = [(p, sprite('rabbit', s, flip, m), m) for m, p in moods]
    kw.setdefault('bob', (6, 2.0))
    return L(imgs[0][1], x, y, swaps=imgs, **kw)


def isil(path, s=0.9, flip=False, **kw):
    x, y = path[0][1], path[0][2]
    kw.setdefault('light', 150)
    return L(sprite('firefly', s, flip), x, y, path=path, bob=(14, 1.3), z=12, **kw)


# ------------------------------------------------------------------ arka planlar

def bg_day():
    b = BG(W, H, [(0, '#8FD3F4'), (0.55, '#CDEBF5'), (1, '#FFE6B8')])
    b.circ(1650, 220, 90, hexc('#FFE27A'), None)
    b.hill(700, 60, '#9ED38A', 1, 0.7)
    for x in (120, 420, 1700, 1950):
        b.tree(x, 720, 160, scale=0.8)
    b.hill(820, 40, '#7CC36B', 3, 1.1)
    b.oak_home(1300, 940, 470, window_light=False)
    b.hill(980, 25, '#6AB35A', 5, 1.4)
    b.flowers(70, 840, 1130)
    b.grass(120, 860, 1140, '#4F9A45')
    return b.done()


def bg_dusk():
    b = BG(W, H, [(0, '#2E2B6B'), (0.45, '#7D5BA6'), (0.8, '#F2A07B'), (1, '#F7C98B')])
    b.stars(40, 0.35)
    b.hill(760, 60, '#4E6E8E', 2, 0.8)
    for x in (150, 1850):
        b.tree(x, 790, 170, leaves=('#3E6F5C', '#4A7F67', '#365F50'), scale=0.85)
    b.oak_home(1200, 980, 470)
    b.hill(1000, 25, '#3F6E58', 5, 1.4)
    b.grass(90, 900, 1140, '#2F5A45')
    return b.done()


def bg_night(home=True, window=True, stars=True):
    b = BG(W, H, [(0, '#0E1233'), (0.6, '#24305E'), (1, '#33406F')])
    if stars:
        b.stars(110, 0.5)
    b.hill(760, 60, '#1E2C48', 2, 0.8)
    for x in (130, 1880):
        b.pine(x, 820, 380, '#1C3A35')
    if home:
        b.oak_home(1150, 990, 470, night=True, window_light=window)
    b.hill(1010, 25, '#1F3A33', 5, 1.4)
    b.grass(80, 920, 1140, '#2A4C40')
    return b.done()


def bg_path():
    b = BG(W, H, [(0, '#0B0F2C'), (0.7, '#1D2750'), (1, '#24305A')])
    b.stars(70, 0.4)
    for i, x in enumerate(range(-40, 2100, 170)):
        b.pine(x, 760 + (i % 2) * 30, 420 + (i % 3) * 60, '#152B2A')
    b.poly([(0, 1148), (0, 900), (700, 820), (1300, 840), (2040, 880), (2040, 1148)], hexc('#1E3A33'), None)
    b.poly([(500, 1148), (880, 860), (1160, 860), (1500, 1148)], hexc('#4A4A5E'), None)  # patika
    for i, x in enumerate(range(-60, 2100, 260)):
        b.pine(x, 1148, 300 + (i % 2) * 120, '#0E201F')
    return b.done()


def bg_stream():
    b = BG(W, H, [(0, '#0C1132'), (0.6, '#1F2A55'), (1, '#24305A')])
    b.stars(90, 0.45)
    for x in range(-40, 2100, 210):
        b.pine(x, 720, 360, '#16302D')
    b.poly([(0, 1148), (0, 760), (2040, 760), (2040, 1148)], hexc('#1E3A33'), None)
    # dere
    b.poly([(0, 900), (2040, 880), (2040, 1040), (0, 1060)], hexc('#2E5C8A'), None)
    rng = random.Random(3)
    for _ in range(40):
        x, y = rng.uniform(0, 2000), rng.uniform(905, 1030)
        b.line([(x, y), (x + rng.uniform(30, 70), y)], hexc('#7FB3E0', 160), 3)
    b.grass(60, 780, 880, '#2F5A45')
    b.grass(30, 1070, 1140, '#2F5A45')
    # kütük köprü
    b.rect(380, 930, 1660, 975, hexc('#7A5034'), art.OUT, 5, r=22)
    for x in (380, 1660):
        b.ell(x, 952, 16, 24, hexc('#C9A57A'), art.OUT, 4)
    for x in range(480, 1600, 160):
        b.line([(x, 945), (x + 60, 945)], hexc('#5C3B28'), 3)
    return b.done()


def bg_bush():
    b = BG(W, H, [(0, '#0B0F2C'), (0.7, '#1D2750'), (1, '#24305A')])
    b.stars(60, 0.35)
    for x in range(-40, 2100, 230):
        b.pine(x, 760, 380, '#152B2A')
    b.poly([(0, 1148), (0, 840), (2040, 820), (2040, 1148)], hexc('#1E3A33'), None)
    b.poly([(0, 1148), (0, 1000), (2040, 960), (2040, 1148)], hexc('#3E4458'), None)
    art.bush_and_stump(b, 1300, 900)
    return b.done()


def bg_hill(moon_hidden=True):
    b = BG(W, H, [(0, '#0E1233'), (0.6, '#24305E'), (1, '#33406F')])
    b.stars(100, 0.45)
    b.hill(800, 40, '#1E2C48', 1, 0.6)
    b.poly([(0, 1148), (0, 900), (500, 760), (1100, 700), (1700, 760), (2040, 860), (2040, 1148)],
           hexc('#28513F'), art.OUT, 5)
    # çınar
    x, base = 1350, 760
    b.poly([(x - 70, base + 10), (x - 50, base - 330), (x + 50, base - 330), (x + 80, base + 10)],
           hexc('#8C7660'), art.OUT, 5)
    for dx, dy, r, c in [(-260, -380, 170, '#2F5E45'), (250, -380, 170, '#2F5E45'), (0, -520, 220, '#386B52'),
                         (-140, -430, 180, '#3F7559'), (140, -430, 180, '#3F7559'), (0, -360, 170, '#336349')]:
        b.circ(x + dx, base + dy, r, hexc(c), art.OUT, 5)
    b.grass(80, 800, 1140, '#3A6B52')
    b.flowers(25, 860, 1130, ('#D8D8F0', '#C8C0E8'))
    return b.done()


# ------------------------------------------------------------------ sahneler

def clouds_over(cx, cy, cover_p, start_dx=900):
    c1 = art.cloud(520, 260, '#7E8199', '#5F6280')
    c2 = art.cloud(440, 220, '#8A8DA6', '#6A6D8B')
    return [
        L(c1, cx + start_dx, cy + 150, path=[(0, cx + start_dx, cy + 150), (cover_p, cx - 40, cy + 150)], z=5),
        L(c2, cx + start_dx + 300, cy + 190, path=[(0, cx + start_dx + 300, cy + 190), (cover_p, cx + 120, cy + 190)],
          z=6),
    ]


def build():
    S = {}
    S['title'] = dict(bg=bg_night(home=False), layers=[
        L(art.moon_sprite(90), 1680, 760),
        hedge(1020, 980, s=1.25, moods=(('happy', 0),)),
        isil([(0, 700, 520), (0.25, 1300, 420), (0.5, 1350, 700), (0.75, 760, 760), (1, 700, 520)], s=1.0),
    ], title=True)
    S[1] = dict(bg=bg_day(), layers=[
        hedge(820, 1000, moods=(('normal', 0), ('happy', 0.6))),
        L(sprite('butterfly', 0.9), 500, 700, path=[(0, 300, 760), (0.5, 700, 620), (1, 1000, 760)], bob=(30, 1.1)),
        L(sprite('butterfly', 0.8), 1700, 600, path=[(0, 1800, 640), (0.5, 1500, 760), (1, 1700, 560)], bob=(25, 1.3)),
        L(sprite('bird', 0.7, True), 2000, 300, path=[(0, 2100, 300), (1, -100, 260)], bob=(18, 0.9)),
        L(sprite('bird', 0.6, True), 2200, 360, path=[(0, 2400, 360), (1, 100, 330)], bob=(14, 1.0)),
    ])
    S[2] = dict(bg=bg_dusk(), layers=[
        L(art.moon_sprite(80), 420, 420, show=(0.45, 0.6)),
        hedge(700, 1010, flip=True, moods=(('normal', 0), ('scared', 0.3), ('normal', 0.55), ('happy', 0.82))),
    ], darken=[(0, 0), (0.3, 0.0), (0.55, 0.25), (1, 0.2)])
    S[3] = dict(bg=bg_night(), layers=[
        L(art.moon_sprite(85), 560, 480, z=1),
        *clouds_over(560, 380, 0.42),
        hedge(820, 1010, flip=True, moods=(('normal', 0), ('scared', 0.45)), show=(0, 0, 0.8, 0.84)),
        L(art.hedgehog_ball(), 820, 1010, show=(0.82, 0.88), bob=(4, 0.5)),
    ], darken=[(0, 0), (0.25, 0), (0.5, 0.45), (1, 0.5)])
    S[4] = dict(bg=bg_night(window=True), layers=[
        rab(600, 1000, moods=(('scared', 0),), bob=(5, 0.35)),
        hedge(1160, 1005, flip=True, moods=(('scared', 0), ('normal', 0.25)), show=(0.2, 0.28)),
    ], darken=[(0, 0.35), (1, 0.35)])
    S[5] = dict(bg=bg_path(), layers=[
        hedge(820, 1020, moods=(('scared', 0), ('normal', 0.45), ('happy', 0.62)),
              path=[(0, 820, 1020), (0.86, 820, 1020), (1, 1000, 1000)]),
        rab(560, 1020, moods=(('scared', 0), ('normal', 0.4), ('happy', 0.85)),
            path=[(0, 560, 1020), (0.86, 560, 1020), (1, 760, 1000)]),
    ], darken=[(0, 0.15), (1, 0.15)])
    S[6] = dict(bg=bg_path(), layers=[
        hedge(1060, 1030, moods=(('scared', 0), ('normal', 0.5), ('happy', 0.75))),
        rab(800, 1030, moods=(('scared', 0), ('normal', 0.55), ('happy', 0.8))),
        isil([(0, 1900, 300), (0.18, 1900, 300), (0.35, 1400, 560), (0.55, 1180, 620), (0.85, 1000, 560),
              (1, 1300, 520)], show=(0.18, 0.22)),
    ], darken=[(0, 0.3), (0.3, 0.3), (0.5, 0.1), (1, 0.05)])
    S[7] = dict(bg=bg_stream(), layers=[
        hedge(500, 940, s=0.7, moods=(('normal', 0), ('happy', 0.85)),
              path=[(0, 300, 940), (0.42, 480, 945), (0.82, 1620, 945), (1, 1760, 900)]),
        rab(330, 940, s=0.66, moods=(('scared', 0), ('normal', 0.6), ('happy', 0.85)),
            path=[(0, 160, 900), (0.46, 300, 940), (0.85, 1440, 945), (1, 1560, 900)]),
        isil([(0, 700, 500), (0.4, 600, 600), (0.82, 1600, 600), (1, 1700, 560)], s=0.8),
    ])
    S[8] = dict(bg=bg_bush(), layers=[
        L(art.shadow_monster(), 1340, 960, show=(0, 0, 0.42, 0.52), z=2),
        hedge(520, 1040, moods=(('scared', 0), ('happy', 0.55), ('normal', 0.8))),
        rab(260, 1030, moods=(('scared', 0), ('happy', 0.55))),
        isil([(0, 650, 560), (0.36, 650, 560), (0.46, 1300, 520), (0.7, 1250, 560), (1, 800, 520)], s=0.85,
             light_boost=[(0.4, 150), (0.5, 330), (0.75, 330), (0.9, 160)]),
    ], darken=[(0, 0.4), (0.4, 0.4), (0.52, 0.05), (1, 0.05)])
    S[9] = dict(bg=bg_hill(), layers=[
        L(sprite('turtle', 0.8, True), 1600, 960),
        hedge(820, 1030, moods=(('normal', 0), ('happy', 0.25), ('normal', 0.45)), s=0.75),
        rab(560, 1020, moods=(('normal', 0), ('happy', 0.25)), s=0.7),
        isil([(0, 700, 600), (1, 1000, 620)], s=0.8),
        *[L(art.cloud(560, 280, '#6E7190', '#55587A'), 400 + i * 600, 340, z=5,
            path=[(0, 400 + i * 600, 340), (1, 440 + i * 600, 340)]) for i in range(3)],
    ])
    gather = [
        L(sprite('turtle', 0.7, True), 1250, 960),
        hedge(820, 1040, moods=(('happy', 0),), s=0.7),
        rab(560, 1030, moods=(('happy', 0),), s=0.66),
        L(sprite('squirrel', 0.7), 1620, 1050, bob=(10, 1.4)),
        L(sprite('frog', 0.7), 330, 1080, bob=(8, 1.1)),
        L(sprite('bird', 0.6), 1800, 1060, bob=(8, 0.9)),
        L(sprite('bird', 0.55, False), 1470, 1080, bob=(6, 1.0)),
        L(sprite('frog', 0.6, True), 1900, 1090, bob=(7, 1.2)),
    ]
    S[10] = dict(bg=bg_hill(), layers=gather[:3] + [
        isil([(0, 900, 600), (1, 1100, 560)], s=0.8),
        L(sprite('squirrel', 0.7), 1620, 1050, show=(0.25, 0.32), bob=(10, 1.4)),
        L(sprite('frog', 0.7), 330, 1080, show=(0.3, 0.36), bob=(8, 1.1)),
        L(sprite('bird', 0.6), 1800, 1060, show=(0.35, 0.4), bob=(8, 0.9)),
        L(sprite('frog', 0.6, True), 1900, 1090, show=(0.4, 0.45), bob=(7, 1.2)),
        L(sprite('owl', 0.75), 1350, 560, path=[(0, 1350, 420), (0.62, 1350, 420), (0.78, 1450, 1060)],
          show=(0.58, 0.64), bob=(4, 2)),
        *[L(art.cloud(560, 280, '#6E7190', '#55587A'), 400 + i * 600, 340, z=5) for i in range(3)],
    ], fireflies=(40, 0.08))
    S[11] = dict(bg=bg_hill(), layers=[
        L(art.moon_sprite(95), 1020, 560, z=1),
        L(art.cloud(620, 300, '#6E7190', '#55587A'), 760, 470, z=5, path=[(0, 760, 470), (0.35, 760, 470), (0.75, -300, 420)]),
        L(art.cloud(620, 300, '#6E7190', '#55587A'), 1280, 470, z=5, path=[(0, 1280, 470), (0.35, 1280, 470), (0.75, 2400, 420)]),
        *[dict(g, jump=0.8) for g in gather],
        L(sprite('owl', 0.75), 1450, 1060, bob=(4, 2)),
    ], fireflies=(40, 0), notes=(0.0, 0.7), darken=[(0, 0.35), (0.4, 0.35), (0.75, 0.0), (1, 0)],
        moonlight=[(0.4, 0), (0.8, 0.35)])
    S[12] = dict(bg=bg_night(window=True), layers=[
        L(art.moon_sprite(90), 520, 520, swaps=[(0, art.moon_sprite(90), 'm'), (0.58, art.moon_sprite(90, wink=True), 'm'),
                                                (0.64, art.moon_sprite(90), 'm')]),
        hedge(860, 1010, flip=True, moods=(('happy', 0), ('normal', 0.3), ('happy', 0.62))),
        isil([(0, 1000, 640), (1, 1200, 600)], s=0.8),
    ], moonlight=[(0, 0.25), (1, 0.25)])
    S['end'] = dict(bg=bg_night(home=False), layers=[
        L(art.moon_sprite(90), 1680, 760),
        hedge(760, 1000, moods=(('happy', 0),), s=1.0),
        rab(500, 1000, moods=(('happy', 0),), s=0.9),
        isil([(0, 1100, 560), (0.5, 1250, 640), (1, 1100, 560)], s=0.9),
        L(sprite('turtle', 0.7, True), 1350, 1000),
    ] + [L(sprite('apple', 0.9), 700 + i * 300, 0, path=[(0, 700 + i * 300, -100 - i * 60), (0.35 + i * 0.12, 700 + i * 300, 560 + (i % 2) * 40)])
         for i in range(3)], end=True)
    return S
