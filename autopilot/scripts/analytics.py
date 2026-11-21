#!/usr/bin/env python3
"""analytics.py — the daily numbers the autopilot reviews before making the next post.

  .venv/bin/python autopilot/scripts/analytics.py

Writes:
  autopilot/log/metrics/<today>.json   raw numbers (YouTube Data + Analytics, Buffer/Instagram, trending)
  autopilot/log/scoreboard.md          one table, every post so far, newest first (rewritten each run)
  autopilot/research/trending.md       today's top US Gaming videos on YouTube (what the audience is watching)
Missing access (no token yet / no Buffer channel) is reported, never fatal.
YouTube Analytics lags 24-72 h: a post <2 days old shows Data-API views only."""
import json, os, re, subprocess, datetime as dt, urllib.request
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
    vids, durs = {}, {}
    if ids:
        for v in yt.videos().list(part="snippet,statistics,contentDetails", id=",".join(ids)).execute()["items"]:
            s = v["statistics"]
            vids[v["id"]] = {"title": v["snippet"]["title"], "published": v["snippet"]["publishedAt"][:10],
                             "views": int(s.get("viewCount", 0)), "likes": int(s.get("likeCount", 0)), "comments": int(s.get("commentCount", 0))}
            m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", v["contentDetails"]["duration"]); durs[v["id"]] = int(m[1] or 0) * 3600 + int(m[2] or 0) * 60 + int(m[3] or 0) if m else 0
            vids[v["id"]]["dur"] = durs[v["id"]]
        start = min(v["published"] for v in vids.values())
        try:
            r = ya.reports().query(ids="channel==MINE", startDate=start, endDate=today, dimensions="video",
                                   metrics="views,averageViewDuration,averageViewPercentage,subscribersGained,shares,likes",
                                   filters="video==" + ",".join(vids), maxResults=200).execute()
            for row in r.get("rows", []):
                vid, views, avd, avp, subs, shares, likes = row
                vids[vid].update({"an_views": views, "avg_view_s": avd, "avg_view_pct": round(avp, 1), "subs": subs, "shares": shares})
            # Hook strength (19 Nov): YouTube's retention curve per video. audienceWatchRatio at a point = share of starting
            # viewers still watching there (can exceed 1 on loops). The first second is where every Short loses most people.
            for vid in vids:
                try:
                    dur_s = durs.get(vid) or 0
                    rr = ya.reports().query(ids="channel==MINE", startDate=start, endDate=today, dimensions="elapsedVideoTimeRatio",
                                            metrics="audienceWatchRatio,relativeRetentionPerformance", filters="video==" + vid).execute().get("rows", [])
                    if not rr or not dur_s: continue
                    def at(sec, rr=rr, dur_s=dur_s):
                        x = min(1.0, sec / dur_s); return min(rr, key=lambda r: abs(r[0] - x))
                    vids[vid].update({"hold_1s": round(at(1)[1] * 100), "hold_3s": round(at(3)[1] * 100),
                                      "hold_end": round(rr[-1][1] * 100), "vs_similar_3s": round(at(3)[2], 2), "dur_s": dur_s})
                except Exception as e:
                    out["notes"].append(f"retention {vid}: {str(e)[:100]}"); break
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
           ){ edges{ node{ id text sentAt externalLink channelService metrics{ type value } } } } }"""
    req = urllib.request.Request("https://api.buffer.com", data=json.dumps({"query": q, "variables": {"o": cfg["buffer_organization_id"],
          "c": [c for c in (cfg["buffer_channels"]["instagram"], cfg["buffer_channels"].get("tiktok")) if c]}}).encode(), headers={"Content-Type": "application/json", "Authorization": "Bearer " + key})
    try:
        body = json.loads(urllib.request.urlopen(req, timeout=60).read())
        for e in ((body.get("data") or {}).get("posts") or {}).get("edges", []):
            n = e["node"]; m = {x["type"]: x["value"] for x in (n.get("metrics") or [])}
            out["instagram"][n["id"]] = {"sent": (n.get("sentAt") or "")[:10], "text": n["text"][:60], "link": n.get("externalLink"), "service": n.get("channelService"), **m}
        if body.get("errors"): out["notes"].append("Buffer: " + json.dumps(body["errors"])[:200])
    except Exception as ex:
        out["notes"].append(f"Buffer metrics failed: {ex}")
else:
    out["notes"].append("no Buffer key / Instagram channel configured yet")

# ---------------- Instagram straight from Instagram (20 Nov: token now has instagram_manage_insights) ----------------
# Buffer only knows posts it published and lost IG for a day; the Graph API sees every Reel, direct posts included.
out["ig_graph"] = {}
IG_TOK = os.environ.get("IG_ACCESS_TOKEN") or subprocess.run(["security", "find-generic-password", "-s", "ggeconomics-instagram",
          "-a", "ig_graph", "-w"], capture_output=True, text=True).stdout.strip()
IG_UID = os.environ.get("IG_USER_ID") or cfg.get("instagram_user_id", "17841461684732203")
if IG_TOK:
    def igg(path):
        return json.loads(urllib.request.urlopen(f"https://graph.facebook.com/v21.0/{path}{'&' if '?' in path else '?'}access_token={IG_TOK}", timeout=60).read())
    try:
        since = (dt.date.today() - dt.timedelta(days=30)).isoformat()
        for m in igg(f"{IG_UID}/media?fields=id,caption,timestamp,media_product_type,permalink,like_count,comments_count&limit=50").get("data", []):
            if m["timestamp"][:10] < since: continue
            reel = m.get("media_product_type") == "REELS"
            mets = "views,reach,saved,shares,total_interactions" + (",ig_reels_avg_watch_time" if reel else "")
            try: ins = {x["name"]: x["values"][0]["value"] for x in igg(f"{m['id']}/insights?metric={mets}").get("data", [])}
            except Exception as e: ins = {"error": str(e)[:80]}
            out["ig_graph"][m["id"]] = {"sent": m["timestamp"][:10], "type": "reel" if reel else "post", "caption": (m.get("caption") or "")[:300],
                                        "link": m.get("permalink"), "likes": m.get("like_count"), "comments": m.get("comments_count"), **ins}
    except Exception as e: out["notes"].append(f"Instagram Graph failed: {str(e)[:150]}")
_n = lambda s: re.sub(r"[^a-z0-9]", "", (s or "").lower())
def ig_graph_for(q, kind):
    """kind reel|post: the Graph media for this queue post (direct id first, else caption match)."""
    b = json.load(open(q / "buffer_ids.json")); did = (b.get("direct") or {}).get("instagram_reel")
    if kind == "reel" and did in out["ig_graph"]: return out["ig_graph"][did]
    pj = json.load(open(q / "post.json")) if (q / "post.json").exists() else {}
    keys = [_n(pj.get("ig_first_line"))[:40], _n(pj.get("caption"))[:40]]
    for m in out["ig_graph"].values():
        if m["type"] == kind and any(k and k in _n(m["caption"]) for k in keys): return m
    return None

# ---------------- Per post, views split by platform (queue post → YouTube video + Buffer Instagram posts) ----------------
yt_done = json.load(open(AP / "log/yt_done.json")) if (AP / "log/yt_done.json").exists() else {}
per_post = {}
for q in sorted((AP / "queue").iterdir(), reverse=True):
    if not (q / "buffer_ids.json").exists() or (q / "dry").exists() or q.name[:10] > today: continue
    ids = json.load(open(q / "buffer_ids.json")).get("ids", {})
    title = json.load(open(q / "post.json")).get("title", "?") if (q / "post.json").exists() else "?"
    yv = (out["youtube"].get("videos") or {}).get((yt_done.get(q.name) or {}).get("video"))
    def ig(name):
        p = out["instagram"].get(ids.get(name) or "")
        v = None if p is None else p.get("views", p.get("reach"))
        return None if v is None else int(float(v))
    gr, gp = ig_graph_for(q, "reel"), ig_graph_for(q, "post")
    per_post[q.name] = {"title": title, "youtube_short": yv["views"] if yv else None,
                        "instagram_reel": gr["views"] if gr and "views" in gr else ig("instagram_reel"),
                        "instagram_carousel": (gp.get("views", gp.get("reach")) if gp else None) or ig("instagram_carousel"),
                        "tiktok_video": ig("tiktok_video")}
out["per_post"] = per_post

# ---------------- Reach alarm (18 Nov: TikTok sat at 0 views for 16 h and nobody looked) ----------------
# any post sent 12h+ ago with 0 views on a platform, or a YouTube Short under 50 views after 24h = a distribution problem
now = dt.datetime.now(dt.timezone.utc); alarms = []
for pid, p in out["instagram"].items():
    if not p.get("sent"): continue
    age = (now - dt.datetime.fromisoformat(p["sent"] + "T00:00:00+00:00")).total_seconds() / 3600
    if age >= 24 and int(float(p.get("views", p.get("reach", 0)) or 0)) == 0:
        alarms.append(f"{p.get('service') or 'instagram'} 0 views: {p['text'][:40]}")
for vid, v in (out["youtube"].get("videos") or {}).items():
    if v["published"] <= (now - dt.timedelta(days=1)).date().isoformat() and v["views"] < 50:
        alarms.append(f"youtube {v['views']} views after 24h: {v['title'][:40]}")
if alarms:
    out["notes"].append("REACH ALARM: " + " | ".join(alarms))
    seen_p = AP / "log/alarms_sent.json"; seen = json.loads(seen_p.read_text()) if seen_p.exists() else []
    new = [a for a in alarms if a not in seen]
    if new:
        subprocess.run(["python3", str(AP / "scripts/notify.py"), "Reach alarm: " + "; ".join(new)[:900], "high"])
        seen_p.write_text(json.dumps(seen + new, indent=1))
(AP / "log/metrics").mkdir(parents=True, exist_ok=True)
json.dump(out, open(AP / f"log/metrics/{today}.json", "w"), indent=1)

# ---------------- Scoreboard ----------------
rows = ["# Scoreboard (rewritten daily by analytics.py)\n", f"Updated {today}. YouTube Analytics lags 1-3 days.\n",
        "## Per post: views by platform", "(— = not sent yet / no metrics yet; carousel shows reach when Buffer gives no views)",
        "| post | YouTube Short | IG Reel | IG carousel | TikTok | total | title |", "|---|---|---|---|---|---|---|"]
for name, p in per_post.items():
    nums = [p[k] for k in ("youtube_short", "instagram_reel", "instagram_carousel", "tiktok_video")]
    rows.append(f"| {name} | " + " | ".join("—" if n is None else str(n) for n in nums) + f" | {sum(n for n in nums if n)} | {p['title'][:60]} |")
rows += ["", "## YouTube", "| published | views | avg view % | avg view s | kept 1s % | kept 3s % | 3s vs similar | likes | shares | subs+ | title |", "|---|---|---|---|---|---|---|---|---|---|---|"]
for vid, v in sorted(out["youtube"].get("videos", {}).items(), key=lambda kv: kv[1]["published"], reverse=True):
    rows.append(f"| {v['published']} | {v['views']} | {v.get('avg_view_pct','—')} | {v.get('avg_view_s','—')} | {v.get('hold_1s','—')} | {v.get('hold_3s','—')} | {v.get('vs_similar_3s','—')} | {v['likes']} | {v.get('shares','—')} | {v.get('subs','—')} | {v['title'][:60]} |")
longs = {k: v for k, v in out["youtube"].get("videos", {}).items() if v.get("dur", 0) >= 180}
if longs:   # the weekly 8-min Top 10 (from 22 Nov): judged on avg view %, minutes watched and subscribers, not 3 s holds
    rows += ["", "## YouTube long videos (weekly Top 10)", "| published | length | views | avg view % | avg view s | subs+ | likes | comments | title |", "|---|---|---|---|---|---|---|---|---|"]
    for vid, v in sorted(longs.items(), key=lambda kv: kv[1]["published"], reverse=True):
        rows.append(f"| {v['published']} | {v['dur'] // 60}:{v['dur'] % 60:02d} | {v['views']} | {v.get('avg_view_pct','—')} | {v.get('avg_view_s','—')} | {v.get('subs','—')} | {v['likes']} | {v['comments']} | {v['title'][:60]} |")
if out["youtube"].get("traffic_sources"):
    rows += ["", "Traffic sources (all time): " + ", ".join(f"{k} {v}" for k, v in out["youtube"]["traffic_sources"].items())]
if out["ig_graph"]:
    rows += ["", "## Instagram (from Instagram itself)", "| sent | type | views | reach | likes | comments | shares | saves | avg watch s | post |", "|---|---|---|---|---|---|---|---|---|---|"]
    for mid, m in sorted(out["ig_graph"].items(), key=lambda kv: kv[1]["sent"], reverse=True):
        w = m.get("ig_reels_avg_watch_time"); w = round(w / 1000, 1) if isinstance(w, (int, float)) else "—"
        rows.append(f"| {m['sent']} | {m['type']} | {m.get('views','—')} | {m.get('reach','—')} | {m.get('likes','—')} | {m.get('comments','—')} | {m.get('shares','—')} | {m.get('saved','—')} | {w} | {m['caption'][:60].splitlines()[0] if m['caption'] else ''} |")
rows += ["", "## Instagram via Buffer (old view)", "| sent | views | reach | likes | comments | shares | saves | follows | avg watch s | post |", "|---|---|---|---|---|---|---|---|---|---|"]
for pid, p in out["instagram"].items():
    if p.get("service") == "tiktok": continue
    g = lambda k: int(p[k]) if k in p else "—"
    rows.append(f"| {p['sent']} | {g('views')} | {g('reach')} | {g('reactions')} | {g('comments')} | {g('shares')} | {g('saves')} | {g('follows')} | {p.get('averageTimeWatched','—')} | {p['text']} |")
tt = [p for p in out["instagram"].values() if p.get("service") == "tiktok"]
if tt:
    rows += ["", "## TikTok", "| sent | views | reach | likes | comments | shares | avg watch s | post |", "|---|---|---|---|---|---|---|---|"]
    for p in tt:
        g = lambda k: int(float(p[k])) if k in p else "—"
        rows.append(f"| {p['sent']} | {g('views')} | {g('reach')} | {g('reactions')} | {g('comments')} | {g('shares')} | {p.get('averageTimeWatched','—')} | {p['text']} |")
if out["notes"]:
    rows += ["", "Notes: " + " · ".join(out["notes"])]
(AP / "log/scoreboard.md").write_text("\n".join(rows) + "\n")
print("\n".join(rows))
