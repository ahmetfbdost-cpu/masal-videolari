import math, os, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageChops
from scipy.signal import butter, lfilter

FD = "/usr/share/fonts/opentype/inter/"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
FONTS = {"B": FD + "Inter-ExtraBold.otf", "M": FD + "Inter-Medium.otf", "SB": FD + "Inter-Bold.otf"}

BG_TOP = (9, 13, 30)
BG_BOT = (28, 18, 66)
ACCENT = (96, 220, 190)
ACCENT2 = (130, 120, 255)
WHITE = (245, 247, 252)
MUTED = (165, 175, 200)
CODE_BG = (16, 24, 52)
CODE_BORDER = (58, 70, 125)
C_KEY = (255, 123, 114)    # keywords
C_STR = (165, 214, 120)    # strings
C_FUN = (130, 190, 255)    # functions
C_PLAIN = (230, 235, 245)
C_NUM = (255, 200, 110)

REEL = dict(W=1080, H=1920, brand_y=290, bar_y=355, y_min=470, y_max=1440, x=90, maxw=900)
POST = dict(W=1080, H=1350, brand_y=90, bar_y=None, y_min=200, y_max=1130, x=90, maxw=900)

_font_cache = {}
def F(key, size):
    k = (key, size)
    if k not in _font_cache:
        path = MONO if key == "MONO" else FONTS[key]
        _font_cache[k] = ImageFont.truetype(path, size)
    return _font_cache[k]

def ease(a):
    a = max(0.0, min(1.0, a))
    return 1 - (1 - a) ** 3

def gradient(W, H):
    t = np.linspace(0, 1, H)[:, None, None]
    top = np.array(BG_TOP)[None, None, :]
    bot = np.array(BG_BOT)[None, None, :]
    arr = (top + (bot - top) * t) * np.ones((1, W, 1))
    return Image.fromarray(arr.astype("uint8"), "RGB").convert("RGBA")

def glow(size, color, strength):
    y, x = np.mgrid[0:size, 0:size]
    r = np.sqrt((x - size / 2) ** 2 + (y - size / 2) ** 2) / (size / 2)
    a = np.clip(1 - r, 0, 1) ** 2 * strength * 255
    arr = np.zeros((size, size, 4), dtype="uint8")
    arr[..., 0], arr[..., 1], arr[..., 2] = color
    arr[..., 3] = a.astype("uint8")
    return Image.fromarray(arr, "RGBA")

def wrap(text, fnt, maxw):
    d = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    out = []
    for para in text.split("\n"):
        cur = ""
        for w in para.split(" "):
            t = (cur + " " + w).strip()
            if d.textlength(t, font=fnt) <= maxw:
                cur = t
            else:
                out.append(cur)
                cur = w
        out.append(cur)
    return out

def text_layer(text, key, size, color, maxw):
    fnt = F(key, size)
    lines = wrap(text, fnt, maxw)
    lh = int(size * 1.22)
    img = Image.new("RGBA", (maxw + 20, lh * len(lines) + 10), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for i, ln in enumerate(lines):
        d.text((0, i * lh), ln, font=fnt, fill=color + (255,))
    return img

def badge_layer(num):
    s = 150
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, s - 1, s - 1], radius=40, fill=ACCENT + (255,))
    fnt = F("B", 96)
    w = d.textlength(str(num), font=fnt)
    d.text(((s - w) / 2, 14), str(num), font=fnt, fill=(10, 20, 30, 255))
    return img

def chip_layer(text):
    fnt = F("SB", 40)
    d = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    w = int(d.textlength(text, font=fnt)) + 60
    img = Image.new("RGBA", (w, 76), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, w - 1, 75], radius=38, fill=(96, 220, 190, 40), outline=ACCENT + (255,), width=3)
    d.text((30, 14), text, font=fnt, fill=ACCENT + (255,))
    return img

