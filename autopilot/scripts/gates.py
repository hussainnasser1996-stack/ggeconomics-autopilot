#!/usr/bin/env python3
"""gates.py <D>  — the publish gates, machine-checked (the cloud build has no human or LLM looking).
1. VO: what Whisper HEARD must match the script (word similarity >= 0.80) — catches mispronounced names/numbers.
2. OVERLAY SAFE: PASS (overlays clear of the Shorts/Reels UI).
3. critic: CONTRAST_MIN and CAPTION_LEGIBLE pass.
4. length 15-40 s. Exit 1 with reasons if any gate fails."""
import sys, json, re, difflib, subprocess
from pathlib import Path
Q = Path(__file__).resolve().parents[1] / "queue" / sys.argv[1]; bad = []
norm = lambda t: [w for w in re.sub(r"[^a-z0-9 ]", " ", t.lower().replace("-", " ")).split() if w]
script = " ".join(l.get("say", l["text"]) for l in json.load(open(Q / "script.json"))["lines"])
qa = (Q / "vo_qa.txt").read_text(); heard = qa.split("HEARD:", 1)[1] if "HEARD:" in qa else ""
sim = difflib.SequenceMatcher(None, norm(script), norm(heard)).ratio()
if sim < 0.80: bad.append(f"VO similarity {sim:.2f} < 0.80 (heard: {heard.strip()[:200]})")
if "OVERLAY SAFE: PASS" not in (Q / "overlay_safe.txt").read_text(): bad.append("overlay safe zones FAIL")
crit = (Q / "critic.txt").read_text() if (Q / "critic.txt").exists() else ""
for g in ("CONTRAST_MIN", "CAPTION_LEGIBLE"):
    if not re.search(rf"PASS \[[^\]]*\] {g}", crit): bad.append(f"critic {g} not PASS")
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(Q / "short.mp4")], capture_output=True, text=True).stdout or 0)
if not 15 <= dur <= 40: bad.append(f"duration {dur:.1f}s outside 15-40")
(Q / "gates.txt").write_text(f"VO similarity {sim:.2f}\nduration {dur:.1f}s\n" + ("PASS\n" if not bad else "FAIL\n" + "\n".join(bad) + "\n"))
print((Q / "gates.txt").read_text()); sys.exit(1 if bad else 0)
