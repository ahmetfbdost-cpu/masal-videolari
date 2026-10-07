"""Masal için karakter ve arka plan çizimleri (Pillow, 2x süper örnekleme)."""
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

SS = 2  # süper örnekleme katsayısı
OUT = (60, 38, 30, 255)  # çizgi rengi (koyu kahve)
OW = 5  # çizgi kalınlığı (1x)


def hexc(h, a=255):
    h = h.lstrip('#')
    if len(h) == 8:
        a = int(h[6:8], 16)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (a,)


class Pen:
    """1x koordinatlarla çizer, içeride SS katı çözünürlükte tutar."""

    def __init__(self, w, h, bg=(0, 0, 0, 0)):
        self.w, self.h = w, h
        self.img = Image.new('RGBA', (w * SS, h * SS), bg)
        self.d = ImageDraw.Draw(self.img)

    def s(self, v):
        return v * SS

    def pts(self, pts):
        return [(x * SS, y * SS) for x, y in pts]

    def ell(self, cx, cy, rx, ry, fill, outline=OUT, ow=OW, angle=0):
        if angle == 0:
            self.d.ellipse([(cx - rx) * SS, (cy - ry) * SS, (cx + rx) * SS, (cy + ry) * SS],
                           fill=fill, outline=outline, width=int(ow * SS) if outline else 0)
        else:
            self.poly(ellipse_pts(cx, cy, rx, ry, angle), fill, outline, ow)

    def circ(self, cx, cy, r, fill, outline=OUT, ow=OW):
        self.ell(cx, cy, r, r, fill, outline, ow)

    def poly(self, pts, fill, outline=OUT, ow=OW):
        p = self.pts(pts)
        self.d.polygon(p, fill=fill)
        if outline:
            self.d.line(p + [p[0]], fill=outline, width=int(ow * SS), joint='curve')

    def line(self, pts, fill=OUT, w=OW):
        p = self.pts(pts)
        self.d.line(p, fill=fill, width=int(w * SS), joint='curve')
        r = w * SS / 2
        for x, y in (p[0], p[-1]):
            self.d.ellipse([x - r, y - r, x + r, y + r], fill=fill)

    def arc(self, cx, cy, rx, ry, a0, a1, fill=OUT, w=OW):
        pts = [(cx + rx * math.cos(math.radians(a)), cy + ry * math.sin(math.radians(a)))
               for a in np.linspace(a0, a1, 24)]
        self.line(pts, fill, w)

    def rect(self, x0, y0, x1, y1, fill, outline=OUT, ow=OW, r=0):
        self.d.rounded_rectangle([x0 * SS, y0 * SS, x1 * SS, y1 * SS], radius=r * SS, fill=fill,
                                 outline=outline, width=int(ow * SS) if outline else 0)

    def done(self):
        return self.img.resize((self.w, self.h), Image.LANCZOS)


def ellipse_pts(cx, cy, rx, ry, angle=0, n=72):
    a = math.radians(angle)
    out = []
    for i in range(n):
        t = 2 * math.pi * i / n
        x, y = rx * math.cos(t), ry * math.sin(t)
        out.append((cx + x * math.cos(a) - y * math.sin(a), cy + x * math.sin(a) + y * math.cos(a)))
    return out


def glow(r, color=(255, 230, 120), power=2.0):
    """Yumuşak ışık halesi sprite'ı."""
    size = int(r * 2)
    yy, xx = np.mgrid[0:size, 0:size]
    d = np.sqrt((xx - r) ** 2 + (yy - r) ** 2) / r
    a = np.clip(1 - d, 0, 1) ** power
    arr = np.zeros((size, size, 4), np.uint8)
    arr[..., 0], arr[..., 1], arr[..., 2] = color
    arr[..., 3] = (a * 255).astype(np.uint8)
    return Image.fromarray(arr, 'RGBA')


# ---------------------------------------------------------------- KARAKTERLER

