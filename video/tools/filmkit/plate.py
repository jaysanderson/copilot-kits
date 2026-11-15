#!/usr/bin/env python3
"""Read the text INSIDE a captured plate, and put it in composition coordinates.

Why this is a separate primitive from the stage: a captured screenshot is pixels.
No font-size rule reaches into it, so an authored-type floor measures the half of
the film that was authored and says nothing about the half that was recorded -
and the recorded half is where the evidence and the qualifications live.

That asymmetry has now been found three times on three films:

* University, 9 Oct: every headline legible, while the answer body, the per-answer
  quality numerals, the synthetic-corpus disclosure and the query-log rows were
  not. Every unreadable item was text inside a plate.
* Kuraray English cut, 17 Oct: headlines ~65px, while the `[1]` citation marker -
  the only visible link between an answer and its source - was the smallest
  object in the film.
* Fin-demo, 16 Oct: 09-the-output.html, the payoff beat, carries ZERO authored text
  and one image. The schema-filled-in proof is entirely plate pixels.

So the population of any legibility verdict is authored type UNION plate text,
and the verdict is reported BY CONTENT CLASS, because the failure correlates with
the class rather than with the average.

DECLARED BLIND CLASS, and it is not optional reading. Tesseract under-reads
white-on-green and orange-on-cream; a two-item gap between two classes on this
instrument is instrument noise, not a finding about the film. A pass here means
NOTHING WAS RECOGNISED, never nothing is present.

THIRD MEMBER OF THAT CLASS, AND THE EXPENSIVE ONE (20 Oct 2026, Harbourline):
WHITE TEXT INSIDE A FILLED DARK DISC. A shortlist card carried its match score
in a black circular badge - 92%, 90%, 89%, 63% - and tesseract read NONE of the
four, on a 2x still, at full confidence settings. The badge is high contrast and
perfectly legible to an eye; what defeats the recogniser is that the glyphs sit
on a dark ground inside a shape with no straight baseline near them.

It cost a true claim. The producer read the zero as a finding about the PRODUCT,
cut "every card carrying a score" from the narration, and wrote into a note
bound for the customer's own room that the feature does not exist - understating
a customer's product, which is the direction nobody re-reads. It was overturned
by an independent agent that LOOKED at the cards.

So the rule has a positive form worth more than the blind list: WHERE AN OCR ZERO
WOULD BE A FINDING ABOUT THE ARTIFACT RATHER THAN ABOUT THE TEXT, CROP THE REGION
AND LOOK AT IT. A zero is only ever evidence when the control has fired on that
exact colour-on-colour combination, and a control built from dark-on-light type
says nothing about a disc. The blind list will never be complete; the habit of
distrusting a zero about absence is the part that transfers. Every call therefore runs a
positive control that renders the strings it must catch and proves the OCR path
recognises them - without it, a clean sweep is indistinguishable from OCR
returning nothing, which is how a serene PASS gets reported over an unread
population.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import subprocess
import tempfile
from dataclasses import dataclass
from urllib.parse import unquote, urlparse

MIN_CONF = 40          # tesseract word confidence below this is not a reading

# OCR is the expensive step, and several checks read the SAME plates: a single
# gate run over one film OCR'd the same captures four times over. The cache is
# keyed on the file's CONTENT hash plus the scale, never its path or mtime, so
# re-capturing a plate under the same filename correctly misses and an untouched
# plate hits. It lives in the system temp directory rather than the repo, so it
# cannot be committed and cannot collide with a project's own files.
_MEM: dict[tuple[str, float], list] = {}
_DISK = pathlib.Path(tempfile.gettempdir()) / "filmkit-ocr-cache"
CACHE = os.environ.get("FILMKIT_OCR_CACHE", "1") != "0"
CONTROL_STRINGS = ("Needs review", "89%", "checksum", "4 / 4")


@dataclass
class Word:
    text: str
    x: float          # native pixel coords inside the source image
    y: float
    w: float
    h: float
    conf: float

    def to_stage(self, box) -> "Word":
        """Map into composition coordinates using the ImageBox it is drawn in.

        Scale is derived per axis from displayed size over natural size, so a
        plate that is letterboxed or non-uniformly fitted still lands correctly.
        """
        if not box.natural_w or not box.natural_h:
            raise ValueError(
                f"{box.selector}: natural size unknown, cannot map plate text into "
                "stage coordinates - resolve the source off disk first"
            )
        sx = box.w / box.natural_w
        sy = box.h / box.natural_h
        return Word(
            text=self.text,
            x=box.x + self.x * sx,
            y=box.y + self.y * sy,
            w=self.w * sx,
            h=self.h * sy,
            conf=self.conf,
        )

    def at_delivery(self, frame_width: int, css_width: int = 390) -> float:
        """Glyph height on the delivery medium, in CSS px.

        Call this on a STAGE-mapped word. Calling it on a native-coordinate word
        measures the source file instead of the film, which is a different and
        usually flattering number.
        """
        return self.h * (css_width / frame_width)


def resolve_src(src: str, project_root: pathlib.Path) -> pathlib.Path | None:
    """Turn an <img> src or a CSS url() into a file on disk, or None."""
    if src.startswith("data:"):
        return None
    if src.startswith("file://"):
        return pathlib.Path(unquote(urlparse(src).path))
    if src.startswith(("http://", "https://")):
        return None
    p = (project_root / src.lstrip("/")).resolve()
    return p if p.exists() else None


def natural_size(path: pathlib.Path) -> tuple[int, int]:
    from PIL import Image

    with Image.open(path) as im:
        return im.size


def _digest(path: pathlib.Path, scale: float) -> str:
    h = hashlib.md5(path.read_bytes()).hexdigest()
    return f"{h}-{scale:g}"


def words(path: pathlib.Path, scale: float = 1.0) -> list[Word]:
    """OCR one image at native resolution and return word boxes.

    scale > 1 upsamples before OCR. Small source text recognises better
    upsampled, and the returned geometry is divided back so coordinates stay in
    NATIVE pixels whatever the scale - otherwise a tuning change silently moves
    every measurement that depends on it.
    """
    from PIL import Image

    key = None
    if CACHE:
        key = (_digest(path, scale), scale)
        if key in _MEM:
            return _MEM[key]
        blob = _DISK / f"{key[0]}.json"
        if blob.exists():
            try:
                rows = json.loads(blob.read_text())
                out = [Word(**r) for r in rows]
                _MEM[key] = out
                return out
            except (ValueError, TypeError):
                blob.unlink(missing_ok=True)   # a corrupt cache entry is not a reading

    with Image.open(path) as im:
        im = im.convert("RGB")
        if scale != 1.0:
            im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
        with tempfile.TemporaryDirectory() as td:
            png = pathlib.Path(td) / "ocr.png"
            im.save(png)
            tsv = subprocess.run(
                ["tesseract", str(png), "stdout", "--psm", "11", "tsv"],
                capture_output=True, text=True, check=True,
            ).stdout
    out = []
    for line in tsv.splitlines()[1:]:
        f = line.split("\t")
        if len(f) < 12:
            continue
        txt = f[11].strip()
        if not txt:
            continue
        try:
            conf = float(f[10])
            left, top, wid, hei = (float(f[6]), float(f[7]), float(f[8]), float(f[9]))
        except ValueError:
            continue
        if conf < MIN_CONF:
            continue
        out.append(Word(txt, left / scale, top / scale, wid / scale, hei / scale, conf))
    if CACHE and key is not None:
        _MEM[key] = out
        try:
            _DISK.mkdir(parents=True, exist_ok=True)
            (_DISK / f"{key[0]}.json").write_text(
                json.dumps([w.__dict__ for w in out]))
        except OSError:
            pass            # a cache that cannot be written is not a failed reading
    return out


def ocr_control(strings=CONTROL_STRINGS, scale: float = 1.0) -> tuple[bool, list[str], list[str]]:
    """Render `strings` and prove this OCR path reads them back.

    Returns (ok, found, missed). A check that reports clean without this having
    passed is reporting that tesseract produced no output, which is a different
    fact from the film being clean.
    """
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (1400, 90 * len(strings) + 40), "white")
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 56)
    except OSError:
        font = ImageFont.load_default()
    for i, s in enumerate(strings):
        d.text((24, 24 + i * 90), s, fill="black", font=font)
    with tempfile.TemporaryDirectory() as td:
        p = pathlib.Path(td) / "control.png"
        img.save(p)
        got = " ".join(w.text for w in words(p, scale=scale))
    norm = lambda s: re.sub(r"\s+", "", s).lower()
    hay = norm(got)
    found = [s for s in strings if norm(s) in hay]
    missed = [s for s in strings if norm(s) not in hay]
    return (len(found) >= max(1, len(strings) // 2), found, missed)


def plate_words(stage, project_root, t: float, upsample: float = 2.0):
    """Every plate on screen at time t, with its text in STAGE coordinates.

    Yields (ImageBox, [Word in stage coords]). Images that cannot be resolved off
    disk are returned with an empty list and named by the caller, because an
    unresolved plate is an unmeasured population and must not read as a clean one.
    """
    root = pathlib.Path(project_root)
    out, unresolved = [], []
    for box in stage.image_boxes(t):
        path = resolve_src(box.src, root)
        if path is None:
            unresolved.append(box.src)
            out.append((box, []))
            continue
        if not box.natural_w:
            nw, nh = natural_size(path)
            box.natural_w, box.natural_h = nw, nh
        ws = [w.to_stage(box) for w in words(path, scale=upsample)]
        out.append((box, ws))
    return out, unresolved
