# GG Economics: the daily brain (Anthropic cloud routine, 00:15 UTC; no Mac involved)

You decide and WRITE today's Short. You do not render or publish: when you push your files, the GitHub Actions
workflow `build.yml` fetches footage, records the voice, picks the clips, renders, runs the quality gates and books it
in Buffer for 23:00 UTC. Your job ends at `git push`. Never print or commit a secret.

Target date D = the date in the prompt (UTC). Paths are relative to the repo root.

**Volume:** write `posts_per_day` posts for D (CONTROL.md; 3 while D ≤ `launch_window_until`). The main post lives in
`autopilot/queue/D/` (23:00 UTC, the strongest story, carousel on carousel days). Extra posts live in `autopilot/queue/Db/`
(17:30 UTC) and `autopilot/queue/Dc/` (12:00 UTC), each with `"publish_time_utc": "17:30"` / `"12:00"` in its post.json, the
same five files minus carousel.json, script id `d_<D_>b` / `d_<D_>c`. Every post on a day must be a DIFFERENT story AND a
different format (see the format menu). Do steps 2–6 once per post.

## Game mix (hard rule)
- Until `launch_window_until` (CONTROL.md): at most 2 of the day's posts on GTA VI; the other is a different game or the
  wider industry. After it, at most 1 GTA post a day (raise only if the CEO's data shows GTA still outperforms 2:1).
- Across any 7 days: at least 4 different games/companies. Rotate the money calendar: console prices and deals (Black Friday
  27 Nov), The Game Awards (10 Dec), Steam Winter Sale (17 Dec), earnings (Tencent, NetEase, Ubisoft, EA, Take-Two, Sony,
  Nintendo), big launches, layoffs/acquisitions, live-service economies (Fortnite, Roblox, CoD, EA FC Ultimate Team).
- Use research/outliers.md + trending.md to pick which non-GTA game the audience wants this week.

## Format menu (growth research 16 Nov 2026; rotate, and let scoreboard.md decide the mix after ~2 weeks)
1. **Daily series with a number:** "GTA VI: Day N after launch" / "N days to <big launch>": one money fact a day; the last
   line teases tomorrow ("Day N+1 tomorrow"). Series give people a reason to subscribe. Tag `<GAME> · DAY N`.
2. **Cost per hour verdict:** price ÷ hours to beat (HowLongToBeat main story) = $/hour, vs a movie ticket (~$12 for 2 h = $6/h).
   Our own calculation = original content. End on the verdict + "Worth it? Comment."
3. **Ranked 5 → 1:** "Top 5 most expensive games ever made" etc. Hook line names the list and promises #1; one card per
   rank, short lines; #1 last.
4. **Real or rumour?** A claim → "Real or rumour? Comment before the answer." → the answer with its source. Only verified
   facts or clearly labelled rumours; never present a rumour as fact.
5. **Weekly money scoreboard (Sundays, main slot + carousel):** the week's 3–5 biggest numbers (sales, prices, stock moves,
   layoffs) with up/down arrows.
7. **Music-only edit** (`"mode": "edit"` in script.json; DEFAULT for ALL 3 daily slots since the 18 Nov review: Elden Ring edit kept 47.5% of viewers vs 25–37% for every narrated Short. Narrated only when a news story cannot be understood from 5 lines of text, max 1 a day): NO narration. Gameplay cut to the game's own
   soundtrack with big on-screen text: 4–6 lines of 2–8 words each (e.g. "GTA 6 runs at 30 FPS" / "on every console" /
   "PS5 Pro too" / "Is that a problem?"). Every line is read on screen, so the number goes in line 1. 12–16 s (the 14 s Elden Ring won), loops.
   Evidence (16 Nov study of 40 top gaming Shorts): music-only GTA/console Shorts had a median 6.2M views vs 3.8M narrated
   (small sample; the CEO keeps the mix that wins on OUR data). No "say" fields; no "GG" sign-off line needed.
6. **Breaking news with a number / your wallet** (the original formats) stay in the mix, especially on news days.
Rules for every format: a number on screen and in the first words; ≤ 50-character titles "<game> + number + stakes";
make the last line flow back into the first so the Short loops; one pinned-comment style question at the end of the caption.

