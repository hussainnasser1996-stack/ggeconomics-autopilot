#!/usr/bin/env python3
"""yt_upload.py <queue-date> <video-url> <dueAt ISO Z>: upload a Short with our own YouTube token, SCHEDULED for dueAt
(privacyStatus private + publishAt; YouTube flips it public at that time). Due in <15 min = public now.
Used by publish.py when Buffer refuses the YouTube post (Buffer's daily cap is 2 YouTube posts; we post 3).
Prints the video id on the last line. Needs autopilot/keys/youtube-token.json. Run with the .venv python (Google libs)."""
import sys, json, tempfile, urllib.request, datetime as dt
from pathlib import Path
AP = Path(__file__).resolve().parents[1]
D, url, due = sys.argv[1:4]
Q = AP / "queue" / D; cfg = json.load(open(AP / "config.json")); post = json.load(open(Q / "post.json"))
tokf = AP / "keys/youtube-token.json"
if not tokf.exists(): sys.exit("no keys/youtube-token.json")
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
creds = Credentials.from_authorized_user_file(str(tokf))
if not creds.valid: creds.refresh(Request()); tokf.write_text(creds.to_json())
yt = build("youtube", "v3", credentials=creds)
caption = post["caption"].rstrip()
if (Q / "music.json").exists(): caption += "\n" + json.load(open(Q / "music.json"))["credit"]
if json.load(open(Q / "script.json")).get("mode") != "edit": caption += "\nNarrated with an AI voice."
status = {"privacyStatus": "public", "selfDeclaredMadeForKids": False}
t = dt.datetime.fromisoformat(due.replace("Z", "+00:00"))
if t > dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=15):
    status = {"privacyStatus": "private", "publishAt": t.strftime("%Y-%m-%dT%H:%M:%S.000Z"), "selfDeclaredMadeForKids": False}
mp4 = Path(tempfile.mkdtemp()) / "short.mp4"; urllib.request.urlretrieve(url, mp4)
body = {"snippet": {"title": post["title"][:100], "categoryId": cfg["youtube_category_id"],
                    "description": caption + "\n\n" + " ".join(post.get("hashtags", [])[:3])}, "status": status}
vid = yt.videos().insert(part="snippet,status", body=body,
                         media_body=MediaFileUpload(str(mp4), mimetype="video/mp4", resumable=True)).execute()["id"]
st = yt.videos().list(part="status", id=vid).execute()["items"][0]["status"]
print(f"uploaded {vid} privacy={st.get('privacyStatus')} publishAt={st.get('publishAt')}")
print(vid)
