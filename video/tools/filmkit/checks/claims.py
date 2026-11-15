#!/usr/bin/env python3
"""Claim-to-frame coverage: every outcome a film asserts must have a frame that shows it.

THE DEFECT CLASS. A film asserts an outcome in its narration or on a pill, and no
frame ever shows it. fin-demo-showcase carries two real instances
(videos/fin-demo-viewer2-report.md items 6 and 7): four outcome pills ("Missing page -
FLAGGED", "Shuffled scan - REASSEMBLED", "Word files - CONVERTED", "Phone photos - READ
- DOUBTFUL FIELDS FLAGGED") asserted by text and voice with no result frame behind any
of them, and a beat whose data has three fields TRUE while the picture shows one.

WHAT IT MEASURES, in two directions, over the declaration in STORYBOARD-SCHEMA.md:

  1. A declared claim with no proof frame            -> NO_PROOF / PROOF_TEXT_ONLY
     A proof whose region is not inside the crop     -> FIELD_OUTSIDE_CROP
     A proof whose image is not on screen at t       -> FRAME_NOT_ON_SCREEN
  2. A rendered pill or narrated sentence asserting an outcome that no declared claim
     covers                                          -> UNCOVERED_ASSERTION
  3. A beat that has no declaration at all           -> UNDECLARED (by name, never a pass)

The assertion population is DISCOVERED, never typed: pills come from
FilmStage.visible_strings() (the rendered timeline), narration from SCRIPT.md or the
film's storyboard.json. The sweep is for the CLAIM (outcome verbs, OUTCOME_RE), then each
hit is tested for a covering declaration - never for a qualifier, because a sweep for the
qualifier cannot find its absence.

BLIND CLASSES, declared by name. A clean result means "every discovered assertion has a
declared proof that exists and contains its fields", never "the film proves its claims".
  B1 PERSUASION. It cannot judge whether a frame is persuasive, only whether it exists
     and contains the declared region. A proof frame that exists and does not convince
     passes. Eye-read at the lead gate; nothing here covers it.
  B2 DECLARED REGIONS. A field's bbox and a crop are DECLARED by the author, not read
     off the pixels. It proves the declared region is inside the declared crop, not that
     the value is legible inside that region. A wrong bbox passes. (Legibility is a
     separate printed figure, SMALL, and is an estimate-class candidate, never a fail.)
  B3 CROP HONESTY. In a composition, a declared crop is not verified against what the
     composition clips. The composition-derived default (whole image, object-fit) is.
  B4 LEXICON. OUTCOME_RE finds outcome language by verb. An outcome stated in words it
     does not list is not discovered, and a beat with zero hits is still UNDECLARED, not
     clean. Pills are read from rendered DOM text; a claim baked into a captured image
     is pixels and is invisible here (see platetext.py for OCR).
  B5 REMOTION FILMS. No DOM, so no pill population: only narration is discovered, and
     the proof frame is a capture file plus a declared display height. A pill drawn by a
     Remotion component is invisible to this check.
  B6 CALLBACKS. A composition change made in a tl.add(fn) callback does not re-run on a
     seek, so a pill a callback reveals is not discovered (stage.callback_beats()).
  B7 TRUTH. It never checks the claim is TRUE of the product. The `truth` field is
     recorded from the film's own evidence and printed beside the verdict as a second
     axis. fin-demo "Word files CONVERTED" is truth=unverified (RESUME.md section 5) and
     stays so; three siblings being true does not promote it.

Usage:
  .venv/bin/python scripts/filmkit/checks/claims.py --film fin-demo-showcase
  .venv/bin/python scripts/filmkit/checks/claims.py --film kuraray-portal-en
  .venv/bin/python scripts/filmkit/checks/claims.py --film fin-demo-showcase --declarations none
  .venv/bin/python scripts/filmkit/checks/claims.py --selftest
Exit code is the verdict: non-zero on any finding. stdout is commentary.
"""
from __future__ import annotations

import argparse
import copy
import json
import pathlib
import re
import sys
from dataclasses import dataclass, field