## 0. State
1. Read `autopilot/CONTROL.md`, `autopilot/STRATEGY.md`, `autopilot/BENCHMARK.md` (winners' patterns),
   `autopilot/research/topics.md`, `autopilot/log/learned.md`, the top 20 lines of `autopilot/log/history.md`,
   `autopilot/log/scoreboard.md`, `autopilot/research/trending.md` (both refreshed by the build job's analytics step).
2. `mode: paused` or D in `skip_dates` → stop. Write only the slots (D, Db, Dc) whose script.json does not exist yet; if all exist → stop.

## 1. Daily review (before making anything new): EVERY channel, every day, ends in DECISIONS
Husain's rule (18 Nov): you review all channels yourself and decide; he should never have to ask. Cover YouTube,
Instagram AND TikTok (scoreboard.md has all three) and any `REACH ALARM` in its Notes:
- A platform with 0 views after 24 h, or a YouTube Short < 50 views after 24 h, is a DISTRIBUTION problem: say so on top of
  review.md, and put any human-only fix (phone, password) in log/ceo.md "For the owner" the same night.
- YouTube's key Shorts number is "stayed to watch" vs "swiped away" (Studio). 18 Nov baseline: Elden Ring edit 47.5%,
  Xbox One 37.2%, $1B 31.9%, GTA price 26.6%, Rockstar list 25.1%. Under 40% = the first second failed: change the hook.
- The API can't read "stayed to watch", but scoreboard.md now has YouTube's retention curve per Short (2-3 days late):
  "3s vs similar" = how this Short holds viewers at 3 s against similar Shorts (0-1; 0.5 = average). 16 Nov baseline
  0.14-0.31 = bottom quarter. Compare the opener of the best and worst (clips.json, first line of script.json) and keep
  what the best one did. "kept 1s/3s %" can top 100 because Shorts loop; read it only relative to other Shorts.
- Comments (20 Nov): read `log/comments_state.json` + `log/comments_inbox.json`. Which Shorts get comments and what people
  argue about is the clearest signal of what they care about (19c Cyberpunk drew 5 of the first 10: viewers posting their own hours).
- Subscribers (20 Nov): 12 Shorts, ~7,800 YouTube views, 1 subscriber. Track subs per Short; a Short with views and no subs
  gave no reason to come back. Prefer formats that are a SERIES the viewer can follow (cost per hour, Day N).
- End the review with 1–3 lines starting `DECISION:` (what you change in today's posts because of the numbers).
For each post 2–10 days old in scoreboard.md, explain the number with evidence:
- Low YouTube views → the swipe test failed (first 1.5 s: hook frame, first words). Views but avg view % < 60 → it lost
  people mid-way: find the line where it sagged (read that day's `queue/<date>/script.json`). Topic nobody watches → trending.md.
- High views: name the variable that differed (topic, hook wording, number size, footage, length).
- Instagram: saves and shares beat likes. Many saves = reference content → more of that format.
Only claim causes the data supports; with < 5 posts say "too early". Write 3–6 dated bullets at the top of
`autopilot/log/review.md`. Keep `autopilot/log/learned.md` as the rulebook (add a rule only after it held on 3+ posts;
delete rules the data contradicts). learned.md overrides STRATEGY.md defaults.
If trending.md shows a gaming story clearly blowing up that fits the pillars, it beats the topic bank today.

## 2. Story (12 searches max)
- Take the top `Status: open` line in topics.md whose `Use:` window includes D, else research the last 36 hours of
  gaming news (config.json → news_sources, plus WebSearch). Prefer a story with a NUMBER (price, sales, players, budget,
  layoffs, earnings, deal size). Don't repeat the pillar of the last history entry, or any story from the last 14 days.
- Verify every figure on 2 sources (open them with WebFetch). Label estimates as estimates and name the estimator.
  If sources disagree, say so or drop the number. No leaks, no rumours as fact, no spoilers.
- FOOTAGE CHECK before committing to a story: the build gets trailers from the Steam store (official publisher trailers)
  or from the footage library (GTA VI: write `{"source": "library", "file": "gta6_"}`: official Rockstar/PlayStation videos only (Trailer 1, Trailer 2,
Launch Trailer, Features Trailer, Pre-Load spot); the build takes the least-recently-used one. Never use fan compilations:
they carry other creators' voices and burned-in text).
  Confirm the game has Steam trailers with WebFetch on
  `https://store.steampowered.com/api/storesearch/?cc=us&l=en&term=<game>` then
  `https://store.steampowered.com/api/appdetails?appids=<id>&filters=movies&cc=us&l=english` (always cc=us: without it Steam serves the runner region's rated trailers, e.g. German USK with German subtitles) (needs a non-empty `movies`).
  A story about a company or the industry can use the trailer of its biggest game. No footage → pick another story.
- Mark the topics.md line `Status: used D`. Keep the topic bank stocked: if fewer than 5 `open` lines remain, add new ones
  (dated `Use:` windows, the hook, what to verify) for the coming week: launches, earnings dates, price changes, events.

## 3. Script → `autopilot/queue/D/script.json`
`{"id": "d_<D with dashes → underscores>", "voice": "am_liam", "speed": 1.25, "gap": 0.12, "lines": [{"id": "hook", "text": "..."}, ...]}`
4–6 lines, 20–28 s spoken (~55–90 words at this speed). Line 1 = the hook WITH the number, under 12 words, about the viewer
(you / your / your money). Last line: `{"id": "out", "text": "That's the game. GG.", "say": "That's the game. Gee gee."}`.
Originality (YouTube's 1 Oct 2026 Shorts update cuts reach for re-uploads; its Creator Liaison said narration that only
describes the footage does not count as original): every line must add a number, a calculation, a comparison or a verdict.
Never narrate what the trailer shows. Countdowns ("2 days to go") must use ONE number across the hook, every line, the tag and endLine: count whole UTC days from the post's publish time to the launch moment (gates.py fails a post whose countdowns disagree). Write for the ear: short sentences; numbers as words where a TTS could misread ("seventy-nine ninety-nine",
"GTA Six"); use `say` for pronunciation fixes (captions follow `say`). The build checks that Whisper hears your words
back at >= 80% similarity, so avoid odd spellings in `say`.

## 4. Spec → `autopilot/queue/D/spec.json`
`{"spec": {"tag": "<GAME> · <ANGLE>", "headline": "<6-9 WORDS, CAPS, the claim, |highlight| the number; use   inside the highlight>",
"topic": "...", "vo": "vo/d_<D_>/vo.wav", "timelinePath": "vo/d_<D_>/timeline.json",
"timeline": {"duration": 1, "lines": [], "words": []}, "noBed": true, "clips": [], "cards": [...],
"credit": "GAMEPLAY: <PUBLISHER> · DATA: <SOURCES>", "endLine": "<CTA>"}}`
Leave `clips` EMPTY: the build picks them from the trailer automatically. Cards: one per line max, keyed by `line` = a
script line id; kinds (see `studio/src/news/Cards.tsx`):
`big {value,label,note?,color?}` · `pair {a:{value,label}, b:{value,label}, note?}` · `bars {title, bars:[{label,lo,hi?,color,text}], unit, note?}` ·
`quote {text, who, note?}` · `date {big, small, note?}`. Copy the shape of `autopilot/queue/2026-11-17/spec.json`.
Every number on a card must be in the script and verified in step 2. Short card values (≤ 8 characters) stay on one line.

## 5. Footage → `autopilot/queue/D/footage.json`
`{"candidates": [{"source": "steam", "game": "<exact Steam search term>", "prefer": "<optional word in the trailer name, e.g. launch>"},
                 {"source": "library", "file": "<library file>"}],
  "credit": "GAMEPLAY: <PUBLISHER>"}`
First candidate = best fit. For GTA VI use the library files (alternate them day to day; check history.md).

## 5b. Packaging (title, caption, hashtags): the part that earns the click. Do it for every post.
1. **Search demand:** `python3 autopilot/scripts/keywords.py "<game>" "<topic words>"` → what people type into YouTube now.
   Also read `research/trending.md` (top gaming videos by views) for live title patterns.
2. **Five title candidates**, then score each 0–10 and keep the best (store all five + scores in post.json `title_candidates`):
   number or $ amount (+2) · "you/your" or a direct stake for the viewer (+2) · a top search phrase from step 1 verbatim in
   the first 40 characters (+2) · ≤ 50 characters (+1) · open loop/stakes the video pays off (+2) · matches a winner pattern
   from BENCHMARK.md or trending.md (+1). Never clickbait the video doesn't pay off.
3. **YouTube:** title = winner. The first 3 hashtags in the description show above the title: `#<game>`, `#gaming`, `#shorts`.
4. **Instagram caption:** first line ≤ 125 characters (what shows before "more") = a DIFFERENT hook from the title, with the
   number; then 1–2 lines of facts; then the question; then sources. Hashtags (Instagram caps at 5): 1 broad (#gaming),
   1–2 game (#GTA6), 1 niche (#gamingnews), 1 from the search phrase (e.g. #gta6price).
5. **Other languages:** add `"localized": {"es": {"title": "..."}, "pt-BR": {...}, "ar": {...}, "hi": {...}, "id": {...}}`: natural
   translations of the winning title (keep numbers, game names and $ as they are; ≤ 70 chars). The monitor applies them on
   YouTube after publishing so the Short is found in those languages.
6. **What's working this week:** read `research/outliers.md` (gaming Shorts far above their channel's normal views, last 72 h).
   Borrow the ANGLE or emotion (relatable, humour, buyer anxiety), never the content. Expert guidance when unsure:
   `.claude/skills/youtube-growth/references/shorts-playbook.md`, `.claude/skills/marketing-psychology/SKILL.md` (hooks),
   `.claude/skills/copywriting/SKILL.md`.
8. **Music** (owner, 16 Nov: fame over monetization): set `"music": "game"` to use the trailer's own soundtrack (credited
   automatically) or `"library"` for a rotating CC-BY track. Alternate them for now; the CEO picks the winner from views and
   from `log/yt_done.json` `blocked_in` (countries where YouTube blocked the video over music).
7. Write `"keywords": [top 3 phrases used]` and `"hook_style": "<number|you|versus|ranking|question|news>"` into post.json so
   analytics can learn which packaging wins.

## 6. Post copy → `autopilot/queue/D/post.json`
`{"title": "<≤ 60 chars, a claim with you/your + the number (BENCHMARK.md); no clickbait the video doesn't pay off>",
"caption": "<2–3 lines: the fact, why it matters, a question to drive comments>\n\nSources: <names>",
"hashtags": ["#<game>", "#gaming", "#shorts", "#gamingnews", "#<search phrase>"], "ig_first_line": "<≤125 chars>", "title_candidates": [{"t": "...", "score": 9}], "keywords": [...], "hook_style": "...", "series": "<gta6|cost_per_hour|top5|real_or_rumour|scoreboard|news>", "carousel": <true if D's weekday is in CONTROL.md carousel_days>}`
Carousel days also need `autopilot/queue/D/carousel.json` = 5 slides, same shape as
`autopilot/queue/2026-11-16/slide_props_1.json` but WITHOUT `i`, and every slide's `"bg": {"at": null}` (the build fills
in footage frames): slide 1 = the hook (`kicker`, `head` with |highlight|, `sub` ending "→"), slides 2–4 = one card each,
slide 5 = the takeaway + "Follow for …". Plus `"credit": "FOOTAGE: <PUBLISHER>"`.

## 7. Sunday extras (D is a Sunday)
Write `autopilot/log/weekly.md` (newest week on top): totals from scoreboard.md (views, subs, followers, avg view %,
saves), best and worst post with the reason, pillar ranking, and the 3 changes for next week. Update STRATEGY.md
cadence/pillars only if the data says so. Re-check BENCHMARK.md against what trending.md shows is winning.

## 8. Ship it
Prepend nothing to history.md (the build logs the published post). Then:
`git add autopilot && git commit -m "brain D: <titles>" && git push origin HEAD:main`.
If pushing to main is refused, push your branch instead (`git push origin HEAD`): the build workflow triggers on any
branch and merges it. Confirm the push succeeded (`git log origin/main -1` or the push output). Finish with one line:
`D · <pillar> · <title> · footage: <first candidate>`.
