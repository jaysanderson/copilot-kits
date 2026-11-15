#!/usr/bin/env python3
"""Legibility over authored type UNION plate text, reported BY CONTENT CLASS.

WHAT IT MEASURES. For every composition, at sampled points of its own paused
timeline, the glyph height on a 390 CSS px phone of (a) every visible authored
text leaf and (b) every word OCR reads inside a captured plate that is actually
hit-testable on screen (not clipped away, not under something). Each item is
classed CLAIM / QUALIFICATION / EVIDENCE and the verdict is per class, never an
average, because the failure this exists for is an ASYMMETRY: headlines legible
while evidence and qualifications are not (University 9 Oct, Kuraray 17 Oct,
Fin-demo 16 Oct - every unreadable item was text inside a plate).

POPULATION (printed on every run): compositions, sample points, plates seen,
plates declared to be READ, plate words before and after the noise filter,
authored leaves, items per class. Zero of zero is not a pass: a film with no
measurable item exits 2, and a film whose plates are all undeclared reports
them as UNMEASURED by name and exits 2 - it does not pass them.

THE DECLARATION. Many plates are decorative thumbnails (0.66x) where small text
is correct. The set a viewer is asked to READ comes from an optional JSON file,
`<project>/plates-to-read.json` or `--declare PATH`:
    {"09-the-output.html": ["screen-result.png"], "*": ["form-page1.png"]}
keys are composition file names or "*", values are plate file basenames. Plates
not declared are listed as UNMEASURED; they are never silently passed.

GLYPH UNIT. Floor is READ_FLOOR_PHONE = 11.0 CSS px EM on a phone, the same
floor tools_typescale.py derives (smallest state marker a person reads). OCR
gives a word BOX height, not an em, so a plate word is converted at
BBOX_PER_EM = 0.75 (ascender-to-baseline of a Latin sans; descenders make real
boxes taller, which flatters the plate side slightly). Both numbers are printed
beside every figure. Each unique item is judged at its BEST sampled size, so an
entrance animation caught mid-scale is not accused; an item failing here never
reaches the floor at any sampled moment.

DECLARED BLIND CLASSES (inherited from plate.py plus this check's own):
* Tesseract under-reads white-on-green and orange-on-cream, and '4 / 4' fails
  its own control. A pass means NOTHING WAS RECOGNISED, never nothing is
  present, and a two-item gap between two classes is OCR noise, not a finding.
* Content class is LEXICAL (keywords, digits, brackets). It cannot read intent.
  Authored text is CLAIM by default; plate text is EVIDENCE by default (it is
  the recorded product). A plate headline is therefore classed evidence.
* Plate opacity and CSS filters/blur are not read; a dimmed plate is measured
  as if bright. Clipping is modelled only by hit-testing, so a word under a
  semi-transparent panel counts as visible.
* Text inside SVG <text> and canvas is not an authored leaf here.
* Samples are every ~1s; a beat shorter than that can fall between samples.
"""
from __future__ import annotations

import argparse
import functools
import json
import pathlib
import re
import sys
from dataclasses import dataclass, field

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from filmkit import plate  # noqa: E402
from filmkit.stage import FilmStage  # noqa: E402

READ_FLOOR_PHONE = 11.0
BBOX_PER_EM = 0.75
PHONE = 390.0
FRAME_W = 1920
CLASS_FAIL_SHARE = 0.20     # a class fails when more than this share of its items is below floor
CLASS_MIN_N = 3             # ... and it has at least this many items
CLASSES = ("claim", "qualification", "evidence")

QUAL_RE = re.compile(
    r"\b(not|no|only|may|might|approx\w*|synthetic|disclos\w*|note|notes|caveat|except|unless|"
    r"limit\w*|sample|illustrative|estimate\w*|doubtful|flagged|review|misread|miswrit\w*|"
    r"checksum|invalid|fail\w*)\b", re.I)
EVID_RE = re.compile(r"\d|%|\[\d+\]|[|:]")
WORD_RE = re.compile(r"[A-Za-z]{2,}|\d+(?:\.\d+)?%|\[\d+\]|\d{2,}")


# -- reporting: ONE function prints and registers every verdict --------------

