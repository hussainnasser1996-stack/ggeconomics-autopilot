#!/usr/bin/env python3
"""lf_footage.py <P>: official Steam trailers for every game in longform/<P>/data.json -> clean gameplay clips -> spec.json.
Same rejection rules as the Shorts' autopick.py, applied to the full 16:9 frame: title cards / logos (OCR incl. the chroma
pass), console ad slates, flat poster typography, white-on-black rating cards, black or near-black frames, cuts inside a
clip. Clip picking follows the 22 Nov episode (build.py): best-scoring pieces spread over every trailer, <=3.4 s each.
Writes studio/public/footage/L_<key>_<i>.mp4 and longform/<P>/spec.json (without vo/music; lf_audio.py adds those)."""
import sys, json, re, os, glob, math, random, subprocess, tempfile
from pathlib import Path
import numpy as np, cv2
GN = Path(__file__).resolve().parents[3]; AP = GN / "autopilot"; P = sys.argv[1]; L = AP / "longform" / P
W = GN / "work/lf"; W.mkdir(parents=True, exist_ok=True); FOOT = GN / "studio/public/footage"; FOOT.mkdir(parents=True, exist_ok=True)
data = json.load(open(L / "data.json")); E = data["entries"]
T = {10: 30, 9: 40, 8: 40, 7: 40, 6: 40, 5: 40, 4: 36, 3: 45, 2: 45, 1: 60}       # seconds of gameplay per rank (22 Nov cut)

def download(url, out):
    if out.exists() and out.stat().st_size > 1e5: return True
    tmp = out.with_suffix(".part.mp4")
    r = subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", url, "-t", "240", "-map", "0:v:0", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
                        "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fps=30", "-an", str(tmp)], stdin=subprocess.DEVNULL)
    if r.returncode == 0 and tmp.exists(): tmp.rename(out); return True
    return False

def tess(img, psm="11", tsv=False):
    fd, p = tempfile.mkstemp(suffix=".png"); os.close(fd); cv2.imwrite(p, img)
    try: out = subprocess.run(["tesseract", p, "-", "--psm", psm] + (["tsv"] if tsv else []), stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=30).stdout.decode(errors="ignore")
    except Exception: out = ""
    os.remove(p); return out
def confident_words(f):
    n = 0; g = cv2.cvtColor(cv2.resize(f, (1280, 720)), cv2.COLOR_BGR2GRAY)
    for img in (g, 255 - g):
        for row in tess(img, tsv=True).splitlines()[1:]:
            c = row.split("\t")
            if len(c) == 12 and c[11].strip() and float(c[10]) > 75 and sum(ch.isalpha() for ch in c[11]) >= 3: n += 1
    return n
TITLE0 = {"presents", "playstation", "xbox", "nintendo", "steam", "trailer", "available", "preorder", "pre-order", "order", "coming",
          "rated", "edition", "launch", "wishlist", "pre-load", "preload", "captured", "early", "access", "update", "season", "release"}
def title_hit(f, TITLE):
    """the game's name/logo or a store card anywhere in the frame (grey at two scales + the chroma pass for coloured type)"""
    h, w = f.shape[:2]; g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
    ch = (f.max(2).astype(np.int16) - f.min(2)).clip(0, 255).astype(np.uint8)
    for im, sc in ((g, 720), (g, 360), (ch, 720)):
        toks = set(re.findall(r"[a-z-]{4,}", tess(cv2.resize(im, (int(w * sc / h), sc))).lower()))
        if toks & TITLE or any(len(k) >= 5 and len(t) >= 6 and t.startswith(k[:6]) for k in toks for t in TITLE): return True
        if any(len(k) >= 5 and k in t for k in toks for t in TITLE): return True
    return False
def textiness_dark(f):
    g = cv2.cvtColor(cv2.resize(f, (480, 270)), cv2.COLOR_BGR2GRAY)
    return float(((cv2.Canny(g, 120, 240) > 0) & (cv2.blur(g.astype(np.float32), (9, 9)) < 60)).mean() * 100)
def ad_slate(f):
    sm = cv2.resize(f, (480, 270)); g = cv2.cvtColor(sm, cv2.COLOR_BGR2GRAY).astype(np.float32)
    m = cv2.blur(np.hypot(cv2.Sobel(g, cv2.CV_32F, 1, 0), cv2.Sobel(g, cv2.CV_32F, 0, 1)), (5, 5))
    return (m < 6).mean() * 100 >= 60 and g.mean() >= 120 and float(cv2.cvtColor(sm, cv2.COLOR_BGR2HSV)[..., 1].mean()) >= 60
