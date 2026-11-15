#!/usr/bin/env python3
"""notify.py "<message>" [high]  — push to Husain's phone via ntfy (topic in config.json)."""
import sys, json, urllib.request
from pathlib import Path
t = json.load(open(Path(__file__).resolve().parents[1] / "config.json")).get("ntfy_topic")
if not t: sys.exit("no ntfy_topic")
req = urllib.request.Request(f"https://ntfy.sh/{t}", data=sys.argv[1].encode(), headers={"Title": "GG Economics",
      "Priority": "high" if len(sys.argv) > 2 else "default", "Tags": "video_game"})
urllib.request.urlopen(req, timeout=20); print("sent")
