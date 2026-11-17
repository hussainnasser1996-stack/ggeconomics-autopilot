import React from "react";
import { AbsoluteFill, Audio, interpolate, OffthreadVideo, Sequence, staticFile, useCurrentFrame, useVideoConfig, Easing } from "remotion";
import { BRAND, C, CRT, DISPLAY, Mark, MONO, SANS, useScale, RGBSplit } from "../brand";
import { Card, CardView } from "./Cards";

export type Clip = { src: string; from: number; dur: number; zoom?: number; x?: number };
export type Timeline = { duration: number; lines: { id: string; start: number; end: number }[]; words: { w: string; s: number; e: number }[] };
export type ShortSpec = {
  tag: string; topic: string; vo: string; timeline: Timeline; clips: Clip[]; cards: Card[];
  credit: string; endLine: string; noBed?: boolean; hideBroll?: boolean; headline?: string; sfxOn?: Record<string, string>; layout?: "full" | "feed";
};

export const END = 54; // frames of end card after VO
export const shortFrames = (s: ShortSpec, fps = 30) => Math.ceil(s.timeline.duration * fps) + END;

/** Full-bleed B-roll: cover-crop any source, slow push-in, hard cuts with a 2-frame flash */
export const Broll: React.FC<{ clips: Clip[] }> = ({ clips }) => {
  const { fps, width, height } = useVideoConfig();
  let at = 0;
  return (
    <>
      {clips.map((c, i) => {
        const from = Math.round(at * fps), d = Math.round(c.dur * fps); at += c.dur;
        return (
          <Sequence key={i} from={from} durationInFrames={d}>
            <ClipLayer c={c} d={d} w={width} h={height} />
          </Sequence>
        );
      })}
    </>
  );
};

const ClipLayer: React.FC<{ c: Clip; d: number; w: number; h: number }> = ({ c, d, w, h }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const push = interpolate(f, [0, d], [1, 1.03], { easing: Easing.inOut(Easing.sin) }) * (c.zoom ?? 1);
  const flash = interpolate(f, [0, 2], [0.35, 0], { extrapolateRight: "clamp" });
  // source is 16:9; cover the frame
  const srcAR = 16 / 9, dstAR = w / h;
  const vw = dstAR < srcAR ? h * srcAR : w, vh = dstAR < srcAR ? h : w / srcAR;
  const xShift = (c.x ?? 0) * (vw - w) / 2;
  return (
    <AbsoluteFill style={{ overflow: "hidden", background: "#000" }}>
      <OffthreadVideo
        src={staticFile(`footage/${c.src}.mp4`)} startFrom={Math.round(c.from * fps)} muted
        style={{ position: "absolute", width: vw, height: vh, left: (w - vw) / 2 - xShift, top: (h - vh) / 2, transform: `scale(${push})`, filter: "saturate(1.08) contrast(1.05)" }}
      />
      <AbsoluteFill style={{ background: "#fff", opacity: flash }} />
    </AbsoluteFill>
  );
};

/** Word-by-word captions, chunks of up to 3 words, active word lime */
export const Captions: React.FC<{ words: Timeline["words"]; y: number; padL?: number; padR?: number }> = ({ words, y, padL, padR }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { u } = useScale();
  const t = f / fps;
  // chunk by max 3 words or punctuation
  const chunks: Timeline["words"][] = [];
  let cur: Timeline["words"] = [];
  // merge tokens Whisper splits ("$3" ".35", "pre" "-orders")
  const merged: Timeline["words"] = [];
  words.forEach((w) => {
    const prev = merged[merged.length - 1];
    if (prev && /^[.\-%]/.test(w.w) && !/^-$/.test(w.w)) { prev.w += w.w; prev.e = w.e; } else merged.push({ ...w });
  });
  merged.forEach((w) => {
    cur.push(w);
    if (cur.length >= 2 || /[.,?!:]$/.test(w.w)) { chunks.push(cur); cur = []; }
  });
  if (cur.length) chunks.push(cur);
  const ch = chunks.find((c, i) => t >= c[0].s - 0.05 && t < (chunks[i + 1]?.[0].s ?? c[c.length - 1].e + 0.4));
  if (!ch) return null;
  const local = (t - ch[0].s) * fps;
  const pop = interpolate(local, [0, 4], [0.85, 1], { extrapolateRight: "clamp", easing: Easing.out(Easing.back(2)) });
  return (
    <div style={{ position: "absolute", top: y, left: padL ?? 60 * u, right: padR ?? 60 * u, display: "flex", justifyContent: "center", flexWrap: "wrap", gap: `0 ${18 * u}px`, transform: `scale(${pop})` }}>
      {ch.map((w, i) => {
        const on = t >= w.s - 0.03;
        const active = t >= w.s - 0.03 && t < w.e + 0.05;
        return (
          <span key={i} style={{
            fontFamily: SANS, fontWeight: 900, fontSize: 88 * u, textTransform: "uppercase", letterSpacing: -1 * u,
            color: active ? C.ink : on ? C.white : "rgba(255,255,255,0.45)",
            background: active ? C.lime : "transparent", padding: `0 ${10 * u}px`, borderRadius: 10 * u,
            WebkitTextStroke: active ? "none" : `${2 * u}px rgba(0,0,0,0.6)`,
            textShadow: active ? "none" : `0 ${4 * u}px ${18 * u}px rgba(0,0,0,0.9)`,
          }}>{w.w}</span>
        );
      })}
    </div>
  );
};

