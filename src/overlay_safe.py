#!/usr/bin/env python3
"""overlay_safe.py <spec.json> <out_dir> — render key frames of DailyShort with the footage OFF, then check that
no overlay (cards, captions, chips, credit) sits in the Shorts/Reels UI zones. Exit 1 on failure.
Zones: right 13%, bottom 17% (platform buttons + caption), left 4%. The top progress bar (≤ 10 px) is allowed."""
import sys, json, subprocess
from pathlib import Path
import numpy as np
from PIL import Image
spec_p, out = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(); out.mkdir(parents=True, exist_ok=True)
GN = Path(__file__).resolve().parents[1]
s = json.load(open(spec_p)); s["spec"]["hideBroll"] = True
tl = json.load(open(GN / "studio/public" / s["spec"]["timelinePath"]))
pp = out / "props_nobroll.json"; json.dump(s, open(pp, "w"))
frames = sorted({int((l["start"] + (l["end"] - l["start"]) * 0.6) * 30) for l in tl["lines"]})
bad = []
for fr in frames:
    png = out / f"ov_{fr}.png"
    subprocess.run(["npx", "remotion", "still", "src/index.ts", "DailyShort", str(png), f"--frame={fr}", f"--props={pp}", "--log=error"],
                   cwd=GN / "studio", check=True, capture_output=True)
    a = np.asarray(Image.open(png).convert("L"), np.float32); H, W = a.shape
    ink = a > 150                       # overlay text/panels are bright on the dark ground
    zones = {"right": ink[12:int(H * .83), int(W * .87):], "bottom": ink[int(H * .83):, :], "left": ink[12:int(H * .83), :int(W * .04)]}
    for z, m in zones.items():
        if m.mean() > 0.002: bad.append(f"frame {fr}: {z} zone {m.mean()*100:.2f}% overlay ink")
print("OVERLAY SAFE: PASS" if not bad else "OVERLAY SAFE: FAIL\n  " + "\n  ".join(bad))
sys.exit(1 if bad else 0)
