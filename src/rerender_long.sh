#!/bin/zsh
cd "$(dirname $0)/../studio"
until grep -q ALL_DONE ../work/rest_render.log; do sleep 20; done
nice -n 5 npx remotion render src/index.ts GtaLong ../out/gta_long_raw.mp4 --log=error --concurrency=4 && python3 "/Users/hussainnasser/Developer/Personal Business/Motion Studio/tools/audio/master.py" ../out/gta_long_raw.mp4 ../out/gta_long_16x9.mp4 && rm ../out/gta_long_raw.mp4 && echo LONG2_OK
