#!/usr/bin/env python3
"""Broadcast-style music post-mix: duck music under the programme audio, then master to -14 LUFS.

  python3 src/mix.py in.mp4 music.ogg out.mp4 [--start 16] [--gain -14] [--fadein 0.5] [--tail 2.5] [--skip 0]

--skip N: keep the first N seconds music-free (e.g. ident / cold open has its own sound).
The programme audio (VO + SFX) is the sidechain key: whenever it speaks, the music dips ~8 dB."""
import argparse, subprocess, json, sys
from pathlib import Path
ap = argparse.ArgumentParser()
ap.add_argument("inp"); ap.add_argument("music"); ap.add_argument("out")
ap.add_argument("--start", type=float, default=0); ap.add_argument("--gain", type=float, default=-14)
ap.add_argument("--fadein", type=float, default=0.6); ap.add_argument("--tail", type=float, default=2.5)
ap.add_argument("--skip", type=float, default=0)
a = ap.parse_args()
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", a.inp], capture_output=True, text=True).stdout)
mlen = dur - a.skip
fc = (
    f"[1:a]atrim=0:{mlen},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,"
    f"highpass=f=45,equalizer=f=3000:t=q:w=1.2:g=-5,volume={a.gain}dB,"
    f"afade=t=in:d={a.fadein},afade=t=out:st={max(0, mlen - a.tail)}:d={a.tail},adelay={int(a.skip*1000)}|{int(a.skip*1000)}[mus];"
    f"[0:a]aresample=48000,aformat=channel_layouts=stereo,asplit=2[prog][key];"
    f"[mus][key]sidechaincompress=threshold=0.02:ratio=6:attack=15:release=400:makeup=1[duck];"
    f"[prog][duck]amix=inputs=2:normalize=0:duration=first[mix]"
)
tmp = Path(a.out).with_suffix(".premaster.mp4")
r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a.inp, "-stream_loop", "-1", "-ss", str(a.start), "-i", a.music,
                    "-filter_complex", fc, "-map", "0:v", "-map", "[mix]", "-c:v", "copy", "-c:a", "aac", "-b:a", "320k", "-ar", "48000", str(tmp)])
if r.returncode: sys.exit("mix failed")
M = str(Path(__file__).resolve().parents[1] / "tools/audio/master.py")
subprocess.run(["python3", M, str(tmp), a.out], check=True, capture_output=True); tmp.unlink()
print("mixed ->", a.out)
