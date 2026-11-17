#!/bin/zsh
# build.sh <date>  — expects queue/<date>/script.json and queue/<date>/spec.json (props for DailyShort)
set -e
D=$1; GN="$(cd "$(dirname $0)/../.." && pwd)"; Q="$GN/autopilot/queue/$D"
cd "$GN"
ID=$(python3 -c "import json;print(json.load(open('$Q/script.json'))['id'])")
.venv/bin/python src/vo.py "$Q/script.json" "studio/public/vo/$ID" 2>&1 | grep -E "^(duration|HEARD)" | tee "$Q/vo_qa.txt"
cp "studio/public/vo/$ID/timeline.json" "$Q/timeline.json" 2>/dev/null || true   # kept for exact YouTube captions (yt_engage.py)
# music-only "edit" format: no spoken words, so no karaoke captions (Husain 17 Nov)
python3 -c "import json;q='$Q';e=json.load(open(q+'/script.json')).get('mode')=='edit';s=json.load(open(q+'/spec.json'));s['spec']['noCaptions']=e;json.dump(s,open(q+'/spec.json','w'),indent=1)"
# cloud build: no eyes on contact sheets, so clips are chosen by autopick.py when the brain left them empty
if python3 -c "import json,sys;sys.exit(0 if not json.load(open('$Q/spec.json'))['spec'].get('clips') else 1)"; then
  .venv/bin/python autopilot/scripts/autopick.py "$D"
fi
cd studio
nice -n 5 npx remotion render src/index.ts DailyShort "$Q/raw.mp4" --props="$Q/spec.json" --jpeg-quality=95 --crf=15 --log=error --concurrency=$(( $(getconf _NPROCESSORS_ONLN) < 4 ? $(getconf _NPROCESSORS_ONLN) : 4 ))
cd "$GN"
# 16:9 trailers are cropped ~3x into 9:16: light sharpen + high-quality encode (Husain 17 Nov: Elden Ring looked soft)
ffmpeg -v error -y -i "$Q/raw.mp4" -vf "unsharp=5:5:0.7:5:5:0" -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p -c:a copy "$Q/raw_s.mp4" && mv "$Q/raw_s.mp4" "$Q/raw.mp4"
# re-pick when there is no music.json OR its extracted file is gone (a rebuild on a fresh runner: work/ is not kept)
[ -f "$Q/music.json" ] && [ -f "$(python3 -c "import json;m=json.load(open('$Q/music.json'));print(m.get('path') or 'assets/music/lib/'+m['file'])")" ] || .venv/bin/python autopilot/scripts/pick_music.py "$D"
MP=$(python3 -c "import json;m=json.load(open('$Q/music.json'));print(m.get('path') or 'assets/music/lib/'+m['file'])"); MS=$(python3 -c "import json;print(json.load(open('$Q/music.json'))['start'])")
MG=$(python3 -c "import json;m=json.load(open('$Q/music.json'));e=json.load(open('$Q/script.json')).get('mode')=='edit';print(-2 if e else (-10 if m.get('game') else -12))")
python3 src/mix.py "$Q/raw.mp4" "$MP" "$Q/short.mp4" --start "$MS" --gain "$MG" && rm "$Q/raw.mp4"
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
