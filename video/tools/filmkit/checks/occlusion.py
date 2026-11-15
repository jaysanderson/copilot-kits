#!/usr/bin/env python3
"""An authored element drawn over a plate's own content, and authored over authored.

WHAT IT MEASURES. At sampled points of each composition's paused timeline:

1. PLATE OCCLUSION. Every word OCR reads in a captured plate (plate.plate_words,
   read from the SOURCE IMAGE so words already hidden are still found) is
   hit-tested on a 9 x 3 grid of points with elementsFromPoint. A word is OCCLUDED when the
   plate is visible at it and an opaque authored panel (background alpha >= 0.5,
   cumulative opacity >= 0.5, under 70% of the frame) or an authored glyph run
   sits above the plate in paint order at >= 20% of its visible points (a word cut off is a defect, not only a word hidden). This is
   the fin-demo callout pills sitting over the validation note (viewer item 10).
2. AUTHORED OVER AUTHORED. Two authored text leaves whose glyph boxes overlap by
   >= 20% of the smaller one (neither inside the other's subtree), and an authored
   text leaf whose centre is covered by a NON-ancestor opaque panel above it.

It is arithmetic after layout: rects come from getBoundingClientRect and Range
client rects at device scale 1, ordering from the browser's own hit test with
`pointer-events:auto` forced so an authored pointer-events:none cannot hide a
cover. No render is needed.

POPULATION (printed): compositions, sample points, plates, plate words read,
words kept after the noise filter, words hit-tested visible, authored text
leaves, authored panels, text-pair candidates. Zero of zero is not a pass: a film
with no plate words AND no authored leaves exits 2.

DECLARED BLIND CLASSES (plate.py's are inherited: tesseract under-reads
white-on-green and orange-on-cream, '4 / 4' fails its own control, and a pass
means NOTHING WAS RECOGNISED, not nothing is present):
* Words tesseract cannot read cannot be reported as covered. A cover over text
  OCR cannot see is invisible here; the pill over the validation note is found
  only because that text is dark-on-light and reads.
* Panels with background alpha under 0.5, gradients, box-shadows, SVG shapes,
  canvas and CSS filters are not painters. A translucent wash over a word is not
  reported (it is dimming, not occluding - and also not measured).
* A card that CARRIES another plate (a fan of page thumbnails) is plate stacked
  on plate, skipped as a painter; stacked thumbnails hiding each other are not
  reported by this check at all.
* A rounded pill is treated at its glyph/panel hit point, never by area, so a
  word touching only a pill's transparent corner is not reported.
* Plate opacity is not read; a plate faded to 0.3 is measured as bright.
* A panel that intentionally frames a plate region (a cropping window) is an
  ANCESTOR of the plate and is excluded by tree position, not by judgement.
* Cross-dissolve cover from a neighbouring shot is out of scope (stage.py).
* Samples are every ~1s; a beat shorter than that can fall between samples.
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import pathlib
import sys
from dataclasses import dataclass

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from filmkit import plate  # noqa: E402
from filmkit.checks.platetext import (  # noqa: E402
    Reporter, declared_for, to_verdict, is_word, load_declaration, memoise_ocr, plate_hits,
    sample_times, with_pointer_events_js,
)
from filmkit.stage import FilmStage  # noqa: E402

WORD_COVER_FRAC = 0.20       # share of a word's visible points that must be covered
WORD_VISIBLE_FRAC = 0.50     # plate must be hit-testable at this share of the word's points
TEXT_OVERLAP_FRAC = 0.20     # intersection over the SMALLER text box


# -- decision logic (pure; what specimens exercise) ---------------------------

@dataclass
class WordHit:
    text: str
    points: int
    visible: int
    covered: int
    occluders: dict


def occluded(h: WordHit) -> bool:
    if h.points == 0 or h.visible / h.points < WORD_VISIBLE_FRAC:
        return False
    return h.covered / h.visible >= WORD_COVER_FRAC


def rect_overlap_small(a, b) -> float:
    """Intersection area over the SMALLER rect; a, b = (x, y, w, h)."""
    ix = max(0.0, min(a[0] + a[2], b[0] + b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1]))
    small = min(a[2] * a[3], b[2] * b[3])
    return (ix * iy) / small if small > 0 else 0.0


def text_pair_defects(texts, panels, above):
    """texts/panels: dicts id, sel, rect, ancestors(set of ids). above(p, t) -> bool
    answers 'is panel p above text t at t's centre' from the browser stack."""
    out = []
    for i, a in enumerate(texts):
        for b in texts[i + 1:]:
            if a["id"] in b["ancestors"] or b["id"] in a["ancestors"]:
                continue
            f = rect_overlap_small(a["rect"], b["rect"])
            if f >= TEXT_OVERLAP_FRAC:
                out.append(("text-over-text", a["sel"], b["sel"], f))
        for p in panels:
            if p["id"] in a["ancestors"] or a["id"] in p["ancestors"] or p["id"] == a["id"]:
                continue
            if rect_overlap_small(a["rect"], p["rect"]) > 0 and above(p["id"], a["id"]):
                out.append(("panel-over-text", p["sel"], a["sel"], rect_overlap_small(a["rect"], p["rect"])))
    return out


