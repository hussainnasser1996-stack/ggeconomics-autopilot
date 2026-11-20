#!/usr/bin/env python3
"""engage.py — comment replies with no human in the loop (monitor.yml, every 6 h). Two halves:
1. SEND: autopilot/log/comments_outbox.json (written by the Claude heartbeat routine, rules in autopilot/COMMENTS.md)
   = [{"platform": "youtube"|"instagram", "id": "<comment id>", "reply": "..."} | {..., "skip": "<reason>"}].
   Posts each reply as the channel, records it in log/comments_state.json, empties the outbox.
2. COLLECT: every comment from the last 14 days on YouTube + Instagram that isn't ours and isn't handled yet
   → log/comments_inbox.json, with the post's title and caption (the facts + sources a reply may use).
Likes/hearts on comments: no API exists on YouTube, Instagram or TikTok. TikTok comments: no API for our account type.
Missing token = that platform is skipped, never fatal. Exit 0 always."""
import json, os, re, sys, urllib.request, urllib.parse, datetime as dt
from pathlib import Path
AP = Path(__file__).resolve().parents[1]; L = AP / "log"
cfg = json.load(open(AP / "config.json"))
state_p, inbox_p, out_p = L / "comments_state.json", L / "comments_inbox.json", L / "comments_outbox.json"
state = json.loads(state_p.read_text()) if state_p.exists() else {}
outbox = json.loads(out_p.read_text()) if out_p.exists() and out_p.read_text().strip() else []
now = dt.datetime.now(dt.timezone.utc); cutoff = now - dt.timedelta(days=14)
YT_CH = cfg.get("youtube_channel_id", "UCpsoR_hS2XJT-Yv7UN0qZbQ"); IG_NAME = cfg.get("instagram_username", "ggeconomics")
log = []

# ---------- clients ----------
yt = None
tok = AP / "keys/youtube-token.json"
if tok.exists():
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        c = Credentials.from_authorized_user_file(str(tok))
        if not c.valid: c.refresh(Request()); tok.write_text(c.to_json())
        yt = build("youtube", "v3", credentials=c, cache_discovery=False)
    except Exception as e: log.append(f"youtube client failed: {e}")
IG_TOK, IG_UID = os.environ.get("IG_ACCESS_TOKEN"), os.environ.get("IG_USER_ID") or cfg.get("instagram_user_id", "17841461684732203")
G = "https://graph.facebook.com/v21.0/"
def ig(path, data=None):
    if data is None:
        url = G + path + ("&" if "?" in path else "?") + "access_token=" + IG_TOK
        return json.loads(urllib.request.urlopen(url, timeout=60).read())
    body = urllib.parse.urlencode({**data, "access_token": IG_TOK}).encode()
    return json.loads(urllib.request.urlopen(urllib.request.Request(G + path, data=body), timeout=60).read())

# ---------- 1. SEND ----------
left = []
for o in outbox:
    cid, plat = o.get("id"), o.get("platform"); parent = o.get("reply_to") or cid
    if not cid or cid in state: continue
    if o.get("skip"):
        state[cid] = {"platform": plat, "status": "skipped", "why": o["skip"], "at": now.isoformat()}; continue
    reply = (o.get("reply") or "").strip()
    if not reply or re.search(r"https?://|www\.", reply): log.append(f"refused reply to {cid}: empty or has a link"); continue
    try:
        if plat == "youtube" and yt:
            yt.comments().insert(part="snippet", body={"snippet": {"parentId": parent, "textOriginal": reply[:1000]}}).execute()
        elif plat == "instagram" and IG_TOK:
            ig(f"{parent}/replies", {"message": reply[:900]})
        else: left.append(o); continue
        state[cid] = {"platform": plat, "status": "replied", "reply": reply, "at": now.isoformat()}
        log.append(f"replied on {plat} {cid}: {reply[:80]}")
    except Exception as e:
        err = getattr(e, "read", lambda: b"")(); log.append(f"reply failed {plat} {cid}: {e} {err[:200]!r}")
        o["tries"] = o.get("tries", 0) + 1
        if o["tries"] < 3: left.append(o)
        else: state[cid] = {"platform": plat, "status": "failed", "at": now.isoformat()}
