#!/bin/zsh
cd "$(dirname $0)/../studio"
until grep -q V2_DONE ../work/v2.log; do sleep 20; done
for c in TwitchStartingSoon:starting_soon_loop TwitchBRB:brb_loop; do
  nice -n 5 npx remotion render src/index.ts ${c%%:*} ../out/twitch/${c##*:}.mp4 --log=error --concurrency=4 && echo "OK ${c%%:*}"
done
S=../work/seam; mkdir -p $S
for f in starting_soon_loop brb_loop; do for n in 0 1 1151; do ffmpeg -v error -y -i ../out/twitch/$f.mp4 -vf "select=eq(n\,$n)" -frames:v 1 $S/${f}_$n.png; done
python3 - $S $f <<'PY'
import sys; from PIL import Image, ImageChops
S,f=sys.argv[1:]
def d(a,b):
    x=ImageChops.difference(Image.open(f"{S}/{f}_{a}.png").convert("L"),Image.open(f"{S}/{f}_{b}.png").convert("L")); return round(sum(x.get_flattened_data())/(x.width*x.height),2)
print("SEAM", f, "wrap", d(1151,0), "normal", d(0,1))
PY
done
echo V3_DONE
