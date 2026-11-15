"""
metrics.py — the HARD RUBRIC for the critic loop.

Everything in here is a measurement, not an opinion. The point of the loop is that
each pass produces numbers that can be compared against the previous pass, so
"did it get better" is answerable instead of arguable.

Two families:
  frame_metrics(...)     — per-frame: value structure, focal clarity, palette, safe area
  temporal_metrics(...)  — across frames: the motion curve, holds, impacts, linear-easing
                           tells, dead air, cuts, and micro-churn (unreadable counters)

Nothing here knows anything about Figures specifically except BRAND — swap that and
it works on any deterministic renderer.
"""
from __future__ import annotations
import json, math
import numpy as np
from PIL import Image

# ── palette + safe-area PROFILES ─────────────────────────────────────────────
# The timing and legibility checks are brand-agnostic; only the palette lock and the
# platform-chrome zones are project-specific. Switch with set_profile().
FIGURES_BRAND = {
    "bg":   (0x13, 0x15, 0x19),
    "ink":  (0xEC, 0xE7, 0xDC),
    "gold": (0xF0, 0xC2, 0x5A),
    "mute": (0x8a, 0x84, 0x78),
    "cap":  (0xB9, 0xB2, 0xA4),
    "mat_ceramic_hi": (0x3a, 0x3d, 0x44),
    "mat_ceramic_lo": (0x19, 0x1c, 0x22),
    "mat_body":       (0x23, 0x26, 0x2d),
    "mat_coffee":     (0x5a, 0x37, 0x20),
    "mat_shadow":     (0x0c, 0x0d, 0x10),
}
# Singular Link — canonical, from Dashboard for Singular/social-content/_brand/brand.css
SL_BRAND = {
    "black":     (0x00, 0x00, 0x00),
    "bg":        (0x0A, 0x1F, 0x2A),
    "ink":       (0xB5, 0xDA, 0xDF),
    "inkBright": (0xD5, 0xE8, 0xEC),
    "cyan":      (0x00, 0xD1, 0xFF),
    "cyanSoft":  (0x2E, 0xD0, 0xFF),
    "blue":      (0x1A, 0x9F, 0xD4),
    "teal":      (0x0D, 0x4F, 0x6B),
    "navy":      (0x1C, 0x3D, 0x82),
    "border":    (0x5A, 0x8F, 0xA0),
    "muted":     (0x7A, 0xA0, 0xAE),
    "orange":    (0xF1, 0x5A, 0x27),
    "white":     (0xFF, 0xFF, 0xFF),
}

# YouTube Shorts / Reels / TikTok chrome — content here is functionally invisible.
SHORTS_CHROME = {"bottom": 0.17, "right": 0.13, "top": 0.06, "left": 0.04}
# 16:9 has no platform chrome; use a conventional broadcast title-safe margin instead.
BROADCAST_SAFE = {"bottom": 0.05, "right": 0.05, "top": 0.05, "left": 0.05}

BRAND = FIGURES_BRAND
SHORTS_UNSAFE = SHORTS_CHROME
PALETTE_TOL = 46          # max RGB distance to count as "on palette"


def set_profile(name: str):
    """Select the project profile. 'figures' (9:16 Shorts) or 'sl' (16:9 Singular Link)."""
    global BRAND, SHORTS_UNSAFE
    if name == "sl":
        BRAND, SHORTS_UNSAFE = SL_BRAND, BROADCAST_SAFE
    elif name == "figures":
        BRAND, SHORTS_UNSAFE = FIGURES_BRAND, SHORTS_CHROME
    else:
        raise ValueError(f"unknown profile {name!r}")
    return name


LUMA_W = np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)


def load_gray(path, size=None) -> np.ndarray:
    im = Image.open(path).convert("RGB")
    if size:
        im = im.resize(size, Image.BILINEAR)
    a = np.asarray(im, dtype=np.float32) / 255.0
    return a @ LUMA_W


def load_rgb(path, size=None) -> np.ndarray:
    im = Image.open(path).convert("RGB")
    if size:
        im = im.resize(size, Image.BILINEAR)
    return np.asarray(im, dtype=np.float32)


