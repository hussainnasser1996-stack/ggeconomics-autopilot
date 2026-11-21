import React from "react";
import { AbsoluteFill, Audio, CalculateMetadataFunction, Easing, interpolate, OffthreadVideo, Sequence, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { BRAND, C, CRT, DISPLAY, Mark, MONO, SANS } from "../brand";

/** Long-form weekly Top 10 (16:9, experiment 20 Nov 2026). Structure copied from the most-viewed long Top 10s
 *  (gameranx monthly 450-750k, Midnight Play 2M): cold-open montage of every game -> title -> big number card ->
 *  ~40-60 s of full-screen gameplay per game with a name tag top-left -> #1 longest -> recap board / end screen.
 *  No narration: OUR data carries it (players, price, reviews, Metacritic, a fact per game, a value verdict). */
export type LClip = { src: string; from: number; dur: number; crop?: number; zoom?: number };
export type LEntry = {
  rank: number; name: string; dev: string; genre: string; released: string;
  players: number; price: string; priceNote?: string; reviews: string; meta?: string;
  facts: string[]; verdict: string; clips: LClip[];
};
export type LongSpec = {
  title: string; sub: string; week: string; credit: string;
  cold: LClip[]; entries: LEntry[];
  music: { src: string; start: number; at: number }[];   // `at` = seconds into the video where this track starts
  introSec: number; cardSec: number; outroSec: number;
  /** optional hook before the montage (20 Nov intro test): big number over blurred #1 footage */
  hook?: { sec: number; big: number; line: string; ask: string; clip: LClip };
  boardSub?: string;
  vo?: { src: string; at: number; len?: number }[];   // narration lines, `at` in seconds; music ducks under them
};
const FPS = 30;
const coldSec = (s: LongSpec) => s.cold.reduce((a, c) => a + c.dur, 0);
const hookSec = (s: LongSpec) => s.hook?.sec ?? 0;
const segSec = (e: LEntry) => e.clips.reduce((a, c) => a + c.dur, 0);
export const longLayout = (s: LongSpec) => {
  let t = hookSec(s) + coldSec(s) + s.introSec; const segs: { at: number; card: number; play: number }[] = [];
  for (const e of s.entries) { segs.push({ at: t, card: s.cardSec, play: segSec(e) }); t += s.cardSec + segSec(e); }
  return { segs, outroAt: t, total: t + s.outroSec };
};
export const longMetadata: CalculateMetadataFunction<{ spec: LongSpec }> = async ({ props }) => ({ durationInFrames: Math.round(longLayout(props.spec).total * FPS) });

const Footage: React.FC<{ clips: LClip[]; push?: number }> = ({ clips, push = 1.04 }) => {
  let at = 0;
  return <>{clips.map((c, i) => { const from = Math.round(at * FPS), d = Math.round(c.dur * FPS); at += c.dur;
    return <Sequence key={i} from={from} durationInFrames={d}><Shot c={c} d={d} push={push} /></Sequence>; })}</>;
};
const Shot: React.FC<{ c: LClip; d: number; push: number }> = ({ c, d, push }) => {
  const f = useCurrentFrame();
  const z = interpolate(f, [0, d], [1, push], { easing: Easing.inOut(Easing.sin) }) * (c.crop ? 1.17 : 1) * (c.zoom ?? 1);   // crop: hide burned-in subtitles at the bottom
  return (
    <AbsoluteFill style={{ overflow: "hidden", background: "#000" }}>
      <OffthreadVideo src={staticFile(`footage/${c.src}.mp4`)} startFrom={Math.round(c.from * FPS)} muted
        style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${z})`, transformOrigin: c.crop ? "50% 8%" : "50% 50%" }} />
    </AbsoluteFill>
  );
};

const fade = (f: number, a: number, b: number, len = 8) =>
  Math.min(interpolate(f, [a, a + len], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }), interpolate(f, [b - len, b], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));

const Brand: React.FC<{ op?: number }> = ({ op = 1 }) => (
  <div style={{ position: "absolute", top: 40, right: 48, display: "flex", alignItems: "center", gap: 12, opacity: op * 0.9 }}>
    <Mark size={34} /><span style={{ fontFamily: DISPLAY, fontWeight: 900, fontSize: 26, color: C.white, letterSpacing: 1, textShadow: "0 2px 8px #000" }}>{BRAND.name}</span>
  </div>
);

/* ---------- cold open: fast montage, title lands at the end ---------- */
const Cold: React.FC<{ s: LongSpec; d: number }> = ({ s, d }) => {
  const f = useCurrentFrame();
  const tIn = d - 5.5 * FPS;
  const pop = spring({ frame: f - tIn, fps: FPS, config: { damping: 13, stiffness: 150 } });
  return (
    <AbsoluteFill>
      <Footage clips={s.cold} push={1.06} />
      <AbsoluteFill style={{ background: `rgba(7,7,11,${0.55 * pop})` }} />
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", flexDirection: "column", opacity: pop, transform: `scale(${0.85 + 0.15 * pop})` }}>
        <div style={{ fontFamily: MONO, fontWeight: 700, fontSize: 30, color: C.ink, background: C.lime, padding: "8px 18px", borderRadius: 8, letterSpacing: 4 }}>{s.week}</div>
        <div style={{ fontFamily: DISPLAY, fontWeight: 900, fontSize: 150, color: C.white, lineHeight: 0.95, marginTop: 24, textAlign: "center", letterSpacing: -3, textShadow: "0 6px 30px #000" }}>{s.title}</div>
        <div style={{ fontFamily: DISPLAY, fontWeight: 900, fontSize: 64, color: C.lime, marginTop: 14, textAlign: "center" }}>{s.sub}</div>
      </AbsoluteFill>
      <Brand op={pop} />
    </AbsoluteFill>
  );
};

/* ---------- hook: the one number that makes you ask "which game?" ---------- */
const Hook: React.FC<{ s: LongSpec; d: number }> = ({ s, d }) => {
  const f = useCurrentFrame(); const h = s.hook!;
  const n = Math.round(h.big * interpolate(f, [6, 48], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) }));
  const p = spring({ frame: f - 2, fps: FPS, config: { damping: 12, stiffness: 160 } });
  const lineP = interpolate(f, [30, 42], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const askP = spring({ frame: f - Math.round(d * 0.62), fps: FPS, config: { damping: 9, stiffness: 220 } });
  const out = interpolate(f, [d - 5, d], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ opacity: out }}>
      <AbsoluteFill style={{ filter: "blur(22px) brightness(0.45)", transform: "scale(1.1)" }}><Footage clips={[h.clip]} push={1.08} /></AbsoluteFill>
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", flexDirection: "column" }}>
        <div style={{ fontFamily: DISPLAY, fontWeight: 900, fontSize: 230, color: C.lime, lineHeight: 0.9, letterSpacing: -6, transform: `scale(${0.8 + 0.2 * p})`, opacity: p,
          textShadow: `0 0 70px ${C.lime}55, 0 8px 30px #000` }}>{n.toLocaleString("en-US")}</div>
        <div style={{ fontFamily: SANS, fontWeight: 800, fontSize: 58, color: C.white, marginTop: 26, textAlign: "center", maxWidth: 1400, lineHeight: 1.15, opacity: lineP,
          transform: `translateY(${(1 - lineP) * 20}px)`, textShadow: "0 4px 20px #000" }}>{h.line}</div>
        <div style={{ fontFamily: DISPLAY, fontWeight: 900, fontSize: 96, color: C.ink, background: C.lime, padding: "6px 34px", borderRadius: 14, marginTop: 40,
          opacity: Math.min(1, askP * 1.4), transform: `scale(${1.4 - 0.4 * askP})` }}>{h.ask}</div>
      </AbsoluteFill>
      <Brand />
    </AbsoluteFill>
  );
};

