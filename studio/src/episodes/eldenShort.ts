import { ShortSpec } from "../news/NewsShort";
import { C } from "../brand";
import timeline from "../../public/vo/elden_short/timeline.json";
// Tips backed by on-screen game text (work/v3/verify.jpg): Guidance of Grace (688s), Crafting Kit shop (765s),
// Church of Elleh grace (1166s), Stonesword Key pickup (1292s).
export const eldenShort: ShortSpec = {
  tag: "ELDEN RING · FIRST HOUR",
  topic: "3 things to do in your first hour",
  vo: "vo/elden_short/vo.wav",
  timeline: timeline as any,
  noBed: true,
  credit: "GAMEPLAY: ELDEN RING · FROMSOFTWARE / BANDAI NAMCO",
  endLine: "FULL WALKTHROUGH · PART 1 ON THE CHANNEL",
  clips: [
    { src: "v3", from: 677.0, dur: 1.9 },
    { src: "v3", from: 340.0, dur: 1.4 },
    { src: "v3", from: 1166.0, dur: 1.9 },
    { src: "v3", from: 686.0, dur: 1.9 },
    { src: "v3", from: 752.0, dur: 1.7 },
    { src: "v3", from: 764.5, dur: 1.6 },
    { src: "v3", from: 1288.5, dur: 3.5 },
    { src: "v3", from: 698.0, dur: 4.6 },
  ],
  cards: [
    { kind: "big", line: "hook", value: "3", label: "things · first hour" },
    { kind: "big", line: "one", value: "01", label: "Rest at grace", note: "golden rays = your next objective", color: C.lime },
    { kind: "big", line: "two", value: "02", label: "Buy the Crafting Kit", note: "merchant · Church of Elleh", color: C.cyan },
    { kind: "big", line: "three", value: "03", label: "Keep Stonesword Keys", note: "they open imp-statue seals", color: C.coral },
    { kind: "date", line: "out", small: "FULL WALKTHROUGH", big: "PT.1" },
  ],
};
