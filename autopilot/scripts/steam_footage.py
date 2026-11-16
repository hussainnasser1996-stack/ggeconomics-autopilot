#!/usr/bin/env python3
"""steam_footage.py "<game name>"  — official publisher trailers from the Steam store (no YouTube needed).
Prints the trailers with their HLS URL; then run:
  fetch_footage.py "<game> steam" d_<D> --url "<hls url>"
Games not on Steam (e.g. GTA VI before PC release) have none: pick a story about a game that is, or use YouTube."""
import sys, json, urllib.request, urllib.parse
q = sys.argv[1]
get = lambda u: json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read())
items = get("https://store.steampowered.com/api/storesearch/?cc=us&l=en&term=" + urllib.parse.quote(q))["items"][:4]
if not items: sys.exit("no Steam match")
for it in items:
    d = get(f"https://store.steampowered.com/api/appdetails?appids={it['id']}&filters=movies&cc=us&l=english").get(str(it["id"]), {})
    movies = (d.get("data") or {}).get("movies") or []
    print(f"\n{it['name']} (app {it['id']}): {len(movies)} trailers")
    for m in movies[:8]:
        u = m.get("hls_h264") or (m.get("mp4") or {}).get("max") or m.get("dash_h264")
        print(f"  - {m['name'][:60]}\n    {u}")
