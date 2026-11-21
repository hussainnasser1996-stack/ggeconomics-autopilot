#!/usr/bin/env python3
"""lf_post.py <P> thumb|gates|meta
thumb: 4 clean gameplay tiles from the finished render (ranks 8, 7, 5, 2; never #1), taken after the data panel has gone
       and cropped above the fact chips, for the LongThumb still.
gates: duration 7-10 min, no black run >= 0.5 s, loudness -16..-12 LUFS, audio present, contact sheet -> longform/<P>/contact.jpg.
meta:  meta.json for yt_long.py: title, description with chapters from the spec, music credits, publish Saturday 16:00 UTC."""
import sys, json, re, subprocess, datetime as dt
from pathlib import Path
GN = Path(__file__).resolve().parents[3]; AP = GN / "autopilot"; P, what = sys.argv[1], sys.argv[2]; L = AP / "longform" / P
spec = json.load(open(L / "spec.json")); E = spec["entries"]; MP4 = GN / f"work/lf/top10-{P}.mp4"
cold = sum(c["dur"] for c in spec["cold"]); t = spec["hook"]["sec"] + cold + spec["introSec"]; seg = {}
for e in E: play = sum(c["dur"] for c in e["clips"]); seg[e["rank"]] = (t, t + spec["cardSec"], play); t += spec["cardSec"] + play
outro, total = t, t + spec["outroSec"]
def ff(*a): return subprocess.run(["ffmpeg", "-v", "error", "-y", *a], capture_output=True, text=True)

if what == "thumb":
    D = GN / "studio/public/thumbs"; D.mkdir(parents=True, exist_ok=True)
    for i, r in enumerate([8, 7, 5, 2]):
        _, g0, play = seg[r]; panel_end = min(16, play * 0.42)
        ts = g0 + min(panel_end + 1.2, max(1.0, play - 9))           # after the data panel, before the verdict
        ff("-ss", f"{ts:.2f}", "-i", str(MP4), "-frames:v", "1", "-vf", "crop=900:800:510:110", "-q:v", "2", str(D / f"t{i}.jpg"))
        print("tile", i, "rank", r, "at", round(ts, 1))

elif what == "gates":
    fails = []; dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(MP4)], capture_output=True, text=True).stdout)
    if not 420 <= dur <= 600: fails.append(f"duration {dur:.0f} s outside 7-10 min")
    bl = ff("-i", str(MP4), "-vf", "blackdetect=d=0.5:pix_th=0.08", "-an", "-f", "null", "-").stderr
    blacks = re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", bl)
    if blacks: fails.append(f"black runs >= 0.5 s at {[(round(float(a), 1), round(float(b), 1)) for a, b in blacks][:5]}")
    ln = ff("-i", str(MP4), "-af", "ebur128", "-f", "null", "-").stderr
    I = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", ln)[-1])
    if not -16 <= I <= -12: fails.append(f"loudness {I} LUFS outside -16..-12")
    ff("-i", str(MP4), "-vf", "fps=1/16,scale=384:-1,tile=6x5", "-frames:v", "1", "-q:v", "3", str(L / "contact.jpg"))
    ff("-i", str(MP4), "-t", "40", "-vf", "fps=1/2,scale=384:-1,tile=5x4", "-frames:v", "1", "-q:v", "3", str(L / "contact_intro.jpg"))
    rep = [f"duration {dur:.1f} s", f"loudness {I} LUFS", f"black runs {len(blacks)}", "PASS" if not fails else "FAIL: " + "; ".join(fails)]
    (L / "gates.txt").write_text("\n".join(rep) + "\n"); print("\n".join(rep))
    sys.exit(1 if fails else 0)

elif what == "meta":
    mmss = lambda s: f"{int(s) // 60}:{int(s) % 60:02d}"
    week = dt.date.fromisoformat(json.load(open(L / "data.json"))["week_end"])
    one = next(e for e in E if e["rank"] == 1)
    ch = ["0:00 Intro"] + [f"{mmss(seg[e['rank']][0])} " + ("#1 revealed" if e["rank"] == 1 else f"#{e['rank']} {e['name']}") for e in E] + [f"{mmss(outro)} Full ranking"]
    tracks = spec.get("music_titles", [])
    credit = ", ".join(f'"{x}"' for x in tracks[:-1]) + f' and "{tracks[-1]}"' if len(tracks) > 1 else f'"{tracks[0]}"'
    sale = any(e.get("priceNote") for e in E)
    desc = f"""The 10 games with the most players on Steam in the week to {week.strftime('%-d %B %Y')}, ranked by peak concurrent players. Each one gets its price, Steam reviews, Metacritic score where it has one, and a verdict on whether it's worth the money. Number 1 had {one['players']:,} people playing at once.

Which of these are you playing right now? Tell us in the comments.

{chr(10).join(ch)}

Data: Steam (peak concurrent players, US store prices and reviews on {week.strftime('%-d %b %Y')}) and Metacritic.{' Some prices were sale prices that week.' if sale else ''}
Footage: official Steam trailers.
Music: {credit} by Kevin MacLeod (incompetech.com), licensed under Creative Commons: By Attribution 4.0.
The intro is narrated with an AI voice.

#steam #pcgaming #top10"""
    pub = dt.date.fromisoformat(P)
    tags = ["top 10 steam games", "most played steam games", "steam top 10", "pc gaming", "steam charts"] + \
           [e["name"].lower() for e in sorted(E, key=lambda e: e["rank"])[:7]] + ["is it worth it", "gg economics"]
    meta = {"title": f"Top 10 Games on Steam This Week: Worth the Money? ({pub.strftime('%b %Y')})", "description": desc, "tags": tags[:15],
            "publish_at": f"{P}T16:00:00Z", "video_url": f"https://github.com/hussainnasser1996-stack/ggeconomics-autopilot/releases/download/longform-{P}/top10-{P}.mp4",
            "thumb": "thumb.png", "playlist_title": "Top 10 on Steam (weekly)",
            "playlist_description": "Every week: the 10 most played games on Steam, with price, reviews and whether each is worth the money."}
    json.dump(meta, open(L / "meta.json", "w"), indent=1); print(meta["title"]); print(desc)
