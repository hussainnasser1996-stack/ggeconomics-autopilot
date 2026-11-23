#!/usr/bin/env python3
"""monitor.py — operations check (GitHub Actions, every 6 h). Verifies, never assumes:
1. Every booked post in the last 5 days: its real Buffer status (scheduled / sent / error) + the live link once sent.
2. Every post the brain wrote for today..+3 that is NOT booked: retries the build once (gates_failed → retry), else flags it.
3. Channel health: a Buffer channel that lost its login (isDisconnected) is a problem with the exact fix for Husain;
   once it is reconnected, posts that errored on it in the last 12 h are re-booked by themselves (publish.py --rebook).
4. Writes autopilot/log/delivery.md (the CEO review and the brain read it). Exit 0 always; problems go in the file."""
import json, os, subprocess, urllib.request, urllib.error, datetime, time
from pathlib import Path
AP = Path(__file__).resolve().parents[1]; Qd = AP / "queue"
now = datetime.datetime.now(datetime.timezone.utc); today = now.date()
def gql(q, v):
    req = urllib.request.Request("https://api.buffer.com", data=json.dumps({"query": q, "variables": v}).encode(),
          headers={"Content-Type": "application/json", "Authorization": "Bearer " + os.environ["BUFFER_API_KEY"]})
    for i in range(5):   # 23 Nov: Buffer answered 429 for most posts and the monitor went blind; back off and retry
        try: return json.loads(urllib.request.urlopen(req, timeout=60).read())
        except urllib.error.HTTPError as e:
            if e.code != 429 or i == 4: raise
            time.sleep(min(60, int(e.headers.get("Retry-After") or 0) or 3 * 2 ** i))
# Posts already SENT never change: cache them so the monitor only asks Buffer about posts still in play.
FIN = AP / "log/buffer_final.json"; final = json.loads(FIN.read_text()) if FIN.exists() else {}
Q = 'query($i:PostId!){ post(input:{id:$i}){ status dueAt sentAt externalLink error { message } } }'
rows, problems, actions = [], [], []
# 23 Nov (Husain): priority YouTube > Instagram > TikTok. A missed post is retried this many hours after its slot.
RETRY_H = {"youtube_short": 48, "instagram_reel": 24, "instagram_carousel": 24, "tiktok_video": 12}
SERVICE = {"youtube_short": "youtube", "instagram_reel": "instagram", "instagram_carousel": "instagram", "tiktok_video": "tiktok"}
cfg = json.load(open(AP / "config.json"))
try:
    chans = gql('query($o:OrganizationId!){ channels(input:{organizationId:$o}){ service isDisconnected isLocked isQueuePaused } }',
                {"o": cfg["buffer_organization_id"]})["data"]["channels"]
    down = {c["service"] for c in chans if c["isDisconnected"] or c["isLocked"] or c["isQueuePaused"]}
except Exception as e: chans, down = [], set(); problems.append(f"Buffer channel check failed: {e}")
for c in chans:
    if c["service"] in down:
        problems.append(f"Buffer {c['service']} channel is DISCONNECTED/locked/paused: every {c['service']} post will fail. FIX (Husain, 1 min): "
                        f"buffer.com → Channels → {c['service']} → Refresh connection. Failed posts from the last 12 h re-book themselves after.")
busy = subprocess.run(["gh", "run", "list", "-R", os.environ["GITHUB_REPOSITORY"], "--workflow", "build.yml", "--json", "status",
                       "-q", '[.[]|select(.status!="completed")]|length'], capture_output=True, text=True).stdout.strip() not in ("", "0")
