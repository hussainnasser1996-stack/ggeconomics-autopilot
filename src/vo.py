#!/usr/bin/env python3
"""Script JSON -> Kokoro VO wav + timeline (per-line + per-word from Whisper round-trip QA)."""
import sys, json, numpy as np, soundfile as sf
from pathlib import Path
spec = json.load(open(sys.argv[1])); out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
from kokoro import KPipeline
kp = KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M")
SR = 24000; buf = []; t = 0.35; lines = []
buf.append(np.zeros(int(0.35 * SR)))
for ln in spec["lines"]:
    a = np.concatenate([np.asarray(x) for _, _, x in kp(ln.get("say", ln["text"]), voice=spec["voice"], speed=spec["speed"])])
    # trim silence
    idx = np.where(np.abs(a) > 0.01)[0]; a = a[max(0, idx[0] - 600): idx[-1] + 1200]
    d = len(a) / SR
    lines.append({"id": ln["id"], "text": ln["text"], "start": round(t, 3), "end": round(t + d, 3)})
    buf += [a, np.zeros(int(spec["gap"] * SR))]; t += d + spec["gap"]
y = np.concatenate(buf + [np.zeros(int(0.5 * SR))])
sf.write(out / "vo.wav", y, SR)
# Whisper round-trip: word timings for captions + pronunciation QA
from faster_whisper import WhisperModel
m = WhisperModel("small.en", device="cpu", compute_type="int8")
import librosa
y16 = librosa.resample(y.astype(np.float32), orig_sr=SR, target_sr=16000)
segs, _ = m.transcribe(y16, word_timestamps=True)
words = [{"w": w.word.strip(), "s": round(w.start, 3), "e": round(w.end, 3)} for s in segs for w in s.words]
heard = " ".join(w["w"] for w in words)
# --- align: captions use the SCRIPT's spelling, Whisper's timing ---
import re, difflib
script = [t for ln in spec["lines"] for t in ln.get("say", ln["text"]).split()]
norm = lambda x: re.sub(r"[^a-z0-9]", "", x.lower())
a = [norm(t) for t in script]; b = [norm(w["w"]) for w in words]
out_w = []
for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
    if op == "equal":
        for k in range(i2 - i1): out_w.append({"w": script[i1 + k], "s": words[j1 + k]["s"], "e": words[j1 + k]["e"]})
    elif i2 > i1:
        if j2 > j1: s0, e0 = words[j1]["s"], words[j2 - 1]["e"]
        else:
            s0 = out_w[-1]["e"] if out_w else 0.0; e0 = words[j1]["s"] if j1 < len(words) else s0 + 0.3 * (i2 - i1)
        n = i2 - i1
        for k in range(n): out_w.append({"w": script[i1 + k], "s": round(s0 + (e0 - s0) * k / n, 3), "e": round(s0 + (e0 - s0) * (k + 1) / n, 3)})
words = out_w
json.dump({"duration": round(len(y) / SR, 3), "lines": lines, "words": words}, open(out / "timeline.json", "w"), indent=1)
print("duration", round(len(y) / SR, 2)); print("HEARD:", heard)
