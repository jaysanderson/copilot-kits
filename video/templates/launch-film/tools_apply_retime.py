#!/usr/bin/env python3
"""Apply the measured retime to every frame composition.

Design, and why it is this shape rather than a literal rewrite:

  * Tween POSITIONS stay in the source in OLD-take time. A single block appended
    at the end of each frame walks `tl.getChildren()` and moves each child to
    P(startTime). The population is GSAP's own children, so every beat the frame
    schedules is remapped exactly once, by construction - a hand-edited literal
    list can miss one silently and this cannot.
  * Driver-scrubbed frames keep EVERY threshold in old-take time and instead
    inverse-map the driver read: `stateAt(Q(driver.t))`. The first attempt
    wrapped the thresholds in P() instead, and the verifier caught it - in
    frame 06 the same values are ALSO tween positions, so P() was applied twice
    and ten beats landed up to 0.79s early. Inverting the driver touches one
    line per frame and cannot double-apply.
  * `DURATION - X` becomes `DURATION - P(X)`: X is an old-take position.
  * Tween DURATIONS are left alone. A 0.5s fade is a perceptual constant, not a
    narration-locked time; only positions are locked to words.

Every edit asserts its pattern matched before writing (an inert .replace() that
changes nothing reads as a clean pass), and the file is refused if it already
carries the marker.
"""
import json, pathlib, re, sys
import tools_retime as R

P = pathlib.Path(__file__).parent
FR = P / "compositions/frames"
MARK = "/* == RETIMED (tools_apply_retime.py) == */"

FRAMES = {
    "01-powered-by.html": "01", "02-sample-pack.html": "02", "03-the-hard-page.html": "03",
    "04-step-1-split.html": "04", "05-step-2-identify.html": "05", "06-step-3-ask.html": "06",
    "07-step-4-score.html": "07", "08-step-5-delete.html": "08", "09-the-output.html": "09",
    "10-measured.html": "10", "11-messy-ones.html": "11", "12-powered-by-close.html": "12",
}
DURVAR = {"02-sample-pack.html": "DUR", "06-step-3-ask.html": "T", "07-step-4-score.html": "DUR"}

# Driver reads: inverse-map so old-time thresholds need no edit.
SEQ_EDITS = [
    ("01-powered-by.html", "var s = stateAt(driver.t);", "var s = stateAt(Q(driver.t));"),
    ("03-the-hard-page.html", "var n = countAt(state.t);", "var n = countAt(Q(state.t));"),
    ("06-step-3-ask.html", "var time = driver.t;", "var time = Q(driver.t);"),
    ("06-step-3-ask.html", "BLINK_CYCLES * time / T", "BLINK_CYCLES * driver.t / T"),
    ("12-powered-by-close.html", "applyState(stateAt(driver.t));", "applyState(stateAt(Q(driver.t)));"),
    # End pins already sit at the NEW duration, so the walk must not move them.
    ("06-step-3-ask.html", "tl.set({}, {}, T);", 'tl.set({}, { data: "pin" }, T);'),
    ("07-step-4-score.html", "tl.set({}, {}, DUR);", 'tl.set({}, { data: "pin" }, DUR);'),
]
# DURATION - X  ->  DURATION - P(X)
ARITH_EDITS = [
    ("01-powered-by.html", "DURATION - JITTER_START", "DURATION - P(JITTER_START)"),
    ("02-sample-pack.html", "DUR - IDLE_START", "DUR - P(IDLE_START)"),
    ("09-the-output.html", "DURATION - (ZOOM_AT + ZOOM_DUR)", "DURATION - P(ZOOM_AT + ZOOM_DUR)"),
    ("12-powered-by-close.html", "DURATION - 9.6", "DURATION - P(9.6)"),
]

WALK = """
      %s
      /* Every registered beat moves to its remapped position. Refuses on an
         empty child list, and names anything that would overrun the packet. */
      (function () {
        var kids = tl.getChildren(false, true, true);
        if (!kids.length) throw new Error("retime: no children to reposition");
        var moved = 0, over = [];
        kids.forEach(function (c) {
          if (c.vars && c.vars.data === "pin") return;   /* already in new-take time */
          var s = c.startTime(), n = P(s);
          if (Math.abs(n - s) > 0.0005) { c.startTime(n); moved++; }
          /* Every frame puts its eyebrow in the same top-left zone, so at a FADE
             boundary the incoming eyebrow is already up while the outgoing one is
             still half-opaque and the two smear. Hold any eyebrow until the 0.5s
             transition has finished. */
          var tg = (c.targets ? c.targets() : []);
          var nm = tg.length ? ((tg[0].id || "") + " " + (tg[0].className || "")) : "";
          if (/-eyebrow(\s|$)/.test(nm) && c.startTime() < 0.52) {
            c.startTime(0.52);
          }
          if (c.startTime() + c.duration() > %s + 0.02) {
            over.push(Math.round((c.startTime() + c.duration()) * 1000) / 1000);
          }
        });
        window.__retime = window.__retime || {};
        window.__retime["%s"] = { beats: kids.length, moved: moved, overrun: over };
      })();
"""