class Reporter:
    def __init__(self):
        self.rows: list[tuple[str, str, str]] = []

    def check(self, name: str, ok: bool, detail: str = "", kind: str = "FAIL") -> bool:
        """kind is what a failed check means: FAIL (defect) or UNMEASURED (hole)."""
        verdict = "PASS" if ok else kind
        self.rows.append((verdict, name, detail))
        print(f"{verdict:10s} {name}" + (f"  - {detail}" if detail else ""))
        return ok

    def exit_code(self) -> int:
        if any(v == "FAIL" for v, _, _ in self.rows):
            return 1
        if any(v == "UNMEASURED" for v, _, _ in self.rows):
            return 2
        return 0


# -- shared helpers (occlusion.py imports these) ------------------------------

def sample_times(duration: float, step: float = 1.0) -> list[float]:
    n = max(3, int(duration / step))
    ts = [duration * i / n for i in range(n)] + [max(0.0, duration - 0.05)]
    return [round(t, 3) for t in ts]


def is_word(text: str) -> bool:
    return bool(WORD_RE.search(text))


def classify(text: str, authored: bool) -> str:
    if QUAL_RE.search(text):
        return "qualification"
    if authored:
        letters = len(re.findall(r"[A-Za-z]", text))
        digits = len(re.findall(r"\d", text))
        return "evidence" if digits and digits >= letters else "claim"
    return "evidence"


def load_declaration(project: pathlib.Path, explicit: str | None):
    p = pathlib.Path(explicit) if explicit else project / "plates-to-read.json"
    if not p.exists():
        return None, p
    return json.loads(p.read_text()), p


def declared_for(decl, comp_name: str) -> set[str]:
    if decl is None:
        return set()
    return set(decl.get(comp_name, [])) | set(decl.get("*", []))


def memoise_ocr() -> None:
    """OCR each distinct image once per process. plate.plate_words calls the
    module-level words() per box per sample; the geometry changes, the pixels do
    not. Idempotent. This wraps the primitive, it does not reimplement it."""
    if not getattr(plate.words, "_filmkit_memo", False):
        cached = functools.lru_cache(maxsize=None)(plate.words)
        cached._filmkit_memo = True
        plate.words = cached
        # plate.resolve_src hands an .svg to PIL, which raises and kills the whole
        # sweep (found on fin-demo: logo-progress-arag.svg). A vector file is not a
        # captured plate and tesseract cannot read it; route it to "unresolved" so it
        # is NAMED as unmeasured instead of crashing. Primitive bug, reported upstream.
        orig = plate.resolve_src

        def resolve_raster(src, project_root):
            if src.split("?")[0].lower().endswith((".svg", ".gif", ".webm", ".mp4")):
                return None
            return orig(src, project_root)
        plate.resolve_src = resolve_raster


def with_pointer_events_js(body: str) -> str:
    """Wrap a JS body so hit-testing ignores authored pointer-events:none."""
    return """(arg) => {
        const st = document.createElement('style');
        st.textContent = '#mount *{pointer-events:auto !important}';
        document.head.appendChild(st);
        try { %s } finally { st.remove(); }
    }""" % body


