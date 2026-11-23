#!/usr/bin/env python3
"""pick_music.py <D>  — choose today's music bed and where it starts.
Rotates assets/music/lib (Kevin MacLeod / incompetech.com, CC BY 4.0: credit goes into the caption automatically),
never repeats any of the last 4 posts' tracks, and starts the track at its first big energy rise (the "drop") so the
hook lands on impact, not an intro. Writes queue/D/music.json {file, start, credit}."""
import sys, json, random, glob
from pathlib import Path
import numpy as np, librosa
GN = Path(__file__).resolve().parents[2]; D = sys.argv[1]; Q = GN / "autopilot/queue" / D
lib = sorted(glob.glob(str(GN / "assets/music/lib/*.m4a")))
recent = []
for q in sorted((GN / "autopilot/queue").iterdir(), reverse=True):
    if q.name != D and (q / "music.json").exists(): recent.append(json.load(open(q / "music.json"))["file"])
    if len(recent) >= 4: break
pool = [f for f in lib if Path(f).name not in recent] or lib
post = json.load(open(Q / "post.json")) if (Q / "post.json").exists() else {}
fr = json.load(open(Q / "footage_resolved.json")) if (Q / "footage_resolved.json").exists() else {}
is_edit = (Q / "script.json").exists() and json.load(open(Q / "script.json")).get("mode") == "edit"
GAME = (post.get("music") == "game" or (is_edit and post.get("music") != "library")) and fr   # edits default to the game's soundtrack
# the Steam-screenshot reel (resolve_footage) has a silent track: mixing it gave silence and master.py failed (23c, 23 Nov)
if GAME and str(fr.get("id", "")).startswith("steamshots:"): GAME = False
if GAME:   # the trailer's own score/song (owner's call 16 Nov: reach > monetization; credit it). monitor checks for blocks.
    import subprocess
    f = str(GN / f"work/{fr['tag']}_music.m4a")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(GN / f"work/{fr['tag']}.mp4"), "-vn", "-c:a", "aac", "-b:a", "192k", f], check=True)
else:
    f = random.Random(D).choice(pool)
# how long the bed must run = the video length (timeline) + tail
tlp = GN / f"studio/public/vo/{json.load(open(Q / 'script.json'))['id']}/timeline.json" if (Q / "script.json").exists() else None
need = (json.load(open(tlp))["duration"] + 3) if tlp and tlp.exists() else 30
speech = []
if GAME:   # game audio can contain dialogue/narration: find speech so the bed window avoids it
    from faster_whisper import WhisperModel
    a16, _ = librosa.load(f, sr=16000, mono=True)
    segs, _ = WhisperModel("base.en", device="cpu", compute_type="int8").transcribe(a16, vad_filter=True)
    speech = [(x.start, x.end) for x in segs]
y, sr = librosa.load(f, sr=22050, mono=True, duration=None if GAME else 100)
if GAME and float(np.sqrt(np.mean(y ** 2))) < 0.005:         # a silent/near-silent trailer track: never a silent Short
    GAME = False; f = random.Random(D).choice(pool); speech = []
    y, sr = librosa.load(f, sr=22050, mono=True, duration=100)
rms = librosa.feature.rms(y=y, hop_length=512)[0]; t = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=512)
win = int(2.0 * sr / 512); e = np.convolve(rms, np.ones(win) / win, mode="same")
rise = np.diff(e, prepend=e[0]); lim = t < max(10, t[-1] - 40)               # leave >= 40 s of music after the start
_, beats = librosa.beat.beat_track(y=y, sr=sr); bt = librosa.frames_to_time(beats, sr=sr)
def overlap(a, b): return sum(max(0, min(b, e2) - max(a, s2)) for s2, e2 in speech)
if GAME:
    # candidate starts on beats; must leave `need` seconds; score = energy rise, heavy penalty for speech in the window
    cands = [b for b in bt if b + need <= t[-1]] or [0.0]
    def sc(b):
        k = int(np.searchsorted(t, b)); return float(rise[min(k, len(rise) - 1)] + e[min(k, len(e) - 1)]) - 10 * overlap(b, b + need) / need
    start = max(cands, key=sc)
    if overlap(start, start + need) / need > 0.15:          # no clean window: fall back to the library bed
        GAME = False; f = random.Random(D).choice(pool); speech = []
        y, sr = librosa.load(f, sr=22050, mono=True, duration=100)
        rms = librosa.feature.rms(y=y, hop_length=512)[0]; t = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=512)
        e = np.convolve(rms, np.ones(win) / win, mode="same"); rise = np.diff(e, prepend=e[0]); lim = t < max(10, t[-1] - 40)
        _, beats = librosa.beat.beat_track(y=y, sr=sr); bt = librosa.frames_to_time(beats, sr=sr)
if not GAME:
    i = int(np.argmax(np.where(lim & (e > np.percentile(e, 60)), rise, -1)))
    start = float(bt[bt <= t[i]][-1]) if len(bt[bt <= t[i]]) else float(t[i])       # snap to a beat
title = Path(f).stem.replace("_", " ").title()
credit = (f"Music: official trailer audio ({fr.get('label', '').replace('.mp4', '').replace('_', ' ')}){' · ' + fr['credit'].replace('GAMEPLAY: ', '') if fr.get('credit') else ''}"
          if GAME else f'Music: "{title}" by Kevin MacLeod (incompetech.com), CC BY 4.0')
out = {"file": Path(f).name, "path": str(Path(f).relative_to(GN)), "start": round(max(0.0, start - 0.25), 2), "credit": credit, "game": bool(GAME)}
json.dump(out, open(Q / "music.json", "w"), indent=1); print("music:", out)