def eye(p, x, y, r, mood):
    if mood == 'blink' or mood == 'happy':
        p.arc(x, y + (2 if mood == 'blink' else 4), r, r * 0.7, 200 if mood == 'happy' else 10,
              340 if mood == 'happy' else 170, OUT, 4.5)
        return
    if mood == 'scared':
        p.circ(x, y, r * 1.45, hexc('#FFFFFF'), OUT, 3.5)
        p.circ(x, y + 2, r * 0.75, hexc('#2A1B14'), None)
        p.circ(x - r * 0.25, y - r * 0.2, r * 0.3, hexc('#FFFFFF'), None)
        return
    p.circ(x, y, r, hexc('#2A1B14'), None)
    p.circ(x - r * 0.3, y - r * 0.35, r * 0.38, hexc('#FFFFFF'), None)
    p.circ(x + r * 0.3, y + r * 0.35, r * 0.15, hexc('#FFFFFF'), None)


def hedgehog(mood='normal'):
    """Fındık – sağa bakar. 380x300."""
    p = Pen(380, 300)
    spike = hexc('#7A4A2E')
    spike_d = hexc('#5C3520')
    cx, cy = 165, 175
    L = 62 if mood == 'scared' else 48
    # dikenler: arka sırt boyunca üçgenler
    for row, (rad, col, ln) in enumerate([(120, spike_d, L + 8), (105, spike, L)]):
        for a in np.linspace(150, 375, 19 if row == 0 else 17):
            ar = math.radians(a + (6 if row else 0))
            bx, by = cx + rad * 0.92 * math.cos(ar), cy + rad * 0.72 * math.sin(ar)
            tx, ty = cx + (rad + ln) * math.cos(ar), cy + (rad * 0.72 + ln) * math.sin(ar)
            nx, ny = -math.sin(ar) * 17, math.cos(ar) * 17
            p.poly([(bx + nx, by + ny), (tx, ty), (bx - nx, by - ny)], col, OUT, 3.5)
    # gövde
    p.ell(cx, cy + 10, 118, 88, hexc('#8E5B3A'))
    # yüz
    face = hexc('#F1CFA6')
    p.ell(cx + 82, cy + 22, 70, 58, face)
    p.ell(cx + 128, cy + 34, 52, 30, face, angle=8)
    p.ell(cx + 108, cy + 28, 52, 46, face, None)  # birleştirme
    p.circ(cx + 176, cy + 36, 13, hexc('#2A1B14'), None)  # burun
    p.circ(cx + 172, cy + 32, 4, hexc('#6E5A50'), None)
    # kulak
    p.circ(cx + 52, cy - 34, 18, face)
    p.circ(cx + 52, cy - 34, 9, hexc('#E9A3A0'), None)
    # yanak
    p.ell(cx + 110, cy + 52, 15, 9, hexc('#F29C94', 190), None)
    eye(p, cx + 100, cy + 4, 12, mood)
    # ağız
    if mood == 'scared':
        p.ell(cx + 140, cy + 60, 9, 11, hexc('#5C2B22'), OUT, 3)
    else:
        p.arc(cx + 140, cy + 52, 16, 10 if mood != 'happy' else 13, 20, 160, OUT, 4)
    # ayaklar
    for fx in (cx - 55, cx + 50):
        p.ell(fx, cy + 96, 24, 13, hexc('#5C3520'))
    return p.done()


def rabbit(mood='normal'):
    """Pamuk – sağa bakar. 300x430."""
    p = Pen(300, 430)
    white, pink = hexc('#FBF8F3'), hexc('#F4B6B8')
    ear_tilt = 0 if mood != 'scared' else 1
    # kulaklar
    for ex, ang in ((132, -12 - 8 * ear_tilt), (182, 10 + 8 * ear_tilt)):
        p.ell(ex, 92, 24, 78, white, angle=ang)
        p.ell(ex, 98, 11, 56, pink, None, angle=ang)
    # kuyruk
    p.circ(62, 330, 30, white)
    # gövde
    p.ell(140, 318, 88, 92, white)
    p.ell(150, 330, 50, 56, hexc('#F1ECE4'), None)
    # baş
    p.ell(160, 200, 78, 70, white)
    eye(p, 192, 190, 12, mood)
    p.ell(232, 210, 10, 7, pink)  # burun
    p.ell(200, 228, 15, 9, hexc('#F7A9A6', 180), None)
    if mood == 'scared':
        p.ell(222, 240, 7, 9, hexc('#5C2B22'), OUT, 3)
    else:
        p.arc(222, 228, 12, 9 if mood != 'happy' else 12, 20, 160, OUT, 4)
    # bıyık
    for dy in (-6, 6):
        p.line([(238, 214 + dy), (268, 208 + dy * 2)], hexc('#B9A89A'), 2.5)
    # kol ve ayaklar
    p.ell(198, 300, 18, 30, white, angle=-20)
    for fx in (100, 185):
        p.ell(fx, 404, 34, 16, white)
    return p.done()


