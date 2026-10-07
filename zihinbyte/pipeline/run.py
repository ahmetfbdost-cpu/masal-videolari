import sys, os, time
sys.path.insert(0, os.path.dirname(__file__))
import importlib
_m = importlib.import_module(os.environ.get('ZB_MODULE','content'))
from content import *
VIDEOS = getattr(_m,'VIDEOS',VIDEOS)
CAROUSELS = getattr(_m,'CAROUSELS',CAROUSELS)

OUT = os.environ.get("ZB_OUT", "/home/claude/zihinbyte/paket1")
os.makedirs(OUT, exist_ok=True)
SCR = os.path.dirname(__file__)

def do_video(key):
    v = VIDEOS[key]
    t0 = time.time()
    fmt = REEL
    total = make_video(os.path.join(OUT, key + ".mp4"), v["scenes"], fmt, seed=v.get("seed", 0), bpm=v.get("bpm", 88), tmp_dir=SCR, voice=v.get("voice"))
    print(f"video {key}: {total:.1f}s in {time.time()-t0:.0f}s", flush=True)

def do_slides(key):
    d = os.path.join(OUT, key)
    os.makedirs(d, exist_ok=True)
    sl = CAROUSELS[key]
    for i, s in enumerate(sl, 1):
        make_slide(os.path.join(d, f"slide_{i}.png"), s, (i, len(sl)))
    print(f"slides {key}: {len(sl)}", flush=True)

def preview(key):
    """single still frames of a video for a quick look"""
    v = VIDEOS[key]
    W, H = REEL["W"], REEL["H"]
    base = gradient(W, H)
    glows = [glow(1000, ACCENT2, 0.30), glow(900, ACCENT, 0.20)]
    imgs = []
    for i in range(min(3, len(v["scenes"]))):
        sc = v["scenes"][i]
        els = build_scene(sc, REEL)
        im = render_frame(base, glows, els, min(sc["dur"] - 0.5, 3.0), sc["dur"], REEL, 2.0 + i * 3, 25.0)
        imgs.append(im.resize((360, 640)))
    sheet = Image.new("RGB", (360 * len(imgs), 640))
    for i, im in enumerate(imgs):
        sheet.paste(im, (360 * i, 0))
    sheet.save(os.path.join(SCR, f"preview_{key}.png"))

if __name__ == "__main__":
    mode, key = sys.argv[1], sys.argv[2]
    {"video": do_video, "slides": do_slides, "preview": preview}[mode](key)
