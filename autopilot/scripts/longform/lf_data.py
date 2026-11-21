#!/usr/bin/env python3
"""lf_data.py <P>: weekly Top 10 data for the long video published on date P (YYYY-MM-DD).
Source: Steam's own most-played chart (ISteamChartsService/GetMostPlayedGames: weekly rollup, peak_in_game) + store
appdetails (cc=us&l=english). Ranked by peak players, PAID games only: the video is about whether a game is worth the
money, so free-to-play games and non-game apps (Wallpaper Engine) are left out (the 22 Nov episode used the same rule).
Every fact and verdict is computed from these numbers; nothing is written by hand. Writes autopilot/longform/<P>/data.json."""
import sys, json, re, time, datetime as dt, urllib.request
from pathlib import Path
AP = Path(__file__).resolve().parents[2]; P = sys.argv[1]; OUT = AP / "longform" / P; OUT.mkdir(parents=True, exist_ok=True)
def get(u):
    for i in range(4):
        try: return json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read())
        except Exception as e: err = e; time.sleep(3 + 5 * i)
    raise err
resp = get("https://api.steampowered.com/ISteamChartsService/GetMostPlayedGames/v1/")["response"]
week_end = dt.datetime.fromtimestamp(resp["rollup_date"], dt.timezone.utc).date()
NOT_GAME = {"Animation & Modeling", "Utilities", "Design & Illustration", "Video Production", "Audio Production", "Photo Editing",
            "Software Training", "Web Publishing", "Game Development", "Education", "Accounting"}
GENERIC = {"Indie", "Early Access", "Free To Play", "Massively Multiplayer", "Casual", "Adventure"}
games = []
for x in sorted(resp["ranks"], key=lambda r: -r["peak_in_game"]):
    if len(games) == 10: break
    d = get(f"https://store.steampowered.com/api/appdetails?appids={x['appid']}&cc=us&l=english").get(str(x["appid"]), {})
    time.sleep(0.4)
    if not d.get("success"): continue
    d = d["data"]; po = d.get("price_overview")
    genres = [g["description"] for g in d.get("genres", [])]
    if d.get("type") != "game" or d.get("is_free") or not po or NOT_GAME & set(genres): continue
    movies = [m for m in d.get("movies", []) if m.get("hls_h264") and not re.search(  # talking heads, not gameplay (WARDOGS "Game Mode Explained", 21 Nov)
        r"pre-?load|pre-?order|teaser|explained|interview|dev(eloper)? ?diar|behind the|q ?& ?a|podcast|director|commentary|developer", m["name"], re.I)]
    if not movies: print("skip (no trailer):", d["name"]); continue
    rel = None
    for fmt in ("%b %d, %Y", "%d %b, %Y", "%B %d, %Y", "%b %Y"):
        try: rel = dt.datetime.strptime(d.get("release_date", {}).get("date", ""), fmt).date(); break
        except ValueError: pass
    name = re.sub(r"[™®©]", "", d["name"]).strip()
    name = re.split(r"\s+[-–:]\s+", name)[0] if len(name) > 26 else name      # "Probably Stolen - Cyberpunk Shopkeeper Sim"
    g2 = [g for g in genres if g not in GENERIC] or genres[:1]
    games.append({"appid": x["appid"], "name": name, "full_name": d["name"], "peak": x["peak_in_game"], "chart_rank": x["rank"],
                  "last_week_rank": x.get("last_week_rank"), "price": po["final_formatted"], "initial": po["initial_formatted"] or po["final_formatted"],
                  "discount": po.get("discount_percent", 0), "price_cents": po["final"], "meta": (d.get("metacritic") or {}).get("score"),
                  "reviews": (d.get("recommendations") or {}).get("total") or 0, "released": rel.isoformat() if rel else None,
                  "early_access": "Early Access" in genres, "genre": " ".join(g2[:2]) if len(" ".join(g2[:2])) <= 18 else g2[0],
                  "dev": (d.get("developers") or ["?"])[0], "movies": [[m["name"], m["hls_h264"]] for m in sorted(movies, key=lambda m: bool(re.search(r"ESRB|PEGI|rating", m["name"], re.I)))[:8]]})
    print(len(games), x["peak_in_game"], name, po["final_formatted"])
if len(games) < 10: sys.exit(f"only {len(games)} paid games found")

