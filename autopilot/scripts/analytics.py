#!/usr/bin/env python3
"""analytics.py — the daily numbers the autopilot reviews before making the next post.

  .venv/bin/python autopilot/scripts/analytics.py

Writes:
  autopilot/log/metrics/<today>.json   raw numbers (YouTube Data + Analytics, Buffer/Instagram, trending)
  autopilot/log/scoreboard.md          one table, every post so far, newest first (rewritten each run)
  autopilot/research/trending.md       today's top US Gaming videos on YouTube (what the audience is watching)
Missing access (no token yet / no Buffer channel) is reported, never fatal.
YouTube Analytics lags 24-72 h: a post <2 days old shows Data-API views only."""
import json, os, subprocess, datetime as dt, urllib.request
from pathlib import Path
AP = Path(__file__).resolve().parents[1]
cfg = json.load(open(AP / "config.json"))
today = dt.date.today().isoformat()
out = {"date": today, "youtube": {}, "instagram": {}, "trending": [], "notes": []}

# ---------------- YouTube ----------------
yt = None
tok = AP / "keys/youtube-token.json"
if tok.exists():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    creds = Credentials.from_authorized_user_file(str(tok))
    if not creds.valid:
        creds.refresh(Request()); tok.write_text(creds.to_json())
    yt = build("youtube", "v3", credentials=creds)
    ya = build("youtubeAnalytics", "v2", credentials=creds)
    ch = yt.channels().list(part="id,statistics,contentDetails", mine=True).execute()["items"][0]
    out["youtube"]["channel"] = {"id": ch["id"], **{k: int(v) for k, v in ch["statistics"].items() if str(v).isdigit()}}
    uploads = ch["contentDetails"]["relatedPlaylists"]["uploads"]
    ids = [i["contentDetails"]["videoId"] for i in yt.playlistItems().list(part="contentDetails", playlistId=uploads, maxResults=50).execute().get("items", [])]
    vids = {}
    if ids:
        for v in yt.videos().list(part="snippet,statistics,contentDetails", id=",".join(ids)).execute()["items"]:
            s = v["statistics"]
            vids[v["id"]] = {"title": v["snippet"]["title"], "published": v["snippet"]["publishedAt"][:10],
                             "views": int(s.get("viewCount", 0)), "likes": int(s.get("likeCount", 0)), "comments": int(s.get("commentCount", 0))}
        start = min(v["published"] for v in vids.values())
        try:
            r = ya.reports().query(ids="channel==MINE", startDate=start, endDate=today, dimensions="video",
                                   metrics="views,averageViewDuration,averageViewPercentage,subscribersGained,shares,likes",
                                   filters="video==" + ",".join(vids), maxResults=200).execute()
            for row in r.get("rows", []):
                vid, views, avd, avp, subs, shares, likes = row
                vids[vid].update({"an_views": views, "avg_view_s": avd, "avg_view_pct": round(avp, 1), "subs": subs, "shares": shares})
            r = ya.reports().query(ids="channel==MINE", startDate=start, endDate=today, dimensions="insightTrafficSourceType",
                                   metrics="views", sort="-views").execute()
            out["youtube"]["traffic_sources"] = {row[0]: row[1] for row in r.get("rows", [])}
        except Exception as e:
            out["notes"].append(f"YouTube Analytics not available yet: {str(e)[:160]}")
    out["youtube"]["videos"] = vids
else:
    out["notes"].append("no YouTube token (run autopilot/scripts/yt_auth.py once)")

# ---------------- Trending (needs any YouTube auth; uses the channel token) ----------------
if yt:
    tr = yt.videos().list(part="snippet,statistics", chart="mostPopular", videoCategoryId="20", regionCode="US", maxResults=25).execute()
    out["trending"] = [{"title": v["snippet"]["title"], "channel": v["snippet"]["channelTitle"],
                        "views": int(v["statistics"].get("viewCount", 0)), "published": v["snippet"]["publishedAt"][:10]} for v in tr["items"]]
    lines = [f"# Trending in Gaming on YouTube (US), {today}\n", "| # | views | channel | title |", "|---|---|---|---|"]
    lines += [f"| {i+1} | {t['views']:,} | {t['channel']} | {t['title']} |" for i, t in enumerate(out["trending"])]
    # Outliers: gaming Shorts from the last 72 h with views far above their channel's typical video (what's working NOW)
    try:
        import datetime as _dt, statistics as _st
        since = (_dt.datetime.utcnow() - _dt.timedelta(hours=72)).strftime("%Y-%m-%dT%H:%M:%SZ")
        focus = [l.split(":", 1)[1].split("#")[0].strip().strip('"') for l in (AP / "CONTROL.md").read_text().splitlines() if l.startswith("focus_this_week")]
        qs = ["gaming news", "gta 6"] + ([focus[0].split()[0] + " " + focus[0].split()[1]] if focus and len(focus[0].split()) > 1 else [])
        found = {}
        for q in dict.fromkeys(qs):
            r = yt.search().list(part="snippet", q=q, type="video", videoDuration="short", order="viewCount", publishedAfter=since,
                                 regionCode="US", relevanceLanguage="en", maxResults=15).execute()
            for it in r.get("items", []): found[it["id"]["videoId"]] = it["snippet"]
        vs = yt.videos().list(part="statistics,snippet", id=",".join(list(found)[:50])).execute().get("items", [])
        chans = list({v["snippet"]["channelId"] for v in vs})[:50]
        cs = {c["id"]: c for c in yt.channels().list(part="statistics", id=",".join(chans)).execute().get("items", [])} if chans else {}
        rows = []
        for v in vs:
            views = int(v["statistics"].get("viewCount", 0)); c = cs.get(v["snippet"]["channelId"], {}).get("statistics", {})
            avg = int(c.get("viewCount", 0)) / max(1, int(c.get("videoCount", 1)))
            rows.append((views / max(avg, 1), views, int(c.get("subscriberCount", 0) or 0), v["snippet"]["channelTitle"], v["snippet"]["title"]))
        rows.sort(reverse=True)
        L = [f"# Outlier gaming Shorts, last 72 h ({today}): views ÷ channel's average views per video", "",
             "| x avg | views | channel subs | channel | title |", "|---|---|---|---|---|"]
        L += [f"| {r[0]:.1f}x | {r[1]:,} | {r[2]:,} | {r[3]} | {r[4]} |" for r in rows[:20]]
        (AP / "research/outliers.md").write_text("\n".join(L) + "\n"); out["outliers"] = rows[:20]
    except Exception as e: out["notes"].append(f"outliers failed: {e}")

