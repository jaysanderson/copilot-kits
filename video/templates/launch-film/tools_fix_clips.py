#!/usr/bin/env python3
"""Re-derive every INNER clip's data-start/data-duration onto the new takes.

This is the single cause behind all nine bare-stage runs. The retime moved each
frame's JS timeline and its ROOT data-duration, and left the inner `.clip`
elements declaring their OLD Kokoro-era windows. A clip whose data-duration
lapses stops rendering, so nine frames went bare partway through their own slot
and the narration played over an empty stage. Nine symptoms, one cause.

Derivation, not nudging: a clip's start maps through P() like every beat, and a
clip that ran to the END of the old packet is extended to the new SLOT length so
it also covers the 0.65s transition tail rather than expiring inside it. A clip
that ended early was a deliberate staged layer and keeps that intent through P().
"""
import json, pathlib, re, sys
import tools_retime as R

P = pathlib.Path(__file__).parent
FR = P / "compositions/frames"
NAMES = ["01-powered-by", "02-sample-pack", "03-the-hard-page", "04-step-1-split",
         "05-step-2-identify", "06-step-3-ask", "07-step-4-score", "08-step-5-delete",
         "09-the-output", "10-measured", "11-messy-ones", "12-powered-by-close"]
EL = re.compile(r'(<(?:div|img|svg)\b[^>]*?)data-start="([\d.]+)"([^>]*?)data-duration="([\d.]+)"([^>]*?>)')


def main():
    tl = json.load(open(P / "timeline.json"))
    total_changed = 0
    print(f"{'frame':22s} {'take':>7s} {'slot':>7s} {'clips':>6s} {'to-end':>7s} {'staged':>7s}")
    for i, name in enumerate(NAMES):
        f = FR / f"{name}.html"
        s = f.read_text()
        r = R.remap(f"{i+1:02d}")
        slot = tl["scene_dur"][i]
        cand = [m for m in EL.finditer(s) if 'data-width="1920"' not in m.group(0)]
        if not cand:
            sys.exit(f"{name}: no inner timed clips found - the pattern is wrong, not the file")
        packet_end = max(float(m.group(2)) + float(m.group(4)) for m in cand)
        to_end = staged = 0

        def rewrite(m):
            nonlocal to_end, staged
            a, st, b, du, c = m.group(1), float(m.group(2)), m.group(3), float(m.group(4)), m.group(5)
            old_end = st + du
            ns = r(st)
            if old_end >= packet_end - 0.01:
                ne = slot              # ran to the end: now cover the whole slot
                to_end += 1
            else:
                ne = r(old_end)        # deliberate staged layer: keep the intent
                staged += 1
            return f'{a}data-start="{ns:.3f}"{b}data-duration="{max(ne - ns, 0.05):.3f}"{c}'

        s2 = EL.sub(lambda m: m.group(0) if 'data-width="1920"' in m.group(0) else rewrite(m), s)
        assert s2 != s, f"{name}: clip rewrite was inert"
        f.write_text(s2)
        total_changed += to_end + staged
        print(f"{name:22s} {r.new_dur:7.3f} {slot:7.3f} {len(cand):6d} {to_end:7d} {staged:7d}")

    print(f"\n{total_changed} inner clips re-derived across 12 frames")
    # post-check: no clip may now expire before its frame's narration ends
    bad = []
    for i, name in enumerate(NAMES):
        s = (FR / f"{name}.html").read_text()
        take = tl["takes"][i]
        slot = tl["scene_dur"][i]
        ends = [float(m.group(2)) + float(m.group(4)) for m in EL.finditer(s)
                if 'data-width="1920"' not in m.group(0)]
        if max(ends) < take - 0.02:
            bad.append((name, round(max(ends), 3), round(take, 3)))
    print("POST-CHECK, latest clip end vs the take it must cover:")
    print("  " + ("none short" if not bad else f"STILL SHORT: {bad}"))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
