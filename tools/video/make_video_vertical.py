"""Leo Katika Historia - 17 Novemba, v2 (real map). Usage: python make_video2.py [preview]"""
import os, sys, subprocess, json
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
os.chdir(HERE)  # needs countries.geojson here (see README)
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import make_video as mv
from make_video import W, H, FPS, clamp, ease, prog, mix, path_pts, wrap
import map_geometry as bx   # map geometry + routes

OUT = os.path.join(HERE, "out"); os.makedirs(OUT, exist_ok=True)
GOLD = (140, 47, 27)      # faded red ink (accent)
WHITE = (46, 33, 22)      # dark brown ink (main text)
MUTED = (122, 98, 72)     # light brown (secondary text)
NAVY2 = (214, 196, 158)   # progress bar track
PAPER_TOP, PAPER_BOT = (241, 230, 204), (228, 211, 174)
BRIC = os.path.join(HERE, "../../historia/assets/fonts/PlayfairDisplay.ttf")
GARA = os.path.join(HERE, "../../historia/assets/fonts/EBGaramond.ttf")
_bc = {}
def bric(size):
    if size not in _bc:
        f = ImageFont.truetype(BRIC, size)
        try: f.set_variation_by_axes([900])
        except Exception: pass
        _bc[size] = f
    return _bc[size]
_gc = {}
def inter(w, s):
    k = (w, s)
    if k not in _gc:
        f = ImageFont.truetype(GARA, int(s * 1.12)); f.set_variation_by_axes([int(w)]); _gc[k] = f
    return _gc[k]

