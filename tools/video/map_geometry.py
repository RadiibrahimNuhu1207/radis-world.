"""Build Stewdio XML for Leo Katika Historia - 17 Novemba (v2, real map)."""
import json, math
from shapely.geometry import shape, box, Polygon, MultiPolygon
from shapely.ops import unary_union
from xml.sax.saxutils import escape

W, H = 1080, 1920
NAVY, NAVY2 = "#0B162C", "#14284A"
GOLD, WHITE, MUTED, SEA = "#F2B544", "#F5F2EB", "#96A5BE", "#2A6EAA"
LAND, LANDEDGE = "#1F3A63", "#2E5385"
HEAD = 'font="Bricolage Grotesque" font-weight="800"'

# ---------- map projection ----------
LON0, LON1, LAT0, LAT1 = -22, 58, -38, 50
MW = 980; MH = round(MW * (LAT1 - LAT0) / (LON1 - LON0))
MX, MY = 50, 330
def proj(lon, lat):
    return ((lon - LON0) / (LON1 - LON0) * MW, (LAT1 - lat) / (LAT1 - LAT0) * MH)
def scr(lon, lat):
    x, y = proj(lon, lat); return MX + x, MY + y

feats = json.load(open("countries.geojson"))["features"]
bbox = box(LON0, LAT0, LON1, LAT1)
geoms, egypt, tz = [], None, None
for f in feats:
    g = shape(f["geometry"])
    if not g.intersects(bbox): continue
    name = f["properties"]["ADMIN"]
    if name == "Egypt": egypt = g
    if name == "United Republic of Tanzania": tz = g
    geoms.append(g)
land = unary_union(geoms).intersection(bbox)

