"""Language-free artwork for each history story: a dark brand-coloured map with a glowing marker (or a space scene)."""
import json, math, random, sys
from PIL import Image, ImageDraw, ImageFilter
from shapely.geometry import shape, box, Point

W, H, S = 1600, 900, 2          # output size, supersample
OUT = sys.argv[1]
NIGHT=(11,15,26); OCEAN=(14,22,38); LAND=(26,36,58); LAND_HI=(38,54,88); EDGE=(120,140,175); GOLD=(242,184,75); BLUE=(77,163,255)

# slug: (lon, lat, half-width in degrees, [arc from (lon,lat)])
SPOTS = {
 "suez-1869":(32.35,30.6,14,None), "wanafunzi-1939":(14.42,50.08,11,None), "uhuru-1961":(39.28,-6.82,14,None),
 "muungano-1964":(39.28,-6.82,9,(39.31,-6.13)), "mapinduzi-1964":(39.31,-6.13,5,None), "tanu-1954":(39.28,-6.82,10,None),
 "nyerere-1999":(-0.12,51.5,10,None), "kilimanjaro-1889":(37.35,-3.07,7,None), "oau-1963":(38.75,9.03,18,None),
 "mandela-1990":(18.42,-33.92,13,None), "ghana-1957":(-0.19,5.6,13,None), "worldcup-1930":(-56.16,-34.9,16,None),
 "worldcup-2010":(28.05,-26.2,14,None), "bayi-1974":(172.6,-43.5,13,None), "titanic-1912":(-49.95,41.73,32,(-1.4,50.9)),
 "great-pyramid":(31.13,29.98,9,None), "mansa-musa":(39.83,21.42,34,(-3.0,16.77)), "ibn-battuta-kilwa":(39.51,-8.96,8,None),
 "gutenberg-press":(8.27,50.0,10,None), "vasco-da-gama-east-africa":(40.12,-3.22,16,(18.47,-34.36)),
 "zanzibar-slave-market-closed":(39.31,-6.13,4,None), "berlin-conference":(13.4,52.52,34,None),
 "battle-of-adwa":(38.9,14.16,10,None), "maji-maji":(37.5,-9.5,10,None), "berlin-wall-falls":(13.4,52.52,8,None),
}
SPACE = {"lunokhod-1970":"moon_imbrium", "apollo-1969":"moon_tranq", "gagarin-1961":"orbit"}

feats = [shape(f["geometry"]) for f in json.load(open(sys.argv[0].replace("make_art.py","countries.geojson")))["features"]]

def backdrop():
    im = Image.new("RGB", (W*S, H*S), NIGHT)
    d = ImageDraw.Draw(im)
    for y in range(0, H*S, 4*S): d.line([(0,y),(W*S,y)], fill=(16,22,36))   # fine engraving lines
    return im

def glow(im, xy, r, color, alpha):
    g = Image.new("RGBA", im.size, (0,0,0,0)); gd = ImageDraw.Draw(g)
    x, y = xy; gd.ellipse([x-r, y-r, x+r, y+r], fill=color + (alpha,))
    g = g.filter(ImageFilter.GaussianBlur(r*0.55))
    im.paste(Image.alpha_composite(im.convert("RGBA"), g).convert("RGB"))

def pin(im, xy):
    glow(im, xy, 260*S, BLUE, 70); glow(im, xy, 90*S, GOLD, 120)
    d = ImageDraw.Draw(im); x, y = xy
    for r, w, c in ((44, 2, (242,184,75)), (24, 2, (242,184,75))):
        d.ellipse([x-r*S, y-r*S, x+r*S, y+r*S], outline=c, width=w*S)
    d.ellipse([x-9*S, y-9*S, x+9*S, y+9*S], fill=GOLD)