for q in sorted(Qd.iterdir()):
    d = q.name[:10]
    try: day = datetime.date.fromisoformat(d)
    except ValueError: continue
    if (q / "dry").exists() or not (today - datetime.timedelta(days=5) <= day <= today + datetime.timedelta(days=3)): continue
    title = json.load(open(q / "post.json"))["title"] if (q / "post.json").exists() else "?"
    if (q / "buffer_ids.json").exists():
        bj = json.load(open(q / "buffer_ids.json"))
        for name, vid in (bj.get("direct") or {}).items():
            link = f"https://www.youtube.com/shorts/{vid}" if name == "youtube_short" else vid
            rows.append(f"| {q.name} | {name} | direct (own API) | {bj.get('due', '')} | {link} | {title[:50]} |")
        for name, msg in list((bj.get("failed") or {}).items()):
            # 22 Nov: a YouTube Short refused at publish time (Buffer 2/day cap + YouTube upload cap) is retried directly
            # while it is still within 6 h of its slot; after that it is dropped so Shorts don't bunch up late in the day.
            try: due_f = datetime.datetime.fromisoformat(bj.get("due", "").replace("Z", "+00:00"))
            except Exception: due_f = None
            if (name == "youtube_short" and due_f and not (bj.get("direct") or {}).get(name)
                    and now - due_f <= datetime.timedelta(hours=RETRY_H[name]) and (AP / "keys/youtube-token.json").exists()):
                r = subprocess.run(["python3", str(AP / "scripts/publish.py"), q.name, "--rebook", name, "--direct"], capture_output=True, text=True)
                (actions if r.returncode == 0 else problems).append(f"{q.name} {name}: retried direct YouTube upload: {(r.stdout + r.stderr).strip()[-200:]}")
                if r.returncode == 0: continue
            if name != "youtube_short" and due_f and now - due_f <= datetime.timedelta(hours=RETRY_H.get(name, 12)):
                # 23 Nov: Instagram/TikTok refused at publish time (Buffer quota/outage): book again; Instagram past its slot → direct.
                late = now > due_f - datetime.timedelta(minutes=10)   # Buffer only takes future times; a late Reel goes direct
                if not late or name == "instagram_reel":
                    cmd = ["python3", str(AP / "scripts/publish.py"), q.name, "--rebook", name] + (["--direct"] if late and name == "instagram_reel" else [])
                    r = subprocess.run(cmd, capture_output=True, text=True)
                    (actions if r.returncode == 0 else problems).append(f"{q.name} {name}: re-booked after publish-time failure: {(r.stdout + r.stderr).strip()[-200:]}")
                    if r.returncode == 0: continue
            problems.append(f"{q.name} {name}: not booked at publish time: {msg}")
        for name, pid in bj["ids"].items():
            if pid in final: p = final[pid]
            else:
                try: p = gql(Q, {"i": pid})["data"]["post"] or {}; time.sleep(0.4)
                except Exception as e: p = {"status": f"query failed: {e}"}
                if p.get("status") == "sent": final[pid] = p
                elif str(p.get("status", "")).startswith("query failed"): problems.append(f"{q.name} {name}: Buffer status unknown ({p['status'][:80]})")
            st = p.get("status"); err = (p.get("error") or {}).get("message")
            rows.append(f"| {q.name} | {name} | {st} | {p.get('sentAt') or p.get('dueAt') or ''} | {p.get('externalLink') or ''} | {title[:50]} |")
            if err or st in ("error", "failed"):
                due_t = datetime.datetime.fromisoformat((p.get("dueAt") or now.isoformat()).replace("Z", "+00:00"))
                if (name == "youtube_short" and (AP / "keys/youtube-token.json").exists()
                        and now - due_t <= datetime.timedelta(hours=RETRY_H[name])):   # ANY Buffer YouTube failure → our own upload
                    # Buffer caps YouTube posts (19 Nov incident): upload the Short ourselves instead of losing the slot.
                    r = subprocess.run(["python3", str(AP / "scripts/publish.py"), q.name, "--rebook", name, "--direct"], capture_output=True, text=True)
                    (actions if r.returncode == 0 else problems).append(f"{q.name} {name}: Buffer posting limit → direct YouTube upload: {(r.stdout + r.stderr).strip()[-200:]}")
                elif (name == "instagram_reel" and os.environ.get("IG_ACCESS_TOKEN") and (SERVICE.get(name) in down or (err and "limit" in err.lower()))
                      and now - due_t <= datetime.timedelta(hours=RETRY_H[name])):
                    # Buffer lost Instagram (18 Nov): don't wait for the owner, post the Reel straight through the Graph API.
                    r = subprocess.run(["python3", str(AP / "scripts/publish.py"), q.name, "--rebook", name, "--direct"], capture_output=True, text=True)
                    (actions if r.returncode == 0 else problems).append(f"{q.name} {name}: Buffer IG down → direct post: {(r.stdout + r.stderr).strip()[-200:]}")
                elif err and "limit" in err.lower():
                    # Platform/Buffer posting cap: a re-book would spend the reduced daily allowance and starve later slots.
                    problems.append(f"{q.name} {name}: Buffer posting limit hit, not re-booked: {err}")
                elif SERVICE.get(name) in down or now - due_t > datetime.timedelta(hours=RETRY_H.get(name, 12)):
                    problems.append(f"{q.name} {name}: Buffer error: {err}" + ("" if SERVICE.get(name) in down else f" (older than {RETRY_H.get(name, 12)} h: not re-booked, stale)"))
                else:
                    r = subprocess.run(["python3", str(AP / "scripts/publish.py"), q.name, "--rebook", name], capture_output=True, text=True)
                    (actions if r.returncode == 0 else problems).append(f"{q.name} {name}: errored ({err}) → re-book: {(r.stdout + r.stderr).strip()[-200:]}")
            due = p.get("dueAt")
            if st == "scheduled" and due and datetime.datetime.fromisoformat(due.replace("Z", "+00:00")) < now - datetime.timedelta(hours=1):
                problems.append(f"{q.name} {name}: still 'scheduled' >1 h after due time")
    elif (q / "publish_failed").exists():
        problems.append(f"{q.name}: built but NO channel accepted it: {(q / 'publish_failed').read_text().strip()[:300]}")
    elif (q / "script.json").exists() and busy:
        actions.append(f"{q.name}: not booked yet, a build is running/queued → checked again next run")
    elif (q / "script.json").exists():
        tries = int((q / "retries").read_text()) if (q / "retries").exists() else 0
        if tries < 1:
            (q / "retries").write_text(str(tries + 1)); (q / "gates_failed").unlink(missing_ok=True)
            subprocess.run(["gh", "workflow", "run", "build.yml", "-R", os.environ["GITHUB_REPOSITORY"], "-f", f"date={q.name}"])
            actions.append(f"{q.name}: not booked → build re-dispatched (retry 1)")
        else:
            problems.append(f"{q.name}: NOT BOOKED after a retry ({'gates failed: ' + (q / 'gates.txt').read_text().strip() if (q / 'gates.txt').exists() else 'build failed'})")