def firefly(mood='normal'):
    """Işıl – minicik ateşböceği. 130x110 (ışık ayrı çizilir)."""
    p = Pen(130, 110)
    wing = hexc('#E8F4FF', 170)
    p.ell(58, 30, 22, 30, wing, hexc('#7FA6C9'), 3, angle=-25)
    p.ell(82, 32, 20, 28, wing, hexc('#7FA6C9'), 3, angle=20)
    p.ell(48, 68, 26, 22, hexc('#FFE45C'), OUT, 4)  # parlayan kuyruk
    p.ell(78, 62, 22, 19, hexc('#4B3A63'), OUT, 4)  # gövde
    p.circ(100, 54, 17, hexc('#5B4876'))
    eye(p, 106, 50, 5, mood)
    p.arc(106, 60, 6, 4, 20, 160, hexc('#FFFFFF'), 2.5)
    p.line([(104, 38), (112, 18)], OUT, 3)
    p.circ(113, 16, 4, hexc('#FFE45C'), None)
    return p.done()


def turtle(mood='normal'):
    """Bilge Nine – yaşlı kaplumbağa, gözlüklü. 520x330."""
    p = Pen(520, 330)
    skin = hexc('#A8C98F')
    for lx in (120, 300):  # bacaklar
        p.ell(lx, 270, 34, 30, skin)
    # kabuk
    p.d.pieslice([40 * SS, 60 * SS, 400 * SS, 400 * SS], 180, 360, fill=hexc('#5E9A57'),
                 outline=OUT, width=OW * SS)
    p.rect(30, 222, 410, 258, hexc('#C9B27A'), r=18)
    for (x, y, r) in [(220, 140, 40), (140, 185, 30), (300, 185, 30), (220, 70 + 30, 0)]:
        if r:
            p.ell(x, y, r * 1.2, r, hexc('#7DB574'), hexc('#3F6E3C'), 4)
    # baş
    p.ell(410, 226, 46, 28, skin)
    p.ell(450, 200, 58, 50, skin)
    p.ell(412, 226, 40, 22, skin, None)
    eye(p, 462, 190, 9, mood if mood != 'scared' else 'normal')
    # gözlük
    p.circ(462, 192, 21, None, hexc('#3B3B3B'), 4)
    p.line([(441, 190), (412, 182)], hexc('#3B3B3B'), 3.5)
    p.arc(478, 222, 16, 9, 20, 160, OUT, 4)
    p.ell(486, 212, 10, 6, hexc('#F29C94', 170), None)
    # kaşlar (beyaz, yaşlı)
    p.line([(450, 166), (476, 162)], hexc('#E8E8E8'), 5)
    return p.done()


def owl():
    p = Pen(200, 240)
    body = hexc('#8C6A4F')
    p.poly([(52, 50), (40, 10), (82, 40)], body)
    p.poly([(148, 50), (160, 10), (118, 40)], body)
    p.ell(100, 130, 80, 98, body)
    p.ell(100, 160, 52, 60, hexc('#D9C2A0'), None)
    for ex in (70, 130):
        p.circ(ex, 92, 30, hexc('#FFF6DC'))
        eye(p, ex, 94, 12, 'normal')
    p.poly([(92, 112), (108, 112), (100, 130)], hexc('#F2B544'))
    for fx in (78, 122):
        p.ell(fx, 226, 16, 9, hexc('#F2B544'))
    return p.done()


