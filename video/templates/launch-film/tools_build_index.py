#!/usr/bin/env python3
"""Rebuild index.html from the MEASURED take durations.

Schedule, derived - no inherited window:
    PRE  0.30  the picture leads the voice, so a scene has settled when the line starts
    GAP  0.15  silence between lines
    XF   0.50  cross-transition, fired at the incoming scene's start
    TAIL 1.10  hold on the close card after the last word

    T[1]      = PRE
    T[i+1]    = T[i] + V[i] + GAP
    scene[i].start    = T[i] - PRE
    scene[i].duration = V[i] + GAP + XF        (last: V + PRE + TAIL)

Each frame's root data-duration is set to its scene duration to match, which is
the pattern the original build used (root = slot length, internal timeline =
take length). The captions scene is not emitted.
"""
import json, pathlib, re, subprocess, sys

P = pathlib.Path(__file__).parent
VOICE = P / "assets/voice-el"
FRAMES = [
    ("01-powered-by", "01"), ("02-sample-pack", "02"), ("03-the-hard-page", "03"),
    ("04-step-1-split", "04"), ("05-step-2-identify", "05"), ("06-step-3-ask", "06"),
    ("07-step-4-score", "07"), ("08-step-5-delete", "08"), ("09-the-output", "09"),
    ("10-measured", "10"), ("11-messy-ones", "11"), ("12-powered-by-close", "12"),
]
PRE, GAP, XF, TAIL = 0.30, 0.15, 0.50, 1.10
NAVY = "#00216B"

# Transition style per boundary, carried over from the original cut (the GRAMMAR of
# the edit is authored; only its TIMING is re-derived).
TRANS = ["fade", "slide", "slide", "fade", "slide", "fade", "fade", "zoom", "slide", "fade", "blur"]


def dur(p):
    return float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
        capture_output=True, text=True, check=True).stdout.strip())


