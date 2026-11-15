import json, sys, cv2, numpy as np
tag, n = sys.argv[1], int(sys.argv[2]); mind = float(sys.argv[3]) if len(sys.argv) > 3 else 1.2
S = json.load(open(f"work/{tag}/shots.json"))
c = [s for s in S if s["dur"] >= mind and s["bright"] > 35]
for s in c: s["score"] = (min(s["motion"], 25) / 25) * 0.5 + (min(s["sharp"], 1500) / 1500) * 0.3 + (s["sat"] / 255) * 0.2
c.sort(key=lambda s: -s["score"]); top = c[:n]
imgs = [cv2.resize(cv2.imread(f"work/{tag}/th_{s['id']:04d}.jpg"), (288, 162)) for s in sorted(top, key=lambda s: s["id"])]
while len(imgs) % 8: imgs.append(np.zeros_like(imgs[0]))
cv2.imwrite(f"work/{tag}/top.jpg", np.vstack([np.hstack(imgs[r*8:(r+1)*8]) for r in range(len(imgs)//8)]))
print(len(c), "candidates")