def graphic(f):
    sm = cv2.resize(f[int(f.shape[0] * .2):int(f.shape[0] * .8)], (240, 108)); hsv = cv2.cvtColor(sm, cv2.COLOR_BGR2HSV)
    g = cv2.cvtColor(sm, cv2.COLOR_BGR2GRAY).astype(np.float32)
    grad = cv2.blur(np.hypot(cv2.Sobel(g, cv2.CV_32F, 1, 0), cv2.Sobel(g, cv2.CV_32F, 0, 1)), (5, 5))
    return float(((grad < 5) & (hsv[..., 1] > 150) & (hsv[..., 2] > 150)).mean() * 100)

def shots_of(path):
    """split at cuts (histogram jump or a dip under 28 brightness), keep lit, sharp, moving shots inside 6-90% of the trailer"""
    cap = cv2.VideoCapture(str(path)); fps = cap.get(cv2.CAP_PROP_FPS) or 30; N = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)); dur = N / fps
    prev = None; S = []; i = 0
    while True:
        ok, fr = cap.read()
        if not ok: break
        if i % 3 == 0:
            sm = cv2.resize(fr, (160, 90)); g = cv2.cvtColor(sm, cv2.COLOR_BGR2GRAY)
            h = cv2.calcHist([cv2.cvtColor(sm, cv2.COLOR_BGR2HSV)], [0, 1], None, [16, 8], [0, 180, 0, 256]); cv2.normalize(h, h)
            d = 0 if prev is None else cv2.compareHist(prev[0], h, cv2.HISTCMP_BHATTACHARYYA)
            mot = 0 if prev is None else float(np.mean(cv2.absdiff(prev[1], g)))
            S.append((i / fps, d, mot, float(g.mean()), float(cv2.Laplacian(cv2.cvtColor(cv2.resize(fr, (640, 360)), cv2.COLOR_BGR2GRAY), cv2.CV_64F).var())))
            prev = (h, g)
        i += 1
    cuts = sorted(set([0.0] + [t for t, d, _, b, _ in S if d > 0.22 or b < 28] + [dur]))
    out = []
    for a, b in zip(cuts, cuts[1:]):
        a2, b2 = a + 0.2, b - 0.2
        if b2 - a2 < 1.4 or a2 < dur * 0.06 or b2 > dur * 0.9: continue
        ins = [x for x in S if a2 <= x[0] <= b2]
        if not ins: continue
        br = [x[3] for x in ins]
        if min(br) < 30 or np.mean(br) > 225 or np.median([x[4] for x in ins]) < 60: continue
        out.append({"a": round(a2, 2), "b": round(b2, 2), "mot": float(np.mean([x[2] for x in ins])), "sharp": float(np.median([x[4] for x in ins])), "lum": min(br)})
    return out, dur

def frame(cap, t):
    cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000); ok, f = cap.read(); return f if ok else None
def boxzoom(path, t):
    o = subprocess.run(["ffmpeg", "-ss", str(max(0, t - 0.3)), "-i", str(path), "-t", "0.6", "-vf", "cropdetect=24:2:0", "-f", "null", "-"], capture_output=True, text=True).stderr
    hs = [int(m) for m in re.findall(r"crop=\d+:(\d+):", o)]
    if not hs: return 1.0
    h = max(set(hs), key=hs.count); return round(1080 / h * 1.01, 3) if 600 < h < 1040 else 1.0

spec = {"title": "TOP 10 GAMES ON STEAM", "sub": "THIS WEEK, BY PEAK PLAYERS",
        "week": "WEEK TO " + __import__("datetime").date.fromisoformat(data["week_end"]).strftime("%-d %b %Y").upper(),
        "credit": "DATA: STEAM (PEAK CONCURRENT PLAYERS, STORE PRICES, REVIEWS), METACRITIC · FOOTAGE: OFFICIAL STEAM TRAILERS · MUSIC: KEVIN MACLEOD (INCOMPETECH.COM) CC BY 4.0",
        "introSec": 7, "cardSec": 2, "outroSec": 20, "boardSub": "Price, reviews and a verdict for every game · #1 revealed at the end", "entries": []}
