"""Leo Katika Historia - 17 Novemba, LANDSCAPE 16:9 (1920x1080), vintage style."""
import os, sys, subprocess
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
os.chdir(HERE)  # needs countries.geojson here (see README)
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from shapely.geometry import Polygon
from make_video import clamp, ease, prog, mix, path_pts, wrap
import map_geometry as bx

W, H, FPS = 1920, 1080, 30
OUT = os.path.join(HERE, "out"); os.makedirs(OUT, exist_ok=True)
GOLD, INK, MUTED, TRACK = (140, 47, 27), (46, 33, 22), (122, 98, 72), (214, 196, 158)
_bc, _gc = {}, {}
def serif(size):
    if size not in _bc:
        f = ImageFont.truetype(os.path.join(HERE, "../../historia/assets/fonts/PlayfairDisplay.ttf"), size); f.set_variation_by_axes([900]); _bc[size] = f
    return _bc[size]
def gara(w, s):
    k = (w, s)
    if k not in _gc:
        f = ImageFont.truetype(os.path.join(HERE, "../../historia/assets/fonts/EBGaramond.ttf"), int(s * 1.12)); f.set_variation_by_axes([int(w)]); _gc[k] = f
    return _gc[k]

# aged paper
_y = np.linspace(0, 1, H)[:, None, None]
paper = np.broadcast_to(np.array((241, 230, 204), np.float32) * (1 - _y) + np.array((228, 211, 174), np.float32) * _y, (H, W, 3)).copy()
_r = np.random.default_rng(3)
bl = Image.fromarray((_r.random((H // 24, W // 24)) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)
paper += (np.asarray(bl.filter(ImageFilter.GaussianBlur(30)), np.float32) / 255 - 0.5)[..., None] * np.array([18, 16, 12])
paper += _r.normal(0, 4.5, (H, W, 1))
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
vig = ((xx - W / 2) / (W * 0.6)) ** 2 + ((yy - H / 2) / (H * 0.62)) ** 2
paper *= (1 - 0.32 * np.clip(vig, 0, 1.4) ** 1.6)[..., None]
BG = Image.fromarray(paper.clip(0, 255).astype(np.uint8))

def text(d, xy, s, f, fill, a=1.0, anchor="mm", align="center", img=None):
    if a <= 0: return
    src = img or BG
    under = src.getpixel((int(clamp(xy[0], 0, W - 1)), int(clamp(xy[1], 0, H - 1))))
    d.multiline_text(xy, s, font=f, fill=mix(under, fill, clamp(a)), anchor=anchor, align=align, spacing=8)

def header(d, t, img=None):
    a = prog(t, 0, 0.4)
    text(d, (W // 2, 62), "LEO KATIKA HISTORIA", gara("700", 34), GOLD, a, img=img)
    text(d, (W // 2, 104), "17 NOVEMBA", gara("500", 28), MUTED, a, img=img)
def footer(d, img=None): text(d, (W // 2, 1036), "Radi the Storyteller", gara("600", 28), MUTED, 1, img=img)

# ---------------- map (left side) ----------------
MH = 900; MW = round(MH * (bx.LON1 - bx.LON0) / (bx.LAT1 - bx.LAT0)); MX, MY = 150, 130
def P(lon, lat):
    return (MX + (lon - bx.LON0) / (bx.LON1 - bx.LON0) * MW, MY + (bx.LAT1 - lat) / (bx.LAT1 - bx.LAT0) * MH)
S = 2
def mask(geom, tol, min_area):
    g = geom.simplify(tol, preserve_topology=True)
    polys = [g] if isinstance(g, Polygon) else list(getattr(g, "geoms", []))
    m = Image.new("L", (W * S, H * S), 0); dr = ImageDraw.Draw(m)
    for p in polys:
        if isinstance(p, Polygon) and p.area >= min_area:
            dr.polygon([(x * S, y * S) for x, y in (P(*c) for c in p.exterior.coords)], fill=255)
    return np.asarray(m.resize((W, H), Image.LANCZOS), np.float32) / 255
land = mask(bx.land, 0.08, 0.15)
land *= np.clip((yy - MY) / 110, 0, 1) * np.clip((MX + MW - xx) / 130, 0, 1)
egypt, tz = mask(bx.egypt, 0.03, 0.01), mask(bx.tz, 0.03, 0.01)
LANDC, GOLDC = np.array([196, 172, 128], np.float32), np.array(GOLD, np.float32)
def rpts(wps): return [P(*p) for p in [(bx.LON0 + x / bx.MW * (bx.LON1 - bx.LON0), bx.LAT1 - y / bx.MH * (bx.LAT1 - bx.LAT0))
                                      for x, y in bx.chaikin([bx.proj(*w) for w in wps])]]
CAPE, SUEZ = rpts(bx.CAPE), rpts(bx.SUEZ)
SUEZ_PT, DAR = P(32.4, 30.6), P(*bx.DAR)

def comp(base, m, c, a):
    if a <= 0: return base
    m = (m * a)[..., None]; return base * (1 - m) + c * m
def route(d, pts, p, c, w):
    seg = path_pts(pts, p)
    if len(seg) > 1:
        d.line(seg, fill=c, width=w, joint="curve")
        for x, y in (seg[0], seg[-1]): d.ellipse([x - w / 2, y - w / 2, x + w / 2, y + w / 2], fill=c)
    return seg[-1] if seg else None
def dot(d, xy, r, c, s):
    if s > 0: r *= s; d.ellipse([xy[0] - r, xy[1] - r, xy[0] + r, xy[1] + r], fill=c)
def pop(t, t0):
    if t < t0: return 0
    u = t - t0; return 1.4 * ease(u / 0.4) if u < 0.4 else 1.4 - 0.4 * ease((u - 0.4) / 0.4)

def s_map(t):
    base = np.asarray(BG, np.float32)
    base = comp(base, land, LANDC, prog(t, 0, 0.8))
    base = comp(base, egypt, GOLDC, 0.42 * prog(t, 0.8, 0.6))
    base = comp(base, tz, GOLDC, 0.42 * prog(t, 7.4, 0.6))
    img = Image.fromarray(base.clip(0, 255).astype(np.uint8)); d = ImageDraw.Draw(img)
    T = lambda xy, s, f, c, a, **k: text(d, xy, s, f, c, a, img=img, **k)
    header(d, t, img)
    T(P(17, 6), "AFRIKA", serif(60), (150, 124, 86), prog(t, 0.6, 0.6))
    T(P(8, 47.5), "ULAYA", gara("700", 34), INK, prog(t, 0.6, 0.6))
    T((P(24.6, 26.5)[0], P(24.6, 26.5)[1]), "Misri", gara("600", 30), INK, prog(t, 1.2, 0.5), anchor="rm")
    route(d, CAPE, prog(t, 1.6, 2.8), (120, 100, 76), 4)
    cx, cy = P(10, -33)
    T((cx, cy), "Kabla: kuzunguka\nRasi ya Tumaini Jema", gara("600", 27), MUTED, prog(t, 3.6, 0.5), anchor="rm", align="right")
    head = route(d, SUEZ, prog(t, 5.0, 2.4), GOLD, 7)
    if head and 5.0 < t < 7.5: dot(d, head, 9, INK, 1)
    dot(d, SUEZ_PT, 12, GOLD, pop(t, 5.6))
    T((SUEZ_PT[0] + 30, SUEZ_PT[1] - 4), "Mfereji wa Suez", gara("800", 31), GOLD, prog(t, 5.9, 0.5), anchor="lm")
    dot(d, DAR, 10, INK, pop(t, 7.3))
    T((DAR[0] + 24, DAR[1] + 3), "Tanzania", gara("800", 31), INK, prog(t, 7.6, 0.5), anchor="lm")
    # right column story
    T((1180, 330), "1869", serif(110), GOLD, prog(t, 0.4, 0.6), anchor="lm")
    a = prog(t, 8.2, 0.6)
    for i, line in enumerate(["Meli hazikuhitaji tena", "kuzunguka Afrika nzima"]):
        T((1180, 520 + i * 70 + int((1 - a) * 25)), line, serif(54), INK, a, anchor="lm")
    T((1180, 700), "Njia kutoka Ulaya hadi Afrika Mashariki\nikawa fupi zaidi kupitia Bahari ya Shamu.", gara("500", 34),
      MUTED, prog(t, 8.8, 0.6), anchor="lm", align="left")
    footer(d, img)
    return img

def s_intro(t, d):
    text(d, (W // 2, 270), "LEO KATIKA HISTORIA", gara("700", 44), GOLD, prog(t, 0.1, 0.6))
    s = 0.7 + 0.3 * prog(t, 0.3, 0.8)
    text(d, (800, 520), "17", serif(int(330 * s)), INK, prog(t, 0.3, 0.5), anchor="rm")
    a = prog(t, 0.8, 0.6); text(d, (860 + int((1 - a) * 40), 545), "NOVEMBA", serif(130), INK, a, anchor="lm")
    lw = int(700 * prog(t, 1.2, 0.8))
    if lw > 8: d.rounded_rectangle([W // 2 - lw // 2, 772, W // 2 + lw // 2, 779], 3, fill=GOLD)
    text(d, (W // 2, 850), "Siku hii, miaka iliyopita…", gara("500", 42), MUTED, prog(t, 1.8, 0.5))
    footer(d)

def s_year(t, d):
    header(d, t)
    s = 1.25 - 0.25 * prog(t, 0.1, 0.9)
    text(d, (880, 540), "1869", serif(int(280 * s)), GOLD, prog(t, 0.1, 0.5), anchor="rm")
    a = prog(t, 0.9, 0.6)
    for i, line in enumerate(["Mfereji wa Suez", "wafunguliwa rasmi"]):
        text(d, (960 + int((1 - a) * 40), 470 + i * 105), line, serif(88), INK, a, anchor="lm")
    text(d, (965, 690), "Misri  ·  17 Novemba 1869", gara("500", 40), MUTED, prog(t, 1.6, 0.5), anchor="lm")
    footer(d)

def s_build(t, d):
    header(d, t)
    text(d, (W // 2, 270), "Ujenzi ulichukua", gara("600", 48), MUTED, prog(t, 0.1, 0.5))
    a = prog(t, 0.3, 0.6); text(d, (W // 2, 420 + int((1 - a) * 40)), "miaka ~10", serif(170), INK, a)
    x0, x1, y = 460, 1460, 620
    d.rounded_rectangle([x0, y - 13, x1, y + 13], 13, fill=TRACK)
    p = prog(t, 0.8, 2.2)
    if p > 0.03: d.rounded_rectangle([x0, y - 13, x0 + int((x1 - x0) * p), y + 13], 13, fill=GOLD)
    text(d, (x0, y + 70), "1859", gara("700", 48), INK, prog(t, 0.8, 0.5), anchor="lm")
    text(d, (x1, y + 70), "1869", gara("800", 48), GOLD, prog(t, 2.8, 0.5), anchor="rm")
    a = prog(t, 3.0, 0.6)
    text(d, (W // 2, 850 + int((1 - a) * 25)), "Hadi leo, ni moja ya njia muhimu zaidi za meli duniani", gara("600", 46), INK, a)
    footer(d)

def s_also(t, d):
    header(d, t)
    a = prog(t, 0, 0.6); text(d, (W // 2, 250 + int((1 - a) * 30)), "PIA LEO", serif(100), GOLD, a)
    items = [("1970", "Lunokhod 1 — roboti ya kwanza\nkutembea kwenye Mwezi", 260, 0.6),
             ("1939", "Chanzo cha Siku ya Kimataifa\nya Wanafunzi", 1020, 1.8)]
    for yr, s, x, t0 in items:
        a = prog(t, t0, 0.6); dy = int((1 - a) * 40)
        if a > 0: d.rectangle([x, 440 + dy, x + 7, 700 + dy], fill=mix(BG.getpixel((x, 500)), GOLD, a))
        text(d, (x + 45, 500 + dy), yr, serif(90), INK, a, anchor="lm")
        text(d, (x + 45, 625 + dy), s, gara("500", 42), MUTED, prog(t, t0 + 0.2, 0.5), anchor="lm", align="left")
    footer(d)

def s_outro(t, d):
    a = prog(t, 0.1, 0.6); text(d, (W // 2, 400 + int((1 - a) * 40)), "LEO KATIKA", serif(130), INK, a)
    a = prog(t, 0.3, 0.6); text(d, (W // 2, 540 + int((1 - a) * 40)), "HISTORIA", serif(130), GOLD, a)
    lw = int(420 * prog(t, 0.6, 0.6))
    if lw > 6: d.rounded_rectangle([W // 2 - lw // 2, 640, W // 2 + lw // 2, 646], 3, fill=GOLD)
    text(d, (W // 2, 730), "Tukio jipya kila siku", gara("500", 46), MUTED, prog(t, 0.8, 0.5))
    a = prog(t, 1.2, 0.6); text(d, (W // 2, 860 + int((1 - a) * 30)), "Fuatilia  ·  Like  ·  Share", gara("700", 48), INK, a)
    footer(d)

SCENES = [("L_01", s_intro, 4.0), ("L_02", s_year, 5.0), ("L_03", "map", 11.0),
          ("L_04", s_build, 6.0), ("L_05", s_also, 6.0), ("L_06", s_outro, 4.0)]
def frame(fn, t, dur):
    img = s_map(t) if fn == "map" else BG.copy()
    if fn != "map": fn(t, ImageDraw.Draw(img))
    a = min(clamp(t / 0.35), clamp((dur - t) / 0.35))
    return Image.blend(BG, img, a) if a < 1 else img
def render(name, fn, dur):
    tmp, fin = f"{OUT}/{name}.tmp.mp4", f"{OUT}/{name}.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "20", "-preset", "veryfast", "-pix_fmt", "yuv420p", tmp],
                         stdin=subprocess.PIPE)
    for i in range(int(dur * FPS)): p.stdin.write(frame(fn, i / FPS, dur).tobytes())
    p.stdin.close()
    if p.wait(): raise SystemExit("ffmpeg failed")
    os.replace(tmp, fin); return fin

if __name__ == "__main__":
    if sys.argv[1:] == ["preview"]:
        shots = [frame(fn, tt, dur) for (n, fn, dur), tt in zip(SCENES, [3, 4, 10, 5, 5, 3])]
        sheet = Image.new("RGB", (640 * 2, 360 * 3))
        for i, im in enumerate(shots): sheet.paste(im.resize((640, 360)), ((i % 2) * 640, (i // 2) * 360))
        sheet.save(f"{OUT}/L_contact.png"); sys.exit()
    files = [render(*s) for s in SCENES]
    open(f"{OUT}/L_list.txt", "w").writelines(f"file '{f}'\n" for f in files)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", f"{OUT}/L_list.txt", "-i", os.path.join(HERE, "music.wav"),
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest",
                    f"{OUT}/Leo_Katika_Historia_17_Novemba_16x9.mp4"], check=True)
    print("done")
