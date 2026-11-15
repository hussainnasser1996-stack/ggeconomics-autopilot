#!/usr/bin/env python3
"""Synthesise the SAVE STATE ident soundtrack + a sound kit, $0, frame-synced.

All cue times are in FRAMES @30fps so they line up with studio/src/Ident.tsx.
Outputs (48 kHz stereo wav) into studio/public/sfx/:
  ident.wav        4.0 s full ident
  sting.wav        1.2 s short sting (impact + chime) for Shorts end-cards / Twitch stinger
  whoosh.wav, blip.wav, tick.wav, boom.wav, chime.wav, glitch.wav  (kit for edits)
  bed_loop.wav     16 bars of a dark synthwave loop for news beds / Twitch 'starting soon'
"""
import numpy as np, soundfile as sf
from pathlib import Path

SR = 48000
FPS = 30
OUT = Path(__file__).resolve().parents[1] / "studio/public/sfx"
OUT.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(7)


def t(n):
    return np.arange(int(n)) / SR


def env_adsr(n, a=0.002, d=0.05, s=0.6, r=0.05):
    n = int(n); e = np.ones(n) * s
    A, D, R = int(a * SR), int(d * SR), int(r * SR)
    A = min(A, n); e[:A] = np.linspace(0, 1, A)
    D = min(D, n - A); e[A:A + D] = np.linspace(1, s, D)
    if R: e[-R:] *= np.linspace(1, 0, R)
    return e


def square(f, n, duty=0.5):
    ph = (f * t(n)) % 1.0
    return np.where(ph < duty, 1.0, -1.0)


def lp(x, a):  # one-pole lowpass, a in (0,1): smaller = darker
    y = np.empty_like(x); acc = 0.0
    for i, v in enumerate(x):
        acc += a * (v - acc); y[i] = acc
    return y


def hp(x, a):
    return x - lp(x, a)


def blip(f, dur=0.07, duty=0.25, vol=0.35):
    n = dur * SR
    return square(f, n, duty) * env_adsr(n, 0.001, dur * 0.5, 0.3, dur * 0.4) * vol


def boom(dur=1.6, vol=1.0):
    n = int(dur * SR); tt = t(n)
    f = 38 + 90 * np.exp(-tt * 18)              # pitch-dropping sub
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-tt * 2.6)
    click = rng.standard_normal(n) * np.exp(-tt * 90) * 0.6
    crunch = np.tanh(rng.standard_normal(n) * 3) * np.exp(-tt * 14) * 0.25
    x = body + lp(click, 0.35) + hp(crunch, 0.2)
    return np.tanh(x * 1.6) * vol


def riser(dur=0.9, vol=0.5):
    n = int(dur * SR); tt = t(n)
    noise = rng.standard_normal(n)
    # sweep filter open by blending lp coefficients chunk-wise
    out = np.zeros(n); chunks = 30
    for i in range(chunks):
        s, e = i * n // chunks, (i + 1) * n // chunks
        a = 0.02 + 0.6 * (i / chunks) ** 2
        out[s:e] = lp(noise[s:e], a)
    f = 200 * (2 ** (tt / dur * 3))
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.3
    return (out * 2 + tone) * (tt / dur) ** 2 * vol


def whoosh(dur=0.5, vol=0.5):
    n = int(dur * SR); tt = t(n)
    x = lp(rng.standard_normal(n), 0.15)
    e = np.sin(np.pi * tt / dur) ** 2
    return x * e * vol * 3


def glitch(dur=0.25, vol=0.35):
    n = int(dur * SR); x = np.zeros(n); i = 0
    while i < n:
        L = int(rng.integers(200, 1600))
        kind = rng.integers(0, 3)
        seg = (square(rng.uniform(300, 3000), L, 0.5) if kind == 0 else
               np.round(rng.standard_normal(L) * 2) / 2 if kind == 1 else np.zeros(L))
        x[i:i + L] = seg[: n - i]; i += L
    return x * np.exp(-t(n) * 6) * vol


def chime(vol=0.35):
    out = np.zeros(int(0.9 * SR))
    for k, (f, st) in enumerate([(1046.5, 0.0), (1568.0, 0.09)]):
        n = int(0.7 * SR); tt = t(n)
        tone = (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * f * 2 * tt)) * np.exp(-tt * 5)
        s = int(st * SR); out[s:s + n] += tone
    return out * vol


def tick(vol=0.25):
    n = int(0.03 * SR)
    return hp(rng.standard_normal(n), 0.5) * np.exp(-t(n) * 250) * vol


def place(buf, x, frame):
    s = int(frame / FPS * SR); e = min(len(buf), s + len(x))
    buf[s:e] += x[: e - s]