def mapart(lon, lat, half, arc):
    im = backdrop(); d = ImageDraw.Draw(im)
    k = math.cos(math.radians(lat)); hw = half / max(k, .35)    # degrees of longitude across half the width
    cx = lon - hw * (0.68 - 0.5) * 2                            # put the marker at 68% across
    lon0, lon1 = cx - hw, cx + hw; hh = hw * k * H / W; lat0, lat1 = lat - hh, lat + hh
    P = lambda lo, la: ((lo - lon0) / (lon1 - lon0) * W * S, (lat1 - la) / (lat1 - lat0) * H * S)
    # ocean tint + graticule
    d.rectangle([0,0,W*S,H*S], fill=OCEAN)
    for y in range(0, H*S, 4*S): d.line([(0,y),(W*S,y)], fill=(18,27,45))
    step = 10 if half > 12 else 5
    for g in range(int(lon0//step)*step, int(lon1)+step, step): d.line([P(g, lat1), P(g, lat0)], fill=(30,42,66), width=S)
    for g in range(int(lat0//step)*step, int(lat1)+step, step): d.line([P(lon0, g), P(lon1, g)], fill=(30,42,66), width=S)
    view = box(lon0-2, lat0-2, lon1+2, lat1+2); here = Point(lon, lat)
    for f in feats:
        if not f.intersects(view): continue
        g = f.intersection(view); hot = f.buffer(0.05).contains(here)
        polys = [g] if g.geom_type == "Polygon" else [p for p in getattr(g, "geoms", []) if p.geom_type == "Polygon"]
        for p in polys:
            pts = [P(*c) for c in p.exterior.coords]
            if len(pts) > 2: d.polygon(pts, fill=LAND_HI if hot else LAND, outline=(70,88,120) if not hot else (200,160,80))
    if arc:
        a, b = P(*arc), P(lon, lat); mx, my = (a[0]+b[0])/2, (a[1]+b[1])/2 - abs(b[0]-a[0])*0.25
        pts = [((1-t)**2*a[0] + 2*(1-t)*t*mx + t*t*b[0], (1-t)**2*a[1] + 2*(1-t)*t*my + t*t*b[1]) for t in [i/80 for i in range(81)]]
        for i in range(0, 80, 2): d.line([pts[i], pts[i+1]], fill=GOLD, width=3*S)
        d.ellipse([a[0]-7*S, a[1]-7*S, a[0]+7*S, a[1]+7*S], outline=GOLD, width=2*S)
    pin(im, P(lon, lat))
    return im

def moon(site):
    im = backdrop(); random.seed(site)
    d = ImageDraw.Draw(im)
    for _ in range(260):
        x, y = random.randrange(W*S), random.randrange(H*S); r = random.choice([1,1,1,2])*S
        d.ellipse([x-r,y-r,x+r,y+r], fill=(200,210,230))
    cx, cy, R = int(W*S*0.68), int(H*S*0.52), int(H*S*0.62)
    glow(im, (cx, cy), R+60*S, BLUE, 60)
    d = ImageDraw.Draw(im)
    d.ellipse([cx-R, cy-R, cx+R, cy+R], fill=(52,60,78))
    for _ in range(70):                                          # craters
        a = random.random()*2*math.pi; rr = R*math.sqrt(random.random())*0.95; r = random.randint(5, 26)*S
        x, y = cx + rr*math.cos(a), cy + rr*math.sin(a)
        d.ellipse([x-r, y-r, x+r, y+r], fill=(44,51,68), outline=(66,75,96), width=S)
    for mx, my, mr in ((-.25,-.3,.17), (.15,-.05,.13), (.3,.25,.1)):   # dark seas
        d.ellipse([cx+mx*R-mr*R, cy+my*R-mr*R, cx+mx*R+mr*R, cy+my*R+mr*R], fill=(38,44,60))
    shade = Image.new("L", im.size, 0); sd = ImageDraw.Draw(shade)
    sd.ellipse([cx-R+R*0.35, cy-R-R*0.1, cx+R+R*0.6, cy+R+R*0.1], fill=150)
    shade = shade.filter(ImageFilter.GaussianBlur(60*S)); dark = Image.new("RGB", im.size, NIGHT)
    mask = Image.new("L", im.size, 0); ImageDraw.Draw(mask).ellipse([cx-R, cy-R, cx+R, cy+R], fill=255)
    from PIL import ImageChops
    im = Image.composite(dark, im, ImageChops.multiply(shade, mask))
    pin(im, (cx - 0.25*R, cy - 0.3*R) if site == "moon_imbrium" else (cx + 0.15*R, cy - 0.05*R))
    return im

def orbit():
    im = backdrop(); random.seed(3); d = ImageDraw.Draw(im)
    for _ in range(300):
        x, y = random.randrange(W*S), random.randrange(H*S); r = random.choice([1,1,2])*S
        d.ellipse([x-r,y-r,x+r,y+r], fill=(200,210,230))
    cx, cy, R = int(W*S*0.66), int(H*S*1.15), int(H*S*0.85)
    glow(im, (cx, cy), R+120*S, BLUE, 130)
    d = ImageDraw.Draw(im); d.ellipse([cx-R, cy-R, cx+R, cy+R], fill=(18,40,72))
    for i in range(1, 9):                                         # atmosphere bands
        r = R - i*10*S; d.ellipse([cx-r, cy-r, cx+r, cy+r], outline=(30+i*2, 70+i*3, 120+i*4), width=S)
    ox, oy, a, b = cx, cy - R*0.35, R*1.25, R*0.42
    for t in range(0, 360, 3):
        if t % 6: continue
        x1, y1 = ox + a*math.cos(math.radians(t)), oy + b*math.sin(math.radians(t))
        x2, y2 = ox + a*math.cos(math.radians(t+3)), oy + b*math.sin(math.radians(t+3))
        d.line([(x1,y1),(x2,y2)], fill=GOLD, width=3*S)
    pin(im, (ox + a*math.cos(math.radians(225)), oy + b*math.sin(math.radians(225))))
    return im

def finish(im, name):
    im = im.resize((W, H), Image.LANCZOS)
    v = Image.new("L", (W, H), 0); ImageDraw.Draw(v).ellipse([-W*0.25, -H*0.5, W*1.25, H*1.5], fill=255)
    v = v.filter(ImageFilter.GaussianBlur(120))
    im = Image.composite(im, Image.new("RGB", (W, H), NIGHT), v)
    im.save(f"{OUT}/{name}-art.jpg", quality=84, optimize=True, progressive=True)

only = sys.argv[2:] or list(SPOTS) + list(SPACE)
for slug in only:
    if slug in SPACE: im = orbit() if SPACE[slug] == "orbit" else moon(SPACE[slug])
    else: im = mapart(*SPOTS[slug])
    finish(im, slug); print("ok", slug)
