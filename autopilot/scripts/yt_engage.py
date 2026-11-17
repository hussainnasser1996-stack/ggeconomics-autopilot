#!/usr/bin/env python3
"""yt_engage.py — after a Short goes live on YouTube (runs in monitor.yml every 6 h):
  1. posts the video's question as a comment from the channel (gets the comment section going), once per video;
  2. uploads exact English captions (SRT from our own script + VO timing) for NARRATED Shorts only.
     Music-only "edit" Shorts get no captions: nobody speaks (Husain, 17 Nov).
Matches YouTube videos to queue folders by title. State: autopilot/log/yt_engaged.json. Never edits or deletes a video.
Needs the token with the youtube.force-ssl scope. Missing token = skip, never fatal."""
import json, re, sys, tempfile, datetime as dt
from pathlib import Path
AP = Path(__file__).resolve().parents[1]
tok = AP / "keys/youtube-token.json"
if not tok.exists(): sys.exit(print("yt_engage: no token, skipped") or 0)
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

creds = Credentials.from_authorized_user_file(str(tok))
if not creds.valid: creds.refresh(Request()); tok.write_text(creds.to_json())
yt = build("youtube", "v3", credentials=creds)
state_p = AP / "log/yt_engaged.json"
state = json.loads(state_p.read_text()) if state_p.exists() else {}
norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())

# queue folders by title
queue = {}
for q in sorted((AP / "queue").iterdir()):
    if (q / "post.json").exists() and (q / "script.json").exists() and not (q / "dry").exists():
        queue[norm(json.load(open(q / "post.json"))["title"][:100])] = q

ch = yt.channels().list(part="contentDetails", mine=True).execute()["items"][0]
uploads = ch["contentDetails"]["relatedPlaylists"]["uploads"]
items = yt.playlistItems().list(part="snippet,contentDetails", playlistId=uploads, maxResults=25).execute().get("items", [])
cutoff = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=7)).isoformat()

def question(q):
    lines = json.load(open(q / "script.json"))["lines"]
    for l in lines:
        if l["id"] == "q" and l["text"].strip().endswith("?"): return l["text"].strip()
    for l in json.load(open(q / "post.json"))["caption"].splitlines():
        if l.strip().endswith("?"): return l.strip()
    return lines[-1]["text"].strip() if lines[-1]["text"].strip().endswith("?") else None

def ts(t):
    ms = int(round(t * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

def srt(q):
    tl = q / "timeline.json"
    if not tl.exists(): return None
    text = {l["id"]: l["text"] for l in json.load(open(q / "script.json"))["lines"]}
    rows = [l for l in json.load(open(tl))["lines"] if l["id"] in text]
    return "\n".join(f"{i}\n{ts(l['start'])} --> {ts(l['end'])}\n{text[l['id']]}\n" for i, l in enumerate(rows, 1)) or None

for it in items:
    vid = it["contentDetails"]["videoId"]; sn = it["snippet"]
    if sn.get("publishedAt", "") < cutoff: continue
    q = queue.get(norm(sn["title"]))
    if not q: continue
    st = state.setdefault(vid, {"queue": q.name})
    edit = json.load(open(q / "script.json")).get("mode") == "edit"
    if not st.get("comment"):
        text = question(q)
        if text:
            try:
                yt.commentThreads().insert(part="snippet", body={"snippet": {"videoId": vid,
                    "topLevelComment": {"snippet": {"textOriginal": text}}}}).execute()
                st["comment"] = text; print(f"{q.name} {vid}: commented '{text}'")
            except Exception as e: print(f"{q.name} {vid}: comment failed: {e}")
        else: st["comment"] = "none (no question line)"
    if not st.get("captions"):
        if edit: st["captions"] = "skipped: music-only"
        else:
            s = srt(q)
            if not s: st["captions"] = "skipped: no timeline (built before 17 Nov)"
            else:
                f = Path(tempfile.mkdtemp()) / "en.srt"; f.write_text(s)
                try:
                    yt.captions().insert(part="snippet", body={"snippet": {"videoId": vid, "language": "en", "name": "English", "isDraft": False}},
                                         media_body=MediaFileUpload(str(f), mimetype="application/octet-stream")).execute()
                    st["captions"] = "uploaded"; print(f"{q.name} {vid}: captions uploaded")
                except Exception as e: print(f"{q.name} {vid}: captions failed: {e}")
state_p.write_text(json.dumps(state, indent=1))
print(f"yt_engage: {len(state)} videos tracked")
