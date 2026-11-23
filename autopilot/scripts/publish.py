#!/usr/bin/env python3
"""publish.py <date> [--dry] | publish.py <date> --rebook <channel_job> [--direct]
--direct: skip Buffer. instagram_reel → Instagram Graph API (IG_ACCESS_TOKEN, IG_USER_ID); youtube_short → YouTube Data API
(keys/youtube-token.json), used when Buffer's YouTube posting cap blocks a slot.
--rebook: re-create ONE failed Buffer post (e.g. instagram_reel after a channel reconnect) from the media already hosted,
due in 5 min; the old id moves to buffer_ids.json "replaced". Used by monitor.py.
Hosts queue/<date>/short.mp4 (+ carousel PNGs) in the public media repo, then schedules them in Buffer:
YouTube Short + Instagram Reel + TikTok (+ Instagram carousel on carousel days). Writes queue/<date>/buffer_ids.json.
Never runs twice for the same date (buffer_ids.json guard). Key: macOS keychain (config.json → buffer_key_keychain)."""
import sys, json, os, subprocess, shutil, urllib.request, urllib.error, time
# the macOS keychain only exists on the Mac; on the Linux runner the secrets come from env (23 Nov: analytics.py
# crashed with FileNotFoundError: 'security' when IG_ACCESS_TOKEN was not set in that step)
import shutil as _sh
_kc = lambda a, **k: subprocess.run(a, **k) if _sh.which(a[0]) else subprocess.CompletedProcess(a, 1, "", "")
from pathlib import Path
from datetime import datetime
AP = Path(__file__).resolve().parents[1]
cfg = json.load(open(AP / "config.json"))
D = sys.argv[1]; dry = "--dry" in sys.argv
rebook = sys.argv[sys.argv.index("--rebook") + 1] if "--rebook" in sys.argv else None
Q = AP / "queue" / D
post = json.load(open(Q / "post.json"))          # {title, caption, hashtags, carousel: bool}
ctl = (AP / "CONTROL.md").read_text()
mode = next((l.split(":", 1)[1].split("#")[0].strip() for l in ctl.splitlines() if l.startswith("mode:")), "dry_run")
if mode != "auto": dry = True
if (Q / "buffer_ids.json").exists() and not rebook: sys.exit("already scheduled (buffer_ids.json exists)")
if rebook and not (Q / "buffer_ids.json").exists(): sys.exit("--rebook needs an existing buffer_ids.json")
hh, mm = cfg.get("publish_time_utc", "23:00").split(":") if "publish_time_utc" in cfg else \
    next(l.split('"')[1] for l in ctl.splitlines() if l.startswith("publish_time_utc")).split(":")
if post.get("publish_time_utc"): hh, mm = post["publish_time_utc"].split(":")   # extra daily slots (queue/<date>b, c…)
DATE = D[:10]
due = f"{DATE}T{hh}:{mm}:00.000Z"
from datetime import timezone, timedelta
_now = datetime.now(timezone.utc)
if rebook or datetime.fromisoformat(due.replace("Z", "+00:00")) < _now + timedelta(minutes=4):    # built late: post in 5 min
    due = (_now + timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:00.000Z")

# ---- 1. host media
repo = Path(os.path.expanduser(os.environ.get("MEDIA_REPO_DIR") or cfg["media_repo_local"]))
raw = f"https://raw.githubusercontent.com/{cfg['media_repo']}/main"
import hashlib
if not rebook:                                         # rebook: the video is not in git, reuse the hosted URLs below
    sha = hashlib.sha1(open(Q / "short.mp4", "rb").read()).hexdigest()[:8]
    vname = f"video/{D}-{sha}.mp4"; urls = {"video": f"{raw}/{vname}", "images": []}
    slides = sorted(Q.glob("slide_*.png")) if post.get("carousel") and not (Q / "carousel_sent").exists() else []   # carousel_sent: unbook kept an already-posted carousel
if rebook:
    urls = json.load(open(Q / "buffer_ids.json"))["urls"]; slides = urls["images"]
elif not dry:
    shutil.copy(Q / "short.mp4", repo / vname)
    for s in slides:
        shutil.copy(s, repo / f"img/{D}-{sha}-{s.name}"); urls["images"].append(f"{raw}/img/{D}-{sha}-{s.name}")
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-qm", f"media {D}"], check=True)
    subprocess.run(["git", "-C", str(repo), "push", "-q"], check=True)
    for u in [urls["video"]] + urls["images"]:
        code = subprocess.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "-I", u], capture_output=True, text=True).stdout
        if code != "200": sys.exit(f"media not reachable yet: {u} -> {code}")

