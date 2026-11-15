import { ShortSpec } from "../news/NewsShort";
import { C } from "../brand";
import timeline from "../../public/vo/gta_short/timeline.json";
import clips from "./gta_clips.json";

// Facts (checked 2026-11-15):
//  - $79.99 / $99.99, launch 19 Nov 2026, PS5 + Xbox Series X|S — TNW / Rockstar
//  - Sensor Tower: >$1B est. digital pre-orders (not confirmed by Take-Two) — Yahoo Finance, TweakTown, BigGo
//  - Take-Two Jul–Sep 2026 net bookings $1.6B, -18% YoY; Oct–Dec guide $3.35–3.5B — Take-Two Q2 FY27 results via Reuters/TNW
//  - Zelnick quote from the Q2 earnings call — TNW
export const gtaShort: ShortSpec = {
  tag: "GTA VI · LAUNCH WEEK",
  topic: "GTA VI: the $1B pre-order",
  vo: "vo/gta_short/vo.wav",
  timeline: timeline as any,
  noBed: true,
  credit: "GAMEPLAY: ROCKSTAR GAMES · DATA: SENSOR TOWER, TAKE-TWO",
  endLine: "LAUNCH WEEK · FOLLOW FOR DAY ONE",
  clips: clips as any,
  cards: [
    { kind: "big", line: "hook", value: "$1B+", label: "before launch day" },
    { kind: "big", line: "pre", value: "EST.", label: "digital pre-orders", note: "Sensor Tower estimate\nnot confirmed by Take-Two", color: C.cyan },
    { kind: "pair", line: "price", a: { value: "$79.99", label: "STANDARD" }, b: { value: "$99.99", label: "ULTIMATE" } },
    { kind: "big", line: "bet", value: "−18%", label: "Take-Two bookings", note: "Jul–Sep 2026 · $1.6B", color: C.coral },
    {
      kind: "bars", line: "guide", title: "TAKE-TWO NET BOOKINGS", unit: "$B",
      bars: [
        { label: "JUL–SEP\nACTUAL", lo: 1.6, color: C.dim, text: "$1.6B" },
        { label: "OCT–DEC\nGUIDANCE", lo: 3.35, hi: 3.5, color: C.lime, text: "$3.35–3.5B" },
      ],
    },
    { kind: "quote", line: "quote", text: "We tend to avoid claiming success before it occurs.", who: "STRAUSS ZELNICK, TAKE-TWO CEO" },
    { kind: "date", line: "out", small: "PS5 · XBOX SERIES X|S", big: "NOV 19" },
  ],
};