class CodeEl:
    """lines: list of list of (text, color). Typing animation over `typing` seconds."""
    def __init__(self, lines, maxw, label="", size=44):
        self.size = size
        self.fnt = F("MONO", size)
        self.lh = int(size * 1.55)
        self.lines = lines
        self.maxw = maxw
        self.head = 78
        self.h = self.head + self.lh * len(lines) + 48
        card = Image.new("RGBA", (maxw, self.h), (0, 0, 0, 0))
        d = ImageDraw.Draw(card)
        d.rounded_rectangle([0, 0, maxw - 1, self.h - 1], radius=30, fill=CODE_BG + (255,), outline=CODE_BORDER + (255,), width=3)
        for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
            d.ellipse([36 + i * 40, 28, 36 + i * 40 + 22, 50], fill=c + (255,))
        if label:
            d.text((maxw - 40 - d.textlength(label, font=F("M", 30)), 24), label, font=F("M", 30), fill=MUTED + (255,))
        self.card = card
        self.total = sum(len(t) for ln in lines for t, _ in ln)

    def frame(self, frac):
        img = self.card.copy()
        d = ImageDraw.Draw(img)
        n = int(self.total * frac + 0.0001)
        cw = self.fnt.getlength("M")
        shown = 0
        last_xy = (36, self.head)
        for li, ln in enumerate(self.lines):
            x = 36
            y = self.head + li * self.lh
            for text, color in ln:
                take = max(0, min(len(text), n - shown))
                if take > 0:
                    d.text((x, y), text[:take], font=self.fnt, fill=color + (255,))
                x += cw * take
                shown += len(text)
                if take < len(text):
                    break
            last_xy = (x, y)
            if shown >= n and n < self.total:
                break
        if frac < 1.0 or int(frac * 1000) % 2 == 0:
            cx, cy = last_xy
            d.rectangle([cx + 2, cy + 4, cx + 2 + 14, cy + self.size + 2], fill=ACCENT + (255,))
        return img

