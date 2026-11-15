import React from "react";
import { AbsoluteFill, Audio, interpolate, OffthreadVideo, Sequence, spring, staticFile, useCurrentFrame, useVideoConfig, Easing } from "remotion";
import { BRAND, C, CRT, DISPLAY, GlitchSlices, GridBG, Mark, MONO, RGBSplit, SANS } from "../brand";
import { Ident, IDENT_FRAMES } from "../Ident";

export type Tip = { at: number; dur: number; kind: "objective" | "tip" | "boss" | "item"; title: string; body?: string };
export type Segment = { src: string; from: number; dur: number; place: string; tips: Tip[] };
export type WalkSpec = { game: string; part: string; title: string; segments: Segment[] };

const TITLE = 120, GAP = 24, ENDF = 300;
export const walkFrames = (s: WalkSpec, fps = 30) =>
  IDENT_FRAMES + TITLE + s.segments.reduce((a, g) => a + Math.round(g.dur * fps) + GAP, 0) + ENDF;

const fmt = (sec: number) => `${String(Math.floor(sec / 60)).padStart(2, "0")}:${String(Math.floor(sec % 60)).padStart(2, "0")}`;

const TitleCard: React.FC<{ spec: WalkSpec }> = ({ spec }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: f, fps, config: { damping: 15 } });
  const seg = spec.segments[0];
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ filter: "blur(10px) brightness(0.35)", transform: "scale(1.08)" }}>
        <OffthreadVideo src={staticFile(`footage/${seg.src}.mp4`)} startFrom={Math.round(seg.from * fps)} muted />
      </AbsoluteFill>
      <AbsoluteFill style={{ justifyContent: "center", paddingLeft: 150, flexDirection: "column" }}>
        <div style={{ fontFamily: MONO, fontWeight: 700, fontSize: 34, color: C.lime, letterSpacing: 10, opacity: s }}>{spec.game} · WALKTHROUGH</div>
        <RGBSplit amount={interpolate(f, [0, 12], [22, 0], { extrapolateRight: "clamp" })}>
          <div style={{ fontFamily: DISPLAY, fontWeight: 900, fontSize: 170, color: C.white, lineHeight: 1, letterSpacing: -5, transform: `translateX(${(1 - s) * 80}px)` }}>{spec.part}</div>
        </RGBSplit>
        <div style={{ fontFamily: SANS, fontWeight: 800, fontSize: 56, color: C.white, marginTop: 14, opacity: s }}>{spec.title}</div>
        <div style={{ display: "flex", gap: 12, marginTop: 40 }}>
          {spec.segments.map((g, i) => (
            <div key={i} style={{ fontFamily: MONO, fontWeight: 700, fontSize: 20, color: C.dim, border: `2px solid ${C.line}`, padding: "6px 12px", borderRadius: 8, opacity: interpolate(f, [10 + i * 4, 18 + i * 4], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) }}>
              {String(i + 1).padStart(2, "0")} {g.place}
            </div>
          ))}
        </div>
      </AbsoluteFill>
      <CRT strength={0.4} />
    </AbsoluteFill>
  );
};

const TipCard: React.FC<{ tip: Tip; d: number }> = ({ tip, d }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: f, fps, config: { damping: 15, stiffness: 170 } });
  const out = interpolate(f, [d - 8, d], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const col = { objective: C.lime, tip: C.cyan, boss: C.coral, item: C.white }[tip.kind];
  const label = { objective: "OBJECTIVE", tip: "TIP", boss: "BOSS", item: "ITEM" }[tip.kind];
  return (
    <div style={{
      position: "absolute", right: 60, top: 300, maxWidth: 640, opacity: out,
      transform: `translateX(${(1 - s) * 80}px)`, display: "flex", background: "rgba(7,7,11,0.86)", borderRadius: 14, overflow: "hidden",
      boxShadow: "0 20px 60px rgba(0,0,0,0.5)", border: `2px solid ${C.line}`,
    }}>
      <div style={{ width: 10, background: col }} />
      <div style={{ padding: "18px 24px" }}>
        <div style={{ fontFamily: MONO, fontWeight: 700, fontSize: 20, color: col, letterSpacing: 4 }}>{label}</div>
        <div style={{ fontFamily: SANS, fontWeight: 800, fontSize: 38, color: C.white, marginTop: 4 }}>{tip.title}</div>
        {tip.body && <div style={{ fontFamily: SANS, fontWeight: 500, fontSize: 26, color: "#D6D6DE", marginTop: 8, lineHeight: 1.3 }}>{tip.body}</div>}
      </div>
    </div>
  );
};