# ── per-frame ────────────────────────────────────────────────────────────────
def frame_metrics(path: str, portrait: bool = True) -> dict:
    """Measurable composition/value/palette/safe-area facts about ONE frame."""
    rgb = load_rgb(path, size=(432, 768) if portrait else (768, 432))
    H, W, _ = rgb.shape
    g = (rgb / 255.0) @ LUMA_W

    # value structure — a good frame is bimodal (dark ground, bright figure),
    # not a grey mush. Measured as how much mass sits in the mid-tones.
    p = np.percentile(g, [5, 25, 50, 75, 95, 99])
    midtone_mass = float(((g > 0.28) & (g < 0.62)).mean())

    # focal clarity — the fraction of the frame that is genuinely bright.
    # Below ~0.3% there's nothing to look at; above ~12% nothing dominates.
    bright = g > 0.62
    focal_frac = float(bright.mean())

    # where is the bright mass? (composition balance, and drift off-centre)
    if bright.any():
        ys, xs = np.nonzero(bright)
        cx, cy = float(xs.mean() / W), float(ys.mean() / H)
        spread = float(np.hypot(xs.std() / W, ys.std() / H))
    else:
        cx = cy = 0.5
        spread = 0.0

    # contrast of the focal element against its ground (WCAG-style ratio).
    # NOTE: must use a far tail, not p99 — a focal element smaller than 1% of the
    # frame (small gold text on black, which is most of this engine) is invisible
    # to p99 and reads as a false low-contrast failure.
    def rel_lum(v):
        v = np.clip(v, 0, 1)
        return np.where(v <= 0.03928, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)
    hi, lo = rel_lum(np.percentile(g, 99.9)), rel_lum(p[1])
    contrast_ratio = float((hi + 0.05) / (lo + 0.05))

    # legibility of the CAPTION layer — the sub-lines, not the hero figure.
    # Must be measured in the band where captions actually live (POS puts numSub/motifSub/
    # gSub at 0.62–0.78 of H). Sampling every mid-tone pixel in the frame instead measures
    # the gold glow field, which is why an earlier version of this check was completely
    # insensitive to the caption colour.
    band = g[int(H * 0.58): int(H * 0.82), :]
    btxt = band[band > 0.14]
    if btxt.size > 120:
        bg_local = float(np.percentile(band, 25))
        dim_contrast = float((rel_lum(np.percentile(btxt, 99.0)) + 0.05)
                             / (rel_lum(bg_local) + 0.05))
    else:
        dim_contrast = None

    # is this frame a full-frame EFFECT (flash, light leak, wipe) rather than content?
    # Composition/palette/safe-area checks are meaningless on these and must skip them.
    is_flash = bool((g > 0.40).mean() > 0.25)

    # edge density (Sobel) — busyness. Motion graphics should be sparse.
    gx = np.abs(np.diff(g, axis=1)).mean()
    gy = np.abs(np.diff(g, axis=0)).mean()
    edge_density = float(gx + gy)

    # palette adherence — how much of the frame is a colour we never chose.
    # (ignores near-black ground and the bg→ink neutral ramp)
    flat = rgb.reshape(-1, 3)
    lit = flat[(flat.max(axis=1) > 40)]
    if len(lit):
        sample = lit[:: max(1, len(lit) // 20000)]
        d = [np.linalg.norm(sample - np.array(c, dtype=np.float32), axis=1)
             for c in BRAND.values()]
        # Alpha-compositing ANY brand colour over the background produces the whole line
        # between bg and that colour — glows, gradients, fades and low-opacity fills are
        # all legitimate. Allowing only the bg→ink ramp made the gold glow field itself
        # read as ~10% "off-palette", which was a metric bug, not a design defect.
        bgv = np.array(BRAND["bg"], np.float32)
        for name, c in BRAND.items():
            if name == "bg":
                continue
            cv = np.array(c, dtype=np.float32) - bgv
            t = np.clip(((sample - bgv) @ cv) / float(cv @ cv), 0, 1)[:, None]
            d.append(np.linalg.norm(sample - (bgv + t * cv), axis=1))
        off_palette = float((np.vstack(d).min(axis=0) > PALETTE_TOL).mean())
    else:
        off_palette = 0.0

    # safe area — content sitting under platform chrome is content thrown away.
    ink = g > 0.40
    u = SHORTS_UNSAFE
    zones = {
        "bottom": ink[int(H * (1 - u["bottom"])):, :],
        "right":  ink[:, int(W * (1 - u["right"])):],
        "top":    ink[: int(H * u["top"]), :],
        "left":   ink[:, : int(W * u["left"])],
    }
    unsafe = {k: float(v.mean()) for k, v in zones.items()}

    return {
        "luma_p5": float(p[0]), "luma_p50": float(p[2]), "luma_p95": float(p[4]),
        "midtone_mass": midtone_mass,
        "focal_frac": focal_frac,
        "focal_cx": cx, "focal_cy": cy, "focal_spread": spread,
        "contrast_ratio": contrast_ratio,
        "dim_contrast": dim_contrast,
        "is_flash": is_flash,
        "edge_density": edge_density,
        "off_palette": off_palette,
        "unsafe": unsafe,
    }


# ── temporal ─────────────────────────────────────────────────────────────────
# Grain gate. The engine's Grain layer re-seeds every frame under mixBlendMode:overlay,
# which suppresses grain on black but amplifies it on mid-tones — so a frozen BRIGHT frame
# still reports ~2.7e-4 of inter-frame delta while a frozen DARK frame reports ~1e-5.
# A single global threshold therefore cannot separate holds from motion.
# Measured: grain never moves a pixel by more than ~3/255 (1.2%); real motion moves pixels
# by tens of levels. Gating per-pixel diffs below 2% makes a true freeze read as exactly 0
# at any brightness, which is what makes hold detection brightness-invariant.
GRAIN_GATE = 0.02


def motion_curve(frame_paths: list[str], size=(160, 284), gate: float = GRAIN_GATE) -> np.ndarray:
    """Mean absolute inter-frame difference, grain-gated. This one array is where most of
    the animation-craft signal lives — holds, impacts, easing, cuts, dead air."""
    prev, out = None, []
    for p in frame_paths:
        g = load_gray(p, size)
        if prev is None:
            out.append(0.0)
        else:
            d = np.abs(g - prev)
            d[d < gate] = 0.0                 # discard grain, keep motion
            out.append(float(d.mean()))
        prev = g
    m = np.array(out, dtype=np.float32)
    if len(m) > 1:
        m[0] = m[1]
    return m


def _runs(mask: np.ndarray) -> list[tuple[int, int]]:
    runs, start = [], None
    for i, v in enumerate(mask):
        if v and start is None:
            start = i
        elif not v and start is not None:
            runs.append((start, i - 1)); start = None
    if start is not None:
        runs.append((start, len(mask) - 1))
    return runs


def temporal_metrics(m: np.ndarray, fps: int = 30, baseline: float | None = None,
                     exclude: np.ndarray | None = None) -> dict:
    """Derive animation-craft facts from the motion curve.

    Two calibration subtleties, both learned the hard way:

    1. NOISE FLOOR. This renderer animates film grain every frame (Grain re-seeds on
       `frame % 12`), so a genuinely frozen frame still reports ~2.5e-4 of inter-frame
       delta. Hold detection must be relative to that floor, not to zero and not to the
       content median — a threshold below the floor can never fire.

    2. PINNED BASELINE. Thresholds normalised to the CURRENT version's median are
       self-defeating: adding motion to one scene raises the median and pushes unrelated
       scenes below the bar, so the diff table reports phantom regressions. `baseline`
       pins the reference scale to the first measured version of a slug.
    """
    med = float(np.median(m))
    mean, sd = float(m.mean()), float(m.std())
    # the renderer's own dither/grain floor — the quietest frames are, by definition,
    # frames where nothing but grain changed.
    noise_floor = float(np.percentile(m, 3)) or 1e-6

    # CUTS — motion spikes far outside the distribution.
    cut_thr = mean + 5 * sd
    cuts = [int(i) for i in np.nonzero(m > cut_thr)[0]]
    # collapse adjacent
    cuts = [c for i, c in enumerate(cuts) if i == 0 or c - cuts[i - 1] > 3]

    mask_cut = np.zeros_like(m, dtype=bool)
    for c in cuts:
        mask_cut[max(0, c - 2): c + 3] = True
    # Cross-fade transitions are not content. An 18-frame dissolve ramps motion up and back
    # down, which looks exactly like a discrete accent to a pixel-difference detector — three
    # of this film's six reported "unpunctuated impacts" were dissolves, not animation.
    if exclude is not None:
        mask_cut = mask_cut | exclude
    body = m[~mask_cut] if (~mask_cut).any() else m
    bmed_now = float(np.median(body)) or 1e-6
    # the RULER: pinned to the slug's first measured version so versions are comparable
    bmed = float(baseline) if baseline else bmed_now

    # HOLDS — runs of near-stillness ≥3 frames. Holds are craft, not laziness.
    # "Still" means indistinguishable from a frozen frame plus grain, hence the floor.
    # grain is gated out of the motion curve, so a frozen frame is EXACTLY 0.0 at any
    # brightness. A hold is therefore an absolute condition, not a relative one.
    hold_thr = 1e-5
    hold_mask = (m <= hold_thr) & (~mask_cut)
    holds = [(a, b) for a, b in _runs(hold_mask) if b - a + 1 >= 3]

    # DEAD AIR — a hold so long it stops being a beat and becomes a stall.
    dead = [(a, b) for a, b in holds if b - a + 1 >= int(fps * 0.75)]

    # IMPACTS — genuine accents, not every wiggle. A per-frame count-up produces
    # dozens of small local maxima; requiring a spike to clear BOTH a global floor
    # and 2.5x its own local neighbourhood is what separates an accent from churn.
    impacts = []
    thr = max(bmed * 6.0, mean + 2.0 * sd)
    for i in range(4, len(m) - 4):
        if mask_cut[i] or m[i] < thr:
            continue
        if m[i] != max(m[max(0, i - 5): i + 6]):
            continue
        local = float(np.median(m[max(0, i - 20): i + 21])) or 1e-6
        if m[i] < 2.5 * local:
            continue
        # An ACCENT is a DISCRETE event: motion spikes and then falls away. A spike inside
        # sustained fast motion (a count-up mid-flight, a chart still drawing, a camera move)
        # is not an accent and must not be judged as one. Requiring the fall is what
        # separates the two — without it this check fired on mid-animation frames and
        # reported designed landings as failures while ignoring the landings themselves.
        after = m[i + 1: i + 10]
        if after.size and float(after.min()) > 0.40 * float(m[i]):
            continue
        if not impacts or i - impacts[-1] > 8:
            impacts.append(i)
    # is each impact punctuated by a hold within 5 frames after?
    unpunctuated = []
    for i in impacts:
        win = hold_mask[i + 1: i + 7]
        if not win.any():
            unpunctuated.append(int(i))

    # LINEAR-EASING TELL — a move whose velocity is a flat plateau.
    # Real animation accelerates and decelerates; tweens don't.
    move_mask = (m > 0.55 * bmed) & (~mask_cut)
    linear_segs = []
    for a, b in _runs(move_mask):
        n = b - a + 1
        if n < 8:
            continue
        seg = m[a:b + 1]
        mu = float(seg.mean()) or 1e-6
        flatness = 1.0 - float(seg.std()) / mu       # →1.0 means constant velocity
        if flatness > 0.72:
            linear_segs.append({"start": int(a), "end": int(b), "flatness": round(flatness, 3)})

    # MICRO-CHURN — long stretches of small, constant change. This is what a
    # per-frame count-up looks like: the eye never gets a stable read.
    churn_mask = (m > 0.25 * bmed) & (m < 0.9 * bmed) & (~mask_cut)
    churn = [{"start": int(a), "end": int(b), "frames": int(b - a + 1)}
             for a, b in _runs(churn_mask) if b - a + 1 >= int(fps * 1.2)]

    # ON-Ns — is there deliberate frame-rate quantisation? (autocorrelation of
    # the de-meaned motion curve at lag 2 and 3). Smooth tweening → ~0.
    d = m - m.mean()
    def ac(lag):
        if len(d) <= lag or d.std() == 0:
            return 0.0
        return float(np.corrcoef(d[:-lag], d[lag:])[0, 1])
    on2, on3 = ac(2), ac(3)

    # HOOK ENERGY — motion in the first 1.5s, normalised. Retention proxy.
    hook = float(m[: int(fps * 1.5)].mean() / bmed) if len(m) > fps else 0.0

    return {
        "frames": int(len(m)),
        "motion_median": round(bmed, 6),
        "motion_median_thisversion": round(bmed_now, 6),
        "noise_floor": round(noise_floor, 6),
        "hold_threshold": round(hold_thr, 6),
        "baseline_pinned": baseline is not None,
        "cuts": cuts,
        "holds": [[int(a), int(b)] for a, b in holds],
        "hold_frames_total": int(sum(b - a + 1 for a, b in holds)),
        "hold_pct": round(sum(b - a + 1 for a, b in holds) / max(1, len(m)), 4),
        "dead_air": [[int(a), int(b)] for a, b in dead],
        "impacts": [int(i) for i in impacts],
        "impacts_unpunctuated": unpunctuated,
        "linear_segments": linear_segs,
        "micro_churn": churn,
        "churn_frames_total": int(sum(c["frames"] for c in churn)),
        "autocorr_lag2": round(on2, 3),
        "autocorr_lag3": round(on3, 3),
        "hook_energy": round(hook, 3),
    }


# ── the rubric: turn measurements into PASS/FAIL, no opinions ────────────────
# Each check is (id, description, predicate, severity). Thresholds are the
# argument — keep them here so a change of standard is a one-line diff.
def evaluate(frames: list[dict], temporal: dict, bounds=None, m=None,
             fps: int = 30, landings: list[int] | None = None) -> list[dict]:
    # Full-frame effects (light leaks, wipes, flashes) are not compositions.
    # Judging value/palette/safe-area on them produced the v1 false positives.
    content = [f for f in frames if not f.get("is_flash")] or frames

    def agg(key, fn=np.mean, src=None):
        vals = [f[key] for f in (src or content) if f.get(key) is not None]
        return float(fn(vals)) if vals else 0.0

    n = temporal["frames"]
    checks = []

    def chk(cid, desc, ok, detail, sev="major"):
        checks.append({"id": cid, "desc": desc, "pass": bool(ok),
                       "detail": detail, "severity": sev})

    # — value & composition —
    mid = agg("midtone_mass")
    chk("VALUE_BIMODAL", "Value structure is bimodal, not grey mush",
        mid < 0.30, f"mean midtone mass {mid:.3f} (want <0.30)")

    foc = agg("focal_frac")
    chk("FOCAL_PRESENT", "Every frame has a clear bright focal element",
        0.004 < foc < 0.14, f"mean bright fraction {foc:.4f} (want 0.004–0.14)")

    lowc = [i for i, f in enumerate(content) if f["contrast_ratio"] < 4.5]
    chk("CONTRAST_MIN", "Hero focal element clears 4.5:1 against its ground",
        len(lowc) <= len(content) * 0.1,
        f"{len(lowc)}/{len(content)} content frames below 4.5:1", "critical")

    # the sub-lines / captions, not the hero figure — the real phone-legibility risk
    dimc = [i for i, f in enumerate(content)
            if f.get("dim_contrast") is not None and f["dim_contrast"] < 3.0]
    chk("CAPTION_LEGIBLE", "Secondary/caption text clears 3:1",
        len(dimc) <= len(content) * 0.2,
        f"{len(dimc)}/{len(content)} content frames have sub-text under 3:1 "
        f"(mean {agg('dim_contrast'):.2f}:1)")

    drift = agg("off_palette", np.max)
    chk("PALETTE_LOCK", "No off-brand colour anywhere",
        drift < 0.02, f"worst content frame {drift*100:.2f}% off-palette (want <2%)", "minor")

    # — 9:16 platform chrome —
    worst = {k: max(f["unsafe"][k] for f in content) for k in ("bottom", "right", "top", "left")}
    chk("SAFE_BOTTOM", "Nothing important under the Shorts title/channel row",
        worst["bottom"] < 0.010, f"bottom zone ink {worst['bottom']*100:.2f}% (want <1%)", "critical")
    chk("SAFE_RIGHT", "Nothing under the like/comment rail",
        worst["right"] < 0.010, f"right zone ink {worst['right']*100:.2f}% (want <1%)", "critical")

    # — timing & animation craft —
    chk("HOLDS_EXIST", "Motion is punctuated by holds (≥8% of runtime)",
        temporal["hold_pct"] >= 0.08,
        f"{temporal['hold_pct']*100:.1f}% of frames are holds ({len(temporal['holds'])} holds)")

    # IMPACTS_PUNCTUATED infers accents from the motion curve. That is a guess, and on a film
    # with continuously-animating figures it keeps flagging count-up oscillations as accents.
    # When a project DECLARES its landings, LANDINGS_SETTLE checks the real thing and this
    # heuristic is redundant — so it is reported, not scored.
    if not landings:
        chk("IMPACTS_PUNCTUATED", "Every impact is followed by a hold within 6 frames",
            len(temporal["impacts_unpunctuated"]) == 0,
            f"{len(temporal['impacts_unpunctuated'])}/{len(temporal['impacts'])} impacts not punctuated: "
            f"{temporal['impacts_unpunctuated'][:8]}")

    lin = temporal["linear_segments"]
    lin_frames = sum(s["end"] - s["start"] + 1 for s in lin)
    chk("NO_LINEAR_EASING", "No move runs at constant velocity",
        lin_frames < n * 0.06,
        f"{lin_frames} frames ({lin_frames/max(1,n)*100:.1f}%) in constant-velocity moves, "
        f"{len(lin)} segments")

    chk("NO_DEAD_AIR", "No hold longer than 0.75s without a compositional reason",
        len(temporal["dead_air"]) == 0,
        f"{len(temporal['dead_air'])} stalls: {temporal['dead_air'][:6]}")

    ch = temporal["churn_frames_total"]
    chk("NO_MICRO_CHURN", "No long stretch of unreadable low-level churn",
        ch < n * 0.15,
        f"{ch} frames ({ch/max(1,n)*100:.1f}%) of micro-churn in "
        f"{len(temporal['micro_churn'])} runs: "
        f"{[(c['start'], c['end']) for c in temporal['micro_churn'][:5]]}")

    chk("HOOK_ENERGY", "First 1.5s carries above-average motion energy",
        temporal["hook_energy"] > 1.15,
        f"hook energy {temporal['hook_energy']:.2f}× median (want >1.15)")

    # — DECLARED FIGURE LANDINGS —
    # The film states where its accents are (SL_SCENES.holdAt -> spec). Checking those exact
    # frames is strictly better than inferring accents from the motion curve: a heuristic
    # cannot distinguish a designed landing from a chart mid-draw, and got it wrong here.
    if landings and m is not None:
        late = []
        for L in landings:
            if L + 8 >= len(m):
                continue
            after = m[L + 1: L + 9]
            if not after.size or float(after.min()) > temporal["hold_threshold"]:
                late.append({"frame": int(L),
                             "min_after": round(float(after.min()) if after.size else -1, 6)})
        chk("LANDINGS_SETTLE",
            "Every declared figure landing settles into a hold",
            len(late) == 0,
            f"{len(late)}/{len(landings)} declared landings never settle: "
            + "; ".join(f"f{x['frame']} (min motion after = {x['min_after']})" for x in late))

    # — SCENE TAIL STALL —
    # A scene that lands its payload (count finishes / reveal completes) and then
    # holds the same frame for a second-plus is paying full runtime for zero
    # information. On a Short that tail is exactly where the swipe happens.
    # This is the check that matters most for this engine.
    if bounds is not None and m is not None:
        bmed = temporal["motion_median"] or 1e-6       # PINNED baseline, not this version
        stall_thr = 0.06 * bmed          # tail is doing essentially nothing
        stalls = []
        for b in bounds:
            sc, s, e = b["sc"], b["start"], b["end"]
            land = s + sc["countStart"] + sc["countDur"] if "countStart" in sc else None
            if land is None:                       # non-count scene: judge its last second
                land = s + int(sc["dur"] * 0.45)
            tail_a = min(land + 4, e)
            if e - tail_a < int(fps * 0.6):
                continue
            tail = m[tail_a:e + 1]
            if tail.size and float(tail.mean()) < stall_thr:
                stalls.append({"scene": b["i"], "kind": b["kind"],
                               "from": int(tail_a), "to": int(e),
                               "sec": round((e - tail_a + 1) / fps, 2),
                               "motion_vs_floor": round(float(tail.mean())
                                                        / temporal["noise_floor"], 2)})
        wasted = sum(s["sec"] for s in stalls)
        chk("NO_SCENE_TAIL_STALL",
            "No scene freezes after delivering its payload",
            len(stalls) == 0,
            f"{len(stalls)} scenes stall for {wasted:.1f}s total "
            f"({wasted/(n/fps)*100:.0f}% of runtime): "
            + "; ".join(f"s{s['scene']}:{s['kind']} f{s['from']}–{s['to']} ({s['sec']}s)"
                        for s in stalls),
            "critical")

    # — DEAD OPENING —
    # Found by eye first (every count scene opened on a literal "$0" and held it ~1s), then
    # generalised. Measured from the RENDER, not from the spec: a check that reads countStart
    # out of the spec cannot see whether the fix actually reached the screen.
    # A scene whose first 0.7s after its transition is motionless wastes the moment the
    # viewer is deciding whether to keep watching.
    if bounds is not None and m is not None:
        bmed_o = temporal["motion_median"] or 1e-6
        win = int(fps * 0.7)
        dead_open = []
        for b in bounds:
            a = b["start"] + b["trans_out"] * 0 + b["trans_in"]
            seg = m[a: min(a + win, b["end"] + 1)]
            if seg.size >= win // 2 and float(seg.mean()) < 0.10 * bmed_o:
                dead_open.append({"scene": b["i"], "kind": b["kind"],
                                  "from": int(a), "to": int(a + seg.size - 1),
                                  "vs_median": round(float(seg.mean()) / bmed_o, 3)})
        chk("NO_DEAD_OPENING",
            "No scene opens with a motionless first 0.7s",
            len(dead_open) == 0,
            f"{len(dead_open)} scenes open dead: "
            + "; ".join(f"s{z['scene']}:{z['kind']} f{z['from']}–{z['to']} "
                        f"({z['vs_median']}× median)" for z in dead_open))

    # — SCENE OPENS POPULATED —
    # A scene whose opening frame is nearly empty wastes its most valuable moment.
    thin = [f for f in content if f["focal_frac"] < 0.004]
    chk("OPENS_POPULATED", "No sampled composition is near-empty",
        len(thin) <= len(content) * 0.08,
        f"{len(thin)}/{len(content)} sampled frames have <0.4% bright content", "minor")

    # — LOWER-THIRD USE —
    # 9:16 gives you height; leaving 0.62→0.83 (above the chrome) permanently empty
    # while cramming everything into the upper middle wastes the format.
    lower = agg("focal_cy", np.max)
    chk("USES_FRAME_HEIGHT", "Composition uses the vertical frame, not just the top half",
        lower > 0.55, f"lowest focal centroid across content frames is {lower:.2f} "
                      f"of frame height (want some content past 0.55)", "minor")

    return checks


def score(checks: list[dict]) -> dict:
    w = {"critical": 3, "major": 2, "minor": 1}
    tot = sum(w[c["severity"]] for c in checks)
    got = sum(w[c["severity"]] for c in checks if c["pass"])
    return {"score": round(100 * got / max(1, tot), 1),
            "passed": sum(c["pass"] for c in checks), "total": len(checks)}
