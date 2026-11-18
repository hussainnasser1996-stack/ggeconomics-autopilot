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
        # check EVERY post first, delete nothing until all are known (18 Nov: the carousel goes out ~8 h before the
        # video, so a mixed record used to get half-deleted before the "already sent" stop)
        stat = {}
        for ch, pid in ids.items():
            st = gql("query($i:PostId!){ post(input:{id:$i}){ id status } }", {"i": pid})
            stat[ch] = ((st.get("data") or {}).get("post") or {}).get("status")
        sent = [ch for ch, s in stat.items() if s == "sent"]
        if any(ch != "instagram_carousel" for ch in sent): sys.exit(f"{name}: {sent} already published, not touching anything")
        if "instagram_carousel" in sent:
            (q / "carousel_sent").write_text(ids["instagram_carousel"]); print(name, "carousel already out: kept, won't re-book")
        for ch, pid in ids.items():
            status = stat[ch]
            if status == "sent": continue
            r = gql("mutation($i: DeletePostInput!){ deletePost(input:$i){ __typename ... on MutationError { message } } }", {"i": {"id": pid}})
            print(name, ch, pid, status, "->", json.dumps(r.get("data") or r.get("errors"))[:200])
        b.unlink()
    for f in ("gates_failed", "music.json"): (q / f).unlink(missing_ok=True)   # music re-picked on the rebuild runner
    sp = q / "spec.json"
    if sp.exists():
        s = json.load(open(sp)); s["spec"]["clips"] = []; json.dump(s, open(sp, "w"), indent=1)
    up = AP / "log/used_shots.json"            # the shots it used are free again for its own rebuild
    if up.exists():
        u = json.load(open(up)); u.pop(name, None); json.dump(u, open(up, "w"), indent=1)
    print(name, "unbooked")