# Per-word hit test. For each plate box (matched in the DOM by rect) and each
# word, a 9 x 3 grid of points is tested with elementsFromPoint: the plate counts as
# visible at a point when it is in the stack at all (overflow clipping removes it
# from hit testing), and a point is covered when an opaque painter or a text
# glyph run sits ABOVE it in the stack.
HIT_JS = with_pointer_events_js(r"""
    const near = (r, b) => Math.abs(r.x-b.x)<1.5 && Math.abs(r.y-b.y)<1.5 &&
                           Math.abs(r.width-b.w)<1.5 && Math.abs(r.height-b.h)<1.5;
    const alpha = (c) => { const m = c.match(/rgba?\(([^)]+)\)/); if (!m) return 0;
        const p = m[1].split(',').map(parseFloat); return p.length > 3 ? p[3] : 1; };
    const cumOp = (el) => { let o = 1, n = el;
        while (n && n !== document.body) { const v = parseFloat(getComputedStyle(n).opacity);
            if (!isNaN(v)) o *= v; n = n.parentElement; } return o; };
    const sel = (el) => el.id ? '#'+el.id :
        el.tagName.toLowerCase() + ((el.className||'').toString().trim().split(/\s+/)[0] ?
        '.'+(el.className||'').toString().trim().split(/\s+/)[0] : '');
    const inGlyphs = (el, x, y) => {
        if (el.children.length || !(el.textContent||'').trim()) return false;
        const r = document.createRange(); r.selectNodeContents(el);
        return [...r.getClientRects()].some(q => x>=q.left && x<=q.right && y>=q.top && y<=q.bottom);
    };
    const carriesPlate = (el) => !!el.querySelector('img') ||
        [el, ...el.querySelectorAll('*')].some(d => getComputedStyle(d).backgroundImage.includes('url('));
    const painter = (el, x, y) => {
        if (cumOp(el) < 0.5) return null;
        // a card that CARRIES another plate is plate stacked on plate (a fan of pages),
        // a different class from an authored element over a plate; it is skipped here
        if (el.tagName !== 'IMG' && carriesPlate(el)) return 'carrier';
        const cs = getComputedStyle(el);
        if (alpha(cs.backgroundColor) >= 0.5) {
            const r = el.getBoundingClientRect();
            if (r.width*r.height < 0.7*innerWidth*innerHeight) return 'panel';
        }
        if (inGlyphs(el, x, y)) return 'text';
        return null;
    };
    const out = [];
    for (const b of arg.boxes) {
        const rows = [];
        for (const w of b.words) {
            if (w.x+w.w < 0 || w.y+w.h < 0 || w.x > innerWidth || w.y > innerHeight) {
                rows.push({i: w.i, points: 27, visible: 0, covered: 0, occluders: {}}); continue; }
            const pts = []; for (let iy = 0; iy < 3; iy++) for (let ix = 0; ix < 9; ix++)
                pts.push([w.x + w.w*(ix+.5)/9, w.y + w.h*(iy+.5)/3]);
            let vis = 0, cov = 0; const occ = {};
            for (const [x,y] of pts) {
                if (x<0||y<0||x>=innerWidth||y>=innerHeight) continue;
                const stack = document.elementsFromPoint(x, y);
                const idx = stack.findIndex(e => (e.tagName==='IMG' || getComputedStyle(e).backgroundImage.includes('url(')) &&
                                                 near(e.getBoundingClientRect(), b));
                if (idx < 0) continue;
                vis++;
                for (let i = 0; i < idx; i++) {
                    const k = painter(stack[i], x, y);
                    if (k === 'carrier') continue;
                    if (k) { cov++; const s = sel(stack[i]); occ[s] = k; break; }
                }
            }
            rows.push({i: w.i, points: pts.length, visible: vis, covered: cov, occluders: occ});
        }
        out.push(rows);
    }
    return out;
""")


def plate_hits(stage: FilmStage, plates):
    """plates: [(ImageBox, [Word in stage coords])] -> per box, per word hit rows."""
    boxes = []
    for box, ws in plates:
        boxes.append({
            "x": box.x, "y": box.y, "w": box.w, "h": box.h,
            "words": [{"i": i, "x": w.x, "y": w.y, "w": w.w, "h": w.h} for i, w in enumerate(ws)],
        })
    return stage.evaluate(HIT_JS, {"boxes": boxes})


# -- the pure decision logic (what specimens exercise) ------------------------

@dataclass
class Item:
    comp: str
    source: str        # authored | plate
    key: str
    text: str
    cls: str
    stage_em: float    # best em-equivalent in 1920-wide STAGE px across samples (medium-independent)
    where: str


def em_at(i: Item, css_width: float) -> float:
    return i.stage_em * css_width / FRAME_W


def legibility(items: list[Item], floor: float = READ_FLOOR_PHONE, css_width: float = PHONE):
    """Per class: n, n_below, share, smallest. Verdict per class, not overall.
    The delivery medium is css_width: the CSS width the 1920 frame is shown at."""
    out = {}
    for c in CLASSES:
        grp = [i for i in items if i.cls == c]
        below = [i for i in grp if em_at(i, css_width) < floor]
        share = len(below) / len(grp) if grp else 0.0
        out[c] = {
            "n": len(grp), "below": len(below), "share": share,
            "smallest": min((em_at(i, css_width) for i in grp), default=None),
            "fails": len(grp) >= CLASS_MIN_N and share > CLASS_FAIL_SHARE,
            "examples": [f"{i.text[:28]!r}@{em_at(i, css_width):.1f}" for i in sorted(below, key=lambda i: i.stage_em)[:4]],
        }
    return out