def knot_block(lid, durvar, new_dur, old_dur):
    r = R.remap(lid)
    xs = ", ".join(f"{x:.4f}" for x in r.xs)
    ys = ", ".join(f"{y:.4f}" for y in r.ys)
    return f"""{MARK}
      /* Beat times below are in OLD-take time. P() maps them onto the DELIVERED
         take, through {r.n_anchor} word anchors matched by text between the two
         alignments ({r.coverage:.0%} of {max(r.n_old, r.n_new)} words; largest
         un-anchored stretch {r.max_gap:.2f}s). Generated - do not hand-edit. */
      var __KX = [{xs}];
      var __KY = [{ys}];
      function P(t) {{
        if (t <= __KX[0]) return __KY[0] + (t - __KX[0]);
        var n = __KX.length - 1;
        if (t >= __KX[n]) return __KY[n] + (t - __KX[n]) * (__KY[n] / __KX[n]);
        var lo = 0, hi = n;
        while (hi - lo > 1) {{ var m = (lo + hi) >> 1; if (__KX[m] <= t) lo = m; else hi = m; }}
        return __KY[lo] + (t - __KX[lo]) / (__KX[hi] - __KX[lo]) * (__KY[hi] - __KY[lo]);
      }}
      /* Q is P inverse: new-take time -> old-take time. Driver tweens now run
         0 -> the new duration, so a threshold written in old time is compared
         against Q(driver.t) and needs no edit of its own. */
      function Q(u) {{
        if (u <= __KY[0]) return __KX[0] + (u - __KY[0]);
        var n = __KY.length - 1;
        if (u >= __KY[n]) return __KX[n] + (u - __KY[n]) * (__KX[n] / __KY[n]);
        var lo = 0, hi = n;
        while (hi - lo > 1) {{ var m = (lo + hi) >> 1; if (__KY[m] <= u) lo = m; else hi = m; }}
        return __KX[lo] + (u - __KY[lo]) / (__KY[hi] - __KY[lo]) * (__KX[hi] - __KX[lo]);
      }}
      var {durvar} = {new_dur:.3f};  /* measured delivered take (was {old_dur:.3f}) */"""


def main():
    changed = []
    for fname, lid in FRAMES.items():
        path = FR / fname
        s = path.read_text()
        if MARK in s:
            sys.exit(f"{fname} already retimed - refusing to apply twice")
        r = R.remap(lid)
        dv = DURVAR.get(fname, "DURATION")
        pat = re.compile(r"var %s\s*=\s*([0-9.]+);" % dv)
        m = pat.search(s)
        if not m:
            sys.exit(f"{fname}: no `var {dv} = <n>;` found")
        old_dur = float(m.group(1))
        if abs(old_dur - r.old_dur) > 0.01:
            sys.exit(f"{fname}: declared {dv}={old_dur} but old take is {r.old_dur} - "
                     f"the frame is not the one these anchors describe")
        s2 = s[:m.start()] + knot_block(lid, dv, r.new_dur, old_dur) + s[m.end():]
        assert s2 != s, f"{fname}: duration block edit was inert"
        s = s2
        for f2, a, b in SEQ_EDITS + ARITH_EDITS:
            if f2 != fname:
                continue
            if s.count(a) != 1:
                sys.exit(f"{fname}: edit anchor {a!r} appears {s.count(a)} times, expected 1")
            s = s.replace(a, b)
        # append the walk before the IIFE close at the end of the script block
        tail = re.search(r"\n(\s*)\}\)\(\);\s*\n\s*</script>", s)
        if not tail:
            sys.exit(fname + ": could not find the closing IIFE of the script block")
        walk = WALK % ("/* == RETIMED (tools_apply_retime.py) == beat walk == */", f"{r.new_dur:.3f}", fname.replace(".html", ""))
        s = s[:tail.start()] + "\n" + walk + s[tail.start():]
        path.write_text(s)
        changed.append((fname, r.old_dur, r.new_dur, r.n_anchor, r.coverage))
    print(f"{'frame':26s} {'old':>8s} {'new':>8s} {'anchors':>8s} {'cover':>6s}")
    for c in changed:
        print(f"{c[0]:26s} {c[1]:8.3f} {c[2]:8.3f} {c[3]:8d} {c[4]:6.0%}")
    print(f"\n{len(changed)} frames retimed")


if __name__ == "__main__":
    main()
