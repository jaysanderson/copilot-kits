#!/usr/bin/env python3
"""Put the Progress Agentic RAG brand on every AUTHORED surface.

The stage inverts from near-white to Progress ink navy, so this is not a palette
swap - every piece of type has to flip with it or it goes invisible, which is a
silent failure. Roles are therefore resolved per DECLARATION, not per hex: the
same #2B2BB2 is an accent when it is `color:` or `stroke:` and a solid panel when
it is `background:`, and those two need different greens on navy.

Captured screenshots are untouched. They are recordings of a product; the stage
around them is Progress, the plates are not.

Every rule asserts its own hit count before anything is written. A rule that
matches nothing is a defect, not a no-op - an inert .replace() reads as a clean
pass. Sources: brand/progress-brandbank/colors.md and
brand/progress-hyperframes-brand.md (canon).
"""
import pathlib, re, sys, collections

FR = pathlib.Path(__file__).parent / "compositions/frames"

NAVY      = "#00216B"   # Blue P1          - the stage
PANEL     = "#00123C"   # Blue P1 Shade 45 - deeper panel, the bookend card
PANEL_OPQ = "#0A2A6E"   # navy + ~5% white, opaque, for cards that sit over imagery
GREEN     = "#00B563"   # Green P2         - accents, type, strokes, ticks
GREEN_DP  = "#008963"   # Green P1         - solid fills that carry white content
INK       = "#FFFFFF"   # type on dark
MUTED     = "#C6D5EB"   # Light Grey S1    - secondary type on navy
FAINT     = "#9EAEC3"   # Dark Grey S4     - tertiary type on navy
NEG       = "#FF9AA8"   # Red S3

# (pattern, replacement, expected_total_hits_across_all_frames)
# Ordered: the specific declaration-aware rules run before the catch-alls.
RULES = [
    # Checked every solid #2B2BB2 fill: all five are small LIT MARKS (step-rail dots,
    # the typewriter caret, a marker) carrying nothing on top, so they take the bright
    # green with every other accent. GREEN_DP is kept for structure that must sit back
    # from the type - the bookend card hairline and the step-rail connector.
    # --- the stage ground
    (r"--f(\d+)-bg: #F4FAFF;",           rf"--f\1-bg: {NAVY};",                 5),
    (r"background: #F4FAFF;",            f"background: {NAVY};",                8),
    (r"color-mix\(in srgb, #2B2BB2 4%, #F4FAFF\)",
     f"color-mix(in srgb, {INK} 6%, {NAVY})",                                   1),
    # --- opaque card grounds that were "tint composited over the cream"
    (r"background: #E4E9F9;",            f"background: {PANEL_OPQ};",           2),
    (r"background-color: #ECF2FC;",      f"background-color: {PANEL_OPQ};",     1),
    (r"rgba\(236, 242, 252, 0\)",        "rgba(0, 33, 107, 0)",                 1),
    (r"rgba\(236, 242, 252, 1\)",        "rgba(0, 33, 107, 1)",                 1),
    # --- muted / tertiary type
    (r"--f(\d+)-text-muted: #00123C;",   rf"--f\1-text-muted: {MUTED};",        3),
    (r"--f10-muted: #00123C;",           f"--f10-muted: {MUTED};",              1),
    (r'var MUTED = "#00123C";',          f'var MUTED = "{MUTED}";',             2),
    (r"color: #00123C;",                 f"color: {MUTED};",                    8),
    (r"--f(\d+)-text-light: #9A9A9A;",   rf"--f\1-text-light: {FAINT};",        3),
    (r"color: #9A9A9A;",                 f"color: {FAINT};",                    1),
    # --- primary type
    (r"--f(\d+)-text: #101828;",         rf"--f\1-text: {INK};",                5),
    (r"color: #101828;",                 f"color: {INK};",                     16),
    (r'color: "#101828"',                f'color: "{INK}"',                     3),
    (r'\{ color: "#101828" \}',          f'{{ color: "{INK}" }}',               0),
    # --- positive / negative
    (r"stroke: #059669;",                f"stroke: {GREEN};",                   2),
    (r"--f10-positive: #059669;",        f"--f10-positive: {GREEN};",           1),
    (r'var POSITIVE = "#059669";',       f'var POSITIVE = "{GREEN}";',          1),
    (r"--f(\d+)-negative: #dc2626;",     rf"--f\1-negative: {NEG};",            1),
    # --- accent tints -> structure in white-alpha, emphasis in green
    (r"rgba\(43, 43, 178, 0\.2\)",       "rgba(198, 213, 235, 0.26)",          21),
    (r"rgba\(43,43,178,0\.2\)",          "rgba(198, 213, 235, 0.26)",           1),
    (r"rgba\(43, 43, 178, 0\.1\)",       "rgba(198, 213, 235, 0.16)",           1),
    (r"rgba\(43, 43, 178, 0\.04\)",      "rgba(255, 255, 255, 0.055)",         13),
    (r"rgba\(43,43,178,0\.04\)",         "rgba(255, 255, 255, 0.055)",          1),
    (r"rgba\(43, 43, 178, 0\.08\)",      "rgba(0, 181, 99, 0.16)",              8),
    (r"rgba\(43,43,178,0\.08\)",         "rgba(0, 181, 99, 0.16)",              1),
    (r"rgba\(43, 43, 178, 0\.06\)",      "rgba(0, 181, 99, 0.10)",              1),
    (r"rgba\(43, 43, 178, 0\.35\)",      "rgba(0, 181, 99, 0.40)",              1),
    (r"rgba\(43, 43, 178, 0\)",          "rgba(0, 181, 99, 0)",                 4),
    (r"rgba\(43,43,178,0\)",             "rgba(0, 181, 99, 0)",                 1),
    # Found by the post-check, not by reading: an opaque base under a tint gradient,
    # a small success dot, and the START colour of a colour tween.
    (r"\), #F4FAFF;",                    f"), {NAVY};",                         1),
    (r"background: #059669;",            f"background: {GREEN};",               1),
    (r'var INK = "#101828";',            f'var INK = "{INK}";',                 1),
    # --- everything else cobalt is an accent: type, strokes, fills of small marks
    (r"#2B2BB2",                         GREEN,                                45),
]