out_p.write_text(json.dumps(left, indent=1))

# ---------- 2. COLLECT ----------
# A thread = top comment + replies, oldest first. Answer only what came AFTER our last message in it, once.
def pending(msgs, is_ours):
    last = max([i for i, m in enumerate(msgs) if is_ours(m)], default=-1)
    return [m for m in msgs[last + 1:] if not is_ours(m)]
inbox = []
if yt:
    try:
        threads = yt.commentThreads().list(part="snippet,replies", allThreadsRelatedToChannelId=YT_CH, maxResults=100,
                                           textFormat="plainText").execute().get("items", [])
        vids = list({t["snippet"]["videoId"] for t in threads}); meta = {}
        for i in range(0, len(vids), 50):
            for v in yt.videos().list(part="snippet", id=",".join(vids[i:i + 50])).execute().get("items", []):
                meta[v["id"]] = (v["snippet"]["title"], v["snippet"]["description"][:900])
        ours = lambda m: (m["snippet"].get("authorChannelId") or {}).get("value") == YT_CH
        for t in threads:
            top = t["snippet"]["topLevelComment"]; vid = t["snippet"]["videoId"]
            reps = sorted((t.get("replies") or {}).get("comments", []), key=lambda m: m["snippet"]["publishedAt"])
            for m in pending([top] + reps, ours):
                sn = m["snippet"]
                if m["id"] in state or sn["publishedAt"] < cutoff.isoformat(): continue
                inbox.append({"platform": "youtube", "id": m["id"], "reply_to": top["id"], "author": sn.get("authorDisplayName"),
                              "text": sn.get("textOriginal") or sn.get("textDisplay"), "at": sn["publishedAt"],
                              "thread": [x["snippet"].get("textOriginal", "")[:200] for x in [top] + reps][-4:],
                              "post_title": meta.get(vid, ("?", ""))[0], "post_caption": meta.get(vid, ("", ""))[1],
                              "link": f"https://www.youtube.com/shorts/{vid}"})
    except Exception as e: log.append(f"youtube collect failed: {str(e)[:200]}")
if IG_TOK:
    try:
        media = ig(f"{IG_UID}/media?fields=id,caption,timestamp,permalink,comments_count&limit=30").get("data", [])
        ours = lambda x: x.get("username") == IG_NAME
        for m in media:
            if m["timestamp"] < cutoff.strftime("%Y-%m-%dT%H:%M:%S") or not m.get("comments_count"): continue
            for c in ig(f"{m['id']}/comments?fields=id,text,username,timestamp,replies{{id,text,username,timestamp}}&limit=50").get("data", []):
                reps = sorted((c.get("replies") or {}).get("data", []), key=lambda x: x.get("timestamp", ""))
                for x in pending([c] + reps, ours):
                    if x["id"] in state: continue
                    inbox.append({"platform": "instagram", "id": x["id"], "reply_to": c["id"], "author": x.get("username"),
                                  "text": x.get("text"), "at": x.get("timestamp"),
                                  "thread": [y.get("text", "")[:200] for y in [c] + reps][-4:],
                                  "post_title": (m.get("caption") or "").split("\n")[0][:100],
                                  "post_caption": (m.get("caption") or "")[:900], "link": m.get("permalink")})
    except Exception as e: log.append(f"instagram collect failed: {str(e)[:200]}")
inbox_p.write_text(json.dumps(inbox, indent=1, ensure_ascii=False))
state_p.write_text(json.dumps(state, indent=1, ensure_ascii=False))
print(f"engage: inbox {len(inbox)} new comment(s), outbox left {len(left)}"); print("\n".join(log))
