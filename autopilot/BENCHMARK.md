# Benchmark: top gaming-news Shorts vs GG Economics (2026-11-15)

Method: YouTube Data API search (8 queries, last 21 days, US, Shorts) → ranked by views → 8 downloaded for analysis
only (work/bench/, never reused) → measured: cuts/s, shot length, words per minute (Whisper), first-3s hook text,
loudness, and a strip of the first 5 s (work/bench/hooks.jpg) looked at frame by frame.

| Video | Views | Length | Cuts/s | WPM | LUFS | Hook (first 3 s) |
|---|---|---|---|---|---|---|
| Mark Tilbury: How GTA 6 Could Save You $5,000 | 6.9M | 30 s | 0.60 | 173 | −16.9 | "Buying GTA 6 can actually save you $5,000" |
| CarterPCs: Which console should I buy for GTA 6? | 5.9M | 29 s | 0.45 | 233 | −14.5 | "GTA 6 comes out in 12 days, and I still don't have…" |
| CarterPCs: The cheapest way to play GTA 6 | 3.4M | 25 s | 0.49 | 240 | −12.8 | "You can play GTA 6 on an Xbox One" |
| ByteTalkYT: Sony Wants To Buy Your PS5 Back | 2.9M | 19 s | 0.32 | 245 | −22.0 | "Apparently Sony wants to buy your PS5 back" |
| Kriss K3B: What Happened to My GTA 6 Investment? | 2.8M | 69 s | 0.68 | 154 | −7.7 | (personal story) |
| Runtime Caffeine: GTA 6 Runs at 30 FPS | 1.9M | 70 s | 0.04 | 194 | −14.0 | "Even the PS5 Pro runs GTA 6 at 30 frames" |
| JtheSlopFrog: Today is a fun day in gaming | 1.7M | 79 s | 0.81 | 180 | −11.9 | "That was truly an amazing day for gaming" |
| jacobweeby: GTA 6 New Zealand trick explained | 7.6M | 63 s | 0.29 | 182 | −13.7 | "We at Rockstar are happy to announce…" |
| **GG Economics v1 (before)** | — | 29.5 s | 0.68 | **169** | −14.1 | "GTA 5 made a billion dollars in three days" |
| **GG Economics v2 (after)** | — | 21.8 s | 0.68 | **209** | −14 | "GTA 6 might make a billion dollars before you can even play it" |

## What the winners do (applied)
1. **A persistent headline** with the topic, readable from frame 0 to the end → `spec.headline` (`A |highlight| B`).
2. **The hook is about the viewer**: you / your / your money / what you should buy. Not company numbers in the 3rd person.
3. **Fast delivery: 200–245 wpm** → Kokoro speed 1.25, gap 0.12 (our v1 was 169 wpm).
4. **Frame 0 already shows the hook number** → the first card is pre-rolled.
5. **1–2 word captions, very large** → chunks of 2, 88 px, weight 900.
6. **Length 20–30 s** for news.
7. **Buyer-intent topics win**: which console, cheapest way, trade-ins, performance, how to save. "Money" = the VIEWER's money first,
   industry money second.

## Not yet applied (backlog, in order of expected impact)
- A face or a character. 6 of 8 winners show a human; the faceless ones that work use a mascot (JtheSlopFrog) or very bold
  static graphics (Runtime Caffeine, ByteTalkYT). Option: a GG coin mascot puppeted with the news-anchor pipeline.
- Concrete objects on screen: the console, a price tag, a calculator (Tilbury's $5,000 calculator, ByteTalk's $400 tag).
- Titles in the winners' pattern: short claim + you/your ("Sony Wants To Buy Your PS5 Back Before GTA 6").
