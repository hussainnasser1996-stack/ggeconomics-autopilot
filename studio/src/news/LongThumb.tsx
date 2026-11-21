import React from "react";
import { AbsoluteFill, Img, staticFile } from "remotion";
import { C, DISPLAY, Mark, SANS } from "../brand";
import type { LongSpec } from "./LongTop";

/** 1280x720 thumbnail for the weekly Top 10: four games from the list (never #1) + the hidden-#1 hook. */
export const LongThumb: React.FC<{ spec: LongSpec; ranks?: number[] }> = ({ spec, ranks = [8, 7, 5, 2] }) => {
  const pick = ranks.map((r) => spec.entries.find((e) => e.rank === r)).filter(Boolean) as LongSpec["entries"];
  const one = spec.entries.find((e) => e.rank === 1)!;
  return (
    <AbsoluteFill style={{ background: C.ink }}>
      <div style={{ position: "absolute", left: 0, top: 0, width: 760, height: 720, display: "grid", gridTemplateColumns: "1fr 1fr", gridTemplateRows: "1fr 1fr", gap: 6 }}>
        {pick.map((e, i) => {
                    return (
            <div key={i} style={{ position: "relative", overflow: "hidden" }}>
              <Img src={staticFile(`thumbs/t${i}.jpg`)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
              <div style={{ position: "absolute", left: 10, top: 10, fontFamily: DISPLAY, fontWeight: 900, fontSize: 40, color: C.ink, background: C.cyan, padding: "0 12px", borderRadius: 8 }}>#{e.rank}</div>
            </div>
          );
        })}
      </div>
      <div style={{ position: "absolute", left: 700, top: 0, width: 580, height: 720, background: `linear-gradient(90deg, ${C.ink}00, ${C.ink} 12%)` }} />
      <div style={{ position: "absolute", left: 790, right: 40, top: 70, display: "flex", flexDirection: "column", gap: 10 }}>
        <div style={{ fontFamily: DISPLAY, fontWeight: 900, fontSize: 92, color: C.white, lineHeight: 0.95, letterSpacing: -3 }}>TOP 10<br />ON STEAM</div>
        <div style={{ fontFamily: SANS, fontWeight: 800, fontSize: 34, color: C.dim, marginTop: 10 }}>{spec.week.replace(/^WEEK TO/i, "Week to")}</div>
        <div style={{ fontFamily: DISPLAY, fontWeight: 900, fontSize: 150, color: C.ink, background: C.lime, borderRadius: 18, textAlign: "center", marginTop: 40, lineHeight: 1.15 }}>#1 ?</div>
        <div style={{ fontFamily: SANS, fontWeight: 800, fontSize: 34, color: C.lime, marginTop: 14, textAlign: "center" }}>{one.players.toLocaleString("en-US")} players</div>
      </div>
      <div style={{ position: "absolute", right: 34, bottom: 26 }}><Mark size={40} /></div>
    </AbsoluteFill>
  );
};
