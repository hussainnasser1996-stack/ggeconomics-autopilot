#!/usr/bin/env python3
"""pick_music.py <D>  — choose today's music bed and where it starts.
Rotates assets/music/lib (Kevin MacLeod / incompetech.com, CC BY 4.0: credit goes into the caption automatically),
never repeats any of the last 4 posts' tracks, and starts the track at its first big energy rise (the "drop") so the
hook lands on impact, not an intro. Writes queue/D/music.json {file, start, credit}."""
import sys, json, random, glob
from pathlib import Path
import numpy as np, librosa
GN = Path(__file__).resolve().parents[2]; D = sys.argv[1]; Q = GN / "autopilot/queue" / D
lib = sorted(glob.glob(str(GN / "assets/music/lib/*.m4a")))
recent = []
for q in sorted((GN / "autopilot/queue").iterdir(), reverse=True):
    if q.name != D and (q / "music.json").exists(): recent.append(json.load(open(q / "music.json"))["file"])
    if len(recent) >= 4: break
pool = [f for f in lib if Path(f).name not in recent] or lib
f = random.Random(D).choice(pool)
y, sr = librosa.load(f, sr=22050, mono=True, duration=100)
rms = librosa.feature.rms(y=y, hop_length=512)[0]; t = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=512)
win = int(2.0 * sr / 512); e = np.convolve(rms, np.ones(win) / win, mode="same")
rise = np.diff(e, prepend=e[0]); lim = t < max(10, t[-1] - 40)               # leave >= 40 s of music after the start
i = int(np.argmax(np.where(lim & (e > np.percentile(e, 60)), rise, -1)))
_, beats = librosa.beat.beat_track(y=y, sr=sr); bt = librosa.frames_to_time(beats, sr=sr)
start = float(bt[bt <= t[i]][-1]) if len(bt[bt <= t[i]]) else float(t[i])       # snap to a beat
title = Path(f).stem.replace("_", " ").title()
out = {"file": Path(f).name, "start": round(max(0.0, start - 0.25), 2),
       "credit": f'Music: "{title}" by Kevin MacLeod (incompetech.com), CC BY 4.0'}
json.dump(out, open(Q / "music.json", "w"), indent=1); print("music:", out)
