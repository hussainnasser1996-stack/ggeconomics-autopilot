import React from "react";
import { AbsoluteFill, Audio, interpolate, OffthreadVideo, Sequence, spring, staticFile, useCurrentFrame, useVideoConfig, Easing, random } from "remotion";
import { BRAND, C, CRT, DISPLAY, GlitchSlices, GridBG, Mark, MONO, RGBSplit, SANS } from "../brand";
import { Ident, IDENT_FRAMES } from "../Ident";
import { Card, CardView } from "./Cards";
import { Broll, Clip, Timeline } from "./NewsShort";

export type LongSpec = {
  vo: string; timeline: Timeline; clips: Clip[]; cards: Card[];
  chapters: { line: string; n: string; title: string }[];
  cold: { src: string; from: number; dur: number; words: Timeline["words"]; source: string };
  credit: string; title: string; noBed?: boolean;
  endTiles: string[];
};

export const END_SCREEN = 600; // 20 s, YouTube's max end-screen window
export const longFrames = (s: LongSpec, fps = 30) =>
  Math.round(s.cold.dur * fps) + IDENT_FRAMES + Math.ceil(s.timeline.duration * fps) + END_SCREEN;

/* ---------- cold open: cited soundbite in a monitor frame ---------- */
const ColdOpen: React.FC<{ cold: LongSpec["cold"] }> = ({ cold }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: f, fps, config: { damping: 18, stiffness: 120 } });
  const t = f / fps + cold.from;
  const shown = cold.words.filter((w) => w.s <= t);
  const glitchOut = f > cold.dur * fps - 8 ? 1 : 0;
  return (
    <AbsoluteFill>
      <GridBG />
      <GlitchSlices intensity={glitchOut} seed="cold">
        <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", flexDirection: "column", gap: 40 }}>
          <div style={{
            width: 1180, height: 664, borderRadius: 24, overflow: "hidden", border: `3px solid ${C.line}`, position: "relative",
            transform: `perspective(1600px) rotateY(${(1 - s) * -14}deg) scale(${0.9 + 0.1 * s})`, opacity: s,
            boxShadow: `0 40px 120px rgba(0,0,0,0.7), 0 0 0 1px ${C.lime}22`, marginTop: -60,
          }}>
            <OffthreadVideo src={staticFile(`footage/${cold.src}.mp4`)} startFrom={Math.round(cold.from * fps)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
            <div style={{ position: "absolute", left: 22, top: 20, display: "flex", gap: 10, alignItems: "center", background: "rgba(7,7,11,0.85)", padding: "8px 14px", borderRadius: 10 }}>
              <div style={{ width: 10, height: 10, borderRadius: 99, background: C.coral }} />
              <span style={{ fontFamily: MONO, fontWeight: 700, fontSize: 20, color: C.white, letterSpacing: 2 }}>{cold.source}</span>
            </div>
          </div>
          <div style={{ fontFamily: SANS, fontWeight: 800, fontSize: 50, color: C.white, maxWidth: 1400, textAlign: "center", lineHeight: 1.2, minHeight: 130 }}>
            {shown.map((w, i) => {
              const isLast = i === shown.length - 1;
              return <span key={i} style={{ color: /money/.test(w.w) ? C.lime : C.white, opacity: isLast ? interpolate((t - w.s) * fps, [0, 3], [0.3, 1], { extrapolateRight: "clamp" }) : 1 }}>{w.w}</span>;
            })}
          </div>
        </AbsoluteFill>
      </GlitchSlices>
      <CRT strength={0.5} />
    </AbsoluteFill>
  );
};

