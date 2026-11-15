import React from "react";
import { AbsoluteFill } from "remotion";
import { BRAND, C, DISPLAY, GridBG, Mark, MONO } from "./brand";

export const Avatar: React.FC = () => (
  <AbsoluteFill style={{ background: C.ink, alignItems: "center", justifyContent: "center" }}>
    <GridBG drift={false} />
    <div style={{ filter: `drop-shadow(0 0 60px ${C.lime}88)` }}><Mark size={520} /></div>
  </AbsoluteFill>
);

/** YouTube banner 2560x1440; everything important inside the 1546x423 centre safe area */
export const Banner: React.FC = () => (
  <AbsoluteFill style={{ background: C.ink }}>
    <GridBG drift={false} />
    <AbsoluteFill style={{ background: `radial-gradient(ellipse 900px 300px at 50% 50%, ${C.lime}22, transparent)` }} />
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", flexDirection: "column", gap: 16 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 28 }}>
        <Mark size={130} />
        <div style={{ fontFamily: DISPLAY, fontWeight: 900, fontSize: 128, color: C.white, letterSpacing: -4, lineHeight: 1 }}>{BRAND.name}</div>
      </div>
      <div style={{ fontFamily: MONO, fontWeight: 700, fontSize: 38, color: C.lime, letterSpacing: 14 }}>{BRAND.tagline}</div>
      <div style={{ fontFamily: MONO, fontWeight: 500, fontSize: 26, color: C.dim, letterSpacing: 6, marginTop: 2 }}>NEW SHORT EVERY DAY · 6 PM ET</div>
    </AbsoluteFill>
  </AbsoluteFill>
);

/** debug: draw the 1546x423 all-devices safe box */
export const BannerSafe: React.FC = () => (<AbsoluteFill><Banner /><div style={{ position: "absolute", left: (2560 - 1546) / 2, top: (1440 - 423) / 2, width: 1546, height: 423, border: "4px solid red" }} /></AbsoluteFill>);
