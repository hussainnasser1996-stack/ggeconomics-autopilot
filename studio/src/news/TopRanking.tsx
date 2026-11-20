import React from "react";
import { AbsoluteFill, Audio, CalculateMetadataFunction, interpolate, Sequence, spring, staticFile, useCurrentFrame, useVideoConfig, Easing } from "remotion";
import { BRAND, C, CRT, DISPLAY, Mark, MONO, SANS, useScale } from "../brand";
import { Broll, Clip } from "./NewsShort";

/** "Ranking" format, copied from the structure of the most-viewed ranking Shorts (20 Nov research, 5-19M views):
 *  the title never leaves the screen, a numbered list down the left fills in from the bottom, and the empty #1 slot
 *  is visible from frame 0 (that empty slot is the retention device). Music only, cuts on the beat, ~7 s per game. */
export type RankEntry = { rank: number; name: string; clips: Clip[]; players: number; price: string; fact: string; factUp?: boolean };
export type RankSpec = {
  titleA: string; titleB: string; kicker: string; credit: string; hookClips: Clip[]; entries: RankEntry[];
  music: { src: string; start: number; volume?: number }; beat: number; hookBeats: number; entryBeats: number; topBeats: number;
};
const fr = (s: RankSpec, b: number, fps: number) => Math.round(b * s.beat * fps);
export const rankFrames = (s: RankSpec, fps = 30) => fr(s, s.hookBeats, fps) + (s.entries.length - 1) * fr(s, s.entryBeats, fps) + fr(s, s.topBeats, fps);
export const rankMetadata: CalculateMetadataFunction<{ spec: RankSpec }> = async ({ props }) => ({ durationInFrames: rankFrames(props.spec) });

const Title: React.FC<{ s: RankSpec; u: number }> = ({ s, u }) => (
  <div style={{ position: "absolute", top: 70 * u, left: 0, right: 0, display: "flex", flexDirection: "column", alignItems: "center", gap: 10 * u }}>
    <div style={{ display: "flex", alignItems: "center", gap: 12 * u }}>
      <Mark size={30 * u} />
      <span style={{ fontFamily: DISPLAY, fontWeight: 900, fontSize: 24 * u, color: C.white, letterSpacing: 1 * u }}>{BRAND.name}</span>
      <span style={{ fontFamily: MONO, fontWeight: 700, fontSize: 21 * u, color: C.ink, background: C.lime, padding: `${5 * u}px ${12 * u}px`, borderRadius: 8 * u, letterSpacing: 2 * u }}>{s.kicker}</span>
    </div>
    <div style={{ textAlign: "center", lineHeight: 1.0, background: "rgba(7,7,11,0.78)", padding: `${10 * u}px ${24 * u}px`, borderRadius: 16 * u }}>
      <div style={{ fontFamily: DISPLAY, fontWeight: 900, fontSize: 74 * u, color: C.white, letterSpacing: -1 * u }}>{s.titleA}</div>
      <div style={{ fontFamily: DISPLAY, fontWeight: 900, fontSize: 52 * u, color: C.lime, letterSpacing: -1 * u, marginTop: 4 * u }}>{s.titleB}</div>
    </div>
  </div>
);

