import { WalkSpec } from "../walkthrough/Walkthrough";
// Every label/tip below is backed by on-screen game text verified in work/v3/verify.jpg:
// "Chapel of Anticipation" (302s), boss bar "Grafted Scion" (340s), "Guidance of Grace" tutorial (688s),
// Crafting Kit purchase screen (765s), "Church of Elleh" grace (1166s), "Stonesword Key" pickup (1292s).
export const eldenWalk: WalkSpec = {
  game: "ELDEN RING", part: "PART 1", title: "From the Chapel to Limgrave",
  segments: [
    { src: "v3", from: 298, dur: 28, place: "CHAPEL OF ANTICIPATION", tips: [
      { at: 2, dur: 7, kind: "objective", title: "The opening", body: "Follow the path to the arena ahead." },
    ] },
    { src: "v3", from: 330, dur: 16, place: "FIRST BOSS", tips: [
      { at: 1, dur: 10, kind: "boss", title: "Grafted Scion", body: "Most players lose this one. That's by design: the story moves on either way." },
    ] },
    { src: "v3", from: 446, dur: 26, place: "STRANDED GRAVEYARD", tips: [
      { at: 3, dur: 9, kind: "tip", title: "Learn the dodge early", body: "Rolling through attacks is your main defence. Practise here, where it's safe." },
    ] },
    { src: "v3", from: 674, dur: 32, place: "LIMGRAVE", tips: [
      { at: 2, dur: 7, kind: "objective", title: "Step out into Limgrave" },
      { at: 12, dur: 10, kind: "tip", title: "Guidance of Grace", body: "Golden rays from a Site of Grace point toward your next objective." },
    ] },
    { src: "v3", from: 748, dur: 29, place: "MERCHANT KALÉ", tips: [
      { at: 15, dur: 11, kind: "item", title: "Buy the Crafting Kit", body: "Craft consumables from what you gather. One of the best early purchases." },
    ] },
    { src: "v3", from: 1164, dur: 28, place: "CHURCH OF ELLEH", tips: [
      { at: 3, dur: 10, kind: "tip", title: "Rest at a Site of Grace", body: "Refills your flasks and sets your respawn. Enemies come back when you rest." },
    ] },
    { src: "v3", from: 1278, dur: 22, place: "STONESWORD KEY", tips: [
      { at: 12, dur: 9, kind: "item", title: "Stonesword Key", body: "Opens imp-statue seals. Save them for places worth unlocking." },
    ] },
  ],
};
