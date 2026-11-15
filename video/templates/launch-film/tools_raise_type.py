#!/usr/bin/env python3
"""Raise the small authored type so the evidence class stops being fine print.

Measured first (tools_typescale.py): 106 of 178 authored text elements sat under
26px, and the smallest were the EVIDENCE and the QUALIFICATIONS - outcome pills,
the ID, "NO TICK HERE", the per-tile labels - while every headline cleared.
That asymmetry is the one a procurement team catches.

HONEST LIMIT, stated rather than implied: a phone-legible 11px glyph needs 54px
authored at this frame size (scale 0.2031), and a five-row table with four
columns plus a 28-tile grid cannot carry 54px type at all. This raise does not
make the film phone-legible and is not claimed to. It removes the asymmetry
WITHIN each frame and lifts the worst class from 2.6px to about 4.6px at phone
scale, against a 1920 embed - the stated destination - where it is comfortable.

Raising type is MOVING GEOMETRY, so the caller must re-run the layout check and
the rendered-overflow measure afterwards; several rules are held back from the
general bump because their container cannot absorb it.
"""
import pathlib, re, sys

FR = pathlib.Path(__file__).parent / "compositions/frames"
CAP = 26
FACTOR = 1.35
# Rules whose container genuinely cannot take the general bump, with the reason.
HELD = {
    "f02-num": 17,        # numeral inside a small stacked tile badge
    "f02-label": 19,      # caption under a 150px-wide document tile
    "f08-deleted": 17,    # overlay word inside a deleted page card
    "f10-th": 20,         # four-column table header, must not wrap
    "f03-ocr-txt": 24,    # 14 lines of OCR dump in a fixed column
}


def target(sel, fs):
    for k, v in HELD.items():
        if sel.startswith(k):
            return v
    return min(CAP, round(fs * FACTOR))


def main():
    RULE = re.compile(r"(\n\s*)([^\n{}]+?)\s*\{([^{}]*?)\}")
    total = 0
    print(f"{'frame':22s} {'selector':28s} {'was':>5s} {'now':>5s}")
    for f in sorted(FR.glob("*.html")):
        s = f.read_text()
        changes = []

        def sub(m):
            lead, sel, body = m.groups()
            if "@font-face" in sel or "@keyframes" in sel:
                return m.group(0)
            fm = re.search(r"font-size:\s*([0-9.]+)px", body)
            if not fm:
                return m.group(0)
            fs = float(fm.group(1))
            if fs >= CAP:
                return m.group(0)
            key = sel.strip().lstrip(".#").split()[0].split(":")[0].split(",")[0]
            t = target(key, fs)
            if t <= fs:
                return m.group(0)
            changes.append((sel.strip()[:28], fs, t))
            nb = body.replace(fm.group(0), f"font-size: {t}px", 1)
            return f"{lead}{sel} {{{nb}}}"

        s2 = RULE.sub(sub, s)
        if changes:
            assert s2 != s, f"{f.name}: edits listed but nothing written"
            f.write_text(s2)
            for sel, a, b in changes:
                print(f"{f.stem[:22]:22s} {sel:28s} {a:5.0f} {b:5.0f}")
            total += len(changes)
    print(f"\n{total} rules raised (cap {CAP}px, factor {FACTOR}, {len(HELD)} held back by container)")
    if total == 0:
        sys.exit("nothing was raised - the rule pattern found no candidates, which cannot be right")


if __name__ == "__main__":
    main()
