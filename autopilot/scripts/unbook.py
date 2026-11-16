#!/usr/bin/env python3
"""unbook.py <queue-name> [...]  — take booked posts back out of Buffer so they can be fixed and rebuilt.
Deletes each still-scheduled Buffer post in queue/<name>/buffer_ids.json, then removes buffer_ids.json, gates_failed and
the auto-picked clips (so autopick runs again). Refuses posts that already went out. Used by .github/workflows/rebuild.yml."""
import sys, json, os, urllib.request
from pathlib import Path
AP = Path(__file__).resolve().parents[1]
def gql(q, v):
    req = urllib.request.Request("https://api.buffer.com", data=json.dumps({"query": q, "variables": v}).encode(),
          headers={"Content-Type": "application/json", "Authorization": "Bearer " + os.environ["BUFFER_API_KEY"]}, method="POST")
    return json.loads(urllib.request.urlopen(req, timeout=60).read())
for name in sys.argv[1:]:
    q = AP / "queue" / name; b = q / "buffer_ids.json"
    if b.exists():
        ids = json.load(open(b))["ids"]
        for ch, pid in ids.items():
            st = gql("query($i:PostId!){ post(input:{id:$i}){ id status } }", {"i": pid})
            status = ((st.get("data") or {}).get("post") or {}).get("status")
            if status == "sent": sys.exit(f"{name}: {ch} already published, not touching it")
            r = gql("mutation($i: DeletePostInput!){ deletePost(input:$i){ __typename ... on MutationError { message } } }", {"i": {"id": pid}})
            print(name, ch, pid, status, "->", json.dumps(r.get("data") or r.get("errors"))[:200])
        b.unlink()
    (q / "gates_failed").unlink(missing_ok=True)
    sp = q / "spec.json"
    if sp.exists():
        s = json.load(open(sp)); s["spec"]["clips"] = []; json.dump(s, open(sp, "w"), indent=1)
    print(name, "unbooked")
