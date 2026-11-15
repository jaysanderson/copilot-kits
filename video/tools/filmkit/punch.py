"""Punch geometry: is this crop legible, and does its edge cut through content.

A punch is a crop of a high-resolution still, blown up so a phrase the voice is
reading can be read in the room. Two things go wrong with them, repeatedly, and
both are arithmetic available before anything renders.

**Magnification is a proxy, and the wrong one.** A 3x floor was the standing rule
and it fails in both directions: a wide row at 2.3x over large source type can
deliver more readable text than a narrow one at 4x over small type. What matters
is the glyph height the frame DELIVERS. `legibility()` measures the median glyph
inside the rect and scales it by the plate factor, so the floor is set on the
thing the room experiences. It reports the ratio beside it rather than instead.

**An edge that lands on ink cuts a card in half.** The first Harbourline cut
cropped a search result at x=2000 and put half a second card hard against the
frame edge, clipping five lines mid-word. A gutter column is uniform and an edge
through content is not, so `assert_edges()` refuses and names the nearest quiet
column. It fired twice for real on its first build - once on that defect, once
on a crop landing exactly on a card's own 1px border, where taking its hint gave
a legal edge and a slightly better frame.

**OCR silence is not a pass.** Where the recogniser reads nothing inside the
rect, `legibility()` says so and the caller falls back to the ratio, because a
clean measurement and an absent one are different findings.

Selftest: `.venv/bin/python scripts/filmkit/punch.py --selftest`
"""
import pathlib
import sys

MIN_GLYPH_PX = 28.0     # delivered glyph height on a 1920-wide frame
EDGE_STD = 20.0         # a punch edge must land in a quiet column
MIN_MAG = 3.0           # fallback floor, used only when OCR reads nothing
MIN_BLOCK_PX = 20.0     # under this, framing a whole block beats nothing - see frame_block


def _lum(png, y0=None, y1=None):
    import numpy as np
    from PIL import Image
    a = np.asarray(Image.open(png).convert("RGB"), dtype=float)
    if y0 is not None:
        a = a[y0:y1]
    return 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]


def strip_rows(png, bright=120.0, limit=200):
    """Leading rows of a page capture that are a dark chrome strip.

    Measured per source, never assumed: a scrolled capture of the same site has
    no strip at all, and a constant eats real pixels off every one of those.
    """
    lum = _lum(png)
    n = 0
    for y in range(min(limit, lum.shape[0])):
        if lum[y].mean() > bright:
            break
        n += 1
    return n


def assert_edges(png, rect, tol=EDGE_STD, hunt=90):
    """Raise if either vertical edge of `rect` sits on ink. Returns a note."""
    x0, y0, x1, y1 = rect
    lum = _lum(png, y0, y1)
    for edge, x in (("left", x0), ("right", x1 - 1)):
        if not (0 <= x < lum.shape[1]):
            continue
        sd = lum[:, x].std()
        if sd <= tol:
            continue
        near = [c for c in range(max(0, x - hunt), min(lum.shape[1], x + hunt))
                if lum[:, c].std() <= tol]
        hint = (f" nearest quiet column {min(near, key=lambda c: abs(c - x))}"
                if near else f" no quiet column within {hunt}px")
        raise SystemExit(
            f"punch {edge} edge at x={x} on {pathlib.Path(png).name} sits on ink "
            f"(column std {sd:.1f} > {tol}): the crop cuts through content.{hint}")
    return f"{pathlib.Path(png).name} edges clear at x={x0} and x={x1 - 1}"