def main():
    V = [dur(VOICE / f"{lid}.wav") for _, lid in FRAMES]
    T, t = [], PRE
    for v in V:
        T.append(round(t, 3)); t += v + GAP
    sc_start = [round(T[i] - PRE, 3) for i in range(12)]
    sc_dur = [round(V[i] + GAP + XF, 3) for i in range(11)] + [round(V[11] + PRE + TAIL, 3)]
    total = round(sc_start[11] + sc_dur[11], 3)

    # frame roots must declare their slot length
    for i, (name, _) in enumerate(FRAMES):
        f = P / "compositions/frames" / f"{name}.html"
        s = f.read_text()
        pat = re.compile(r'(data-composition-id="%s" data-width="1920" data-height="1080" data-duration=")[0-9.]+(")' % name)
        if pat.search(s):
            s = pat.sub(lambda m: f"{m.group(1)}{sc_dur[i]:.3f}{m.group(2)}", s)
        else:
            # frame 12's root carries no data-duration at all - add one rather than
            # leaving its slot length declared only in the host.
            anchor = ('id="root" data-composition-id="%s" data-width="1920" data-height="1080"' % name)
            if s.count(anchor) != 1:
                sys.exit(f"{name}: cannot locate the root element to set a duration on")
            s = s.replace(anchor, anchor + f' data-duration="{sc_dur[i]:.3f}"')
        f.write_text(s)

    L = []
    for i, (name, lid) in enumerate(FRAMES):
        track = i % 2
        L.append(f'      <div data-hf-id="hf-sc{i:02d}" id="el-{name}" class="scene" '
                 f'data-composition-id="{name}" data-composition-src="compositions/frames/{name}.html" '
                 f'data-start="{sc_start[i]:.3f}" data-duration="{sc_dur[i]:.3f}" data-track-index="{track}"></div>')
        L.append(f'      <audio data-hf-id="hf-vo{i:02d}" id="el-{name}-voice" src="assets/voice-el/{lid}.wav" '
                 f'data-start="{T[i]:.3f}" data-duration="{V[i]:.3f}" data-track-index="10" data-volume="1"></audio>')
        L.append("")
    scenes = "\n".join(L).rstrip()

    tr = []
    for i in range(11):
        a, b = FRAMES[i][0], FRAMES[i + 1][0]
        at = f"{sc_start[i + 1]:.3f}"
        k = TRANS[i]
        if k == "fade":
            tr.append(f'        tl.to("#el-{a}", {{ opacity: 0, duration: 0.5, ease: "power2.inOut" }}, {at});')
            tr.append(f'        tl.fromTo("#el-{b}", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.5, ease: "power2.inOut" }}, {at});')
        elif k == "slide":
            tr.append(f'        tl.to("#el-{a}", {{ x: -1920, duration: 0.5, ease: "power3.inOut" }}, {at});')
            tr.append(f'        tl.fromTo("#el-{b}", {{ x: 1920, opacity: 1 }}, {{ x: 0, opacity: 1, duration: 0.5, ease: "power3.inOut" }}, {at});')
        elif k == "zoom":
            tr.append(f'        tl.to("#el-{a}", {{ scale: 2.5, opacity: 0, filter: "blur(8px)", duration: 0.4, ease: "power3.in" }}, {at});')
            tr.append(f'        tl.fromTo("#el-{b}", {{ scale: 0.5, opacity: 0, filter: "blur(8px)" }}, {{ scale: 1, opacity: 1, filter: "blur(0px)", duration: 0.4, ease: "power3.out" }}, {at});')
        else:
            tr.append(f'        tl.to("#el-{a}", {{ filter: "blur(10px)", scale: 1.03, opacity: 0, duration: 0.6, ease: "power2.inOut" }}, {at});')
            tr.append(f'        tl.fromTo("#el-{b}", {{ filter: "blur(10px)", scale: 0.97, opacity: 0 }}, {{ filter: "blur(0px)", scale: 1, opacity: 1, duration: 0.6, ease: "power2.inOut" }}, {at});')
    trans = "\n".join(tr)

    html = f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=1920, height=1080">
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js" integrity="sha384-sG0Hv1tP1lZCk9KQmrIbY/XNwi+OY84GQqhMscbnsoBFqAz8KNCil1kvfL3Hbbk2" crossorigin="anonymous"></script>
    <style>
      * {{
        margin: 0;
        padding: 0;
        box-sizing: border-box;
      }}
      html,
      body {{
        width: 1920px;
        height: 1080px;
        overflow: hidden;
        background: #000;
      }}
      /* Progress ink navy (Blue P1) is the stage for the whole film. */
      #root {{
        position: relative;
        width: 1920px;
        height: 1080px;
        overflow: hidden;
        background: {NAVY};
      }}
      .scene {{
        position: absolute;
        inset: 0;
        width: 100%;
        height: 100%;
      }}
    </style>
  </head>
  <body>
    <div data-hf-id="hf-adas" id="root" data-composition-id="main" data-start="0" data-duration="{total:.3f}" data-width="1920" data-height="1080">
{scenes}

      <!-- No captions scene: captions are off by default (GM, 4 Sep 2026) and the
           GM's stated preference on 16 Oct is a clean frame so a player's own
           auto-captioning has nothing to collide with. -->
    </div>

    <script>
      window.__timelines = window.__timelines || {{}};
      window.__timelines["main"] = gsap.timeline({{ paused: true }});
      // -- frame transitions, fired at each incoming scene's own measured start --
      (function () {{ var tl = window.__timelines["main"];
{trans}
        tl.to({{}}, {{ duration: {total:.3f} }}, 0); // full-span anchor - main.duration() == composition total
      }})();
    </script>
  </body>
</html>
"""
    (P / "index.html").write_text(html)
    print(f"{'#':>2s} {'take':>7s} {'voice@':>8s} {'scene@':>8s} {'scene_dur':>9s}")
    for i, (name, _) in enumerate(FRAMES):
        print(f"{i+1:2d} {V[i]:7.3f} {T[i]:8.3f} {sc_start[i]:8.3f} {sc_dur[i]:9.3f}  {name}")
    print(f"\nspeech {sum(V):.3f}s + {11*GAP:.2f}s gaps + {PRE:.2f}s pre + {TAIL:.2f}s tail = {total:.3f}s")
    json.dump({"takes": V, "voice_start": T, "scene_start": sc_start, "scene_dur": sc_dur,
               "total": total, "PRE": PRE, "GAP": GAP, "XF": XF, "TAIL": TAIL},
              open(P / "timeline.json", "w"), indent=1)


if __name__ == "__main__":
    main()
