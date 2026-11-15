#!/usr/bin/env python3
"""shots.py — the 'eyes'. Split a video into shots and score each one so we can pick B-roll by LOOKING.

  .venv/bin/python src/shots.py work/v2.mp4 v2

Writes work/<tag>/shots.json and work/<tag>/sheet_XX.jpg (numbered contact sheets, 5x4 per page).
Per shot: start/end, motion (mean frame diff), sharpness (Laplacian var), brightness, saturation,
audio loudness, face count (OpenCV DNN-free Haar is unreliable -> we use a simple skin+frontal test
only as a hint), and 'textiness' (edge density in flat regions ~ HUD / title cards).
"""
import sys, json, subprocess
from pathlib import Path
import numpy as np, cv2, soundfile as sf
from scenedetect import open_video, SceneManager
from scenedetect.detectors import AdaptiveDetector

src, tag = Path(sys.argv[1]), sys.argv[2]
out = Path("work") / tag; out.mkdir(parents=True, exist_ok=True)

video = open_video(str(src))
sm = SceneManager(); sm.add_detector(AdaptiveDetector(min_scene_len=12))
sm.detect_scenes(video, frame_skip=1, show_progress=False)
scenes = [(s.get_seconds(), e.get_seconds()) for s, e in sm.get_scene_list()]
print(len(scenes), "shots")

wav = src.with_suffix(".wav")
audio, sr = sf.read(str(wav)) if wav.exists() else (None, 16000)
cap = cv2.VideoCapture(str(src)); fps = cap.get(cv2.CAP_PROP_FPS)


def grab(t):
    cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000); ok, fr = cap.read(); return fr if ok else None


shots = []
for i, (a, b) in enumerate(scenes):
    dur = b - a
    ts = np.linspace(a + 0.1, b - 0.1, max(2, min(6, int(dur * 2)))) if dur > 0.3 else [a]
    frames = [f for f in (grab(t) for t in ts) if f is not None]
    if not frames: continue
    small = [cv2.resize(f, (320, 180)) for f in frames]
    g = [cv2.cvtColor(s, cv2.COLOR_BGR2GRAY).astype(np.float32) for s in small]
    motion = float(np.mean([np.abs(g[k + 1] - g[k]).mean() for k in range(len(g) - 1)])) if len(g) > 1 else 0
    mid = small[len(small) // 2]
    hsv = cv2.cvtColor(mid, cv2.COLOR_BGR2HSV)
    sharp = float(cv2.Laplacian(cv2.cvtColor(mid, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var())
    loud = 0.0
    if audio is not None:
        seg = audio[int(a * sr): int(b * sr)]
        loud = float(20 * np.log10(np.sqrt(np.mean(seg ** 2)) + 1e-6)) if len(seg) else -90
    shots.append(dict(id=i, start=round(a, 2), end=round(b, 2), dur=round(dur, 2), motion=round(motion, 2),
                      sharp=round(sharp, 1), bright=round(float(hsv[..., 2].mean()), 1),
                      sat=round(float(hsv[..., 1].mean()), 1), loud_db=round(loud, 1)))
    th = cv2.resize(frames[len(frames) // 2], (384, 216))
    cv2.rectangle(th, (0, 0), (150, 30), (0, 0, 0), -1)
    cv2.putText(th, f"#{i} {a:.0f}s {dur:.1f}", (4, 21), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (58, 255, 212), 1)
    cv2.imwrite(str(out / f"th_{i:04d}.jpg"), th)

json.dump(shots, open(out / "shots.json", "w"), indent=1)
# contact sheets 5x4
ths = sorted(out.glob("th_*.jpg"))
for p in range(0, len(ths), 20):
    imgs = [cv2.imread(str(x)) for x in ths[p:p + 20]]
    while len(imgs) < 20: imgs.append(np.zeros_like(imgs[0]))
    rows = [np.hstack(imgs[r * 5:(r + 1) * 5]) for r in range(4)]
    cv2.imwrite(str(out / f"sheet_{p // 20:02d}.jpg"), np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 80])
print("sheets:", len(range(0, len(ths), 20)))