# -- the project run -----------------------------------------------------------

def _run(project: str, declare: str | None, step: float, R: Reporter, only=None, dump=None,
         floor: float = READ_FLOOR_PHONE, widths=(390.0, 1280.0)) -> None:
    root = pathlib.Path(project).resolve()
    memoise_ocr()
    ok, found, missed = plate.ocr_control()
    R.check("OCR positive control (renders strings, reads them back)", ok,
            f"read {found}, missed {missed}", kind="UNMEASURED")
    decl, decl_path = load_declaration(root, declare)
    print(f"declaration: {decl_path if decl is not None else 'NONE (' + str(decl_path) + ' absent)'}")

    items: dict[tuple, Item] = {}
    n_comp = n_samples = n_authored_seen = n_plate_seen = 0
    words_raw = words_kept = 0
    plates_seen: dict[str, set[str]] = {}
    plates_read: dict[str, set[str]] = {}
    unresolved: set[str] = set()
    with FilmStage(root) as st:
        for comp in st.compositions():
            if only and comp.name not in only:
                continue
            st.mount(comp)
            n_comp += 1
            D = st.duration()
            want = declared_for(decl, comp.name)
            for t in sample_times(D, step):
                n_samples += 1
                for tb in st.text_boxes(t):
                    if tb.opacity < 0.5 or not tb.text.strip():
                        continue
                    n_authored_seen += 1
                    em = tb.rendered_font_size
                    key = ("authored", comp.name, tb.selector, tb.text)
                    cls = classify(tb.text, True)
                    prev = items.get(key)
                    if prev is None or em > prev.stage_em:
                        items[key] = Item(comp.name, "authored", f"{tb.selector}", tb.text, cls, em,
                                          f"{comp.name} {tb.selector} t={t}")
                pw, unres = plate.plate_words(st, root, t)
                for u in unres:
                    unresolved.add(f"{comp.name}:{pathlib.Path(u.split('?')[0]).name}")
                for box, ws in pw:
                    name = pathlib.Path(box.src.split("?")[0]).name
                    plates_seen.setdefault(comp.name, set()).add(name)
                    if name not in want:
                        continue
                    plates_read.setdefault(comp.name, set()).add(name)
                    n_plate_seen += 1
                hits = plate_hits(st, [(b, ws) for b, ws in pw if pathlib.Path(b.src.split("?")[0]).name in want])
                hi = 0
                for box, ws in pw:
                    name = pathlib.Path(box.src.split("?")[0]).name
                    if name not in want:
                        continue
                    for w, h in zip(ws, hits[hi]):
                        words_raw += 1
                        if not is_word(w.text):
                            continue
                        words_kept += 1
                        if h["visible"] / h["points"] < 0.5:
                            continue
                        em = w.h / BBOX_PER_EM
                        key = ("plate", comp.name, name, h["i"])
                        prev = items.get(key)
                        if prev is None or em > prev.stage_em:
                            items[key] = Item(comp.name, "plate", f"{name}#{h['i']}", w.text,
                                              classify(w.text, False), em,
                                              f"{comp.name} {name} t={t}")
                    hi += 1

    all_plates = {(c, p) for c, s in plates_seen.items() for p in s}
    read_plates = {(c, p) for c, s in plates_read.items() for p in s}
    unmeasured = sorted(all_plates - read_plates)
    ilist = list(items.values())
    print("\nPOPULATION")
    print(f"  compositions {n_comp}   sample points {n_samples}   floor {floor} em px "
          f"(bbox/em {BBOX_PER_EM})")
    print(f"  plates seen {len(all_plates)}   declared-to-read and measured {len(read_plates)}   "
          f"UNMEASURED {len(unmeasured)}")
    print(f"  plate words OCR'd {words_raw}   kept as words {words_kept}   "
          f"discarded as noise {words_raw - words_kept}")
    print(f"  authored leaf sightings {n_authored_seen}   unique items {len(ilist)} "
          f"(authored {sum(i.source == 'authored' for i in ilist)}, plate {sum(i.source == 'plate' for i in ilist)})")
    if unresolved:
        R.check("every on-screen image resolves to a raster file on disk", False,
                "UNRESOLVED (vector or missing, never OCR'd): " + ", ".join(sorted(unresolved)),
                kind="UNMEASURED")
    R.check("population non-empty", len(ilist) > 0, f"{len(ilist)} items", kind="UNMEASURED")
    if unmeasured:
        by_comp: dict[str, list[str]] = {}
        for c, p in unmeasured:
            by_comp.setdefault(c, []).append(p)
        R.check("every plate the film shows is declared to be read or not",
                False, "UNMEASURED plates (not declared to be read) - " +
                "; ".join(f"{c}: {', '.join(v)}" for c, v in by_comp.items()),
                kind="UNMEASURED")

    print(f"\nFLOOR is {floor} CSS px em at EVERY medium (a glyph under that is unreadable on any screen);"
          f" the medium is the CSS width the 1920 frame is shown at: {', '.join(f'{w:g}px (x{w/FRAME_W:.3f})' for w in widths)}")
    for cw in widths:
        for source in ("authored", "plate", "both"):
            grp = [i for i in ilist if source == "both" or i.source == source]
            res = legibility(grp, floor, cw)
            print(f"\nLEGIBILITY BY CLASS - {source} @ {cw:g}px wide (best sampled size, em px, floor {floor})")
            for c in CLASSES:
                r = res[c]
                sm = "n/a" if r["smallest"] is None else f"{r['smallest']:.1f}"
                sizes = sorted(em_at(i, cw) for i in grp if i.cls == c)
                med = f"{sizes[len(sizes)//2]:.1f}" if sizes else "n/a"
                big = f"{sizes[-1]:.1f}" if sizes else "n/a"
                print(f"  {c:14s} n={r['n']:4d} below={r['below']:4d} ({r['share']*100:5.1f}%) smallest={sm} median={med} largest={big}"
                      f"  {' '.join(r['examples'])}")
                if source == "both":
                    R.check(f"{c} legible at {cw:g}px wide", not r["fails"],
                            f"{r['below']}/{r['n']} below {floor}px em, smallest {sm}, median {med}")
    both = legibility(ilist, floor, widths[0])
    if dump:
        pathlib.Path(dump).write_text(json.dumps([i.__dict__ for i in ilist], indent=1))
    shares = {c: both[c]["share"] for c in CLASSES if both[c]["n"] >= CLASS_MIN_N}
    if len(shares) > 1:
        hi_c = max(shares, key=shares.get); lo_c = min(shares, key=shares.get)
        print(f"\nASYMMETRY (descriptive, not a verdict): worst class {hi_c} {shares[hi_c]*100:.0f}% below floor, "
              f"best {lo_c} {shares[lo_c]*100:.0f}%. A gap smaller than ~2 items is OCR noise.")



