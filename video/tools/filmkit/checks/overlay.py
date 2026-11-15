#!/usr/bin/env python3
"""Pre-render check: a marker drawn over a captured plate may not assert a
detection the plate does not contain.

THE DEFECT CLASS. Fin-demo showcase, frame 03-the-hard-page over assets/form-page3.png
(fresh-eyes report item 1, confirmed at 5x): three green rings sit on the Skin, Lung
and Bone checkboxes; only Bone carries a handwritten X. A "handwritten X" pill then
attaches to the Bone ring, teaching a viewer that a ring means a found tick. The
picture asserts two detections the page does not contain, on the beat the film is
built around. Every other gate passed because none of them reads a marker's
POSITION against the plate's CONTENT, and the coordinates were typed in by hand
(`toView(186, 570)` - literals read off the scan by eye).

TWO HALVES, both per marker.

1. PROVENANCE. A marker's position must be DERIVED from an extraction result, never
   authored. A derived marker declares its source with `data-from="path.json#field-id"`
   on itself or an ancestor. The file must exist and the id must resolve (otherwise
   this RAISES), and the marker's centre must actually sit on that field's bbox, so a
   derivation claim is itself verified. No `data-from` = HAND-AUTHORED = FAIL.
2. CONTENT. Where a truth/result file covers the plate, a marker centred on a field
   whose value is false or absent is a blocking FAIL: this is the no-fake gate
   (hard rule 3) expressed in geometry. A marker declared neutral with
   `data-marker-kind="examined"` is exempt from this half only (the report's own
   remedy: ring every box in a neutral stroke with a legend) - and the exemption is
   counted and printed, never silent.

RESULT FILE SCHEMA (overlay-truth.json at the project root, or --truth, or the
file named by data-from):
  {"plates": {"assets/form-page3.png": {"fields": [
      {"id": "bone", "label": "Bone / Injury", "value": true,
       "bbox": [x, y, w, h]}]}}}        # bbox in the plate's NATIVE pixels

WHAT IS A MARKER. An SVG circle/ellipse/rect/path/line/polygon/polyline, or any
element carrying data-marker, whose centre sits on a plate and whose bounding box
is under 10 per cent of the plate's visible area (larger shapes are regions,
brackets, frames - see blind classes). Plate visible area is the image rect
clipped by every overflow-hidden ancestor.

RAISES (never a quiet pass): zero compositions; an overlay element
(`[data-overlay]`, or an svg whose id/class contains "overlay") that holds zero
marker shapes; a data-from that does not resolve; a plate that cannot be resolved
off disk; a timeline that does not register or an asset that fails to load (from
FilmStage). Zero markers across the whole sweep is a FAIL, not a pass.

DECLARED BLIND CLASSES - a clean result means none of the following were seen:
* DATA FLOW. Provenance is a declaration check plus a bbox cross-check, not a
  trace. A marker that carries a data-from it does not really use, whose bbox
  happens to sit under it, passes. It cannot see a position computed from a data
  file that never declared itself (that reads as hand-authored: a FALSE FAIL by
  design - declare it).
* LARGE MARKERS. A shape over 10 per cent of the plate is treated as a region and
  not tested. A big ring is invisible to this check.
* LABELS AND PILLS. An HTML pill or caption attached to a marker (the "handwritten
  X" pill) is not a marker here unless it carries data-marker. The grammar a
  caption teaches is NOT measured; only what the marker sits on.
* COVERAGE. A marker on a plate whose truth file does not cover the area it sits on
  is reported UNMEASURED (a hole, by source), never PASS. No truth file = the
  content half is a hole for that plate.
* TRUTH QUALITY. The truth file is only as right as whoever wrote it. The selftest
  truth was read off the scan by eye at 5x plus a crop; it was NOT produced by an
  independent extractor.
* STROKE GRAMMAR. What a stroke weight, dash or colour asserts (a solid stroke
  meaning "available today") is not read. See videos/_motifs/GRAMMAR.md.
* CALLBACKS. Markers added by a tl.add(fn) callback do not exist on a seek (the
  stage's own declared blind class).
* PLATE OCR EVIDENCE is advisory (tesseract under-reads white-on-green and
  orange-on-cream; plate.py's declared class). Words under a marker are printed as
  evidence, never used for a verdict.
* ONE COMPOSITION AT A TIME. A cross-dissolve covering or revealing a marker from a
  neighbouring shot is not seen.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import shutil
import sys
import tempfile
from dataclasses import dataclass, field

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from filmkit.stage import FilmStage, StageError  # noqa: E402
from filmkit import plate as platemod  # noqa: E402

MARKER_MAX_FRAC = 0.10   # a shape larger than this share of the visible plate is a region
BBOX_PAD = 12            # native px of tolerance around a truth bbox
SAMPLES = (0.0, 0.25, 0.5, 0.75, 1.0)


class OverlayError(RuntimeError):
    pass


# -- single verdict function ---------------------------------------------------

class Verdicts:
    def __init__(self):
        self.rows: list[tuple[str, str, str, str]] = []   # (status, comp, id, text)

    def record(self, status: str, comp: str, mid: str, text: str) -> None:
        assert status in ("PASS", "FAIL", "HOLE", "NOTE")
        self.rows.append((status, comp, mid, text))
        print(f"  {status:4}  {comp}  {mid}  {text}")

    @property
    def failed(self) -> bool:
        return any(r[0] == "FAIL" for r in self.rows)

    def _strings(self, status: str) -> list[str]:
        return [f"{c} {m}: {t}" for (s, c, m, t) in self.rows if s == status]

    # gate.py contract: each a list of self-contained strings
    @property
    def fails(self) -> list[str]:
        return self._strings("FAIL")

    @property
    def holes(self) -> list[str]:
        return self._strings("HOLE")

    @property
    def warns(self) -> list[str]:
        return self._strings("NOTE")

    @property
    def candidates(self) -> list[str]:
        return []


# -- truth files ---------------------------------------------------------------

def load_json(p: pathlib.Path) -> dict:
    try:
        return json.loads(p.read_text())
    except (OSError, ValueError) as e:
        raise OverlayError(f"cannot read result file {p}: {e}")


def fields_for(truth: dict | None, rel: str) -> list[dict]:
    if not truth:
        return []
    plates = truth.get("plates", {})
    for k, v in plates.items():
        if pathlib.PurePosixPath(k).as_posix() == rel:
            return v.get("fields", [])
    return []


def resolve_from(root: pathlib.Path, spec: str):
    """data-from="path.json#id" -> (path, field dict, plate rel). Raises if unresolved."""
    path, _, fid = spec.partition("#")
    p = (root / path).resolve()
    if not p.exists() or not fid:
        raise OverlayError(f"data-from={spec!r} does not resolve: file missing or no #id")
    doc = load_json(p)
    for rel, v in doc.get("plates", {}).items():
        for f in v.get("fields", []):
            if f.get("id") == fid:
                return p, f, rel
    raise OverlayError(f"data-from={spec!r}: no field {fid!r} in {p.name}")


# -- reading markers off a mounted composition ---------------------------------

_JS = r"""(t) => {
  const mount = document.getElementById('mount'), out = {images: [], markers: [], overlays: []};
  const vis = (el) => { let o = 1, n = el;
    while (n && n !== document.body) { const cs = getComputedStyle(n);
      if (cs.display === 'none' || cs.visibility === 'hidden') return 0;
      const v = parseFloat(cs.opacity); if (!isNaN(v)) o *= v; n = n.parentElement; }
    return o; };
  const clipped = (el) => { const r = el.getBoundingClientRect();
    let l = r.left, tp = r.top, rt = r.right, b = r.bottom, n = el.parentElement;
    while (n && n !== document.body) { const cs = getComputedStyle(n);
      if (cs.overflow !== 'visible' || cs.overflowX !== 'visible' || cs.overflowY !== 'visible') {
        const q = n.getBoundingClientRect();
        l = Math.max(l, q.left); tp = Math.max(tp, q.top); rt = Math.min(rt, q.right); b = Math.min(b, q.bottom); }
      n = n.parentElement; }
    return {x: l, y: tp, w: Math.max(0, rt - l), h: Math.max(0, b - tp)}; };
  const sel = (el) => el.id ? '#' + el.id : el.tagName.toLowerCase() + '.' + ((el.getAttribute('class')||'').split(/\s+/)[0] || '_');
  mount.querySelectorAll('img').forEach((el, i) => { const r = el.getBoundingClientRect();
    if (r.width <= 0) return;
    out.images.push({i, src: el.getAttribute('src'), nw: el.naturalWidth, nh: el.naturalHeight,
      x: r.x, y: r.y, w: r.width, h: r.height, clip: clipped(el), vis: vis(el)}); });
  const SH = 'circle,ellipse,rect,path,line,polygon,polyline,[data-marker]';
  mount.querySelectorAll(SH).forEach((el, i) => {
    if (el.closest('defs,clipPath,mask')) return;
    const r = el.getBoundingClientRect();
    if (r.width <= 0 && r.height <= 0) return;
    const from = el.closest('[data-from]');
    out.markers.push({idx: i, key: sel(el), tag: el.tagName.toLowerCase(),
      x: r.x, y: r.y, w: r.width, h: r.height, vis: vis(el),
      from: from ? from.getAttribute('data-from') : null,
      kind: (el.closest('[data-marker-kind]')||{getAttribute:()=>null}).getAttribute('data-marker-kind'),
      explicit: el.hasAttribute('data-marker'),
      attrs: {cx: el.getAttribute('cx'), cy: el.getAttribute('cy'), x: el.getAttribute('x'), y: el.getAttribute('y')}}); });
  mount.querySelectorAll('[data-overlay], svg').forEach(el => {
    const id = (el.id || '') + ' ' + (el.getAttribute('class') || '');
    if (!el.hasAttribute('data-overlay') && !/overlay/i.test(id)) return;
    out.overlays.push({key: sel(el), shapes: el.querySelectorAll(SH).length}); });
  return out;
}"""


@dataclass
class Marker:
    comp: str
    key: str
    tag: str
    cx: float
    cy: float
    w: float
    h: float
    plate_src: str
    plate_rel: str
    nx: float          # centre in the plate's NATIVE pixels
    ny: float
    from_spec: str | None
    kind: str | None
    literal_attrs: bool
    scripted: bool
    under: list[str] = field(default_factory=list)


def _plate_hit(imgs: list[dict], cx: float, cy: float):
    best = None
    for im in imgs:
        c = im["clip"]
        if c["x"] <= cx <= c["x"] + c["w"] and c["y"] <= cy <= c["y"] + c["h"]:
            if best is None or im["i"] > best["i"]:   # topmost in document order
                best = im
    return best


def scan_composition(stage: FilmStage, comp, root: pathlib.Path):
    stage.mount(comp)
    D = stage.duration()
    seen: dict[str, dict] = {}
    overlays: dict[str, int] = {}
    imgs_last: list[dict] = []
    for f in SAMPLES:
        stage.seek(D * f)
        got = stage.evaluate(_JS, D * f)
        imgs_last = got["images"]
        for o in got["overlays"]:
            overlays[o["key"]] = max(overlays.get(o["key"], 0), o["shapes"])
        for m in got["markers"]:
            k = f'{m["key"]}@{m["idx"]}'
            if m["vis"] > 0.01 or k not in seen:
                m["_imgs"] = got["images"]
                m["_seen_vis"] = m["vis"] > 0.01 or seen.get(k, {}).get("_seen_vis", False)
                seen[k] = m
    for key, n in overlays.items():
        if n == 0:
            raise OverlayError(
                f"{comp.name}: overlay {key} resolves to ZERO marker shapes - a marker "
                "silently applying to nothing leaves a frame looking unchanged and correct")
    out: list[Marker] = []
    n_regions = 0
    for k, m in seen.items():
        if not m["_seen_vis"]:
            continue
        cx, cy = m["x"] + m["w"] / 2, m["y"] + m["h"] / 2
        im = _plate_hit(m["_imgs"], cx, cy)
        if im is None:
            continue
        c = im["clip"]
        if not m["explicit"] and m["w"] * m["h"] > MARKER_MAX_FRAC * c["w"] * c["h"]:
            n_regions += 1
            continue
        p = platemod.resolve_src(im["src"] or "", root)
        if p is None:
            raise OverlayError(f"{comp.name}: plate {im['src']!r} cannot be resolved off disk")
        rel = p.relative_to(root).as_posix() if str(p).startswith(str(root)) else p.as_posix()
        nw = im["nw"] or platemod.natural_size(p)[0]
        nh = im["nh"] or platemod.natural_size(p)[1]
        nx = (cx - im["x"]) * nw / im["w"]
        ny = (cy - im["y"]) * nh / im["h"]
        mid = re.escape(m["key"][1:]) if m["key"].startswith("#") else None
        tag_re = re.search(rf'<{m["tag"]}\b[^>]*\bid="{mid}"[^>]*>', comp.body) if mid else None
        literal = bool(tag_re and re.search(r'\b(cx|cy|x|y|d|points)="-?[0-9.]+', tag_re.group(0)))
        scripted = bool(mid and re.search(rf'["\']{mid}["\']', comp.body) is not None
                        and re.search(r'setAttribute\(\s*["\'](cx|cy|x|y)["\']|\.style\.(left|top)\s*=', comp.body))
        out.append(Marker(comp.name, m["key"], m["tag"], cx, cy, m["w"], m["h"],
                          im["src"], rel, nx, ny, m["from"], m["kind"], literal, scripted))
    # evidence only: plate words near each marker (advisory, see blind classes)
    if out:
        stage.seek(D)
        pw, _unres = platemod.plate_words(stage, root, D)
        for mk in out:
            near = []
            for box, ws in pw:
                if box.src.endswith(mk.plate_src) or mk.plate_src.endswith(box.src.rsplit("/", 1)[-1]):
                    near = sorted(ws, key=lambda w: (w.x + w.w / 2 - mk.cx) ** 2 + (w.y + w.h / 2 - mk.cy) ** 2)[:3]
            mk.under = [w.text for w in near]
    return out, n_regions, overlays


# -- judging -------------------------------------------------------------------

def judge(mk: Marker, root: pathlib.Path, truth: dict | None, V: Verdicts, tag: str = ""):
    """Run both halves on one marker. Returns (provenance_ok, content_ok|None)."""
    ev = f"on {mk.plate_rel} native ({mk.nx:.0f},{mk.ny:.0f}); words nearby {mk.under or '-'}"
    # 1. provenance
    fields = fields_for(truth, mk.plate_rel)
    prov = None
    src_field = None
    if mk.from_spec:
        p, src_field, rel = resolve_from(root, mk.from_spec)
        x, y, w, h = src_field["bbox"]
        inside = (x - BBOX_PAD <= mk.nx <= x + w + BBOX_PAD) and (y - BBOX_PAD <= mk.ny <= y + h + BBOX_PAD)
        prov = inside
        V.record("PASS" if inside else "FAIL", mk.comp, mk.key + f" prov{tag}",
                 f"data-from={mk.from_spec} " + ("and the marker sits on that field's bbox" if inside else
                 f"but the marker is NOT on that field's bbox {src_field['bbox']} ({ev})"))
    else:
        how = ("literal coordinates in the markup" if mk.literal_attrs else
               "coordinates assigned by script with no data source" if mk.scripted else
               "no data-from declaration")
        prov = False
        V.record("FAIL", mk.comp, mk.key + f" prov{tag}", f"HAND-AUTHORED marker ({how}); {ev}")
    # 2. content
    if mk.kind == "examined":
        V.record("NOTE", mk.comp, mk.key + f" content{tag}",
                 "declared neutral (data-marker-kind=examined): content half exempt, by declaration")
        return prov, None
    cand = fields if not src_field else fields + [src_field]
    best, bd = None, None
    for f in cand:
        x, y, w, h = f["bbox"]
        if x - BBOX_PAD <= mk.nx <= x + w + BBOX_PAD and y - BBOX_PAD <= mk.ny <= y + h + BBOX_PAD:
            d = (mk.nx - (x + w / 2)) ** 2 + (mk.ny - (y + h / 2)) ** 2
            if bd is None or d < bd:
                best, bd = f, d
    if not fields and not src_field:
        V.record("HOLE", mk.comp, mk.key + f" content{tag}", f"no result file covers {mk.plate_rel}: content UNMEASURED")
        return prov, None
    if best is None:
        V.record("HOLE", mk.comp, mk.key + f" content{tag}", f"marker is not on any field the result file lists ({ev}): UNMEASURED")
        return prov, None
    if best.get("value") in (False, None):
        V.record("FAIL", mk.comp, mk.key + f" content{tag}",
                 f"marker sits on {best.get('label', best['id'])!r} whose extracted value is {best.get('value')!r}: "
                 "it asserts a detection the plate does not contain (no-fake, blocking)")
        return prov, False
    V.record("PASS", mk.comp, mk.key + f" content{tag}", f"marker sits on {best.get('label', best['id'])!r}, value {best['value']!r}")
    return prov, True


def sweep(root, frames_glob, truth_path, V: Verdicts, quiet_header=False):
    root = pathlib.Path(root).resolve()
    truth = None
    tp = pathlib.Path(truth_path) if truth_path else root / "overlay-truth.json"
    if tp.exists():
        truth = load_json(tp)
    ok, found, missed = platemod.ocr_control()
    print(f"OCR control: {'OK' if ok else 'FAILED'} found={found} missed={missed} "
          "(advisory words under markers are unproven when FAILED)")
    results, n_comp, n_regions, plates = [], 0, 0, set()
    with FilmStage(root, frames_glob=frames_glob) as st:
        comps = st.compositions()
        for c in comps:
            n_comp += 1
            ms, reg, _ = scan_composition(st, c, root)
            n_regions += reg
            for mk in ms:
                plates.add((c.name, mk.plate_rel))
                results.append((mk, judge(mk, root, truth, V)))
    print(f"POPULATION: {len(results)} markers over {len(plates)} plate-uses across {n_comp} compositions "
          f"({n_regions} region-sized shapes over plates not tested; truth file: {tp if truth else 'NONE'})")
    if not results:
        V.record("FAIL", "-", "-", "zero markers over plates across the whole sweep: zero of zero is not a pass")
    return results


# -- selftest: specimens declare FIRE or QUIET -----------------------------------

# Derived from observed output on fin-demo-showcase frame 03 (fresh-eyes report item 1,
# lead-confirmed at 5x, plus a 3x crop read for this check): the film's own
# authored centres in native plate px. Skin and Lung boxes are EMPTY; Bone carries
# a handwritten X. Boxes are ~24 native px square, hence the 20x20 bbox.
FIN-DEMO_TRUTH = {"plates": {"assets/form-page3.png": {"fields": [
    {"id": "skin", "label": "Skin conditions", "value": False, "bbox": [176, 560, 20, 20]},
    {"id": "lung", "label": "Lung conditions", "value": False, "bbox": [393, 544, 20, 20]},
    {"id": "bone", "label": "Bone / Injury conditions", "value": True, "bbox": [390, 752, 20, 20]},
]}}}

# (marker key, half) -> expected
EXPECT_FIN-DEMO = {
    ("#f03-ring-1", "prov"): "FAIL", ("#f03-ring-2", "prov"): "FAIL", ("#f03-ring-3", "prov"): "FAIL",
    ("#f03-ring-1", "content"): "FAIL", ("#f03-ring-2", "content"): "FAIL",
    ("#f03-ring-3", "content"): "PASS",        # the DISCRIMINATE control: the correct ring stays quiet
}


def _synthetic(root: pathlib.Path, plate_png: pathlib.Path, ring_field: str, data_from: bool, truth: dict):
    (root / "assets").mkdir(parents=True)
    (root / "compositions/frames").mkdir(parents=True)
    shutil.copy(plate_png, root / "assets/form-page3.png")
    (root / "assets/form-page3.truth.json").write_text(json.dumps(truth))
    f = {x["id"]: x for x in truth["plates"]["assets/form-page3.png"]["fields"]}[ring_field]
    bx, by, bw, bh = f["bbox"]
    cx, cy = (bx + bw / 2) * 0.5, (by + bh / 2) * 0.5          # plate drawn at 0.5 scale
    df = f' data-from="assets/form-page3.truth.json#{ring_field}"' if data_from else ""
    (root / "compositions/frames/s.html").write_text(
        '<template id="s" data-composition-id="s" data-width="1920" data-height="1080" data-duration="2">'
        '<div id="root" style="position:relative;width:1920px;height:1080px">'
        '<div id="card" style="position:absolute;left:100px;top:0;width:534px;height:764px;overflow:hidden">'
        '<img src="assets/form-page3.png" style="position:absolute;left:0;top:0;width:533.5px;height:764px">'
        f'<svg id="ov" data-overlay width="534" height="764"{df}>'
        f'<circle id="r" cx="{cx}" cy="{cy}" r="9" fill="none" stroke="#0f0" stroke-width="3"/></svg>'
        '</div></div><script>window.__timelines=window.__timelines||{};'
        'var tl=gsap.timeline({paused:true});tl.to("#card",{opacity:1,duration:2});'
        'window.__timelines["s"]=tl;</script></template>')
    return root


def selftest() -> int:
    repo = pathlib.Path(__file__).resolve().parents[3]
    umv = repo / "fin-demo-showcase"
    fails = 0

    def check(label, got, want):
        nonlocal fails
        good = got == want
        fails += 0 if good else 1
        print(f"SPECIMEN {'ok  ' if good else 'WRONG'} {label}: expected {want}, got {got}")

    print("== specimen set 1: fin-demo-showcase 03-the-hard-page (real, pre-fix) ==")
    V = Verdicts()
    root = umv
    with FilmStage(root, frames_glob="compositions/frames/03-the-hard-page.html") as st:
        c = st.compositions()[0]
        ms, reg, _ = scan_composition(st, c, root)
    rings = [m for m in ms if m.key.startswith("#f03-ring")]
    check("rings found (population)", len(rings), 3)
    for m in sorted(rings, key=lambda m: m.key):
        p, cn = judge(m, root, FIN-DEMO_TRUTH, V)
        check(f"{m.key} provenance", "PASS" if p else "FAIL", EXPECT_FIN-DEMO[(m.key, "prov")])
        check(f"{m.key} content", {True: "PASS", False: "FAIL", None: "HOLE"}[cn], EXPECT_FIN-DEMO[(m.key, "content")])
    # inverted expectation: flip Bone to false and the Bone ring MUST now fire (plant mutated its input)
    flipped = json.loads(json.dumps(FIN-DEMO_TRUTH))
    flipped["plates"]["assets/form-page3.png"]["fields"][2]["value"] = False
    assert flipped != FIN-DEMO_TRUTH, "inert plant"
    bone = next(m for m in rings if m.key == "#f03-ring-3")
    V2 = Verdicts()
    _, cn = judge(bone, root, flipped, V2)
    check("bone ring with Bone flipped to false (plant)", "FAIL" if cn is False else "NOT-FIRED", "FAIL")

    print("== specimen set 2: synthetic derived markers (QUIET provenance control) ==")
    plate = umv / "assets/form-page3.png"
    for fid, want_content in (("bone", "PASS"), ("lung", "FAIL")):
        td = pathlib.Path(tempfile.mkdtemp(prefix="overlaychk_"))
        try:
            r = _synthetic(td / "p", plate, fid, True, FIN-DEMO_TRUTH)
            with FilmStage(r) as st:
                cc = st.compositions()[0]
                ms2, _, _ = scan_composition(st, cc, r)
            check(f"synthetic {fid}: marker count", len(ms2), 1)
            Vs = Verdicts()
            p, cn = judge(ms2[0], r, None, Vs)
            check(f"synthetic {fid} provenance (derived, on bbox)", "PASS" if p else "FAIL", "PASS")
            check(f"synthetic {fid} content", {True: "PASS", False: "FAIL", None: "HOLE"}[cn], want_content)
        finally:
            shutil.rmtree(td, ignore_errors=True)
    print("== specimen set 3: an overlay holding zero shapes must RAISE ==")
    td = pathlib.Path(tempfile.mkdtemp(prefix="overlaychk_"))
    try:
        r = _synthetic(td / "p", plate, "bone", True, FIN-DEMO_TRUTH)
        f = r / "compositions/frames/s.html"
        before = f.read_text()
        after = re.sub(r"<circle[^>]*/>", "", before)
        assert after != before, "inert plant"
        f.write_text(after)
        raised = False
        try:
            with FilmStage(r) as st:
                scan_composition(st, st.compositions()[0], r)
        except OverlayError:
            raised = True
        check("empty overlay raises", "RAISED" if raised else "PASSED-QUIETLY", "RAISED")
    finally:
        shutil.rmtree(td, ignore_errors=True)
    print(f"SELFTEST {'PASS' if fails == 0 else 'FAIL'}: {fails} specimen(s) disagree with their declared FIRE/QUIET")
    return 1 if fails else 0


def run(project_root: str, verbose: bool = False, frames: str = "compositions/frames/*.html",
        truth: str | None = None) -> Verdicts:
    """Gate entry point. Raises become FAIL strings, never a quiet pass."""
    V = Verdicts()
    try:
        sweep(project_root, frames, truth, V)
    except (OverlayError, StageError) as e:
        V.record("FAIL", "-", "-", f"RAISED: {e}")
    return V


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("root", nargs="?", help="film project root (contains compositions/frames)")
    ap.add_argument("--frames", default="compositions/frames/*.html")
    ap.add_argument("--truth", help="result file (default: <root>/overlay-truth.json if present)")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.root:
        ap.error("root required")
    V = run(a.root, True, a.frames, a.truth)
    if any("RAISED:" in t for _, _, _, t in V.rows):
        return 2
    print(f"VERDICT (axis: marker provenance + marker-over-false-value, over markers only): "
          f"{len(V.fails)} FAIL, {len(V.holes)} HOLE (unmeasured), {sum(1 for r in V.rows if r[0]=='PASS')} PASS")
    return 1 if V.failed else 0


if __name__ == "__main__":
    sys.exit(main())
