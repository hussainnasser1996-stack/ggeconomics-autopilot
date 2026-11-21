# GG Economics growth plan: YouTube + Instagram (CEO, 21 Nov 2026)

Owner's instruction (21 Nov): Claude is the CEO. Review, decide, act, measure, repeat. Husain does not approve day-to-day
changes. TikTok is parked until he fixes the account in the app; keep posting there, but no work goes into it.
The daily brain reads this file in step 0, runs the live experiments in step 3-6, and in step 1 closes any experiment
whose decision date has come: ADOPT (fold into BRAIN.md / learned.md, move to "Adopted"), KILL (move to "Killed"),
or EXTEND once with a reason. "Too early" is not allowed once an experiment has its sample.

## Diagnosis (data to 21 Nov: 15 YouTube Shorts, 17 Reels, 3 carousels)
1. YouTube: every Short stops near 1,000 views. That is the first test pool. "3s vs similar" is 0.19-0.51 (0.5 = average),
   while avg view % is 55-83%. People who stay, watch; too many swipe in the first second. **The opener is the bottleneck.**
2. The opener gives the answer away: headline and hook card show the same number at frame 0. No open loop.
3. Subscribers: 5 from ~13k views. Nothing on screen ever asked for anything: in music-only edits, lines without a card were
   invisible (fixed 21 Nov: they now show as text cards), and the end card was removed 20 Nov.
4. Comments are all viewers arguing about THEIR hours ("It's 27 hours if you barely explore"). The audience wants to take part.
5. Instagram Reels: 100-250 views, 5-9 s average watch, 0 shares, 0 saves. Instagram spreads Reels by sends (DM shares);
   nothing invites a send.
6. Instagram carousels: 3 posted, reach 0, likes 0 (Graph insights, not a read error). Each reused the Reel's caption.

## Strategy
- **One signature, owned:** cost per hour is the channel's identity (5 for 5 at 850-1,470 YouTube views; best retention).
  After the GTA launch window (23 Nov) it fills 2 of 3 daily slots. Slot 3 = the test slot (a different format each day,
  same price-per-hour or money lens) so we keep finding the next winner.
- **Win the first second** before anything else: run hook experiments until "3s vs similar" median is > 0.5.
- **Turn viewers into participants:** viewers request games in the comments, we price them, and credit them. Requests feed
  the topic bank, comments feed the algorithm, and a numbered series gives a reason to subscribe.
- **Instagram earns sends and saves:** every Reel gives a reason to send it to a friend, and carousels become the
  save-worthy leaderboard instead of a copy of the Reel.

## Live experiments
Measure from scoreboard.md (YouTube retention lands 2-3 days late) and log/metrics/<date>.json. Record each post's variant in
post.json `"experiment": {"E1": "A"}` so analytics can be joined later.

### E1 · Hook: answer-first (A) vs question-first (B), cost-per-hour posts. Started 22 Nov. Decide 28 Nov.
- A (control, current): line 1 = "<Game> costs you $X an hour", headline = same claim, hook card = $X/HR.
- B: line 1 = "Is <Game> worth $<price>?" (the price the viewer pays). NO card on line 1 (it shows as a text card).
  Headline = "IS <GAME> WORTH |$<PRICE>|?". The $X/HR card lands on line 2 (~3 s). Rest identical.
- Assignment: alternate by day. Even days of the month: b = A, c = B. Odd days: b = B, c = A. (Main slot joins after 23 Nov, as A.)
- Metric: "3s vs similar" (primary), YouTube views at 48 h, IG avg watch s. Sample: 3 posts per arm with retention data.
- Rule: B wins if its median "3s vs similar" beats A by >= 0.05 AND views are not lower by > 20%. Then B becomes the default.

### E2 · Request loop + numbered series. Started 22 Nov. Decide 29 Nov.
- Every cost-per-hour Short: tag "COST PER HOUR #N" (N = count of cost-per-hour posts ever, from history.md + queue).
  Last line (shown on screen): "Comment a game. We price it next."
  Caption question: "Which game should we price next?"
- When a comment names a game (log/comments_inbox.json): pick it for a cost-per-hour slot within 3 days if Steam/HLTB have it.
  Caption line 1: "You asked, @<name>: <Game> costs $X an hour." Reply to the comment once the Short is live (COMMENTS.md rules,
  humanizer pass, approval mode applies).
- Metric: comments per 1,000 YouTube views and subscribers per 1,000 views vs the 21 Nov baseline (~4 comments / 1k on
  cost-per-hour; 0.4 subs / 1k). ADOPT if either doubles.

### E3 · Instagram send trigger. Started 22 Nov. Decide 29 Nov.
- Instagram first line (ig_first_line) on cost-per-hour posts names who to send it to: "Send this to the friend with
  300 hours in <Game>." (keep the number in the line). The video itself is unchanged (YouTube unaffected).
- Metric: IG shares + saves per Reel (baseline 0) and reach. ADOPT if 3+ Reels get any shares; else try a send trigger on screen.

### E4 · Carousel = the cost-per-hour leaderboard. Started 23 Nov (next carousel day). Decide 30 Nov (3 carousels).
- Carousel days (Mon/Wed/Fri) stop reusing the Reel. carousel.json = "We priced <N> games by the hour": slide 1 hook,
  slides 2-4 = the ranking cheapest per hour first (5-6 games per slide, `bars` or a list on each), slide 5 = "Comment a game,
  we price it next." Its OWN caption (not the Reel's), set as post.json `carousel_caption` if the build supports it, else note it.
- Metric: reach > 0, saves. KILL carousels entirely (set carousel_days: [] in CONTROL.md) if reach is still ~0 after 3.

## Adopted
- (21 Nov) Lines without a number card are shown on screen in music-only edits (code fix, NewsShort.tsx).
- (21 Nov) 3 posts a day stays after the launch window: each Short is a ~1,000-view test; more tests, faster learning.

## Killed
- (20 Nov) Rumour and company-earnings angles (5-53 views).

## Next up (start one when a live experiment closes)
- Opening frame motion: the first clip must be the highest-motion shot, not just the highest score (autopick hook rule).
- Length: 9-10 s cut vs 13 s (more loops; Shorts reward views per viewer over 100%).
- Head-to-head cost per hour ("Elden Ring vs Dark Souls 3: which is cheaper per hour?") as the test-slot format.
- Pinned comment on YouTube with the request prompt (yt_engage.py) once E2 has data.