# ---------------- Instagram via Buffer ----------------
def buffer_key():
    if os.environ.get("BUFFER_API_KEY"): return os.environ["BUFFER_API_KEY"]
    k = cfg["buffer_key_keychain"]
    return subprocess.run(["security", "find-generic-password", "-s", k["service"], "-a", k["account"], "-w"], capture_output=True, text=True).stdout.strip()
key = buffer_key()
if key and cfg["buffer_channels"].get("instagram"):
    q = """query($o: OrganizationId!, $c: [ChannelId!]){ posts(first: 50, input:{organizationId:$o, filter:{status:[sent], channelIds:$c}},
           ){ edges{ node{ id text sentAt externalLink metrics{ type value } } } } }"""
    req = urllib.request.Request("https://api.buffer.com", data=json.dumps({"query": q, "variables": {"o": cfg["buffer_organization_id"],
          "c": [cfg["buffer_channels"]["instagram"]]}}).encode(), headers={"Content-Type": "application/json", "Authorization": "Bearer " + key})
    try:
        body = json.loads(urllib.request.urlopen(req, timeout=60).read())
        for e in ((body.get("data") or {}).get("posts") or {}).get("edges", []):
            n = e["node"]; m = {x["type"]: x["value"] for x in (n.get("metrics") or [])}
            out["instagram"][n["id"]] = {"sent": (n.get("sentAt") or "")[:10], "text": n["text"][:60], "link": n.get("externalLink"), **m}
        if body.get("errors"): out["notes"].append("Buffer: " + json.dumps(body["errors"])[:200])
    except Exception as ex:
        out["notes"].append(f"Buffer metrics failed: {ex}")
else:
    out["notes"].append("no Buffer key / Instagram channel configured yet")

(AP / "log/metrics").mkdir(parents=True, exist_ok=True)
json.dump(out, open(AP / f"log/metrics/{today}.json", "w"), indent=1)

# ---------------- Scoreboard ----------------
rows = ["# Scoreboard (rewritten daily by analytics.py)\n", f"Updated {today}. YouTube Analytics lags 1-3 days.\n",
        "## YouTube", "| published | views | avg view % | avg view s | likes | shares | subs+ | title |", "|---|---|---|---|---|---|---|---|"]
for vid, v in sorted(out["youtube"].get("videos", {}).items(), key=lambda kv: kv[1]["published"], reverse=True):
    rows.append(f"| {v['published']} | {v['views']} | {v.get('avg_view_pct','—')} | {v.get('avg_view_s','—')} | {v['likes']} | {v.get('shares','—')} | {v.get('subs','—')} | {v['title'][:60]} |")
if out["youtube"].get("traffic_sources"):
    rows += ["", "Traffic sources (all time): " + ", ".join(f"{k} {v}" for k, v in out["youtube"]["traffic_sources"].items())]
rows += ["", "## Instagram", "| sent | views | reach | likes | comments | shares | saves | follows | avg watch s | post |", "|---|---|---|---|---|---|---|---|---|---|"]
for pid, p in out["instagram"].items():
    g = lambda k: int(p[k]) if k in p else "—"
    rows.append(f"| {p['sent']} | {g('views')} | {g('reach')} | {g('reactions')} | {g('comments')} | {g('shares')} | {g('saves')} | {g('follows')} | {p.get('averageTimeWatched','—')} | {p['text']} |")
if out["notes"]:
    rows += ["", "Notes: " + " · ".join(out["notes"])]
(AP / "log/scoreboard.md").write_text("\n".join(rows) + "\n")
print("\n".join(rows))
