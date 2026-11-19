# GG Economics autopilot — control panel (Husain edits this; the routine obeys it)

mode: auto               # dry_run = build + queue locally, no publishing | auto = publish via Buffer | paused = do nothing
footage_policy: downloaded_as_is   # Husain's decision 2026-11-15: any YouTube source may be used; always add our narration/data/credit
platforms: [youtube_shorts, instagram_reels, tiktok]   # Buffer Free: 3 channels (all used); TikTok added 17 Nov
publish_time_utc: "23:00"   # main Short (queue/<D>)
posts_per_day: 2            # 2 = main + a second Short at 17:30 UTC (queue/<D>b); 3 adds 12:00 UTC (queue/<D>c) for launch weeks
extra_slots_utc: ["17:30", "12:00"]   # 19 Nov: b moved 16:00→17:30. All 3 weak YT Shorts (11, 29 views; others 294-1177) were 16:00, only 4 h after c; test even 5.5 h spacing. Review 26 Nov.
carousel_days: [Mon, Wed, Fri]
longform_day: Sun           # phase 2: needs the new channel's YouTube API token
focus_this_week: "GTA VI launch week (launch 19 Nov 2026), then the GTA VI first-week numbers"
launch_window_until: 2026-11-23   # posts_per_day is raised to 3 until this date
skip_dates: []
max_short_seconds: 35
