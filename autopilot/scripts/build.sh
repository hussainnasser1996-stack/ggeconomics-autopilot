#!/bin/zsh
# build.sh <date>  — expects queue/<date>/script.json and queue/<date>/spec.json (props for DailyShort)
set -e
D=$1; GN="$(cd "$(dirname $0)/../.." && pwd)"; Q="$GN/autopilot/queue/$D"
cd "$GN"
ID=$(python3 -c "import json;print(json.load(open('$Q/script.json'))['id'])")
.venv/bin/python src/vo.py "$Q/script.json" "studio/public/vo/$ID" 2>&1 | grep -E "^(duration|HEARD)" | tee "$Q/vo_qa.txt"
# cloud build: no eyes on contact sheets, so clips are chosen by autopick.py when the brain left them empty
if python3 -c "import json,sys;sys.exit(0 if not json.load(open('$Q/spec.json'))['spec'].get('clips') else 1)"; then
  .venv/bin/python autopilot/scripts/autopick.py "$D"
fi
cd studio
nice -n 5 npx remotion render src/index.ts DailyShort "$Q/raw.mp4" --props="$Q/spec.json" --log=error --concurrency=$(( $(getconf _NPROCESSORS_ONLN) < 4 ? $(getconf _NPROCESSORS_ONLN) : 4 ))
cd "$GN"
python3 src/mix.py "$Q/raw.mp4" assets/music/synthwavehouse.ogg "$Q/short.mp4" --start 16 --gain -13 && rm "$Q/raw.mp4"
.venv/bin/python src/critic.py "$Q/short.mp4" "studio/public/vo/$ID/timeline.json" "daily_$D" 2>&1 | grep -v objc > "$Q/critic.txt" || true
.venv/bin/python src/overlay_safe.py "$Q/spec.json" "$Q/ovsafe" 2>&1 | grep -v objc | tee "$Q/overlay_safe.txt"
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$Q/short.mp4")
python3 - "$Q" "$DUR" <<'PY'
import sys, subprocess
Q, dur = sys.argv[1], float(sys.argv[2])
for i, f in enumerate([0.08, 0.3, 0.55, 0.8, 0.97]):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(dur * f), "-i", f"{Q}/short.mp4", "-frames:v", "1", "-vf", "scale=270:-1", f"{Q}/k{i}.png"])
subprocess.run(["ffmpeg", "-v", "error", "-y"] + sum([["-i", f"{Q}/k{i}.png"] for i in range(5)], []) + ["-filter_complex", "hstack=5", f"{Q}/contact.png"])
for i in range(5): subprocess.run(["rm", f"{Q}/k{i}.png"])
PY
echo "BUILT $Q/short.mp4 — LOOK at $Q/contact.png and read $Q/critic.txt"
