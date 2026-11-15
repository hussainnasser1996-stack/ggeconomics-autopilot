#!/bin/zsh
# 1080p H.264 proxies with 1s GOP for fast random access + 48k wav for analysis
set -e
in="$1"; out="$2"
nice -n 10 ffmpeg -v error -y -i "$in" -vf "scale=-2:1080,fps=30" -c:v libx264 -preset veryfast -crf 18 -g 30 -pix_fmt yuv420p -c:a aac -b:a 192k -ar 48000 "$out"
nice -n 10 ffmpeg -v error -y -i "$out" -vn -ac 1 -ar 16000 "${out%.mp4}.wav"
