# GG Economics autopilot — control panel (Husain edits this; the routine obeys it)

mode: auto               # dry_run = build + queue locally, no publishing | auto = publish via Buffer | paused = do nothing
footage_policy: downloaded_as_is   # Husain's decision 2026-11-15: any YouTube source may be used; always add our narration/data/credit
platforms: [youtube_shorts, instagram_reels, tiktok]   # Buffer Free: 3 channels (all used); TikTok added 17 Nov
publish_time_utc: "23:00"   # main Short (queue/<D>)
posts_per_day: 3            # CEO 21 Nov (GROWTH.md): 3 stays after the launch window. Each Short is a ~1,000-view test; more tests = faster learning
extra_slots_utc: ["17:30", "12:00"]   # 19 Nov: b moved 16:00→17:30. All 3 weak YT Shorts (11, 29 views; others 294-1177) were 16:00, only 4 h after c; test even 5.5 h spacing. Review 26 Nov.
carousel_days: [Mon, Wed, Fri]
longform_day: Sun           # phase 2: needs the new channel's YouTube API token
focus_this_week: "Cost per hour series (2 of 3 slots, E1-E3 live), GTA VI at most 1 post a day, Black Friday 27 Nov / Cyber Monday 30 Nov wallet angle, The Game Awards 10 Dec"   # CEO 22 Nov
launch_window_until: 2026-11-23   # posts_per_day is raised to 3 until this date
skip_dates: []
max_short_seconds: 35