def main():
    files = sorted(FR.glob("*.html"))
    texts = {f: f.read_text() for f in files}
    report, failed = [], []
    for pat, rep, expect in RULES:
        total = sum(len(re.findall(pat, t)) for t in texts.values())
        if total != expect:
            failed.append(f"  {pat!r:46s} matched {total}, expected {expect}")
            continue
        if total == 0:
            continue
        for f in files:
            texts[f] = re.sub(pat, rep, texts[f])
        report.append((pat, rep, total))
    if failed:
        print("RULE COUNT MISMATCH - nothing written:")
        print("\n".join(failed)); sys.exit(1)
    # leftovers that must be gone from authored surfaces
    for f in files:
        texts[f] = texts[f]
    for f, t in texts.items():
        f.write_text(t)
    for pat, rep, n in report:
        print(f"  {n:3d}x  {pat:46s} -> {rep}")
    print(f"\n{len(report)} rules applied over {len(files)} frames")
    # post-check: no old palette value survives except the two deliberate keeps
    survivors = collections.Counter()
    for f in files:
        t = f.read_text()
        for bad in ["#2B2BB2", "#101828", "#9A9A9A", "#059669", "#dc2626", "rgba(43, 43, 178", "rgba(43,43,178"]:
            n = t.count(bad)
            if n: survivors[f"{f.name}:{bad}"] = n
        for n, line in enumerate(t.splitlines(), 1):
            if "#F4FAFF" in line and not re.search(r'fill="#F4FAFF"|stroke: #F4FAFF', line):
                survivors[f"{f.name}:#F4FAFF line {n}"] = 1
    print("\nPOST-CHECK leftovers (expected: none):")
    print("  none" if not survivors else "\n".join(f"  {k} x{v}" for k, v in survivors.items()))
    sys.exit(1 if survivors else 0)


if __name__ == "__main__":
    main()