def squirrel():
    p = Pen(230, 240)
    fur = hexc('#D9783A')
    p.ell(60, 120, 56, 100, fur, angle=-15)  # kuyruk
    p.ell(70, 110, 30, 70, hexc('#E99A5E'), None, angle=-15)
    p.ell(140, 170, 52, 60, fur)
    p.circ(155, 95, 46, fur)
    p.poly([(130, 60), (128, 30), (150, 52)], fur)
    p.poly([(170, 58), (182, 30), (186, 62)], fur)
    p.ell(150, 186, 30, 36, hexc('#F6D5B0'), None)
    eye(p, 170, 88, 8, 'normal')
    p.circ(198, 104, 6, hexc('#2A1B14'), None)
    p.arc(186, 112, 9, 6, 20, 160, OUT, 3.5)
    p.ell(176, 108, 9, 6, hexc('#F29C94', 170), None)
    return p.done()


def frog():
    p = Pen(200, 150)
    g = hexc('#6CC24A')
    p.ell(100, 100, 82, 46, g)
    for ex in (62, 138):
        p.circ(ex, 52, 26, g)
        p.circ(ex, 52, 15, hexc('#FFFFFF'), None)
        eye(p, ex, 54, 8, 'normal')
    p.arc(100, 102, 34, 14, 15, 165, OUT, 4)
    p.ell(60, 110, 10, 6, hexc('#F29C94', 170), None)
    p.ell(140, 110, 10, 6, hexc('#F29C94', 170), None)
    return p.done()


def bird(color='#5DA9E9'):
    p = Pen(150, 120)
    c = hexc(color)
    p.ell(70, 70, 50, 40, c)
    p.ell(60, 78, 30, 20, hexc('#FFFFFF', 200), None)
    p.ell(50, 62, 26, 18, c, angle=-25)
    p.poly([(116, 64), (140, 70), (116, 78)], hexc('#F2B544'))
    eye(p, 96, 58, 7, 'normal')
    return p.done()


def butterfly(color='#F28FB2'):
    p = Pen(90, 70)
    c = hexc(color)
    p.ell(28, 26, 22, 18, c, OUT, 3, angle=-20)
    p.ell(62, 26, 22, 18, c, OUT, 3, angle=20)
    p.ell(30, 50, 14, 12, c, OUT, 3)
    p.ell(60, 50, 14, 12, c, OUT, 3)
    p.ell(45, 38, 5, 22, hexc('#4B3A63'), None)
    return p.done()


def music_note():
    p = Pen(70, 90)
    c = hexc('#FFF2B3')
    p.ell(22, 70, 16, 12, c, OUT, 3, angle=-20)
    p.line([(36, 66), (36, 12)], OUT, 5)
    p.line([(36, 12), (58, 24)], OUT, 6)
    return p.done()


def apple():
    p = Pen(110, 120)
    p.circ(55, 70, 42, hexc('#E5484D'))
    p.ell(40, 56, 10, 14, hexc('#FF9A9C', 180), None, angle=-20)
    p.line([(55, 32), (60, 12)], hexc('#5C3520'), 6)
    p.ell(76, 20, 18, 9, hexc('#6CC24A'), OUT, 3, angle=-20)
    return p.done()


# ---------------------------------------------------------------- ARKA PLAN

def vgrad(w, h, stops):
    """stops: [(pos, '#hex'), ...] dikey renk geçişi."""
    ys = np.linspace(0, 1, h)
    cols = np.zeros((h, 3))
    pos = [s[0] for s in stops]
    rgb = [np.array(hexc(s[1])[:3], float) for s in stops]
    for ch in range(3):
        cols[:, ch] = np.interp(ys, pos, [c[ch] for c in rgb])
    arr = np.repeat(cols[:, None, :], w, axis=1).astype(np.uint8)
    a = np.full((h, w, 1), 255, np.uint8)
    return Image.fromarray(np.concatenate([arr, a], 2), 'RGBA')


