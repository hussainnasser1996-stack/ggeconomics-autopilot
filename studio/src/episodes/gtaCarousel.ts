import { Slide } from "../news/Carousel";
import { C } from "../brand";
export const gtaCarousel: Slide[] = [
  { bg: { src: "v2", at: 290.6 }, kicker: "GTA VI · LAUNCH WEEK", head: "|$1B| BEFORE\nIT'S EVEN OUT", sub: "The money behind the biggest launch of the year. Four numbers →" },
  { bg: { src: "v2", at: 195.0 }, kicker: "01 · THE PRE-ORDERS", card: { kind: "big", line: "", value: "$1B+", label: "est. digital pre-orders", note: "Sensor Tower estimate\nnot confirmed by Take-Two" } },
  { bg: { src: "v2", at: 714.0 }, kicker: "02 · THE PRICE", card: { kind: "pair", line: "", a: { value: "$79.99", label: "STANDARD" }, b: { value: "$99.99", label: "ULTIMATE" }, note: "PS5 · Xbox Series X|S · Nov 19" } },
  { bg: { src: "v2", at: 866.0 }, kicker: "03 · THE BET", card: { kind: "bars", line: "", title: "TAKE-TWO NET BOOKINGS", unit: "$B", bars: [
      { label: "JUL–SEP\nACTUAL", lo: 1.6, color: C.dim, text: "$1.6B" }, { label: "OCT–DEC\nGUIDANCE", lo: 3.35, hi: 3.5, color: C.lime, text: "$3.35–3.5B" }], note: "Jul–Sep bookings fell 18%" } },
  { bg: { src: "v2", at: 821.0 }, kicker: "04 · THE CEO", card: { kind: "quote", line: "", text: "We tend to avoid claiming success before it occurs.", who: "STRAUSS ZELNICK, TAKE-TWO" }, sub: "Follow for the launch-day numbers." },
];