const SegmentView: React.FC<{ seg: Segment; idx: number; spec: WalkSpec }> = ({ seg, idx, spec }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const d = Math.round(seg.dur * fps);
  const chipIn = spring({ frame: f - 4, fps, config: { damping: 14 } });
  const vol = interpolate(f, [0, 8, d - 8, d], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <AbsoluteFill>
      <OffthreadVideo src={staticFile(`footage/${seg.src}.mp4`)} startFrom={Math.round(seg.from * fps)} volume={vol * 0.9} />
      <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(7,7,11,0.45) 0%, rgba(7,7,11,0) 16%, rgba(7,7,11,0) 70%, rgba(7,7,11,0.65) 100%)" }} />
      {/* brand bug */}
      <div style={{ position: "absolute", bottom: 84, right: 60, display: "flex", alignItems: "center", gap: 10, opacity: 0.75 }}>
        <Mark size={26} /><span style={{ fontFamily: DISPLAY, fontWeight: 900, fontSize: 18, color: C.white, textShadow: "0 2px 10px #000" }}>{BRAND.name}</span>
      </div>
      {/* location chip */}
      <div style={{ position: "absolute", top: 40, right: 60, display: "flex", alignItems: "center", gap: 0, transform: `translateY(${(1 - chipIn) * -40}px)`, opacity: chipIn }}>
        <div style={{ background: C.lime, padding: "10px 14px", fontFamily: MONO, fontWeight: 700, fontSize: 22, color: C.ink, borderRadius: "10px 0 0 10px" }}>{String(idx + 1).padStart(2, "0")}</div>
        <div style={{ background: "rgba(7,7,11,0.85)", padding: "10px 18px", fontFamily: MONO, fontWeight: 700, fontSize: 22, color: C.white, letterSpacing: 2, borderRadius: "0 10px 10px 0" }}>{seg.place}</div>
      </div>
      {/* source timestamp — honest: where in the run this is */}
      <div style={{ position: "absolute", top: 92, right: 60, fontFamily: MONO, fontSize: 18, color: "rgba(255,255,255,0.6)", letterSpacing: 2 }}>RUN TIME {fmt(seg.from + f / fps)}</div>
      {seg.tips.map((t, i) => (
        <Sequence key={i} from={Math.round(t.at * fps)} durationInFrames={Math.round(t.dur * fps)}>
          <Audio src={staticFile("sfx/blip.wav")} volume={0.35} />
          <TipCard tip={t} d={Math.round(t.dur * fps)} />
        </Sequence>
      ))}
      {/* chapter progress bar */}
      <div style={{ position: "absolute", left: 60, right: 60, bottom: 40, display: "flex", gap: 8 }}>
        {spec.segments.map((g, i) => {
          const p = i < idx ? 1 : i > idx ? 0 : f / d;
          return (
            <div key={i} style={{ flex: g.dur, height: 8, background: "rgba(255,255,255,0.2)", borderRadius: 4, overflow: "hidden" }}>
              <div style={{ width: `${p * 100}%`, height: "100%", background: C.lime }} />
            </div>
          );
        })}
      </div>
      <div style={{ position: "absolute", left: 60, bottom: 56, fontFamily: MONO, fontSize: 18, color: "rgba(255,255,255,0.7)", letterSpacing: 2 }}>{spec.game} · {spec.part}</div>
      <CRT strength={0.2} />
    </AbsoluteFill>
  );
};

