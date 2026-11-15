#!/usr/bin/env python3
"""fetch_footage.py "<search query>" <tag> [--pick N]
Search YouTube (yt-dlp), list candidates, prefer official channels (config.json), download <=1080p,
make the 1080p/30 proxy at work/<tag>.mp4 (+ .wav), hard-link it into studio/public/footage/<tag>.mp4,
then run shots.py + topsheet.py so Claude can LOOK at work/<tag>/top.jpg.
Without --pick it only prints the candidate table (choose, then rerun with --pick N)."""
import sys, json, subprocess, os
from pathlib import Path
GN = Path(__file__).resolve().parents[2]            # experiments/game-news
cfg = json.load(open(GN / "autopilot/config.json"))
q, tag = sys.argv[1], sys.argv[2]
pick = sys.argv[sys.argv.index("--pick") + 1] if "--pick" in sys.argv else None   # a VIDEO ID (stable) or a row number
url = sys.argv[sys.argv.index("--url") + 1] if "--url" in sys.argv else None   # direct video/HLS URL (e.g. Steam trailer)
ents = []
if not url:
    r = subprocess.run(["yt-dlp", "--flat-playlist", "-J", f"ytsearch10:{q}"], capture_output=True, text=True)
    ents = json.loads(r.stdout)["entries"] if r.stdout.strip() else []
    if not ents: sys.exit("yt-dlp search returned nothing (blocked?). Fallback: autopilot/scripts/steam_footage.py \"<game>\"")
off = set(cfg["official_channels"])
rows = []
for i, e in enumerate(ents):
    d = e.get("duration") or 0
    rows.append({"i": i, "id": e["id"], "title": e.get("title", "")[:70], "uploader": e.get("channel") or e.get("uploader") or "",
                 "dur": int(d), "official": (e.get("channel") or e.get("uploader") or "") in off})
for x in rows:
    print(f"[{x['i']}] {x['id']}  {'OFFICIAL ' if x['official'] else '         '}{x['dur']:5d}s  {x['uploader'][:28]:28s} {x['title']}")
if url: pick = "URL"
if pick is None:
    best = next((x for x in rows if x["official"] and 30 <= x["dur"] <= 1500), next((x for x in rows if 30 <= x["dur"] <= 1500), rows[0]))
    print(f"\nsuggested: --pick {best['id']}"); sys.exit(0)
x = {"id": url, "title": q, "uploader": "direct", "official": True} if url else next((r for r in rows if r["id"] == pick), None) or (rows[int(pick)] if pick.isdigit() else {"id": pick, "title": "?", "uploader": "?", "official": False})
dl = GN / "work/dl"; dl.mkdir(parents=True, exist_ok=True)
src = dl / f"{tag}.mp4"
if url:
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", url, "-c", "copy", str(src)], check=True)
else:
    subprocess.run(["yt-dlp", "-f", "bv*[height<=1080]+ba/b[height<=1080]", "--merge-output-format", "mp4", "-o", str(src),
                    f"https://www.youtube.com/watch?v={x['id']}"], check=True)
subprocess.run([str(GN / "src/proxy.sh"), str(src), str(GN / f"work/{tag}.mp4")], check=True)
pub = GN / f"studio/public/footage/{tag}.mp4"; pub.parent.mkdir(parents=True, exist_ok=True)
if pub.exists(): pub.unlink()
os.link(GN / f"work/{tag}.mp4", pub)
py = str(GN / ".venv/bin/python")
subprocess.run([py, "src/shots.py", f"work/{tag}.mp4", tag], cwd=GN, check=True)
subprocess.run([py, "src/topsheet.py", tag, "48", "1.2"], cwd=GN, check=True)
json.dump({"query": q, "video_id": x["id"], "title": x["title"], "uploader": x["uploader"], "official": x["official"]},
          open(GN / f"work/{tag}/source.json", "w"), indent=1)
print(f"\nLOOK: work/{tag}/top.jpg  (then: src/pick.py {tag} <clips.json> ids... and LOOK at the _check.jpg)")
