import React from "react";
import { AbsoluteFill, OffthreadVideo, staticFile } from "remotion";
import { BRAND, C, DISPLAY, Mark, MONO, SANS } from "../brand";
import { Card, CardView } from "./Cards";

export type Slide = { bg: { src: string; at: number }; kicker: string; card?: Card; head?: string; sub?: string };

export const CarouselSlide: React.FC<{ slides: Slide[]; i: number; credit: string }> = ({ slides, i, credit }) => {
  const s = slides[i];
  return (
    <AbsoluteFill style={{ background: C.ink }}>
      <OffthreadVideo src={staticFile(`footage/${s.bg.src}.mp4`)} startFrom={Math.round(s.bg.at * 30)} muted
        style={{ position: "absolute", height: "100%", left: "50%", transform: "translateX(-50%) scale(1.12)", filter: i === 0 ? "brightness(0.75)" : "brightness(0.42) blur(2px)" }} />
      <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(7,7,11,0.7) 0%, rgba(7,7,11,0) 25%, rgba(7,7,11,0) 60%, rgba(7,7,11,0.9) 100%)" }} />
      <div style={{ position: "absolute", top: 56, left: 60, display: "flex", alignItems: "center", gap: 12 }}>
        <Mark size={36} /><span style={{ fontFamily: DISPLAY, fontWeight: 900, fontSize: 28, color: C.white }}>{BRAND.name}</span>
      </div>
      <div style={{ position: "absolute", top: 60, right: 60, fontFamily: MONO, fontWeight: 700, fontSize: 26, color: C.dim, letterSpacing: 3 }}>{i + 1}/{slides.length}</div>
      <div style={{ position: "absolute", top: 150, left: 60, right: 60, fontFamily: MONO, fontWeight: 700, fontSize: 30, color: C.lime, letterSpacing: 5 }}>{s.kicker}</div>
      {s.head && (
        <div style={{ position: "absolute", left: 60, right: 60, bottom: 250, fontFamily: DISPLAY, fontWeight: 900, fontSize: i === 0 ? 108 : 84, color: C.white, lineHeight: 0.98, letterSpacing: -3, whiteSpace: "pre-line" }}>
          {s.head.split("|").map((t, k) => <span key={k} style={{ color: k % 2 ? C.lime : C.white }}>{t}</span>)}
        </div>
      )}
      {s.card && (
        <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
          <CardView card={s.card} local={40} dur={1000} u={1.05} />
        </AbsoluteFill>
      )}
      {s.sub && <div style={{ position: "absolute", left: 60, right: 60, bottom: 140, fontFamily: SANS, fontWeight: 600, fontSize: 36, color: "#D6D6DE", lineHeight: 1.3 }}>{s.sub}</div>}
      <div style={{ position: "absolute", left: 60, right: 60, bottom: 56, display: "flex", justifyContent: "space-between", fontFamily: MONO, fontSize: 18, color: "rgba(255,255,255,0.5)", letterSpacing: 2 }}>
        <span>{credit}</span><span style={{ color: i < slides.length - 1 ? C.lime : C.dim }}>{i < slides.length - 1 ? "SWIPE →" : BRAND.handle}</span>
      </div>
    </AbsoluteFill>
  );
};
