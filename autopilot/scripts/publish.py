#!/usr/bin/env python3
"""publish.py <date> [--dry] | publish.py <date> --rebook <channel_job> [--direct]
--direct (instagram_reel only): skip Buffer and post the Reel through the Instagram Graph API (IG_ACCESS_TOKEN, IG_USER_ID).
--rebook: re-create ONE failed Buffer post (e.g. instagram_reel after a channel reconnect) from the media already hosted,
due in 5 min; the old id moves to buffer_ids.json "replaced". Used by monitor.py.
Hosts queue/<date>/short.mp4 (+ carousel PNGs) in the public media repo, then schedules them in Buffer:
YouTube Short + Instagram Reel + TikTok (+ Instagram carousel on carousel days). Writes queue/<date>/buffer_ids.json.
Never runs twice for the same date (buffer_ids.json guard). Key: macOS keychain (config.json → buffer_key_keychain)."""
import sys, json, os, subprocess, shutil, urllib.request
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
    return subprocess.run(["security", "find-generic-password", "-s", k["service"], "-a", k["account"], "-w"],
                          capture_output=True, text=True).stdout.strip()
def gql(q, v):
    req = urllib.request.Request("https://api.buffer.com", data=json.dumps({"query": q, "variables": v}).encode(),
          headers={"Content-Type": "application/json", "Authorization": "Bearer " + key()}, method="POST")
    body = json.loads(urllib.request.urlopen(req, timeout=60).read())
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
        jobs.append(("instagram_carousel", {"text": text[:2200], "channelId": ch["instagram"], "schedulingType": "automatic",
            "mode": "customScheduled", "dueAt": due2, "assets": [{"image": {"url": u}} for u in urls["images"]],
            "metadata": {"instagram": {"type": "post", "shouldShareToFeed": True}}}))
if ch.get("tiktok"):   # added 17 Nov 2026: same Short to TikTok @ggeconomics
    jobs.append(("tiktok_video", {"text": text[:2200], "channelId": ch["tiktok"], "schedulingType": "automatic",
        "mode": "customScheduled", "dueAt": due, "assets": [{"video": {"url": urls["video"]}}],
        "metadata": {"tiktok": {"title": post["title"][:90], "isAiGenerated": not is_edit}}}))
if rebook: jobs = [j for j in jobs if j[0] == rebook] or sys.exit(f"no job named {rebook}")
if dry:
    print(json.dumps({"mode": mode, "dry": True, "due": due, "jobs": [j[0] for j in jobs] or "no Buffer channels configured yet"}, indent=1)); sys.exit(0)
if rebook and "--direct" in sys.argv:                  # Buffer's Instagram link is down: post the Reel straight to Instagram (Graph API)
    if rebook != "instagram_reel": sys.exit("--direct only supports instagram_reel")
    tok, uid = os.environ.get("IG_ACCESS_TOKEN"), os.environ.get("IG_USER_ID")
    if not (tok and uid):
        tok = subprocess.run(["security", "find-generic-password", "-s", "ggeconomics-instagram", "-a", "ig_graph", "-w"],
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
    json.dump(b, open(Q / "buffer_ids.json", "w"), indent=1); print("posted direct", rebook, mid); sys.exit(0)
if rebook:
    b = json.load(open(Q / "buffer_ids.json"))
    res = gql(MUT, {"i": jobs[0][1]})["createPost"]
    if res["__typename"] != "PostActionSuccess": sys.exit(f"Buffer rejected {rebook}: {res.get('message')}")
    b.setdefault("replaced", []).append({rebook: b["ids"].get(rebook)}); b["ids"][rebook] = res["post"]["id"]
    json.dump(b, open(Q / "buffer_ids.json", "w"), indent=1); print("rebooked", rebook, res["post"]); sys.exit(0)
ids = {}
for name, inp in jobs:
    res = gql(MUT, {"i": inp})["createPost"]
    if res["__typename"] != "PostActionSuccess": sys.exit(f"Buffer rejected {name}: {res.get('message')}")
    ids[name] = res["post"]["id"]
json.dump({"due": due, "ids": ids, "urls": urls}, open(Q / "buffer_ids.json", "w"), indent=1)
print("scheduled", ids)