const TopBar: React.FC<{ spec: ShortSpec; total: number; padL?: number; padR?: number }> = ({ spec, total, padL = 0, padR = 0 }) => {
  const f = useCurrentFrame();
  const { u } = useScale();
  const p = f / total;
  const blink = Math.floor(f / 15) % 2 === 0;
  return (
    <>
      <div style={{ position: "absolute", top: 0, left: 0, height: 8 * u, width: `${p * 100}%`, background: C.lime, boxShadow: `0 0 ${16 * u}px ${C.lime}` }} />
      <div style={{ position: "absolute", top: 120 * u, left: padL, right: padR, display: "flex", justifyContent: "center", gap: 14 * u, alignItems: "center" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 * u, background: "rgba(7,7,11,0.8)", padding: `${10 * u}px ${18 * u}px`, borderRadius: 12 * u, border: `${2 * u}px solid ${C.line}` }}>
          <Mark size={30 * u} />
          <span style={{ fontFamily: DISPLAY, fontWeight: 900, fontSize: 26 * u, color: C.white, letterSpacing: 1 * u }}>{BRAND.name}</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 10 * u, background: C.lime, padding: `${10 * u}px ${18 * u}px`, borderRadius: 12 * u }}>
          <div style={{ width: 12 * u, height: 12 * u, borderRadius: 99, background: C.coral, opacity: blink ? 1 : 0.25 }} />
          <span style={{ fontFamily: MONO, fontWeight: 700, fontSize: 26 * u, color: C.ink, letterSpacing: 2 * u }}>{spec.tag}</span>
        </div>
      </div>
    </>
  );
};

/** Persistent headline (the topic, readable from frame 0 to the end) — benchmark: every top news Short does this */
const Headline: React.FC<{ text: string; top: number; padL: number; padR: number; voEnd: number }> = ({ text, top, padL, padR, voEnd }) => {
  const f = useCurrentFrame();
  const { u } = useScale();
  const o = interpolate(f, [voEnd - 8, voEnd], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <div style={{ position: "absolute", top, left: padL + 40 * u, right: padR + 40 * u, textAlign: "center", opacity: o }}>
      <span style={{ fontFamily: DISPLAY, fontWeight: 900, fontSize: 54 * u, lineHeight: 1.12, color: C.white, letterSpacing: -1 * u,
        background: "rgba(7,7,11,0.82)", boxDecorationBreak: "clone", WebkitBoxDecorationBreak: "clone", padding: `${4 * u}px ${16 * u}px`, borderRadius: 10 * u }}>
        {text.split("|").map((t, i) => <span key={i} style={{ color: i % 2 ? C.lime : C.white }}>{t}</span>)}
      </span>
    </div>
  );
};