# -- browser readers ------------------------------------------------------------

COLLECT_JS = with_pointer_events_js(r"""
    const alpha = (c) => { const m = c.match(/rgba?\(([^)]+)\)/); if (!m) return 0;
        const p = m[1].split(',').map(parseFloat); return p.length > 3 ? p[3] : 1; };
    const cumOp = (el) => { let o = 1, n = el;
        while (n && n !== document.body) { const v = parseFloat(getComputedStyle(n).opacity);
            if (!isNaN(v)) o *= v; n = n.parentElement; } return o; };
    const sel = (el) => el.id ? '#'+el.id :
        el.tagName.toLowerCase() + ((el.className||'').toString().trim().split(/\s+/)[0] ?
        '.'+(el.className||'').toString().trim().split(/\s+/)[0] : '');
    const root = document.getElementById('mount');
    const FW = innerWidth * innerHeight;
    const texts = [], panels = [];
    let n = 0;
    const ancestors = (el) => { const a = []; let p = el.parentElement;
        while (p && p !== root) { if (p.__fk !== undefined) a.push(p.__fk); p = p.parentElement; } return a; };
    // assign ids to every element first so ancestor lists are complete
    root.querySelectorAll('*').forEach(el => { el.__fk = n++; });
    root.querySelectorAll('*').forEach(el => {
        const cs = getComputedStyle(el);
        if (cs.visibility === 'hidden' || cs.display === 'none' || cumOp(el) < 0.5) return;
        const r = el.getBoundingClientRect();
        if (r.width <= 0 || r.height <= 0) return;
        const txt = el.children.length ? '' : (el.textContent||'').trim();
        if (el.tagName !== 'STYLE' && el.tagName !== 'SCRIPT' && txt) {
            const g = document.createRange(); g.selectNodeContents(el);
            const q = [...g.getClientRects()];
            if (q.length) {
                const x0 = Math.min(...q.map(c=>c.left)), y0 = Math.min(...q.map(c=>c.top));
                const x1 = Math.max(...q.map(c=>c.right)), y1 = Math.max(...q.map(c=>c.bottom));
                texts.push({id: el.__fk, sel: sel(el), text: txt.slice(0,40), rect: [x0,y0,x1-x0,y1-y0],
                            ancestors: ancestors(el)});
            }
        }
        if (alpha(cs.backgroundColor) >= 0.5 && r.width*r.height < 0.7*FW && el.tagName !== 'IMG')
            panels.push({id: el.__fk, sel: sel(el), rect: [r.x,r.y,r.width,r.height], ancestors: ancestors(el)});
    });
    // paint order: for each panel/text pair that overlaps, is the panel above the text at the text's centre?
    const above = {};
    for (const t of texts) for (const p of panels) {
        if (t.id === p.id || t.ancestors.includes(p.id) || p.ancestors.includes(t.id)) continue;
        const ix = Math.max(0, Math.min(t.rect[0]+t.rect[2], p.rect[0]+p.rect[2]) - Math.max(t.rect[0], p.rect[0]));
        const iy = Math.max(0, Math.min(t.rect[1]+t.rect[3], p.rect[1]+p.rect[3]) - Math.max(t.rect[1], p.rect[1]));
        if (ix*iy <= 0) continue;
        const cx = Math.max(t.rect[0], p.rect[0]) + ix/2, cy = Math.max(t.rect[1], p.rect[1]) + iy/2;
        const st = document.elementsFromPoint(cx, cy).map(e => e.__fk);
        const ip = st.indexOf(p.id), it = st.indexOf(t.id);
        above[p.id + ':' + t.id] = ip >= 0 && (it < 0 || ip < it);
    }
    return {texts, panels, above};
""")