# ---- 2. Buffer
def key():
    if os.environ.get("BUFFER_API_KEY"): return os.environ["BUFFER_API_KEY"]
    k = cfg["buffer_key_keychain"]
    return _kc(["security", "find-generic-password", "-s", k["service"], "-a", k["account"], "-w"],
                          capture_output=True, text=True).stdout.strip()
def gql(q, v):
    req = urllib.request.Request("https://api.buffer.com", data=json.dumps({"query": q, "variables": v}).encode(),
          headers={"Content-Type": "application/json", "Authorization": "Bearer " + key()}, method="POST")
    for i in range(4):   # 23 Nov: Buffer's free plan allows ~250 calls / 24 h; back off on 429 instead of crashing the build
        try: body = json.loads(urllib.request.urlopen(req, timeout=60).read()); break
        except urllib.error.HTTPError as e:
            if e.code != 429 or i == 3: raise
            time.sleep(min(60, int(e.headers.get("Retry-After") or 0) or 5 * 2 ** i))
    if body.get("errors"): sys.exit("GraphQL error: " + json.dumps(body["errors"]))
    return body["data"]
MUT = """mutation($i: CreatePostInput!){ createPost(input:$i){ __typename
  ... on PostActionSuccess { post { id dueAt } } ... on MutationError { message } } }"""
if (Q / "music.json").exists():                       # CC BY credit for the music bed
    post["caption"] = post["caption"].rstrip() + "\n" + json.load(open(Q / "music.json"))["credit"]
is_edit = json.load(open(Q / "script.json")).get("mode") == "edit"   # music-only edit = real gameplay + text, no voice
if not is_edit:                                       # 19 Nov: edits were wrongly captioned "Narrated with an AI voice"
    post["caption"] = post["caption"].rstrip() + "\nNarrated with an AI voice."           # transparency (no AI persona)
ig_caption = (post["ig_first_line"].strip() + "\n" + post["caption"].strip()) if post.get("ig_first_line") else post["caption"].strip()
text = ig_caption + "\n\n" + " ".join([h for h in post.get("hashtags", []) if h.lower() != "#shorts"][:5])
jobs = []
ch = cfg["buffer_channels"]
if ch.get("youtube"):
    jobs.append(("youtube_short", {"text": post["caption"].strip() + "\n\n" + " ".join(post.get("hashtags", [])[:3]), "channelId": ch["youtube"],
        "schedulingType": "automatic", "mode": "customScheduled", "dueAt": due, "assets": [{"video": {"url": urls["video"]}}],
        "metadata": {"youtube": {"title": post["title"][:100], "categoryId": cfg["youtube_category_id"], "privacy": "public",
                                 "madeForKids": False, "notifySubscribers": True}}}))
if ch.get("instagram"):
    jobs.append(("instagram_reel", {"text": text[:2200], "channelId": ch["instagram"], "schedulingType": "automatic",
        "mode": "customScheduled", "dueAt": due, "assets": [{"video": {"url": urls["video"], "metadata": {"thumbnailOffset": 1500}}}],
        "metadata": {"instagram": {"type": "reel", "shouldShareToFeed": True, "isAiGenerated": not is_edit}}}))   # firstComment needs Buffer paid (tested 16 Nov)   # Meta: realistic AI audio (our narrator) → disclose
    if slides:
        due2 = due if rebook else f"{DATE}T{(int(hh) - 8) % 24:02d}:{mm}:00.000Z"   # carousel ~8h before the Reel
        ctext = (post.get("carousel_caption") or text)   # E4 (GROWTH.md, 21 Nov): its own caption, never a copy of the Reel's
        if post.get("carousel_caption") and post.get("hashtags"): ctext += "\n\n" + " ".join([h for h in post["hashtags"] if h.lower() != "#shorts"][:5])
        jobs.append(("instagram_carousel", {"text": ctext[:2200], "channelId": ch["instagram"], "schedulingType": "automatic",
            "mode": "customScheduled", "dueAt": due2, "assets": [{"image": {"url": u}} for u in urls["images"]],
            "metadata": {"instagram": {"type": "post", "shouldShareToFeed": True}}}))
