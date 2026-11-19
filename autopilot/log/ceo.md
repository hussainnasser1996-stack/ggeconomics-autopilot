# CEO log (newest first; written by the weekly CEO review, autopilot/CEO.md)

## For the owner
- Optional, only you can do these (each unlocks something real; none is needed for daily posting):
  0. 🔴 URGENT 19 Nov: Buffer lost its Instagram login (channel isDisconnected since 18 Nov; 18 + 18b Reels failed, every IG post fails until fixed). buffer.com → Channels → Instagram @ggeconomics → Refresh connection (log in as @ggeconomics). The monitor re-books IG posts that failed in the last 12 h by itself once it is reconnected.
  1. ✅ DONE 17 Nov: TikTok @ggeconomics created + connected in Buffer; publish.py books every Short there.
  2. ✅ DONE 17 Nov: YouTube Analytics API enabled (monitor run 10:58 UTC returned no 403). ✅ DONE 17 Nov: token re-authorised with `youtube.force-ssl` (captions, comments, replies now possible).
  4. 🔴 18 Nov: TikTok has 0 views on every video. Warm the account: 10 min/day on the phone as @ggeconomics for 2-3 days (watch, like, follow gaming videos). Not automatable without bot risk.
  3. ⏳ IN PROGRESS 17 Nov (app "GG Economics Publisher" stopped at owner's FB password re-entry): a free Meta developer app for @ggeconomics → Instagram Trial Reels (test a 2nd hook on non-followers), custom cover frame, collab posts.
  4. Keymailer, Terminals.io, Steam Curator page, Ubisoft Creators Program → free game keys. See PARTNERSHIPS.md. No milestone reached yet (0 subscribers, log/metrics/2026-11-16.json), so nothing new.

## Engineering backlog (from the 16 Nov tools scout; the engineering routine works top-down, measures each change)
1. Hook frame: score 20–30 candidate frames (aesthetic predictor v2.5 or LAION, + sharpness, no text) and open on the best; time it on the 2-core runner first (budget < 60 s).
2. TransNetV2 (transnetv2-pytorch, MIT) in front of OpenCV shot scoring: cleaner shot boundaries, catches dissolves; pin device=cpu.
3. Beat grid per library track (Beat This!, MIT; compute once offline → assets/music/lib/*.beats.json); snap clip cuts to beats in autopick.
4. Saliency 9:16 reframe (OpenCV spectral-residual + MediaPipe faces) instead of centre crop; smooth the crop path.
5. Chatterbox Turbo voice trial vs Kokoro: adopt only if a 30 s VO renders < 3 min on the runner AND gates VO similarity ≥ 0.9.

## 2026-11-16 (16:51 UTC) · addendum, second run on the same day

**What happened (since the 10:51 review)**
- Delivery: the earlier engineering request is resolved. log/delivery.md (16:48 UTC) shows 11-16c sent 12:22 UTC (YT 2lyn0JAlPoU, IG DfzWFNchCUT) and 11-16b sent 16:01 UTC (YT ct7tlizYNYQ, IG DfzvK0aNWmC); 11-16 carousel sent 15:04 UTC; main 11-16 Short/Reel scheduled 23:00 UTC. Problems: none. gates.txt PASS for 11-16b (VO 0.95, 23.9 s) and 11-16c (VO 0.96, 24.9 s).
- First numbers: log/metrics/2026-11-16.json + scoreboard.md: 11-16c (top-5 ranked, "Rockstar Made 2 of the 5 Best-Selling Games Ever") 145 views, 1 like, 0 comments; channel 0 subscribers. YouTube Analytics returns HTTP 403 (avg % viewed, subs per video unavailable). Instagram metrics all empty. 11-16b not in metrics yet (published after the metrics run). 1 post with data, < 1 day: **too early**.
- Music / edit-vs-narrated comparison (1a): no data. yt_done.json has `music: null` for 11-16b and no `music` key for 11-16c; no `mode: edit` post has published (2026-12-31c is a dry test).
- Packaging review (1b): blocked. No post.json in queue/2026-11-16..19 contains `title_candidates`, `hook_style` or `keywords` (keys present: title, caption, hashtags, carousel, publish_time_utc, localized), although BRAIN.md 5b says to store all five candidates + scores. Without them the top-vs-bottom-third comparison cannot be done next week.
- Budget: ~470 of 2,000 Actions minutes used this month (delivery.md). At 3 posts/day × ~17 min until 23 Nov plus monitor runs, the month should still fit, but watch the figure daily.

**Market**
- The Game Awards 2026 nominees: still not confirmed. Search (16 Nov) found the official page "coming mid-November" and one unverified geekchamp report that they are out; last year's list came on a Monday (17 Nov 2025, Game Informer). The topics.md TGA lines stay as they are: use only after the list is on thegameawards.com.
- Nothing else re-searched: the 10:51 review covered trending, platform rules and peers 6 hours ago; research/outliers.md (16 Nov) shows GTA 6 humour/relatable Shorts as the 5–17x outliers, consistent with that review.

**Decisions**
- No changes. One post with 145 views is not evidence; this morning's decision 1 (BRAIN step 3, no pure narration) stands and is judged next week.

**Engineering requests**
- post.json is missing `title_candidates` (with scores), `hook_style` and `keywords` on every post 11-16..11-19. Either the brain is skipping BRAIN.md 5b step 2 or a script drops the keys when it writes post.json. Fix so the Sunday packaging review has data.
- YouTube Analytics 403 (scoreboard.md notes): the token likely lacks the `yt-analytics.readonly` scope or the API is not enabled on the project. Without it, avg % viewed and subs per video stay blank and the weekly ranking can't run. If it needs a consent click, add it to the owner's item 2 below.
- yt_done.json: record `music` for every post (11-16b null, 11-16c missing) so 1a can compare game vs library music.

**For the owner**: unchanged (list at the top). No milestone reached (0 subscribers).

## 2026-11-16 · first review (pipeline went live today)

**What happened**
- Nothing has published yet. log/metrics/2026-11-16.json: YouTube channel 0 views, 0 subscribers, 0 videos; Instagram empty. scoreboard.md has no rows. log/weekly.md does not exist yet (first Sunday run is 22 Nov). Verdict: too early; at most one change.
- Delivery (log/delivery.md, 10:51 UTC): 10 posts booked in Buffer for 11-16..11-19 (YT + IG Reel each day, carousels 11-16 and 11-18). 11-16b (16:00 UTC) and 11-16c (12:00 UTC) were not booked; the monitor re-dispatched both builds (retry 1). gates.txt PASS for 11-18 (VO 0.88, 23.9 s) and 11-19 (VO 0.86, 22.7 s). No failures yet.
- Fact flag from review.md resolved: tonight's 11-16 post says Sensor Tower estimates "more than a billion" in digital pre-orders. Opened tech-ish.com (11 Nov): Sensor Tower 10.31M copies, just over $1B (PS5 7.73M / $751M, Xbox 2.58M / $250M). The $751M figure ITC.ua quoted is the PS5-only number (or the 5 Nov total on ggrecon.com, 7.71M / $751M). The claim holds and the caption says Take-Two hasn't confirmed it.

**Market**
- YouTube trending gaming (research/trending.md, 16 Nov): TGG "GTA 6: Everything You NEED To Know (2 Days Left)" at 1.81M, FoltynGaming "I Downloaded GTA 6!" 405k, plus GTA 5 nostalgia and RP videos. GTA 6 practical/what-you-need angles are where demand is; our 11-17..11-19 queue already sits there.
- Platform: on 1 Oct 2026 YouTube said Shorts recommendations favour original content and cut distribution for channels that mainly re-upload; per ppc.land/Search Engine Journal, YouTube's Creator Liaison said voice-over that only describes the footage does not make a clip original. That matters because CONTROL.md footage_policy allows any YouTube source. No Instagram Reels change found for November.
- Calendar: The Game Awards 10 Dec (Insider Gaming and others; nominees due mid-Nov, not yet confirmed out). Black Friday 27 Nov; Steam has no storewide sale then (Autumn Sale ran 1–8 Oct, Winter Sale 17 Dec – 4 Jan). Tencent/NetEase/Ubisoft result dates in topics.md are not confirmed on company pages.
- Fast-growing peers: no source I found names a fast-growing gaming-news Shorts channel this month. ChannelCrawler's 2026 lists are dominated by Roblox/Minecraft Shorts channels; vidIQ notes generic "GTA 6 news" without an angle did not win. Not enough evidence to copy anyone; revisit with our own data next week.

**Decisions**
1. BRAIN.md step 3: every script line must add a number, calculation, comparison or verdict; never narrate what the trailer shows. Reason: YouTube's 1 Oct originality update + our footage is third-party trailers. Metric next week: YouTube views per Short vs Instagram views per Reel for the same render (a YouTube-only reach penalty would show as YT far below IG).
2. Restocked research/topics.md with 10 dated topics for 17 Nov – 3 Dec (Day-N-after-launch series, pre-order record ranking, TGA eligibility real-or-rumour, TGA nominees, two Sunday scoreboards, Black Friday console prices, Steam sale timing, GTA 6 cost per hour, GTA Online prices). Housekeeping, not a strategy change.
- No change to CONTROL.md / STRATEGY.md: no performance data to justify one. Nothing from last week to revert.

**Engineering requests**
- Confirm 11-16b and 11-16c actually got booked after the retry (16:00 and 12:00 UTC today). If retries keep being needed on new b/c slots, the brain → build chain for extra slots needs a look (delivery.md 10:51 UTC shows both unbooked ~1 h before the 12:00 slot).
- analytics.py: once posts are live, add per-post views split by platform to scoreboard.md so decision 1's metric can be read directly.
- [eng 2026-11-16] Request 1 checked: 11-16b (YT ct7tlizYNYQ + IG reel, 16:01 UTC) and 11-16c (YT 2lyn0JAlPoU + IG reel, 12:22 UTC) both sent per delivery.md 16:48 UTC; no code change. Watch whether new b/c slots keep needing the monitor retry before touching the chain.
- [eng 2026-11-16] Request 2 done on branch eng/2026-11-16 (merges via eng-test.yml only if the dry build passes; see engineering.md): analytics.py now writes a "Per post: views by platform" table at the top of scoreboard.md (YouTube Short / IG Reel / IG carousel / total per queue post), mapped via log/yt_done.json and queue/*/buffer_ids.json, and saves it as per_post in log/metrics/<date>.json. YouTube = Data API views; IG = Buffer views (reach for carousels without views); — = not sent or no metrics yet.

