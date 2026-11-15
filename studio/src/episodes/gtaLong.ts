import { LongSpec } from "../news/LongForm";
import { C } from "../brand";
import timeline from "../../public/vo/gta_long/timeline.json";
import clips from "./gta_long_clips.json";

// Sources (checked 2026-11-15)
//  price / date / platforms / 30fps / Xbox cloud 1am ET / Zelnick quotes / Take-Two Q2 + guidance — TNW (Reuters, Variety, IGN)
//  >$1B est. digital pre-orders — Sensor Tower via Yahoo Finance / TweakTown / BigGo (unconfirmed by Take-Two)
//  4,700+ staff; "not quite as much as the Burj Khalifa" (~$1.5B est.); 500M franchise units; GTA V 230-235M;
//  GTA Online ~$500M/yr; online mode comes later — Bloomberg Originals video (work/v1_transcript.txt 99s, 121s, 300s, 304s/637s, 630s, 598s)
export const gtaLong: LongSpec = {
  title: "GTA VI: The Billion-Dollar Bet",
  vo: "vo/gta_long/vo.wav",
  timeline: timeline as any,
  noBed: true,
  clips: clips as any,
  credit: "GAMEPLAY: ROCKSTAR GAMES · DATA: SENSOR TOWER, TAKE-TWO, BLOOMBERG",
  cold: {
    src: "v1", from: 18.9, dur: 6.2, source: "VIA BLOOMBERG ORIGINALS",
    words: [
      [" Grand", 19.05], [" Theft", 19.12], [" Auto", 19.19], [" 6", 19.43], [" is", 19.63], [" going", 19.85], [" to", 20.03], [" be", 20.21],
      [" a", 20.33], [" black", 20.49], [" hole", 20.79], [" of", 21.13], [" people's", 21.53], [" attention,", 21.95], [" of", 22.59],
      [" people's", 22.63], [" money,", 23.19], [" of", 23.87], [" people's", 23.91], [" time.", 24.31],
    ].map(([w, s]) => ({ w: w as string, s: s as number, e: (s as number) + 0.3 })),
  },
  chapters: [
    { line: "c1", n: "01", title: "THE PRE-ORDER" },
    { line: "c2", n: "02", title: "THE BUDGET" },
    { line: "c3", n: "03", title: "THE QUARTER" },
    { line: "c4", n: "04", title: "WHAT TO WATCH" },
  ],
  cards: [
    { kind: "date", line: "l1", small: "PS5 · XBOX SERIES X|S", big: "NOV 19" },
    { kind: "big", line: "l2", value: "$1B+", label: "est. digital pre-orders", note: "Sensor Tower estimate\nnot confirmed by Take-Two" },
    { kind: "pair", line: "l3", a: { value: "$79.99", label: "STANDARD" }, b: { value: "$99.99", label: "ULTIMATE" } },
    { kind: "big", line: "l4", value: "<$1.5B", label: "budget, by Rockstar's hint", note: "\"not quite as much as the Burj Khalifa\"\nRockstar to Bloomberg", color: C.cyan },
    { kind: "big", line: "l5", value: "4,700+", label: "Rockstar employees", note: "≈2× when work began · via Bloomberg", countTo: 4700, suffix: "+" },
    { kind: "pair", line: "l6", a: { value: "500M", label: "SERIES, ALL TIME" }, b: { value: "230M+", label: "GTA V ALONE" }, note: "units · via Bloomberg" },
    { kind: "big", line: "l7", value: "−18%", label: "Take-Two net bookings", note: "Jul–Sep 2026 · $1.6B", color: C.coral },
    {
      kind: "bars", line: "l8", title: "TAKE-TWO NET BOOKINGS", unit: "$B",
      bars: [
        { label: "JUL–SEP\nACTUAL", lo: 1.6, color: C.dim, text: "$1.6B" },
        { label: "OCT–DEC\nGUIDANCE", lo: 3.35, hi: 3.5, color: C.lime, text: "$3.35–3.5B" },
      ],
    },
    { kind: "quote", line: "l9", text: "We tend to avoid claiming success before it occurs.", who: "STRAUSS ZELNICK, TAKE-TWO CEO" },
    { kind: "date", line: "l10", small: "XBOX CLOUD OPENS", big: "1 AM ET", note: "30 fps target on both consoles" },
    { kind: "big", line: "l11", value: "~$500M", label: "GTA Online, per year", note: "GTA V era · via Bloomberg" },
  ],
  endTiles: ["▶ GTA VI IN 30 SECONDS", "▶ NEXT: LAUNCH-DAY VERDICT"],
};