def collect(stage: FilmStage):
    return stage.evaluate(COLLECT_JS, None)


# -- project run -----------------------------------------------------------------

def _run(project: str, step: float, R: Reporter, only=None, dump=None, declare=None) -> None:
    root = pathlib.Path(project).resolve()
    decl, decl_path = load_declaration(root, declare)
    print(f"declaration: {decl_path if decl is not None else 'NONE - STRICT: every plate is treated as one to be read'}")
    info_defects: dict[tuple, dict] = {}
    memoise_ocr()
    ok, found, missed = plate.ocr_control()
    R.check("OCR positive control (renders strings, reads them back)", ok,
            f"read {found}, missed {missed}", kind="UNMEASURED")
    n_comp = n_samples = words_raw = words_kept = words_visible = 0
    n_texts = n_panels = n_pairs = 0
    plate_set: set[tuple[str, str]] = set()
    unresolved: set[str] = set()
    plate_defects: dict[tuple, dict] = {}
    auth_defects: dict[tuple, dict] = {}
    with FilmStage(root) as st:
        for comp in st.compositions():
            if only and comp.name not in only:
                continue
            st.mount(comp)
            n_comp += 1
            for t in sample_times(st.duration(), step):
                n_samples += 1
                pw, unres = plate.plate_words(st, root, t)
                unresolved.update(f"{comp.name}:{pathlib.Path(u.split('?')[0]).name}" for u in unres)
                hits = plate_hits(st, pw)
                for (box, ws), rows in zip(pw, hits):
                    name = pathlib.Path(box.src.split("?")[0]).name
                    plate_set.add((comp.name, name))
                    strict = decl is None or name in declared_for(decl, comp.name)
                    for w, h in zip(ws, rows):
                        words_raw += 1
                        if not is_word(w.text):
                            continue
                        words_kept += 1
                        wh = WordHit(w.text, h["points"], h["visible"], h["covered"], h["occluders"])
                        if wh.points and wh.visible / wh.points >= WORD_VISIBLE_FRAC:
                            words_visible += 1
                        if occluded(wh):
                            for occ, kind in wh.occluders.items():
                                k = (comp.name, name, occ)
                                bucket = plate_defects if strict else info_defects
                                d = bucket.setdefault(k, {"kind": kind, "words": {}, "first_t": t})
                                d["words"].setdefault(h["i"], f"{w.text} [{wh.covered}/{wh.visible} pts]")
                data = collect(st)
                n_texts += len(data["texts"]); n_panels += len(data["panels"])
                n_pairs += len(data["texts"]) * (len(data["texts"]) - 1) // 2
                above = lambda p, tx, a=data["above"]: a.get(f"{p}:{tx}", False)
                for kind, a_sel, b_sel, f in text_pair_defects(data["texts"], data["panels"], above):
                    k = (comp.name, kind, a_sel, b_sel)
                    d = auth_defects.setdefault(k, {"frac": f, "first_t": t})
                    d["frac"] = max(d["frac"], f)

    # LIVE PLANTED CONTROL: fin-demo has zero authored-over-authored hits, so that half of
    # the check has no real positive. Mount a real composition, drag one real text leaf
    # onto another in the live DOM, and require the same collect() path to find it.
    def plant(st2, c0):
        st2.mount(c0)
        for frac in (0.95, 0.6, 0.3):
            st2.seek(st2.duration() * frac)
            before = collect(st2)
            if len(before["texts"]) >= 2:
                break
        if len(before["texts"]) < 2:
            return None
        ia, ib = before["texts"][0]["id"], before["texts"][1]["id"]
        st2.evaluate("""([ia, ib]) => {
            const find = (id) => [...document.querySelectorAll('#mount *')].find(e => e.__fk === id);
            const g = document.createRange(); g.selectNodeContents(find(ia));
            const a0 = g.getClientRects()[0], a = {x: a0.left + a0.width/2, y: a0.top},
                  b = find(ib), q = b.getBoundingClientRect();
            // translate relative to where it already is, so an ancestor transform cannot misplace it
            b.style.transform = 'translate(' + (a.x - q.x) + 'px,' + (a.y - q.y) + 'px)';
        }""", [ia, ib])
        after = collect(st2)
        look = lambda d: text_pair_defects(d["texts"], d["panels"],
                                           lambda p, tx, a=d["above"]: a.get(f"{p}:{tx}", False))
        return len(look(before)), len(look(after))

    outcome = None
    tried = []
    with FilmStage(root) as st2:
        for c0 in [c for c in st2.compositions() if (not only or c.name in only)]:
            r = plant(st2, c0)
            tried.append(c0.name)
            if r and r[1] > r[0]:
                outcome = (c0.name, r)
                break
    R.check("planted live control: moving a real leaf onto another is found; the untouched frame is not",
            outcome is not None,
            f"found on {outcome[0]} (before {outcome[1][0]}, after {outcome[1][1]})" if outcome
            else f"not found on any of {len(tried)} compositions tried", kind="FAIL")
    print("\nPOPULATION")
    print(f"  compositions {n_comp}   sample points {n_samples}   plates seen {len(plate_set)}")
    print(f"  plate words OCR'd {words_raw}   kept as words {words_kept}   "
          f"discarded as noise {words_raw - words_kept}   hit-tested visible {words_visible}")
    print(f"  authored text leaves (sightings) {n_texts}   authored panels (sightings) {n_panels}   "
          f"text pair candidates {n_pairs}")
    if unresolved:
        R.check("every on-screen image resolves to a raster file on disk", False,
                "UNRESOLVED (vector or missing, never OCR'd): " + ", ".join(sorted(unresolved)),
                kind="UNMEASURED")
    R.check("population non-empty", words_visible + n_texts > 0,
            f"{words_visible} visible plate words, {n_texts} authored leaf sightings", kind="UNMEASURED")

    print("\nPLATE OCCLUSION")
    if not plate_defects:
        print("  none recognised (a pass means nothing was recognised under a cover, not that nothing is)")
    for (comp, plate_name, occ), d in sorted(plate_defects.items()):
        words = " ".join(d["words"].values())
        R.check(f"{comp} {occ} ({d['kind']}) does not cover {plate_name}", False,
                f"{len(d['words'])} plate words under it from t={d['first_t']}: {words[:160]!r}")
    if info_defects:
        print(f"  INFO (plate not declared to be read, so not a FAIL): "
              + "; ".join(f"{c} {o} over {n} ({len(d['words'])} words)" for (c, n, o), d in sorted(info_defects.items())))
    print("\nAUTHORED OVER AUTHORED")
    if not auth_defects:
        print("  none")
    for (comp, kind, a_sel, b_sel), d in sorted(auth_defects.items()):
        R.check(f"{comp} {kind}: {a_sel} / {b_sel}", False,
                f"overlap {d['frac']*100:.0f}% of the smaller, from t={d['first_t']}")
    if not plate_defects and not auth_defects:
        R.check("no occlusion recognised", True, f"over {words_visible} visible plate words and {n_texts} leaves")
    if dump:
        pathlib.Path(dump).write_text(json.dumps({
            "plate": {"|".join(k): v for k, v in plate_defects.items()},
            "authored": {"|".join(k): v for k, v in auth_defects.items()}}, indent=1, default=str))



