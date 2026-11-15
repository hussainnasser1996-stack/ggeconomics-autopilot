import React from "react";
import { AbsoluteFill, OffthreadVideo, staticFile } from "remotion";
import { C, DISPLAY, Mark, MONO } from "../brand";

export const Thumb: React.FC<{ src: string; at: number; big: string; line1: string; tag: string }> = ({ src, at, big, line1, tag }) => (
  <AbsoluteFill style={{ background: C.ink }}>
    <OffthreadVideo src={staticFile(`footage/${src}.mp4`)} startFrom={Math.round(at * 30)} muted style={{ position: "absolute", width: 1280 * 1.15, height: 720 * 1.15, left: -60, top: -50 }} />
    <AbsoluteFill style={{ background: "linear-gradient(90deg, rgba(7,7,11,0.95) 0%, rgba(7,7,11,0.85) 38%, rgba(7,7,11,0) 70%)" }} />
    <div style={{ position: "absolute", left: 50, top: 46, display: "flex", gap: 12, alignItems: "center" }}>
      <div style={{ background: C.lime, padding: "8px 16px", borderRadius: 10, fontFamily: MONO, fontWeight: 700, fontSize: 30, color: C.ink, letterSpacing: 2 }}>{tag}</div>
    </div>
    <div style={{ position: "absolute", left: 40, top: 140, fontFamily: DISPLAY, fontWeight: 900, fontSize: 250, color: C.lime, lineHeight: 0.9, letterSpacing: -10, textShadow: `0 0 60px ${C.lime}66, 6px 6px 0 #000` }}>{big}</div>
    <div style={{ position: "absolute", left: 50, top: 400, fontFamily: DISPLAY, fontWeight: 900, fontSize: 74, color: C.white, lineHeight: 1, letterSpacing: -2, textShadow: "4px 4px 0 #000", whiteSpace: "pre-line" }}>{line1}</div>
    <div style={{ position: "absolute", right: 36, bottom: 30 }}><Mark size={64} /></div>
  </AbsoluteFill>
);