cold = []; report = []
for e in E:
    key = e["key"]; TITLE = TITLE0 | {w for w in re.findall(r"[a-z]{4,}", (e["name"] + " " + e["dev"]).lower())}
    pieces = []
    for i, (mname, url) in enumerate(e["movies"]):
        src = f"{key}_{i}"; path = W / f"{src}.mp4"
        if not download(url, path): print("download failed", e["name"], mname); continue
        shots, dur = shots_of(path)
        for s in shots:
            L_ = s["b"] - s["a"]; n = 1 if L_ <= 4.2 else min(3, int(L_ // 3.2)); step = L_ / n
            for k in range(n):
                x = s["a"] + k * step; pieces.append({"src": src, "path": path, "a": round(x, 2), "b": round(x + min(3.4, step), 2),
                    "score": s["mot"] * 0.6 + min(s["sharp"], 3000) / 300, "rel": x / dur + i, "shot": (src, s["a"])})
    pieces.sort(key=lambda p: -p["score"])
    caps = {}; chosen = []; tot = 0; rejected = 0; per_shot = {}
    for p in pieces:                                              # judge lazily, best first, until the segment is full
        if tot >= T[e["rank"]]: break
        if per_shot.get(p["shot"], 0) >= 2: continue
        cap = caps.setdefault(p["src"], cv2.VideoCapture(str(p["path"])))
        fr = [f for f in (frame(cap, p["a"] + 0.1), frame(cap, (p["a"] + p["b"]) / 2), frame(cap, p["b"] - 0.1)) if f is not None]
        if len(fr) < 3: continue
        if (any(float(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).mean()) < 30 for f in fr) or any(ad_slate(f) for f in fr) or max(graphic(f) for f in fr) >= 2.5
                or textiness_dark(fr[1]) > 2.2 or confident_words(fr[1]) >= 2 or any(title_hit(f, TITLE) for f in fr)):
            rejected += 1; continue
        chosen.append(p); tot += p["b"] - p["a"]; per_shot[p["shot"]] = per_shot.get(p["shot"], 0) + 1
    if tot < 8: sys.exit(f"lf_footage: only {tot:.1f} s of clean gameplay for {e['name']} (need 8+)")
    base = list(chosen)
    while tot < T[e["rank"]] * 0.8 and base:                     # thin trailers: replay the best pieces from a later point
        p = dict(base.pop(0)); p["a"] = round(p["a"] + 0.4, 2); chosen.append(p); tot += p["b"] - p["a"]
    chosen.sort(key=lambda p: p["rel"])
    for i in range(1, len(chosen) - 1):                          # never two pieces of one shot back to back
        if chosen[i]["shot"] == chosen[i - 1]["shot"]: chosen[i], chosen[i + 1] = chosen[i + 1], chosen[i]
    clips, t = [], 0
    for p in chosen:
        d = min(p["b"] - p["a"], T[e["rank"]] - t)
        if d < 0.6: break
        c = {"src": "L_" + p["src"], "from": p["a"], "dur": round(d, 3)}
        z = boxzoom(p["path"], p["a"] + d / 2)
        if z > 1.005: c["zoom"] = z
        clips.append(c); t += d
    ent = {k: v for k, v in e.items() if k not in ("key", "movies", "appid")}; ent["clips"] = clips
    spec["entries"].append(ent)
    cold += [{"src": c["src"], "from": round(c["from"] + 0.4, 2), "dur": 0.9752, **({"zoom": c["zoom"]} if "zoom" in c else {})} for c in sorted(clips, key=lambda c: -c["dur"])[:2]]
    report.append(f"#{e['rank']} {e['name']}: {t:.1f}/{T[e['rank']]} s, {len(clips)} clips, {rejected} pieces rejected")
    print(report[-1], flush=True)
    for c in caps.values(): c.release()
random.Random(P).shuffle(cold); spec["cold"] = cold[:18]
for u in sorted({c["src"] for e in spec["entries"] for c in e["clips"]} | {c["src"] for c in spec["cold"]}):
    dst = FOOT / f"{u}.mp4"
    if dst.exists(): dst.unlink()
    os.link(W / f"{u[2:]}.mp4", dst)
json.dump(spec, open(L / "spec.json", "w"), indent=1)
(L / "footage.txt").write_text("\n".join(report) + "\n")