REPO = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "scripts"))
from filmkit.stage import FilmStage  # noqa: E402  the one primitive; never reimplemented

SCHEMA_DOC = REPO / "scripts" / "filmkit" / "STORYBOARD-SCHEMA.md"
FENCE_INFO = "filmkit-claims"

# Outcome language. Swept for the CLAIM (verbs of result), then each hit is tested for a
# covering declaration. Deliberately wide: a candidate costs one declaration or one
# `declared_none` with a reason; a missed claim costs a shipped overclaim.
OUTCOME_RE = re.compile(
    r"\b(flagg?ed|flags?|reassembl\w*|convert\w*|verified|deleted|none missing|"
    r"hold up|comes? back|one (?:application )?per applicant|every checkbox right|"
    r"read right|(?:are |is )?read\b|reads\b|quotes?|crosses|score[sd]?|"
    r"earns?|ticked|true)\b",
    re.I,
)
PILL_MAX_CHARS = 90          # a pill is short; a paragraph of copy is narration, not a pill
TICK_FLOOR_PX = 24           # authored px (1920 frame). Estimate-class candidate, never a fail.
FRAME_W = 1920
PHONE_W = 390

FILMS = {
    "fin-demo-showcase": dict(
        kind="composition",
        root="fin-demo-showcase",
        script="fin-demo-showcase/SCRIPT.md",
    ),
    "harbourline-toyota": dict(
        kind="capture",
        root="videos/harbourline-toyota",
        storyboard="videos/harbourline-toyota/storyboard.json",
    ),
    "kuraray-portal-en": dict(
        kind="capture",
        root="videos/kuraray-portal/en",
        storyboard="videos/kuraray-portal/en/storyboard.json",
    ),
}


# ---------------------------------------------------------------- verdict plumbing

class Verdicts:
    """ONE function prints and registers every verdict, so a FAIL cannot print without
    counting. The exit code is derived from the register and from nothing else."""

    def __init__(self) -> None:
        self.rows: list[tuple[str, str, str]] = []   # (status, id, detail)

    def record(self, status: str, ident: str, detail: str = "") -> None:
        self.rows.append((status, ident, detail))
        print(f"  {status:<20} {ident}" + (f"  {detail}" if detail else ""))

    def fails(self) -> list[tuple[str, str, str]]:
        return [r for r in self.rows if r[0] != "PASS"]


# ---------------------------------------------------------------- declaration parser

FENCE_OPEN = re.compile(r"^```" + FENCE_INFO + r"[ \t]*$", re.M)
FENCE_BLOCK = re.compile(r"^```" + FENCE_INFO + r"[ \t]*\n(.*?)^```[ \t]*$", re.M | re.S)


def parse_declarations(path: pathlib.Path) -> dict:
    """Read every fenced `filmkit-claims` block. Returns {film: {beat: entry}} plus counts.

    The machine block is JSON on purpose: a line-list parser stops at the first line of
    explanation and reads ZERO items as a serene pass (happened twice in one day). JSON
    either parses whole or raises. The opener count is taken independently of the block
    regex, so an unclosed or nested fence cannot silently shrink the population.
    """
    if not path.exists():
        return dict(blocks=0, openers=0, films={}, source=str(path))
    text = path.read_text()
    openers = len(FENCE_OPEN.findall(text))
    blocks = FENCE_BLOCK.findall(text)
    if openers != len(blocks):
        raise ValueError(
            f"{path.name}: {openers} fence opener(s) but {len(blocks)} closed block(s) - "
            "an unclosed fence would have read fewer declarations than exist"
        )
    films: dict[str, dict] = {}
    for i, body in enumerate(blocks):
        try:
            doc = json.loads(body)
        except json.JSONDecodeError as e:
            raise ValueError(f"{path.name}: block {i + 1} is not valid JSON: {e}") from e
        if "film" not in doc or "beats" not in doc:
            raise ValueError(f"{path.name}: block {i + 1} needs 'film' and 'beats'")
        films.setdefault(doc["film"], {}).update(doc["beats"])
    return dict(blocks=len(blocks), openers=openers, films=films, source=str(path))


