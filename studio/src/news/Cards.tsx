import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig, Easing } from "remotion";
import { C, DISPLAY, MONO, SANS } from "../brand";

export type Card =
  | { kind: "big"; line: string; value: string; label: string; note?: string; color?: string; countTo?: number; prefix?: string; suffix?: string; decimals?: number }
  | { kind: "pair"; line: string; a: { value: string; label: string }; b: { value: string; label: string }; note?: string }
  | { kind: "bars"; line: string; title: string; bars: { label: string; lo: number; hi?: number; color: string; text: string }[]; unit: string; note?: string }
  | { kind: "quote"; line: string; text: string; who: string; note?: string }
  | { kind: "date"; line: string; big: string; small: string; note?: string };

/** Enter: snappy spring up + blur-in; exit handled by parent via `exitAt` */
const useEnter = (local: number, delay = 0) => {
  const { fps } = useVideoConfig();
  const s = spring({ frame: local - delay, fps, config: { damping: 14, stiffness: 160, mass: 0.6 } });
  return { s, style: { opacity: Math.min(1, s * 1.4), transform: `translateY(${(1 - s) * 60}px) scale(${0.92 + 0.08 * s})` } };
};

const Note: React.FC<{ text?: string; local: number; u: number }> = ({ text, local, u }) =>
  text ? (
    <div style={{ ...useEnter(local, 8).style, marginTop: 22 * u, fontFamily: MONO, fontWeight: 500, fontSize: 24 * u, color: C.dim, letterSpacing: 1 * u, textAlign: "center", lineHeight: 1.35, whiteSpace: "pre-line" }}>
      {text}
    </div>
  ) : null;

const Panel: React.FC<{ children: React.ReactNode; u: number; out: number }> = ({ children, u, out }) => (
  <div style={{
    background: "rgba(7,7,11,0.78)", backdropFilter: "blur(14px)", border: `${2 * u}px solid ${C.line}`,
    borderRadius: 26 * u, padding: `${38 * u}px ${44 * u}px`, display: "flex", flexDirection: "column", alignItems: "center",
    boxShadow: `0 ${30 * u}px ${80 * u}px rgba(0,0,0,0.55)`, opacity: out, transform: `scale(${0.96 + 0.04 * out})`,
  }}>
    {children}
  </div>
);