class BG(Pen):
    def __init__(self, w, h, sky):
        super().__init__(w, h)
        self.img.paste(vgrad(w * SS, h * SS, sky))
        self.d = ImageDraw.Draw(self.img)
        self.rng = random.Random(7)

    def stars(self, n=90, ymax=0.55):
        for _ in range(n):
            x, y = self.rng.uniform(0, self.w), self.rng.uniform(0, self.h * ymax)
            r = self.rng.uniform(1.2, 3.2)
            self.circ(x, y, r, hexc('#FFF8E1', self.rng.randint(150, 255)), None)

    def hill(self, y, amp, col, seed=0, freq=1.0, outline=None):
        pts = [(0, self.h)]
        for x in np.linspace(0, self.w, 120):
            yy = y - amp * (0.6 * math.sin(x / self.w * math.pi * 2 * freq + seed)
                            + 0.4 * math.sin(x / self.w * math.pi * 5 * freq + seed * 2))
            pts.append((x, yy))
        pts.append((self.w, self.h))
        self.poly(pts, hexc(col) if isinstance(col, str) else col, outline, 4)

    def tree(self, x, base, h, trunk='#7A5034', leaves=('#4E9A51', '#5FB15E', '#3F8445'), scale=1.0,
             outline=OUT):
        tw = 22 * scale
        self.rect(x - tw, base - h, x + tw, base + 6, hexc(trunk), outline, 4, r=6)
        r = 70 * scale
        cy = base - h
        blobs = [(-0.9, 0.2, 0.75), (0.9, 0.2, 0.75), (0, -0.45, 0.95), (-0.5, -0.1, 0.8),
                 (0.5, -0.1, 0.8), (0, 0.15, 0.85)]
        for i, (dx, dy, rr) in enumerate(blobs):
            self.circ(x + dx * r, cy + dy * r, rr * r, hexc(leaves[i % len(leaves)]), outline, 4)

    def pine(self, x, base, h, col='#2F6B4F', outline=OUT):
        for i in range(3):
            w = h * (0.42 - i * 0.09)
            yb = base - h * (0.18 + i * 0.25)
            self.poly([(x - w, yb), (x, yb - h * 0.42), (x + w, yb)], hexc(col), outline, 4)
        self.rect(x - 10, base - h * 0.18, x + 10, base, hexc('#5C3B28'), outline, 4)

    def flowers(self, n, y0, y1, cols=('#FFFFFF', '#FFD84D', '#F7A1C4')):
        for _ in range(n):
            x, y = self.rng.uniform(0, self.w), self.rng.uniform(y0, y1)
            c = hexc(self.rng.choice(cols))
            for k in range(5):
                a = k * 2 * math.pi / 5
                self.circ(x + 7 * math.cos(a), y + 7 * math.sin(a), 6, c, None)
            self.circ(x, y, 4.5, hexc('#F2B544'), None)

    def grass(self, n, y0, y1, col):
        for _ in range(n):
            x, y = self.rng.uniform(0, self.w), self.rng.uniform(y0, y1)
            self.line([(x, y), (x - 6, y - 18)], hexc(col), 3)
            self.line([(x + 6, y), (x + 9, y - 16)], hexc(col), 3)

    def moon(self, x, y, r, face=True):
        g = glow(r * 2.6 * SS, (255, 246, 210), 1.8)
        self.img.alpha_composite(g, (int((x - r * 2.6) * SS), int((y - r * 2.6) * SS)))
        self.circ(x, y, r, hexc('#FFF4C7'), hexc('#E8D9A0'), 4)
        self.circ(x - r * 0.35, y - r * 0.2, r * 0.14, hexc('#F0E2AE'), None)
        self.circ(x + r * 0.3, y + r * 0.35, r * 0.1, hexc('#F0E2AE'), None)
        if face:
            self.arc(x - r * 0.3, y - r * 0.02, r * 0.13, r * 0.09, 200, 340, hexc('#B79F6A'), 4)
            self.arc(x + r * 0.3, y - r * 0.02, r * 0.13, r * 0.09, 200, 340, hexc('#B79F6A'), 4)
            self.arc(x, y + r * 0.25, r * 0.25, r * 0.15, 20, 160, hexc('#B79F6A'), 4)

    def oak_home(self, x, base, h, night=False, window_light=True):
        trunk = '#6E4A30' if not night else '#4A3628'
        self.poly([(x - 120, base), (x - 95, base - h), (x + 95, base - h), (x + 130, base)],
                  hexc(trunk), OUT, 5)
        for rx in (-60, 10, 60):  # kabuk çizgileri
            self.line([(x + rx, base - 40), (x + rx + 8, base - h + 60)], hexc('#00000033'), 4)
        # kökler
        self.poly([(x - 150, base + 10), (x - 110, base - 50), (x - 80, base + 10)], hexc(trunk), OUT, 5)
        self.poly([(x + 160, base + 10), (x + 115, base - 50), (x + 90, base + 10)], hexc(trunk), OUT, 5)
        # taç
        leaves = ('#4E9A51', '#5FB15E', '#3F8445') if not night else ('#2E5A45', '#386B52', '#264C3B')
        for i, (dx, dy, r) in enumerate([(-230, -10, 150), (230, -10, 150), (0, -120, 200), (-120, -60, 170),
                                         (120, -60, 170), (0, 20, 160)]):
            self.circ(x + dx, base - h + dy, r, hexc(leaves[i % 3]), OUT, 5)
        # kapı
        self.d.chord([(x - 52) * SS, (base - 150) * SS, (x + 52) * SS, (base - 46) * SS], 180, 360,
                     fill=hexc('#B5703E'), outline=OUT, width=OW * SS)
        self.rect(x - 52, base - 100, x + 52, base, hexc('#B5703E'), OUT, 5)
        self.d.rectangle([(x - 49) * SS, (base - 104) * SS, (x + 49) * SS, (base - 96) * SS], fill=hexc('#B5703E'))
        self.circ(x + 30, base - 50, 7, hexc('#F2B544'), OUT, 3)
        # pencere
        wl = hexc('#FFD77A') if window_light else hexc('#3A3550')
        self.circ(x + 10, base - h + 150, 44, hexc('#8A5A36'), OUT, 5)
        self.circ(x + 10, base - h + 150, 32, wl, OUT, 4)
        # yaprak yığını
        for i in range(14):
            lx = x - 220 + i * 34 + self.rng.uniform(-8, 8)
            self.ell(lx, base + 12, 30, 16, hexc(self.rng.choice(['#E39B3A', '#D9783A', '#C8553D', '#F2B544'])),
                     OUT, 3, angle=self.rng.uniform(-30, 30))


