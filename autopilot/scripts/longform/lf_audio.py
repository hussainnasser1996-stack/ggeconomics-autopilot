#!/usr/bin/env python3
"""lf_audio.py <P>: the voice intro (Kokoro am_liam, the voice the owner approved on 21 Nov) + the hook + the music bed.
Three lines like the 22 Nov episode: hook (the #1 peak, rounded), how it's ranked, "#1 stays hidden". Whisper round-trip
checks every line was said right (fails the build if not). Music: 5 Kevin MacLeod tracks from assets/music/lib, rotated
by week, switching on the number cards for 9, 6, 3 and 1; music ducks to 0.3 under the voice (LongTop.tsx)."""
import sys, json, re, shutil, datetime as dt
from pathlib import Path
import numpy as np, soundfile as sf
GN = Path(__file__).resolve().parents[3]; AP = GN / "autopilot"; P = sys.argv[1]; L = AP / "longform" / P
spec = json.load(open(L / "spec.json")); E = spec["entries"]; one = next(e for e in E if e["rank"] == 1)
FPS = 30
# ---- hook: the #1 peak over blurred #1 footage (the 22 Nov intro) ----
c1 = max(one["clips"], key=lambda c: c["dur"])
spec["hook"] = {"sec": 5.5, "big": one["players"], "line": "people were playing ONE game at the same time this week", "ask": "WHICH ONE?",
                "clip": {"src": c1["src"], "from": c1["from"], "dur": 5.5}}
hook_sec = 5.5; cold = sum(c["dur"] for c in spec["cold"]); first_card = hook_sec + cold + spec["introSec"]
# ---- voice ----
n_round = f"{one['players'] // 1000 * 1000:,}"
LINES = [("hook", f"This week, {n_round} people were playing one game at the same time. Which one?"),
         ("how", "These are the 10 biggest games on Steam right now, ranked by peak players. For every game you get the price, the reviews, and whether it's worth the money."),
         ("go", "Number one stays hidden until the end. Let's start at number 10.")]
VO = GN / f"studio/public/vo/d_lf_{P}"; VO.mkdir(parents=True, exist_ok=True)
from kokoro import KPipeline
kp = KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M"); SR = 24000; lens = {}
for k, text in LINES:
    a = np.concatenate([np.asarray(x) for _, _, x in kp(text, voice="am_liam", speed=1.15)])
    idx = np.where(np.abs(a) > 0.01)[0]; a = a[max(0, idx[0] - 600): idx[-1] + 1200]
    sf.write(VO / f"{k}.wav", a, SR); lens[k] = round(len(a) / SR, 2)
from faster_whisper import WhisperModel
import librosa
m = WhisperModel("small.en", device="cpu", compute_type="int8"); qa = []; bad = []
norm = lambda s: re.sub(r"[^a-z0-9 ]", "", s.lower().replace(",", "")).split()
for k, text in LINES:
    y, _ = librosa.load(VO / f"{k}.wav", sr=16000)
    heard = " ".join(s.text for s in m.transcribe(y)[0]).strip()
    want, got = norm(text), norm(heard)
    miss = [w for w in want if w not in got]
    qa.append(f"{k}: SAID {text!r} | HEARD {heard!r} | missing {miss}")
    if len(miss) > 1: bad.append(k)
(L / "vo_qa.txt").write_text("\n".join(qa) + "\n"); print("\n".join(qa))
if bad: sys.exit(f"VO QA failed on {bad}")
go_at = round(first_card - lens["go"] - 3.2, 2)
spec["vo"] = [{"src": f"vo/d_lf_{P}/hook.wav", "at": 0.25, "len": lens["hook"]},
              {"src": f"vo/d_lf_{P}/how.wav", "at": round(max(6.4, 0.25 + lens["hook"] + 0.6), 2), "len": lens["how"]},
              {"src": f"vo/d_lf_{P}/go.wav", "at": go_at, "len": lens["go"]}]
if spec["vo"][1]["at"] + lens["how"] + 0.5 > go_at: sys.exit("VO lines overlap: the cold open is too short for the intro")
# ---- music ----
t = first_card; at = {}
for e in E: at[e["rank"]] = t; t += spec["cardSec"] + sum(c["dur"] for c in e["clips"])
total = t + spec["outroSec"]
POOL = ["raving_energy", "rocket", "killers", "volatile_reaction", "five_armies", "crusade", "exhilarate", "movement_proposition", "unholy_knight"]
KNOWN = {"raving_energy": 59.68, "rocket": 0.6, "killers": 3.0, "volatile_reaction": 16.0, "five_armies": 14.0}   # 22 Nov starts (ear-checked)
wk = dt.date.fromisoformat(P).isocalendar()[1]; pick = [POOL[(wk * 5 + i) % len(POOL)] for i in range(5)]
bounds = [0, at[9], at[6], at[3], at[1], total]; MUS = GN / "studio/public/music"; MUS.mkdir(parents=True, exist_ok=True); spec["music"] = []; titles = []
for i, name in enumerate(pick):
    src = GN / f"assets/music/lib/{name}.m4a"; shutil.copy(src, MUS / f"{name}.m4a")
    need = bounds[i + 1] - bounds[i] + 1; sr = 11025
    import subprocess
    y = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", str(src), "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True).stdout, np.float32); dur = len(y) / sr
    if name in KNOWN: st = KNOWN[name]
    else:                                                     # skip a quiet intro: first second at 60% of the median loudness
        rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=512)[0]; ok = np.where(rms >= 0.6 * np.median(rms))[0]
        st = float(ok[0] * 512 / sr) if len(ok) else 0.0
    st = round(max(0.0, min(st, dur - need)), 2)
    spec["music"].append({"src": f"music/{name}.m4a", "start": st, "at": round(bounds[i], 3)})
    titles.append(name.replace("_", " ").title())
spec["music_titles"] = titles
json.dump(spec, open(L / "spec.json", "w"), indent=1)
print("TOTAL", round(total, 1), "s; music", titles)
