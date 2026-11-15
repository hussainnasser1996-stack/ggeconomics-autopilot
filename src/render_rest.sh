#!/bin/zsh
cd "$(dirname $0)/../studio"
M="/Users/hussainnasser/Developer/Personal Business/Motion Studio/tools/audio/master.py"
until grep -q -e LONG_OK -e Error ../work/long_render.log; do sleep 15; done
r() { nice -n 5 npx remotion render src/index.ts "$@" --log=error --concurrency=4 && echo "OK $1"; }
mastered() { python3 "$M" ../out/$1_raw.mp4 ../out/$1.mp4 >/dev/null && rm ../out/$1_raw.mp4 && echo "MASTERED $1"; }
r EldenWalk ../out/elden_walkthrough_raw.mp4 && mastered elden_walkthrough
mkdir -p ../out/twitch
r TwitchStartingSoon ../out/twitch/starting_soon_loop.mp4
r TwitchBRB ../out/twitch/brb_loop.mp4
r TwitchStinger ../out/twitch/stinger_alpha.mov --codec=prores --prores-profile=4444 --pixel-format=yuva444p10le --image-format=png
nice npx remotion still src/index.ts TwitchOverlay ../out/twitch/overlay_alpha.png --frame=0 --image-format=png --log=error && echo "OK overlay png"
r TwitchOverlayDemo ../out/twitch/overlay_demo.mp4
echo ALL_DONE
