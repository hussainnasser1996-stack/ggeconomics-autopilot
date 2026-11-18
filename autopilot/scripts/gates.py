#!/usr/bin/env python3
"""gates.py <D>  — the publish gates, machine-checked (the cloud build has no human or LLM looking).
1. VO: what Whisper HEARD must match the script (word similarity >= 0.80) — catches mispronounced names/numbers.
2. OVERLAY SAFE: PASS (overlays clear of the Shorts/Reels UI).
3. critic: CONTRAST_MIN and CAPTION_LEGIBLE pass.
4. length 15-40 s. 5. day countdowns agree across script + on-screen text. Exit 1 with reasons if any gate fails."""
import sys, json, re, difflib, subprocess
from pathlib import Path
Q = Path(__file__).resolve().parents[1] / "queue" / sys.argv[1]; bad = []
NUMW = set("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen "
           "eighteen nineteen twenty thirty forty fifty sixty seventy eighty ninety hundred thousand million billion trillion "
           "point dollars dollar percent first second third fourth fifth sixth seventh eighth ninth tenth eleventh twelfth "
           "thirteenth nineteenth twentieth thirtieth and".split())
# Whisper writes numbers as digits ("$79.99"), scripts spell them ("seventy-nine ninety-nine"): compare the WORDS around
# the numbers, and check the numbers separately by count, so a correct read isn't failed on notation.
def norm(t):
    w = [x for x in re.sub(r"[^a-z0-9 ]", " ", t.lower().replace("-", " ")).split() if x]
    return [x for x in w if x not in NUMW and not re.fullmatch(r"\d+(st|nd|rd|th|s)?|\d+", x)]
script = " ".join(l.get("say", l["text"]) for l in json.load(open(Q / "script.json"))["lines"])
qa = (Q / "vo_qa.txt").read_text(); heard = qa.split("HEARD:", 1)[1] if "HEARD:" in qa else ""
edit = json.load(open(Q / "script.json")).get("mode") == "edit"
sim = 1.0 if edit else difflib.SequenceMatcher(None, norm(script), norm(heard)).ratio()
if not edit and sim < 0.80: bad.append(f"VO similarity {sim:.2f} < 0.80 (heard: {heard.strip()[:200]})")
if "OVERLAY SAFE: PASS" not in (Q / "overlay_safe.txt").read_text(): bad.append("overlay safe zones FAIL")
crit = (Q / "critic.txt").read_text() if (Q / "critic.txt").exists() else ""
for g in (("CONTRAST_MIN",) if edit else ("CONTRAST_MIN", "CAPTION_LEGIBLE")):   # music-only edits have no word captions (17 Nov)
    if not re.search(rf"PASS \[[^\]]*\] {g}", crit): bad.append(f"critic {g} not PASS")
# countdowns must agree everywhere (17b, 16 Nov: badge "2 DAYS TO GO", last line "1 day to go")
WN = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "a": 1}
def strings(o):
    if isinstance(o, str): return [o]
    if isinstance(o, dict): o = list(o.values())
    return [x for v in o for x in strings(v)] if isinstance(o, list) else []
txt = " ".join(strings(json.load(open(Q / "script.json")))) + " " + (" ".join(strings(json.load(open(Q / "spec.json")))) if (Q / "spec.json").exists() else "")
counts = {int(n) if n.isdigit() else WN[n] for n in re.findall(r"\b(\d+|one|two|three|four|five|six|seven|a)\s+days?\s+(?:to go|to gta|until|left|away|out)\b", txt.lower())}
if len(counts) > 1: bad.append(f"countdown disagrees with itself: {sorted(counts)} days")
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(Q / "short.mp4")], capture_output=True, text=True).stdout or 0)
if not (10 if edit else 15) <= dur <= 40: bad.append(f"duration {dur:.1f}s outside 15-40")
(Q / "gates.txt").write_text(f"VO similarity {sim:.2f}\nduration {dur:.1f}s\n" + ("PASS\n" if not bad else "FAIL\n" + "\n".join(bad) + "\n"))
print((Q / "gates.txt").read_text()); sys.exit(1 if bad else 0)
