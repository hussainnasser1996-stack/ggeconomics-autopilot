# GG Economics: failure fixer (Anthropic cloud routine, every 2 h)

Every failed GitHub run is classified by `.github/workflows/triage.yml` → `autopilot/log/failures.json`. Your job: make
each open entry green WITHOUT Husain having to report it. Hard rule: verify, never assume. $0 only. Money/accounts = Husain.
1. `git pull`. Read `autopilot/log/failures.json`. Entries with status `open` (or `retrying` older than 1 h). None → log
   one line "<UTC> no open failures" to `autopilot/log/fixer.md`, push, STOP. (Most runs end here.)
2. For each open entry (oldest first, max 3 per run): read `runs[-1].error`; get the full log with
   `gh run view <id from runs[].run> --log-failed` if you need it. Find the ROOT CAUSE in the code / queue files. Same cause
   as an entry fixed before (`autopilot/log/fixer.md`)? Then the earlier fix was incomplete: fix it properly this time.
3. Fix by kind:
   - `code` / `loop`: change code on a branch `eng/<UTC date>-fix-<short>` and push it (never to main). `eng-test.yml` dry-builds
     12-31 + 12-31c and merges only if green. Then re-run the affected post: delete `queue/<target>/gates_failed`, commit
     to main, and `gh workflow run build.yml -f date=<target>` (or `rebuild.yml` if it was booked). If the post's slot has
     already passed by more than 12 h, don't rebuild: mark `status: "stale"` with a reason.
   - `transient` that failed twice: re-run once more; if it fails again treat it as `code`.
   - `owner` (billing, lost login, token): you can't fix it. Make sure Husain got ONE alert (`notified` set), state the exact
     click he needs in `fixer.md`, set `status: "owner"`.
   - `gate`: an eng branch was rejected. Read why; fix the branch or abandon it and note it.
4. Set the entry `status: "fixing"` + `fix: "<what you changed, branch/commit>"` and push. triage.yml closes it
   (`resolved`) when the next run of that workflow for that target goes green; check it did on your next run.
5. Append to `autopilot/log/fixer.md`: time, entry, cause, fix, result. Push. Never post or delete on YouTube/IG/TikTok
   yourself beyond what build/monitor/rebuild already do. If the same entry is still open after 3 of your attempts,
   send ONE high push (`python3 autopilot/scripts/notify.py "<what's stuck and why>" high`) and keep trying.
