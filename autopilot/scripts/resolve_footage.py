#!/usr/bin/env python3
"""resolve_footage.py <D>  — turn queue/D/footage.json (written by the brain) into a downloaded, shot-split trailer.
footage.json: {"candidates": [{"source": "steam", "game": "<Steam search term>", "prefer": "<word in trailer name>"},
                              {"source": "library", "file": "<asset in the footage-library release>"}, ...],
               "credit": "GAMEPLAY: <PUBLISHER>"}
Tries each candidate in order (YouTube is blocked from cloud runners, so it is never tried here).
Final fallback: the newest library file. Writes queue/D/footage_resolved.json {tag, id, label, credit}."""
import sys, json, subprocess, urllib.request, urllib.parse
from pathlib import Path
GN = Path(__file__).resolve().parents[2]; D = sys.argv[1]; Q = GN / "autopilot/queue" / D
spec = json.load(open(Q / "footage.json")) if (Q / "footage.json").exists() else {"candidates": []}
tag = "d_" + D.replace("-", "_")
get = lambda u: json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read())
used = json.load(open(GN / "autopilot/log/used_shots.json")) if (GN / "autopilot/log/used_shots.json").exists() else {}
recent_src = [u["src_id"] for d in sorted(used)[-3:] for u in used[d][:1]]

BAD = ("pegi", "esrb", "online", "dlc", "update", "season", "expansion", "pack", "bundle", "usk", " de ", "soundtrack",
       "(kr)", "(jp)", "(de)", "(fr)", "(es)", "(br)", "(ru)", "(cn)", " kr ", " jp ")
GOOD = ("launch", "gameplay", "official", "trailer", "story", "reveal")
def steam(c):
    """all trailers of the best-matching Steam app, most promising first"""
    items = get("https://store.steampowered.com/api/storesearch/?cc=us&l=en&term=" + urllib.parse.quote(c["game"]))["items"][:3]
    for it in items:
        d = get(f"https://store.steampowered.com/api/appdetails?appids={it['id']}&filters=movies&cc=us&l=english").get(str(it["id"]), {})
        movies = [m for m in ((d.get("data") or {}).get("movies") or []) if m.get("hls_h264")]
        if not movies: continue
        pref = (c.get("prefer") or "").lower()
        def rank(m):
            n = " " + m["name"].lower() + " "
            return (bool(pref) and pref not in n, sum(b in n for b in BAD), f"steam:{m['id']}" in recent_src,
                    -sum(g in n for g in GOOD), not m.get("highlight"))
        clean = [m for m in movies if not any(b in " " + m["name"].lower() + " " for b in BAD)]
        movies = clean or movies                  # never a regional/DLC trailer while a clean one exists
        return [{"id": f"steam:{m['id']}", "label": f"{it['name']} — {m['name']}", "url": m["hls_h264"]} for m in sorted(movies, key=rank)[:4]]
    return []
def library(c):
    f = c.get("file") or ""
    if not f.endswith(".mp4"):     # no file, or a prefix like "gta6_comp": take the least-recently-used matching asset
        a = json.loads(subprocess.run(["gh", "release", "view", "footage-library", "--json", "assets"], capture_output=True, text=True, cwd=GN).stdout)["assets"]
        a = [x["name"] for x in a if x["name"].startswith(f)] or [x["name"] for x in a]
        a = [n for n in a if not any(b in n for b in ("features", "preload"))] or a   # PlayStation ad files: features (18 Nov), preload = "PRE-LOAD NOW" + logos (19 Nov)
        last = {}
        for d in sorted(used):
            for u in used[d][:1]: last[u["src_id"]] = d
        f = sorted(a, key=lambda n: (last.get(f"lib:{n}", ""), n))[0]
    p = subprocess.run(["python3", "autopilot/scripts/library.py", f], capture_output=True, text=True, cwd=GN, check=True).stdout.strip().splitlines()[-1]
    return [{"id": f"lib:{f}", "label": f, "url": p}]
def usable():
    sh = json.load(open(GN / f"work/{tag}/shots.json")); tot = max(x["end"] for x in sh)
    return sum(  # NOTE: counts clean-looking shots before OCR + recency; autopick re-checks
1 for x in sh if tot * 0.07 <= x["start"] and x["end"] <= tot * 0.88 and x["dur"] >= 1.35
               and x["sat"] >= 22 and x["motion"] >= 3 and 28 <= x["bright"] <= 225)

best = None   # (usable shots, option): a trailer with 14+ clean shots is taken at once; otherwise keep the richest
for c in spec.get("candidates", []) + [{"source": "library", "generic": True}]:
    if c.get("generic") and best and best[0] >= 8: break        # the brain's own picks are good enough
    try: opts = (steam if c["source"] == "steam" else library)(c)
    except Exception as e: print(f"candidate {c} failed: {e}", file=sys.stderr); continue
    for r in opts:
        try:
            subprocess.run(["python3", "autopilot/scripts/fetch_footage.py", r["label"], tag, "--url", r["url"]], cwd=GN, check=True)
            n = usable(); print(f"{r['label']}: {n} usable shots")
        except Exception as e:
            print(f"{r['label']} failed: {e}", file=sys.stderr); continue
        if not best or n > best[0]: best = (n, r)
        if n >= 14: break
    if best and best[0] >= 14: break
if best:
    r = best[1]
    if not (GN / f"work/{tag}/source.json").exists() or json.load(open(GN / f"work/{tag}/source.json"))["video_id"] != r["url"]:
        subprocess.run(["python3", "autopilot/scripts/fetch_footage.py", r["label"], tag, "--url", r["url"]], cwd=GN, check=True)
    credit = spec.get("credit", "")
    if r["id"].startswith("lib:gta6") and "ROCKSTAR" not in credit.upper(): credit = "GAMEPLAY: ROCKSTAR GAMES"
    out = {"tag": tag, "id": r["id"], "label": r["label"], "credit": credit, "usable_shots": best[0]}
    json.dump(out, open(Q / "footage_resolved.json", "w"), indent=1); print("footage:", out); sys.exit(0)
sys.exit("no footage source worked")
