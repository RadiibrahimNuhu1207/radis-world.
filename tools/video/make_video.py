"""Leo Katika Historia - sample graphic video generator (17 Novemba).
Usage: python make_video.py [preview]   -> preview writes still PNGs only
"""
import math, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
OUT = os.path.dirname(os.path.abspath(__file__))
F = "/usr/share/fonts/opentype/inter/"
NAVY = (11, 22, 44); NAVY2 = (20, 40, 74); GOLD = (242, 181, 68)
WHITE = (245, 242, 235); MUTED = (150, 165, 190); SEA = (40, 110, 170)

_fc = {}
def font(name, size):
    k = (name, size)
    if k not in _fc: _fc[k] = ImageFont.truetype(F + name, size)
    return _fc[k]

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(x): x = clamp(x); return 1 - (1 - x) ** 3
def prog(t, start, dur): return ease((t - start) / dur)
def mix(c1, c2, a): return tuple(int(c1[i] + (c2[i] - c1[i]) * a) for i in range(3))

# background: vertical gradient + faint latitude lines
BG = Image.new("RGB", (W, H), NAVY)
_d = ImageDraw.Draw(BG)
for y in range(H):
    _d.line([(0, y), (W, y)], fill=mix(NAVY, NAVY2, y / H))
for y in range(160, H, 160):
    _d.line([(0, y), (W, y)], fill=mix(NAVY, NAVY2, y / H + 0.25), width=1)

def text(d, xy, s, fnt, fill, a=1.0, anchor="mm"):
    if a <= 0: return
    col = mix(BG.getpixel((int(clamp(xy[0], 0, W - 1)), int(clamp(xy[1], 0, H - 1)))), fill, clamp(a))
    d.text(xy, s, font=fnt, fill=col, anchor=anchor)

