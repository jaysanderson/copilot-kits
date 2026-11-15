#!/usr/bin/env python3
"""Reconcile every FIGURE a film shows against every figure it says.

Run:  .venv/bin/python scripts/filmkit/checks/figures.py <film-root> [--script SCRIPT.md]
      .venv/bin/python scripts/filmkit/checks/figures.py --selftest

WHY. fin-demo-showcase shipped two figure defects that every gate passed, because
each gate read ONE population:
  * a captured plate's header read "28 pages - 8 applications" while the voice
    said seven. The FILM was right (the batch holds seven; the 8 is the example
    number in the filename leaking into the app as a count), so the screen is
    not the authority and this check never assumes it is.
  * "89% overall confidence" on one frame and "99%" under an OVERALL column on
    another, same model, same four pages, nothing saying they are different
    measures.

THREE POPULATIONS, all read, all counted, and zero of zero is a FAIL:
  authored  - FilmStage.text_boxes(t) across the timeline, plus visible_strings
              as a cross-check (strings with no box are kept, without geometry)
  plate     - text OCR'd out of every captured image on screen (plate.words),
              mapped into stage coordinates, then CLIPPED to what is visible
              (frame edge and any overflow-hidden ancestor), so a figure in the
              part of a screenshot the crop cuts off is not counted as shown
  voice     - the narration script (indented blocks under "## Line N ... (Frame K)")

METHOD. Sweep for the CLAIM (a number: digits, number words, ranges, percent) and
only then test each hit for its qualifier. Figures are grouped by SUBJECT, never
by value (28 pages and 4 pages are not in conflict; 7 applicants and 8
applications are one subject). "seven" and "7" are one figure.

VERDICTS (one function, `verdict`, prints and registers; exit 1 on any FAIL):
  CONTRADICTION  FAIL    the voice states exactly ONE value for a subject and a
                         frame shows a different value for it
  UNDISTINGUISHED FAIL   two or more places show a different figure for one
                         MEASURE (confidence/score) and no measuring-basis word
                         (accuracy, hand-labelled, per-field ...) sits near them
  SCREEN-ONLY    REVIEW  a counted figure on a frame that the voice never states
  VOICE-ONLY     REVIEW  a counted figure the voice states that no frame shows
  REVIEW items are printed in full, are NOT failures, and are UNVERIFIED by this
  instrument: it can say "not recognised", never "not present".

DECLARED BLIND CLASSES (also printed on every run):
  * OCR: tesseract under-reads white-on-green and orange-on-cream. A VOICE-ONLY
    or SCREEN-ONLY line is a candidate, not a finding; a PASS means nothing was
    recognised, never nothing is present.
  * Figures with no counted noun and no measure word ("1 OF 5", "4 / 4",
    "47/48", seconds, token counts) are counted as UNCLASSIFIED and not compared.
  * Voice "one X per Y" and "Step one" are skipped as ratios and ordinals.
  * A voice subject with several stated values (pages: 28 and four) is not
    singleton, so a differing screen value there is REVIEW, not FAIL.
  * CSS background-size/position cropping and object-fit are not applied; a
    plate is assumed to be drawn whole inside its clip rectangle.
  * An element covered by a later sibling is counted as visible (only opacity,
    display, visibility, frame edge and overflow clips are applied).
  * Samples are timeline points (default 20 per composition); a figure shown
    between samples is caught only through visible_strings, without geometry.
  * Digits inside a hyphenated or dotted token (example-8-bulk.pdf, p11, 5.5 in
    a model name) are not figures, by design.
  * Voice qualifiers are read within the same sentence only.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys
from dataclasses import dataclass, field

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from filmkit.stage import FilmStage  # noqa: E402
from filmkit import plate  # noqa: E402

# ---------------------------------------------------------------- numbers

_UNITS = {w: i for i, w in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve thirteen "
    "fourteen fifteen sixteen seventeen eighteen nineteen".split())}
_TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60,
         "seventy": 70, "eighty": 80, "ninety": 90}
_WORDNUM = "|".join(sorted(list(_UNITS) + list(_TENS), key=len, reverse=True))
_NUMWORD = rf"(?:(?:{'|'.join(_TENS)})(?:[\s-](?:one|two|three|four|five|six|seven|eight|nine))?|{_WORDNUM})"
_NUMDIG = r"\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?"
_NUM = rf"(?:{_NUMDIG}|{_NUMWORD})"

FIG_RE = re.compile(
    rf"(?<![\w\-./])(?P<pre>under|below|over|above|at least)?\s*"
    rf"(?P<a>{_NUM})(?![\w\-/])(?:\s*(?:to|-|–)\s*(?P<b>{_NUM})(?![\w\-/]))?"
    rf"\s*(?P<unit>%|percent|per cent)?",
    re.I,
)


def to_num(s: str) -> float:
    s = s.lower().replace(",", "").strip()
    if re.fullmatch(_NUMDIG, s):
        return float(s)
    parts = re.split(r"[\s-]+", s)
    return float(sum(_TENS.get(p, _UNITS.get(p, 0)) for p in parts))


# ---------------------------------------------------------------- subjects

COUNT_SUBJECTS = {
    "applications": r"applications?|applicants?",
    "pages": r"pages?",
    "files": r"files?",
    "kinds": r"kinds?",
    "models": r"models?",
    "runs": r"runs?",
    "fields": r"fields?",
    "notes": r"notes?",
}
# A MEASURE: what a percent is a percent OF. confidence/overall/score/accuracy are
# one family on purpose - the defect is the same word ("overall") naming two things.
MEASURE_WORDS = r"confidence|overall|accuracy|scores?|scored"
# Words that say WHAT is being scored (the measuring basis). Deliberately does NOT
# contain the measure words themselves, or "overall confidence" would qualify itself.
QUALIFIERS = (r"accuracy|hand-?labell?ed|reference|scored against|per-?field|"
              r"self-reported|bake-?off|ground truth")


MIN_LINE_CONF = 80.0      # median OCR confidence of a line; below it the line is exhibit noise
NOISE_LINES = 0           # lines dropped for low confidence, printed so the drop is never silent


@dataclass
class Item:
    text: str
    x: float
    y: float
    w: float = 0.0
    h: float = 0.0
    conf: float = 100.0      # OCR word confidence; authored text is 100

    @property
    def cx(self): return self.x + self.w / 2
    @property
    def cy(self): return self.y + self.h / 2


@dataclass
class Fig:
    pop: str                 # authored | plate | voice
    where: str               # frame name or "Line N"
    raw: str
    lo: float
    hi: float
    unit: str                # count | percent
    subject: str             # a COUNT_SUBJECTS key, "measure", "threshold" or "?"
    ctx: str                 # neighbourhood text, for printing and the qualifier test
    qualified: bool
    cx: float = 0.0
    cy: float = 0.0
    t: float = -1.0

    @property
    def values(self): return {self.lo, self.hi}
    def show(self):
        rng = f"{self.lo:g}" if self.lo == self.hi else f"{self.lo:g}-{self.hi:g}"
        return f"{rng}{'%' if self.unit == 'percent' else ''} [{self.subject}] ({self.pop}, {self.where}) {self.raw!r}"


def _words(s): return re.findall(r"[A-Za-z][A-Za-z'\-]*", s)


def classify(line: str, m: re.Match) -> tuple[str, str]:
    """(unit, subject) for one number hit inside one line of text."""
    after = line[m.end():]
    before = line[: m.start()]
    pre = (m.group("pre") or "").lower()
    if m.group("unit"):
        if pre in ("under", "below"):
            return "percent", "threshold"
        return "percent", "measure"
    nxt = re.match(r"\s*(?:[-–·|]\s*)?(?:\w+\s+){0,1}?(" + "|".join(COUNT_SUBJECTS.values()) + r")\b",
                   after, re.I)
    if nxt:
        noun = nxt.group(1).lower()
        for k, rx in COUNT_SUBJECTS.items():
            if re.fullmatch(rx, noun):
                return "count", k
    return "count", "?"


def skip_figure(line: str, m: re.Match) -> bool:
    """Ratios and ordinals that are not claims about the world."""
    a = m.group("a").lower()
    before = line[: m.start()].rstrip().lower()
    after = line[m.end():].lower()
    if a in ("one", "1") and re.match(r"\s*(?:\w+\s+){0,3}per\b", after):
        return True                                   # "one application per applicant"
    if before.endswith("step") or before.endswith("page") or before.endswith("p"):
        return True                                   # "Step one", "page 3" (label, not count)
    if re.match(r"\s*(?:of|/)\s*\d", after) and not m.group("unit"):
        return True                                   # "1 OF 5", "4 / 4"
    return False


def figures_in_line(line: str, pop: str, where: str, ctx: str, cx=0.0, cy=0.0, t=-1.0) -> tuple[list[Fig], int]:
    """(figures, skipped). Sweeps for the NUMBER first; qualifier test comes after."""
    out, skipped = [], 0
    for m in FIG_RE.finditer(line):
        if skip_figure(line, m):
            skipped += 1
            continue
        unit, subject = classify(line, m)
        a = to_num(m.group("a"))
        b = to_num(m.group("b")) if m.group("b") else a
        out.append(Fig(pop, where, m.group(0).strip(), min(a, b), max(a, b), unit, subject,
                       ctx, bool(re.search(QUALIFIERS, ctx, re.I)), cx, cy, t))
    return out, skipped


# ---------------------------------------------------------------- scenes

def lines_from_items(items: list[Item], gap: float = 90.0) -> list[Item]:
    """Join items that sit on one row into reading-order lines."""
    rows: list[list[Item]] = []
    for it in sorted(items, key=lambda i: (i.cy, i.x)):
        for r in rows:
            ref = r[0]
            if abs(ref.cy - it.cy) <= max(6.0, 0.6 * max(ref.h, it.h, 1)):
                r.append(it)
                break
        else:
            rows.append([it])
    out = []
    for r in rows:
        r.sort(key=lambda i: i.x)
        cur = [r[0]]
        for it in r[1:]:
            prev = cur[-1]
            if it.x - (prev.x + prev.w) <= gap:
                cur.append(it)
            else:
                out.append(_merge(cur)); cur = [it]
        out.append(_merge(cur))
    return out


def _merge(cur: list[Item]) -> Item:
    x0 = min(i.x for i in cur); y0 = min(i.y for i in cur)
    x1 = max(i.x + i.w for i in cur); y1 = max(i.y + i.h for i in cur)
    cs = sorted(i.conf for i in cur)
    return Item(" ".join(i.text for i in cur), x0, y0, x1 - x0, y1 - y0, cs[len(cs) // 2])


def figures_in_scene(items: list[Item], pop: str, where: str, t: float,
                     near_dx=650.0, near_dy=260.0) -> tuple[list[Fig], int]:
    """Figures in one frame-instant. Context = every item within a box around the figure."""
    global NOISE_LINES
    figs, skipped, unread = [], 0, 0
    lines = lines_from_items(items)
    for ln in lines:
        if ln.conf < MIN_LINE_CONF:
            unread += 1              # OCR noise (a scanned form page), not a claim the film makes
            continue
        hits, sk = figures_in_line(ln.text, pop, where, "", ln.cx, ln.cy, t)
        skipped += sk
        for f in hits:
            near = [i for i in items if abs(i.cx - ln.cx) <= near_dx and abs(i.cy - ln.cy) <= near_dy]
            f.ctx = " | ".join(i.text for i in near)
            if f.subject == "?" and f.unit == "count" and re.fullmatch(rf"\s*{_NUM}\s*", ln.text):
                # a standalone count-up numeral ("75") is named by the label directly under it
                below = [i for i in items if 0 < i.y - (ln.y + ln.h) <= 160 and abs(i.cx - ln.cx) <= 320]
                if below:
                    lab = min(below, key=lambda i: i.y).text
                    _, f.subject = classify(f"{ln.text} {lab}", FIG_RE.search(f"{ln.text} {lab}"))
            f.qualified = bool(re.search(QUALIFIERS, f.ctx, re.I))
            if f.subject == "measure":
                # a percent is a MEASURE only if a measure word is near; otherwise unclassified
                if not re.search(MEASURE_WORDS, f.ctx, re.I):
                    f.subject = "?"
            figs.append(f)
    NOISE_LINES += unread
    return figs, skipped


# ---------------------------------------------------------------- voice

def parse_script(path: pathlib.Path) -> list[tuple[str, str]]:
    """[(label, text)] - indented blocks under '## Line N'. Parsed by POSITION: the
    block is the 4-space-indented lines, so '-' bullets in metadata cannot leak in."""
    out, label, buf = [], None, []
    for raw in path.read_text().splitlines():
        if raw.startswith("## "):
            if label and buf:
                out.append((label, " ".join(buf)))
            m = re.match(r"##\s+(Line\s+\d+)", raw)
            label, buf = (m.group(1) if m else raw[3:].strip()), []
        elif raw.startswith("    ") and label:
            buf.append(raw.strip())
    if label and buf:
        out.append((label, " ".join(buf)))
    return out


def voice_figures(blocks: list[tuple[str, str]]) -> tuple[list[Fig], int, int]:
    figs, skipped, nsent = [], 0, 0
    for label, text in blocks:
        for sent in re.split(r"(?<=[.!?])\s+", text):
            nsent += 1
            hits, sk = figures_in_line(sent, "voice", label, sent)
            skipped += sk
            for f in hits:
                if f.subject == "measure" and not re.search(MEASURE_WORDS, sent, re.I):
                    f.subject = "?"
                figs.append(f)
    return figs, skipped, nsent


# ---------------------------------------------------------------- judgement

def judge(screen: list[Fig], voice: list[Fig]) -> list[tuple[str, str, str]]:
    """[(kind, severity, message)] over classified figures. Pure: specimens call this."""
    out = []
    vsubj: dict[str, set] = {}
    for f in voice:
        if f.unit == "count" and f.subject != "?":
            vsubj.setdefault(f.subject, set()).update(f.values - {1.0})
    vsubj = {k: v for k, v in vsubj.items() if v}   # "one application" states no quantity

    for subj, vals in sorted(vsubj.items()):
        shown = [f for f in screen if f.unit == "count" and f.subject == subj]
        for f in shown:
            if f.values <= vals or f.values == {1.0}:
                continue
            if len(vals) == 1:
                out.append(("CONTRADICTION", "FAIL",
                            f"{f.show()} but the voice states {subj} = {sorted(vals)} only. "
                            f"Near it on screen: {f.ctx[:140]!r}"))
            else:
                out.append(("SCREEN-ONLY", "REVIEW",
                            f"{f.show()} - voice states {subj} = {sorted(vals)}; value not among them "
                            "(subject has several voice values, so not a proven contradiction)"))
    for f in screen:
        if f.unit == "count" and f.subject != "?" and f.subject not in vsubj and f.values != {1.0}:
            out.append(("SCREEN-ONLY", "REVIEW", f"{f.show()} - the voice never states any {f.subject} figure"))
    sshown: dict[str, set] = {}
    for f in screen:
        if f.unit == "count" and f.subject != "?":
            sshown.setdefault(f.subject, set()).update(f.values)
    for subj, vals in sorted(vsubj.items()):
        for v in sorted(vals):
            if v not in sshown.get(subj, set()):
                out.append(("VOICE-ONLY", "REVIEW",
                            f"voice states {subj} = {v:g} and no frame shows it (OCR-blind candidate)"))

    # two figures, one measure, no basis words
    inst = [f for f in screen + voice if f.unit == "percent" and f.subject == "measure"]
    byloc: dict[tuple, list[Fig]] = {}
    for f in inst:
        byloc.setdefault((f.pop, f.where), []).append(f)
    unq = {loc: fs for loc, fs in byloc.items() if any(not f.qualified for f in fs)}
    locs = sorted(unq)
    for i, a in enumerate(locs):
        for b in locs[i + 1:]:
            av = {v for f in unq[a] if not f.qualified for v in f.values}
            bv = {v for f in unq[b] if not f.qualified for v in f.values}
            if av and bv and not (av & bv) and a[1] != b[1]:
                fa = [f for f in unq[a] if not f.qualified][0]
                fb = [f for f in unq[b] if not f.qualified][0]
                out.append(("UNDISTINGUISHED", "FAIL",
                            f"two figures for one measure, neither carries a basis word "
                            f"(accuracy / hand-labelled / per-field ...): {fa.show()}  vs  {fb.show()}. "
                            f"Near the first: {fa.ctx[:110]!r}  Near the second: {fb.ctx[:110]!r}"))
    seen, uniq = set(), []
    for r in out:
        if r[2] not in seen:
            seen.add(r[2]); uniq.append(r)
    return uniq


# ---------------------------------------------------------------- gathering

CLIP_JS = """({x, y, w, h}) => {
    const W = innerWidth, H = innerHeight;
    let best = null, bd = 1e9;
    document.querySelectorAll('#mount *').forEach(el => {
        const r = el.getBoundingClientRect();
        const d = Math.abs(r.x-x)+Math.abs(r.y-y)+Math.abs(r.width-w)+Math.abs(r.height-h);
        if (d < bd) { bd = d; best = el; }
    });
    if (!best || bd > 4) return null;
    let c = [0, 0, W, H], op = 1, n = best;
    while (n && n !== document.body) {
        const cs = getComputedStyle(n);
        const v = parseFloat(cs.opacity); if (!isNaN(v)) op *= v;
        if (n !== best && /(hidden|clip|auto|scroll)/.test(cs.overflow + cs.overflowX + cs.overflowY)) {
            const r = n.getBoundingClientRect();
            c = [Math.max(c[0], r.x), Math.max(c[1], r.y), Math.min(c[2], r.right), Math.min(c[3], r.bottom)];
        }
        n = n.parentElement;
    }
    return {clip: c, opacity: op};
}"""

N_SAMPLES = 20


def gather(root: pathlib.Path, samples=N_SAMPLES):
    authored, plates, notes = [], [], []
    counts = dict(a_items=0, a_strings=0, a_nobox=0, p_images=0, p_unread=0, p_words=0, p_off=0)
    ocr_cache: dict[pathlib.Path, list] = {}
    with FilmStage(root) as st:
        for c in st.compositions():
            st.mount(c)
            D = st.duration()
            seen_a, seen_p = set(), set()
            vs = st.visible_strings(40)
            counts["a_strings"] += len(vs)
            box_texts = set()
            for k in range(samples + 1):
                t = D * k / samples
                items = [Item(b.text, b.x, b.y, b.w, b.h) for b in st.text_boxes(t) if b.opacity > 0.05]
                for b in items:
                    box_texts.add(b.text)
                scene_items = list(items)
                for box in st.image_boxes(t):
                    path = plate.resolve_src(box.src, root)
                    if path is None or path.suffix.lower() == ".svg":
                        if (path is None or path.suffix.lower() != ".svg") and box.src not in seen_p:
                            notes.append(f"{c.name}: plate not resolvable off disk: {box.src[-60:]}")
                        seen_p.add(box.src)
                        continue
                    info = st.evaluate(CLIP_JS, {"x": box.x, "y": box.y, "w": box.w, "h": box.h})
                    if info is None or info["opacity"] <= 0.05:
                        continue
                    if path not in ocr_cache:
                        ocr_cache[path] = plate.words(path, 2.0)
                    if not box.natural_w:
                        box.natural_w, box.natural_h = plate.natural_size(path)
                    cx0, cy0, cx1, cy1 = info["clip"]
                    key = (path.name, round(box.x), round(box.y), round(box.w))
                    for w in ocr_cache[path]:
                        s = w.to_stage(box)
                        if s.x >= cx0 - 1 and s.y >= cy0 - 1 and s.x + s.w <= cx1 + 1 and s.y + s.h <= cy1 + 1:
                            scene_items.append(Item(s.text, s.x, s.y, s.w, s.h, w.conf))
                            if (key, s.text, round(s.x / 20), round(s.y / 20)) not in seen_p:
                                seen_p.add((key, s.text, round(s.x / 20), round(s.y / 20)))
                                counts["p_words"] += 1
                        else:
                            counts["p_off"] += 1
                    if key not in seen_p:
                        seen_p.add(key); counts["p_images"] += 1
                counts["a_items"] += len(items)
                fa, _ = figures_in_scene(items, "authored", c.name, t)
                fp_items = scene_items
                fall, _ = figures_in_scene(fp_items, "plate", c.name, t)
                # plate figures = those in the combined scene NOT already an authored hit
                for f in fa:
                    k2 = ("a", c.name, f.raw, f.subject, round(f.cx / 40), round(f.cy / 40))
                    if k2 not in seen_a:
                        seen_a.add(k2); authored.append(f)
                for f in fall:
                    k2 = ("p", c.name, f.raw, f.subject, round(f.cx / 40), round(f.cy / 40))
                    if k2 in seen_p:
                        continue
                    seen_p.add(k2)
                    plates.append(f)
            # strings the box sampling never saw: keep, without geometry
            for s in vs:
                if s not in box_texts:
                    counts["a_nobox"] += 1
                    hits, _ = figures_in_line(s, "authored", c.name, s)
                    authored.extend(hits)
    return authored, plates, counts, notes


def dedupe_plate(authored: list[Fig], plates: list[Fig]) -> list[Fig]:
    """Combined-scene figures that are really authored text are removed, so the
    plate population is the OCR'd text and the authored population is not counted twice."""
    akey = {(f.where, f.raw, f.subject, round(f.cx / 40), round(f.cy / 40)) for f in authored}
    return [f for f in plates if (f.where, f.raw, f.subject, round(f.cx / 40), round(f.cy / 40)) not in akey]


