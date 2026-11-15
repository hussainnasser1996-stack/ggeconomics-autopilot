import React from "react";
import { AbsoluteFill, Audio, interpolate, OffthreadVideo, random, staticFile, useCurrentFrame, useVideoConfig, Easing, Loop } from "remotion";
import { BRAND, C, CRT, DISPLAY, GridBG, Mark, MONO, RGBSplit, SANS } from "../brand";

export const TICKER = [
  "GTA VI LAUNCHES NOV 19 · PS5 + XBOX SERIES X|S",
  "STANDARD $79.99 · ULTIMATE $99.99",
  "SENSOR TOWER: $1B+ EST. DIGITAL PRE-ORDERS",
  "TAKE-TWO GUIDES $3.35–3.5B NET BOOKINGS OCT–DEC",
  "XBOX CLOUD STREAMING OPENS 1 AM ET LAUNCH DAY",
];

/** Seamless scrolling ticker: loop length = frames for one full pass */
export const LOOP = 1152; // = bed_loop.wav (16 bars @100bpm = 38.4 s)
export const Ticker: React.FC<{ y?: number; height?: number }> = ({ y, height = 64 }) => {
  const f = useCurrentFrame();
  const text = TICKER.map((t) => `◆ ${t}`).join("     ");
  const tileW = 4200; // fixed tile; LOOP frames move exactly one tile -> seamless
  const x = -(((f % LOOP) / LOOP) * tileW);
  return (
    <div style={{ position: "absolute", left: 0, right: 0, top: y, bottom: y === undefined ? 0 : undefined, height, background: C.ink, borderTop: `3px solid ${C.lime}`, overflow: "hidden", display: "flex", alignItems: "center" }}>
      <div style={{ position: "absolute", left: 0, top: 0, bottom: 0, zIndex: 2, background: C.lime, display: "flex", alignItems: "center", padding: "0 22px", gap: 10 }}>
        <Mark size={30} color={C.ink} label={C.lime} />
        <span style={{ fontFamily: DISPLAY, fontWeight: 900, fontSize: 22, color: C.ink }}>NEWS</span>
      </div>
      <div style={{ position: "absolute", left: 180, whiteSpace: "nowrap", transform: `translateX(${x}px)`, fontFamily: MONO, fontWeight: 700, fontSize: 26, color: C.white, letterSpacing: 0 }}>
        <span style={{ display: "inline-block", width: tileW }}>{text}</span><span style={{ display: "inline-block", width: tileW }}>{text}</span>
      </div>
    </div>
  );
};

/** Starting Soon / BRB — designed to loop seamlessly (all motion periodic on `period`) */
export const HoldScreen: React.FC<{ title: string; sub: string; period: number }> = ({ title, sub, period }) => {
  const f = useCurrentFrame();
  const ph = (f % period) / period;
  const blocks = 12;
  const filled = Math.floor(ph * (blocks + 3)) % (blocks + 3);
  const bob = Math.sin(ph * Math.PI * 2) * 10;
  const glitch = (f % 96) < 3; // 96 | 1152
  return (
    <AbsoluteFill>
      <GridBG />
      <Audio src={staticFile("sfx/bed_loop.wav")} volume={0.5} loop />
      {/* floating pixels, periodic */}
      {Array.from({ length: 26 }).map((_, i) => {
        const x = random(`x${i}`) * 1920, sp = 1 + Math.floor(random(`s${i}`) * 3);
        const yy = 1080 - ((ph * sp + random(`y${i}`)) % 1) * 1240;
        const sz = 6 + random(`z${i}`) * 12;
        return <div key={i} style={{ position: "absolute", left: x, top: yy, width: sz, height: sz, background: [C.lime, C.cyan, C.white][i % 3], opacity: 0.35 }} />;
      })}
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", flexDirection: "column", gap: 34, transform: `translateY(${bob - 40}px)` }}>
        <Mark size={130} />
        <RGBSplit amount={glitch ? 16 : 0}>
          <div style={{ fontFamily: DISPLAY, fontWeight: 900, fontSize: 132, color: C.white, letterSpacing: -3, textAlign: "center", lineHeight: 1 }}>{title}</div>
        </RGBSplit>
        <div style={{ display: "flex", gap: 10 }}>
          {Array.from({ length: blocks }).map((_, i) => (
            <div key={i} style={{ width: 34, height: 34, border: `4px solid ${i < filled ? C.lime : C.line}`, background: i < filled ? C.lime : "transparent", boxShadow: i < filled ? `0 0 14px ${C.lime}` : "none" }} />
          ))}
        </div>
        <div style={{ fontFamily: MONO, fontWeight: 700, fontSize: 32, color: C.lime, letterSpacing: 8 }}>{sub}{Math.floor(f / 16) % 2 ? "_" : " "}</div>
      </AbsoluteFill>
      <Ticker />
      <CRT strength={0.6} />
    </AbsoluteFill>
  );
};