/* ---------- intro board: how it's ranked + the 10 slots, #1 hidden ---------- */
const Board: React.FC<{ s: LongSpec; reveal: number; heading: string; showPlayers?: boolean; sub?: string }> = ({ s, reveal, heading, showPlayers, sub }) => {
  const f = useCurrentFrame();
  const byRank = [...s.entries].sort((a, b) => a.rank - b.rank);
  return (
    <AbsoluteFill style={{ background: `radial-gradient(circle at 30% 20%, ${C.ink2}, ${C.ink})`, padding: "70px 110px" }}>
      <Brand />
      <div style={{ fontFamily: MONO, fontWeight: 700, fontSize: 26, color: C.lime, letterSpacing: 4 }}>{s.week}</div>
      <div style={{ fontFamily: DISPLAY, fontWeight: 900, fontSize: 66, color: C.white, marginTop: 6 }}>{heading}</div>
      {sub && <div style={{ fontFamily: SANS, fontWeight: 700, fontSize: 32, color: C.cyan, marginTop: 8, opacity: interpolate(f, [10, 22], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) }}>{sub}</div>}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gridAutoFlow: "column", gridTemplateRows: "repeat(5, 1fr)", gap: "18px 40px", marginTop: sub ? 28 : 40, flex: 1 }}>
        {byRank.map((e, i) => {
          const shown = e.rank >= reveal; const p = spring({ frame: f - 6 - (10 - e.rank) * 3, fps: FPS, config: { damping: 15 } });
          return (
            <div key={e.rank} style={{ display: "flex", alignItems: "center", gap: 22, background: e.rank === 1 ? "rgba(212,255,58,0.10)" : "rgba(255,255,255,0.04)",
              border: `2px solid ${e.rank === 1 ? C.lime : C.line}`, borderRadius: 16, padding: "0 26px", opacity: p, transform: `translateX(${(1 - p) * -40}px)` }}>
              <div style={{ fontFamily: DISPLAY, fontWeight: 900, fontSize: 64, width: 90, color: e.rank === 1 ? C.lime : e.rank <= 3 ? C.cyan : C.white }}>{e.rank}</div>
              <div style={{ fontFamily: SANS, fontWeight: 800, fontSize: 38, color: C.white, flex: 1, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{shown ? e.name : e.rank === 1 ? "???" : "· · ·"}</div>
              {showPlayers && <div style={{ fontFamily: MONO, fontWeight: 700, fontSize: 28, color: C.dim }}>{e.players.toLocaleString("en-US")}</div>}
            </div>
          );
        })}
      </div>
      <div style={{ fontFamily: MONO, fontSize: 20, color: C.dim, marginTop: 26, letterSpacing: 2 }}>{s.credit}</div>
    </AbsoluteFill>
  );
};