def build_scene(scene, fmt):
    """Return list of elements with layout info."""
    els = []
    for e in scene["els"]:
        k = e["t"]
        if k == "text":
            layer = text_layer(e["text"], e.get("f", "B"), e["size"], e.get("color", WHITE), fmt["maxw"])
            els.append(dict(kind="img", img=layer, delay=e.get("delay", 0), gap=e.get("gap", 36), h=layer.height))
        elif k == "badge":
            layer = badge_layer(e["text"])
            els.append(dict(kind="img", img=layer, delay=e.get("delay", 0), gap=e.get("gap", 40), h=layer.height))
        elif k == "chip":
            layer = chip_layer(e["text"])
            els.append(dict(kind="img", img=layer, delay=e.get("delay", 0), gap=e.get("gap", 40), h=layer.height))
        elif k == "code":
            ce = CodeEl(e["lines"], fmt["maxw"], e.get("label", ""), e.get("size", 44))
            els.append(dict(kind="code", code=ce, delay=e.get("delay", 0), typing=e.get("typing", 1.6), gap=e.get("gap", 36), h=ce.h))
    total = sum(x["h"] for x in els) + sum(x["gap"] for x in els[:-1])
    y = fmt["y_min"] + max(0, ((fmt["y_max"] - fmt["y_min"]) - total) // 2)
    for x in els:
        x["y"] = y
        y += x["h"] + x["gap"]
    return els

def scale_alpha(img, a):
    if a >= 0.999:
        return img
    r, g, b, al = img.split()
    al = al.point(lambda v: int(v * a))
    return Image.merge("RGBA", (r, g, b, al))

def render_frame(base, glows, scene_els, t_local, dur, fmt, g_t, g_total, page=None, static=False):
    W, H = fmt["W"], fmt["H"]
    img = base.copy()
    # moving glows
    gx = int(W * 0.55 + math.sin(g_t * 0.7) * 160) - glows[0].width // 2
    gy = int(H * 0.22 + math.cos(g_t * 0.5) * 120) - glows[0].height // 2
    img.alpha_composite(glows[0], (gx, gy)) if (0 <= gx + glows[0].width and gx < W) else None
    hx = int(W * 0.25 + math.cos(g_t * 0.6) * 140) - glows[1].width // 2
    hy = int(H * 0.82 + math.sin(g_t * 0.45) * 120) - glows[1].height // 2
    img.alpha_composite(glows[1], (hx, hy))
    d = ImageDraw.Draw(img)
    # brand
    d.text((fmt["x"], fmt["brand_y"]), "ZİHİNBYTE", font=F("B", 40), fill=ACCENT + (255,))
    if fmt["bar_y"] is not None:
        d.rounded_rectangle([fmt["x"], fmt["bar_y"], W - fmt["x"], fmt["bar_y"] + 8], radius=4, fill=(52, 58, 96, 255))
        wfill = int((W - 2 * fmt["x"]) * min(1.0, g_t / g_total))
        if wfill > 8:
            d.rounded_rectangle([fmt["x"], fmt["bar_y"], fmt["x"] + wfill, fmt["bar_y"] + 8], radius=4, fill=ACCENT + (255,))
    if page:
        txt = f"{page[0]}/{page[1]}"
        d.text((W - fmt["x"] - d.textlength(txt, font=F("SB", 36)), fmt["brand_y"] + 2), txt, font=F("SB", 36), fill=MUTED + (255,))
        if page[0] < page[1]:
            d.text((W - fmt["x"] - d.textlength("Kaydır →", font=F("SB", 38)), H - 110), "Kaydır →", font=F("SB", 38), fill=ACCENT + (255,))
    # exit fade
    exit_a = 1.0 if static else max(0.0, min(1.0, (dur - t_local) / 0.3))
    for e in scene_els:
        a = 1.0 if static else ease((t_local - e["delay"]) / 0.5)
        if a <= 0:
            continue
        dy = 0 if static else int((1 - a) * 55)
        alpha = a * exit_a
        if alpha <= 0.01:
            continue
        if e["kind"] == "img":
            layer = scale_alpha(e["img"], alpha)
        else:
            frac = 1.0 if static else max(0.0, min(1.0, (t_local - e["delay"] - 0.2) / e["typing"]))
            layer = scale_alpha(e["code"].frame(frac), alpha)
        img.alpha_composite(layer, (fmt["x"], e["y"] + dy))
    return img.convert("RGB")

# ------------------------------------------------------------------ audio
SR = 44100

def _env(n, a, r):
    e = np.ones(n)
    na, nr = min(int(a * SR), n), min(int(r * SR), n)
    if na > 0:
        e[:na] = np.linspace(0, 1, na)
    if nr > 0:
        e[-nr:] *= np.linspace(1, 0, nr)
    return e

def make_audio(path, total, cuts, seed=0, bpm=88, key_shift=0):
    rng = np.random.default_rng(seed)
    n = int(total * SR)
    t = np.arange(n) / SR
    mix = np.zeros(n)
    beat = 60.0 / bpm
    bar = beat * 4
    s = 2 ** (key_shift / 12)
    chords = [
        [220.00, 261.63, 329.63],   # Am
        [174.61, 220.00, 261.63],   # F
        [196.00, 261.63, 329.63],   # C
        [196.00, 246.94, 293.66],   # G
    ]
    nb = int(total / bar) + 2
    for b in range(nb):
        t0 = b * bar
        ch = [f * s for f in chords[b % 4]]
        i0 = int(t0 * SR)
        i1 = min(n, int((t0 + bar + 0.6) * SR))
        if i0 >= n:
            break
        seg = np.arange(i1 - i0) / SR
        pad = np.zeros(len(seg))
        for f in ch:
            pad += np.sin(2 * np.pi * f * seg) + 0.4 * np.sin(2 * np.pi * f * 1.004 * seg) + 0.25 * np.sin(2 * np.pi * 2 * f * seg)
        pad *= 0.045 * _env(len(seg), 0.5, 0.7)
        mix[i0:i1] += pad
        # bass
        bf = ch[0] / 2
        bass = np.sin(2 * np.pi * bf * seg) * 0.16 * _env(len(seg), 0.05, 0.4)
        mix[i0:i1] += bass
        # plucks (eighth notes arpeggio)
        notes = [ch[0] * 2, ch[1] * 2, ch[2] * 2, ch[1] * 2]
        for k in range(8):
            ts = t0 + k * beat / 2
            j0 = int(ts * SR)
            if j0 >= n:
                break
            L = int(0.45 * SR)
            j1 = min(n, j0 + L)
            tt = np.arange(j1 - j0) / SR
            f = notes[k % 4]
            p = (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * 2 * f * tt)) * np.exp(-tt * 7) * 0.075
            mix[j0:j1] += p
        # kick on beats 1 and 3, hat on offbeats
        for k in (0, 2):
            ts = t0 + k * beat
            j0 = int(ts * SR)
            if j0 >= n:
                break
            L = int(0.25 * SR)
            j1 = min(n, j0 + L)
            tt = np.arange(j1 - j0) / SR
            fr = 45 + 90 * np.exp(-tt * 28)
            ph = 2 * np.pi * np.cumsum(fr) / SR
            mix[j0:j1] += np.sin(ph) * np.exp(-tt * 14) * 0.30
        for k in range(4):
            ts = t0 + k * beat + beat / 2
            j0 = int(ts * SR)
            if j0 >= n:
                break
            L = int(0.05 * SR)
            j1 = min(n, j0 + L)
            tt = np.arange(j1 - j0) / SR
            nz = rng.standard_normal(j1 - j0)
            nz = np.diff(nz, prepend=0)
            mix[j0:j1] += nz * np.exp(-tt * 90) * 0.05
    # whoosh at cuts
    bb, aa = butter(2, [700 / (SR / 2), 5000 / (SR / 2)], btype="band")
    for c in cuts:
        j0 = int(max(0, c - 0.25) * SR)
        L = int(0.5 * SR)
        j1 = min(n, j0 + L)
        if j1 <= j0:
            continue
        tt = np.linspace(0, 1, j1 - j0)
        nz = lfilter(bb, aa, rng.standard_normal(j1 - j0))
        env = np.sin(np.pi * tt) ** 2
        mix[j0:j1] += nz * env * 0.22
    # soft stereo
    delay = int(0.012 * SR)
    left = mix
    right = np.concatenate([np.zeros(delay), mix[:-delay]]) * 0.97
    st = np.stack([left, right], axis=1)
    fade = np.ones(n)
    nf = int(1.0 * SR)
    fade[-nf:] = np.linspace(1, 0, nf)
    fi = int(0.15 * SR)
    fade[:fi] = np.linspace(0, 1, fi)
    st *= fade[:, None]
    st = st / (np.max(np.abs(st)) + 1e-9) * 0.85
    pcm = (st * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())