if ch.get("tiktok"):   # added 17 Nov 2026: same Short to TikTok @ggeconomics
    jobs.append(("tiktok_video", {"text": text[:2200], "channelId": ch["tiktok"], "schedulingType": "automatic",
        "mode": "customScheduled", "dueAt": due, "assets": [{"video": {"url": urls["video"]}}],
        "metadata": {"tiktok": {"title": post["title"][:90], "isAiGenerated": not is_edit}}}))
if rebook: jobs = [j for j in jobs if j[0] == rebook] or sys.exit(f"no job named {rebook}")
if dry:
    print(json.dumps({"mode": mode, "dry": True, "due": due, "jobs": [j[0] for j in jobs] or "no Buffer channels configured yet"}, indent=1)); sys.exit(0)
if rebook == "youtube_short" and "--direct" in sys.argv:   # Buffer's YouTube cap (19 Nov incident): upload with our own token
    tokf = AP / "keys/youtube-token.json"
    if not tokf.exists(): sys.exit("--direct youtube_short needs keys/youtube-token.json")
    # 22 Nov: go through yt_upload.py so a re-post can never duplicate a title already on the channel, and is scheduled
    py = str(AP.parent / ".venv/bin/python") if (AP.parent / ".venv/bin/python").exists() else sys.executable
    r = subprocess.run([py, str(AP / "scripts/yt_upload.py"), D, urls["video"], due], capture_output=True, text=True)
    print((r.stdout + r.stderr).strip()[-400:])
    if r.returncode != 0: sys.exit(f"direct YouTube upload failed: {(r.stdout + r.stderr).strip()[-300:]}")
    vid = r.stdout.strip().splitlines()[-1]; st = {}
    b = json.load(open(Q / "buffer_ids.json"))
    b.setdefault("replaced", []).append({rebook: b["ids"].pop(rebook, None)}); b.setdefault("direct", {})[rebook] = vid
    (b.get("failed") or {}).pop(rebook, None)
    json.dump(b, open(Q / "buffer_ids.json", "w"), indent=1)
    print("posted direct", rebook, vid); sys.exit(0)
    sys.exit(0)
if rebook and "--direct" in sys.argv:                  # Buffer's Instagram link is down: post the Reel straight to Instagram (Graph API)
    if rebook != "instagram_reel": sys.exit("--direct supports instagram_reel and youtube_short")
    tok, uid = os.environ.get("IG_ACCESS_TOKEN"), os.environ.get("IG_USER_ID")
    if not (tok and uid):
        tok = _kc(["security", "find-generic-password", "-s", "ggeconomics-instagram", "-a", "ig_graph", "-w"],
                             capture_output=True, text=True).stdout.strip(); uid = cfg.get("instagram_user_id", "17841461684732203")
    if not tok: sys.exit("--direct needs IG_ACCESS_TOKEN")
    import urllib.parse, time
    G = "https://graph.facebook.com/v21.0/"
    def g(path, data=None):
        url = G + path + ("" if data else ("&" if "?" in path else "?") + "access_token=" + tok)
        body = urllib.parse.urlencode({**data, "access_token": tok}).encode() if data else None
        try: return json.loads(urllib.request.urlopen(urllib.request.Request(url, data=body), timeout=60).read())
        except urllib.error.HTTPError as e: sys.exit(f"Instagram Graph error: {e.read().decode()[:300]}")
    c = g(f"{uid}/media", {"media_type": "REELS", "video_url": urls["video"], "caption": text[:2200], "share_to_feed": "true"})["id"]
    for _ in range(40):
        st = g(f"{c}?fields=status_code,status")
        if st.get("status_code") == "FINISHED": break
        if st.get("status_code") in ("ERROR", "EXPIRED"): sys.exit(f"Instagram processing failed: {st.get('status')}")
        time.sleep(10)
    else: sys.exit("Instagram processing timed out")
    mid = g(f"{uid}/media_publish", {"creation_id": c})["id"]
    b = json.load(open(Q / "buffer_ids.json"))
    b.setdefault("replaced", []).append({rebook: b["ids"].pop(rebook, None)}); b.setdefault("direct", {})[rebook] = mid
    (b.get("failed") or {}).pop(rebook, None)
    json.dump(b, open(Q / "buffer_ids.json", "w"), indent=1); print("posted direct", rebook, mid); sys.exit(0)