/** Between segments: a 'GAME SAVED' snap */
const SaveSnap: React.FC<{ next: string }> = ({ next }) => {
  const f = useCurrentFrame();
  const o = interpolate(f, [0, 3, GAP - 4, GAP], [0, 1, 1, 0]);
  return (
    <AbsoluteFill style={{ background: C.ink, opacity: o, alignItems: "center", justifyContent: "center", flexDirection: "column", gap: 20 }}>
      <Audio src={staticFile("sfx/chime.wav")} volume={0.4} />
      <GlitchSlices intensity={f < 5 ? 0.8 : 0} seed={`snap${next}`}>
        <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", flexDirection: "column", gap: 18 }}>
          <Mark size={80} />
          <div style={{ fontFamily: MONO, fontWeight: 700, fontSize: 26, color: C.lime, letterSpacing: 8 }}>◆ GAME SAVED</div>
          <div style={{ fontFamily: DISPLAY, fontWeight: 900, fontSize: 64, color: C.white }}>{next}</div>
        </AbsoluteFill>
      </GlitchSlices>
    </AbsoluteFill>
  );
};

const WalkEnd: React.FC = () => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: f, fps, config: { damping: 16 } });
  return (
    <AbsoluteFill>
      <GridBG />
      <Audio src={staticFile("sfx/bed_loop.wav")} volume={(fr) => interpolate(fr, [0, 15, ENDF - 30, ENDF], [0, 0.45, 0.45, 0])} />
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", flexDirection: "column", gap: 30, opacity: s }}>
        <div style={{ fontFamily: DISPLAY, fontWeight: 900, fontSize: 80, color: C.white }}>NEXT: PART 2</div>
        <div style={{ display: "flex", gap: 60 }}>
          {["▶ PART 2", "▶ GTA VI · THE $1B BET"].map((t, i) => (
            <div key={i} style={{ width: 560, height: 315, border: `4px solid ${i ? C.cyan : C.lime}`, borderRadius: 16, display: "flex", alignItems: "flex-end", padding: 18, fontFamily: MONO, fontWeight: 700, fontSize: 22, color: C.white }}>{t}</div>
          ))}
        </div>
        <div style={{ fontFamily: MONO, fontWeight: 700, fontSize: 28, color: C.lime, letterSpacing: 8 }}>{BRAND.tagline}</div>
      </AbsoluteFill>
      <CRT strength={0.5} />
    </AbsoluteFill>
  );
};

export const Walkthrough: React.FC<{ spec: WalkSpec }> = ({ spec }) => {
  const { fps } = useVideoConfig();
  let at = IDENT_FRAMES + TITLE;
  const items: React.ReactNode[] = [];
  spec.segments.forEach((g, i) => {
    const d = Math.round(g.dur * fps);
    items.push(<Sequence key={`s${i}`} from={at} durationInFrames={d}><SegmentView seg={g} idx={i} spec={spec} /></Sequence>);
    at += d;
    const next = spec.segments[i + 1]?.place ?? "TO BE CONTINUED";
    items.push(<Sequence key={`g${i}`} from={at - 4} durationInFrames={GAP + 4}><SaveSnap next={next} /></Sequence>);
    at += GAP;
  });
  return (
    <AbsoluteFill style={{ background: C.ink }}>
      <Sequence durationInFrames={IDENT_FRAMES}><Ident /></Sequence>
      <Sequence from={IDENT_FRAMES} durationInFrames={TITLE}><Audio src={staticFile("sfx/whoosh.wav")} volume={0.5} /><TitleCard spec={spec} /></Sequence>
      {items}
      <Sequence from={at}><WalkEnd /></Sequence>
    </AbsoluteFill>
  );
};
