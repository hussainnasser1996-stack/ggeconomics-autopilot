#!/usr/bin/env python3
"""autopick.py <D>  — choose the B-roll with no human/LLM eyes (cloud build).
Reads work/<tag>/shots.json (from shots.py) for the tag in queue/D/footage_resolved.json, the VO duration from
studio/public/vo/<id>/timeline.json, and writes spec.clips (+ carousel slide backgrounds when bg.at is null).

Rules (what the old LOOK step enforced):
- skip the first 7% and last 12% of the trailer (rating cards, logos, end slates, release-date text)
- skip black / white-flash shots and soft (blurry) shots; drop shots with heavy text (edge-dense flat areas)
- prefer motion + sharpness; spread picks across the trailer; never two neighbouring shots back to back
- avoid shots this source already used in the last 14 days (autopilot/log/used_shots.json)
- clip length 1.2-2.4 s, total >= VO + 2 s"""
import sys, json, math, random, datetime
from pathlib import Path
import numpy as np, cv2
GN = Path(__file__).resolve().parents[2]
D = sys.argv[1]; Q = GN / "autopilot/queue" / D
src = json.load(open(Q / "footage_resolved.json")); tag = src["tag"]
script = json.load(open(Q / "script.json"))
tl = json.load(open(GN / f"studio/public/vo/{script['id']}/timeline.json"))
need = float(tl.get("duration") or tl["lines"][-1]["end"]) + 2.5
shots = json.load(open(GN / f"work/{tag}/shots.json"))
total = max(s["end"] for s in shots)
used_p = GN / "autopilot/log/used_shots.json"
used = json.load(open(used_p)) if used_p.exists() else {}
cut = (datetime.date.fromisoformat(D) - datetime.timedelta(days=14)).isoformat()
recent = {(u["src_id"], round(u["start"], 1)) for d, lst in used.items() if d >= cut and d != D for u in lst}

cap = cv2.VideoCapture(str(GN / f"work/{tag}.mp4"))
def frame(t):
    cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000); ok, f = cap.read(); return f if ok else None
import subprocess, tempfile, os
def ocr_words(f):
    """confident words tesseract reads in the frame (title cards, logos, 'PLAY NOW', rating cards)"""
    g = cv2.cvtColor(cv2.resize(f, (960, 540)), cv2.COLOR_BGR2GRAY)
    n = 0
    for img in (g, 255 - g):                       # light-on-dark and dark-on-light
        fd, p = tempfile.mkstemp(suffix=".png"); os.close(fd); cv2.imwrite(p, img)
        try:
            out = subprocess.run(["tesseract", p, "-", "--psm", "11", "tsv"], capture_output=True, text=True, timeout=30).stdout
        except Exception: out = ""
        os.remove(p)
        for row in out.splitlines()[1:]:
            c = row.split("\t")
            if len(c) == 12 and c[11].strip() and float(c[10]) > 70 and sum(ch.isalpha() for ch in c[11]) >= 3: n += 1
    return n
def textiness(f):
    g = cv2.cvtColor(cv2.resize(f, (480, 270)), cv2.COLOR_BGR2GRAY)
    e = cv2.Canny(g, 120, 240) > 0
    flat = cv2.blur(g.astype(np.float32), (9, 9))
    # text = many sharp edges sitting on an otherwise flat/dark background
    return float((e & (flat < 60)).mean() * 100), float(e.mean() * 100)

cands = []
for s in shots:
    if s["start"] < total * 0.07 or s["end"] > total * 0.88: continue
    if s["dur"] < 1.35 or not (28 <= s["bright"] <= 225) or s["sharp"] < 120: continue
    if s["sat"] < 22 or s["motion"] < 3: continue          # grey logo slates / frozen holds
    if (src["id"], round(s["start"], 1)) in recent: continue
    mid = frame((s["start"] + s["end"]) / 2)
    if mid is None: continue
    t_dark, t_all = textiness(mid)
    if t_dark > 2.2: continue                      # title/rating card: white type on black
    if any(ocr_words(fr) >= 2 for fr in (mid, frame(s["start"] + 0.15), frame(s["end"] - 0.15)) if fr is not None): continue
    score = (s["motion"] + 2) * math.log10(s["sharp"] + 10) * (0.7 + min(s["sat"], 140) / 200)
    cands.append({**s, "score": score})