@dataclass
class Verdict:
    fails: list = field(default_factory=list)
    candidates: list = field(default_factory=list)
    warns: list = field(default_factory=list)
    holes: list = field(default_factory=list)


def to_verdict(R: Reporter, tag: str) -> Verdict:
    """FAIL rows are fails; UNMEASURED rows are holes (never passed, never failed)."""
    v = Verdict()
    for kind, name, detail in R.rows:
        msg = f"{tag}: {name}" + (f" - {detail}" if detail else "")
        if kind == "FAIL":
            v.fails.append(msg)
        elif kind == "UNMEASURED":
            v.holes.append(msg)
    return v


def run(project_root: str, verbose: bool = False, declare: str | None = None,
        step: float = 1.0, only=None, dump=None, floor: float = READ_FLOOR_PHONE,
        widths=(390.0, 1280.0)) -> Verdict:
    """Gate entry point. Selftest is not run here; use --selftest."""
    import contextlib, io
    R = Reporter()
    sink = None if verbose else io.StringIO()
    with (contextlib.redirect_stdout(sink) if sink else contextlib.nullcontext()):
        _run(project_root, declare, step, R, only, dump, floor, widths)
    return to_verdict(R, "platetext")


# -- specimens ---------------------------------------------------------------
# Every specimen is a shape OBSERVED in the fin-demo-showcase run of 19 Oct 2026
# (figures are this check's own printed output on 09-the-output.html, or the
# film's typescale.json for authored type) and declares FIRE or QUIET.

