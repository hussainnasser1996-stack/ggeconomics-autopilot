#!/usr/bin/env python3
"""keywords.py "<game>" "<topic words>" [more seeds...] — what people actually TYPE into YouTube search right now.
Expands each seed with YouTube autocomplete (and a-z / question / money modifiers), scores each phrase by how early and how
often it is suggested, and prints the top 15. Use the top phrases (verbatim) in titles, the first caption line and hashtags.
stdlib only; no API key. Writes nothing."""
import sys, json, urllib.request, urllib.parse, collections
seeds = [s for s in sys.argv[1:] if s.strip()]
if not seeds: sys.exit(__doc__)
game = seeds[0].lower()
mods = ["", " price", " cost", " how much", " is it worth", " sales", " ps5", " xbox", " pc", " vs", " why", " when"]
score, seen = collections.Counter(), collections.Counter()
def suggest(q):
    u = "https://suggestqueries.google.com/complete/search?client=firefox&ds=yt&hl=en&gl=us&q=" + urllib.parse.quote(q)
    try: return json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=15).read().decode("utf-8", "ignore"))[1]
    except Exception: return []
queries = [game + m for m in mods] + [s.lower() for s in seeds[1:]] + [f"{game} {s.lower()}" for s in seeds[1:]]
for q in dict.fromkeys(queries):
    for i, p in enumerate([x for x in suggest(q) if x.strip() != q.strip()]):   # drop the echo of the query itself
        score[p] += 10 - i; seen[p] += 1          # earlier suggestion = more searched; repeated across seeds = broader demand
top = sorted(score, key=lambda p: -(score[p] * (1 + 0.5 * (seen[p] - 1))))[:15]
for p in top: print(f"{score[p]:4d}  x{seen[p]}  {p}")