# ---------------------------------------------------------------- reporting

class Verdicts:
    def __init__(self):
        self.rows, self.fail = [], 0

    def verdict(self, kind: str, severity: str, message: str):
        print(f"  {severity:6s} {kind:15s} {message}")
        self.rows.append((kind, severity, message))
        if severity == "FAIL":
            self.fail += 1


# ---------------------------------------------------------------- specimens

def _scene(texts, pop, where):
    items = [Item(t, x, y, 8.0 * len(t), 18.0) for t, x, y in texts]
    return figures_in_scene(items, pop, where, 0.0)[0]


def _voice(text, label="Line 2"):
    return voice_figures([(label, text)])[0]


# (id, expectation, description, screen_scenes, voice_text, kind that must fire/stay quiet)
# Strings are observed output: the 28/8 header from screen-bulk-result.png OCR, the
# 89% and OVERALL column from screen-result.png / screen-scoreboard.png OCR, the voice
# from fin-demo-showcase/SCRIPT.md Lines 2, 10 and 11.
VOICE_L2 = ("And one scanner batch with seven applicants in a single twenty-eight page file.")
SPECIMENS = [
    ("S1", "FIRE", "CONTRADICTION",
     [("f11", [("28 pages - 8 applications", 600, 80)])], VOICE_L2, None),
    ("S2", "QUIET", "CONTRADICTION",       # the nearest look-alike: same claim, "7" vs "seven"
     [("f02", [("28 pages · 7 applicants", 600, 80)])], VOICE_L2, None),
    ("S3", "QUIET", "CONTRADICTION",       # a filename carrying the example number is not a count
     [("f11", [("example-8-bulk-from-scanner.pdf", 100, 80), ("28 pages - 7 applications", 700, 80)])],
     VOICE_L2, None),
    ("S4", "QUIET", "CONTRADICTION",       # "one application per applicant" is a ratio, not a count
     [("f11", [("ONE APPLICATION PER APPLICANT", 100, 400)])],
     "And the twenty-eight page scanner batch comes back as one application per applicant. "
     "A batch with seven applicants.", None),
    ("S5", "FIRE", "UNDISTINGUISHED",
     [("f09", [("OVERALL CONFIDENCE", 1200, 560), ("89%", 1200, 600)]),
      ("f10", [("MODEL MODE RUN OVERALL", 300, 400), ("99%", 800, 460)])], "", None),
    ("S6", "QUIET", "UNDISTINGUISHED",     # same two numbers, the second now says what it measures
     [("f09", [("OVERALL CONFIDENCE", 1200, 560), ("89%", 1200, 600)]),
      ("f10", [("MODEL ACCURACY vs hand-labelled reference", 300, 400), ("99%", 800, 460)])], "", None),
    ("S7", "QUIET", "UNDISTINGUISHED",     # one measure, several rows of one column: not two measures
     [("f10", [("OVERALL", 300, 400), ("99%", 300, 460), ("97%", 300, 500), ("93%", 300, 540)])], "", None),
    ("S8", "FIRE", "CONTRADICTION",        # plant: voice says seven, screen says eight, different frame
     [("f11", [("8 applications", 100, 100)])], "One scanner batch with seven applicants.", None),
    ("S9", "QUIET", "CONTRADICTION",       # a count the voice states in several values is REVIEW, not FAIL
     [("f06", [("24 page resources deleted", 100, 100)])], VOICE_L2 + " Four pages found.", None),
]


