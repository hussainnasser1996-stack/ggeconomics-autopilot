import React from "react";
import { AbsoluteFill, Audio, CalculateMetadataFunction, Easing, interpolate, Sequence, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { BRAND, C, CRT, DISPLAY, Mark, MONO, SANS, useScale } from "../brand";
import { Broll, Clip } from "./NewsShort";

/** Weekly countdown (pilot 20 Nov 2026): no narration, music only, every rank change cut on the beat.
 *  Text lives in two bands (Husain's rule): top = series + rank + name, bottom = the number card. Middle = gameplay.
 *  No end card: #1 holds, then the video loops into the hook. */
export type TopEntry = {
  rank: number; name: string; clips: Clip[];
  players: number; playersLabel: string;
  price: string; priceNote?: string;
  move?: { text: string; up: boolean };
};
export type TopFiveSpec = {
  kicker: string; title: string; sub: string; question: string;
  hookClips: Clip[]; entries: TopEntry[]; credit: string;
  music: { src: string; start: number; volume?: number };
  beat: number; hookBeats: number; entryBeats: number; topBeats: number;
};

const fr = (s: TopFiveSpec, beats: number, fps: number) => Math.round(beats * s.beat * fps);
export const topFrames = (s: TopFiveSpec, fps = 30) =>
  fr(s, s.hookBeats, fps) + (s.entries.length - 1) * fr(s, s.entryBeats, fps) + fr(s, s.topBeats, fps);

export const topMetadata: CalculateMetadataFunction<{ spec: TopFiveSpec }> = async ({ props }) => ({ durationInFrames: topFrames(props.spec) });

const Chip: React.FC<{ children: React.ReactNode; bg: string; fg: string; u: number; size?: number }> = ({ children, bg, fg, u, size = 26 }) => (
  <div style={{ background: bg, color: fg, fontFamily: MONO, fontWeight: 700, fontSize: size * u, letterSpacing: 2 * u,
    padding: `${8 * u}px ${16 * u}px`, borderRadius: 10 * u, whiteSpace: "nowrap" }}>{children}</div>
);

const TopBar: React.FC<{ s: TopFiveSpec; active: number | null; u: number }> = ({ s, active, u }) => (
  <div style={{ position: "absolute", top: 110 * u, left: 0, right: 0, display: "flex", flexDirection: "column", alignItems: "center", gap: 18 * u }}>
    <div style={{ display: "flex", alignItems: "center", gap: 14 * u }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10 * u, background: "rgba(7,7,11,0.8)", padding: `${8 * u}px ${14 * u}px`, borderRadius: 10 * u }}>
        <Mark size={30 * u} />
        <span style={{ fontFamily: DISPLAY, fontWeight: 900, fontSize: 24 * u, color: C.white, letterSpacing: 1 * u }}>{BRAND.name}</span>
      </div>
      <Chip bg={C.lime} fg={C.ink} u={u} size={22}>{s.kicker}</Chip>
    </div>
    {/* rank pips: 5 4 3 2 1, the live one lit */}
    <div style={{ display: "flex", gap: 10 * u }}>
      {s.entries.map((e) => (
        <div key={e.rank} style={{ width: 54 * u, height: 54 * u, borderRadius: 12 * u, display: "flex", alignItems: "center", justifyContent: "center",
          fontFamily: DISPLAY, fontWeight: 900, fontSize: 28 * u,
          background: active === e.rank ? C.lime : active !== null && e.rank > active ? "rgba(212,255,58,0.25)" : "rgba(7,7,11,0.75)",
          color: active === e.rank ? C.ink : C.white, border: `${2 * u}px solid ${active === e.rank ? C.lime : C.line}` }}>{e.rank}</div>
      ))}
    </div>
  </div>
);

const Hook: React.FC<{ s: TopFiveSpec; d: number }> = ({ s, d }) => {
  const f = useCurrentFrame(); const { fps } = useVideoConfig(); const { u } = useScale();
  const pop = spring({ frame: f, fps, config: { damping: 11, stiffness: 180 } });
  return (
    <AbsoluteFill>
      <TopBar s={s} active={null} u={u} />
      <div style={{ position: "absolute", top: 330 * u, left: 0, right: 0, textAlign: "center", transform: `scale(${0.7 + 0.3 * pop})` }}>
        <div style={{ fontFamily: DISPLAY, fontWeight: 900, fontSize: 210 * u, color: C.lime, lineHeight: 0.9, letterSpacing: -6 * u,
          textShadow: `0 0 ${50 * u}px ${C.lime}66, ${6 * u}px ${6 * u}px 0 #000` }}>{s.title}</div>
        <div style={{ display: "inline-block", marginTop: 18 * u, fontFamily: DISPLAY, fontWeight: 900, fontSize: 58 * u, color: C.white, lineHeight: 1.1,
          background: "rgba(7,7,11,0.82)", padding: `${6 * u}px ${20 * u}px`, borderRadius: 12 * u, whiteSpace: "pre-line" }}>{s.sub}</div>
      </div>
      <div style={{ position: "absolute", bottom: 380 * u, left: 0, right: 0, textAlign: "center", opacity: interpolate(f, [d * 0.35, d * 0.5], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) }}>
        <span style={{ fontFamily: SANS, fontWeight: 800, fontSize: 44 * u, color: C.white, background: "rgba(7,7,11,0.8)", padding: `${8 * u}px ${20 * u}px`, borderRadius: 12 * u }}>{s.question}</span>
      </div>
    </AbsoluteFill>
  );
};

