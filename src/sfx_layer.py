#!/usr/bin/env python3
"""v2 sound: layer CC0 Kenney foley on top of the synthesised ident/sting/kit (keeps cue frames from sfx_ident.py)."""
import numpy as np, soundfile as sf, librosa
from pathlib import Path
R = Path(__file__).resolve().parents[1]; K = R / "assets/kenney"; OUT = R / "studio/public/sfx"
SR, FPS = 48000, 30
def k(name, gain=1.0, pitch=0):
    p = next(K.rglob(name + ".ogg"))
    y, _ = librosa.load(p, sr=SR, mono=True)
    if pitch: y = librosa.effects.pitch_shift(y, sr=SR, n_steps=pitch)
    return y / (np.abs(y).max() + 1e-9) * gain
def load(name):
    y, _ = sf.read(OUT / name); return y.mean(1) if y.ndim > 1 else y
def place(buf, x, frame):
    s = int(frame / FPS * SR); e = min(len(buf), s + len(x)); buf[s:e] += x[: e - s]
def stereo(m, w=0.3):
    d = int(0.011 * SR); r = np.concatenate([np.zeros(d), m[:-d]]); return np.stack([m, (1 - w) * m + w * r], 1)
def norm(x, p=0.89): return x / (np.abs(x).max() + 1e-9) * p

# ---- IDENT v2 ----
base = load("ident_synth.wav") if (OUT / "ident_synth.wav").exists() else load("ident.wav")
sf.write(OUT / "ident_synth.wav", stereo(base, 0), SR)  # keep the original synth stem
b = base * 0.8
place(b, k("tick_001", 0.25), 2); place(b, k("tick_002", 0.25), 10)
place(b, k("phaserUp3", 0.22), 32)
place(b, k("lowFrequency_explosion_000", 0.9), 48)
place(b, k("impactMetal_heavy_000", 0.45), 48)
place(b, k("explosionCrunch_000", 0.35), 48)
place(b, k("glitch_001", 0.35), 49); place(b, k("glitch_003", 0.3), 58)
for i in range(0, 17, 2): place(b, k(f"click_00{1 + i % 5}", 0.12), 62 + i * 1.5)
place(b, k("powerUp2", 0.3), 92)
place(b, k("phaserDown2", 0.3), 106)
sf.write(OUT / "ident.wav", stereo(norm(b)), SR)

# ---- STING v2 ----
st = load("sting_synth.wav") if (OUT / "sting_synth.wav").exists() else load("sting.wav")
sf.write(OUT / "sting_synth.wav", stereo(st, 0), SR)
st = st * 0.8
place(st, k("lowFrequency_explosion_001", 0.8), 8); place(st, k("impactMetal_heavy_001", 0.4), 8); place(st, k("glitch_002", 0.3), 9)
sf.write(OUT / "sting.wav", stereo(norm(st)), SR)

# ---- KIT v2 (tip pop, card whoosh stays synth) ----
a, t2 = k("select_003"), k("tick_004"); n = max(len(a), len(t2)); a = np.pad(a, (0, n - len(a))) + 0.4 * np.pad(t2, (0, n - len(t2)))
sf.write(OUT / "blip.wav", stereo(norm(a, 0.7)), SR)
sf.write(OUT / "chime.wav", stereo(norm(k("confirmation_002"), 0.75)), SR)
print("ok")
