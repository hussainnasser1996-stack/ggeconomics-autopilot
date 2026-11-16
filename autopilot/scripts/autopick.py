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
    if (src["id"], round(s["start"], 1)) in recent: continue
    mid = frame((s["start"] + s["end"]) / 2)
    if mid is None: continue
    t_dark, t_all = textiness(mid)
    if t_dark > 2.2: continue                      # title/rating card: white type on black
    score = (s["motion"] + 2) * math.log10(s["sharp"] + 10) * (0.7 + min(s["sat"], 140) / 200)
    cands.append({**s, "score": score})
if len(cands) < 6:                                # thin trailer: relax the recency + text filters
    cands = [{**s, "score": (s["motion"] + 2) * math.log10(s["sharp"] + 10)} for s in shots
             if total * 0.05 <= s["start"] and s["end"] <= total * 0.92 and s["dur"] >= 1.3 and 20 <= s["bright"] <= 235]
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
for s in order:
    if t >= need: break
    a = s["start"] + 0.12; dur = round(min(2.4, s["end"] - 0.08 - a, max(1.2, need - t)), 2)
    if dur < 1.2: continue
    picked.append({"src": tag, "from": round(a, 2), "dur": dur, "shot": s["id"]}); t += dur
k = 0
while t < need and picked:                                # still short: reuse picks (thin trailer)
    s = dict(picked[k % len(picked)]); picked.append(s); t += s["dur"]; k += 1
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
