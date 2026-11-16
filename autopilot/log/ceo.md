# CEO log (newest first; written by the weekly CEO review, autopilot/CEO.md)

## For the owner
- Optional, only you can do these (each unlocks something real; none is needed for daily posting):
  1. TikTok account → connect it in the GG Economics Buffer (free 3rd slot) = the same videos reach TikTok.
  2. Re-authorise the YouTube token with the `youtube.force-ssl` scope (one Google consent click) → exact captions upload + auto question comment + comment replies.
  3. A free Meta developer app for @ggeconomics → Instagram Trial Reels (test a 2nd hook on non-followers), custom cover frame, collab posts.
  4. Keymailer, Terminals.io, Steam Curator page, Ubisoft Creators Program → free game keys. See PARTNERSHIPS.md. No milestone reached yet (0 subscribers, log/metrics/2026-11-16.json), so nothing new.

## Engineering backlog (from the 16 Nov tools scout; the engineering routine works top-down, measures each change)
1. Hook frame: score 20–30 candidate frames (aesthetic predictor v2.5 or LAION, + sharpness, no text) and open on the best; time it on the 2-core runner first (budget < 60 s).
2. TransNetV2 (transnetv2-pytorch, MIT) in front of OpenCV shot scoring: cleaner shot boundaries, catches dissolves; pin device=cpu.
3. Beat grid per library track (Beat This!, MIT; compute once offline → assets/music/lib/*.beats.json); snap clip cuts to beats in autopick.
4. Saliency 9:16 reframe (OpenCV spectral-residual + MediaPipe faces) instead of centre crop; smooth the crop path.
5. Chatterbox Turbo voice trial vs Kokoro: adopt only if a 30 s VO renders < 3 min on the runner AND gates VO similarity ≥ 0.9.

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

