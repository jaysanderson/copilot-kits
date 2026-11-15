"""Smooth Ken Burns motion for the whole video pipeline (one reusable helper).

Replaces the old per-script zoompan pattern

    scale={W*2}:{H*2},zoompan=z='1+amount*on/frames':d=frames:
        x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H}

which read badly to a reviewer. Three separate faults, all fixed here:

1. JUDDER on fine text. zoompan recomputes the crop origin (x, y) every frame
   and truncates it to an INTEGER pixel of its input buffer. A 2x pre-scale
   shrinks the step but does not remove it, so slide text and thin lines shimmer
   as the origin snaps frame to frame. Fix: render the pan at 2x the OUTPUT
   resolution (s = 3840x2160) and then lanczos-downscale to 1920x1080. An
   integer jump in the 3840 space is half a pixel at output, and the final
   lanczos pass dissolves it. Belt and braces: the source is also lanczos
   supersampled so the pan samples down, never up.

2. LINEAR ramp. z = 1+amount*on/frames moves at constant speed and stops dead,
   so every move visibly jerks at its start and end. Fix: an ease-in-out
   (smoothstep, 3t^2-2t^3) so the move accelerates and settles gently.

3. THE SAME MOVE ON EVERY SHOT, at a fixed amount regardless of length. A fast
   push on a short hold looks nervous; an identical centre-push on twenty slides
   reads mechanical. Fix: pick_motion() varies push-in / push-out / gentle drift
   / hold across a sequence, and amount_for_duration() gentles and slows the
   move on longer holds.

Everything returns an ffmpeg filter-chain string (kenburns_chain) or renders a
still to an mp4 (render_motion); no new dependency, same libx264/crf ladder the
rest of the pipeline uses.
"""
import subprocess
from pathlib import Path

W, H = 1920, 1080
FPS = 30


def amount_for_duration(dur, rate=0.009, lo=0.035, hi=0.09):
    """Total zoom travel for a shot of `dur` seconds.

    Scales with length (~0.9 percent per second) but clamped, so a 3-second hold
    gets a barely-there move and a long hold never pushes past ~9 percent. This
    is what stops a short shot looking nervous and a long one looking like a
    slow-motion zoom.
    """
    return max(lo, min(hi, rate * max(0.1, dur)))


# A tasteful, non-repeating sequence. Drifts alternate side and axis; a hold is
# dropped in every so often so the eye gets a rest and a hero beat can sit still.
_CYCLE = [
    ("in", None),
    ("out", None),
    ("drift", "left"),
    ("in", None),
    ("drift", "up"),
    ("out", None),
    ("drift", "right"),
    ("none", None),
    ("in", None),
    ("drift", "down"),
    ("out", None),
    ("drift", "left"),
]


def pick_motion(i):
    """(motion, anchor) for shot index i - varied so no two neighbours match."""
    return _CYCLE[i % len(_CYCLE)]


def _smooth(u):
    """smoothstep(u) = 3u^2 - 2u^3 as an ffmpeg expression string, u in [0,1]."""
    return f"({u})*({u})*(3-2*({u}))"