def stereo(m, width=0.0):
    d = int(0.011 * SR)
    r = np.concatenate([np.zeros(d), m[:-d]]) if width else m
    return np.stack([m, (1 - width) * m + width * r], 1)


def norm(x, peak=0.89):
    return x / (np.abs(x).max() + 1e-9) * peak


# ---------------- IDENT (120 frames) ----------------
ident = np.zeros(int(4.0 * SR) + SR)
place(ident, blip(1760, 0.04, 0.5, 0.25), 2)       # cursor blink
place(ident, blip(1760, 0.04, 0.5, 0.25), 10)
arp = [261.6, 329.6, 392.0, 523.3, 659.3, 784.0, 1046.5, 1318.5]   # C major climbing
for i, f in enumerate(arp):                         # 8 save-bar blocks, frames 14..38
    place(ident, blip(f, 0.08, 0.25, 0.32), 14 + i * 3)
    place(ident, blip(f * 0.5, 0.08, 0.5, 0.12), 14 + i * 3)
place(ident, riser(0.6, 0.45), 30)                  # riser into impact at 48
place(ident, whoosh(0.35, 0.4), 41)
place(ident, boom(1.8, 1.0), 48)                    # IMPACT
place(ident, glitch(0.3, 0.4), 48)
place(ident, glitch(0.15, 0.25), 58)
for k in range(17):                                 # tagline typing
    place(ident, tick(0.18), 62 + k * 1.5)
place(ident, chime(0.4), 92)                        # SAVED
ident = ident[: int(4.0 * SR)]
ident[-int(0.08 * SR):] *= np.linspace(1, 0, int(0.08 * SR))
sf.write(OUT / "ident.wav", stereo(norm(ident), 0.35), SR)

# ---------------- STING (36 frames) ----------------
st = np.zeros(int(1.6 * SR))
place(st, whoosh(0.3, 0.4), 0)
place(st, boom(1.3, 0.9), 8)
place(st, glitch(0.2, 0.35), 8)
place(st, chime(0.3), 18)
st[-int(0.1 * SR):] *= np.linspace(1, 0, int(0.1 * SR))
sf.write(OUT / "sting.wav", stereo(norm(st), 0.35), SR)

# ---------------- KIT ----------------
for name, x in {"whoosh": whoosh(0.5), "blip": blip(1046.5, 0.08), "tick": tick(),
                "boom": boom(1.6), "chime": chime(), "glitch": glitch(0.3)}.items():
    sf.write(OUT / f"{name}.wav", stereo(norm(x, 0.8), 0.3), SR)

# ---------------- BED LOOP: dark synthwave, 100 bpm, 16 bars ----------------
bpm = 100; beat = 60 / bpm; bars = 16
N = int(bars * 4 * beat * SR); bed = np.zeros(N)
roots = [55.0, 55.0, 43.65, 49.0]                  # A1 A1 F1 G1
for b in range(bars):
    root = roots[b % 4]
    for s in range(8):                              # 8th-note saw-ish bass
        tt0 = (b * 4 + s * 0.5) * beat
        n = int(beat * 0.5 * SR * 0.9)
        x = (square(root, n, 0.5) * 0.5 + square(root * 2, n, 0.3) * 0.2)
        x = lp(x, 0.08) * env_adsr(n, 0.003, 0.08, 0.5, 0.03)
        s0 = int(tt0 * SR); bed[s0:s0 + n] += x * 0.5
    for q in range(4):                              # kick on 1/3, hat on 8ths
        s0 = int((b * 4 + q) * beat * SR)
        if q in (0, 2):
            k = boom(0.35, 0.6); bed[s0:s0 + len(k)] += k[: N - s0]
        else:
            sn = hp(rng.standard_normal(int(0.18 * SR)), 0.3) * np.exp(-t(0.18 * SR) * 22) * 0.25
            bed[s0:s0 + len(sn)] += sn[: N - s0]
        for h in (0, 0.5):
            s1 = int((b * 4 + q + h) * beat * SR); th = tick(0.12)
            bed[s1:s1 + len(th)] += th[: N - s1]
    if b % 2 == 0:                                  # pad
        n = int(8 * beat * SR); tt = t(n)
        chord = [root * 4, root * 4 * 1.189, root * 4 * 1.498]
        pad = sum(np.sin(2 * np.pi * f * tt + np.sin(2 * np.pi * 0.3 * tt)) for f in chord)
        pad *= np.minimum(1, tt / 1.0) * np.minimum(1, (n / SR - tt) / 1.0) * 0.08
        s0 = int(b * 4 * beat * SR); bed[s0:s0 + n] += pad[: N - s0]
sf.write(OUT / "bed_loop.wav", stereo(norm(np.tanh(bed * 1.2), 0.7), 0.5), SR)
print("wrote", sorted(p.name for p in OUT.iterdir()))