def run(project_root: str, verbose: bool = False, declare=None, step: float = 1.0, only=None, dump=None):
    """Gate entry point. Selftest is not run here; use --selftest."""
    R = Reporter()
    sink = None if verbose else io.StringIO()
    with (contextlib.redirect_stdout(sink) if sink else contextlib.nullcontext()):
        _run(project_root, step, R, only, dump, declare)
    return to_verdict(R, "occlusion")


# -- specimens ----------------------------------------------------------------
# Observed in fin-demo-showcase, 19 Oct 2026, from this check's own hit-test and
# collect output on 09-the-output.html (see the firing run in the report).

def _hit(text, points, visible, covered, occ):
    return WordHit(text, points, visible, covered, occ)

HIT_SPECIMENS = [
    # (id, expectation, WordHit, provenance + why). OBSERVED = the figures this check printed on fin-demo.
    ("umv-09-json-pill-over-validation-note", "FIRE",
     _hit("miswritten.", 27, 27, 10, {"#f09-pill-json": "panel"}),
     "OBSERVED 09 t=12.0: 10 of 27 points under the Copy JSON pill - viewer item 10, 'cut off at miswrit'"),
    ("umv-02-number-badge-over-thumbnail-word", "FIRE",
     _hit("FIN-DEMO", 27, 27, 10, {"div.f02-num": "panel"}),
     "OBSERVED 02 t=5.3: the count badge covers 10 of 27 points of a thumbnail word"),
    ("umv-09-note-first-line-clear", "QUIET",
     _hit("checksum", 27, 27, 0, {}),
     "OBSERVED 09: the same note's first-line words, no cover (the nearest legitimate look-alike)"),
    ("umv-09-word-outside-window-clip", "QUIET",
     _hit("Fin-demo", 27, 0, 0, {}),
     "OBSERVED 09: 2338 words kept, 1663 hit-testable; the rest are clipped by the window and are not a cover"),
]

