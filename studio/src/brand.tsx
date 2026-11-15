import React from "react";
import { AbsoluteFill, random, useCurrentFrame, useVideoConfig } from "remotion";
import { loadFont as loadDisplay } from "@remotion/google-fonts/Unbounded";
import { loadFont as loadMono } from "@remotion/google-fonts/JetBrainsMono";
import { loadFont as loadSans } from "@remotion/google-fonts/Inter";

export const DISPLAY = loadDisplay("normal", { weights: ["700", "900"] }).fontFamily;
export const MONO = loadMono("normal", { weights: ["500", "700"] }).fontFamily;
export const SANS = loadSans("normal", { weights: ["500", "700", "800"] }).fontFamily;

// ---- Brand (working name — change here, everything follows) ----
export const BRAND = {
  name: "GG ECONOMICS",
  tagline: "GAMES · MONEY · NEWS",
  handle: "@ggeconomics",
};

// Our own palette (not borrowed): ink, signal lime, cyan, hot coral for "down" numbers
export const C = {
  ink: "#07070B",
  ink2: "#101018",
  line: "#22222E",
  lime: "#D4FF3A",
  cyan: "#3AE0FF",
  coral: "#FF4D6D",
  white: "#F4F4F0",
  dim: "#8A8A99",
};

export const useScale = () => {
  const { width, height } = useVideoConfig();
  const vertical = height > width;
  // base unit relative to the short edge of a 1080 canvas
  const u = Math.min(width, height) / 1080;
  return { vertical, u, width, height };
};

/** Pixel grid + vignette background */
export const GridBG: React.FC<{ opacity?: number; drift?: boolean }> = ({ opacity = 1, drift = true }) => {
  const f = useCurrentFrame();
  const { u } = useScale();
  const g = 36 * u;
  const off = drift ? ((f % 72) / 72) * g : 0; // 72 divides every loop length we use (1152)
  return (
    <AbsoluteFill style={{ background: C.ink, opacity }}>
      <AbsoluteFill
        style={{
          backgroundImage: `linear-gradient(${C.line} 1px, transparent 1px), linear-gradient(90deg, ${C.line} 1px, transparent 1px)`,
          backgroundSize: `${g}px ${g}px`,
          backgroundPosition: `${off}px ${off}px`,
          opacity: 0.55,
        }}
      />
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at center, transparent 30%, rgba(0,0,0,0.85) 100%)" }} />
    </AbsoluteFill>
  );
};

/** CRT scanlines + per-frame grain. Put on top of everything. */
export const CRT: React.FC<{ strength?: number }> = ({ strength = 1 }) => {
  const f = useCurrentFrame();
  const seed = Math.floor(f / 2);
  return (
    <AbsoluteFill style={{ pointerEvents: "none", mixBlendMode: "overlay", opacity: strength }}>
      <AbsoluteFill
        style={{
          backgroundImage: "repeating-linear-gradient(0deg, rgba(0,0,0,0.35) 0px, rgba(0,0,0,0.35) 1px, transparent 1px, transparent 3px)",
        }}
      />
      <svg width="100%" height="100%" style={{ position: "absolute", opacity: 0.22 }}>
        <filter id={`grain${seed}`}>
          <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves={2} seed={seed} />
          <feColorMatrix type="saturate" values="0" />
        </filter>
        <rect width="100%" height="100%" filter={`url(#grain${seed})`} />
      </svg>
    </AbsoluteFill>
  );
};

/** Pixel coin stamped "GG" — the brand mark (arcade coin + money). size = px */
const G = [".XXX.", "X....", "X....", "X.XXX", "X...X", "X...X", ".XXX."];
export const Mark: React.FC<{ size: number; color?: string; label?: string; labelColor?: string }> = ({
  size, color = C.lime, label = C.ink, labelColor,
}) => {
  const N = 16, px = size / N, cells: React.ReactNode[] = [];
  const ink = labelColor ?? label;
  for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) {
    const dx = x + 0.5 - N / 2, dy = y + 0.5 - N / 2, r = Math.sqrt(dx * dx + dy * dy);
    if (r > 7.9) continue;
    let fill = color;
    if (r > 7.0) fill = "#9DBE1F";                     // darker rim (coin edge), no ring through the letters
    const gx = x - 2, gy = y - 4;                      // two G's at x 2..6 and 9..13, y 4..10
    const inG = (ox: number) => gy >= 0 && gy < 7 && gx - ox >= 0 && gx - ox < 5 && G[gy][gx - ox] === "X";
    if (inG(0) || inG(7)) fill = ink;
    if ((x === 5 && y === 2) || (x === 6 && y === 2)) fill = "#F4FFD0";   // small shine
    cells.push(<rect key={`${x}-${y}`} x={x * px} y={y * px} width={px + 0.5} height={px + 0.5} fill={fill} />);
  }
  return <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} shapeRendering="crispEdges">{cells}</svg>;
};

/** RGB-split text: renders children 3x with channel offsets */
export const RGBSplit: React.FC<{ amount: number; children: React.ReactNode; style?: React.CSSProperties }> = ({
  amount, children, style,
}) => (
  <div style={{ position: "relative", ...style }}>
    {amount > 0.2 && (
      <>
        <div style={{ position: "absolute", inset: 0, color: C.coral, transform: `translate(${-amount}px, ${amount * 0.3}px)`, mixBlendMode: "screen", opacity: 0.9 }}>{children}</div>
        <div style={{ position: "absolute", inset: 0, color: C.cyan, transform: `translate(${amount}px, ${-amount * 0.3}px)`, mixBlendMode: "screen", opacity: 0.9 }}>{children}</div>
      </>
    )}
    <div style={{ position: "relative" }}>{children}</div>
  </div>
);

/** Horizontal glitch slices of a layer. intensity 0..1 */
export const GlitchSlices: React.FC<{ intensity: number; seed: string; children: React.ReactNode }> = ({
  intensity, seed, children,
}) => {
  const f = useCurrentFrame();
  if (intensity < 0.05) return <AbsoluteFill>{children}</AbsoluteFill>;
  const n = 7;
  return (
    <AbsoluteFill>
      {Array.from({ length: n }).map((_, i) => {
        const top = (i / n) * 100, bot = 100 - ((i + 1) / n) * 100;
        const r = random(`${seed}-${i}-${Math.floor(f / 2)}`);
        const dx = (r - 0.5) * 80 * intensity * (r > 0.55 ? 1 : 0.15);
        return (
          <AbsoluteFill key={i} style={{ clipPath: `inset(${top}% 0 ${bot}% 0)`, transform: `translateX(${dx}px)` }}>
            {children}
          </AbsoluteFill>
        );
      })}
    </AbsoluteFill>
  );
};
