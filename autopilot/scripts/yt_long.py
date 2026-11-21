#!/usr/bin/env python3
"""yt_long.py <dir>: upload a long-form video with our own YouTube token.
<dir> = autopilot/longform/<D>/ holding meta.json {title, description, tags, publish_at, video_url, thumb (file in dir), playlist_title}.
Schedules it (private + publishAt), sets the thumbnail, files it in its playlist (created if missing). Idempotent: writes
uploaded.json with the video id and skips if it exists. Verifies status and thumbnail through the API."""
import sys, json, tempfile, urllib.request, datetime as dt
from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
AP = Path(__file__).resolve().parents[1]; d = Path(sys.argv[1]); m = json.load(open(d / "meta.json"))
done = d / "uploaded.json"
if done.exists(): sys.exit(f"already uploaded: {done.read_text()}")
creds = Credentials.from_authorized_user_file(str(AP / "keys/youtube-token.json"))
if not creds.valid: creds.refresh(Request())
yt = build("youtube", "v3", credentials=creds, cache_discovery=False)
t = dt.datetime.fromisoformat(m["publish_at"].replace("Z", "+00:00"))
status = {"privacyStatus": "public", "selfDeclaredMadeForKids": False}
if t > dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=15):
    status = {"privacyStatus": "private", "publishAt": t.strftime("%Y-%m-%dT%H:%M:%S.000Z"), "selfDeclaredMadeForKids": False}
mp4 = Path(tempfile.mkdtemp()) / "long.mp4"; urllib.request.urlretrieve(m["video_url"], mp4)
print("downloaded", mp4.stat().st_size, "bytes")
body = {"snippet": {"title": m["title"][:100], "description": m["description"][:4900], "tags": m.get("tags", [])[:15],
                    "categoryId": "20", "defaultLanguage": "en", "defaultAudioLanguage": "en"}, "status": status}
req = yt.videos().insert(part="snippet,status", body=body, media_body=MediaFileUpload(str(mp4), mimetype="video/mp4", chunksize=32 * 1024 * 1024, resumable=True))
resp = None
while resp is None:
    st, resp = req.next_chunk()
    if st: print(f"upload {int(st.progress() * 100)}%")
vid = resp["id"]; rec = {"video": vid}
done.write_text(json.dumps(rec, indent=1))           # written at once so a later failure never double-uploads
try:
    yt.thumbnails().set(videoId=vid, media_body=MediaFileUpload(str(d / m["thumb"]), mimetype="image/png")).execute(); rec["thumb"] = "ok"
except Exception as e: rec["thumb"] = f"error: {e}"[:300]
try:
    pls = yt.playlists().list(part="snippet", mine=True, maxResults=50).execute().get("items", [])
    pl = next((p["id"] for p in pls if p["snippet"]["title"] == m["playlist_title"]), None)
    if not pl:
        pl = yt.playlists().insert(part="snippet,status", body={"snippet": {"title": m["playlist_title"], "description": m.get("playlist_description", "")},
                                                                  "status": {"privacyStatus": "public"}}).execute()["id"]
    yt.playlistItems().insert(part="snippet", body={"snippet": {"playlistId": pl, "resourceId": {"kind": "youtube#video", "videoId": vid}}}).execute()
    rec["playlist"] = pl
except Exception as e: rec["playlist"] = f"error: {e}"[:300]
v = yt.videos().list(part="status,snippet,contentDetails", id=vid).execute()["items"][0]
rec.update(privacy=v["status"]["privacyStatus"], publish_at=v["status"].get("publishAt"), duration=v["contentDetails"]["duration"],
           thumb_url=v["snippet"]["thumbnails"].get("maxres", v["snippet"]["thumbnails"].get("high", {})).get("url"))
done.write_text(json.dumps(rec, indent=1)); print(json.dumps(rec, indent=1))