for d in [today + datetime.timedelta(days=i) for i in range(0, 2)]:
    if not (Qd / d.isoformat() / "script.json").exists() and now.hour >= 2 and d == today:
        problems.append(f"{d}: the brain wrote nothing for today (routine did not run or stopped)")
sent_yt = []
for r in rows:
    c = [x.strip() for x in r.strip("|").split("|")]
    if c[1] == "youtube_short" and c[2] in ("sent", "direct (own API)") and c[4]: sent_yt.append({"queue": c[0], "link": c[4]})
if sent_yt and (AP / "keys/youtube-token.json").exists():
    py = str(AP.parent / ".venv/bin/python") if (AP.parent / ".venv/bin/python").exists() else "python3"
    r = subprocess.run([py, str(AP / "scripts/yt_after.py")], input=json.dumps(sent_yt), capture_output=True, text=True)
    actions += [l for l in (r.stdout + r.stderr[-300:]).splitlines() if l.strip() and "nothing new" not in l]
# Buffer free plan caps scheduled posts per channel (~10): count what's queued per channel and warn early
from collections import Counter
queued = Counter(r.split("|")[2].strip() for r in rows if r.split("|")[3].strip() == "scheduled")
for ch_name, n in queued.items():
    if n >= 8: problems.append(f"Buffer queue for {ch_name}: {n} scheduled (free plan cap ~10) — brain must not book further ahead")
# GitHub Actions minutes this month (repo is PUBLIC: standard runners are free and unmetered; kept for information): sum of job durations, rounded up per job
mins = 0
try:
    month = now.strftime("%Y-%m")
    runs = json.loads(subprocess.run(["gh", "run", "list", "-R", os.environ["GITHUB_REPOSITORY"], "--limit", "300", "--json",
                      "createdAt,startedAt,updatedAt,status"], capture_output=True, text=True).stdout or "[]")
    for r in runs:
        if r["createdAt"].startswith(month) and r["status"] == "completed" and r.get("startedAt"):
            a = datetime.datetime.fromisoformat(r["startedAt"].replace("Z", "+00:00")); b = datetime.datetime.fromisoformat(r["updatedAt"].replace("Z", "+00:00"))
            mins += max(1, -(-int((b - a).total_seconds()) // 60))
    days_left = (datetime.date(today.year + (today.month == 12), today.month % 12 + 1, 1) - today).days
    public = subprocess.run(["gh", "repo", "view", os.environ["GITHUB_REPOSITORY"], "--json", "visibility", "-q", ".visibility"],
                            capture_output=True, text=True).stdout.strip() == "PUBLIC"   # 20 Nov: repo made public = unlimited minutes
    if mins > 1700 and not public: problems.append(f"GitHub Actions minutes this month ≈ {mins}/2000: CEO must lower posts_per_day")
except Exception as e: mins = f"unknown ({e})"
# 23 Nov: a post dated before yesterday is past the 12 h re-book window, but it stayed in Problems and fired a HIGH alert every 6 h
# (18b IG, 22c YT). Keep it on record under "Old", out of Problems and out of the alert.
import re as _re
_cut = (now - __import__("datetime").timedelta(days=1)).strftime("%Y-%m-%d")
_old = [p for p in problems if (m := _re.match(r"(\d{4}-\d{2}-\d{2})", p)) and m.group(1) < _cut]
problems = [p for p in problems if p not in _old]
out = [f"# Delivery check · {now:%Y-%m-%d %H:%M} UTC", "", "## Problems", *(["- " + p for p in problems] or ["- none"]),
       "", "## Old (before yesterday, past the re-book window, no alert)", *(["- " + p for p in _old] or ["- none"]),
       "", "Buffer scheduled per channel: " + (", ".join(f"{k} {v}" for k, v in queued.items()) or "0"),
       "", f"GitHub Actions minutes used this month: ~{mins} (public repo: free, no cap)",
       "", "## Actions taken", *(["- " + a for a in actions] or ["- none"]), "",
       "| post | channel | status | sent/due | link | title |", "|---|---|---|---|---|---|", *rows, ""]
FIN.write_text(json.dumps(final, indent=1))
(AP / "log/delivery.md").write_text("\n".join(out)); print("\n".join(out[:12]))
if problems: subprocess.run(["python3", str(AP / "scripts/notify.py"), f"GG Economics: {len(problems)} delivery problem(s), see log/delivery.md", "high"])