def selftest() -> int:
    v = Verdicts()
    bad = 0
    print("SELFTEST - each specimen declares FIRE or QUIET before it runs")
    for sid, expect, kind, scenes, voice_text, _ in SPECIMENS:
        screen = []
        for where, texts in scenes:
            screen += _scene(texts, "plate", where)
        voice = _voice(voice_text) if voice_text else []
        got = [r for r in judge(screen, voice) if r[0] == kind and r[1] == "FAIL"]
        fired = bool(got)
        ok = fired == (expect == "FIRE")
        bad += (not ok)
        print(f"  {'ok ' if ok else 'BAD'} {sid} expect {expect:5s} fired={fired}  {kind}")
    # inert-plant discipline: mutate the FIRE input and prove (a) the mutation changed it
    # and (b) the verdict flips - otherwise 'fires' could be an artefact of the input shape.
    src = "28 pages - 8 applications"
    mutated = src.replace("8 applications", "7 applications")
    assert mutated != src, "inert plant: the replace changed nothing"
    flipped = [r for r in judge(_scene([(mutated, 600, 80)], "plate", "f11"), _voice(VOICE_L2))
               if r[0] == "CONTRADICTION" and r[1] == "FAIL"]
    print(f"  {'ok ' if not flipped else 'BAD'} PLANT S1 with 8->7 must go quiet: fired={bool(flipped)}")
    bad += bool(flipped)
    # notation: the same figure in two notations is ONE value
    a = _voice("seven applicants")[0]; b = _scene([("7 applicants", 0, 0)], "plate", "f")[0]
    same = a.values == b.values and a.subject == b.subject
    print(f"  {'ok ' if same else 'BAD'} NOTATION seven == 7 same value and subject: {same}")
    bad += (not same)
    # the control the real run depends on: the OCR path can read a figure at all
    ok, found, missed = plate.ocr_control(("28 pages - 8 applications", "89%", "99%", "checksum"))
    print(f"  {'ok ' if ok else 'BAD'} OCR control reads figures back: found={found} missed={missed}")
    bad += (not ok)
    print("SELFTEST", "FAIL" if bad else "PASS", f"({bad} bad)")
    return 1 if bad else 0


