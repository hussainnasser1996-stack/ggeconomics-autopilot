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
        opts = [{"id": f"steam:{m['id']}", "label": f"{it['name']} — {m['name']}", "url": m["hls_h264"], "appid": it["id"]} for m in sorted(movies, key=rank)[:4]]
        # last resort for THIS game: its official screenshots as a Ken Burns reel (23 Nov: all 4 Terraria trailers were
        # text cards/UI = 0-2 clean shots, and the generic fallback would have put GTA 6 footage on a Terraria Short)
        return opts + [{"id": f"steamshots:{it['id']}", "label": f"{it['name']} — Steam screenshots", "reel": it["id"], "appid": it["id"]}]
    return []
def reel(appid):
    """official Steam screenshots -> one 1080p30 'trailer': 4.2 s per still with a slow push/pan, hard cuts between"""
    d = get(f"https://store.steampowered.com/api/appdetails?appids={appid}&cc=us&l=english").get(str(appid), {})
    urls = [x["path_full"] for x in ((d.get("data") or {}).get("screenshots") or []) if x.get("path_full")][:14]
    if len(urls) < 4: raise RuntimeError(f"only {len(urls)} screenshots")
    W = GN / "work/reel" / str(appid); W.mkdir(parents=True, exist_ok=True); parts = []
    for i, u in enumerate(urls):
        img = W / f"{i}.jpg"; out = W / f"{i}.mp4"
        try: img.write_bytes(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read())
        except Exception: continue
        z = "min(1+0.0011*on,1.14)" if i % 2 == 0 else "max(1.14-0.0011*on,1)"          # alternate push in / pull out
        x = "(iw-iw/zoom)*on/126" if i % 3 == 0 else "(iw-iw/zoom)/2"                    # every third pans sideways
        r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(img), "-vf",
                            f"scale=3840:2160:force_original_aspect_ratio=increase,crop=3840:2160,zoompan=z='{z}':x='{x}':y='(ih-ih/zoom)/2':d=126:s=1920x1080:fps=30,format=yuv420p",
                            "-frames:v", "126", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", str(out)], stdin=subprocess.DEVNULL)
        if r.returncode == 0: parts.append(out)
    if len(parts) < 4: raise RuntimeError("screenshot reel: too few stills rendered")
    (W / "list.txt").write_text("".join(f"file '{p}'\n" for p in parts))
    vid = GN / f"work/dl/reel_{appid}.mp4"; vid.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(W / "list.txt"), "-f", "lavfi", "-i",
                    "anullsrc=r=48000:cl=stereo", "-shortest", "-c:v", "copy", "-c:a", "aac", str(vid)], check=True, stdin=subprocess.DEVNULL)
    return str(vid)
def library(c):
    f = c.get("file") or ""
    if any(b in f for b in ("features", "preload")):   # ad files even when named outright (21 Nov: 12-31c named the features
        f = "gta6_"                                       # file, autopick found 5 clean shots and the build failed)
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
def clean(r):
    """the REAL count: autopick's own filter (OCR, logo, graphic, dark-dip...). The rough count below said 12 for the
    Terraria 1.3 trailer where autopick found 0, so 23c failed twice on the same pick (23 Nov)."""
    meta = {"tag": tag, "id": r["id"], "label": r["label"], **({"appid": r["appid"]} if r.get("appid") else {})}
    out = subprocess.run(["python3", "autopilot/scripts/autopick.py", D, "--count", json.dumps(meta)], cwd=GN,
                         capture_output=True, text=True, timeout=1200).stdout
    m = [l for l in out.splitlines() if l.startswith("CLEAN ")]
    return int(m[-1].split()[1]) if m else 0
def usable():
    sh = json.load(open(GN / f"work/{tag}/shots.json")); tot = max(x["end"] for x in sh)
    return sum(  # NOTE: counts clean-looking shots before OCR + recency; autopick re-checks
1 for x in sh if tot * 0.07 <= x["start"] and x["end"] <= tot * 0.88 and x["dur"] >= 1.35
               and x["sat"] >= 22 and x["motion"] >= 3 and 28 <= x["bright"] <= 225)

best = None   # (clean shots, option): a trailer with 10+ clean shots is taken at once; otherwise keep the richest
seen = set()
game_topic = any(c.get("source") == "steam" for c in spec.get("candidates", []))
for c in spec.get("candidates", []) + [{"source": "library", "generic": True}]:
    if c.get("generic") and best and best[0] >= 6: break        # the brain's own picks are good enough
    if c.get("generic") and game_topic: break                    # never another game's footage on a Steam game's Short
    try: opts = (steam if c["source"] == "steam" else library)(c)
    except Exception as e: print(f"candidate {c} failed: {e}", file=sys.stderr); continue
    for r in opts:
        if r["id"] in seen: continue
        seen.add(r["id"])
        if r.get("reel") and best and best[0] >= 6: continue          # a trailer already works: no stills
        try:
            if r.get("reel"): r["url"] = reel(r["reel"])
            subprocess.run(["python3", "autopilot/scripts/fetch_footage.py", r["label"], tag, "--url", r["url"]], cwd=GN, check=True,
                           stdout=subprocess.DEVNULL)
            rough = usable(); n = clean(r) if rough >= 3 else 0
            print(f"{r['label']}: {n} clean shots (rough {rough})")
        except Exception as e:
            print(f"{r['label']} failed: {e}", file=sys.stderr); continue
        if not best or n > best[0]: best = (n, r)
        if n >= 10: break
    if best and best[0] >= 10: break
if best and best[0] < 6:
    sys.exit(f"no trailer has 6+ clean shots (best: {best[1]['label']} = {best[0]})")
if best:
    r = best[1]
    if not (GN / f"work/{tag}/source.json").exists() or json.load(open(GN / f"work/{tag}/source.json"))["video_id"] != r["url"]:
        subprocess.run(["python3", "autopilot/scripts/fetch_footage.py", r["label"], tag, "--url", r["url"]], cwd=GN, check=True)
    credit = spec.get("credit", "")
    if r["id"].startswith("lib:gta6") and "ROCKSTAR" not in credit.upper(): credit = "GAMEPLAY: ROCKSTAR GAMES"
    out = {"tag": tag, "id": r["id"], "label": r["label"], "credit": credit, "usable_shots": best[0], **({"appid": r["appid"]} if r.get("appid") else {})}
    json.dump(out, open(Q / "footage_resolved.json", "w"), indent=1); print("footage:", out); sys.exit(0)
sys.exit("no footage source worked")
