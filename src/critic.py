#!/usr/bin/env python3
"""Score a finished MP4 with the repo's critic metrics (tools/critic/metrics.py).
  python3 src/critic.py out/gta_short_9x16.mp4 studio/public/vo/gta_short/timeline.json gta_short
Scenes = VO lines (+ end card). Palette = SAVE STATE. Writes work/critic/<slug>/{report.json,contact.png}"""
import sys, json, subprocess
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools/critic"))
import metrics as M
mp4, tl, slug = sys.argv[1], sys.argv[2], sys.argv[3]
out = Path("work/critic") / slug; seq = out / "seq"; seq.mkdir(parents=True, exist_ok=True)
import re; w, h = map(int, re.findall(r"\d+", subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=width,height", "-of", "csv=p=0", mp4], capture_output=True, text=True).stdout)[:2])
portrait = h > w
M.BRAND = {"bg": (7, 7, 11), "ink2": (16, 16, 24), "line": (34, 34, 46), "lime": (0xD4, 0xFF, 0x3A), "cyan": (0x3A, 0xE0, 0xFF),
           "coral": (0xFF, 0x4D, 0x6D), "white": (0xF4, 0xF4, 0xF0), "dim": (0x8A, 0x8A, 0x99)}
M.SHORTS_UNSAFE = M.SHORTS_CHROME if portrait else M.BROADCAST_SAFE
if not any(seq.iterdir()):
    sw, shh = (540, 960) if portrait else (960, 540)
    subprocess.run(["ffmpeg", "-v", "error", "-i", mp4, "-vf", f"scale={sw}:{shh}", str(seq / "f-%05d.png")], check=True)
paths = sorted(seq.glob("f-*.png")); n = len(paths)
T = json.load(open(tl)); fps = 30
lines = T["lines"]; bounds = []
for i, l in enumerate(lines):
    s = int(l["start"] * fps); e = int((lines[i + 1]["start"] if i + 1 < len(lines) else T["duration"]) * fps) - 1
    bounds.append({"i": i, "kind": l["id"], "start": s, "end": min(e, n - 1), "dur": e - s + 1, "trans_in": 0, "trans_out": 0, "sc": {"dur": e - s + 1}})
m = M.motion_curve([str(p) for p in paths])
temporal = M.temporal_metrics(m, fps=fps, baseline=None, exclude=np.zeros(len(m), dtype=bool))
keys = sorted({min(n - 1, b["start"] + int(b["dur"] * r)) for b in bounds for r in (0.15, 0.5, 0.85)})
frames = [M.frame_metrics(str(paths[k]), portrait=portrait) for k in keys]
checks = M.evaluate(frames, temporal, bounds=bounds, m=m, fps=fps, landings=[])
sc = M.score(checks)
json.dump({"score": sc, "checks": checks, "temporal": temporal}, open(out / "report.json", "w"), indent=1, default=float)
print(f"SCORE {sc['score']}/100 ({sc['passed']}/{sc['total']})")
for c in checks:
    print(("  PASS " if c["pass"] else "  FAIL ") + f"[{c['severity']:8}] {c['id']:22} {c['detail']}")
