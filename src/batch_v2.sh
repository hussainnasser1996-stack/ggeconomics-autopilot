#!/bin/zsh
cd "$(dirname $0)/../studio"
M="/Users/hussainnasser/Developer/Personal Business/Motion Studio/tools/audio/master.py"
MU=../assets/music
until grep -q -e ES_OK -e rror ../work/es.log; do sleep 20; done
r() { nice -n 5 npx remotion render src/index.ts "$@" --log=error --concurrency=4 && echo "OK $1"; }
r Ident ../out/ident_raw.mp4 && python3 "$M" ../out/ident_raw.mp4 ../out/ident_16x9.mp4 >/dev/null && rm ../out/ident_raw.mp4
r Ident9x16 ../out/ident9_raw.mp4 && python3 "$M" ../out/ident9_raw.mp4 ../out/ident_9x16.mp4 >/dev/null && rm ../out/ident9_raw.mp4
r GtaShort ../out/gs_raw.mp4 && python3 ../src/mix.py ../out/gs_raw.mp4 $MU/synthwavehouse.ogg ../out/gta_short_9x16.mp4 --start 16 --gain -13 && rm ../out/gs_raw.mp4
r GtaFeed4x5 ../out/gf_raw.mp4 && python3 ../src/mix.py ../out/gf_raw.mp4 $MU/synthwavehouse.ogg ../out/gta_feed_4x5.mp4 --start 16 --gain -13 && rm ../out/gf_raw.mp4
cp ../out/gta_long_16x9.mp4 ../out/gl_nomusic.mp4 && python3 ../src/mix.py ../out/gl_nomusic.mp4 $MU/space_city_115.ogg ../out/gta_long_16x9.mp4 --start 5 --gain -15 --skip 10.2 --tail 4 && rm ../out/gl_nomusic.mp4 && echo "OK long mixed"
cp ../out/elden_short_9x16.mp4 ../out/es_nomusic.mp4 && python3 ../src/mix.py ../out/es_nomusic.mp4 $MU/synthwavehouse.ogg ../out/elden_short_9x16.mp4 --start 16 --gain -13 && rm ../out/es_nomusic.mp4 && echo "OK elden short mixed"
r EldenWalk ../out/ew_raw.mp4 && python3 "$M" ../out/ew_raw.mp4 ../out/elden_walkthrough.mp4 >/dev/null && rm ../out/ew_raw.mp4
echo V2_DONE
