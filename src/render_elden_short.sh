#!/bin/zsh
cd "$(dirname $0)/../studio"
until grep -q -e LONG2_OK -e Error ../work/long2.log; do sleep 20; done
nice -n 5 npx remotion render src/index.ts EldenShort ../out/elden_short_raw.mp4 --log=error --concurrency=4 && python3 "/Users/hussainnasser/Developer/Personal Business/Motion Studio/tools/audio/master.py" ../out/elden_short_raw.mp4 ../out/elden_short_9x16.mp4 && rm ../out/elden_short_raw.mp4 && echo ES_OK
