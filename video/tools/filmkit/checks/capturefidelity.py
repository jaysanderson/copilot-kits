#!/usr/bin/env python3
"""Is a captured plate being enlarged, and is it being cut mid-content?

Two defects, both arithmetic, both available before a single frame is rendered,
and both reported by a cold viewer of the Fin-demo showcase as one complaint
(item 9: "captured app screenshots are soft and hard-cropped", 2:00-2:20).

1. UPSCALE. A source smaller than the box it is drawn in is enlarged, and
   enlargement is visible as softness at any viewing size. Measured on the real
   film: 09-the-output.html draws screen-result.png, a 1920x1080 capture, and
   the plate SCALES over the beat - 1600px wide early, 2428px at 0.75 of the
   take, which is 1.26x. That is the film's payoff beat, the one the narration
   calls "the schema, filled in", and it is the softest thing in the film.

2. CLIP. A plate inside an ancestor with overflow:hidden is cut by that
   ancestor. Where the cut lands mid-content the frame reads as a broken product
   rather than a crop: the viewer's own words were a hard cut at about y=940
   with a navy band replacing the page bottom, the field table cut mid-row at
   "main_member.paypoint 85%".

THREE DEFECTS IN THE FIRST VERSION OF THIS CHECK, each found by reading its own
output against the film rather than by it failing, and each fixed here. They are
recorded because every one is a general shape, not a detail of this file:

* IT SAMPLED THREE FIXED FRACTIONS AND MISSED THE DEFECT IT WAS WRITTEN FOR.
  A plate that scales across its beat has a worst case at one instant. At 0.25,
  0.6 and 0.9 of the take the payoff plate measured 0.83x and passed; its 1.26x
  lives near 0.75. A move is worst at one end, so this now samples densely and
  reports the MAXIMUM scale with the time it occurs. A single sampled frame is
  not a measurement of a moving thing.
* IT FAILED A WORD CUT AT A CARD'S EDGE, WHICH IS ORDINARY DESIGN. A card
  showing the top of a long document, with its own boundary, is a window and not
  a broken crop - and whether the frame presents the cut edge as the document's
  own end is a judgement no geometry carries. So the mid-word cut is a
  CANDIDATE, printed and counted, never a FAIL. Only the exact facts fail:
  measured enlargement, and a plate whose visible intersection is zero.
* IT READ ELEMENTS MID-TRANSIT AS CLIPPED. A plate sliding into frame is
  legitimately 91% outside the stage at one instant. Clipping by the stage root
  is therefore only reported when it PERSISTS across every sample; clipping by a
  container is reported on its worst sample.

DECLARED BLIND CLASSES, by name:
* A CSS background-image does not expose its natural size to the browser. Those
  are resolved off disk; any that cannot be resolved are reported UNRESOLVED and
  counted, never passed.
* An SVG has no raster natural size and does not go soft when enlarged, so
  vector sources are exempt from the upscale half and reported as such. They are
  still subject to the clip half.
* A plate drawn with object-fit: cover is cropped by design; reported, not failed.
* The mid-word candidate test inherits every blind class of plate.py's OCR,
  including that tesseract under-reads white-on-green and orange-on-cream, and
  that "4 / 4" fails its own control. No candidate means no clipped word was
  RECOGNISED, never that none exists.
* It cannot see softness from any source other than enlargement - a blurred or
  heavily compressed source file measures as sharp.
* It reads one composition in isolation, so it cannot see a neighbouring shot's
  cross-dissolve covering or revealing a cut edge.
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from filmkit.stage import FilmStage          # noqa: E402
from filmkit import plate                    # noqa: E402

# Enlargement above this is a FAIL. The measured pair that sets it: the real
# payoff plate at 1.26x reads soft to a cold viewer, and every correctly sized
# plate in the same film measures at or below 1.00.
UPSCALE_FAIL = 1.15
UPSCALE_WARN = 1.02
SAMPLES = 24          # dense enough to catch the worst instant of a scaling move
CLIP_EPS = 0.005      # below this, a clip is a rounding artefact

_GEOM_JS = """() => {
    const out = [], root = document.getElementById('mount');
    const rectOf = (el) => { const r = el.getBoundingClientRect();
        return {x: r.x, y: r.y, w: r.width, h: r.height}; };
    const sel = (el) => {
        if (el.id) return '#' + el.id;
        const c = (el.className || '').toString().trim().split(/\\s+/).filter(Boolean);
        return el.tagName.toLowerCase() + (c.length ? '.' + c[0] : '');
    };
    root.querySelectorAll('img').forEach(el => {
        const r = el.getBoundingClientRect();
        if (r.width <= 0 || r.height <= 0) return;
        const cs = getComputedStyle(el);
        if (cs.visibility === 'hidden' || cs.display === 'none') return;
        let clip = null, clipper = null, isRoot = false, n = el.parentElement;
        while (n && n !== document.body) {
            const ns = getComputedStyle(n);
            if (/hidden|clip|auto|scroll/.test(ns.overflow + ns.overflowX + ns.overflowY)) {
                clip = rectOf(n); clipper = sel(n);
                isRoot = (n.id === 'root' || n.id === 'mount');
                break;
            }
            n = n.parentElement;
        }
        out.push({selector: sel(el), src: el.currentSrc || el.src, fit: cs.objectFit,
                  nw: el.naturalWidth, nh: el.naturalHeight,
                  box: rectOf(el), clip: clip, clipper: clipper, is_root_clip: isRoot});
    });
    return out;
}"""


class Verdict:
    """One function prints and registers. A check that prints FAIL without
    failing the run is decoration."""

    def __init__(self) -> None:
        self.fails: list[str] = []
        self.candidates: list[str] = []
        self.warns: list[str] = []
        self.holes: list[str] = []

    def fail(self, msg: str) -> None:
        self.fails.append(msg); print(f"  FAIL       {msg}")

    def candidate(self, msg: str) -> None:
        self.candidates.append(msg); print(f"  CANDIDATE  {msg}")

    def warn(self, msg: str) -> None:
        self.warns.append(msg); print(f"  warn       {msg}")

    def hole(self, msg: str) -> None:
        self.holes.append(msg); print(f"  HOLE       {msg}  (unmeasured, not passed)")

    def ok(self, msg: str) -> None:
        print(f"  ok         {msg}")


def _lost_fraction(box: dict, clip: dict) -> float:
    x0 = max(box["x"], clip["x"]); y0 = max(box["y"], clip["y"])
    x1 = min(box["x"] + box["w"], clip["x"] + clip["w"])
    y1 = min(box["y"] + box["h"], clip["y"] + clip["h"])
    iw, ih = max(0.0, x1 - x0), max(0.0, y1 - y0)
    area = box["w"] * box["h"]
    return 1.0 if area <= 0 else 1.0 - (iw * ih) / area


def _cut_words(src: str, box: dict, clip: dict, root: pathlib.Path) -> list[str]:
    path = plate.resolve_src(src, root)
    if path is None or path.suffix.lower() == ".svg":
        return []
    nw, nh = plate.natural_size(path)
    if not nw or not nh:
        return []
    sx, sy = box["w"] / nw, box["h"] / nh
    ey, ex = clip["y"] + clip["h"], clip["x"] + clip["w"]
    hits = []
    for w in plate.words(path, scale=2.0):
        y0 = box["y"] + w.y * sy; y1 = y0 + w.h * sy
        x0 = box["x"] + w.x * sx; x1 = x0 + w.w * sx
        if len(w.text) > 1 and ((y0 < ey < y1) or (x0 < ex < x1)):
            hits.append(w.text)
    return hits


def run(project_root: str, frames_glob: str = "compositions/frames/*.html",
        verbose: bool = False) -> Verdict:
    v = Verdict()
    root = pathlib.Path(project_root)

    ocr_ok, found, missed = plate.ocr_control()
    print(f"OCR control: {'FIRES' if ocr_ok else 'DEAD'}  recognised={found}  missed={missed}")
    if not ocr_ok:
        v.hole("OCR path produced nothing - no mid-word candidate could be raised")

    plates_seen = comps_seen = 0
    with FilmStage(root, frames_glob=frames_glob) as st:
        for c in st.compositions():
            st.mount(c)
            comps_seen += 1
            d = st.duration()
            # key -> aggregated worst case across the whole beat
            agg: dict[str, dict] = {}
            for i in range(SAMPLES + 1):
                t = d * i / SAMPLES
                st.seek(t, settle_ms=0)
                for row in st.evaluate(_GEOM_JS):
                    key = f"{row['selector']}|{row['src']}"
                    a = agg.setdefault(key, {
                        "row": row, "n": 0, "max_w": 0.0, "max_w_t": 0.0,
                        "worst_lost": 0.0, "worst": None, "clipped_n": 0, "zero_n": 0,
                    })
                    a["n"] += 1
                    if row["box"]["w"] > a["max_w"]:
                        a["max_w"], a["max_w_t"], a["row"] = row["box"]["w"], t, row
                    if row["clip"]:
                        lost = _lost_fraction(row["box"], row["clip"])
                        if lost > CLIP_EPS:
                            a["clipped_n"] += 1
                        if lost >= 1.0:
                            a["zero_n"] += 1
                        if lost > a["worst_lost"]:
                            a["worst_lost"], a["worst"] = lost, row

            for key, a in agg.items():
                row = a["row"]
                name = row["src"].rsplit("/", 1)[-1]
                path = plate.resolve_src(row["src"], root)
                plates_seen += 1
                if path is None:
                    v.hole(f"{c.name} {name}: source not resolvable off disk")
                    continue

                # -- upscale, exact ----------------------------------------
                if path.suffix.lower() == ".svg":
                    if verbose:
                        v.ok(f"{c.name} {name}: vector, exempt from upscale")
                else:
                    nw, nh = plate.natural_size(path)
                    up = (a["max_w"] / nw) if nw else 0.0
                    label = (f"{c.name} {name} peaks at {int(a['max_w'])}px wide "
                             f"(t={a['max_w_t']:.1f}s) from a {nw}x{nh} source")
                    if up >= UPSCALE_FAIL:
                        v.fail(f"{label}: enlarged {up:.2f}x - re-capture at "
                               f"{int(a['max_w'])}px or wider")
                    elif up > UPSCALE_WARN:
                        v.warn(f"{label}: enlarged {up:.2f}x")
                    elif verbose:
                        v.ok(f"{label}: scale {up:.2f}x")

                # -- clip --------------------------------------------------
                worst = a["worst"]
                if worst is None or a["worst_lost"] <= CLIP_EPS:
                    continue
                persistent = a["clipped_n"] == a["n"]
                if worst["is_root_clip"] and not persistent:
                    if verbose:
                        v.ok(f"{c.name} {name}: partly off-stage on "
                             f"{a['clipped_n']}/{a['n']} samples - in motion")
                    continue
                if a["zero_n"] == a["n"]:
                    v.fail(f"{c.name} {name}: clipped entirely away by {worst['clipper']} "
                           f"on every sample - drawn and never visible")
                    continue
                if worst["fit"] == "cover":
                    v.ok(f"{c.name} {name}: {a['worst_lost']*100:.0f}% outside its box, "
                         f"object-fit cover - crop by design")
                    continue
                msg = (f"{c.name} {name}: {a['worst_lost']*100:.0f}% cut by "
                       f"{worst['clipper']} at worst")
                cut = _cut_words(worst["src"], worst["box"], worst["clip"], root) if ocr_ok else []
                if cut:
                    v.candidate(msg + f" - the cut passes through {len(cut)} recognised "
                                      f"word(s) {cut[:5]}; look at the frame and decide "
                                      f"whether the edge reads as the document's own")
                else:
                    v.warn(msg + " - no recognised word straddles the cut")

    print(f"\npopulation: {plates_seen} distinct plate draws across {comps_seen} "
          f"compositions, {SAMPLES + 1} samples each")
    if plates_seen == 0:
        v.hole("no plates examined - zero of zero is not a pass")
    print(f"verdict: {len(v.fails)} FAIL, {len(v.candidates)} candidates, "
          f"{len(v.warns)} warn, {len(v.holes)} holes")
    return v


def specimens() -> list[dict]:
    """Observed shapes this check must get right. Each declares FIRE or QUIET.

    Derived from what the real film contains, never from what a failure might
    look like. The QUIET rows are the discriminate controls, and three of them
    exist because the first version of this check fired on them.
    """
    return [
        {"id": "P1", "expect": "FIRE", "observed": "fin-demo 09-the-output",
         "shape": "1920x1080 source scaling to 2428px wide at t=0.75 of the beat",
         "why": "1.26x enlargement at its worst instant; three fixed samples missed it"},
        {"id": "P2", "expect": "QUIET", "observed": "fin-demo 07-step-4-score",
         "shape": "442x625 source drawn at 293x405", "why": "0.66x, reduction is sharp"},
        {"id": "P3", "expect": "CANDIDATE", "observed": "fin-demo 03-the-hard-page",
         "shape": "document plate cut 52% by its own card, through 'Previous operation'",
         "why": "needs an eye: a card edge can legitimately be a window on a long page"},
        {"id": "P4", "expect": "QUIET", "observed": "general",
         "shape": "plate cropped by object-fit: cover", "why": "crop by design"},
        {"id": "P5", "expect": "FIRE", "observed": "general",
         "shape": "plate whose visible intersection is zero on every sample",
         "why": "drawn and never visible is worse than absent"},
        {"id": "P6", "expect": "QUIET", "observed": "fin-demo 01-powered-by",
         "shape": "logo-progress-arag.svg at any size",
         "why": "vector cannot go soft - exempt rather than excluded"},
        {"id": "P7", "expect": "QUIET", "observed": "fin-demo 05-step-2-identify",
         "shape": "ex10-page1.png 91% outside the stage at one instant",
         "why": "mid-transit, not clipped - root clipping must persist to count"},
    ]


if __name__ == "__main__":
    proj = sys.argv[1] if len(sys.argv) > 1 else "fin-demo-showcase"
    verdict = run(proj, verbose="-v" in sys.argv)
    sys.exit(1 if verdict.fails else 0)