def header(d, t):
    a = prog(t, 0, 0.4)
    text(d, (W // 2, 150), "LEO KATIKA HISTORIA", font("Inter-Bold.otf", 40), GOLD, a)
    text(d, (W // 2, 205), "17 NOVEMBA", font("Inter-Medium.otf", 34), MUTED, a)

def footer(d, a=1.0):
    text(d, (W // 2, H - 120), "Radi the Storyteller", font("Inter-SemiBold.otf", 34), MUTED, a)

def wrap(s, fnt, maxw):
    words, lines, cur = s.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if fnt.getlength(t) <= maxw: cur = t
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

def para(d, cx, y, s, fnt, fill, t, start, gap=1.25, maxw=900, step=0.15):
    lh = int(fnt.size * gap)
    for i, line in enumerate(wrap(s, fnt, maxw)):
        a = prog(t, start + i * step, 0.5)
        text(d, (cx, y + i * lh + int((1 - a) * 30)), line, fnt, fill, a)
    return y + len(wrap(s, fnt, maxw)) * lh

# ---------------- scenes ----------------
def s_intro(t, d, img):
    a = prog(t, 0.1, 0.6)
    text(d, (W // 2, 560), "LEO KATIKA HISTORIA", font("Inter-Bold.otf", 48), GOLD, a)
    s = 0.6 + 0.4 * prog(t, 0.3, 0.8)
    big = font("InterDisplay-Black.otf", int(420 * s))
    text(d, (W // 2, 900), "17", big, WHITE, prog(t, 0.3, 0.6))
    text(d, (W // 2, 1180), "NOVEMBA", font("InterDisplay-Bold.otf", 110), WHITE, prog(t, 0.8, 0.6))
    lw = int(500 * prog(t, 1.2, 0.8))
    d.rectangle([W // 2 - lw // 2, 1290, W // 2 + lw // 2, 1298], fill=GOLD)
    text(d, (W // 2, 1400), "Siku hii, miaka iliyopita…", font("Inter-Medium.otf", 44), MUTED, prog(t, 1.8, 0.6))
    footer(d, prog(t, 1.0, 0.6))

def s_year(t, d, img):
    header(d, t)
    p = prog(t, 0.2, 1.4)
    year = int(1800 + 69 * p)
    text(d, (W // 2, 720), str(year), font("InterDisplay-Black.otf", 300), GOLD, prog(t, 0, 0.4))
    y = para(d, W // 2, 960, "Mfereji wa Suez wafunguliwa rasmi", font("InterDisplay-Bold.otf", 92), WHITE, t, 1.4)
    text(d, (W // 2, y + 60), "Misri", font("Inter-Medium.otf", 48), MUTED, prog(t, 2.2, 0.5))
    footer(d)

def s_canal(t, d, img):
    header(d, t)
    # two seas and the canal between them
    top_a, bot_a = prog(t, 0.0, 0.6), prog(t, 0.3, 0.6)
    d.rounded_rectangle([140, 420, 940, 640], 40, fill=mix(NAVY, SEA, top_a))
    text(d, (540, 530), "BAHARI YA MEDITERANIA", font("Inter-Bold.otf", 46), WHITE, top_a)
    d.rounded_rectangle([140, 1180, 940, 1400], 40, fill=mix(NAVY, SEA, bot_a))
    text(d, (540, 1290), "BAHARI YA SHAMU", font("Inter-Bold.otf", 46), WHITE, bot_a)
    cp = prog(t, 0.9, 1.4)
    y0, y1 = 640, 640 + int((1180 - 640) * cp)
    if cp > 0:
        d.rectangle([520, y0, 560, y1], fill=SEA)
        d.rectangle([516, y0, 520, y1], fill=GOLD); d.rectangle([560, y0, 564, y1], fill=GOLD)
    text(d, (760, 910), "MFEREJI", font("Inter-Bold.otf", 40), GOLD, prog(t, 1.8, 0.5), anchor="lm")
    text(d, (760, 960), "WA SUEZ", font("Inter-Bold.otf", 40), GOLD, prog(t, 1.8, 0.5), anchor="lm")
    # ship sailing through
    sp = clamp((t - 2.3) / 2.6)
    if 0 < sp < 1:
        sy = 560 + int((1260 - 560) * sp)
        d.polygon([(540, sy + 34), (522, sy - 10), (558, sy - 10)], fill=WHITE)
        d.rectangle([536, sy - 40, 544, sy - 10], fill=WHITE)
    para(d, W // 2, 1500, "Unaunganisha bahari mbili — njia fupi kati ya Ulaya na Asia",
         font("Inter-SemiBold.otf", 52), WHITE, t, 2.2)
    footer(d)

def path_pts(pts, p):
    """Return the leading part (fraction p) of a polyline."""
    segs = [(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    lens = [math.dist(a, b) for a, b in segs]; total = sum(lens); want = total * p
    out = [pts[0]]
    for (a, b), L in zip(segs, lens):
        if want >= L: out.append(b); want -= L
        else:
            f = want / L if L else 0
            out.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)); break
    return out

def bezier(p0, p1, p2, p3, n=60):
    return [tuple((1 - u) ** 3 * p0[i] + 3 * (1 - u) ** 2 * u * p1[i] + 3 * (1 - u) * u * u * p2[i] + u ** 3 * p3[i]
                  for i in range(2)) for u in [k / n for k in range(n + 1)]]

def s_route(t, d, img):
    header(d, t)
    a = prog(t, 0, 0.5)
    EU, EA = (300, 430), (760, 1060)
    for (x, y), lab in [(EU, "ULAYA"), (EA, "AFRIKA MASHARIKI")]:
        r = 22
        d.ellipse([x - r, y - r, x + r, y + r], fill=mix(NAVY, WHITE, a))
    text(d, (EU[0], EU[1] - 60), "ULAYA", font("Inter-Bold.otf", 42), WHITE, a)
    text(d, (EA[0] + 40, EA[1]), "AFRIKA", font("Inter-Bold.otf", 42), WHITE, a, anchor="lm")
    text(d, (EA[0] + 40, EA[1] + 50), "MASHARIKI", font("Inter-Bold.otf", 42), WHITE, a, anchor="lm")
    # long route around the Cape (grey)
    longp = bezier(EU, (-120, 1100), (200, 1800), (420, 1500)) + bezier((420, 1500), (600, 1300), (700, 1200), EA)[1:]
    lp = path_pts(longp, prog(t, 0.6, 2.0))
    if len(lp) > 1: d.line(lp, fill=MUTED, width=10, joint="curve")
    text(d, (470, 1590), "Kabla: kuzunguka", font("Inter-Medium.otf", 38), MUTED, prog(t, 1.8, 0.5), anchor="lm")
    text(d, (470, 1638), "Rasi ya Tumaini Jema", font("Inter-SemiBold.otf", 38), MUTED, prog(t, 1.8, 0.5), anchor="lm")
    # short route via Suez (gold)
    shortp = bezier(EU, (520, 480), (620, 650), (640, 760)) + bezier((640, 760), (660, 880), (720, 980), EA)[1:]
    sp = path_pts(shortp, prog(t, 2.6, 1.2))
    if len(sp) > 1: d.line(sp, fill=GOLD, width=14, joint="curve")
    text(d, (640, 580), "Baada: kupitia Suez", font("Inter-Bold.otf", 40), GOLD, prog(t, 3.2, 0.5), anchor="lm")
    para(d, W // 2, 1740, "Meli hazikuhitaji tena kuzunguka Afrika nzima",
         font("Inter-SemiBold.otf", 50), WHITE, t, 3.6, maxw=900)

def s_build(t, d, img):
    header(d, t)
    text(d, (W // 2, 560), "Ujenzi ulichukua", font("Inter-SemiBold.otf", 56), MUTED, prog(t, 0, 0.5))
    text(d, (W // 2, 760), "miaka ~10", font("InterDisplay-Black.otf", 190), WHITE, prog(t, 0.3, 0.6))
    x0, x1, y = 160, 920, 1040
    d.rounded_rectangle([x0, y - 14, x1, y + 14], 14, fill=NAVY2)
    p = prog(t, 0.8, 2.2)
    if p > 0.02: d.rounded_rectangle([x0, y - 14, x0 + int((x1 - x0) * p), y + 14], 14, fill=GOLD)
    text(d, (x0, y + 80), "1859", font("Inter-Bold.otf", 56), WHITE, prog(t, 0.8, 0.4), anchor="lm")
    text(d, (x1, y + 80), "1869", font("Inter-Bold.otf", 56), GOLD, prog(t, 2.8, 0.4), anchor="rm")
    para(d, W // 2, 1300, "Hadi leo, ni moja ya njia muhimu zaidi za meli duniani",
         font("Inter-SemiBold.otf", 50), WHITE, t, 2.6, maxw=860)
    footer(d)

def s_also(t, d, img):
    header(d, t)
    text(d, (W // 2, 440), "PIA LEO", font("InterDisplay-Black.otf", 110), GOLD, prog(t, 0, 0.5))
    items = [("1970", "Lunokhod 1 — roboti ya kwanza kutembea kwenye Mwezi"),
             ("1939", "Chanzo cha Siku ya Kimataifa ya Wanafunzi")]
    y = 680
    for i, (yr, s) in enumerate(items):
        st = 0.6 + i * 1.2; a = prog(t, st, 0.6); dx = int((1 - a) * -60)
        d.rectangle([120 + dx, y - 10, 128 + dx, y + 200], fill=mix(NAVY, GOLD, a))
        text(d, (170 + dx, y + 30), yr, font("InterDisplay-Black.otf", 80), WHITE, a, anchor="lm")
        for j, line in enumerate(wrap(s, font("Inter-Medium.otf", 46), 760)):
            text(d, (170 + dx, y + 110 + j * 58), line, font("Inter-Medium.otf", 46), MUTED, a, anchor="lm")
        y += 400
    footer(d)

def s_outro(t, d, img):
    a = prog(t, 0.1, 0.6)
    text(d, (W // 2, 760), "LEO KATIKA", font("InterDisplay-Black.otf", 130), WHITE, a)
    text(d, (W // 2, 900), "HISTORIA", font("InterDisplay-Black.otf", 130), GOLD, prog(t, 0.3, 0.6))
    lw = int(400 * prog(t, 0.6, 0.6))
    d.rectangle([W // 2 - lw // 2, 1010, W // 2 + lw // 2, 1016], fill=GOLD)
    text(d, (W // 2, 1110), "Tukio jipya kila siku", font("Inter-Medium.otf", 50), MUTED, prog(t, 0.8, 0.6))
    text(d, (W // 2, 1300), "Fuatilia · Like · Share", font("Inter-Bold.otf", 52), WHITE, prog(t, 1.2, 0.6))
    footer(d, prog(t, 1.0, 0.6))

SCENES = [("01_intro", s_intro, 4.0), ("02_year", s_year, 5.0), ("03_canal", s_canal, 6.5),
          ("04_route", s_route, 7.0), ("05_build", s_build, 6.0), ("06_also", s_also, 6.0),
          ("07_outro", s_outro, 4.0)]
FADE = 0.35

def frame(fn, t, dur):
    img = BG.copy(); d = ImageDraw.Draw(img)
    fn(t, d, img)
    a = min(clamp(t / FADE), clamp((dur - t) / FADE))
    if a < 1: img = Image.blend(BG, img, a)
    return img

def render(name, fn, dur):
    tmp, final = f"{OUT}/{name}.tmp.mp4", f"{OUT}/{name}.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "18",
                          "-preset", "veryfast", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for i in range(int(dur * FPS)):
        p.stdin.write(frame(fn, i / FPS, dur).tobytes())
    p.stdin.close()
    if p.wait() == 0: os.replace(tmp, final)
    else: raise SystemExit(f"ffmpeg failed on {name}")
    return final

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "preview":
        for name, fn, dur in SCENES:
            frame(fn, dur - 0.8, dur).save(f"{OUT}/prev_{name}.png")
        sys.exit()
    files = [render(*s) for s in SCENES]
    with open(f"{OUT}/list.txt", "w") as f:
        f.writelines(f"file '{x}'\n" for x in files)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", f"{OUT}/list.txt",
                    "-c", "copy", f"{OUT}/Leo_Katika_Historia_17_Novemba.mp4"], check=True)
    print("done")
