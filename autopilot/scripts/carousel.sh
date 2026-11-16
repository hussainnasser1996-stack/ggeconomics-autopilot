#!/bin/bash
# carousel.sh <D> — render queue/D/carousel.json ({slides:[5], credit}) to slide_1..5.png (only when post.json carousel=true)
set -e; D=$1; GN="$(cd "$(dirname $0)/../.." && pwd)"; Q="$GN/autopilot/queue/$D"
python3 -c "import json,sys;sys.exit(0 if json.load(open('$Q/post.json')).get('carousel') else 1)" || { echo "no carousel today"; exit 0; }
[ -f "$Q/carousel.json" ] || { echo "carousel=true but no carousel.json"; exit 1; }
cd "$GN/studio"; N=$(python3 -c "import json;print(len(json.load(open('$Q/carousel.json'))['slides']))")
for i in $(seq 0 $((N-1))); do
  python3 -c "import json;c=json.load(open('$Q/carousel.json'));c['i']=$i;json.dump(c,open('$Q/slide_props_$((i+1)).json','w'))"
  npx remotion still src/index.ts DailyCarousel "$Q/slide_$((i+1)).png" --props="$Q/slide_props_$((i+1)).json" --log=error
done