if rebook:
    b = json.load(open(Q / "buffer_ids.json"))
    res = gql(MUT, {"i": jobs[0][1]})["createPost"]
    if res["__typename"] != "PostActionSuccess": sys.exit(f"Buffer rejected {rebook}: {res.get('message')}")
    b.setdefault("replaced", []).append({rebook: b["ids"].get(rebook)}); b["ids"][rebook] = res["post"]["id"]
    (b.get("failed") or {}).pop(rebook, None)
    json.dump(b, open(Q / "buffer_ids.json", "w"), indent=1); print("rebooked", rebook, res["post"]); sys.exit(0)
# 20 Nov: one rejected channel used to abort the whole post with no buffer_ids.json, and build.yml's "next pending post"
# step re-queued the same date every 12 min (28 rebuilds, ~350 Actions minutes). Now: book every channel that works,
# send a YouTube post Buffer refuses (its cap is 2/day) straight to YouTube, scheduled; record the rest as failed.
ids, direct, failed = {}, {}, {}
# 22 Nov: never book a second identical post (same channel, slot and text) — a re-run reuses the one already scheduled.
try:
    _ex = gql('query($o:OrganizationId!){ posts(input:{organizationId:$o, filter:{status:[scheduled]}}, first:100){ edges{ node{ id dueAt channelId text } } } }',
              {"o": cfg["buffer_organization_id"]})["posts"]["edges"]
    existing = {(e["node"]["channelId"], e["node"]["dueAt"][:16], (e["node"]["text"] or "")[:80]): e["node"]["id"] for e in _ex}
except (Exception, SystemExit) as e: existing = {}; print("Buffer duplicate check failed (continuing):", e)
for name, inp in jobs:
    # 23 Nov (Husain): YouTube is the priority channel. Upload it with our own token FIRST (scheduled for the slot), so it
    # never depends on Buffer's 2-a-day YouTube cap or its API quota. Buffer is only the fallback for YouTube.
    if name == "youtube_short" and (AP / "keys/youtube-token.json").exists():
        py = str(AP.parent / ".venv/bin/python") if (AP.parent / ".venv/bin/python").exists() else sys.executable
        r = subprocess.run([py, str(AP / "scripts/yt_upload.py"), D, urls["video"], inp["dueAt"]], capture_output=True, text=True)
        print((r.stdout + r.stderr).strip()[-400:])
        if r.returncode == 0: direct[name] = r.stdout.strip().splitlines()[-1]; continue
        print("direct YouTube upload failed, trying Buffer")
    k = (inp.get("channelId"), (inp.get("dueAt") or "")[:16], (inp.get("text") or "")[:80])
    if k in existing: ids[name] = existing[k]; print(f"{name}: already scheduled in Buffer as {existing[k]} (not booked again)"); continue
    try: res = gql(MUT, {"i": inp})["createPost"]
    except (Exception, SystemExit) as e: failed[name] = f"Buffer call failed: {e}"[:300]; print(failed[name]); continue
    if res["__typename"] == "PostActionSuccess": ids[name] = res["post"]["id"]; continue
    msg = res.get("message") or res["__typename"]; print(f"Buffer rejected {name}: {msg}")
    failed[name] = msg
if not ids and not direct:
    (Q / "publish_failed").write_text(json.dumps(failed, indent=1)); sys.exit(f"nothing booked: {failed}")
json.dump({"due": due, "ids": ids, "urls": urls, **({"direct": direct} if direct else {}), **({"failed": failed} if failed else {})},
          open(Q / "buffer_ids.json", "w"), indent=1)
print("scheduled", ids, "direct", direct, "failed", failed)