if len(cands) < 6: sys.exit(f"autopick: only {len(cands)} clean shots in this trailer (need 6+)")
if not cands: sys.exit("autopick: no usable shots")

rng = random.Random(D)
cands.sort(key=lambda s: -s["score"])
pool = cands[: max(14, int(len(cands) * 0.7))]
picked, t = [], 0.0
regions = 8
by_region = [[s for s in pool if int(s["start"] / total * regions) == r] for r in range(regions)]
order = []
while any(by_region):
    for r in rng.sample(range(regions), regions):
        if by_region[r]: order.append(by_region[r].pop(0))
order += [s for s in cands if s not in pool]             # then every other clean shot before any reuse
for s in order:
    if t >= need: break
    a = s["start"] + 0.12; dur = round(min(2.2, s["end"] - 0.08 - a, max(1.2, need - t)), 2)
    if dur < 1.2: continue
    picked.append({"src": tag, "from": round(a, 2), "dur": dur, "shot": s["id"]}); t += dur
for s in sorted(cands, key=lambda s: -s["dur"]):          # long shots: use their second half too
    if t >= need: break
    if s["dur"] >= 3.2 and any(p["shot"] == s["id"] for p in picked):
        a = s["start"] + s["dur"] / 2 + 0.1; dur = round(min(2.0, s["end"] - 0.08 - a), 2)
        if dur >= 1.2: picked.append({"src": tag, "from": round(a, 2), "dur": dur, "shot": s["id"]}); t += dur
k = 0
while t < need and picked:                                # still short: reuse a pick from the other half of the video
    s = dict(picked[(k * 3 + len(picked) // 2) % len(picked)]); s["from"] = round(s["from"] + 0.3, 2); s["dur"] = max(1.2, s["dur"] - 0.3)
    picked.append(s); t += s["dur"]; k += 1
# hook first: the single highest-scoring shot opens the video
best = max(picked, key=lambda c: next(x["score"] for x in cands if x["id"] == c["shot"]) if any(x["id"] == c["shot"] for x in cands) else 0)
picked.remove(best); picked.insert(0, best)
for i in range(1, len(picked) - 1):                       # no neighbouring shot ids back to back
    if abs(picked[i]["shot"] - picked[i - 1]["shot"]) <= 1:
        j = next((k for k in range(i + 1, len(picked)) if abs(picked[k]["shot"] - picked[i - 1]["shot"]) > 1), None)
        if j: picked[i], picked[j] = picked[j], picked[i]

sp = json.load(open(Q / "spec.json")); sp["spec"]["clips"] = picked
json.dump(sp, open(Q / "spec.json", "w"), indent=1)
json.dump(picked, open(Q / "clips.json", "w"), indent=1)
# carousel backgrounds
cp = Q / "carousel.json"
if cp.exists():
    c = json.load(open(cp)); bgs = sorted(picked, key=lambda x: -x["dur"])
    for i, sl in enumerate(c.get("slides", [])):
        bg = sl.setdefault("bg", {})
        if bg.get("at") is None: bg["src"] = tag; bg["at"] = round(bgs[i % len(bgs)]["from"] + 0.4, 2)
    json.dump(c, open(cp, "w"), indent=1)
used[D] = [{"src_id": src["id"], "start": round(next(s["start"] for s in shots if s["id"] == p["shot"]), 1)} for p in picked]
json.dump(used, open(used_p, "w"), indent=1)
print(f"autopick: {len(picked)} clips, {t:.1f}s for {need:.1f}s needed, from {len(cands)} usable shots")