# ---------------------------------------------------------------- main

@dataclass
class FiguresVerdict:
    fails: list = field(default_factory=list)
    candidates: list = field(default_factory=list)
    warns: list = field(default_factory=list)
    holes: list = field(default_factory=list)
    report: str = ""


def run(project_root: str, verbose: bool = False, script: str = "SCRIPT.md",
        samples: int = N_SAMPLES) -> FiguresVerdict:
    """Gate entry point. fails = settled contradictions; candidates = REVIEW lines;
    holes = what could not be attributed or read (unmeasured, never passed)."""
    import contextlib
    import io

    root = pathlib.Path(project_root).resolve()
    out = FiguresVerdict()
    buf = io.StringIO()
    global NOISE_LINES
    NOISE_LINES = 0
    with contextlib.redirect_stdout(buf):
        ok, found, missed = plate.ocr_control(("28 pages - 8 applications", "89%", "99%", "checksum"))
        st_rc = selftest()
    if not ok:
        out.fails.append(f"[figures] OCR control could not read figures back (missed {missed}); "
                         "every plate reading below would be an unread population, not a clean one")
    if st_rc:
        out.fails.append("[figures] own selftest failed - specimens disagree with the judge; see --selftest")
    sp = root / script
    if not sp.exists():
        out.holes.append(f"[figures] narration script {sp} not found - the voice population is UNREAD, "
                         "so no screen figure could be reconciled against it")
        return out
    blocks = parse_script(sp)
    vfigs, vskip, nsent = voice_figures(blocks)
    authored, plates, counts, notes = gather(root, samples)
    plates = dedupe_plate(authored, plates)
    for name, n, desc in (("authored", len(authored), f"{counts['a_items']} box reads"),
                          ("plate", len(plates), f"{counts['p_images']} plate instances"),
                          ("voice", len(vfigs), f"{len(blocks)} script lines")):
        if n == 0:
            out.fails.append(f"[figures] {name} population yielded zero figures ({desc}); "
                             "zero of zero is not a pass")
    for n in notes:
        out.holes.append(f"[figures] {n} - its text is unread")
    screen = authored + plates
    uncl = [f for f in screen + vfigs if f.subject == "?"]
    out.holes.append(
        f"[figures] {len(uncl)} figures (of {len(screen) + len(vfigs)}) had no counted noun or measure word "
        f"and could not be attributed to a subject, so were not compared; {NOISE_LINES} OCR line reads "
        f"below median confidence {MIN_LINE_CONF:g} were dropped as exhibit noise; OCR under-reads "
        "white-on-green and orange-on-cream, so a clean result means not recognised")
    for kind, sev, msg in judge(screen, vfigs):
        line = f"[figures] {kind}: {msg}"
        (out.fails if sev == "FAIL" else out.candidates).append(line)
    out.report = f"screen {len(screen)} figures (authored {len(authored)}, plate {len(plates)}), voice {len(vfigs)}"
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root", nargs="?")
    ap.add_argument("--script", default="SCRIPT.md")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--samples", type=int, default=N_SAMPLES)
    a = ap.parse_args()
    if a.selftest or not a.root:
        return selftest()
    r = run(a.root, script=a.script, samples=a.samples)
    print(r.report)
    for name in ("fails", "candidates", "warns", "holes"):
        for x in getattr(r, name):
            print(f"{name[:-1].upper() if name != 'fails' else 'FAIL':9s} {x}")
    print(f"RESULT {'FAIL' if r.fails else 'PASS'} ({len(r.fails)} fails, {len(r.candidates)} candidates, {len(r.holes)} holes)")
    return 1 if r.fails else 0


if __name__ == "__main__":
    sys.exit(main())