/* ---------- number card between games ---------- */
const NumberCard: React.FC<{ e: LEntry; d: number }> = ({ e, d }) => {
  const f = useCurrentFrame(); const top = e.rank === 1;
  const p = spring({ frame: f, fps: FPS, config: { damping: 10, stiffness: 200 } });
  const out = interpolate(f, [d - 6, d], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ background: C.ink, alignItems: "center", justifyContent: "center", opacity: out }}>
      <div style={{ fontFamily: DISPLAY, fontWeight: 900, fontSize: top ? 520 : 440, color: top ? C.lime : C.white, lineHeight: 0.8,
        transform: `scale(${1.5 - 0.5 * p})`, opacity: Math.min(1, p * 1.4), textShadow: `0 0 80px ${top ? C.lime : C.cyan}55` }}>{e.rank}</div>
      <div style={{ fontFamily: SANS, fontWeight: 800, fontSize: 52, color: C.white, marginTop: 30, opacity: interpolate(f, [8, 16], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) }}>{e.name}</div>
    </AbsoluteFill>
  );
};

/* ---------- one game: gameplay + name tag + data panel + fact chips + verdict ---------- */
const Game: React.FC<{ e: LEntry; d: number; n: number }> = ({ e, d, n }) => {
  const f = useCurrentFrame(); const top = e.rank === 1;
  const tagP = spring({ frame: f - 4, fps: FPS, config: { damping: 15 } });
  const panelA = 1.2 * FPS, panelB = Math.min(16 * FPS, Math.round(d * 0.42));
  const panelP = fade(f, panelA, panelB, 12);
  const count = Math.round(e.players * interpolate(f, [panelA + 6, panelA + 6 + 40], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) }));
  // facts: evenly spread through the middle of the segment, each up ~7 s
  const verdictA = d - 8 * FPS;
  const gap = (verdictA - panelB - 1 * FPS) / Math.max(1, e.facts.length);   // facts share the time between panel and verdict
  const factLen = Math.min(7 * FPS, gap - 0.5 * FPS);
  const factSlots = e.facts.map((_, i) => panelB + 0.5 * FPS + i * gap);
  return (
    <AbsoluteFill>
      <Footage clips={e.clips} />
      <AbsoluteFill style={{ background: "linear-gradient(90deg, rgba(7,7,11,0.55) 0%, rgba(7,7,11,0) 35%, rgba(7,7,11,0) 62%, rgba(7,7,11,0.5) 100%)", opacity: Math.max(panelP, 0.35) }} />
      <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(7,7,11,0.45) 0%, rgba(7,7,11,0) 18%, rgba(7,7,11,0) 78%, rgba(7,7,11,0.6) 100%)" }} />
      {/* name tag, always on */}
      <div style={{ position: "absolute", top: 40, left: 48, display: "flex", alignItems: "stretch", opacity: tagP, transform: `translateX(${(1 - tagP) * -30}px)` }}>
        <div style={{ fontFamily: DISPLAY, fontWeight: 900, fontSize: 48, background: top ? C.lime : C.cyan, color: C.ink, padding: "4px 18px", borderRadius: "10px 0 0 10px" }}>#{e.rank}</div>
        <div style={{ fontFamily: SANS, fontWeight: 800, fontSize: 36, background: "rgba(7,7,11,0.85)", color: C.white, padding: "10px 22px", borderRadius: "0 10px 10px 0", display: "flex", alignItems: "center" }}>{e.name}</div>
      </div>
      <Brand />
      {/* progress pips 10..1 */}
      <div style={{ position: "absolute", top: 108, left: 48, display: "flex", gap: 6, opacity: tagP }}>
        {Array.from({ length: n }, (_, i) => n - i).map((r) => (
          <div key={r} style={{ width: 30, height: 8, borderRadius: 4, background: r === e.rank ? (top ? C.lime : C.cyan) : r > e.rank ? "rgba(255,255,255,0.55)" : "rgba(255,255,255,0.15)" }} />
        ))}
      </div>
      {/* data panel, right side */}
      <div style={{ position: "absolute", right: 56, top: 200, width: 520, opacity: panelP, transform: `translateX(${(1 - panelP) * 60}px)`,
        background: "rgba(7,7,11,0.86)", border: `2px solid ${top ? C.lime : C.line}`, borderRadius: 22, padding: "26px 32px", display: "flex", flexDirection: "column", gap: 14 }}>
        <div style={{ fontFamily: MONO, fontWeight: 700, fontSize: 20, color: C.dim, letterSpacing: 3 }}>PEAK PLAYERS THIS WEEK</div>
        <div style={{ fontFamily: DISPLAY, fontWeight: 900, fontSize: 84, color: top ? C.lime : C.white, lineHeight: 1 }}>{count.toLocaleString("en-US")}</div>
        <Row k="PRICE" v={e.price + (e.priceNote ? `  ${e.priceNote}` : "")} hi={C.cyan} />
        <Row k="STEAM REVIEWS" v={e.reviews} />
        {e.meta && <Row k="METACRITIC" v={e.meta} />}
        <Row k="RELEASED" v={e.released} />
        <Row k="GENRE" v={e.genre} />
        <Row k="STUDIO" v={e.dev} />
      </div>
      {/* fact chips, lower left */}
      {e.facts.map((t, i) => {
        const a = factSlots[i]; const b = a + factLen; if (factLen < 3 * FPS || b > verdictA) return null;
        const p = fade(f, a, b, 10);
        return <div key={i} style={{ position: "absolute", left: 48, bottom: 70, opacity: p, transform: `translateY(${(1 - p) * 24}px)`, maxWidth: 1200,
          fontFamily: SANS, fontWeight: 800, fontSize: 40, color: C.white, background: "rgba(7,7,11,0.86)", borderLeft: `8px solid ${top ? C.lime : C.cyan}`, padding: "16px 26px", borderRadius: 10 }}>{t}</div>;
      })}
      {/* verdict */}
      {(() => { const p = fade(f, verdictA, d - 0.6 * FPS, 10); return (
        <div style={{ position: "absolute", left: 48, bottom: 70, opacity: p, transform: `translateY(${(1 - p) * 24}px)`, display: "flex", alignItems: "center", gap: 18 }}>
          <div style={{ fontFamily: MONO, fontWeight: 700, fontSize: 26, color: C.ink, background: C.lime, padding: "12px 18px", borderRadius: 10, letterSpacing: 3 }}>VERDICT</div>
          <div style={{ fontFamily: SANS, fontWeight: 800, fontSize: 42, color: C.white, background: "rgba(7,7,11,0.86)", padding: "12px 24px", borderRadius: 10 }}>{e.verdict}</div>
        </div>); })()}
      <CRT strength={0.2} />
    </AbsoluteFill>
  );
};
const Row: React.FC<{ k: string; v: string; hi?: string }> = ({ k, v, hi }) => (
  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", borderTop: `1px solid ${C.line}`, paddingTop: 10 }}>
    <span style={{ fontFamily: MONO, fontWeight: 700, fontSize: 20, color: C.dim, letterSpacing: 2 }}>{k}</span>
    <span style={{ fontFamily: SANS, fontWeight: 800, fontSize: 30, color: hi ?? C.white, textAlign: "right", maxWidth: 300 }}>{v}</span>
  </div>
);

