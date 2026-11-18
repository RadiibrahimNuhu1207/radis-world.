"""Three relaxing loops for reading/listening: calm strings & piano, night rain with soft distant thunder, ocean with mbira."""
import numpy as np, subprocess, sys
from scipy.signal import butter, sosfilt, fftconvolve
from scipy.io import wavfile
SR = 32000; DUR = 96.0; XF = 6.0; N = int((DUR + XF) * SR)
OUT = sys.argv[1]
def hz(m): return 440 * 2 ** ((m - 69) / 12)
def lp(x, fc, o=2): return sosfilt(butter(o, fc, "low", fs=SR, output="sos"), x)
def hp(x, fc, o=2): return sosfilt(butter(o, fc, "high", fs=SR, output="sos"), x)
def bp(x, a, b, o=2): return sosfilt(butter(o, [a, b], "band", fs=SR, output="sos"), x)
def env(n, a, r):
    e = np.ones(n); na, nr = max(1, int(a*SR)), max(1, int(r*SR))
    e[:na] = (1 - np.cos(np.linspace(0, np.pi, na))) / 2; e[-nr:] *= (1 + np.cos(np.linspace(0, np.pi, nr))) / 2; return e
class Mix:
    def __init__(s): s.L = np.zeros(N); s.R = np.zeros(N)
    def add(s, sig, t0, g=1.0, pan=0.0):
        i = int(t0 * SR)
        if i >= N: return
        sig = sig[:N - i]; s.L[i:i+len(sig)] += sig*g*np.sqrt(.5*(1-pan)); s.R[i:i+len(sig)] += sig*g*np.sqrt(.5*(1+pan))
def reverb(x, secs=3.2, wet=.35, seed=1):
    r = np.random.default_rng(seed); n = int(secs*SR)
    ir = r.standard_normal(n) * np.exp(-np.linspace(0, 7, n)); ir = lp(ir, 5000)
    y = fftconvolve(x, ir)[:len(x)]; y /= np.max(np.abs(y)) + 1e-9
    return x*(1-wet) + y*wet*np.max(np.abs(x))
def loopify(L, R):
    n, x = int(DUR*SR), int(XF*SR); fade = np.linspace(0, 1, x)
    out = []
    for c in (L, R):
        y = c[:n].copy(); y[:x] = y[:x]*fade + c[n:n+x]*(1-fade); out.append(y)
    return out
def save(name, L, R, gain_db=-16):
    L, R = loopify(L, R); peak = max(np.abs(L).max(), np.abs(R).max()) + 1e-9
    st = np.stack([L, R], 1) / peak * 10**(gain_db/20) * 3.2
    st = np.clip(st, -0.98, 0.98)
    wavfile.write(f"/tmp/amb/{name}.wav", SR, (st*32767).astype(np.int16))
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", f"/tmp/amb/{name}.wav", "-c:a", "libmp3lame", "-b:a", "80k", f"{OUT}/{name}.mp3"], check=True)
    print("ok", name)

rng = np.random.default_rng(7)
# 1 ---------------- calm strings + felt piano ("Old pages")
def strings(f, dur):
    n = int(dur*SR); t = np.arange(n)/SR; out = np.zeros(n)
    for d in (-.006, -.002, .003, .007):
        vib = 1 + .0025*np.sin(2*np.pi*(4.8 + d*100)*t + rng.uniform(0, 6)); ph = np.cumsum(f*(1+d)*vib)/SR; out += 2*(ph % 1) - 1
    return lp(out, 900, 4) * env(n, 3.0, 3.5)
def piano(f, dur=4.5):
    n = int(dur*SR); t = np.arange(n)/SR
    s = sum(np.sin(2*np.pi*f*k*t)*np.exp(-t*(1.4+k*.9))/k**1.6 for k in range(1, 7))
    return lp(s, 2600) * env(n, .004, .6)
m = Mix()
prog = [(50, [62, 65, 69]), (46, [62, 65, 70]), (53, [60, 65, 69]), (48, [60, 64, 67])]   # Dm Bb F C
for bar in range(int((DUR+XF)/12)+1):
    root, ch = prog[bar % 4]; t0 = bar*12
    m.add(strings(hz(root-12), 13.5), t0, .5)
    for i, n_ in enumerate(ch): m.add(strings(hz(n_), 13.5), t0, .22, pan=(i-1)*.5)
    for k, n_ in enumerate(rng.choice(ch + [n_+12 for n_ in ch], 4, replace=False)):
        m.add(piano(hz(int(n_)+12)), t0 + 1.5 + k*2.6 + rng.uniform(-.2, .2), .18, pan=rng.uniform(-.5, .5))
save("calm-pages", reverb(m.L, 3.5, .45, 1), reverb(m.R, 3.5, .45, 2))

# 2 ---------------- night rain + soft distant thunder ("Storm night")
m = Mix(); noise = lambda n: rng.standard_normal(n)
rain = lp(hp(noise(N), 400), 7000)*.35 + lp(noise(N), 900)*.25
m.add(rain, 0, 1, -.1); m.add(lp(hp(noise(N), 500), 6500)*.35, 0, 1, .1)
for _ in range(int((DUR+XF)*40)):                                     # droplets
    t0 = rng.uniform(0, DUR+XF); f = rng.uniform(2500, 6000); n = int(.03*SR); tt = np.arange(n)/SR
    m.add(np.sin(2*np.pi*f*tt)*np.exp(-tt*120), t0, rng.uniform(.02, .07), rng.uniform(-.8, .8))
for t0 in (14, 47, 79):                                               # distant thunder rolls
    n = int(9*SR); tt = np.arange(n)/SR; r = lp(noise(n), 140, 4)*np.exp(-tt*.45)*(1-np.exp(-tt*3))
    r *= 1 + .6*lp(np.abs(noise(n)), 3); m.add(r, t0, 1.6, rng.uniform(-.4, .4))
pad = sum(np.sin(2*np.pi*hz(n_)*np.arange(N)/SR) for n_ in (38, 45, 50))*lp(np.abs(noise(N)), .3)*2
m.add(lp(pad, 400)*.12, 0)
save("storm-night", reverb(m.L, 2.0, .25, 3), reverb(m.R, 2.0, .25, 4), -17)

# 3 ---------------- ocean + mbira ("Swahili coast")
m = Mix(); t = np.arange(N)/SR
for pan, ph in ((-.5, 0), (.5, 2.1)):
    swell = (.55 + .45*np.sin(2*np.pi*t/9.5 + ph))**2
    m.add(lp(hp(noise(N), 120), 2200)*swell*.5, 0, 1, pan)
def mbira(f, dur=3.0):
    n = int(dur*SR); tt = np.arange(n)/SR
    s = np.sin(2*np.pi*f*tt)*np.exp(-tt*2.2) + .35*np.sin(2*np.pi*f*5.4*tt)*np.exp(-tt*9) + .2*np.sin(2*np.pi*f*2*tt)*np.exp(-tt*4)
    return s*env(n, .002, .3)
scale = [62, 64, 67, 69, 71, 74, 76, 79]                              # D major pentatonic-ish
tb = 0.0; prev = 3
while tb < DUR + XF - 3:
    prev = int(np.clip(prev + rng.integers(-2, 3), 0, len(scale)-1))
    m.add(mbira(hz(scale[prev])), tb, .16, rng.uniform(-.4, .4))
    if rng.random() < .3: m.add(mbira(hz(scale[prev]-12)), tb, .12)
    tb += rng.choice([.55, .55, 1.1, 1.65])
save("swahili-coast", reverb(m.L, 2.5, .3, 5), reverb(m.R, 2.5, .3, 6), -17)
