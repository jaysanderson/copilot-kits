#!/usr/bin/env python3
"""OCR every capture at native resolution and sweep for what must not be on screen.

A filename says nothing about what is inside a screenshot, and a visible address
bar is the realistic way a host leaks, so the population is EVERY image the film
loads, read at full size rather than scaled.

Controls, run on every invocation:
  POSITIVE - each forbidden pattern is rendered into a test image and must be
             recognised, because "OCR found nothing" and "nothing is there" are
             different results and only the control separates them
  NEGATIVE - a clean image of ordinary copy must produce no hit
Patterns live in the machine block below, as data, so a prose edit cannot
silently empty the list.
"""
import re, subprocess, sys, pathlib, tempfile
from PIL import Image, ImageDraw, ImageFont

P = pathlib.Path(__file__).parent

# ---- MACHINE BLOCK: (name, regex). Nothing but tuples. ----
FORBIDDEN = [
    ("fly.dev host",      r"[A-Za-z0-9_-]+\.fly\.dev"),
    ("fly.io host",       r"fly\.io"),
    ("localhost:port",    r"localhost:\d+"),
    ("bearer token",      r"[Bb]earer\s+[A-Za-z0-9._\-]{12,}"),
    ("JWT",               r"eyJ[A-Za-z0-9_\-]{10,}"),
    ("api key label",     r"(?i)\b(api[_ -]?key|admin[_ -]?token|x-api-key|service[_ -]?account)\b"),
    ("nuclia",            r"(?i)\bnuclia\b"),
    ("rag.progress.cloud",r"(?i)rag\.progress\.cloud"),
    ("hosting region",    r"(?i)\baws-[a-z]+-[a-z]+-\d+-\d+\b"),
    ("Johan Delport",     r"(?i)\bjohan\b|\bdelport\b"),
    ("Kelly O'Donnell",   r"(?i)\bkelly\b|o[''’]?donnell"),
    ("ISVCO Holdings",      r"(?i)\bMIP Holdings\b"),
]
# ---- END MACHINE BLOCK ----


def ocr(path):
    out = subprocess.run(["tesseract", str(path), "stdout", "--psm", "11"],
                         capture_output=True, text=True)
    return out.stdout


def scan(text, where, hits):
    for name, pat in FORBIDDEN:
        for m in re.finditer(pat, text):
            hits.append((where, name, m.group(0)[:60]))


def make_control(tmp, strings, clean=False):
    img = Image.new("RGB", (1400, 90 + 54 * len(strings)), "white")
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 34)
    except OSError:
        font = ImageFont.load_default()
    for i, s in enumerate(strings):
        d.text((30, 30 + 54 * i), s, fill="black", font=font)
    p = pathlib.Path(tmp) / ("clean.png" if clean else "planted.png")
    img.save(p)
    return p


def main():
    imgs = sorted(P.glob("assets/*.png")) + sorted(P.glob("assets/*.jpg"))
    if not imgs:
        sys.exit("no captures found - a sweep over nothing is not a pass")
    hits = []
    print(f"OCR over {len(imgs)} captures at native resolution:")
    for im in imgs:
        w, h = Image.open(im).size
        t = ocr(im)
        before = len(hits)
        scan(t, im.name, hits)
        print(f"  {im.name:28s} {w}x{h}  {len(t.split()):5d} words  {len(hits)-before} hit(s)")

    with tempfile.TemporaryDirectory() as tmp:
        # Every pattern gets a specimen. An unplanted pattern reports as a blind
        # class, which is honest but useless - so plant all twelve.
        planted = ["your-app.fly.dev", "deployed on fly.io", "localhost:8080",
                   "Authorization: Bearer sk_live_9aQ2mXnP4LtZ", "x-api-key: 7f3b2a",
                   "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
                   "<zone>", "Johan Delport", "Kelly O'Donnell",
                   "ISVCO Holdings", "nuclia", "rag.progress.cloud"]
        pc, pt = make_control(tmp, planted), None
        pt = ocr(pc)
        found = set()
        for name, pat in FORBIDDEN:
            if re.search(pat, pt):
                found.add(name)
        missing = [n for n, _ in FORBIDDEN if n not in found]
        cc = make_control(tmp, ["Membership application form", "Confidence 0.94 on every field",
                                "Four pages found, none missing"], clean=True)
        ct = ocr(cc)
        neg = []
        scan(ct, "NEGATIVE-CONTROL", neg)

    print(f"\nPOSITIVE CONTROL: {len(found)} of {len(FORBIDDEN)} patterns recognised in a planted image")
    print(f"  recognised: {sorted(found)}")
    if missing:
        print(f"  *** NOT RECOGNISED, so a clean sweep says nothing about these: {missing}")
    print(f"NEGATIVE CONTROL: {len(neg)} hit(s) on ordinary copy (expect 0)" + (f" {neg}" if neg else ""))

    print(f"\nFINDINGS: {len(hits)}")
    for w, n, s in hits:
        print(f"  {w}: {n} -> {s!r}")
    bad = bool(hits) or bool(neg) or bool(missing)
    print("\nSWEEP", "FAIL" if bad else "PASS",
          "- OCR pass means nothing RECOGNISED, not nothing present")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