def legibility(png, rect, plate_w, source_scale=2.0,
               min_glyph=MIN_GLYPH_PX, min_mag=MIN_MAG):
    """Raise unless this punch delivers readable type. Returns a note.

    `source_scale` is how many still pixels there are per logical pixel of the
    captured page (2.0 for a 2x screenshot). `plate_w` is the width the crop is
    drawn at on the delivered frame.
    """
    from PIL import Image
    x0, y0, x1, y1 = rect
    cw = x1 - x0
    if cw <= 0 or y1 - y0 <= 0:
        raise SystemExit(f"punch rect {rect} is empty on {png}")
    mag = plate_w / (cw / source_scale)
    scale = plate_w / cw
    name = pathlib.Path(png).name
    try:
        import pytesseract
        d = pytesseract.image_to_data(Image.open(png).crop(rect),
                                      output_type=pytesseract.Output.DICT)
        hs = sorted(d["height"][i] for i, t in enumerate(d["text"])
                    if t.strip() and int(d["conf"][i]) > 40
                    and 8 <= d["height"][i] <= 90)
    except ImportError:
        hs = []
    if hs:
        g = hs[len(hs) // 2] * scale
        if g < min_glyph:
            raise SystemExit(
                f"punch on {name} delivers a median glyph of {g:.0f}px over "
                f"{len(hs)} words, under the {min_glyph:.0f}px floor. Crop to "
                f"the PHRASE with bounded padding, not to its host block.")
        return f"{name} punch {mag:.2f}x, median glyph {g:.0f}px over {len(hs)} words"
    if mag < min_mag:
        raise SystemExit(
            f"punch on {name} magnifies {mag:.2f}x, under the {min_mag}x floor, "
            f"and OCR recognised no words in the rect so the glyph floor could "
            f"not be measured. OCR silence is not a pass.")
    return f"{name} punch {mag:.2f}x, glyph floor UNMEASURED (OCR read 0 words)"


def frame_block(png, rect, plate_w, source_scale=2.0,
                min_glyph=MIN_GLYPH_PX, min_block=MIN_BLOCK_PX, pad=18.0):
    """Turn a rect chosen by eye into one sized by arithmetic, and say which tier.

    `legibility()` above judges a punch somebody already framed. This DERIVES the
    frame, and it exists because judging was not enough: on the Kuraray film 24 of
    26 declared regions were under the glyph floor even at their natural scale,
    because they were page-section rects (780x420) rather than phrase rects. Every
    one would have failed `legibility()` and nothing would have said what to use
    instead.

    Three tiers come back, and they are reported separately because averaging them
    hides the only thing worth knowing:

      FLOOR  the block fits at or above `min_glyph`. Headlines, source cards,
             citation chips, confidence pills, single-sentence answers.
      BLOCK  a paragraph wider than the floor allows, framed WHOLE at the largest
             scale that fits it. Below the floor and UNCLIPPED.
      GUTTER the "block" is a card grid or a whole page, so framing it whole would
             deliver 10 to 16px. A floor-sized window on the densest cluster.

    The ordering rule is the one that matters, and it was learned the expensive way.
    A first pass sized every window from the floor alone and placed it on the ink's
    centre of mass: every glyph duly landed at 28px and 18 of 26 crops sliced a
    paragraph mid-word, which on screen reads as a broken render rather than as a
    close look. **Unclipped at 22px beats clipped at 28px.** A floor constrains the
    window; it does not licence putting the window anywhere.

    Returns (rect, scale, delivered_glyph_px, tier), where `scale` is plate_w over the
    crop's width in SOURCE pixels - the plate-draw factor, not a camera scale; a host
    that punches in page coordinates converts. `tier` carries "/CLIPPED" when
    an edge still crosses a word box, so "nothing is clipped" is a counted result
    rather than something a human decided off a contact sheet. Returns None when OCR
    read nothing inside `rect` - an unreadable region is reported, never guessed at,
    and the caller keeps the declared rect.
    """
    import statistics
    from PIL import Image

    x0, y0, x1, y1 = rect
    try:
        import pytesseract
        d = pytesseract.image_to_data(Image.open(png).crop(rect),
                                      output_type=pytesseract.Output.DICT)
        words = [(d["left"][i] + x0, d["top"][i] + y0, d["width"][i], d["height"][i])
                 for i, t in enumerate(d["text"])
                 if t.strip() and int(d["conf"][i]) > 40]
    except ImportError:
        words = []
    if not words:
        return None

    med = statistics.median(h for _, _, _, h in words)
    band = [w for w in words if 0.55 * med <= w[3] <= 2.2 * med] or words
    src_w = Image.open(png).width

    # The block's own margins, trimming the outermost few per cent so one stray chip
    # cannot define the width of the whole window.
    xs = sorted([w[0] for w in band] + [w[0] + w[2] for w in band])
    ys = sorted([w[1] for w in band] + [w[1] + w[3] for w in band])
    trim = max(1, int(len(xs) * 0.04))
    bl, br = xs[trim - 1] - pad, xs[-trim] + pad
    bt, bb = ys[trim - 1] - pad, ys[-trim] + pad

    def delivered(width):
        return med * (plate_w / width)

    want_w = med * plate_w / min_glyph            # window width that hits the floor
    fit_w = max(1.0, br - bl)
    width = min(max(want_w, 1.0), fit_w) if fit_w > want_w else fit_w
    tier = "FLOOR" if delivered(width) >= min_glyph - 0.05 else "BLOCK"
    if delivered(width) < min_block:
        width, tier = want_w, "GUTTER"            # a grid, not a paragraph

    height = width * (y1 - y0) / max(1, x1 - x0) if x1 > x0 else width * 0.5625
    cx, cy = (bl + br) / 2, (bt + bb) / 2
    nx0 = min(max(cx - width / 2, 0.0), max(0.0, src_w - width))
    ny0 = max(cy - height / 2, 0.0)
    out = (round(nx0), round(ny0), round(nx0 + width), round(ny0 + height))

    cut = any(a < out[0] < a + w or a < out[2] < a + w for a, _, w, _ in band)
    return out, plate_w / width, delivered(width), tier + ("/CLIPPED" if cut else "")


# ------------------------------------------------------------------ selftest

def _specimens(tmp):
    """Specimens derived from shapes observed in real captures, each declaring
    FIRE or QUIET. A check either passes these or declares which it cannot see.
    """
    from PIL import Image, ImageDraw, ImageFont
    f28 = ImageFont.truetype("/Library/Fonts/Managed/ProgressSansText-Md_1479433600.ttf", 28)
    out = []

    # S1 two cards with a real gutter: an edge in the gutter is QUIET, an edge
    # through the second card FIRES. The observed Harbourline defect.
    im = Image.new("RGB", (1200, 400), (255, 255, 255))
    d = ImageDraw.Draw(im)
    for cx in (40, 700):
        d.rectangle([cx, 40, cx + 480, 360], fill=(243, 243, 243))
        d.text((cx + 24, 80), "Toyota LandCruiser Prado", font=f28, fill=(10, 10, 10))
        d.text((cx + 24, 140), "$79,290 from, drive-away", font=f28, fill=(10, 10, 10))
    p = tmp / "s1.png"; im.save(p)
    out.append(("S1 edge in the gutter", "QUIET", p, (40, 40, 620, 360)))
    out.append(("S1 edge through card 2", "FIRE", p, (40, 40, 900, 360)))

    # S2 legibility: the same text crop at two widths.
    im = Image.new("RGB", (1600, 300), (255, 255, 255))
    ImageDraw.Draw(im).text((20, 120), "NSW stamp duty  $1,350", font=f28, fill=(10, 10, 10))
    p = tmp / "s2.png"; im.save(p)
    out.append(("S2 tight crop", "QUIET", p, (0, 100, 500, 200)))
    out.append(("S2 whole-block crop", "FIRE", p, (0, 0, 1600, 300)))

    # S3 the discriminate control: a blank region. OCR reads nothing, so the
    # ratio floor carries it - and a wide blank crop must still FIRE.
    im = Image.new("RGB", (1600, 300), (255, 255, 255))
    p = tmp / "s3.png"; im.save(p)
    out.append(("S3 blank, narrow", "QUIET", p, (0, 0, 400, 300)))
    out.append(("S3 blank, wide (OCR silent)", "FIRE", p, (0, 0, 1600, 300)))
    return out


def selftest():
    import tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="filmkit-punch-"))
    bad = 0
    for label, expect, png, rect in _specimens(tmp):
        try:
            assert_edges(png, rect)
            note = legibility(png, rect, plate_w=1696)
            got, detail = "QUIET", note
        except SystemExit as e:
            got, detail = "FIRE", str(e).split(":")[0]
        ok = got == expect
        bad += not ok
        print(f"  [{'ok ' if ok else 'BAD'}] {label:<30} expect {expect:<5} got {got:<5}  {detail[:70]}")
    print(f"\n{'PASS' if not bad else 'FAIL'}: {bad} specimen(s) disagreed")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else
             print(__doc__) or 0)
