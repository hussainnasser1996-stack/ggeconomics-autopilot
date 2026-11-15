#!/usr/bin/env python3
"""pick.py <tag> <out.json> id[:dur] ...  -> exact clip list inside shot bounds, + a verification sheet"""
import sys, json, subprocess
tag, out, picks = sys.argv[1], sys.argv[2], sys.argv[3:]
S = {s["id"]: s for s in json.load(open(f"work/{tag}/shots.json"))}
clips = []
for p in picks:
    parts = p.split(":"); i = parts[0]; d = parts[1] if len(parts) > 1 else ""; off = float(parts[2]) if len(parts) > 2 else 0.0
    s = S[int(i)]
    a = s["start"] + 0.12 + off; avail = s["end"] - 0.08 - a
    dur = min(float(d) if d else avail, avail)
    clips.append({"src": tag, "from": round(a, 2), "dur": round(dur, 2), "shot": int(i)})
json.dump(clips, open(out, "w"), indent=1)
# verification: first + last frame of every clip
import cv2, numpy as np
cap = cv2.VideoCapture(f"work/{tag}.mp4"); tiles = []
for c in clips:
    row = []
    for t in (c["from"], c["from"] + c["dur"] - 0.05):
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000); ok, f = cap.read()
        f = cv2.resize(f, (240, 135)); cv2.putText(f, f"#{c['shot']} {t:.1f}", (4, 18), 0, 0.5, (58, 255, 212), 1); row.append(f)
    tiles.append(np.hstack(row))
while len(tiles) % 4: tiles.append(np.zeros_like(tiles[0]))
cv2.imwrite(out.replace(".json", "_check.jpg"), np.vstack([np.hstack(tiles[r*4:(r+1)*4]) for r in range(len(tiles)//4)]))
print(sum(c["dur"] for c in clips), "s total")
