#!/bin/bash
# lf_build.sh <P>: the weekly Top 10 long video for publish date P, end to end on the runner (no Mac).
# data -> trailers + clean clips -> voice + music -> render (LongTop, 1080p) -> sharpen + loudnorm -> thumbnail -> gates -> meta
set -euo pipefail
P=$1; GN="$(cd "$(dirname "$0")/../../.." && pwd)"; L="$GN/autopilot/longform/$P"; cd "$GN"; mkdir -p work/lf "$L"
PY=${PY:-.venv/bin/python}
[ -f "$L/data.json" ] || $PY autopilot/scripts/longform/lf_data.py "$P"
$PY autopilot/scripts/longform/lf_footage.py "$P"
$PY autopilot/scripts/longform/lf_audio.py "$P"
python3 -c "import json;json.dump({'spec':json.load(open('$L/spec.json'))},open('work/lf/props.json','w'))"
( cd studio && npx remotion render src/index.ts LongTop "$GN/work/lf/raw.mp4" --props="$GN/work/lf/props.json" --crf=17 --log=error \
    --concurrency=$(( $(getconf _NPROCESSORS_ONLN) < 4 ? $(getconf _NPROCESSORS_ONLN) : 4 )) --timeout=120000 )
ffmpeg -v error -y -i work/lf/raw.mp4 -vf "unsharp=5:5:0.5:5:5:0" -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p \
  -af "loudnorm=I=-14:TP=-1.5:LRA=11" -c:a aac -b:a 192k -ar 48000 -movflags +faststart "work/lf/top10-$P.mp4"
rm -f work/lf/raw.mp4
$PY autopilot/scripts/longform/lf_post.py "$P" thumb
python3 -c "import json;json.dump({'spec':json.load(open('$L/spec.json'))},open('work/lf/props.json','w'))"
( cd studio && npx remotion still src/index.ts LongThumb "$L/thumb.png" --props="$GN/work/lf/props.json" --log=error )
$PY autopilot/scripts/longform/lf_post.py "$P" gates
$PY autopilot/scripts/longform/lf_post.py "$P" meta
echo "BUILT work/lf/top10-$P.mp4 ($(du -h work/lf/top10-$P.mp4 | cut -f1))"