def to_path(g, tol=0.12, min_area=0.25):
    g = g.simplify(tol, preserve_topology=True)
    polys = [g] if isinstance(g, Polygon) else list(getattr(g, "geoms", []))
    parts = []
    for p in polys:
        if not isinstance(p, Polygon) or p.area < min_area: continue
        pts = [proj(*c) for c in p.exterior.coords]
        parts.append("M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + " Z")
    return " ".join(parts)

def chaikin(pts, n=3):
    for _ in range(n):
        out = [pts[0]]
        for a, b in zip(pts, pts[1:]):
            out += [(0.75*a[0]+0.25*b[0], 0.75*a[1]+0.25*b[1]), (0.25*a[0]+0.75*b[0], 0.25*a[1]+0.75*b[1])]
        out.append(pts[-1]); pts = out
    return pts

def route(wps):
    pts = chaikin([proj(*w) for w in wps])
    return "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)

START = (-1.5, 49.5)   # English Channel
DAR = (39.3, -6.8)
CAPE = [START, (-11, 45), (-14, 33), (-21, 18), (-19, 6), (-6, -1), (6, -12), (10, -26),
        (18.5, -36.8), (27, -35.5), (35, -30), (41.5, -22), (42.5, -14), (41, -9), DAR]
SUEZ = [START, (-11, 45), (-10.5, 38), (-5.6, 35.95), (4, 37.6), (12, 37.6), (20, 34.5),
        (29, 32.6), (32.3, 31.3), (32.55, 29.9), (35.2, 26.5), (38.5, 20), (41.5, 15),
        (43.4, 12.6), (48, 12.3), (52.2, 11.4), (50.5, 5), (46, -1), (42, -5), DAR]

def vec(name, d, extra='', anims='', clip=''):
    return (f'<vector name="{name}" view-box="0 0 {MW} {MH}" anchor="0 0" position="{MX} {MY}" '
            f'size="{MW} {MH}" {extra} {clip}><path d="{d}" />{anims}</vector>')

def kf(field, pairs, easing="bezier(0.2 0 0 1)"):
    ks = "".join(f'<keyframe time="{t}" value="{v}" easing="{easing}" />' for t, v in pairs)
    return f'<animation field="{field}">{ks}</animation>'

def fade_in(t0, dur=0.5): return kf("opacity", [(t0, 0), (t0 + dur, 1)])

def text(name, s, x, y, w, size, color, weight=600, font="Inter", align="center", lh=1.2,
         lines=1, anims="", anchor="0.5 0.5", extra=""):
    h = round(lines * size * lh, 1)
    fnt = HEAD if font == "HEAD" else f'font="{font}" font-weight="{weight}"'
    return (f'<text name="{name}" anchor="{anchor}" position="{x} {y}" size="{w} {h}" {fnt} '
            f'font-size="{size}" line-height="{lh}" text-align="{align}" color="{color}" '
            f'auto-resize="height" {extra}><content>{escape(s)}</content>{anims}</text>')

def rise(t0, x, y, dy=40, dur=0.6):
    return (kf("opacity", [(t0, 0), (t0 + dur, 1)]) +
            kf("position", [(t0, f"{x} {y+dy}"), (t0 + dur, f"{x} {y}")]))

def scene(name, start, dur, body):
    fade = kf("opacity", [(0, 0), (0.35, 1), (dur - 0.35, 1), (dur, 0)], "linear")
    return (f'<composition name="{name}" background="#00000000" position="{W/2} {H/2}" size="{W} {H}" '
            f'duration="{dur}" clip-start="{start}" clip-duration="{dur}" clip-trim="0">{body}{fade}</composition>')

# ---------- scenes ----------
s1 = (text("Kichwa", "LEO KATIKA HISTORIA", 540, 560, 900, 50, GOLD, 700, anims=rise(0.1, 540, 560)) +
      text("Tarehe", "17", 540, 880, 900, 420, WHITE, font="HEAD", lh=1.0,
           anims=fade_in(0.3) + kf("scale", [(0.3, "0.7 0.7"), (1.1, "1 1")])) +
      text("Mwezi", "NOVEMBA", 540, 1180, 900, 120, WHITE, font="HEAD", lh=1.0, anims=rise(0.8, 540, 1180)) +
      f'<vector name="Mstari" fill="{GOLD}" position="540 1290" size="500 8">'
      f'<rect corner-radius="4" />{kf("scale", [(1.2, "0 1"), (2.0, "1 1")])}</vector>' +
      text("Utangulizi", "Siku hii, miaka iliyopita…", 540, 1400, 900, 46, MUTED, 500, anims=fade_in(1.8)))

s2 = (text("Mwaka", "1869", 540, 700, 1000, 320, GOLD, font="HEAD", lh=1.0,
           anims=fade_in(0.1) + kf("scale", [(0.1, "1.25 1.25"), (1.0, "1 1")])) +
      text("Kichwa cha habari", "Mfereji wa Suez wafunguliwa rasmi", 540, 1040, 920, 96, WHITE,
           font="HEAD", lh=1.1, lines=2, anims=rise(0.9, 540, 1040)) +
      text("Mahali", "Misri  ·  17 Novemba 1869", 540, 1240, 900, 46, MUTED, 500, anims=fade_in(1.6)))

cape_d, suez_d = route(CAPE), route(SUEZ)
sx, sy = scr(32.4, 30.6); dx, dy = scr(*DAR); cx, cy = scr(18.5, -34.4)
s3 = (vec("Ardhi", to_path(land), f'fill="{LAND}"',
          kf("opacity", [(0, 0), (0.8, 1)])) +
      vec("Misri", to_path(egypt, 0.05, 0.01), f'fill="{GOLD}"',
          kf("opacity", [(0.8, 0), (1.4, 0.55)])) +
      vec("Tanzania", to_path(tz, 0.05, 0.01), f'fill="{GOLD}"',
          kf("opacity", [(7.4, 0), (8.0, 0.55)])) +
      text("Ulaya", "ULAYA", *scr(8, 47.5), 300, 40, WHITE, 700, anims=fade_in(0.6)) +
      text("Afrika", "AFRIKA", *scr(17, 6), 400, 64, "#3E5F8F", 800, anims=fade_in(0.6)) +
      text("Lebo Misri", "Misri", scr(27, 24)[0], scr(27, 24)[1], 200, 34, WHITE, 600, anims=fade_in(1.2)) +
      vec("Njia ya Rasi", cape_d,
          f'stroke="{MUTED}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"',
          kf("stroke-end", [(1.6, 0), (4.4, 1)], "bezier(0.4 0 0.2 1)")) +
      text("Lebo Rasi", "Kabla: kuzunguka\nRasi ya Tumaini Jema", cx - 30, cy + 10, 380, 32, MUTED, 600,
           align="right", lines=2, anchor="1 0.5", anims=fade_in(3.6)) +
      vec("Njia ya Suez", suez_d,
          f'stroke="{GOLD}" stroke-width="9" stroke-linecap="round" stroke-linejoin="round"',
          kf("stroke-end", [(5.0, 0), (7.4, 1)], "bezier(0.4 0 0.2 1)")) +
      f'<vector name="Alama ya Suez" fill="{GOLD}" position="{sx:.1f} {sy:.1f}" size="30 30"><ellipse />'
      f'{kf("scale", [(5.6, "0 0"), (6.0, "1.4 1.4"), (6.4, "1 1")])}</vector>' +
      text("Lebo Suez", "Mfereji wa Suez", sx + 40, sy - 6, 360, 36, GOLD, 800, align="left",
           anchor="0 0.5", anims=fade_in(5.9)) +
      f'<vector name="Alama ya Dar" fill="{WHITE}" position="{dx:.1f} {dy:.1f}" size="24 24"><ellipse />'
      f'{kf("scale", [(7.3, "0 0"), (7.7, "1.4 1.4"), (8.0, "1 1")])}</vector>' +
      text("Lebo Tanzania", "Tanzania", dx + 30, dy + 4, 260, 36, WHITE, 800, align="left",
           anchor="0 0.5", anims=fade_in(7.6)) +
      text("Maelezo", "Meli hazikuhitaji tena kuzunguka Afrika nzima", 540, 1600, 940, 54, WHITE, 700,
           lines=2, anims=rise(8.2, 540, 1600)))

s4 = (text("Ujenzi", "Ujenzi ulichukua", 540, 560, 900, 56, MUTED, 600, anims=fade_in(0.1)) +
      text("Miaka", "miaka ~10", 540, 760, 1000, 200, WHITE, font="HEAD", lh=1.0, anims=rise(0.3, 540, 760)) +
      f'<vector name="Msingi wa mstari" fill="{NAVY2}" position="540 1040" size="760 28"><rect corner-radius="14" /></vector>' +
      f'<vector name="Mstari wa maendeleo" fill="{GOLD}" anchor="0 0.5" position="160 1040" size="760 28">'
      f'<rect corner-radius="14" />{kf("scale", [(0.8, "0 1"), (3.0, "1 1")], "bezier(0.4 0 0.2 1)")}</vector>' +
      text("1859", "1859", 160, 1120, 300, 56, WHITE, 700, align="left", anchor="0 0.5", anims=fade_in(0.8)) +
      text("1869", "1869", 920, 1120, 300, 56, GOLD, 800, align="right", anchor="1 0.5", anims=fade_in(2.8)) +
      text("Umuhimu", "Hadi leo, ni moja ya njia muhimu zaidi za meli duniani", 540, 1340, 880, 50, WHITE, 600,
           lines=2, anims=rise(3.0, 540, 1340)))

def item(i, yr, s, y, t0):
    return (f'<vector name="Upau {yr}" fill="{GOLD}" anchor="0 0" position="120 {y-10}" size="8 210"><rect />{fade_in(t0)}</vector>' +
            text(f"Mwaka {yr}", yr, 170, y + 30, 400, 84, WHITE, font="HEAD", lh=1.0, align="left",
                 anchor="0 0.5", anims=rise(t0, 170, y + 30, 0)) +
            text(f"Tukio {yr}", s, 170, y + 140, 780, 46, MUTED, 500, align="left", anchor="0 0.5",
                 lh=1.25, lines=2, anims=fade_in(t0 + 0.2)))
s5 = (text("Pia leo", "PIA LEO", 540, 440, 900, 110, GOLD, font="HEAD", lh=1.0, anims=rise(0, 540, 440)) +
      item(0, "1970", "Lunokhod 1 — roboti ya kwanza kutembea kwenye Mwezi", 680, 0.6) +
      item(1, "1939", "Chanzo cha Siku ya Kimataifa ya Wanafunzi", 1080, 1.8))

s6 = (text("Leo katika", "LEO KATIKA", 540, 760, 1000, 140, WHITE, font="HEAD", lh=1.0, anims=rise(0.1, 540, 760)) +
      text("Historia", "HISTORIA", 540, 905, 1000, 140, GOLD, font="HEAD", lh=1.0, anims=rise(0.3, 540, 905)) +
      f'<vector name="Mstari wa mwisho" fill="{GOLD}" position="540 1010" size="400 6"><rect corner-radius="3" />'
      f'{kf("scale", [(0.6, "0 1"), (1.2, "1 1")])}</vector>' +
      text("Kila siku", "Tukio jipya kila siku", 540, 1110, 900, 50, MUTED, 500, anims=fade_in(0.8)) +
      text("Wito", "Fuatilia  ·  Like  ·  Share", 540, 1300, 900, 54, WHITE, 700, anims=rise(1.2, 540, 1300)))

SC = [("1 Utangulizi", 0, 4, s1), ("2 Mwaka", 4, 5, s2), ("3 Ramani", 9, 11, s3),
      ("4 Ujenzi", 20, 6, s4), ("5 Pia leo", 26, 6, s5), ("6 Mwisho", 32, 4, s6)]
TOTAL = 36

header = (text("Kichwa cha juu", "LEO KATIKA HISTORIA", 540, 150, 900, 40, GOLD, 700,
               extra='clip-start="4" clip-duration="28" clip-trim="0"',
               anims=kf("opacity", [(0, 0), (0.4, 1), (27.6, 1), (28, 0)], "linear")) +
          text("Tarehe ya juu", "17 NOVEMBA", 540, 205, 900, 34, MUTED, 500,
               extra='clip-start="4" clip-duration="28" clip-trim="0"',
               anims=kf("opacity", [(0, 0), (0.4, 1), (27.6, 1), (28, 0)], "linear")))
footer = text("Sahihi", "Radi the Storyteller", 540, 1800, 900, 34, MUTED, 600)
bg = (f'<vector name="Mwanga wa nyuma" fill="{NAVY2}" opacity="0.6" position="540 1500" size="1600 1400">'
      f'<ellipse /></vector>')

xml = (f'<composition name="Leo Katika Historia – 17 Novemba" background="{NAVY}" '
       f'position="540 960" size="{W} {H}" duration="{TOTAL}">' + bg +
       "".join(scene(n, s, d, b) for n, s, d, b in SC) + header + footer + '</composition>')
open("lkh.xml", "w").write(xml)
print(len(xml), "chars; map", MW, MH)
