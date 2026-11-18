"""Synthesize book sounds: page flips (3 variations), book open, book close."""
import numpy as np, subprocess, os
from scipy.signal import butter, sosfilt
from scipy.io import wavfile
SR = 44100
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sfx_out"); os.makedirs(OUT, exist_ok=True)
def bp(x, lo, hi, o=2): return sosfilt(butter(o, [lo, hi], "band", fs=SR, output="sos"), x)
def lp(x, f): return sosfilt(butter(2, f, "low", fs=SR, output="sos"), x)

def page_flip(seed, dur=0.55):
    r = np.random.default_rng(seed); n = int(dur * SR); t = np.arange(n) / SR
    noise = r.standard_normal(n)
    # paper rustle: band-limited noise, amplitude grains (crinkles)
    grains = np.zeros(n)
    for _ in range(int(40 + 20 * r.random())):
        c = r.uniform(0.05, 0.42) * SR; w = r.uniform(0.004, 0.02) * SR
        grains += r.uniform(0.3, 1) * np.exp(-0.5 * ((np.arange(n) - c) / w) ** 2)
    swish_env = np.sin(np.pi * np.clip(t / (dur * 0.8), 0, 1)) ** 1.5
    rustle = bp(noise, 1200, 7000) * (0.35 * swish_env + 0.9 * grains * swish_env)
    swoosh = bp(noise, 300, 1500) * swish_env * 0.6               # air movement
    # final soft flap as the page lands
    lt = np.clip(t - dur * 0.72, 0, None)
    flap = lp(noise, 900) * np.exp(-lt * 45) * (t > dur * 0.72) * 1.4
    s = rustle + swoosh + flap
    s[:200] *= np.linspace(0, 1, 200); s[-400:] *= np.linspace(1, 0, 400)
    return s / np.abs(s).max() * 0.8

def thump(seed, dur=0.7, heavy=1.0):
    r = np.random.default_rng(seed); n = int(dur * SR); t = np.arange(n) / SR
    body = np.sin(2 * np.pi * (70 + 40 * np.exp(-t * 30)) * t) * np.exp(-t * 18) * heavy
    cover = lp(r.standard_normal(n), 1800) * np.exp(-t * 30) * 0.6
    air = bp(r.standard_normal(n), 400, 2500) * np.exp(-t * 9) * 0.25
    s = body + cover + air; s[:100] *= np.linspace(0, 1, 100); s[-300:] *= np.linspace(1, 0, 300)
    return s / np.abs(s).max() * 0.75

def save(name, s):
    wav = f"/tmp/{name}.wav"; wavfile.write(wav, SR, (s * 32767).astype(np.int16))
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", wav, "-c:a", "libmp3lame", "-b:a", "96k", f"{OUT}/{name}.mp3"], check=True)

for i in range(3): save(f"flip{i+1}", page_flip(i + 1, 0.5 + 0.06 * i))
open_ = np.concatenate([page_flip(9, 0.45) * 0.6, np.zeros(int(0.02 * SR))])
th = thump(4, 0.6, 0.6); mix = np.zeros(len(open_) + len(th) // 2)
mix[:len(open_)] += open_; mix[int(0.3 * SR):int(0.3 * SR) + len(th)] += th[:len(mix) - int(0.3 * SR)]
save("open", mix / np.abs(mix).max() * 0.8)
save("close", thump(5, 0.7, 1.0))
print(os.listdir(OUT))