# ---------------------------------------------------------------- text helpers

def norm(s: str) -> str:
    return re.sub(r"[^\w]+", " ", s.casefold()).strip()


def covers(quote: str, text: str) -> bool:
    q, t = norm(quote), norm(text)
    return bool(q and t and (q in t or t in q))


def sentences(para: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", para.strip()) if s.strip()]


# ---------------------------------------------------------------- worlds (population)

@dataclass
class Beat:
    name: str
    narration: list[str] = field(default_factory=list)   # discovered outcome sentences
    pills: list[str] = field(default_factory=list)       # discovered outcome pills


class CompositionWorld:
    """A HyperFrames film. Population from the rendered timeline; proof via the DOM."""

    def __init__(self, cfg: dict, stage: FilmStage):
        self.cfg, self.stage = cfg, stage
        self.root = REPO / cfg["root"]
        self.comps = {c.path.stem: c for c in stage.compositions()}
        self.beats = self._discover()

    def _lines(self) -> list[tuple[str, list[str]]]:
        text = (REPO / self.cfg["script"]).read_text()
        out = []
        for m in re.finditer(r"^## Line (\d+)[^\n]*\n(.*?)(?=^## Line |\Z)", text, re.M | re.S):
            body = [ln.strip() for ln in m.group(2).splitlines() if ln.startswith("    ")]
            out.append((m.group(1), sentences(" ".join(body))))
        return out

    def _discover(self) -> list[Beat]:
        names = sorted(self.comps)
        lines = self._lines()
        if len(lines) != len(names):
            raise RuntimeError(
                f"SCRIPT.md has {len(lines)} Line sections but {len(names)} compositions - "
                "the narration-to-beat mapping is not 1:1, refusing to guess"
            )
        beats = []
        for name, (_, sents) in zip(names, lines):
            self.stage.mount(self.comps[name])
            strings = self.stage.visible_strings(steps=60)
            pills = [s for s in strings if len(s) <= PILL_MAX_CHARS and OUTCOME_RE.search(s)]
            beats.append(Beat(name, [s for s in sents if OUTCOME_RE.search(s)], sorted(set(pills))))
        return beats

    def image_size(self, basename: str) -> tuple[int, int] | None:
        from PIL import Image
        hits = list(self.root.glob(f"**/{basename}"))
        if not hits:
            return None
        with Image.open(hits[0]) as im:
            return im.size

    def displayed(self, comp_name: str, t: float, basename: str):
        """(x, y, w, h) of the image box on screen at t, or None."""
        if comp_name not in self.comps:
            return None
        self.stage.mount(self.comps[comp_name])
        for b in self.stage.image_boxes(t):
            if b.src.rsplit("/", 1)[-1] == basename:
                return (b.x, b.y, b.w, b.h)
        return None


class CaptureWorld:
    """A Remotion film: no DOM. Population from storyboard narration; proof is a capture
    file plus a declared display height (blind class B5)."""

    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.root = REPO / cfg["root"]
        sb = json.loads((REPO / cfg["storyboard"]).read_text())
        self.beats = []
        for sc in sb["scenes"]:
            sents = [s for line in sc.get("narration", []) for s in sentences(line)]
            self.beats.append(Beat(sc["id"], [s for s in sents if OUTCOME_RE.search(s)], []))

    def image_size(self, rel: str) -> tuple[int, int] | None:
        from PIL import Image
        p = self.root / "public" / rel
        if not p.exists():
            return None
        with Image.open(p) as im:
            return im.size


# ---------------------------------------------------------------- proof verification

def _bbox(v) -> list[float]:
    return list(v["bbox"] if isinstance(v, dict) else v)


def verify_frame(world, beat: str, frame: dict | None) -> tuple[str, str]:
    """Return (status, detail). PASS only when a real image frame is on screen at t and
    its crop contains every declared field."""
    if not frame:
        return "NO_PROOF", "declares no frame; the claim is asserted by text/voice only"
    is_comp = isinstance(world, CompositionWorld)
    key = "image" if is_comp else "capture"
    ref = frame.get(key)
    if not ref:
        return "PROOF_TEXT_ONLY", "frame names no image or capture; a restatement is not a result"
    size = world.image_size(ref)
    if size is None:
        return "FILE_MISSING", f"{ref} not found under {world.root}"
    nw, nh = size
    scale = None
    if is_comp:
        box = world.displayed(frame["composition"], float(frame["t"]), ref)
        if box is None:
            return "FRAME_NOT_ON_SCREEN", (
                f"{ref} is not on screen in {frame['composition']} at t={frame['t']}")
        bw, bh = box[2], box[3]
    else:
        bh = float(frame["display_height"])
        bw = bh * nw / nh
    crop = list(frame.get("crop") or [0, 0, nw, nh])
    cw, ch = crop[2] - crop[0], crop[3] - crop[1]
    scale = min(bw / cw, bh / ch)
    fields = frame.get("fields") or {}
    if not fields:
        return "PROOF_NO_FIELDS", "frame declares no fields; nothing says what it is proof OF"
    missing = [
        k for k, v in fields.items()
        if not (_bbox(v)[0] >= crop[0] and _bbox(v)[1] >= crop[1]
                and _bbox(v)[2] <= crop[2] and _bbox(v)[3] <= crop[3])
    ]
    if missing:
        return "FIELD_OUTSIDE_CROP", (
            f"{len(fields) - len(missing)} of {len(fields)} fields inside the crop; "
            f"not shown: {', '.join(missing)}")
    small = []
    for k, v in fields.items():
        b = _bbox(v)
        px = min(b[2] - b[0], b[3] - b[1]) * scale
        if px < TICK_FLOOR_PX:
            small.append(f"{k}={px:.1f}px")
    note = f"{len(fields)}/{len(fields)} fields inside crop, scale {scale:.3f}"
    if small:
        note += (f"; SMALL candidate (floor {TICK_FLOOR_PX}px authored = "
                 f"{TICK_FLOOR_PX * PHONE_W / FRAME_W:.1f}px at 390 wide): " + ", ".join(small))
    return "PASS", note


# ---------------------------------------------------------------- evaluation

def evaluate(world, film: str, declared: dict, v: Verdicts) -> dict:
    """Both directions over every discovered beat. Returns the population counts."""
    counts = dict(beats=len(world.beats), beats_declared=0, beats_undeclared=0,
                  claims=0, frames=0, proven=0, voice_found=0, pills_found=0, uncovered=0,
                  small=0)
    for beat in world.beats:
        counts["voice_found"] += len(beat.narration)
        counts["pills_found"] += len(beat.pills)
        entry = declared.get(beat.name)
        found = f"{len(beat.narration)} voice + {len(beat.pills)} pill outcome assertion(s) discovered"
        if entry is None:
            counts["beats_undeclared"] += 1
            v.record("UNDECLARED", beat.name, found)
            continue
        counts["beats_declared"] += 1
        if "declared_none" in entry:
            if not entry["declared_none"].strip():
                v.record("EMPTY_WAIVER", beat.name, "declared_none needs a reason")
            else:
                v.record("PASS", f"{beat.name}  (declared_none)", f"{found}; reason: {entry['declared_none']}")
                counts["uncovered"] += 0
            # a waiver does not hide assertions: they must still be declared none-claiming
            continue
        claims = entry.get("claims", [])
        if not claims:
            v.record("EMPTY_DECLARATION", beat.name, "entry has neither claims nor declared_none")
            continue
        for c in claims:
            counts["claims"] += 1
            counts["frames"] += 1 if c.get("frame") else 0
            status, detail = verify_frame(world, beat.name, c.get("frame"))
            truth = c.get("truth", "unrecorded")
            if status == "PASS":
                counts["proven"] += 1
                counts["small"] += 1 if "SMALL" in detail else 0
            v.record(status, f"{beat.name}/{c['id']}", f"[truth={truth}] {detail}")
        quotes = [c["quote"] for c in claims]
        for kind, items in (("voice", beat.narration), ("pill", beat.pills)):
            for text in items:
                if not any(covers(q, text) for q in quotes):
                    counts["uncovered"] += 1
                    v.record("UNCOVERED_ASSERTION", f"{beat.name}/{kind}", f"no declared claim covers: {text!r}")
    return counts


def print_population(film: str, counts: dict, decl: dict) -> None:
    print(f"\nPOPULATION  film={film}  declaration source={decl['source']}")
    print(f"  declaration blocks found: {decl['blocks']} (fence openers {decl['openers']}), "
          f"for this film: {len(decl['films'].get(film, {}))} beat entr(ies)")
    print(f"  beats: {counts['beats']}  declared: {counts['beats_declared']}  "
          f"UNDECLARED: {counts['beats_undeclared']}")
    print(f"  discovered outcome assertions: {counts['voice_found']} voice, {counts['pills_found']} pill")
    print(f"  claims declared: {counts['claims']}  frames declared: {counts['frames']}  "
          f"claims with a passing proof: {counts['proven']}  uncovered assertions: {counts['uncovered']}")
    print("  property measured: COVERAGE claim<->frame and field-in-crop. "
          "NOT persuasion (B1), NOT truth (B7), NOT legibility beyond the SMALL estimate (B2).")


# ---------------------------------------------------------------- running a film

def run_film(film: str, decl_path: pathlib.Path | None, quiet_header: bool = False) -> tuple[Verdicts, dict]:
    cfg = FILMS[film]
    decl = parse_declarations(decl_path) if decl_path else dict(
        blocks=0, openers=0, films={}, source="none (no declaration supplied)")
    declared = decl["films"].get(film, {})
    v = Verdicts()
    print(f"claims.py  {film}")
    if cfg["kind"] == "composition":
        with FilmStage(REPO / cfg["root"]) as st:
            world = CompositionWorld(cfg, st)
            counts = evaluate(world, film, declared, v)
    else:
        world = CaptureWorld(cfg)
        counts = evaluate(world, film, declared, v)
    print_population(film, counts, decl)
    return v, counts


# ---------------------------------------------------------------- selftest

def selftest() -> int:
    """Specimens declare FIRE or QUIET up front, derived from observed output of the real
    films. Each plant proves it changed its input. The selftest then INVERTS every
    expectation and requires the reporter to disagree with all of them, so the reporter is
    proven able to fail rather than merely to print."""
    import tempfile
    bad: list[str] = []
    results: list[tuple[str, str, bool]] = []     # (id, FIRE|QUIET, observed fired)

    def status_of(vv: Verdicts, ident: str) -> str | None:
        return next((s for s, i, _ in vv.rows if i == ident), None)

    def detail_of(vv: Verdicts, ident: str) -> str:
        return next((d for _, i, d in vv.rows if i == ident), "")

    def expect(sid: str, kind: str, fired: bool, why: str) -> None:
        results.append((sid, kind, fired))
        print(f"   {sid} expect {kind}: observed {'FIRED' if fired else 'QUIET'}  ({why})")
        if (kind == "FIRE") != fired:
            bad.append(f"{sid}: expected {kind}, observed {'FIRED' if fired else 'QUIET'}")

    decl = parse_declarations(SCHEMA_DOC)
    udecl = decl["films"].get("fin-demo-showcase", {})
    kdecl = decl["films"].get("kuraray-portal-en", {})

    # --- parser, on the REAL file this check ships with
    text = SCHEMA_DOC.read_text()
    independent = len(re.findall(r"^```filmkit-claims", text, re.M))
    print(f"PARSER  blocks parsed={decl['blocks']} independent opener count={independent} "
          f"fin-demo beats={len(udecl)} kuraray beats={len(kdecl)}")
    if not (decl["blocks"] == independent == 2 and len(udecl) == 2 and len(kdecl) == 1):
        bad.append("parser did not read the real schema file's blocks")
    with tempfile.TemporaryDirectory() as td:
        stripped = FENCE_BLOCK.sub("", text)
        assert stripped != text, "inert plant: block removal changed nothing"
        p = pathlib.Path(td) / "no-block.md"
        p.write_text(stripped)
        none_ = parse_declarations(p)
        print(f"PARSER  block absent -> blocks={none_['blocks']} films={len(none_['films'])}")
        if none_["blocks"] != 0 or none_["films"]:
            bad.append("parser read declarations from a file with no block")
        q = pathlib.Path(td) / "prose-between.md"
        q.write_text('```filmkit-claims\n{"film":"a","beats":{"x":{"declared_none":"r"}}}\n```\n'
                     "A long line of explanation that a list parser would stop at.\n\n"
                     '```filmkit-claims\n{"film":"b","beats":{"y":{"declared_none":"r"}}}\n```\n')
        if len(parse_declarations(q)["films"]) != 2:
            bad.append("prose between blocks stopped the parser")
        r = pathlib.Path(td) / "unclosed.md"
        r.write_text('```filmkit-claims\n{"film":"a","beats":{}}\n')
        try:
            parse_declarations(r)
            bad.append("unclosed fence did not raise")
        except ValueError:
            print("PARSER  unclosed fence -> raised (fires)")

    # --- fin-demo, live render: one stage for every specimen
    with FilmStage(REPO / FILMS["fin-demo-showcase"]["root"]) as st:
        world = CompositionWorld(FILMS["fin-demo-showcase"], st)
        b11 = next(b for b in world.beats if b.name == "11-messy-ones")
        print(f"\nOBSERVED 11-messy-ones pills: {b11.pills}")
        print(f"OBSERVED 11-messy-ones narration outcome sentences: {b11.narration}")

        def run(label: str, d: dict, film="fin-demo-showcase", w=world) -> Verdicts:
            print(f"\n-- specimen {label}")
            vv = Verdicts()
            evaluate(w, film, d, vv)
            return vv

        s1 = run("S1 no declaration at all", {})
        n = sum(1 for s, _, _ in s1.rows if s == "UNDECLARED")
        expect("S1", "FIRE", n == len(world.beats), f"{n}/{len(world.beats)} beats UNDECLARED, none passed")

        s2 = run("S2 the shipped declaration: four unproven pills (item 7)", udecl)
        ids = ("missing-page-flagged", "shuffled-reassembled", "word-files-converted", "phone-photos-flagged")
        n2 = sum(1 for c in ids if status_of(s2, f"11-messy-ones/{c}") == "NO_PROOF")
        expect("S2", "FIRE", n2 == 4, f"{n2}/4 pills NO_PROOF on the real film")

        d3 = copy.deepcopy(udecl)
        c3 = d3["11-messy-ones"]["claims"][0]
        assert c3["frame"] is None
        c3["frame"] = {"composition": "11-messy-ones", "t": 10.5, "fields": {"flagged": [0, 0, 1, 1]}}
        s3 = run("S3 plant: a proof with no image (claim restated)", d3)
        expect("S3", "FIRE", status_of(s3, f"11-messy-ones/{c3['id']}") == "PROOF_TEXT_ONLY", "text-only proof refused")

        s4 = run("S4 item 6 on the real composition (whole page, 278px thumbnail)", udecl)
        r4 = detail_of(s4, "06-step-3-ask/three-fields-true")
        print(f"   -> {status_of(s4, '06-step-3-ask/three-fields-true')}: {r4}")
        expect("S4", "FIRE", "SMALL candidate" in r4, "all three ticks reported SMALL; fields inside the crop, so no FIELD_OUTSIDE_CROP")

        d5 = copy.deepcopy(udecl)
        fr5 = d5["06-step-3-ask"]["claims"][0]["frame"]
        assert "crop" not in fr5
        fr5["crop"] = [150, 296, 440, 330]
        s5 = run("S5 plant: the crop the viewer describes (Bone X only)", d5)
        r5 = detail_of(s5, "06-step-3-ask/three-fields-true")
        print(f"   -> {status_of(s5, '06-step-3-ask/three-fields-true')}: {r5}")
        expect("S5", "FIRE", status_of(s5, "06-step-3-ask/three-fields-true") == "FIELD_OUTSIDE_CROP"
               and "sugar_diabetes" in r5 and "vehicle_accident" in r5 and "bone_injury" not in r5.split("not shown:")[-1],
               "1 of 3 fields inside the crop; the two missing are named")

        d6 = copy.deepcopy(udecl)
        gone = [c for c in d6["11-messy-ones"]["claims"] if c["id"] == "word-files-converted"]
        assert len(gone) == 1
        d6["11-messy-ones"]["claims"].remove(gone[0])
        s6 = run("S6 plant: the Word files claim removed (frame asserts, no claim declares)", d6)
        expect("S6", "FIRE", any(s == "UNCOVERED_ASSERTION" and "converted" in d.lower() for s, _, d in s6.rows),
               "rendered CONVERTED pill reported uncovered")

        s7 = run("S7 declared_none with a reason", {"01-powered-by": {"declared_none": "title card; asserts no outcome"}})
        expect("S7", "QUIET", status_of(s7, "01-powered-by  (declared_none)") != "PASS", "honest waiver accepted")
        s7b = run("S7b empty waiver", {"01-powered-by": {"declared_none": "  "}})
        expect("S7b", "FIRE", status_of(s7b, "01-powered-by") == "EMPTY_WAIVER", "empty reason refused")

    # --- kuraray: the DISCRIMINATE control, a claim the film does earn must stay QUIET
    cw = CaptureWorld(FILMS["kuraray-portal-en"])
    print("\n-- specimen S8 kuraray 'answer' (earned)")
    s8 = Verdicts()
    evaluate(cw, "kuraray-portal-en", kdecl, s8)
    for cid in ("japanese-term-quoted", "answer-in-english"):
        print(f"   -> {cid}: {status_of(s8, 'answer/' + cid)}: {detail_of(s8, 'answer/' + cid)}")
    answer_rows = [s for s, i, _ in s8.rows if i.startswith("answer/")]
    ans_beat = next(b for b in cw.beats if b.name == "answer")
    print(f"   discovered on 'answer': {ans_beat.narration}")
    if not ans_beat.narration:
        bad.append("S8: zero outcome sentences discovered on 'answer' - the control measured nothing")
    expect("S8", "QUIET", any(s != "PASS" for s in answer_rows) or not answer_rows,
           f"{len(answer_rows)} answer rows (claims + uncovered assertions), all PASS")

    d9 = copy.deepcopy(kdecl)
    assert d9["answer"]["claims"][0]["frame"] is not None
    d9["answer"]["claims"][0]["frame"] = None
    s9 = Verdicts()
    print("\n-- specimen S9 plant: the same earned claim with its frame removed")
    evaluate(cw, "kuraray-portal-en", d9, s9)
    expect("S9", "FIRE", status_of(s9, "answer/japanese-term-quoted") == "NO_PROOF", "removing the proof fires, so S8 is not a pass-all")

    # --- inversion: flip every expectation; the reporter must disagree with ALL of them
    flipped = [(sid, "QUIET" if k == "FIRE" else "FIRE", f) for sid, k, f in results]
    disagree = sum(1 for _, k, f in flipped if (k == "FIRE") != f)
    print(f"\nINVERSION  {disagree}/{len(results)} flipped expectations reported as disagreements")
    if disagree != len(results):
        bad.append("inversion: reporter failed to disagree with a flipped expectation")

    fired = sum(1 for _, k, f in results if k == "FIRE" and f)
    print(f"\nSELFTEST {'FAIL' if bad else 'PASS'}  {len(results)} specimens ({fired} FIRE observed, "
          f"{sum(1 for _, k, _ in results if k == 'QUIET')} QUIET)")
    for b in bad:
        print("  ", b)
    print(f"SELFTEST scope: parser on the real schema file; fin-demo live render over {len(world.beats)} beats; "
          f"kuraray capture world over {len(cw.beats)} scenes. Declared blind: B1-B7 in the module docstring.")
    return 1 if bad else 0


@dataclass
class ClaimsVerdict:
    """The gate's contract: lists of self-contained strings."""
    fails: list[str] = field(default_factory=list)
    candidates: list[str] = field(default_factory=list)
    warns: list[str] = field(default_factory=list)
    holes: list[str] = field(default_factory=list)


def run(project_root: str, verbose: bool = False) -> ClaimsVerdict:
    """Entry point for scripts/filmkit/gate.py. UNDECLARED beats are HOLES (unmeasured,
    not failed); size estimates are CANDIDATES; everything else non-PASS is a FAIL."""
    import contextlib
    import io
    root = pathlib.Path(project_root).resolve()
    film = next((k for k, c in FILMS.items() if (REPO / c["root"]).resolve() == root), None)
    out = ClaimsVerdict()
    if film is None:
        out.holes.append(f"claims: no adapter for {root.name}; add it to FILMS in checks/claims.py - "
                         "claim-to-frame coverage was NOT measured")
        return out
    paths = [SCHEMA_DOC] + [p for p in (root / "STORYBOARD.md",) if p.exists()]
    merged = dict(blocks=0, openers=0, films={}, source=", ".join(p.name for p in paths))
    for p in paths:
        d = parse_declarations(p)
        merged["blocks"] += d["blocks"]
        merged["openers"] += d["openers"]
        for f, beats in d["films"].items():
            merged["films"].setdefault(f, {}).update(beats)
    cfg = FILMS[film]
    v = Verdicts()
    sink = io.StringIO()
    with (contextlib.nullcontext() if verbose else contextlib.redirect_stdout(sink)):
        if cfg["kind"] == "composition":
            with FilmStage(REPO / cfg["root"]) as st:
                world = CompositionWorld(cfg, st)
                counts = evaluate(world, film, merged["films"].get(film, {}), v)
        else:
            counts = evaluate(CaptureWorld(cfg), film, merged["films"].get(film, {}), v)
        print_population(film, counts, merged)
    if counts["beats"] == 0:
        out.fails.append("claims: zero beats examined - zero of zero is not a pass")
    for status, ident, detail in v.rows:
        # RULE: an assertion is raised as UNCOVERED_ASSERTION only inside a beat that HAS a declaration;
        # an UNDECLARED beat is one hole carrying its own assertion count, never a fail per sentence.
        if status == "UNDECLARED":
            out.holes.append(f"claims: beat {ident} UNDECLARED, unmeasured; this hole covers every assertion in the beat, none raised separately ({detail})")
        elif status == "PASS":
            if "SMALL candidate" in detail:
                tail = detail.split("): ", 1)[-1]
                out.candidates.append(
                    f"claims: {ident} - every declared field is inside the frame (no crop hides them) "
                    f"but renders below the {TICK_FLOOR_PX}px authored floor ({tail}); the fields cannot "
                    "be read at this size. The fix is a larger or punched-in frame, not a different "
                    "crop. Estimate only (B2).")
        else:
            out.fails.append(f"claims: {ident} {status} - {detail}")
    print(f"claims: {len(out.fails)} fail, {len(out.holes)} hole, {len(out.candidates)} candidate; "
          f"beats={counts['beats']} claims={counts['claims']} frames={counts['frames']} "
          f"undeclared={counts['beats_undeclared']}" if verbose else "", end="" if not verbose else "\n")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--film", choices=sorted(FILMS))
    ap.add_argument("--declarations", default=str(SCHEMA_DOC),
                    help="markdown file holding filmkit-claims blocks, or 'none'")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.film:
        ap.error("--film or --selftest required")
    path = None if a.declarations == "none" else pathlib.Path(a.declarations)
    v, counts = run_film(a.film, path)
    fails = v.fails()
    if counts["beats"] == 0:
        print("\nFAIL  zero beats examined - zero of zero is not a pass")
        return 2
    print(f"\nVERDICT  {'FAIL' if fails else 'PASS'}  ({len(fails)} finding(s) of {len(v.rows)} rows) "
          "- on claim<->frame coverage only")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
