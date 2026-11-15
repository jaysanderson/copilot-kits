#!/usr/bin/env python3
"""Assert the lockup's polarity against the panel it is actually drawn on.

Getting the pair the wrong way round is silent: the reversed mark's green hex
glyph still shows, so a white wordmark on a light panel reads as a design
choice rather than a defect. A filename is not evidence about a background, so
measure both and compare (brand/logos/README.md).
"""
import re, sys, pathlib, subprocess, tempfile
import numpy as np
from PIL import Image

P = pathlib.Path(__file__).parent
BOOKENDS = {"01-powered-by.html": "f01-card", "12-powered-by-close.html": "f12-card"}


def _lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def rel_lum(r, g, b):
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def ratio(l1, l2):
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def lum_hex(h):
    h = h.lstrip("#")
    r, g, b = (int(h[i:i+2], 16) for i in (0, 2, 4))
    return rel_lum(r, g, b)


def main():
    svg = P / "assets/logo-progress-arag.svg"
    with tempfile.TemporaryDirectory() as tmp:
        png = pathlib.Path(tmp) / "mark.png"
        subprocess.run([str(P.parent / ".venv/bin/python"), "-c",
                        f"import cairosvg;cairosvg.svg2png(url={str(svg)!r},write_to={str(png)!r},output_width=620)"],
                       check=True)
        a = np.array(Image.open(png).convert("RGBA")).astype(float)
    opaque = a[..., 3] > 40
    mark = float(np.mean([rel_lum(*px[:3]) for px in a[opaque]]))
    print(f"mark: {svg.name}  mean relative luminance of opaque pixels = {mark:.4f}  "
          f"({int(opaque.sum())} px)")

    ok = True
    for fname, cardid in BOOKENDS.items():
        s = (P / "compositions/frames" / fname).read_text()
        # the panel the mark sits on
        blk = re.search(r"[.#]%s \{(.*?)\}" % cardid, s, re.S)
        if not blk:
            print(f"  {fname}: no .{cardid} rule found"); ok = False; continue
        bg = re.search(r"background:\s*(#[0-9A-Fa-f]{6}|var\(--[a-z0-9-]+\))", blk.group(1))
        val = bg.group(1)
        if val.startswith("var("):
            tok = val[4:-1]
            val = re.search(r"%s:\s*(#[0-9A-Fa-f]{6})" % re.escape(tok), s).group(1)
        pl = lum_hex(val)
        cr = ratio(mark, pl)
        good = mark > pl and cr >= 4.5
        print(f"  {fname:26s} panel {val} L={pl:.4f}  mark L={mark:.4f}  "
              f"contrast {cr:.1f}:1  mark is {'LIGHTER' if mark > pl else 'DARKER'}  "
              f"{'OK' if good else '*** WRONG POLARITY'}")
        if not good: ok = False

    # the stage, for the record
    print(f"  stage #00216B L={lum_hex('#00216B'):.4f} (for the record)")
    # control: the light-background mark must FAIL this same assertion on a dark panel
    alt = P.parent / "brand/logos/primary-horizontal.svg"
    with tempfile.TemporaryDirectory() as tmp:
        png = pathlib.Path(tmp) / "alt.png"
        subprocess.run([str(P.parent / ".venv/bin/python"), "-c",
                        f"import cairosvg;cairosvg.svg2png(url={str(alt)!r},write_to={str(png)!r},output_width=620)"],
                       check=True)
        b = np.array(Image.open(png).convert("RGBA")).astype(float)
    op = b[..., 3] > 40
    am = float(np.mean([rel_lum(*px[:3]) for px in b[op]]))
    acr = ratio(am, lum_hex("#00123C"))
    fires = acr < 4.5
    print(f"\nCONTROL: the light-background lockup ({alt.name}) measures L={am:.4f}, "
          f"contrast {acr:.1f}:1 on the #00123C panel -> "
          f"{'DETECTED as wrong polarity' if fires else 'NOT DETECTED - CHECK IS DECORATION'}")
    if not fires: ok = False
    print("\nPOLARITY", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