/** music level under narration: 0.3 while a line plays, 1 otherwise */
const duckAt = (win: [number, number][], frame: number) => win.reduce((m, [a, b]) => Math.min(m, interpolate(frame, [a - 8, a, b, b + 12], [1, 0.3, 0.3, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })), 1);

export const LongTop: React.FC<{ spec: LongSpec }> = ({ spec: s }) => {
  const L = longLayout(s); const cold = coldSec(s); const total = L.total; const H = Math.round(hookSec(s) * FPS);
  const win: [number, number][] = (s.vo ?? []).map((v) => [Math.round(v.at * FPS), Math.round((v.at + (v.len ?? 6)) * FPS)]);
  const duck = (fr: number) => duckAt(win, fr);
  const n = s.entries.length;
  return (
    <AbsoluteFill style={{ background: C.ink }}>
      {s.hook && <Sequence durationInFrames={H}><Hook s={s} d={H} /></Sequence>}
      <Sequence from={H} durationInFrames={Math.round(cold * FPS)}><Cold s={s} d={Math.round(cold * FPS)} /></Sequence>
      <Sequence from={H + Math.round(cold * FPS)} durationInFrames={Math.round(s.introSec * FPS)}><Board s={s} reveal={99} heading="Ranked by peak players on Steam" sub={s.boardSub} /></Sequence>
      {(s.vo ?? []).map((v, i) => <Sequence key={"vo" + i} from={Math.round(v.at * FPS)}><Audio src={staticFile(v.src)} volume={1} /></Sequence>)}
      {s.entries.map((e, i) => { const g = L.segs[i]; return (
        <React.Fragment key={e.rank}>
          <Sequence from={Math.round(g.at * FPS)} durationInFrames={Math.round(g.card * FPS)}><NumberCard e={e} d={Math.round(g.card * FPS)} /></Sequence>
          <Sequence from={Math.round((g.at + g.card) * FPS)} durationInFrames={Math.round(g.play * FPS)}><Game e={e} d={Math.round(g.play * FPS)} n={n} /></Sequence>
        </React.Fragment>); })}
      <Sequence from={Math.round(L.outroAt * FPS)} durationInFrames={Math.round(s.outroSec * FPS)}><Board s={s} reveal={1} heading="This week's full ranking" showPlayers /></Sequence>
      {s.music.map((m, i) => {
        const a = Math.round(m.at * FPS); const b = Math.round((s.music[i + 1]?.at ?? total) * FPS); const len = b - a;
        return <Sequence key={i} from={a} durationInFrames={len + 30}>
          <Audio src={staticFile(m.src)} startFrom={Math.round(m.start * FPS)}
            volume={(x) => interpolate(x, [0, 20, len - 10, len + 30], [i === 0 ? 0 : 0.2, 0.85, 0.85, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) * duck(a + x)} />
        </Sequence>; })}
    </AbsoluteFill>
  );
};
