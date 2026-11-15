#!/usr/bin/env python3
"""Two-pass `loudnorm` audio mastering — bring a mix to a broadcast/platform loudness target
(EBU R128) instead of a crude peak-normalize. Distilled from the FFmpeg-mastering practice in the
affaan-m / mcpmarket video skills, adapted to this repo's env (ffmpeg at ~/.local/bin, no ffprobe).

Why: peak-normalizing to -1 dB leaves perceived loudness all over the place. loudnorm targets
*integrated* loudness (LUFS) + true-peak, so the narration sits at a consistent, platform-correct
level. Defaults to YouTube's target (-14 LUFS, -1 dBTP).

Two passes: pass 1 measures, pass 2 applies linearly with those measurements (highest quality).

⚠️ Hand it a VIDEO and it used to silently re-encode the picture at ffmpeg's defaults (~1 Mb/s) and
write 96 kHz audio — a quality loss nobody asked for (found in the T6 tutorial-tools build,
2026-09-12). Now: audio outputs are audio-only (`-vn`), video outputs copy the video stream
untouched (`-c:v copy`), and the sample rate is pinned to 48 kHz.

Usage:
  python tools/audio/master.py in.wav out.mp3                       # YouTube master (-14 LUFS)
  python tools/audio/master.py in.wav out.wav --i -16 --tp -1.5     # broadcast/podcast (-16 LUFS)
  python tools/audio/master.py in.mp4 out.mp4                       # master the audio, copy the video
  python tools/audio/master.py in.wav out.mp3 --json                # print measured + applied
"""
from __future__ import annotations
import argparse, json, re, shutil, subprocess, sys
from pathlib import Path

VIDEO_SUFFIXES = {".mp4", ".mov", ".mkv", ".webm", ".m4v"}


def ffmpeg() -> str:
    for c in ("ffmpeg", str(Path.home() / ".local/bin/ffmpeg")):
        if shutil.which(c) or Path(c).exists():
            return c
    return "ffmpeg"


def _measure(inp: str, I: float, TP: float, LRA: float) -> dict:
    """Pass 1 — analyse loudness, return loudnorm's measured_* JSON."""
    r = subprocess.run(
        [ffmpeg(), "-hide_banner", "-i", inp,
         "-af", f"loudnorm=I={I}:TP={TP}:LRA={LRA}:print_format=json",
         "-f", "null", "-"],
        capture_output=True, text=True,
    )
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr, re.DOTALL)
    if not m:
        raise RuntimeError("loudnorm pass-1 produced no measurements:\n" + r.stderr[-500:])
    return json.loads(m.group(0))


def master(inp: str, out: str, I: float = -14.0, TP: float = -1.0, LRA: float = 11.0,
           bitrate: str = "192k", sample_rate: int = 48000) -> dict:
    meas = _measure(inp, I, TP, LRA)
    af = (f"loudnorm=I={I}:TP={TP}:LRA={LRA}:linear=true"
          f":measured_I={meas['input_i']}:measured_TP={meas['input_tp']}"
          f":measured_LRA={meas['input_lra']}:measured_thresh={meas['input_thresh']}"
          f":offset={meas['target_offset']}")
    out_suffix = Path(out).suffix.lower()
    keeps_video = out_suffix in VIDEO_SUFFIXES
    # Never let ffmpeg re-encode the picture just because we're touching the audio.
    stream = ["-map", "0:v:0", "-map", "0:a:0", "-c:v", "copy"] if keeps_video else ["-vn"]
    codec = ["-b:a", bitrate] if out_suffix in {".mp3", ".m4a", ".aac", ".mp4", ".mov"} else []
    r = subprocess.run([ffmpeg(), "-y", "-hide_banner", "-i", inp, "-af", af,
                        *stream, "-ar", str(sample_rate), *codec, out],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("loudnorm pass-2 failed:\n" + r.stderr[-500:])
    return {"target_I": I, "target_TP": TP,
            "measured_I": float(meas["input_i"]), "measured_TP": float(meas["input_tp"]),
            "measured_LRA": float(meas["input_lra"]), "sample_rate": sample_rate,
            "video": "copied" if keeps_video else "none", "output": out}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input"); ap.add_argument("output")
    ap.add_argument("--i", type=float, default=-14.0, help="integrated loudness target LUFS (YouTube -14)")
    ap.add_argument("--tp", type=float, default=-1.0, help="true-peak ceiling dBTP")
    ap.add_argument("--lra", type=float, default=11.0, help="loudness range")
    ap.add_argument("--bitrate", default="192k")
    ap.add_argument("--sample-rate", type=int, default=48000, help="output sample rate (48k = video standard)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    res = master(a.input, a.output, a.i, a.tp, a.lra, a.bitrate, a.sample_rate)
    if a.json:
        print(json.dumps(res, indent=2))
    else:
        print(f"mastered → {res['output']}  (measured {res['measured_I']:.1f} LUFS → target {res['target_I']:.0f}, "
              f"TP {res['measured_TP']:.1f}→{res['target_TP']:.0f} dBTP, {res['sample_rate']} Hz, video {res['video']})")


if __name__ == "__main__":
    main()
