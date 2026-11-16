#!/usr/bin/env python3
"""monitor.py — operations check (GitHub Actions, every 6 h). Verifies, never assumes:
1. Every booked post in the last 5 days: its real Buffer status (scheduled / sent / error) + the live link once sent.
2. Every post the brain wrote for today..+3 that is NOT booked: retries the build once (gates_failed → retry), else flags it.
3. Writes autopilot/log/delivery.md (the CEO review and the brain read it). Exit 0 always; problems go in the file."""
import json, os, subprocess, urllib.request, datetime
from pathlib import Path
AP = Path(__file__).resolve().parents[1]; Qd = AP / "queue"
now = datetime.datetime.now(datetime.timezone.utc); today = now.date()
def gql(q, v):
    req = urllib.request.Request("https://api.buffer.com", data=json.dumps({"query": q, "variables": v}).encode(),
          headers={"Content-Type": "application/json", "Authorization": "Bearer " + os.environ["BUFFER_API_KEY"]})
    return json.loads(urllib.request.urlopen(req, timeout=60).read())
Q = 'query($i:PostId!){ post(input:{id:$i}){ status dueAt sentAt externalLink error { message } } }'
rows, problems, actions = [], [], []
busy = subprocess.run(["gh", "run", "list", "-R", os.environ["GITHUB_REPOSITORY"], "--workflow", "build.yml", "--json", "status",
                       "-q", '[.[]|select(.status!="completed")]|length'], capture_output=True, text=True).stdout.strip() not in ("", "0")
for q in sorted(Qd.iterdir()):
    d = q.name[:10]
    try: day = datetime.date.fromisoformat(d)
    except ValueError: continue
    if (q / "dry").exists() or not (today - datetime.timedelta(days=5) <= day <= today + datetime.timedelta(days=3)): continue
    title = json.load(open(q / "post.json"))["title"] if (q / "post.json").exists() else "?"
    if (q / "buffer_ids.json").exists():
        for name, pid in json.load(open(q / "buffer_ids.json"))["ids"].items():
            try: p = gql(Q, {"i": pid})["data"]["post"] or {}
            except Exception as e: p = {"status": f"query failed: {e}"}
            st = p.get("status"); err = (p.get("error") or {}).get("message")
            rows.append(f"| {q.name} | {name} | {st} | {p.get('sentAt') or p.get('dueAt') or ''} | {p.get('externalLink') or ''} | {title[:50]} |")
            if err or st in ("error", "failed"): problems.append(f"{q.name} {name}: Buffer error: {err}")
            due = p.get("dueAt")
            if st == "scheduled" and due and datetime.datetime.fromisoformat(due.replace("Z", "+00:00")) < now - datetime.timedelta(hours=1):
                problems.append(f"{q.name} {name}: still 'scheduled' >1 h after due time")
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
    if c[1] == "youtube_short" and c[2] == "sent" and c[4]: sent_yt.append({"queue": c[0], "link": c[4]})
if sent_yt and (AP / "keys/youtube-token.json").exists():
    py = str(AP.parent / ".venv/bin/python") if (AP.parent / ".venv/bin/python").exists() else "python3"
    r = subprocess.run([py, str(AP / "scripts/yt_after.py")], input=json.dumps(sent_yt), capture_output=True, text=True)
    actions += [l for l in (r.stdout + r.stderr[-300:]).splitlines() if l.strip() and "nothing new" not in l]
out = [f"# Delivery check · {now:%Y-%m-%d %H:%M} UTC", "", "## Problems", *(["- " + p for p in problems] or ["- none"]),
       "", "## Actions taken", *(["- " + a for a in actions] or ["- none"]), "",
       "| post | channel | status | sent/due | link | title |", "|---|---|---|---|---|---|", *rows, ""]
(AP / "log/delivery.md").write_text("\n".join(out)); print("\n".join(out[:12]))
if problems: subprocess.run(["python3", str(AP / "scripts/notify.py"), f"GG Economics: {len(problems)} delivery problem(s), see log/delivery.md", "high"])