# rects are (x, y, w, h) from the collect output; ids are small ints
def _txt(i, sel, rect, anc=()):
    return {"id": i, "sel": sel, "rect": rect, "ancestors": set(anc)}

PAIR_SPECIMENS = [
    ("umv-09-pill-label-inside-its-own-pill", "QUIET",
     [_txt(2, "#f09-pill-pages", (1578, 586, 186, 54), anc=(1,))],
     [{"id": 1, "sel": "#f09-pill-pages", "rect": (1578, 586, 186, 54), "ancestors": set()}],
     lambda p, t: True,
     "OBSERVED 09 pill geometry: the label and its pill share a rect; ancestry exempts it, not judgement"),
    ("umv-09-pill-dot-inside-pill", "QUIET",
     [_txt(5, "span.f09-pill-dot", (1599, 668, 6, 26), anc=(4,)), _txt(4, "#f09-pill-json", (1429, 654, 334, 54))],
     [{"id": 4, "sel": "#f09-pill-json", "rect": (1429, 654, 334, 54), "ancestors": set()}],
     lambda p, t: True,
     "OBSERVED 09: the separator dot is a descendant of its pill"),
    ("umv-card-label-over-its-own-card", "QUIET",
     [_txt(1, ".card-label", (96, 596, 200, 30))],
     [{"id": 9, "sel": ".card", "rect": (80, 586, 400, 52), "ancestors": set()}],
     lambda p, t: False,
     "pattern from every fin-demo card: text drawn ABOVE a sibling background panel is normal"),
    ("class-text-over-text-legend-collision", "FIRE",
     [_txt(1, ".legend-a", (100, 100, 300, 30)), _txt(2, ".legend-b", (110, 110, 300, 30))],
     [], lambda p, t: False,
     "CLASS observed on the ISV film (a legend printed over a row), GEOMETRY SYNTHETIC: fin-demo has no live positive"),
    ("class-panel-over-sibling-text", "FIRE",
     [_txt(1, "#eyebrow", (96, 596, 200, 30))],
     [{"id": 9, "sel": "#pill", "rect": (80, 586, 190, 52), "ancestors": set()}],
     lambda p, t: True,
     "CLASS observed (verdict-pill over caption on University), GEOMETRY SYNTHETIC"),
]


def selftest(R: Reporter) -> None:
    print("\nSPECIMENS")
    results = []
    for sid, expect, h, why in HIT_SPECIMENS:
        got = occluded(h)
        results.append((got, expect == "FIRE"))
        R.check(f"specimen {sid} expects {expect}", got == (expect == "FIRE"), why)
    for sid, expect, texts, panels, above, why in PAIR_SPECIMENS:
        got = bool(text_pair_defects(texts, panels, above))
        results.append((got, expect == "FIRE"))
        R.check(f"specimen {sid} expects {expect}", got == (expect == "FIRE"), why)
    probe = Reporter()
    with contextlib.redirect_stdout(io.StringIO()):
        probe.check("planted wrong expectation", occluded(HIT_SPECIMENS[2][2]) == True)
    R.check("a wrong expectation makes the reporter exit non-zero (planted)",
            probe.exit_code() == 1, f"throwaway reporter exit {probe.exit_code()}")
    R.check("specimen set holds both FIRE and QUIET",
            any(e for _, e in results) and any(not e for _, e in results),
            f"{sum(e for _, e in results)} FIRE, {sum(not e for _, e in results)} QUIET")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project", nargs="?")
    ap.add_argument("--step", type=float, default=1.0)
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--dump")
    ap.add_argument("--declare", help="plates-to-read.json; undeclared plates demote covers to INFO")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    R = Reporter()
    selftest(R)
    if a.project and not a.selftest:
        _run(a.project, a.step, R, a.only, a.dump, a.declare)
    code = R.exit_code()
    print(f"\nEXIT {code}  (0 pass, 1 FAIL, 2 UNMEASURED/incomplete)")
    return code


if __name__ == "__main__":
    sys.exit(main())