# ------------------------------------------------------------------ video
def make_video(out_path, scenes, fmt=REEL, fps=30, seed=0, bpm=88, tmp_dir=".", voice=None, music_gain=0.22):
    W, H = fmt["W"], fmt["H"]
    base = gradient(W, H)
    glows = [glow(1000, ACCENT2, 0.30), glow(900, ACCENT, 0.20)]
    built = [build_scene(s, fmt) for s in scenes]
    durs = [s["dur"] for s in scenes]
    total = sum(durs)
    cuts, acc = [], 0.0
    for d in durs[:-1]:
        acc += d
        cuts.append(acc)
    wav = os.path.join(tmp_dir, os.path.basename(out_path) + ".wav")
    make_audio(wav, total, cuts, seed=seed, bpm=bpm)
    if voice:
        fc = (f"[1:a]volume={music_gain}[m];"
              "[2:a]aresample=44100,pan=stereo|c0=c0|c1=c0[v];"
              "[m][v]amix=inputs=2:duration=longest:normalize=0[mx];"
              "[mx]loudnorm=I=-16:TP=-1.5:LRA=11[out]")
        cmd = ["ffmpeg", "-y", "-loglevel", "error",
               "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-",
               "-i", wav, "-i", voice,
               "-filter_complex", fc, "-map", "0:v", "-map", "[out]",
               "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
               "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-t", f"{total:.2f}",
               "-movflags", "+faststart", out_path]
    else:
        cmd = ["ffmpeg", "-y", "-loglevel", "error",
               "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-",
               "-i", wav,
               "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
               "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
               "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-shortest", "-movflags", "+faststart", out_path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    frames_total = int(round(total * fps))
    si, scene_start = 0, 0.0
    for fi in range(frames_total):
        g_t = fi / fps
        while si < len(durs) - 1 and g_t >= scene_start + durs[si]:
            scene_start += durs[si]
            si += 1
        t_local = g_t - scene_start
        im = render_frame(base, glows, built[si], t_local, durs[si], fmt, g_t, total)
        p.stdin.write(im.tobytes())
    p.stdin.close()
    p.wait()
    os.remove(wav)
    return total

def make_slide(out_path, scene, page, fmt=POST):
    base = gradient(fmt["W"], fmt["H"])
    glows = [glow(1000, ACCENT2, 0.30), glow(900, ACCENT, 0.20)]
    els = build_scene(scene, fmt)
    im = render_frame(base, glows, els, 99, 99, fmt, 2.0, 10.0, page=page, static=True)
    im.save(out_path, quality=95)