def cloud(w, h, col='#B8BCCB', dark='#9EA3B5'):
    p = Pen(w, h)
    rng = random.Random(w + h)
    blobs = [(0.2, 0.66, 0.17), (0.38, 0.52, 0.22), (0.6, 0.5, 0.23), (0.8, 0.64, 0.16), (0.5, 0.7, 0.2)]
    for bx, by, br in blobs:
        p.circ(bx * w, by * h, br * w * 0.75, hexc(dark), None)
    for bx, by, br in blobs:
        p.circ(bx * w, by * h - 6, br * w * 0.72, hexc(col), None)
    return p.done()


def hedgehog_ball():
    """Korkudan top olmuş Fındık."""
    p = Pen(300, 300)
    cx, cy = 150, 160
    for i, a in enumerate(np.linspace(0, 360, 26, endpoint=False)):
        ar = math.radians(a)
        rad, ln = 100, 46
        bx, by = cx + rad * 0.95 * math.cos(ar), cy + rad * 0.95 * math.sin(ar)
        tx, ty = cx + (rad + ln) * math.cos(ar), cy + (rad + ln) * math.sin(ar)
        nx, ny = -math.sin(ar) * 15, math.cos(ar) * 15
        p.poly([(bx + nx, by + ny), (tx, ty), (bx - nx, by - ny)], hexc('#6B3F26' if i % 2 else '#7A4A2E'),
               OUT, 3.5)
    p.circ(cx, cy, 104, hexc('#8E5B3A'))
    p.ell(cx + 40, cy + 40, 40, 30, hexc('#F1CFA6'))
    eye(p, cx + 40, cy + 36, 9, 'scared')
    p.circ(cx + 76, cy + 50, 9, hexc('#2A1B14'), None)
    return p.done()