def _it(cls, em, text, src="plate"):
    return Item("09-the-output.html", src, text, text, cls, em * FRAME_W / PHONE, "specimen")

SPECIMENS = [
    ("umv-09-checksum-note-in-plate", "FIRE",
     [_it("qualification", em, t) for t, em in
      (("notes", 3.3), ("checksum", 3.5), ("fails:", 3.6), ("misread", 3.5), ("miswritten.", 3.5))],
     "viewer item 10 text: the validation note's own qualification words, 3.3-3.6 phone px, never near 11"),
    ("umv-09-field-table-evidence-in-plate", "FIRE",
     [_it("evidence", em, t) for t, em in
      (("89%", 5.7), ("main_member", 3.3), ("90%", 3.5), ("GP1234", 3.5), ("85%", 3.5), ("employee_no", 4.0))],
     "the field table and confidence column the film is about: 3.3-5.7 phone px"),
    ("umv-01-large-headlines", "QUIET",
     [_it("claim", 80 * PHONE / FRAME_W, t, "authored") for t in
      ("Handwritten forms in.", "Structured data", "out.")],
     "01-powered-by headline lines (80px authored, typescale.json): 16.2 phone px clears 11"),
    ("umv-02-undeclared-thumbnails-empty-population", "QUIET",
     [],
     "02-sample-pack page thumbnails undeclared: no plate item enters the verdict (the run names them UNMEASURED)"),
]

WORD_SPECIMENS = [
    # text, is_word expected, observed where
    ("\u2014", False, "raw OCR noise reported by the lead"),
    ("C]", False, "raw OCR noise reported by the lead"),
    ("4", False, "single glyph from a counter, no word"),
    ("89%", True, "09 confidence figure"),
    ("sa_id_checksum", True, "09 validation note key"),
    ("[1]", True, "citation marker class (Kuraray) - the smallest object in that film"),
]


def selftest(R: Reporter) -> None:
    print("\nSPECIMENS")
    results = []
    for sid, expect, items, why in SPECIMENS:
        fired = any(r["fails"] for r in legibility(items).values())
        results.append((fired, expect == "FIRE"))
        R.check(f"specimen {sid} expects {expect}", fired == (expect == "FIRE"), why)
    for text, expect, why in WORD_SPECIMENS:
        got = is_word(text)
        results.append((got, expect))
        R.check(f"word specimen {text!r} is_word={expect}", got == expect, why)
    # The reporter must be able to fail: plant a specimen whose expectation is
    # deliberately wrong in a THROWAWAY reporter, silence it, and require exit 1.
    probe = Reporter()
    import contextlib, io
    with contextlib.redirect_stdout(io.StringIO()):
        probe.check("planted wrong expectation",
                    any(r["fails"] for r in legibility(SPECIMENS[2][2]).values()) == True)
    R.check("a wrong expectation makes the reporter exit non-zero (planted)",
            probe.exit_code() == 1, f"throwaway reporter exit {probe.exit_code()}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project", nargs="?")
    ap.add_argument("--declare")
    ap.add_argument("--step", type=float, default=1.0)
    ap.add_argument("--only", nargs="*", help="composition file names to run")
    ap.add_argument("--dump", help="write the unique items as JSON")
    ap.add_argument("--floor", type=float, default=READ_FLOOR_PHONE)
    ap.add_argument("--widths", type=float, nargs="+", default=[390.0, 1280.0], help="delivery CSS widths")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    R = Reporter()
    selftest(R)
    if a.project and not a.selftest:
        _run(a.project, a.declare, a.step, R, a.only, a.dump, a.floor, tuple(a.widths))
    code = R.exit_code()
    print(f"\nEXIT {code}  (0 pass, 1 FAIL, 2 UNMEASURED/incomplete)")
    return code


if __name__ == "__main__":
    sys.exit(main())