/* ---------- chapter interstitial ---------- */
const Chapter: React.FC<{ n: string; title: string; dur: number }> = ({ n, title, dur }) => {
  const f = useCurrentFrame();
  const inP = interpolate(f, [0, 8], [0, 1], { extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  const outP = interpolate(f, [dur - 8, dur], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const split = interpolate(f, [0, 10], [24, 0], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ opacity: outP }}>
      <AbsoluteFill style={{ background: `rgba(7,7,11,${0.72 * inP})` }} />
      <GlitchSlices intensity={f < 6 ? 0.8 : 0} seed={`ch${n}`}>
        <AbsoluteFill style={{ alignItems: "flex-start", justifyContent: "center", paddingLeft: 160, flexDirection: "column" }}>
          <div style={{ fontFamily: MONO, fontWeight: 700, fontSize: 34, color: C.lime, letterSpacing: 10, transform: `translateX(${(1 - inP) * -60}px)` }}>CHAPTER {n} / 04</div>
          <RGBSplit amount={split}>
            <div style={{ fontFamily: DISPLAY, fontWeight: 900, fontSize: 150, color: C.white, lineHeight: 1, letterSpacing: -4, marginTop: 10, transform: `translateX(${(1 - inP) * 80}px)` }}>{title}</div>
          </RGBSplit>
          <div style={{ height: 10, background: C.lime, marginTop: 30, width: `${inP * 520}px`, boxShadow: `0 0 20px ${C.lime}` }} />
        </AbsoluteFill>
      </GlitchSlices>
    </AbsoluteFill>
  );
};

/* ---------- sentence subtitles (long-form style, small, bottom) ---------- */
const Subs: React.FC<{ words: Timeline["words"]; skip: [number, number][]; drop: [number, number][] }> = ({ words, skip, drop }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = f / fps;
  if (skip.some(([a, b]) => t >= a && t < b)) return null;
  const groups: Timeline["words"][] = []; let cur: Timeline["words"] = [];
  const merged: Timeline["words"] = [];
  words.filter((w) => !drop.some(([a, b]) => w.s >= a && w.s < b)).forEach((w) => { const p = merged[merged.length - 1]; if (p && /^[.\-%]/.test(w.w) && w.w !== "-") { p.w += w.w; p.e = w.e; } else merged.push({ ...w }); });
  merged.forEach((w) => { cur.push(w); if (cur.length >= 8 || /[.?!]$/.test(w.w)) { groups.push(cur); cur = []; } });
  if (cur.length) groups.push(cur);
  const g = groups.find((x, i) => t >= x[0].s - 0.05 && t < (groups[i + 1]?.[0].s ?? x[x.length - 1].e + 0.5));
  if (!g) return null;
  return (
    <div style={{ position: "absolute", bottom: 70, left: 0, right: 0, display: "flex", justifyContent: "center" }}>
      <div style={{ background: "rgba(7,7,11,0.78)", padding: "10px 22px", borderRadius: 10, fontFamily: SANS, fontWeight: 700, fontSize: 38, color: C.white, maxWidth: 1300, textAlign: "center" }}>
        {g.map((w, i) => <span key={i} style={{ color: t >= w.s ? C.white : "rgba(244,244,240,0.5)" }}>{w.w} </span>)}
      </div>
    </div>
  );
};

/* ---------- persistent chrome: brand bug, chapter tag, credit ---------- */
const Chrome: React.FC<{ chapter?: { n: string; title: string }; credit: string }> = ({ chapter, credit }) => (
  <>
    <div style={{ position: "absolute", top: 46, left: 60, display: "flex", alignItems: "center", gap: 14, background: "rgba(7,7,11,0.7)", padding: "10px 16px", borderRadius: 12 }}>
      <Mark size={30} /><span style={{ fontFamily: DISPLAY, fontWeight: 900, fontSize: 24, color: C.white }}>{BRAND.name}</span>
    </div>
    {chapter && (
      <div style={{ position: "absolute", top: 46, right: 60, display: "flex", alignItems: "center", gap: 12, background: C.lime, padding: "10px 16px", borderRadius: 12 }}>
        <span style={{ fontFamily: MONO, fontWeight: 700, fontSize: 22, color: C.ink, letterSpacing: 2 }}>{chapter.n} · {chapter.title}</span>
      </div>
    )}
    <div style={{ position: "absolute", bottom: 26, right: 60, fontFamily: MONO, fontSize: 16, color: "rgba(255,255,255,0.5)", letterSpacing: 2 }}>{credit}</div>
  </>
);

/* ---------- end screen: 20 s, element-safe layout ---------- */
const EndScreen: React.FC<{ tiles: string[]; clips: Clip[]; bed?: boolean }> = ({ tiles, clips, bed = true }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: f, fps, config: { damping: 16 } });
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ filter: "blur(18px) brightness(0.35)", transform: "scale(1.1)" }}>
        <Broll clips={clips.map((c) => ({ ...c, dur: c.dur * 2 }))} />
      </AbsoluteFill>
      <AbsoluteFill style={{ opacity: 0.4 }}><GridBG drift /></AbsoluteFill>
      <div style={{ position: "absolute", top: 110, left: 0, right: 0, textAlign: "center", fontFamily: DISPLAY, fontWeight: 900, fontSize: 70, color: C.white, opacity: s }}>KEEP PLAYING</div>
      {/* two video slots (YouTube end-screen elements go on top of these) */}
      {tiles.map((t, i) => (
        <div key={i} style={{
          position: "absolute", top: 300, left: 150 + i * 620, width: 560, height: 315, borderRadius: 16,
          border: `4px solid ${i === 0 ? C.lime : C.cyan}`, background: "rgba(7,7,11,0.6)",
          display: "flex", alignItems: "flex-end", padding: 18, transform: `translateY(${(1 - s) * 60}px)`, opacity: s,
        }}>
          <span style={{ fontFamily: MONO, fontWeight: 700, fontSize: 22, color: C.white, letterSpacing: 2 }}>{t}</span>
        </div>
      ))}
      {/* subscribe circle slot */}
      <div style={{ position: "absolute", top: 330, left: 1420, width: 260, height: 260, borderRadius: 999, border: `4px dashed ${C.lime}`, display: "flex", alignItems: "center", justifyContent: "center", opacity: s }}>
        <Mark size={110} />
      </div>
      <div style={{ position: "absolute", top: 640, left: 1360, width: 380, textAlign: "center", fontFamily: MONO, fontWeight: 700, fontSize: 24, color: C.lime, letterSpacing: 3 }}>SUBSCRIBE</div>
      <div style={{ position: "absolute", bottom: 120, left: 0, right: 0, textAlign: "center", fontFamily: MONO, fontWeight: 700, fontSize: 30, color: C.dim, letterSpacing: 8 }}>{BRAND.tagline}</div>
      {bed && <Audio src={staticFile("sfx/bed_loop.wav")} volume={(fr) => interpolate(fr, [0, 20, 560, 600], [0, 0.45, 0.45, 0])} />}
      <CRT strength={0.5} />
    </AbsoluteFill>
  );
};