/** OBS stinger: transparent background; full cover at frame 12 (set OBS transition point = 400 ms) */
export const Stinger: React.FC = () => {
  const f = useCurrentFrame();
  const bars = 6;
  return (
    <AbsoluteFill>
      <Audio src={staticFile("sfx/sting.wav")} />
      {Array.from({ length: bars }).map((_, i) => {
        const d = i * 1.2;
        const inX = interpolate(f, [d, d + 9], [-110, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
        const outX = interpolate(f, [16 + d, 25 + d], [0, 110], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.in(Easing.cubic) });
        return <div key={i} style={{ position: "absolute", left: 0, right: 0, top: `${(i / bars) * 100}%`, height: `${100 / bars + 0.3}%`, background: i % 2 ? C.ink : C.lime, transform: `translateX(${inX + outX}%)` }} />;
      })}
      {f >= 8 && f <= 22 && (
        <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", transform: `scale(${interpolate(f, [8, 12, 22], [1.4, 1, 0.9])})`, opacity: interpolate(f, [8, 10, 19, 22], [0, 1, 1, 0]) }}>
          <div style={{ background: C.ink, padding: 40, borderRadius: 30, border: `6px solid ${C.lime}` }}><Mark size={180} /></div>
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};

/** Live overlay (render as PNG with alpha): webcam frame, brand bug, now-playing, ticker */
export const LiveOverlay: React.FC<{ game: string; showGame?: boolean; demoSrc?: string; demoFrom?: number }> = ({ game, demoSrc, demoFrom = 0 }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  return (
    <AbsoluteFill>
      {demoSrc && <OffthreadVideo src={staticFile(`footage/${demoSrc}.mp4`)} startFrom={Math.round(demoFrom * fps)} volume={0.5} style={{ width: "100%", height: "100%" }} />}
      {/* brand bug */}
      <div style={{ position: "absolute", top: 30, left: 30, display: "flex", alignItems: "center", gap: 12, background: "rgba(7,7,11,0.8)", padding: "10px 16px", borderRadius: 12, border: `2px solid ${C.line}` }}>
        <Mark size={30} /><span style={{ fontFamily: DISPLAY, fontWeight: 900, fontSize: 22, color: C.white }}>{BRAND.name}</span>
        <span style={{ marginLeft: 8, display: "flex", alignItems: "center", gap: 8, background: C.coral, padding: "4px 10px", borderRadius: 6 }}>
          <span style={{ width: 9, height: 9, borderRadius: 9, background: C.white, opacity: Math.floor(f / 24) % 2 ? 1 : 0.3 }} />
          <span style={{ fontFamily: MONO, fontWeight: 700, fontSize: 18, color: C.white }}>LIVE</span>
        </span>
      </div>
      {/* now playing */}
      <div style={{ position: "absolute", top: 30, right: 30, background: "rgba(7,7,11,0.8)", padding: "10px 18px", borderRadius: 12, border: `2px solid ${C.line}`, textAlign: "right" }}>
        <div style={{ fontFamily: MONO, fontWeight: 700, fontSize: 16, color: C.dim, letterSpacing: 3 }}>NOW PLAYING</div>
        <div style={{ fontFamily: SANS, fontWeight: 800, fontSize: 28, color: C.lime }}>{game}</div>
      </div>
      {/* webcam frame (transparent hole) */}
      <div style={{ position: "absolute", right: 30, bottom: 100, width: 420, height: 236, borderRadius: 16, border: `5px solid ${C.lime}`, boxShadow: `0 0 30px ${C.lime}55` }}>
        <div style={{ position: "absolute", left: -5, bottom: -40, background: C.lime, padding: "4px 12px", borderRadius: "0 0 10px 10px", fontFamily: MONO, fontWeight: 700, fontSize: 18, color: C.ink, letterSpacing: 2 }}>{BRAND.handle}</div>
        {demoSrc && <AbsoluteFill style={{ background: "rgba(7,7,11,0.85)", alignItems: "center", justifyContent: "center", fontFamily: MONO, color: C.dim, fontSize: 20, borderRadius: 12 }}>WEBCAM</AbsoluteFill>}
      </div>
      <Ticker />
    </AbsoluteFill>
  );
};