/** The list: rows 1..N top to bottom. Revealed rows show the name; the live row is lit; #1 stays "???" until its turn. */
const List: React.FC<{ s: RankSpec; live: number | null; revealedDown: number; u: number }> = ({ s, live, revealedDown, u }) => {
  const N = s.entries.length;
  const rows = Array.from({ length: N }, (_, i) => i + 1);
  const byRank = Object.fromEntries(s.entries.map((e) => [e.rank, e]));
  const rowH = (N > 5 ? 60 : 84) * u;
  return (
    <div style={{ position: "absolute", top: 400 * u, left: 26 * u, display: "flex", flexDirection: "column", gap: 8 * u }}>
      {rows.map((r) => {
        const shown = r >= revealedDown; const isLive = r === live;
        const col = r === 1 ? C.lime : r <= 3 ? C.cyan : C.white;
        return (
          <div key={r} style={{ height: rowH, display: "flex", alignItems: "center", gap: 12 * u, paddingRight: 16 * u,
            background: isLive ? C.lime : shown ? "rgba(7,7,11,0.78)" : "rgba(7,7,11,0.45)", borderRadius: 10 * u, maxWidth: 520 * u,
            boxShadow: isLive ? `0 0 ${24 * u}px ${C.lime}88` : "none" }}>
            <div style={{ width: 66 * u, textAlign: "right", fontFamily: DISPLAY, fontWeight: 900, fontSize: 38 * u, color: isLive ? C.ink : col }}>{r}.</div>
            <div style={{ fontFamily: SANS, fontWeight: 800, fontSize: 28 * u, color: isLive ? C.ink : C.white, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
              {shown ? byRank[r].name : r === 1 ? "???" : ""}
            </div>
          </div>
        );
      })}
    </div>
  );
};

const Card: React.FC<{ e: RankEntry; d: number; top: boolean; u: number }> = ({ e, d, top, u }) => {
  const f = useCurrentFrame(); const { fps } = useVideoConfig();
  const inP = spring({ frame: f - 2, fps, config: { damping: 14, stiffness: 160 } });
  const factP = spring({ frame: f - Math.round(d * 0.35), fps, config: { damping: 10, stiffness: 200 } });
  const count = Math.round(e.players * interpolate(f, [4, 4 + Math.min(36, d * 0.4)], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) }));
  return (
    <div style={{ position: "absolute", bottom: 300 * u, left: 0, right: 0, display: "flex", justifyContent: "center", transform: `translateY(${(1 - inP) * 70 * u}px)`, opacity: inP }}>
      <div style={{ background: "rgba(7,7,11,0.88)", border: `${2 * u}px solid ${top ? C.lime : C.line}`, borderRadius: 22 * u, padding: `${18 * u}px ${30 * u}px`,
        display: "flex", flexDirection: "column", alignItems: "center", gap: 10 * u, minWidth: 700 * u }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: 16 * u }}>
          <span style={{ fontFamily: DISPLAY, fontWeight: 900, fontSize: 64 * u, color: top ? C.lime : C.cyan }}>#{e.rank}</span>
          <span style={{ fontFamily: DISPLAY, fontWeight: 900, fontSize: (e.name.length > 18 ? 42 : 52) * u, color: C.white }}>{e.name}</span>
        </div>
        <div style={{ fontFamily: DISPLAY, fontWeight: 900, fontSize: 88 * u, color: top ? C.lime : C.white, lineHeight: 1 }}>{count.toLocaleString("en-US")}</div>
        <div style={{ fontFamily: MONO, fontWeight: 700, fontSize: 22 * u, color: C.dim, letterSpacing: 3 * u }}>PEAK PLAYERS THIS WEEK</div>
        <div style={{ display: "flex", gap: 12 * u, marginTop: 4 * u }}>
          <span style={{ fontFamily: MONO, fontWeight: 700, fontSize: 26 * u, background: C.cyan, color: C.ink, padding: `${7 * u}px ${14 * u}px`, borderRadius: 10 * u }}>{e.price}</span>
          <span style={{ fontFamily: MONO, fontWeight: 700, fontSize: 26 * u, background: e.factUp === false ? C.coral : C.lime, color: C.ink, padding: `${7 * u}px ${14 * u}px`,
            borderRadius: 10 * u, transform: `scale(${0.6 + 0.4 * factP})`, opacity: factP }}>{e.fact}</span>
        </div>
      </div>
    </div>
  );
};

export const TopRanking: React.FC<{ spec: RankSpec }> = ({ spec: s }) => {
  const f = useCurrentFrame(); const { fps } = useVideoConfig(); const { u } = useScale();
  const total = rankFrames(s, fps);
  const hook = fr(s, s.hookBeats, fps), ent = fr(s, s.entryBeats, fps), topD = fr(s, s.topBeats, fps);
  const starts = s.entries.map((_, i) => hook + i * ent);
  let idx = -1; starts.forEach((st, i) => { if (f >= st) idx = i; });
  const live = idx >= 0 ? s.entries[idx].rank : null;
  const revealedDown = idx >= 0 ? s.entries[idx].rank : s.entries.length + 1;
  const flash = starts.reduce((a, st, i) => Math.max(a, interpolate(f - st, [0, i === s.entries.length - 1 ? 6 : 3], [i === s.entries.length - 1 ? 0.7 : 0.25, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) * (f >= st ? 1 : 0)), 0);
  return (
    <AbsoluteFill style={{ background: C.ink }}>
      <Broll clips={[...s.hookClips, ...s.entries.flatMap((e) => e.clips)]} />
      <AbsoluteFill style={{ background: "linear-gradient(90deg, rgba(7,7,11,0.55) 0%, rgba(7,7,11,0.0) 45%)" }} />
      <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(7,7,11,0.6) 0%, rgba(7,7,11,0.0) 22%, rgba(7,7,11,0.0) 60%, rgba(7,7,11,0.7) 100%)" }} />
      <AbsoluteFill style={{ background: "#fff", opacity: flash }} />
      <Audio src={staticFile(s.music.src)} startFrom={Math.round(s.music.start * fps)}
        volume={(x) => interpolate(x, [0, 3, total - 10, total], [0, s.music.volume ?? 0.9, s.music.volume ?? 0.9, 0], { extrapolateRight: "clamp" })} />
      <Title s={s} u={u} />
      <List s={s} live={live} revealedDown={revealedDown} u={u} />
      {s.entries.map((e, i) => {
        const isTop = i === s.entries.length - 1; const d = isTop ? topD : ent;
        return <Sequence key={e.rank} from={starts[i]} durationInFrames={d}><Card e={e} d={d} top={isTop} u={u} /></Sequence>;
      })}
      <div style={{ position: "absolute", bottom: 240 * u, left: 0, right: 0, textAlign: "center", fontFamily: MONO, fontSize: 19 * u, color: "rgba(255,255,255,0.6)", letterSpacing: 2 * u }}>{s.credit}</div>
      <CRT strength={0.35} />
    </AbsoluteFill>
  );
};
