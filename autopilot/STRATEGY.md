# GG Economics: growth strategy (v2, 16 Nov 2026)

**Goal:** followers and reach on YouTube + Instagram (not ad revenue), so gaming companies want to partner.
Benchmark: Shorts convert ~1.5–2 subscribers per 1,000 views → 10k subscribers ≈ 5–6M Shorts views. Volume of
good posts and series that give a reason to subscribe are the levers.

**Position:** gaming news told through the money: prices, budgets, sales, earnings, what it costs YOU. Original
numbers (our own calculations, rankings, verdicts) keep us clear of YouTube's "inauthentic content" rule and Instagram's
April-2026 aggregator crackdown, which cut reach for accounts that mostly repost.

## Cadence
- YouTube Shorts + Instagram Reels: **2 a day** (17:30 + 23:00 UTC = 12:30 PM + 6 PM New York; b slot moved from 16:00 on 19 Nov), **3 a day** in launch windows
  (adds 12:00 UTC). Above ~5/day risks spam throttling.
- Instagram carousels Mon/Wed/Fri (Sunday = the weekly money scoreboard). Carousels get a second showing (slide 2) to
  people who didn't swipe, and sends are Instagram's strongest signal for reaching non-followers.
- Re-tune times after 30 days of our own analytics (published "best time" studies contradict each other).

## Formats (rotate; the format menu in BRAIN.md)
1. Daily series: "GTA VI: Day N after launch", "N days to <launch>". Reason to subscribe.
2. Cost per hour verdict: price ÷ hours to beat vs a movie. Our own number.
3. Ranked 5 → 1 with #1 held to the end. Feeds "viewed vs swiped away".
4. Real or rumour? quiz. Comments + sends.
5. Weekly money scoreboard (Sunday carousel + Short).
6. Breaking news with a number / your wallet.

## Every Short
Number on screen from frame 0 and in the first words · title ≤ 50 chars "<game> + number + stakes" · 20–30 s · last line
loops into the first · word-by-word captions · sources on screen · estimates labelled · a question at the end of the caption
· 3–5 descriptive hashtags (Instagram caps at 5).

## Sound
Music bed rotates through a CC-BY library (Kevin MacLeod) and starts on the drop, snapped to a beat; ducks under the voice;
master −14 LUFS. No commercial songs baked in: claims can block a Short in whole countries and Instagram mutes them, which
kills reach. Next: Instagram's own trending audio can be attached via Meta's Graph API (`ig_audio`) when Reels are published
directly instead of through Buffer; Buffer's API has no audio field yet.

## Growth levers (ranked)
1. GTA VI launch window (now → ~10 Dec): 3 posts a day, answer launch questions within hours.
2. Numbered series + playlists so a viewer can binge and has a reason to subscribe.
3. Cross-post the same renders to TikTok (biggest free extra reach; needs a TikTok account in Buffer's free 3rd slot).
4. A question in every caption; YouTube community poll before each series episode (when the tab unlocks).
5. Weekly 3–5 min long-form roll-up (long-form converts ~35% better to subscribers): phase 2.

## Feedback loop
Nightly: analytics.py → scoreboard.md; the brain's daily review explains each post's numbers and writes learned.md rules
(3+ posts before a rule). Sunday: weekly.md with totals, best/worst post, pillar + format ranking, 3 changes.

## What not to do
No clickbait the video doesn't pay off; no fake leaks or AI "gameplay"; no spoilers; no raw re-uploads without our layer;
never present a rumour as fact.

Partnerships plan: `PARTNERSHIPS.md`.
