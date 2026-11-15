#!/bin/zsh
# Nightly entry point (launchd). One run per day; logs to autopilot/log/runs/<date>.log
export PATH="/Users/hussainnasser/.local/node/bin:/opt/homebrew/bin:/Users/hussainnasser/.local/python/bin:/Users/hussainnasser/.local/bin:/usr/local/bin:/usr/bin:/bin:$PATH"
export USER=hussainnasser LOGNAME=hussainnasser HOME=/Users/hussainnasser
# long-lived token from `claude setup-token`, stored in keychain (service ggeconomics-claude)
T=$(security find-generic-password -s ggeconomics-claude -a claude -w 2>/dev/null); [ -n "$T" ] && export CLAUDE_CODE_OAUTH_TOKEN="$T"
GN="/Users/hussainnasser/Developer/Personal Business/Motion Studio/experiments/game-news"
D=$(date -u +%F); LOG="$GN/autopilot/log/runs/$D.log"
cd "$GN" || exit 1
[ -d "autopilot/queue/$D" ] && [ -f "autopilot/queue/$D/buffer_ids.json" ] && { echo "already done $D" >> "$LOG"; exit 0; }
grep -q "^mode: paused" autopilot/CONTROL.md && { echo "paused" >> "$LOG"; exit 0; }
echo "=== run $D $(date)" >> "$LOG"
command claude -p "You are the GG Economics autopilot. Today (UTC) is $D. Follow autopilot/ROUTINE.md exactly, end to end, then stop." \
  --permission-mode bypassPermissions >> "$LOG" 2>&1
RC=$?; echo "=== exit $RC $(date)" >> "$LOG"
[ $RC -ne 0 ] && osascript -e "display notification \"Nightly run failed (exit $RC). See autopilot/log/runs/$D.log\" with title \"GG Economics\" sound name \"Basso\""
exit $RC
