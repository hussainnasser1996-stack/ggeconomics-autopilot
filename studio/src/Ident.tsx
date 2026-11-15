import React from "react";
import { AbsoluteFill, Audio, interpolate, random, spring, staticFile, useCurrentFrame, useVideoConfig, Easing } from "remotion";
import { BRAND, C, CRT, DISPLAY, GlitchSlices, GridBG, Mark, MONO, RGBSplit, useScale } from "./brand";

// Cue frames — MUST match src/sfx_ident.py
const BAR0 = 14, STEP = 3, BLOCKS = 8, SQUEEZE = 40, IMPACT = 48, TYPE0 = 62, SAVED = 92, OFF = 106;
export const IDENT_FRAMES = 120;

export const Ident: React.FC<{ withAudio?: boolean }> = ({ withAudio = true }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { u, vertical } = useScale();

  // --- CRT power-off at the end
  const offY = interpolate(f, [OFF, OFF + 6], [1, 0.006], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.in(Easing.cubic) });
  const offX = interpolate(f, [OFF + 6, OFF + 11], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.in(Easing.quad) });
  const offGlow = f >= OFF ? interpolate(f, [OFF, OFF + 6, OFF + 13], [0, 1, 0], { extrapolateRight: "clamp" }) : 0;

  // --- impact dynamics
  const since = f - IMPACT;
  const hit = since >= 0;
  const shake = hit ? Math.exp(-since / 5) * 22 * u : 0;
  const sx = (random(`sx${f}`) - 0.5) * shake, sy = (random(`sy${f}`) - 0.5) * shake;
  const split = hit ? Math.exp(-since / 7) * 26 * u + (f >= 58 && f < 62 ? 14 * u : 0) : 0;
  const glitch = hit ? Math.max(Math.exp(-since / 4), f >= 58 && f < 62 ? 0.7 : 0) : 0;
  const pop = hit ? spring({ frame: since, fps, config: { damping: 11, stiffness: 180, mass: 0.7 }, from: 1.35, to: 1 }) : 0;
  const flash = hit ? interpolate(since, [0, 3], [0.85, 0], { extrapolateRight: "clamp" }) : 0;

  // --- pre-impact: cursor + save bar
  const cursorOn = f < BAR0 && Math.floor(f / 4) % 2 === 0;
  const filled = Math.max(0, Math.min(BLOCKS, Math.floor((f - BAR0) / STEP) + 1));
  const squeeze = interpolate(f, [SQUEEZE, IMPACT], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.in(Easing.cubic) });
  const blk = 46 * u, gap = 10 * u;

  // --- tagline typing
  const tag = BRAND.tagline;
  const typed = Math.max(0, Math.min(tag.length, Math.floor((f - TYPE0) / 1.5)));
  const saved = f >= SAVED;
  const savedPulse = saved ? interpolate(f - SAVED, [0, 4, 12], [1, 1, 0.0], { extrapolateRight: "clamp" }) : 0;

  const wordSize = (vertical ? 132 : 150) * u;

  return (
    <AbsoluteFill style={{ background: "#000" }}>
      {withAudio && <Audio src={staticFile("sfx/ident.wav")} />}
      <AbsoluteFill style={{ transform: `scale(${offX || 0.0001}, ${offY})`, filter: offGlow ? `brightness(${1 + offGlow * 2.5})` : undefined }}>
        <GridBG />
        <AbsoluteFill style={{ transform: `translate(${sx}px, ${sy}px)` }}>
          {/* cursor */}
          {cursorOn && (
            <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
              <div style={{ width: 22 * u, height: 40 * u, background: C.lime, boxShadow: `0 0 ${30 * u}px ${C.lime}` }} />
            </AbsoluteFill>
          )}

          {/* save bar */}
          {f >= BAR0 && f < IMPACT && (
            <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", flexDirection: "column", gap: 22 * u }}>
              <div style={{ fontFamily: MONO, fontWeight: 700, color: C.dim, fontSize: 26 * u, letterSpacing: 6 * u, opacity: squeeze }}>
                LOADING… {String(Math.round((filled / BLOCKS) * 100)).padStart(3, "0")}%
              </div>
              <div style={{ display: "flex", gap, transform: `scaleX(${squeeze}) scaleY(${0.25 + 0.75 * squeeze})` }}>
                {Array.from({ length: BLOCKS }).map((_, i) => {
                  const on = i < filled;
                  const justOn = on && i === filled - 1 && (f - BAR0) % STEP < 2;
                  return (
                    <div key={i} style={{
                      width: blk, height: blk, border: `${4 * u}px solid ${on ? C.lime : C.line}`,
                      background: on ? C.lime : "transparent",
                      boxShadow: on ? `0 0 ${(justOn ? 40 : 14) * u}px ${C.lime}` : "none",
                      transform: justOn ? "scale(1.15)" : "none",
                    }} />
                  );
                })}
              </div>
            </AbsoluteFill>
          )}

          {/* wordmark */}
          {hit && (
            <GlitchSlices intensity={glitch} seed="ident">
              <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", flexDirection: "column" }}>
                <div style={{ transform: `scale(${pop})`, display: "flex", flexDirection: "column", alignItems: "center", gap: 34 * u }}>
                  <div style={{ filter: `drop-shadow(0 0 ${(saved ? 30 * savedPulse : 0) + 10 * u}px ${C.lime})` }}>
                    <Mark size={120 * u} labelColor={saved && savedPulse > 0.5 ? C.white : C.ink} />
                  </div>
                  <RGBSplit amount={split}>
                    <div style={{
                      fontFamily: DISPLAY, fontWeight: 900, fontSize: wordSize, color: C.white, letterSpacing: -2 * u,
                      lineHeight: 0.92, textAlign: "center", whiteSpace: vertical ? "pre-line" : "nowrap",
                    }}>
                      {vertical ? BRAND.name.replace(" ", "\n") : BRAND.name}
                    </div>
                  </RGBSplit>
                  <div style={{ fontFamily: MONO, fontWeight: 700, fontSize: 30 * u, letterSpacing: 8 * u, color: C.lime, height: 40 * u, whiteSpace: "nowrap" }}>
                    {tag.slice(0, typed)}
                    {f >= TYPE0 && Math.floor(f / 4) % 2 === 0 && <span style={{ background: C.lime, color: C.lime }}>_</span>}
                  </div>
                  <div style={{ fontFamily: MONO, fontWeight: 500, fontSize: 22 * u, letterSpacing: 6 * u, color: C.dim, opacity: saved ? 1 : 0 }}>
                    ◆ GG
                  </div>
                </div>
              </AbsoluteFill>
            </GlitchSlices>
          )}

          {/* pixel burst */}
          {hit && since < 30 &&
            Array.from({ length: 46 }).map((_, i) => {
              const a = random(`a${i}`) * Math.PI * 2;
              const v = (14 + random(`v${i}`) * 34) * u;
              const d = v * since * Math.exp(-since / 14);
              const s = (6 + random(`s${i}`) * 14) * u;
              const col = [C.lime, C.cyan, C.white, C.coral][i % 4];
              return (
                <div key={i} style={{
                  position: "absolute", left: "50%", top: "50%", width: s, height: s, background: col,
                  transform: `translate(${Math.cos(a) * d * 1.6}px, ${Math.sin(a) * d}px)`,
                  opacity: interpolate(since, [0, 30], [1, 0]),
                }} />
              );
            })}
        </AbsoluteFill>
        <AbsoluteFill style={{ background: C.white, opacity: flash }} />
        <CRT />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
