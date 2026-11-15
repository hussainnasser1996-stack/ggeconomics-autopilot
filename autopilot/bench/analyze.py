import sys, json, subprocess, re, glob, os
import numpy as np, cv2, soundfile as sf
from scenedetect import open_video, SceneManager
from scenedetect.detectors import ContentDetector
from faster_whisper import WhisperModel
m = WhisperModel("base.en", device="cpu", compute_type="int8")
rows = []; strips = []
for p in sorted(glob.glob("work/bench/vids/*.mp4")):
    vid = os.path.basename(p)[:-4]
    dur = float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",p],capture_output=True,text=True).stdout)
    v = open_video(p); sm = SceneManager(); sm.add_detector(ContentDetector(threshold=27, min_scene_len=6)); sm.detect_scenes(v, show_progress=False)
    cuts = max(0, len(sm.get_scene_list()) - 1)
    wav = f"/tmp/bench_{vid}.wav"; subprocess.run(["ffmpeg","-v","error","-y","-i",p,"-ac","1","-ar","16000",wav])
    a, _ = sf.read(wav, dtype="float32")
    segs, _ = m.transcribe(a, word_timestamps=True)
    words = [w for s in segs for w in s.words]
    text = " ".join(w.word.strip() for w in words)
    first = " ".join(w.word.strip() for w in words if w.start < 3.0)
    t0 = words[0].start if words else None
    lufs = re.search(r"I:\s+(-?[\d.]+) LUFS", subprocess.run(["ffmpeg","-hide_banner","-i",p,"-af","ebur128","-f","null","-"],capture_output=True,text=True).stderr)
    rows.append({"id": vid, "dur": round(dur,1), "cuts": cuts, "cuts_per_s": round(cuts/dur,2), "avg_shot_s": round(dur/(cuts+1),2),
                 "wpm": round(len(words)/dur*60) if words else 0, "first_word_s": round(t0,2) if t0 is not None else None,
                 "lufs": float(lufs.group(1)) if lufs else None, "hook_3s": first, "text": text})
    cap = cv2.VideoCapture(p); tiles=[]
    for t in [0,0.5,1,1.5,2,3,5]:
        cap.set(cv2.CAP_PROP_POS_MSEC, t*1000); ok, f = cap.read()
        f = cv2.resize(f, (135, 240)) if ok else np.zeros((240,135,3),np.uint8); tiles.append(f)
    s = np.hstack(tiles); cv2.putText(s, vid[:11], (3,14), 0, 0.45, (58,255,212), 1); strips.append(s)
cv2.imwrite("work/bench/hooks.jpg", np.vstack(strips))
json.dump(rows, open("work/bench/metrics.json","w"), indent=1)
for r in rows:
    print(f"{r['id']:12s} dur {r['dur']:5.1f}s cuts {r['cuts']:3d} ({r['cuts_per_s']:.2f}/s, shot {r['avg_shot_s']:.1f}s) wpm {r['wpm']:3d} firstword {r['first_word_s']}s lufs {r['lufs']}")
    print(f"   HOOK: {r['hook_3s']}")
