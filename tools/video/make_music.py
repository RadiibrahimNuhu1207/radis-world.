"""Calm, historical-documentary instrumental (36 s): slow strings, soft felt piano, cello drone, hall reverb.
No drums. Gentle piano accents land on key picture moments. Output: music2.wav"""
import os
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve
from scipy.io import wavfile

SR = 44100; DUR = 36.0; N = int(SR * DUR)
rng = np.random.default_rng(11)
L = np.zeros(N); R = np.zeros(N)
def hz(m): return 440 * 2 ** ((m - 69) / 12)
def lp(x, fc, o=2): return sosfilt(butter(o, fc, "low", fs=SR, output="sos"), x)
def hp(x, fc, o=2): return sosfilt(butter(o, fc, "high", fs=SR, output="sos"), x)

def add(sig, t0, g=1.0, pan=0.0):
    i = int(t0 * SR)
    if i >= N: return
    sig = sig[:N - i]
    L[i:i+len(sig)] += sig * g * np.sqrt(0.5 * (1 - pan))
    R[i:i+len(sig)] += sig * g * np.sqrt(0.5 * (1 + pan))

def env(n, a, r):
    e = np.ones(n); na, nr = int(a*SR), int(r*SR)
    e[:na] = (1 - np.cos(np.linspace(0, np.pi, na))) / 2
    e[-nr:] *= (1 + np.cos(np.linspace(0, np.pi, nr))) / 2
    return e

def strings(f, dur):
    """Ensemble: several detuned saw voices, slow vibrato, warm low-pass."""
    n = int(dur * SR); t = np.arange(n) / SR; out = np.zeros(n)
    for d in (-0.006, -0.002, 0.003, 0.007):
        vib = 1 + 0.0025 * np.sin(2*np.pi*(4.8 + d*100)*t + rng.uniform(0, 6))
        ph = np.cumsum(f * (1 + d) * vib) / SR
        out += 2 * (ph % 1) - 1
    return lp(out, 1100, 4) * env(n, 2.2, 2.6)

def cello(f, dur):
    n = int(dur * SR); t = np.arange(n) / SR
    vib = 1 + 0.003 * np.sin(2*np.pi*5*t)
    ph = 2*np.pi*np.cumsum(f*vib)/SR
    s = sum(np.sin(k*ph) / k**1.3 for k in range(1, 8))
    return lp(s, 700) * env(n, 3.0, 3.0)

def piano(f, dur=4.5, bright=2600):
    n = int(dur * SR); t = np.arange(n) / SR
    s = sum((0.9**k) * np.sin(2*np.pi*f*k*np.sqrt(1 + 0.0004*k*k)*t) * np.exp(-t*(1.1 + 0.6*k)) for k in range(1, 7))
    s[:120] *= np.linspace(0, 1, 120)
    return lp(s, bright)

# Progression (one chord every 4.5 s): Am - Fmaj7 - C - G - Am - Dm - Fmaj7 - E(sus->)
CH = [[57, 60, 64], [53, 57, 64], [55, 60, 64], [55, 59, 62],
      [57, 60, 64], [53, 57, 62], [52, 56, 59], [45, 57, 60, 64]]
BASS = [45, 41, 48, 43, 45, 38, 40, 33]
STEP = 4.5
for i, (ch, b) in enumerate(zip(CH, BASS)):
    t0 = i * STEP
    for j, m in enumerate(ch):
        add(strings(hz(m), STEP + 2.6), t0, 0.030, [-0.5, 0.0, 0.5, 0.25][j])
    add(cello(hz(b), STEP + 3.0), t0, 0.10, -0.15)


# Sparse felt-piano melody, quiet and spacious (A natural minor)
MEL = [(1.0, 76), (2.6, 72), (4.5, 69), (6.0, 72), (7.6, 77), (9.6, 76), (11.2, 72),
       (13.6, 79), (15.6, 76), (18.0, 74), (20.0, 72), (22.0, 71), (24.0, 72), (26.0, 69),
       (28.0, 74), (29.6, 71), (31.6, 72), (33.0, 69)]
for t0, m in MEL:
    add(piano(hz(m)), t0, 0.16, 0.2)
    add(piano(hz(m - 12), bright=1500), t0, 0.05, -0.2)

# Soft accents synced to the picture (no effects, just high piano notes)
for t0, m in [(1.2, 88), (14.6, 84), (16.3, 88)]:
    add(piano(hz(m), 5, 4000), t0, 0.07, 0.4)

# --- hall reverb (synthetic impulse response) ---
def ir(seconds, seed):
    r = np.random.default_rng(seed); n = int(seconds * SR); t = np.arange(n) / SR
    x = r.standard_normal(n) * np.exp(-t * 2.2)
    x = lp(x, 5000); x[:int(0.02*SR)] = 0
    return x / np.sqrt((x**2).sum())
dry = np.stack([L, R], 1)
wet = np.stack([fftconvolve(L, ir(3.2, 1))[:N], fftconvolve(R, ir(3.2, 2))[:N]], 1)
mix = 0.62 * dry + 0.55 * wet
mix = hp(mix.T, 35).T                       # remove sub rumble

fade_in = np.minimum(1, np.arange(N) / (1.5 * SR))
fade_out = np.clip((N - np.arange(N)) / (3.5 * SR), 0, 1) ** 1.5
mix *= (fade_in * fade_out)[:, None]
mix = np.tanh(mix * 1.2) / np.tanh(1.2)
mix *= 0.80 / np.abs(mix).max()
wavfile.write(os.path.join(os.path.dirname(os.path.abspath(__file__)), "music.wav"), SR, (mix * 32767).astype(np.int16))
print("ok")
