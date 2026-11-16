#!/usr/bin/env python3
"""library.py            — list the footage library (GitHub release "footage-library" of this repo)
   library.py <name>     — download one file to work/lib/<name> and print its path
Then: fetch_footage.py "<label>" d_<D> --url work/lib/<name>
For games YouTube won't serve to the cloud and Steam doesn't have (e.g. GTA VI)."""
import sys, json, subprocess
from pathlib import Path
R = "hussainnasser1996-stack/ggeconomics-autopilot"
if len(sys.argv) < 2:
    a = json.loads(subprocess.run(["gh", "release", "view", "footage-library", "-R", R, "--json", "assets"], capture_output=True, text=True, check=True).stdout)
    for x in a["assets"]: print(f"{x['name']:50s} {x['size']/1e6:8.0f} MB")
    sys.exit()
d = Path(__file__).resolve().parents[2] / "work/lib"; d.mkdir(parents=True, exist_ok=True)
subprocess.run(["gh", "release", "download", "footage-library", "-R", R, "-p", sys.argv[1], "-D", str(d), "--clobber"], check=True)
print(d / sys.argv[1])
