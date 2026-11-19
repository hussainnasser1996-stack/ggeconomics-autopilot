#!/usr/bin/env python3
"""autopick.py <D>  — choose the B-roll with no human/LLM eyes (cloud build).
Reads work/<tag>/shots.json (from shots.py) for the tag in queue/D/footage_resolved.json, the VO duration from
studio/public/vo/<id>/timeline.json, and writes spec.clips (+ carousel slide backgrounds when bg.at is null).

Rules (what the old LOOK step enforced):
- skip the first 7% and last 12% of the trailer (rating cards, logos, end slates, release-date text)
- skip black / white-flash shots and any shot with a near-black frame (start/mid/end); hook opens on a bright shot
- skip soft (blurry) shots; drop shots with heavy text (edge-dense flat areas)
- dense scan (every ~0.1 s) of each shot: a hidden hard cut ends the shot there (19b, 19 Nov: a GTA VI logo card
  flashed in the last 0.4 s of a "shot"), and big flat neon graphics in the clear middle band reject it (19c: the
  Cyberpunk trailer's giant yellow letters)
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
cut = (datetime.date.fromisoformat(D[:10]) - datetime.timedelta(days=14)).isoformat()
last_used = {}                                            # shot → most recent day it was used (within 14 days)
for d, lst in used.items():
    if d >= cut and d != D:
        for u in lst: k = (u["src_id"], round(u["start"], 1)); last_used[k] = max(last_used.get(k, ""), d)
recent = set(last_used)

cap = cv2.VideoCapture(str(GN / f"work/{tag}.mp4"))
def frame(t):
    cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000); ok, f = cap.read(); return f if ok else None
import subprocess, tempfile, os
def ocr_words(f):
    """confident words tesseract reads in the frame (title cards, logos, 'PLAY NOW', rating cards)"""
    g = cv2.cvtColor(cv2.resize(f, (960, 540)), cv2.COLOR_BGR2GRAY)
    n = 0
    small = cv2.resize(g, (480, 270))               # giant stylised words only read at a smaller scale
    for img in (g, 255 - g, small, 255 - small):    # light-on-dark and dark-on-light, two scales
        fd, p = tempfile.mkstemp(suffix=".png"); os.close(fd); cv2.imwrite(p, img)
        try:
            out = subprocess.run(["tesseract", p, "-", "--psm", "11", "tsv"], capture_output=True, text=True, timeout=30).stdout
        except Exception: out = ""
        os.remove(p)
        for row in out.splitlines()[1:]:
            c = row.split("\t")
            if len(c) == 12 and c[11].strip() and float(c[10]) > 70 and sum(ch.isalpha() for ch in c[11]) >= 3: n += 1
    return n
import re
TITLE = {"grand", "theft", "auto", "rockstar", "playstation", "xbox", "nintendo", "steam", "trailer", "available", "preorder",
         "pre-order", "order", "coming", "rated", "edition", "launch", "wishlist", "pre-load", "preload", "captured"}
TITLE |= {w for w in re.findall(r"[a-z]{5,}", src.get("label", "").lower()) if not w.startswith(("gta", "official"))}
def title_hit(f):
    """the game's own title/logo or a store card in the 9:16 crop (19b, 19 Nov: the GTA VI logo dissolving into the
    hook shot read as 'GRand ... auto' while ocr_words saw nothing confident). Any-confidence token match."""
    h, w = f.shape[:2]; cw = int(h * 9 / 16); x = (w - cw) // 2
    g = cv2.cvtColor(f[:, x:x + cw], cv2.COLOR_BGR2GRAY)
    for sc in (540, 270):
        fd, p = tempfile.mkstemp(suffix=".png"); os.close(fd); cv2.imwrite(p, cv2.resize(g, (int(cw * sc / h), sc)))
        try: out = subprocess.run(["tesseract", p, "-", "--psm", "11"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=30).stdout.decode(errors="ignore")
        except Exception: out = ""
        os.remove(p)
        toks = set(re.findall(r"[a-z-]{4,}", out.lower()))
        if toks & TITLE or any(len(k) >= 5 and len(w) >= 6 and w.startswith(k[:6]) for k in toks for w in TITLE): return True   # 'playstatic'

    return False
def textiness(f):
    g = cv2.cvtColor(cv2.resize(f, (480, 270)), cv2.COLOR_BGR2GRAY)
    e = cv2.Canny(g, 120, 240) > 0
    flat = cv2.blur(g.astype(np.float32), (9, 9))
    # text = many sharp edges sitting on an otherwise flat/dark background
    return float((e & (flat < 60)).mean() * 100), float(e.mean() * 100)

def ad_slate(f):
    """console/brand ad card (PlayStation 'FEEL THE TENSION' slates, 18b on 18 Nov): a smooth, bright, coloured gradient.
    Measured: ad cards smooth 68-81 / brightness 160+ / sat 79-95; smooth gameplay is dark (brightness <= 53)."""
    sm = cv2.resize(f, (480, 270)); g = cv2.cvtColor(sm, cv2.COLOR_BGR2GRAY).astype(np.float32)
    m = cv2.blur(np.hypot(cv2.Sobel(g, cv2.CV_32F, 1, 0), cv2.Sobel(g, cv2.CV_32F, 0, 1)), (5, 5))
    sat = float(cv2.cvtColor(sm, cv2.COLOR_BGR2HSV)[..., 1].mean())
    return (m < 6).mean() * 100 >= 60 and g.mean() >= 120 and sat >= 60

def centre_band(f):                                      # what the 9:16 crop shows in the band that must stay clear
    h, w = f.shape[:2]; cw = int(h * 9 / 16); x = (w - cw) // 2; return f[int(h * .25):int(h * .72), x:x + cw]
def graphic(f):
    """% of the middle band that is flat, saturated, bright colour = poster typography/logo art, never gameplay.
    Measured 19 Nov: Cyberpunk yellow-letter shots 4.3-30.8, every clean gameplay shot of both trailers 0.0-0.4."""
    sm = cv2.resize(centre_band(f), (160, 141)); hsv = cv2.cvtColor(sm, cv2.COLOR_BGR2HSV)
    g = cv2.cvtColor(sm, cv2.COLOR_BGR2GRAY).astype(np.float32)
    grad = cv2.blur(np.hypot(cv2.Sobel(g, cv2.CV_32F, 1, 0), cv2.Sobel(g, cv2.CV_32F, 0, 1)), (5, 5))
    return float(((grad < 5) & (hsv[..., 1] > 150) & (hsv[..., 2] > 150)).mean() * 100)
def hist(f):
    h = cv2.calcHist([cv2.cvtColor(cv2.resize(f, (160, 90)), cv2.COLOR_BGR2HSV)], [0, 1], None, [30, 16], [0, 180, 0, 256])
    return cv2.normalize(h, h).flatten()
FPS = cap.get(cv2.CAP_PROP_FPS) or 30
def scan(a, b):
    """read [a, b] sequentially (~10 samples/s); split it at hard cuts. Returns [(seg_start, seg_end, max graphic score)]"""
    cap.set(cv2.CAP_PROP_POS_MSEC, a * 1000); prev, gmax, seg0, segs = None, 0.0, a, []
    step = max(1, round(FPS / 10)); n = int((b - a) * FPS)
    for i in range(n):
        ok, f = cap.read()
        if not ok: break
        if i % step: continue
        t = a + i / FPS; hh = hist(f)
        if prev is not None and cv2.compareHist(prev, hh, cv2.HISTCMP_CORREL) < 0.5:
            segs.append((seg0, t - 0.08, gmax)); seg0, gmax = t + 0.25, 0.0   # pad: dissolves span frames
        gmax = max(gmax, graphic(f)); prev = hh
    segs.append((seg0, b, gmax)); return segs

cands = []
for s0 in shots:
    if s0["start"] < total * 0.07 or s0["end"] > total * 0.88: continue
    if s0["dur"] < 1.35 or not (28 <= s0["bright"] <= 225) or s0["sharp"] < 120: continue
    if s0["sat"] < 22 or s0["motion"] < 3: continue          # grey logo slates / frozen holds
    segs = scan(s0["start"] + 0.1, s0["end"] - 0.05)
    for k, (a, b, gmax) in enumerate(segs):                # each piece between hidden cuts is judged on its own
        s = {**s0, "start": round(a - 0.12, 2), "end": round(b + 0.05, 2), "dur": round(b - a + 0.17, 2)}   # clip starts at start+0.12 = a
        if len(segs) > 1: s["id"] = round(s0["id"] + k / 100, 2)   # sub-shot id stays next to its parent
        if s["dur"] < 1.35 or gmax >= 2.5: continue        # too short / poster typography or logo art in the clear middle
        key = (src["id"], round(s["start"], 1))
        mid = frame((s["start"] + s["end"]) / 2)
        if mid is None: continue
        t_dark, t_all = textiness(mid)
        if t_dark > 2.2: continue                  # title/rating card: white type on black
        ends = [fr for fr in (mid, frame(s["start"] + 0.15), frame(s["end"] - 0.15)) if fr is not None]
        lum = [float(cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY).mean()) for fr in ends]
        if min(lum) < 14: continue                 # truly black moments never
        if any(ad_slate(fr) for fr in ends): continue      # brand/console ad cards inside "gameplay" files
        if any(ocr_words(fr) >= 2 for fr in ends): continue
        if any(title_hit(fr) for fr in (frame(t) for t in np.arange(s["start"] + 0.12, s["end"] - 0.05, 0.4)) if fr is not None): continue
        score = (s["motion"] + 2) * math.log10(s["sharp"] + 10) * (0.7 + min(s["sat"], 140) / 200)
        cands.append({**s, "score": score, "lum": min(lum), "used": last_used.get(key, "")})
# near-black moments read as a dead frame on a phone (17c, 16 Nov): drop shots with a frame under 38 brightness, but a
# dark game (Elden Ring) may have few bright shots, so keep at least the 10 brightest rather than failing the build
lit = [c for c in cands if c["lum"] >= 38]
cands = lit if len(lit) >= 10 else sorted(cands, key=lambda c: -c["lum"])[: max(10, len(lit))]
fresh = [c for c in cands if not c["used"]]
# fresh shots first; if the trailer is running dry (several posts a day on one game), add back the shots used longest ago
cands = fresh if len(fresh) >= 10 else fresh + sorted([c for c in cands if c["used"]], key=lambda c: c["used"])[: max(0, 14 - len(fresh))]
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
info = {x["id"]: x for x in cands}
bright = [c for c in picked if info.get(c["shot"], {}).get("lum", 0) >= 60]   # the hook frame must read instantly
best = max(bright or picked, key=lambda c: info[c["shot"]]["score"] if c["shot"] in info else 0)
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
used[D] = [{"src_id": src["id"], "start": round(info[p["shot"]]["start"], 1)} for p in picked]
json.dump(used, open(used_p, "w"), indent=1)
print(f"autopick: {len(picked)} clips, {t:.1f}s for {need:.1f}s needed, from {len(cands)} usable shots")
