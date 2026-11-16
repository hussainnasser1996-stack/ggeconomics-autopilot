#!/usr/bin/env python3
"""yt_after.py — after Buffer publishes a Short (called by monitor.py): file it into its series playlist and post the
engagement question as the channel's first comment. Idempotent via autopilot/log/yt_done.json. Verifies via the API."""
import json, re, sys, os, urllib.request
from pathlib import Path
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
AP = Path(__file__).resolve().parents[1]; cfg = json.load(open(AP / "config.json"))
done_p = AP / "log/yt_done.json"; done = json.load(open(done_p)) if done_p.exists() else {}
yt = build("youtube", "v3", credentials=Credentials.from_authorized_user_file(str(AP / "keys/youtube-token.json")), cache_discovery=False)
PL = cfg["youtube_playlists"]
def series(q):
    p = json.load(open(q / "post.json")); s = p.get("series")
    if s in PL: return s
    tag = json.load(open(q / "spec.json"))["spec"].get("tag", "").upper(); title = p["title"].upper()
    if "COST PER HOUR" in tag or "/HR" in title or "PER HOUR" in title: return "cost_per_hour"
    if "TOP 5" in tag or "TOP 5" in title: return "top5"
    if "RUMOUR" in tag or "RUMOR" in title or "REAL OR" in title: return "real_or_rumour"
    if "SCOREBOARD" in tag: return "scoreboard"
    if "GTA" in tag or "GTA" in title: return "gta6"
    return "news"
out = []
for item in json.load(sys.stdin):            # [{"queue": name, "link": url}] from monitor.py
    q = AP / "queue" / item["queue"]; m = re.search(r"(?:shorts/|v=|youtu\.be/)([\w-]{11})", item["link"] or "")
    if not m or item["queue"] in done: continue
    vid = m.group(1); s = series(q); rec = {"video": vid, "series": s}
    try:
        have = {i["snippet"]["resourceId"]["videoId"] for i in yt.playlistItems().list(part="snippet", playlistId=PL[s], maxResults=50).execute().get("items", [])}
        if vid not in have: yt.playlistItems().insert(part="snippet", body={"snippet": {"playlistId": PL[s], "resourceId": {"kind": "youtube#video", "videoId": vid}}}).execute()
        rec["playlist"] = "ok"
    except Exception as e: rec["playlist"] = f"error: {e}"[:200]
    loc = json.load(open(q / "post.json")).get("localized") or {}
    if loc:                                   # titles/descriptions in other languages: found by + shown to non-English viewers
        try:
            v = yt.videos().list(part="snippet,localizations", id=vid).execute()["items"][0]
            sn = v["snippet"]; sn["defaultLanguage"] = "en"
            L = v.get("localizations", {}) | {k: {"title": x["title"][:100], "description": (x.get("description") or sn["description"])[:4900]}
                                             for k, x in loc.items() if x.get("title")}
            yt.videos().update(part="snippet,localizations", body={"id": vid, "snippet": {k: sn[k] for k in
                ("title", "description", "categoryId", "tags", "defaultLanguage") if k in sn}, "localizations": L}).execute()
            rec["localized"] = sorted(L)
        except Exception as e: rec["localized"] = f"error: {e}"[:200]
    cap = json.load(open(q / "post.json"))["caption"]
    question = next((l.strip() for l in cap.splitlines() if l.strip().endswith("?")), None)
    if question and cfg.get("youtube_comment_enabled"):   # needs the youtube.force-ssl scope (token lacks it); question stays in the caption
        try:
            yt.commentThreads().insert(part="snippet", body={"snippet": {"videoId": vid, "topLevelComment": {"snippet": {"textOriginal": question + " 👇"}}}}).execute()
            rec["comment"] = "ok"
        except Exception as e: rec["comment"] = f"error: {e}"[:200]
    done[item["queue"]] = rec; out.append(f"{item['queue']}: {rec}")
json.dump(done, open(done_p, "w"), indent=1); print("\n".join(out) or "yt_after: nothing new")
