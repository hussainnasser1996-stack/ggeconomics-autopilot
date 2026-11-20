#!/usr/bin/env python3
"""letterbox.py <date>: zoom each clip past the black cinema bars baked into game trailers (20 Nov review).
Trailers are often 2.39:1 inside a 16:9 file (Cyberpunk: 804 of 1080 rows are picture), so the 9:16 cover-crop kept
black bands top and bottom: ~20-25% of the phone screen was dead. ffmpeg cropdetect on each clip's own segment ->
clip["zoom"] = frame height / picture height (+2%). Writes spec.json clips (and clips.json when present)."""
import json, re, subprocess, sys
from collections import Counter
from pathlib import Path
GN = Path(__file__).resolve().parents[2]; Q = GN / "autopilot/queue" / sys.argv[1]
sp = json.load(open(Q / "spec.json")); clips = sp["spec"].get("clips") or []
cache = {}
for c in clips:
    f = GN / "studio/public/footage" / f"{c['src']}.mp4"
    if not f.exists(): continue
    if c["src"] not in cache:
        cache[c["src"]] = int(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=height",
                                              "-of", "csv=p=0", str(f)], capture_output=True, text=True).stdout.strip() or 0)
    H = cache[c["src"]]
    out = subprocess.run(["ffmpeg", "-hide_banner", "-ss", str(c["from"]), "-i", str(f), "-t", str(max(0.6, c["dur"])),
                          "-vf", "cropdetect=24:2:0", "-f", "null", "-"], capture_output=True, text=True).stderr
    crops = Counter(m.group(1) for m in re.finditer(r"crop=\d+:(\d+):\d+:\d+", out))
    if not H or not crops: continue
    ch = int(crops.most_common(1)[0][0])
    if ch < H * 0.55 or ch >= H * 0.97: continue           # near-black shot (can't tell) or no bars
    z = round(H / ch * 1.02, 3)
    c["zoom"] = max(c.get("zoom", 1), z)
    print(f"{c['src']} @{c['from']}: picture {ch}/{H} rows -> zoom {c['zoom']}")
json.dump(sp, open(Q / "spec.json", "w"), indent=1)
if (Q / "clips.json").exists(): json.dump(clips, open(Q / "clips.json", "w"), indent=1)