# ---- facts + verdict, all from the numbers above ----
fmt_n = lambda n: f"{n:,}"
def age_days(g): return (week_end - dt.date.fromisoformat(g["released"])).days if g["released"] else None
def rel_label(g):
    if not g["released"]: return "?"
    r = dt.date.fromisoformat(g["released"]); return r.strftime("%-d %b %Y") if age_days(g) < 120 else r.strftime("%b %Y")
paid = sorted(games, key=lambda g: -g["peak"])
most_rev = max(paid, key=lambda g: g["reviews"]); cheapest = min(paid, key=lambda g: g["price_cents"])
newest = max([g for g in paid if g["released"]], key=lambda g: g["released"], default=None)
oldest = min([g for g in paid if g["released"]], key=lambda g: g["released"], default=None)
metas = [g for g in paid if g["meta"]]; best_meta = max(metas, key=lambda g: g["meta"], default=None); worst_meta = min(metas, key=lambda g: g["meta"], default=None)
used_verdicts = set(); entries = []
for i, g in enumerate(paid):
    rank = i + 1; facts = []; a = age_days(g)
    if rank == 1: facts.append(f"{round((g['peak'] / paid[1]['peak'] - 1) * 100)}% more players than number two")
    if g["discount"]: facts.append(f"{g['discount']}% off this week: {g['price']} instead of {g['initial']}")
    if a is not None and a <= 60: facts.append(f"Out {dt.date.fromisoformat(g['released']).strftime('%-d %b')}. Top 10 on Steam already")
    elif a is not None and a >= 5 * 365: facts.append(f"Released in {g['released'][:4]} and still in the top 10")
    if g is most_rev: facts.append(f"{fmt_n(g['reviews'])} Steam reviews: the most on this list")
    if g is best_meta and len(metas) > 1: facts.append(f"Metacritic {g['meta']}: the best score on this list")
    if g is worst_meta and len(metas) > 1 and g is not best_meta: facts.append(f"Lowest Metacritic here ({g['meta']}), number {rank} for players")
    lw = g.get("last_week_rank")
    if lw and lw - g["chart_rank"] >= 3: facts.append(f"Up {lw - g['chart_rank']} places on Steam's chart this week")
    if g["early_access"]: facts.append("Still in Early Access")
    if len(facts) < 2 and g["reviews"]: facts.append(f"{fmt_n(g['reviews'])} Steam reviews")
    if len(facts) < 2 and g["meta"]: facts.append(f"Metacritic {g['meta']}")
    if len(facts) < 2: facts.append(f"{fmt_n(g['peak'])} players at its peak this week")
    cands = []
    if g is cheapest: cands.append("Cheapest game on the list")
    if g is newest: cands.append("Newest game on the list")
    if g["discount"] >= 40: cands.append("Buy it on sale this week")
    if g["meta"] and g["meta"] >= 85: cands.append("Critics love it, players too")
    if g is oldest: cands.append("Oldest game here and still played")
    if g["price_cents"] >= 5999 and a and a >= 2 * 365: cands.append("Full price and still selling")
    if g["early_access"]: cands.append("Early Access, but already huge")
    if g["price_cents"] <= 2000: cands.append(f"Top 10 for under ${g['price_cents'] / 100:.0f}" if g["price_cents"] % 100 else f"Top 10 for {g['price']}")
    if g is most_rev: cands.append("The most reviewed game here")
    cands.append(f"{g['price']} for a top {rank} game")
    v = next((c for c in cands if c not in used_verdicts), cands[-1]); used_verdicts.add(v)
    entries.append({"key": f"g{rank}", "rank": rank, "appid": g["appid"], "name": g["name"], "dev": g["dev"], "genre": g["genre"],
                    "released": rel_label(g), "players": g["peak"], "price": g["price"], **({"priceNote": f"-{g['discount']}%"} if g["discount"] else {}),
                    "reviews": fmt_n(g["reviews"]), **({"meta": str(g["meta"])} if g["meta"] else {}),
                    "facts": facts[:2] if rank > 1 else facts[:3], "verdict": v, "movies": g["movies"]})
entries.sort(key=lambda e: -e["rank"])
json.dump({"week_end": week_end.isoformat(), "publish": P, "entries": entries}, open(OUT / "data.json", "w"), indent=1)
for e in entries: print(e["rank"], e["name"], e["players"], e["price"], "|", " / ".join(e["facts"]), "|", e["verdict"])
