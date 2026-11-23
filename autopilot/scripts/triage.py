#!/usr/bin/env python3
"""triage.py <run_id> — called by triage.yml after ANY workflow run finishes.
Failure: read the failed log, classify it, retry once if transient, else open an entry in log/failures.json
for the fixer routine (FIXER.md, every 2 h). Success on a retry/rebuild: close the matching open entry.
No human has to report a failure: this is the record."""
import json, os, re, subprocess, sys, datetime
from pathlib import Path
R = Path(__file__).resolve().parents[2]; F = R / "autopilot/log/failures.json"
rid = sys.argv[1]; DRY = "--dry" in sys.argv   # --dry: classify only (tests)
gh = lambda *a: subprocess.run(["gh", *a], capture_output=True, text=True).stdout
run = json.loads(gh("run", "view", rid, "--json", "name,conclusion,attempt,event,headBranch,displayTitle,createdAt,url,workflowName"))
db = json.loads(F.read_text()) if F.exists() else []
now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
wf = run["workflowName"]

if run["conclusion"] == "success":
    live = [e for e in db if e["status"] != "resolved" and e["workflow"] == wf]
    if not live: sys.exit(0)
    full = gh("run", "view", rid, "--log")
    done = re.search(r"target: (\S+)", full)
    for e in live:   # a later green run of the same workflow + target closes it (retry, rebuild, or the fixer's own run)
        if not e.get("target") or (done and done.group(1) == e["target"]) or f"queue/{e['target']}/" in full and "scheduled" in full:
            e.update(status="resolved", resolved=now, resolved_by=run["url"])
    F.write_text(json.dumps(db, indent=1)); sys.exit(0)
if run["conclusion"] != "failure": sys.exit(0)

log = gh("run", "view", rid, "--log-failed")
lines = [re.sub(r"^\ufeff?\d{4}-\d\d-\d\dT[\d:.]+Z ?", "", l.split("\t")[-1]) for l in log.splitlines()]
lines = [l for l in lines if l.strip() and "\x1b[36;1m" not in l and not l.startswith(("##[group]", "##[endgroup]", "  "))]
cut = next((i for i, l in enumerate(lines) if "##[error]" in l), len(lines) - 1); lines = lines[:cut + 1]   # the failing step, not the post-job cleanup
tb = next((i for i in range(len(lines) - 1, -1, -1) if lines[i].startswith("Traceback")), None)
err = lines[tb:] if tb is not None else [l for l in lines if re.search(r"error|fail|exception|exit|rejected|denied|no trailer|gates", l, re.I)]
tail = "\n".join((err[-25:] or lines[-25:]))[-3000:]
m = re.search(r"target: (\d{4}-\d{2}-\d{2}\w?)", log) or re.search(r"queue/(\d{4}-\d{2}-\d{2}\w?)", log)
target = m.group(1) if m else ""
TRANSIENT = r"Could not resolve host|Connection (reset|refused|timed out)|timed? ?out|HTTP Error 5\d\d|\b50[234]\b|Internal Server Error|rate.?limit|429|ECONNRESET|Temporary failure|TLS|fetch first|\[rejected\]|non-fast-forward|Unable to connect|apt-get.*(Failed|Hash Sum)|RemoteDisconnected|IncompleteRead"
OWNER = r"payments have failed|spending limit|billing|isDisconnected|re-?authori[sz]e|invalid_grant|token (has )?expired"
kind = "owner" if re.search(OWNER, log, re.I) else "transient" if re.search(TRANSIENT, tail, re.I) else "code"
if wf == "GG Economics engineering gate": kind = "gate"   # the gate rejecting a branch is the gate working; the fixer reads it

e = next((x for x in db if x["status"] != "resolved" and x["workflow"] == wf and x.get("target") == target), None)
if not e:
    e = {"id": rid, "workflow": wf, "target": target, "opened": now, "status": "open", "kind": kind, "runs": []}
    db.append(e)
e["runs"].append({"run": run["url"], "attempt": run["attempt"], "at": now, "error": tail})
e["kind"] = kind
if kind == "transient" and run["attempt"] < 2:
    DRY or subprocess.run(["gh", "run", "rerun", rid, "--failed"]); e["status"] = "retrying"
elif kind == "gate":
    e["status"] = "open"
else:
    e["status"] = "open"
    if kind == "owner" and not e.get("notified") and not DRY:
        subprocess.run([sys.executable, str(R / "autopilot/scripts/notify.py"), f"Needs you: {wf} {target} — {tail.splitlines()[-1][:180] if tail else ''}", "high"])
        e["notified"] = now
fails = [r for r in e["runs"] if r["at"][:10] >= now[:10]]
q = R / "autopilot/queue" / target
if target and len(fails) >= 3 and q.is_dir() and not (q / "buffer_ids.json").exists():   # circuit breaker: 22 Nov looped 55x
    DRY or (q / "gates_failed").touch(); e["halted"] = now; e["kind"] = "loop"
F.write_text(json.dumps(db, indent=1))
print(json.dumps({k: e[k] for k in ("workflow", "target", "kind", "status")}))