# softer background: gradient + glow ellipse
_y = np.linspace(0, 1, H)[:, None, None]
paper = np.array(PAPER_TOP, np.float32) * (1 - _y) + np.array(PAPER_BOT, np.float32) * _y
paper = np.broadcast_to(paper, (H, W, 3)).copy()
_r = np.random.default_rng(3)
blotch = Image.fromarray((_r.random((H // 24, W // 24)) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)
blotch = np.asarray(blotch.filter(ImageFilter.GaussianBlur(30)), np.float32) / 255 - 0.5
paper += blotch[..., None] * np.array([18, 16, 12])          # uneven aging
paper += _r.normal(0, 4.5, (H, W, 1))                          # paper grain
_yy, _xx = np.mgrid[0:H, 0:W]
vig = ((_xx - W / 2) / (W * 0.62)) ** 2 + ((_yy - H / 2) / (H * 0.6)) ** 2
paper *= (1 - 0.32 * np.clip(vig, 0, 1.4) ** 1.6)[..., None]   # darker, burnt edges
BG = Image.fromarray(paper.clip(0, 255).astype(np.uint8))
mv.BG = BG

def text(d, xy, s, fnt, fill, a=1.0, anchor="mm", align="center", spacing=8):
    if a <= 0: return
    col = mix(BG.getpixel((int(clamp(xy[0], 0, W-1)), int(clamp(xy[1], 0, H-1)))), fill, clamp(a))
    d.multiline_text(xy, s, font=fnt, fill=col, anchor=anchor, align=align, spacing=spacing)

def tcolor(fill, a, under):  # blend toward actual pixel under text
    return mix(under, fill, clamp(a))

def para(d, cx, y, s, fnt, fill, t, start, gap=1.22, maxw=900, step=0.12):
    lines = wrap(s, fnt, maxw); lh = int(fnt.size * gap)
    for i, line in enumerate(lines):
        a = prog(t, start + i * step, 0.5)
        text(d, (cx, y + i * lh + int((1 - a) * 30)), line, fnt, fill, a)

def header(d, t):
    a = prog(t, 0, 0.4)
    text(d, (W//2, 150), "LEO KATIKA HISTORIA", inter("700", 40), GOLD, a)
    text(d, (W//2, 205), "17 NOVEMBA", inter("500", 34), MUTED, a)
def footer(d, a=1.0): text(d, (W//2, 1800), "Radi the Storyteller", inter("600", 34), MUTED, a)

# ---------------- map layers (rendered once, 2x supersampled) ----------------
S = 2
def poly_mask(dpath):
    m = Image.new("L", (W*S, H*S), 0); dr = ImageDraw.Draw(m)
    for sub in dpath.split("M")[1:]:
        nums = [float(v) for v in sub.replace("Z", "").replace("L", " ").split()]
        pts = [((bx.MX + nums[i]) * S, (bx.MY + nums[i+1]) * S) for i in range(0, len(nums)-1, 2)]
        if len(pts) > 2: dr.polygon(pts, fill=255)
    return np.asarray(m.resize((W, H), Image.LANCZOS), dtype=np.float32) / 255

land = poly_mask(bx.to_path(bx.land, 0.08, 0.15))
# fade the cut edges (top + right) of the map so it has no hard box
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
fade = np.clip((yy - bx.MY) / 140, 0, 1) * np.clip((bx.MX + bx.MW - xx) / 160, 0, 1)
land *= fade
egypt = poly_mask(bx.to_path(bx.egypt, 0.03, 0.01))
tz = poly_mask(bx.to_path(bx.tz, 0.03, 0.01))
LANDC = np.array([196, 172, 128], np.float32); GOLDC = np.array(GOLD, np.float32)

def route_pts(wps):
    pts = bx.chaikin([bx.proj(*w) for w in wps])
    return [(bx.MX + x, bx.MY + y) for x, y in pts]
CAPE, SUEZ = route_pts(bx.CAPE), route_pts(bx.SUEZ)
SUEZ_PT = bx.scr(32.4, 30.6); DAR = bx.scr(*bx.DAR)

def comp(base, mask, color, a):
    if a <= 0: return base
    m = (mask * a)[..., None]
    return base * (1 - m) + color * m

def draw_route(d, pts, p, color, width):
    seg = path_pts(pts, p)
    if len(seg) > 1:
        d.line(seg, fill=color, width=width, joint="curve")
        for x, y in (seg[0], seg[-1]):
            r = width / 2; d.ellipse([x-r, y-r, x+r, y+r], fill=color)
    return seg[-1] if seg else None

def dot(d, xy, r, color, s):
    if s <= 0: return
    r = r * s; d.ellipse([xy[0]-r, xy[1]-r, xy[0]+r, xy[1]+r], fill=color)

def pop(t, t0):  # 0 -> 1.4 -> 1
    if t < t0: return 0
    u = t - t0
    return 1.4 * ease(u / 0.4) if u < 0.4 else 1.4 - 0.4 * ease((u - 0.4) / 0.4)

def s_map(t):
    base = np.asarray(BG, np.float32)
    base = comp(base, land, LANDC, prog(t, 0, 0.8))
    base = comp(base, egypt, GOLDC, 0.42 * prog(t, 0.8, 0.6))
    base = comp(base, tz, GOLDC, 0.42 * prog(t, 7.4, 0.6))
    img = Image.fromarray(base.clip(0, 255).astype(np.uint8)); d = ImageDraw.Draw(img)
    def lab(xy, s, f, fill, a, anchor="mm", align="center"):
        if a <= 0: return
        under = img.getpixel((int(clamp(xy[0], 0, W-1)), int(clamp(xy[1], 0, H-1))))
        d.multiline_text(xy, s, font=f, fill=mix(under, fill, a), anchor=anchor, align=align, spacing=6)
    header(d, t)
    lab(bx.scr(17, 6), "AFRIKA", bric(70), (150, 124, 86), prog(t, 0.6, 0.6))
    lab(bx.scr(8, 47.5), "ULAYA", inter("700", 40), WHITE, prog(t, 0.6, 0.6))
    lab((535, 560), "Misri", inter("600", 34), WHITE, prog(t, 1.2, 0.5), anchor="rm")
    draw_route(d, CAPE, prog(t, 1.6, 2.8), (120, 100, 76), 5)
    lab((440, 1425), "Kabla: kuzunguka\nRasi ya Tumaini Jema", inter("600", 32), MUTED, prog(t, 3.6, 0.5),
        anchor="rm", align="right")
    head = draw_route(d, SUEZ, prog(t, 5.0, 2.4), GOLD, 8)
    if head and 5.0 < t < 7.5: dot(d, head, 11, WHITE, 1)          # the "ship"
    dot(d, SUEZ_PT, 15, GOLD, pop(t, 5.6))
    lab((SUEZ_PT[0] + 40, SUEZ_PT[1] - 6), "Mfereji wa Suez", inter("800", 36), GOLD, prog(t, 5.9, 0.5), anchor="lm")
    dot(d, DAR, 12, WHITE, pop(t, 7.3))
    lab((DAR[0] + 30, DAR[1] + 4), "Tanzania", inter("800", 36), WHITE, prog(t, 7.6, 0.5), anchor="lm")
    a = prog(t, 8.2, 0.6)
    for i, line in enumerate(["Meli hazikuhitaji tena kuzunguka", "Afrika nzima"]):
        lab((W//2, 1580 + i * 66 + int((1 - a) * 30)), line, inter("700", 54), WHITE, a)
    footer(d)
    return img

# ---------------- other scenes (new type) ----------------
def s_intro(t, d):
    text(d, (W//2, 560), "LEO KATIKA HISTORIA", inter("700", 50), GOLD, prog(t, 0.1, 0.6))
    s = 0.7 + 0.3 * prog(t, 0.3, 0.8)
    text(d, (W//2, 880), "17", bric(int(420 * s)), WHITE, prog(t, 0.3, 0.5))
    a = prog(t, 0.8, 0.6); text(d, (W//2, 1180 + int((1-a)*40)), "NOVEMBA", bric(120), WHITE, a)
    lw = int(500 * prog(t, 1.2, 0.8)); d.rounded_rectangle([W//2 - lw//2, 1286, W//2 + lw//2, 1294], 4, fill=GOLD) if lw > 8 else None
    text(d, (W//2, 1400), "Siku hii, miaka iliyopita…", inter("500", 46), MUTED, prog(t, 1.8, 0.5))
    footer(d)

def s_year(t, d):
    header(d, t)
    s = 1.25 - 0.25 * prog(t, 0.1, 0.9)
    text(d, (W//2, 700), "1869", bric(int(320 * s)), GOLD, prog(t, 0.1, 0.5))
    a = prog(t, 0.9, 0.6)
    for i, line in enumerate(["Mfereji wa Suez", "wafunguliwa rasmi"]):
        text(d, (W//2, 990 + i * 106 + int((1-a)*40)), line, bric(96), WHITE, a)
    text(d, (W//2, 1240), "Misri  ·  17 Novemba 1869", inter("500", 46), MUTED, prog(t, 1.6, 0.5))
    footer(d)

def s_build(t, d):
    header(d, t)
    text(d, (W//2, 560), "Ujenzi ulichukua", inter("600", 56), MUTED, prog(t, 0.1, 0.5))
    a = prog(t, 0.3, 0.6); text(d, (W//2, 760 + int((1-a)*40)), "miaka ~10", bric(200), WHITE, a)
    d.rounded_rectangle([160, 1026, 920, 1054], 14, fill=NAVY2)
    p = prog(t, 0.8, 2.2)
    if p > 0.04: d.rounded_rectangle([160, 1026, 160 + int(760 * p), 1054], 14, fill=GOLD)
    text(d, (160, 1120), "1859", inter("700", 56), WHITE, prog(t, 0.8, 0.5), anchor="lm")
    text(d, (920, 1120), "1869", inter("800", 56), GOLD, prog(t, 2.8, 0.5), anchor="rm")
    para(d, W//2, 1310, "Hadi leo, ni moja ya njia muhimu zaidi za meli duniani", inter("600", 50), WHITE, t, 3.0, maxw=880)
    footer(d)

def s_also(t, d):
    header(d, t)
    a = prog(t, 0, 0.6); text(d, (W//2, 440 + int((1-a)*40)), "PIA LEO", bric(110), GOLD, a)
    items = [("1970", "Lunokhod 1 — roboti ya kwanza\nkutembea kwenye Mwezi", 680, 0.6),
             ("1939", "Chanzo cha Siku ya Kimataifa\nya Wanafunzi", 1080, 1.8)]
    for yr, s, y, t0 in items:
        a = prog(t, t0, 0.6); dx = int((1 - a) * -50)
        if a > 0: d.rectangle([120 + dx, y - 10, 128 + dx, y + 200], fill=mix(BG.getpixel((124, y)), GOLD, a))
        text(d, (170 + dx, y + 30), yr, bric(84), WHITE, a, anchor="lm")
        text(d, (170 + dx, y + 140), s, inter("500", 46), MUTED, prog(t, t0 + 0.2, 0.5), anchor="lm", align="left")
    footer(d)

def s_outro(t, d):
    a = prog(t, 0.1, 0.6); text(d, (W//2, 760 + int((1-a)*40)), "LEO KATIKA", bric(140), WHITE, a)
    a = prog(t, 0.3, 0.6); text(d, (W//2, 905 + int((1-a)*40)), "HISTORIA", bric(140), GOLD, a)
    lw = int(400 * prog(t, 0.6, 0.6))
    if lw > 6: d.rounded_rectangle([W//2 - lw//2, 1007, W//2 + lw//2, 1013], 3, fill=GOLD)
    text(d, (W//2, 1110), "Tukio jipya kila siku", inter("500", 50), MUTED, prog(t, 0.8, 0.5))
    a = prog(t, 1.2, 0.6); text(d, (W//2, 1300 + int((1-a)*40)), "Fuatilia  ·  Like  ·  Share", inter("700", 54), WHITE, a)
    footer(d)

SCENES = [("v3_01", s_intro, 4.0), ("v3_02", s_year, 5.0), ("v3_03", "map", 11.0),
          ("v3_04", s_build, 6.0), ("v3_05", s_also, 6.0), ("v3_06", s_outro, 4.0)]
FADE = 0.35

def frame(fn, t, dur):
    if fn == "map": img = s_map(t)
    else:
        img = BG.copy(); fn(t, ImageDraw.Draw(img))
    a = min(clamp(t / FADE), clamp((dur - t) / FADE))
    return Image.blend(BG, img, a) if a < 1 else img

def render(name, fn, dur):
    tmp, final = f"{OUT}/{name}.tmp.mp4", f"{OUT}/{name}.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
                          "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for i in range(int(dur * FPS)): p.stdin.write(frame(fn, i / FPS, dur).tobytes())
    p.stdin.close()
    if p.wait() != 0: raise SystemExit("ffmpeg failed " + name)
    os.replace(tmp, final); return final

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "preview":
        shots = [frame(fn, tt, dur) for (n, fn, dur), tt in zip(SCENES, [3, 4, 10, 5, 5, 3])]
        sheet = Image.new("RGB", (360 * 3, 640 * 2))
        for i, im in enumerate(shots): sheet.paste(im.resize((360, 640)), ((i % 3) * 360, (i // 3) * 640))
        sheet.save(f"{OUT}/v3_contact.png"); frame("map", 10, 11).save(f"{OUT}/v3_map.png"); sys.exit()
    files = [render(*s) for s in SCENES]
    open(f"{OUT}/v3_list.txt", "w").writelines(f"file '{f}'\n" for f in files)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", f"{OUT}/v3_list.txt",
                    "-c", "copy", f"{OUT}/Leo_Katika_Historia_17_Novemba_v3_old.mp4"], check=True)
    print("done")
