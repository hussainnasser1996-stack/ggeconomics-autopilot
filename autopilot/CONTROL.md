# GG Economics autopilot — control panel (Husain edits this; the routine obeys it)

mode: auto               # dry_run = build + queue locally, no publishing | auto = publish via Buffer | paused = do nothing
footage_policy: downloaded_as_is   # Husain's decision 2026-11-15: any YouTube source may be used; always add our narration/data/credit
platforms: [youtube_shorts, instagram_reels]   # Buffer Free: 3 channels total, LinkedIn uses 1
publish_time_utc: "23:00"   # 6 PM US Eastern, peak for the main English-speaking gaming audience
carousel_days: [Mon, Wed, Fri]
longform_day: Sun           # phase 2: needs the new channel's YouTube API token
focus_this_week: "GTA VI launch week (launch 19 Nov 2026), then the GTA VI first-week numbers"
skip_dates: []
max_short_seconds: 35