/* ---------- main ---------- */
export const LongForm: React.FC<{ spec: LongSpec }> = ({ spec }) => {
  const { fps } = useVideoConfig();
  const f = useCurrentFrame();
  const coldF = Math.round(spec.cold.dur * fps);
  const bodyFrom = coldF + IDENT_FRAMES;
  const voF = Math.ceil(spec.timeline.duration * fps);
  const L = Object.fromEntries(spec.timeline.lines.map((l) => [l.id, l]));
  const tBody = (f - bodyFrom) / fps;
  const chapNow = [...spec.chapters].reverse().find((c) => L[c.line] && tBody >= L[c.line].start);
  const chapSkips = spec.chapters.map((c) => [L[c.line].start - 0.1, L[c.line].end + 0.6] as [number, number]);

  return (
    <AbsoluteFill style={{ background: C.ink }}>
      <Sequence durationInFrames={coldF}><ColdOpen cold={spec.cold} /></Sequence>
      <Sequence from={coldF} durationInFrames={IDENT_FRAMES}><Ident /></Sequence>

      <Sequence from={bodyFrom} durationInFrames={voF}>
        <Broll clips={spec.clips} />
        <AbsoluteFill style={{ background: "linear-gradient(90deg, rgba(7,7,11,0) 35%, rgba(7,7,11,0.55) 100%), linear-gradient(180deg, rgba(7,7,11,0.5) 0%, rgba(7,7,11,0) 18%, rgba(7,7,11,0) 75%, rgba(7,7,11,0.6) 100%)" }} />
        <Audio src={staticFile(spec.vo)} />
        {!spec.noBed && <Audio src={staticFile("sfx/bed_loop.wav")} loop volume={0.11} />}
        {spec.chapters.map((c, i) => {
          const l = L[c.line]; const from = Math.round(l.start * fps) - 4; const d = Math.round((l.end - l.start + 0.7) * fps);
          return (
            <Sequence key={i} from={from} durationInFrames={d}>
              <Audio src={staticFile("sfx/sting.wav")} volume={0.55} />
              <Chapter n={c.n} title={c.title} dur={d} />
            </Sequence>
          );
        })}
        {spec.cards.map((c, i) => {
          const l = L[c.line]; if (!l) return null;
          const from = Math.round(l.start * fps); const d = Math.round((l.end - l.start + 0.4) * fps);
          return (
            <Sequence key={`c${i}`} from={from} durationInFrames={d}>
              <Audio src={staticFile("sfx/whoosh.wav")} volume={0.3} />
              <AbsoluteFill style={{ alignItems: "flex-end", justifyContent: "center", paddingRight: 110 }}>
                <div style={{ transform: "scale(0.82)", transformOrigin: "right center" }}><LocalCard card={c} d={d} /></div>
              </AbsoluteFill>
            </Sequence>
          );
        })}
        <Subs words={spec.timeline.words} skip={chapSkips} drop={spec.chapters.map((c) => [L[c.line].start - 0.1, L[c.line].end + 0.1] as [number, number])} />
        <Chrome chapter={chapNow ? { n: chapNow.n, title: chapNow.title } : undefined} credit={spec.credit} />
        <CRT strength={0.35} />
      </Sequence>

      <Sequence from={bodyFrom + voF}><EndScreen tiles={spec.endTiles} clips={spec.clips.slice(0, 6)} bed={!spec.noBed} /></Sequence>
    </AbsoluteFill>
  );
};

const LocalCard: React.FC<{ card: Card; d: number }> = ({ card, d }) => {
  const f = useCurrentFrame();
  return <CardView card={card} local={f} dur={d} u={1} />;
};
