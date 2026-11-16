# GG Economics autopilot (runs in the cloud, no Mac)

One Short a day on YouTube Shorts + Instagram Reels (@ggeconomics), plus an Instagram carousel Mon/Wed/Fri.
Gaming news told through the money. Strategy: `autopilot/STRATEGY.md`. Switches: `autopilot/CONTROL.md`.

## How a day runs

| UTC | Where | What |
|---|---|---|
| 00:15 | **Anthropic cloud routine** "GG Economics daily brain" (`trig_012CubYQ8spUB3BSjDANQiJE`, environment *LinkedIn Autopilot* because it has open web access) | Reads yesterday's analytics, picks + verifies the story, writes `autopilot/queue/<D>/{script,spec,post,footage,carousel}.json`, pushes to `main`. Instructions: `autopilot/BRAIN.md`. |
| on that push | **GitHub Actions** `build.yml` | Downloads the trailer (Steam store or the `footage-library` release; YouTube blocks cloud runners), Kokoro voice + Whisper check, auto-picks clips (OCR rejects title/logo cards), renders in Remotion, renders the carousel, runs the gates, hosts media in `savestate-media`, books it in Buffer, logs `history.md`, refreshes analytics, commits state. ~15 min. |
| 04:00 / 12:00 / 19:00 | GitHub Actions (safety net) | Builds anything the brain wrote for today/tomorrow that is still unscheduled. |
| 12:00 / 16:00 / 23:00 (+15:00 carousel) | Buffer | Publishes 2–3 Shorts/day (`posts_per_day` in CONTROL.md). 23:00 UTC = 6 PM New York. |
| every 6 h | GitHub Actions `monitor.yml` | Real Buffer status of every post, re-builds anything unbooked once, files published Shorts into series playlists, tracks Actions minutes → `log/delivery.md`; phone alert only on unresolved problems. |
| Sun 03:00 | Anthropic routine "weekly CEO review" (`trig_01GUBK7jxKYzWgeN72KJSCQD`) | Evidence-based review + market research (may use sub-agents) → edits strategy/format mix/cadence/topics → `log/ceo.md`. Instructions: `autopilot/CEO.md`. |
| Sun 06:00 | Anthropic routine "weekly engineering pass" (`trig_01DhHpmt4FD9hgcSFEAUBJsC`) | Fixes recurring failures / CEO requests on a branch `eng/<date>`; `eng-test.yml` dry-builds it and merges only if it passes → `log/engineering.md`. |

Gates (`autopilot/scripts/gates.py`): voice heard back ≥ 80% word match, overlays clear of the Shorts/Reels UI,
contrast + caption legibility, 15–40 s. A failed gate leaves `queue/<D>/gates_failed` and does not publish.

## Operate
- Pause everything: set `mode: paused` in `autopilot/CONTROL.md`. Skip a day: add it to `skip_dates`.
- Re-run a day's build: Actions → *GG Economics build + publish* → Run workflow → date.
- Test without publishing: same, with **dry** ticked (or put an empty `dry` file in the queue folder).
- Brain routine: https://claude.ai/code/routines/trig_012CubYQ8spUB3BSjDANQiJE

## Secrets (GitHub → Settings → Secrets)
`BUFFER_API_KEY`, `YT_TOKEN_JSON` (YouTube Analytics, production OAuth app, does not expire), `MEDIA_DEPLOY_KEY`
(write deploy key on `savestate-media`). The brain needs no secrets: it runs on the Claude subscription.

The Mac version (`Motion Studio/experiments/game-news/autopilot`, launchd) is retired as of 16 Nov 2026.