export const CardView: React.FC<{ card: Card; local: number; dur: number; u: number }> = ({ card, local, dur, u }) => {
  const out = interpolate(local, [dur - 6, dur], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const e0 = useEnter(local, 0);
  const { fps } = useVideoConfig();

  if (card.kind === "big") {
    const col = card.color ?? C.lime;
    let shown = card.value;
    if (card.countTo !== undefined) {
      const p = interpolate(local, [0, 22], [0, 1], { extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
      shown = `${card.prefix ?? ""}${(card.countTo * p).toFixed(card.decimals ?? 0)}${card.suffix ?? ""}`;
    }
    return (
      <Panel u={u} out={out}>
        <div style={{ ...e0.style, fontFamily: DISPLAY, fontWeight: 900, fontSize: 170 * u, color: col, lineHeight: 1, letterSpacing: -4 * u, textShadow: `0 0 ${40 * u}px ${col}55` }}>{shown}</div>
        <div style={{ ...useEnter(local, 4).style, fontFamily: SANS, fontWeight: 800, fontSize: 40 * u, color: C.white, marginTop: 14 * u, letterSpacing: 2 * u, textTransform: "uppercase", textAlign: "center" }}>{card.label}</div>
        <Note text={card.note} local={local} u={u} />
      </Panel>
    );
  }
  if (card.kind === "pair") {
    return (
      <Panel u={u} out={out}>
        <div style={{ display: "flex", gap: 34 * u, alignItems: "flex-end" }}>
          {[card.a, card.b].map((x, i) => (
            <div key={i} style={{ ...useEnter(local, i * 7).style, display: "flex", flexDirection: "column", alignItems: "center" }}>
              <div style={{ fontFamily: DISPLAY, fontWeight: 900, fontSize: (i ? 76 : 98) * u, color: i ? C.cyan : C.lime, lineHeight: 1 }}>{x.value}</div>
              <div style={{ fontFamily: MONO, fontWeight: 700, fontSize: 26 * u, color: C.white, marginTop: 12 * u, letterSpacing: 3 * u }}>{x.label}</div>
            </div>
          ))}
        </div>
        <Note text={card.note} local={local} u={u} />
      </Panel>
    );
  }
  if (card.kind === "bars") {
    const max = Math.max(...card.bars.map((b) => b.hi ?? b.lo));
    const H = 360 * u;
    return (
      <Panel u={u} out={out}>
        <div style={{ ...e0.style, fontFamily: MONO, fontWeight: 700, fontSize: 26 * u, color: C.dim, letterSpacing: 3 * u, marginBottom: 26 * u }}>{card.title}</div>
        <div style={{ display: "flex", gap: 70 * u, alignItems: "flex-end", height: H + 190 * u }}>
          {card.bars.map((b, i) => {
            const g = spring({ frame: local - 6 - i * 10, fps, config: { damping: 16, stiffness: 90 } });
            const hLo = (b.lo / max) * H * g, hHi = (((b.hi ?? b.lo) - b.lo) / max) * H * g;
            return (
              <div key={i} style={{ display: "flex", flexDirection: "column", alignItems: "center", width: 210 * u }}>
                <div style={{ fontFamily: DISPLAY, fontWeight: 900, fontSize: 38 * u, color: b.color, marginBottom: 12 * u, opacity: g, whiteSpace: "nowrap" }}>{b.text}</div>
                <div style={{ width: 150 * u, height: hHi, background: `repeating-linear-gradient(45deg, ${b.color}, ${b.color} ${6 * u}px, ${b.color}66 ${6 * u}px, ${b.color}66 ${12 * u}px)`, borderRadius: `${8 * u}px ${8 * u}px 0 0` }} />
                <div style={{ width: 150 * u, height: hLo, background: b.color, borderRadius: b.hi ? 0 : `${8 * u}px ${8 * u}px 0 0` }} />
                <div style={{ fontFamily: MONO, fontWeight: 700, fontSize: 24 * u, color: C.white, marginTop: 14 * u, textAlign: "center", lineHeight: 1.25, whiteSpace: "pre-line" }}>{b.label}</div>
              </div>
            );
          })}
        </div>
        <Note text={card.note} local={local} u={u} />
      </Panel>
    );
  }
  if (card.kind === "quote") {
    return (
      <Panel u={u} out={out}>
        <div style={{ ...e0.style, fontFamily: DISPLAY, fontWeight: 900, fontSize: 140 * u, color: C.lime, lineHeight: 0.6, height: 70 * u }}>“</div>
        <div style={{ ...useEnter(local, 3).style, fontFamily: SANS, fontWeight: 800, fontSize: 56 * u, color: C.white, textAlign: "center", lineHeight: 1.18, maxWidth: 820 * u }}>{card.text}</div>
        <div style={{ ...useEnter(local, 10).style, fontFamily: MONO, fontWeight: 700, fontSize: 26 * u, color: C.lime, marginTop: 26 * u, letterSpacing: 2 * u }}>— {card.who}</div>
        <Note text={card.note} local={local} u={u} />
      </Panel>
    );
  }
  // date
  return (
    <Panel u={u} out={out}>
      <div style={{ ...e0.style, fontFamily: MONO, fontWeight: 700, fontSize: 30 * u, color: C.dim, letterSpacing: 6 * u }}>{card.small}</div>
      <div style={{ ...useEnter(local, 4).style, fontFamily: DISPLAY, fontWeight: 900, fontSize: 160 * u, color: C.white, lineHeight: 1.05, letterSpacing: -4 * u, whiteSpace: "nowrap" }}>{card.big}</div>
      <Note text={card.note} local={local} u={u} />
    </Panel>
  );
};