const EndCard: React.FC<{ line: string }> = ({ line }) => {
  const f = useCurrentFrame();
  const { u } = useScale();
  const s = interpolate(f, [0, 8], [1.3, 1], { extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  const split = interpolate(f, [8, 20], [20, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) * u;
  const o = interpolate(f, [6, 10], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ background: "rgba(7,7,11,0.92)", alignItems: "center", justifyContent: "center", flexDirection: "column", gap: 30 * u, opacity: o }}>
      <div style={{ transform: `scale(${s})`, display: "flex", flexDirection: "column", alignItems: "center", gap: 26 * u }}>
        <Mark size={110 * u} />
        <RGBSplit amount={split}>
          <div style={{ fontFamily: DISPLAY, fontWeight: 900, fontSize: 110 * u, color: C.white, lineHeight: 0.95, textAlign: "center", whiteSpace: "pre-line" }}>{BRAND.name.replace(" ", "\n")}</div>
        </RGBSplit>
      </div>
      <div style={{ fontFamily: MONO, fontWeight: 700, fontSize: 30 * u, color: C.lime, letterSpacing: 4 * u, textAlign: "center" }}>{line}</div>
    </AbsoluteFill>
  );
};

export const NewsShort: React.FC<{ spec: ShortSpec }> = ({ spec }) => {
  const { fps, height } = useVideoConfig();
  const { u } = useScale();
  const total = shortFrames(spec, fps);
  const voEnd = Math.ceil(spec.timeline.duration * fps);
  const { width } = useVideoConfig();
  const compact = height / width < 1.5; // 4:5 feed or square
  const L = compact
    ? { cardTop: height * 0.15, cardScale: 0.7, capY: height * 0.74, creditBottom: 26 * u, padL: 0, padR: 0 }
    : { cardTop: height * 0.2, cardScale: 0.88, capY: height * 0.66, creditBottom: 360 * u, padL: width * 0.04, padR: width * 0.13 };
  if (spec.headline && !compact) L.cardTop += 130 * u;      // make room for the persistent headline
  const lineById = Object.fromEntries(spec.timeline.lines.map((l) => [l.id, l]));
  return (
    <AbsoluteFill style={{ background: C.ink }}>
      {!spec.hideBroll && <Broll clips={spec.clips} />}
      {/* legibility gradients */}
      <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(7,7,11,0.75) 0%, rgba(7,7,11,0.0) 22%, rgba(7,7,11,0.0) 45%, rgba(7,7,11,0.85) 100%)" }} />
      <Audio src={staticFile(spec.vo)} />
      {!spec.noBed && <Audio src={staticFile("sfx/bed_loop.wav")} volume={(f) => interpolate(f, [0, 10, voEnd, voEnd + 20], [0, 0.16, 0.16, 0], { extrapolateRight: "clamp" })} />}
      {/* cards, keyed to VO lines */}
      {spec.cards.map((c, i) => {
        const l = lineById[c.line]; if (!l) return null;
        const isFirst = i === 0;
        const from = isFirst ? -14 : Math.round(l.start * fps) - 3;               // hook card already on screen at frame 0
        const d = Math.round(l.end * fps) - from + 10;
        return (
          <Sequence key={i} from={from} durationInFrames={d}>
            {/* no whoosh on text changes: Husain 17 Nov, it sounds AI-made */}
            <AbsoluteFill style={{ alignItems: "center", justifyContent: "flex-start", paddingTop: L.cardTop, paddingLeft: L.padL, paddingRight: L.padR }}>
              <div style={{ transform: `scale(${L.cardScale})`, transformOrigin: "top center" }}><CardLocal card={c} d={d} u={u} /></div>
            </AbsoluteFill>
          </Sequence>
        );
      })}
      {spec.headline && <Headline text={spec.headline} top={205 * u} padL={L.padL} padR={L.padR} voEnd={voEnd} />}
      <Captions words={spec.timeline.words} y={L.capY} padL={L.padL} padR={L.padR} />
      <TopBar spec={spec} total={total} padR={L.padR} padL={L.padL} />
      <div style={{ position: "absolute", bottom: L.creditBottom, left: L.padL, right: L.padR, textAlign: "center", fontFamily: MONO, fontSize: 20 * u, color: "rgba(255,255,255,0.55)", letterSpacing: 2 * u }}>{spec.credit}</div>
      <Sequence from={voEnd - 6}>
        <Audio src={staticFile("sfx/sting.wav")} volume={0.9} />
        <EndCard line={spec.endLine} />
      </Sequence>
      <CRT strength={0.5} />
    </AbsoluteFill>
  );
};

const CardLocal: React.FC<{ card: Card; d: number; u: number }> = ({ card, d, u }) => {
  const f = useCurrentFrame();
  return <CardView card={card} local={f} dur={d} u={u} />;
};