const Entry: React.FC<{ s: TopFiveSpec; e: TopEntry; d: number; top: boolean }> = ({ s, e, d, top }) => {
  const f = useCurrentFrame(); const { fps } = useVideoConfig(); const { u } = useScale();
  const slam = spring({ frame: f, fps, config: { damping: 9, stiffness: 220 } });
  const nameIn = spring({ frame: f - 3, fps, config: { damping: 14, stiffness: 160 } });
  const cardIn = spring({ frame: f - 6, fps, config: { damping: 14, stiffness: 150 } });
  const count = Math.round(e.players * interpolate(f, [6, 6 + Math.min(30, d * 0.45)], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) }));
  const flash = top ? interpolate(f, [0, 5], [0.7, 0], { extrapolateRight: "clamp" }) : interpolate(f, [0, 2], [0.3, 0], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ background: "#fff", opacity: flash }} />
      <TopBar s={s} active={e.rank} u={u} />
      {/* rank + name: top band */}
      <div style={{ position: "absolute", top: 300 * u, left: 0, right: 0, display: "flex", flexDirection: "column", alignItems: "center" }}>
        <div style={{ fontFamily: DISPLAY, fontWeight: 900, fontSize: (top ? 230 : 190) * u, color: top ? C.lime : C.white, lineHeight: 0.85,
          transform: `scale(${1.6 - 0.6 * slam})`, opacity: Math.min(1, slam * 1.5), textShadow: `0 0 ${50 * u}px ${top ? C.lime : "#000"}88, ${6 * u}px ${6 * u}px 0 #000` }}>#{e.rank}</div>
        <div style={{ marginTop: 12 * u, transform: `translateY(${(1 - nameIn) * 30 * u}px)`, opacity: nameIn,
          fontFamily: DISPLAY, fontWeight: 900, fontSize: (e.name.length > 18 ? 52 : 64) * u, color: C.white, textAlign: "center", lineHeight: 1.05,
          background: "rgba(7,7,11,0.82)", padding: `${6 * u}px ${20 * u}px`, borderRadius: 12 * u, maxWidth: 940 * u }}>{e.name}</div>
      </div>
      {/* number card: bottom band */}
      <div style={{ position: "absolute", bottom: 330 * u, left: 0, right: 0, display: "flex", justifyContent: "center",
        transform: `translateY(${(1 - cardIn) * 60 * u}px)`, opacity: cardIn }}>
        <div style={{ background: "rgba(7,7,11,0.86)", border: `${2 * u}px solid ${C.line}`, borderRadius: 22 * u, padding: `${22 * u}px ${34 * u}px`,
          display: "flex", flexDirection: "column", alignItems: "center", gap: 14 * u, minWidth: 640 * u }}>
          <div style={{ fontFamily: DISPLAY, fontWeight: 900, fontSize: 104 * u, color: top ? C.lime : C.white, lineHeight: 1, letterSpacing: -2 * u }}>{count.toLocaleString("en-US")}</div>
          <div style={{ fontFamily: MONO, fontWeight: 700, fontSize: 24 * u, color: C.dim, letterSpacing: 3 * u }}>{e.playersLabel}</div>
          <div style={{ display: "flex", gap: 12 * u, marginTop: 4 * u }}>
            <Chip bg={C.cyan} fg={C.ink} u={u}>{e.price}{e.priceNote ? ` ${e.priceNote}` : ""}</Chip>
            {e.move && <Chip bg={e.move.up ? C.lime : C.coral} fg={C.ink} u={u}>{e.move.up ? "▲" : "▼"} {e.move.text}</Chip>}
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

export const TopFive: React.FC<{ spec: TopFiveSpec }> = ({ spec: s }) => {
  const { fps } = useVideoConfig(); const { u } = useScale();
  const total = topFrames(s, fps);
  const hook = fr(s, s.hookBeats, fps), ent = fr(s, s.entryBeats, fps), topD = fr(s, s.topBeats, fps);
  const allClips = [...s.hookClips, ...s.entries.flatMap((e) => e.clips)];
  let at = hook;
  return (
    <AbsoluteFill style={{ background: C.ink }}>
      <Broll clips={allClips} />
      <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(7,7,11,0.7) 0%, rgba(7,7,11,0.0) 30%, rgba(7,7,11,0.0) 55%, rgba(7,7,11,0.75) 100%)" }} />
      <Audio src={staticFile(s.music.src)} startFrom={Math.round(s.music.start * fps)}
        volume={(f) => interpolate(f, [0, 3, total - 8, total], [0, s.music.volume ?? 0.9, s.music.volume ?? 0.9, 0], { extrapolateRight: "clamp" })} />
      <Sequence durationInFrames={hook}><Hook s={s} d={hook} /></Sequence>
      {s.entries.map((e, i) => {
        const isTop = i === s.entries.length - 1; const d = isTop ? topD : ent; const from = at; at += d;
        return <Sequence key={e.rank} from={from} durationInFrames={d}><Entry s={s} e={e} d={d} top={isTop} /></Sequence>;
      })}
      <div style={{ position: "absolute", bottom: 250 * u, left: 0, right: 0, textAlign: "center", fontFamily: MONO, fontSize: 19 * u, color: "rgba(255,255,255,0.6)", letterSpacing: 2 * u }}>{s.credit}</div>
      <CRT strength={0.4} />
    </AbsoluteFill>
  );
};
