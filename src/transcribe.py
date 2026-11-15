import sys, json
from faster_whisper import WhisperModel
wav, out = sys.argv[1], sys.argv[2]
m = WhisperModel(sys.argv[3] if len(sys.argv) > 3 else "small.en", device="cpu", compute_type="int8", cpu_threads=4)
import soundfile as sf
audio, _sr = sf.read(wav, dtype="float32")
segs, _ = m.transcribe(audio, word_timestamps=True, vad_filter=True)
res = [{"start": s.start, "end": s.end, "text": s.text.strip(),
        "words": [{"w": w.word, "s": w.start, "e": w.end} for w in s.words]} for s in segs]
json.dump(res, open(out, "w"), indent=1)
open(out.replace(".json", ".txt"), "w").write("\n".join(f"[{r['start']:7.1f}] {r['text']}" for r in res))
print("done", len(res))