def kenburns_chain(motion="in", amount=0.06, frames=90, fps=FPS,
                   out_w=W, out_h=H, anchor=None, supersample=3,
                   ease="smooth"):
    """The video filter chain for one still, input-label and output-label free.

    Caller wraps it, e.g.  f"[0:v]{kenburns_chain(...)}[v]".
    """
    cw, ch = out_w * supersample, out_h * supersample          # 2x render canvas
    # Cover the 2x canvas exactly so iw/ih are known and 16:9; a 16:9 source is a
    # no-op, a stray-ratio one is centre-cropped rather than letterboxed.
    pre = (f"scale={cw}:{ch}:force_original_aspect_ratio=increase:flags=lanczos,"
           f"crop={cw}:{ch}")
    post = f"scale={out_w}:{out_h}:flags=lanczos,setsar=1,format=yuv420p"

    if motion == "none" or frames < 2:
        return f"{pre},{post}"

    n = frames - 1
    # smoothstep has ZERO velocity at both ends, so the opening and closing
    # seconds of a long push are motionless - which is where a perceptually-still
    # run comes from even on a shot that is demonstrably moving. One punch in a
    # dealer-management walkthrough measured 100% of its samples under the still
    # threshold at a median of 0.114 while its per-shot mean passed: all the
    # motion was in the middle. `ease="linear"` spreads it evenly instead, which
    # is right for an evidence push, where the move is there to hold attention
    # rather than to feel cinematic. Default unchanged, so no existing film moves.
    s = f"on/{n}" if ease == "linear" else _smooth(f"on/{n}")

    if motion == "in":
        z = f"1+{amount:.5f}*{s}"
        x = "iw/2-(iw/zoom/2)"
        y = "ih/2-(ih/zoom/2)"
    elif motion == "out":
        z = f"1+{amount:.5f}*(1-{s})"
        x = "iw/2-(iw/zoom/2)"
        y = "ih/2-(ih/zoom/2)"
    elif motion == "drift":
        # A near-constant gentle zoom with a slow eased pan across the frame.
        zc = 1 + amount
        z = f"{zc:.5f}"
        # Available travel at this zoom, taking a modest fraction so edges never
        # slam into the frame border.
        frac = 0.55
        span = f"iw*(1-1/{zc:.5f})*{frac}"          # horizontal travel budget
        spanv = f"ih*(1-1/{zc:.5f})*{frac}"         # vertical travel budget
        cx = "iw/2-(iw/zoom/2)"
        cy = "ih/2-(ih/zoom/2)"
        d = f"({s}-0.5)"                             # -0.5 .. +0.5, eased
        if anchor == "left":                        # start right, drift left
            x, y = f"{cx}-({span})*{d}", cy
        elif anchor == "right":
            x, y = f"{cx}+({span})*{d}", cy
        elif anchor == "up":
            x, y = cx, f"{cy}-({spanv})*{d}"
        elif anchor == "down":
            x, y = cx, f"{cy}+({spanv})*{d}"
        else:
            x, y = f"{cx}+({span})*{d}", cy
    else:
        return f"{pre},{post}"

    zp = (f"zoompan=z='{z}':d={frames}:x='{x}':y='{y}':"
          f"s={cw}x{ch}:fps={fps}")
    return f"{pre},{zp},{post}"


def kenburns_video_chain(motion="in", amount=0.05, dur=3.0, fps=FPS,
                         out_w=W, out_h=H, supersample=2, anchor="centre"):
    """The same move, for a VIDEO input rather than a still.

    kenburns_chain above holds ONE frame for `frames` output frames (d=frames),
    which is right for a slide and wrong for footage - on a video it freezes the
    first frame. This variant advances one input frame per output frame (d=1) so
    live footage keeps playing while the camera moves over it, and it keeps the
    anti-judder discipline that matters: supersample, smoothstep rather than a
    linear ramp, and a final lanczos downscale.

    Added 22 Sep 2026 for the ERP hype reel, where live establish shots measured
    74% frozen - a web page mid-answer barely moves, so the camera has to.

    anchor="top" PINS THE TOP EDGE INSTEAD OF ZOOMING ABOUT THE CENTRE, and it
    exists because of a defect class found on the Holidayisle kiosk film, 30 Sep
    2026. A centre zoom crops h*a/(2(1+a)) off EVERY edge, so the authored window
    is not the visible window - the edge SWEEPS as the move runs. On a full-page
    web capture the top of the page is a header strap, and at 9 per cent of 1700
    that sweep is 70px, which put the visible edge straight through the strap's
    glyphs on four shots for seconds at a time. It survived every gate because a
    line sliced through the middle keeps its full glyph height, and it survived
    review because sampling the two ENDS of a move shows a clean frame at each.

    With anchor="top" the top edge never moves, so it cannot cross what it never
    reaches, and the whole crop lands on the bottom edge instead - which on a web
    page is the empty run above the footer. Same amount, same motion magnitude,
    nothing lost at the top: measured on four layouts, the bottom edge landed in
    a 261 to 418px gutter with 64 to 78px of clearance. Prefer it over lowering
    the amount, which pays for the fix with the motion the shot needed.

    DEFAULT IS UNCHANGED. Five other builds call this helper, so "centre" stays
    the default and nothing moves unless a caller asks for the anchor.
    """
    cw, ch = out_w * supersample, out_h * supersample
    pre = (f"scale={cw}:{ch}:force_original_aspect_ratio=increase:flags=lanczos,"
           f"crop={cw}:{ch}")
    post = f"scale={out_w}:{out_h}:flags=lanczos,setsar=1,format=yuv420p"
    if motion == "none" or dur <= 0.1:
        return f"{pre},{post}"
    n = max(1, int(round(dur * fps)) - 1)
    s = _smooth(f"on/{n}")
    z = f"1+{amount:.5f}*{s}" if motion == "in" else f"1+{amount:.5f}*(1-{s})"
    y = "0" if anchor == "top" else "ih/2-(ih/zoom/2)"
    zp = (f"zoompan=z='{z}':d=1:x='iw/2-(iw/zoom/2)':y='{y}':"
          f"s={cw}x{ch}:fps={fps}")
    return f"{pre},{zp},{post}"


