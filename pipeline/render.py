"""Kare kare sahne birleştirici ve video üretici."""
import math, json, random, sys, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import art, scenes

FW, FH = 1920, 1080
FPS = 24
FONT_B = '/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf'
FONT_S = '/usr/share/fonts/opentype/inter/InterDisplay-SemiBold.otf'
TITLE = 'Minik Kirpi Fındık'
SUBTITLE = 've Kayıp Ay Işığı'


def smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def interp(keys, p):
    """keys: [(p, v...)] -> değer (yumuşak geçiş)."""
    if p <= keys[0][0]:
        return keys[0][1:]
    for a, b in zip(keys, keys[1:]):
        if a[0] <= p <= b[0]:
            u = smooth((p - a[0]) / max(1e-6, b[0] - a[0]))
            return tuple(x + (y - x) * u for x, y in zip(a[1:], b[1:]))
    return keys[-1][1:]


def paste(dst, src, x, y, alpha=1.0):
    x, y = int(round(x)), int(round(y))
    sx0, sy0 = max(0, -x), max(0, -y)
    sx1, sy1 = min(src.width, dst.width - x), min(src.height, dst.height - y)
    if sx1 <= sx0 or sy1 <= sy0 or alpha <= 0.01:
        return
    piece = src.crop((sx0, sy0, sx1, sy1)) if (sx0 or sy0 or sx1 < src.width or sy1 < src.height) else src
    if alpha < 0.99:
        a = np.asarray(piece).copy()
        a[..., 3] = (a[..., 3] * alpha).astype(np.uint8)
        piece = Image.fromarray(a, 'RGBA')
    dst.alpha_composite(piece, (x + sx0, y + sy0))


_glows = {}