def moon_sprite(r, wink=False, face=True):
    size = int(r * 5.2)
    p = Pen(size, size)
    c = size / 2
    g = glow(r * 2.6 * SS, (255, 246, 210), 1.8)
    p.img.alpha_composite(g, (0, 0))
    p.circ(c, c, r, hexc('#FFF4C7'), hexc('#E8D9A0'), 4)
    p.circ(c - r * 0.35, c - r * 0.2, r * 0.14, hexc('#F0E2AE'), None)
    p.circ(c + r * 0.3, c + r * 0.35, r * 0.1, hexc('#F0E2AE'), None)
    if face:
        col = hexc('#B79F6A')
        p.arc(c - r * 0.3, c - r * 0.02, r * 0.13, r * 0.09, 200, 340, col, 4)
        if wink:
            p.line([(c + r * 0.18, c - r * 0.02), (c + r * 0.42, c - r * 0.02)], col, 4)
        else:
            p.arc(c + r * 0.3, c - r * 0.02, r * 0.13, r * 0.09, 200, 340, col, 4)
        p.arc(c, c + r * 0.25, r * 0.25, r * 0.15, 20, 160, col, 4)
        p.ell(c - r * 0.45, c + r * 0.2, r * 0.1, r * 0.06, hexc('#F6B9A0', 150), None)
        p.ell(c + r * 0.45, c + r * 0.2, r * 0.1, r * 0.06, hexc('#F6B9A0', 150), None)
    return p.done()


def shadow_monster(w=520, h=560):
    p = Pen(w, h)
    c = (12, 10, 28, 235)
    p.ell(w / 2, h * 0.62, w * 0.3, h * 0.36, c, None)
    p.circ(w / 2, h * 0.28, w * 0.2, c, None)
    p.poly([(w * 0.36, h * 0.2), (w * 0.3, h * 0.0), (w * 0.46, h * 0.14)], c, None)
    p.poly([(w * 0.64, h * 0.2), (w * 0.7, h * 0.0), (w * 0.54, h * 0.14)], c, None)
    p.line([(w * 0.28, h * 0.5), (w * 0.08, h * 0.32), (w * 0.0, h * 0.4)], c, 26)
    p.line([(w * 0.72, h * 0.5), (w * 0.92, h * 0.3), (w * 1.0, h * 0.36)], c, 26)
    p.circ(w * 0.44, h * 0.27, 9, hexc('#F7E27A'), None)
    p.circ(w * 0.56, h * 0.27, 9, hexc('#F7E27A'), None)
    return p.done().filter(ImageFilter.GaussianBlur(3))


def bush_and_stump(p, x, base):
    """Işıkta görünen böğürtlen çalısı ve kütük (BG üzerine)."""
    for dx, dy, r, col in [(-60, -90, 80, '#3F7A4E'), (40, -120, 95, '#4C8C59'), (130, -80, 75, '#3F7A4E'),
                           (40, -40, 90, '#55995F')]:
        p.circ(x + dx, base + dy, r, hexc(col), OUT, 4)
    for bx, by in [(-40, -120), (20, -170), (80, -90), (120, -140), (-10, -60), (60, -40)]:
        p.circ(x + bx, base + by, 11, hexc('#5B2A6E'), OUT, 3)
    p.line([(x - 90, base - 150), (x - 150, base - 230)], hexc('#5C3B28'), 10)
    p.line([(x + 150, base - 140), (x + 210, base - 220)], hexc('#5C3B28'), 10)
    p.rect(x + 200, base - 110, x + 300, base + 10, hexc('#7A5034'), OUT, 5, r=10)
    p.ell(x + 250, base - 110, 50, 16, hexc('#C9A57A'), OUT, 4)