# preset medium, not slow: at crf 18 the visual difference is negligible, and the
# 3x-oversample zoompan is the render-cost hot spot - "slow" made a long deck take
# far too long to narrate. The oversample (not the x264 preset) is the quality lever.
ENC = ["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p"]


def render_motion(img, out, duration, fps=FPS, motion="in", amount=None,
                  out_w=W, out_h=H, audio=None, gap=0.0, supersample=3,
                  anchor=None):
    """Render one still to an mp4 with smooth motion (optionally muxing audio).

    Drop-in for the old per-script card_segment / slide_segment / kb_slice, which
    all built their own zoompan string. `amount=None` picks a duration-aware
    default so callers get the gentled, non-nervous move for free.
    """
    if amount is None:
        amount = amount_for_duration(duration)
    frames = max(2, int(round(duration * fps)))
    chain = kenburns_chain(motion, amount, frames, fps, out_w, out_h,
                           anchor=anchor, supersample=supersample)

    if audio:
        vf = (f"[0:v]{chain}[v];"
              f"[1:a]apad=pad_dur={gap},"
              f"aformat=sample_rates=48000:channel_layouts=stereo[a]")
        cmd = ["ffmpeg", "-y", "-loop", "1", "-i", str(img), "-i", str(audio),
               "-filter_complex", vf, "-map", "[v]", "-map", "[a]",
               "-t", f"{duration}", *ENC,
               "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
               str(out)]
    else:
        cmd = ["ffmpeg", "-y", "-loop", "1", "-i", str(img),
               "-vf", f"{chain}", "-t", f"{duration}", *ENC, str(out)]
    subprocess.run(cmd, check=True, capture_output=True)
    return duration


# ---------------------------------------------------------------------------
# The OLD move, kept ONLY so before/after comparisons can render the artefact.
# Do not call this in production - it is the judder we are replacing.
# ---------------------------------------------------------------------------
def legacy_chain(motion="in", amount=0.08, frames=90, fps=FPS, out_w=W, out_h=H):
    """The pre-2026-09 linear-ramp, single-oversample zoompan (for A/B only)."""
    if motion == "none" or frames < 2:
        return f"scale={out_w}:{out_h}:flags=lanczos,fps={fps}"
    zoom = (f"1+{amount}*on/{frames}" if motion == "in"
            else f"{1 + amount}-{amount}*on/{frames}")
    return (f"scale={out_w * 2}:{out_h * 2}:flags=lanczos,"
            f"zoompan=z='{zoom}':d={frames}:"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"s={out_w}x{out_h}:fps={fps},format=yuv420p")


def render_legacy(img, out, duration, motion="in", amount=0.08, fps=FPS,
                  out_w=W, out_h=H):
    frames = max(2, int(round(duration * fps)))
    chain = legacy_chain(motion, amount, frames, fps, out_w, out_h)
    subprocess.run(
        ["ffmpeg", "-y", "-loop", "1", "-i", str(img),
         "-vf", chain, "-t", f"{duration}", *ENC, str(out)],
        check=True, capture_output=True)
    return duration
