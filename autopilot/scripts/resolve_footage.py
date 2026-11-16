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

def steam(c):
    items = get("https://store.steampowered.com/api/storesearch/?cc=us&l=en&term=" + urllib.parse.quote(c["game"]))["items"][:3]
    for it in items:
        d = get(f"https://store.steampowered.com/api/appdetails?appids={it['id']}&filters=movies").get(str(it["id"]), {})
        movies = [m for m in ((d.get("data") or {}).get("movies") or []) if m.get("hls_h264")]
        if not movies: continue
        pref = (c.get("prefer") or "").lower()
        movies.sort(key=lambda m: (bool(pref) and pref not in m["name"].lower(), ("USK" in m["name"] or " DE " in m["name"] + " "),
                                   f"steam:{m['id']}" in recent_src, not m.get("highlight")))
        m = movies[0]
        return {"id": f"steam:{m['id']}", "label": f"{it['name']} — {m['name']}", "url": m["hls_h264"]}
def library(c):
    f = c.get("file")
    if not f:
        a = json.loads(subprocess.run(["gh", "release", "view", "footage-library", "--json", "assets"], capture_output=True, text=True, cwd=GN).stdout)["assets"]
        a = [x for x in a if f"lib:{x['name']}" not in recent_src] or a
        f = a[0]["name"]
    p = subprocess.run(["python3", "autopilot/scripts/library.py", f], capture_output=True, text=True, cwd=GN, check=True).stdout.strip().splitlines()[-1]
    return {"id": f"lib:{f}", "label": f, "url": p}

for c in spec.get("candidates", []) + [{"source": "library"}]:
    try:
        r = (steam if c["source"] == "steam" else library)(c)
        if not r: continue
        subprocess.run(["python3", "autopilot/scripts/fetch_footage.py", r["label"], tag, "--url", r["url"]], cwd=GN, check=True)
        out = {"tag": tag, "id": r["id"], "label": r["label"], "credit": spec.get("credit", "")}
        json.dump(out, open(Q / "footage_resolved.json", "w"), indent=1); print("footage:", out); sys.exit(0)
    except Exception as e:
        print(f"candidate {c} failed: {e}", file=sys.stderr)
sys.exit("no footage source worked")
