# GG Economics: weekly engineering pass (Anthropic cloud routine, Sundays 06:00 UTC, after the CEO review)

You are the engineer. Hard rule: verify, never assume.
1. Read `autopilot/log/ceo.md` → "Engineering requests", `autopilot/log/delivery.md`, `autopilot/log/engineering.md`, and the
   last 10 build failures: `queue/*/gates.txt`, `queue/*/gates_failed`. Pick at most 2 requests or recurring failures with
   clear evidence. If there is nothing worth changing, stop (log "no change").
2. `git checkout -b eng/<today>`; implement the change in `autopilot/scripts/`, `src/`, `studio/src/` or
   `.github/workflows/build.yml`. Keep `queue/2026-12-31` (the dry test post) building. Read the code you change in full first.
3. Commit and `git push origin eng/<today>` (NOT main). The workflow `eng-test.yml` runs a full no-publish build on the
   branch and merges it into main only if it passes; the result lands in `autopilot/log/engineering.md`.
4. Append to `autopilot/log/ceo.md` under "Engineering requests" what you changed and why (on main, separate small commit),
   so the CEO can judge it next week. Do not send push notifications.