def glow(r, col=(255, 228, 120), power=2.2):
    r = int(max(8, r // 10 * 10))
    k = (r, col, power)
    if k not in _glows:
        _glows[k] = art.glow(r, col, power)
    return _glows[k]


def show_alpha(show, p):
    if not show:
        return 1.0
    a = smooth((p - show[0]) / max(1e-6, show[1] - show[0])) if show[1] > show[0] else (1.0 if p >= show[0] else 0)
    if len(show) == 4:
        a *= 1 - smooth((p - show[2]) / max(1e-6, show[3] - show[2]))
    return a


def wrap(text, font, maxw, draw):
    words, lines, cur = text.split(), [], ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if draw.textlength(t, font=font) <= maxw:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


_subs = {}


def subtitle_img(text):
    if text in _subs:
        return _subs[text]
    font = ImageFont.truetype(FONT_S, 46)
    tmp = ImageDraw.Draw(Image.new('RGBA', (10, 10)))
    lines = wrap(text, font, 1500, tmp)
    lh = 60
    w = int(max(tmp.textlength(l, font=font) for l in lines)) + 80
    h = lh * len(lines) + 36
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=26, fill=(20, 16, 40, 165))
    for i, l in enumerate(lines):
        tw = d.textlength(l, font=font)
        d.text(((w - tw) / 2, 16 + i * lh), l, font=font, fill=(255, 250, 235, 255))
    _subs[text] = im
    return im


def text_card(lines, sizes, color=(255, 246, 214), stroke=(60, 38, 30)):
    ims = []
    for t, s in zip(lines, sizes):
        f = ImageFont.truetype(FONT_B, s)
        d = ImageDraw.Draw(Image.new('RGBA', (10, 10)))
        bb = d.textbbox((0, 0), t, font=f, stroke_width=int(s * 0.09))
        im = Image.new('RGBA', (bb[2] - bb[0] + 20, bb[3] - bb[1] + 20), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((10 - bb[0], 10 - bb[1]), t, font=f, fill=color + (255,),
                                stroke_width=int(s * 0.09), stroke_fill=stroke + (255,))
        ims.append(im)
    return ims


class Renderer:
    def __init__(self):
        self.S = scenes.build()
        self.rng = random.Random(11)
        self.title_ims = text_card([TITLE, SUBTITLE], [118, 78])
        self.end_ims = text_card(['Son', 'Masalı dinlediğin için teşekkürler!'], [150, 56])
        self.note = art.music_note()
        self.flies = [(self.rng.uniform(0, 1), self.rng.uniform(0, 1), self.rng.uniform(0.05, 0.12),
                       self.rng.uniform(0.04, 0.09), self.rng.uniform(0, 6.28)) for _ in range(60)]

    def frame(self, key, p, t, subs=None, fade=1.0, pan_dir=1):
        sc = self.S[key]
        ox = 120 * (smooth(p) if pan_dir > 0 else 1 - smooth(p))
        oy = 34
        fr = sc['bg'].crop((int(ox), oy, int(ox) + FW, oy + FH))
        layers = sorted(enumerate(sc['layers']), key=lambda il: (il[1].get('z', 10), il[0]))
        dark = interp([(a, b) for a, b in sc['darken']], p)[0] if sc.get('darken') else 0

        def draw_layer(ly):
            img = ly['img']
            mood = None
            for th, im, m in ly.get('swaps', []):
                if p >= th:
                    img, mood = im, m
            if ly.get('blink') is not None and mood == 'normal' and (t % 4.1) < 0.14:
                img = ly['blink']
            x, y = (interp(ly['path'], p) if ly.get('path') else (ly['x'], ly['y']))
            bob = ly.get('bob')
            if bob:
                y -= bob[0] * math.sin(2 * math.pi * t / bob[1] + (ly['x'] % 7))
            if ly.get('jump') is not None and p >= ly['jump']:
                y -= 34 * abs(math.sin(2 * math.pi * t / 0.7 + (ly['x'] % 5)))
            a = show_alpha(ly.get('show'), p)
            sx, sy = x - ox, y - oy
            if ly.get('light'):
                r = ly['light']
                if ly.get('light_boost'):
                    r = interp([(q, v) for q, v in ly['light_boost']], p)[0]
                r *= 1 + 0.08 * math.sin(t * 5)
                g = glow(r)
                paste(fr, g, sx - g.width / 2 - img.width * 0.15, sy - img.height * 0.35 - g.height / 2, 0.75 * a)
            paste(fr, img, sx - img.width / 2, sy - img.height, a)

        for _, ly in layers:
            if ly.get('z', 10) < 9:
                draw_layer(ly)
        if dark > 0.01:
            fr = Image.blend(fr, Image.new('RGBA', fr.size, (8, 10, 32, 255)), dark)
        if sc.get('moonlight'):
            ml = interp(sc['moonlight'], p)[0]
            if ml > 0.01:
                fr = Image.blend(fr, Image.new('RGBA', fr.size, (255, 244, 205, 255)), ml * 0.25)
        for _, ly in layers:
            if ly.get('z', 10) >= 9:
                draw_layer(ly)
        if sc.get('fireflies'):
            n, p0 = sc['fireflies']
            a = smooth((p - p0) / 0.1) if p0 else 1
            for i, (bx, by, ax, ay, ph) in enumerate(self.flies[:n]):
                fx = (bx + ax * math.sin(t * 0.5 + ph)) * FW
                fy = (0.25 + by * 0.45 + ay * math.sin(t * 0.7 + ph * 1.3)) * FH
                tw = 0.6 + 0.4 * math.sin(t * 3 + ph * 3)
                g = glow(40)
                paste(fr, g, fx - 20, fy - 20, a * tw)
                ImageDraw.Draw(fr).ellipse([fx - 4, fy - 4, fx + 4, fy + 4], fill=(255, 250, 200, int(255 * a)))
        if sc.get('notes'):
            n0, n1 = sc['notes']
            if n0 <= p <= n1 + 0.05:
                for i in range(10):
                    q = ((t * 0.12 + i / 10) % 1)
                    nx = 200 + i * 170 + 40 * math.sin(t + i)
                    ny = 900 - q * 650
                    paste(fr, self.note, nx, ny, min(1, (1 - q) * 2, q * 4) * (1 - smooth((p - n1) / 0.05)))
        if sc.get('title'):
            a = smooth(t / 1.2)
            ti, si = self.title_ims
            paste(fr, ti, FW / 2 - ti.width / 2, 120, a)
            paste(fr, si, FW / 2 - si.width / 2, 120 + ti.height + 4, a)
        if sc.get('end'):
            a = smooth((p - 0.3) / 0.15)
            ti, si = self.end_ims
            paste(fr, ti, FW / 2 - ti.width / 2, 90, a)
            paste(fr, si, FW / 2 - si.width / 2, 100 + ti.height, a)
        if subs:
            im = subtitle_img(subs)
            paste(fr, im, FW / 2 - im.width / 2, FH - im.height - 40, 1.0)
        if fade < 0.999:
            fr = Image.blend(Image.new('RGBA', fr.size, (0, 0, 0, 255)), fr, max(0, fade))
        return fr


if __name__ == '__main__':
    r = Renderer()
    keys = ['title'] + list(range(1, 13)) + ['end']
    for k in keys:
        for p in (0.1, 0.6, 0.95):
            r.frame(k, p, p * 20, subs='Bir varmış, bir yokmuş. Uzak mı uzak, yeşil mi yeşil bir ormanda.' if k == 1 else None).convert('RGB').resize((960, 540)).save(f'preview/s_{k}_{int(p*100)}.jpg', quality=85)
    print('ok')
