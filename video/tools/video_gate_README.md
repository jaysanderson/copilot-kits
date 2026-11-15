# video_gate.py - shared film gate

One instrument replacing the per-film gate/sweep/measure/motion_rank scripts.
Every check runs its positive AND negative control on every invocation; a check
that cannot run is a HOLE, never a PASS. Every figure is stamped with the md5
and duration it was measured on. Exit 0 all-PASS, 1 any FAIL, 2 any control
failure.

    .venv/bin/python scripts/video_gate.py master.mp4 [--design DESIGN.md]
      [--segments timeline.json] [--reference-strings ref.txt] [--social]
      --out report.json

**identity** - md5, bytes, duration, frames, fps, streams, v/a agreement; with
--segments, currency (segment sum or span closes on the file within 1.0s).
Controls: arithmetic, perturbed against the master duration.

**audio** - integrated LUFS and true peak (loudnorm at `-loglevel info` - load
bearing), head not digital zero, music-free: silent gaps at -45dBFS/0.4s from
decoded PCM in numpy, never silencedetect (its log vanishes under `-v error`).
Controls: silent clip fires; the master with a measured -27dBFS bed under it
returns 0 gaps.

**motion** - freezedetect n=-60dB d=1.5 (EOF-open runs closed), frozen share
<25%; perceptual motion in 0-255 grey levels @390px 10fps: longest still run
(<0.25) under 2.5s; with --segments, per-shot median ranking, top-3 stillest
named, floor 0.05. `motion_exempt: "<reason>"` on a segment declares a HOLE; a
stale exemption FAILs. Controls: planted frozen and oscillating clips (not
testsrc - too weak a control).

**flat-grey artefact** - largest connected flat neutral-grey region
(half-painted browser frames) per frame, ceiling 10%. Controls: planted block
fires; navy/white/tinted-grey look-alikes quiet.

**OCR forbidden strings** - runs when DESIGN.md has a "must not appear" section
(`- item` lines). Cell-segmented tesseract, 3-word Latin signatures. Blind
classes declared in the output: CJK (measured limit - verify source-side) and
small stylised low-light text; a clean run is "OCR clean, not eye-verified".
Controls: planted string fires; same frame unplanted quiet; a one-word
look-alike of a multi-word name (an invented institution name sharing its
first word) stays quiet. The plant is a full-width band anchored to the
frame's bottom edge, not an inset - `_cells()` segments by row across the
WHOLE frame width, so an inset band leaves the real frame's own content in
the untouched side margins, which can keep every row "non-blank" on a dense
frame and fuse the plant into one giant cell tesseract's single-line mode
reads as empty (found on opax-record, 5 Oct 2026: a 960x540 frame with no
genuine blank-row gap merged the whole height into one cell and the control
silently read back nothing).

**crop edges** - segments `shots[]` with `window`+`clip` (swept band, 9 samples
across the move) and `windows[]` with `still` (static): no edge through glyphs
(>=8 glyph-sized ink crossings). `photographic: true` declares the measured
hole. A `window` must be `{"form": "corners"|"xywh", "box": [a,b,c,d]}` - the
form is DECLARED, never inferred, because (x,y,w,h) and (x0,y0,x1,y1) are the
same four numbers whenever w>x and h>y (the ordinary case). A bare list or
missing form is refused per-window (named in `undeclared_window_form`,
excluded from `windows_examined`) rather than guessed - the old guess ("corners
if win[2]>win[0]") measured the wrong rectangle on opax-record's
fitted_windows.json and reported a clean run on geometry that did not exist
(found 5 Oct 2026; any crop.edges PASS recorded before this fix is unproven,
not confirmed clean). Controls: edge through type fires, edge in the gap
quiet, corners and xywh declarations of the same window resolve identically,
a bare/undeclared window is refused.

`edge_crossings()` only ever looks at the top/bottom edges, which rewards
the wrong remedy: a fitter can shrink a window until those edges clear the
text and the check goes green, even if the window is now narrower than the
text block, slicing every line mid-word at the LEFT/RIGHT edges (found live
on a citation beat, caught by eye, not by the gate). `narrower_than_block()`
catches this geometrically - it unions the x-extent of every ink cell
(`_cells()`, the OCR sweep's own segmentation) whose row-band overlaps the
window's y-range, and fails if the window does not cover that extent within
a small tolerance. A window whose y-range has no ink cell to compare
against is named in `narrow_crop_holes` and left unmeasured, never a silent
pass; the check's own `narrow_crop_blind_class` figure states that limit and
the companion risk (unrelated ink sharing a row-band could inflate the
measured block - mitigated by, but not proof against, `_cells()`'s own
column-gap separation). Controls: a window narrower than its text block
fails, the same window widened passes, and a deliberately tight crop on a
short single line that genuinely fits (the legitimate look-alike) passes.

**reference echo** - segment texts vs ref.txt; verbatim, 4-word run,
10-CJK-char run, 0.6 overlap. Controls: planted lift fires; unrelated Japanese
quiet.

**typography on bare stage** - share and longest run of flat frames carrying
text (top2bin16>=0.78). Verdict only when --design declares
`type-only-share-ceiling` / `type-only-run-ceiling` (`social-` variants with
--social); else figures + HOLE. Blind class: flat-UI app footage reads as type.

Floor overrides: `key: value` lines in DESIGN.md (FLOOR_KEYS).

## storyboard.illustrated (added 4 Oct 2026, GM concept-film directive)

Input: `--storyboard STORYBOARD.json` = `{"film_type": "concept|demo|hybrid", "beats":
[{"id","start","dur","kind": "illustration|plate|type|card", "mechanism": bool}]}`.
Asserts, for a concept film, illustration-led runtime >= 60% (`illustration-share-floor`),
no type-only (type/card) run over 3.0s (`type-run-ceiling`), every `mechanism: true` beat
declared `illustration`, AND cross-checks each declared illustration beat against the
measured per-frame motion from `motion.perceptual` (a beat labelled illustration whose
median frame difference sits under `shot-median-floor` FAILS - the label is a claim, the
frames are the fact). Controls: a planted 5s type run / 40% share / typeset mechanism must
FAIL; a compliant storyboard must PASS. No manifest = HOLE. Blind class: it reads the
storyboard's own declaration of KIND and only disproves it by motion, so a moving but
meaningless illustration (motion for its own sake) passes here and is caught only by the
fresh-eyes viewer's "would you keep watching" question.

## Changes of 9 October 2026 (university hybrid film)

Five defects, four of them in the direction that flatters a result. Found by running the
instrument against a new film's own files instead of assuming it read them.

**`design.floors` (new check).** Every floor the author DECLARED was read, and the ones
that were not are NAMED. It exists because of the worst of the five: `parse_design()`
called `float()` on the raw captured value, so a floor declared with its unit -
`type-only-run-ceiling: 3.0s`, which is correct practice because the SOP requires the unit
to be stated in the figure - raised `ValueError` and **killed the entire gate on a
traceback before a single check ran**. Both concept films in flight that day declare
exactly that, so `video_gate.py --design <either DESIGN.md>` could not run at all. A unit
suffix (`s`, `ms`, `%`, `px`, `fps`, `LUFS`, `LU`, `dB`, `x`) is now stripped and read;
anything still unparseable is a FAILED check naming the key and value, never dropped and
never fatal. Controls: `2.5s` reads as 2.5; `abc` is named. **No `--design` = HOLE**, since
a run with no declared floor applied none.

**`illustration-share-floor` and `type-run-ceiling` were missing from `FLOOR_KEYS`.**
`eval_storyboard()` had read both since 4 Oct but `parse_design()` only ever parses the
keys in that tuple, so declaring either in a DESIGN.md was a **silent no-op** and the
default was used. Both in-flight films happened to declare values equal to the defaults,
so no verdict of theirs changes - but a film declaring anything else was unprotected.

**The illustration-share assertion was scoped to `film_type == "concept"`.** A hybrid
film's share was reported and never asserted, which is precisely the hole on a film whose
illustrated halves are the risk. The share is now asserted whenever a floor is explicitly
DECLARED, whatever the film type; the concept default of 0.60 is unchanged.

**`mechanism: true` implies `kind: "illustration"` had no hybrid branch.** On a hybrid the
correct treatment for a mechanism beat is often real footage - that is what makes it a
hybrid - so `plate` is now permitted for `film_type: "hybrid"` and only `type`/`card` fail.
Before this, a hybrid storyboard declaring the truth about its own footage beats failed,
and the only route to a green gate was to mis-declare `mechanism: false`. Controls: a
hybrid mechanism plate passes, a hybrid typeset mechanism beat still fails.

## storyboard.interiors (new check, 9 Oct 2026) - STATIC, and it runs before any render

The rejected concept film's own diagnosis: *"I authored boundaries and labels, and in about
a third of the shots I never authored the interiors."* Ink can only catch that after a
render; this catches it in the storyboard. It is the cheapest instrument of the set and the
earliest.

Reads a per-beat inventory on each `kind: "illustration"` beat:

    "elements": [{"id","kind","count","must_read"}],
    "child_elements": <total, asserted equal to the sum of the counts above>,
    "subject_at_t0": ["ids present at the beat's own t=0"],
    "must_read": [...]  |  "must_read_none_reason": "..."

FAILs on: zero child elements; a `child_elements` total that contradicts its own inventory
(this caught three hand-typed counts on the university storyboard - 38 written as 41, 184 as
159, 31 as 30, and **every one made an interior look differently populated than it was**);
every declared child being a boundary or a label, which is a populated beat with no
interior and the nearest legitimate look-alike; and an empty `subject_at_t0`, which is
GRAMMAR rule 7 (a motif has its subject on screen from its own t=0).

**A beat with no inventory is a HOLE, never a pass and never a FAIL.** Storyboards authored
before this schema carry no `elements`, and failing them would be a finding about the schema
rather than about the film. **Zero examined out of a non-zero illustration population is
also a HOLE**, which is why this is a separate check: folded into `storyboard.illustrated`,
"interiors measured on 0 of 18" read as a PASS, and zero of eighteen is further from a pass
than zero of zero. Controls: six, one negative (a populated self-consistent beat stays
quiet) and five positive, each plant differing from the quiet specimen.

Blind classes, declared, and the second one came from `film-sa-usecases` after it hit the
defect in its own film:

1. **It reads the storyboard's own DECLARATION.** A beat that declares forty tiles and
   renders three passes here. Both concept films are planning to GENERATE their counts by
   querying the rendered DOM instead of reading their own source, which closes this and is
   the better method - the author's source is exactly where the author repeats the author's
   error. A DOM-derived count carries its own declared limit: it measures what the
   composition CREATES, so an element created and then hidden still counts.
2. **CHILDREN EXISTING AND CHILDREN BEING INSIDE THEIR PARENT ARE DIFFERENT FACTS, and this
   check only ever sees the first.** On the `sa-use-cases` build, eighteen tiles rendered
   OUTSIDE both their containers, leaving both boxes visibly empty, while an ink measure
   read 0.1196 and a glyph measure read 20px and **both PASSED**. A full, correct, declared
   inventory would also have passed. The cheap closure is a containment assertion at render
   time - every declared child's rect inside its declared parent's rect - which is a
   different instrument from this one and belongs beside the render, not in the storyboard.

Neither blind class is reduced by a green verdict here, and **the eye-read is a gate step in
its own right that this check never retires**: ink catches emptiness, not wrongness, and a
populated, legible, high-ink frame saying the WRONG thing passes every measure in this file.

## `--storyboard-only` (new, 9 Oct 2026)

    .venv/bin/python scripts/video_gate.py --storyboard-only \
      --storyboard STORYBOARD.json --design DESIGN.md --out report.json

Runs `design.floors`, `storyboard.illustrated` and `storyboard.interiors` with no master
file, so a storyboard can be failed BEFORE anything is built. The motion cross-check cannot
run and says so. Same exit convention as the full gate, including "zero checks produced a
PASS verdict - zero of zero is not a pass".

**Open, for the lead:** a HOLE exits 0 in both paths. That is the documented convention in
this file, and it conflicts with the CLAUDE.md line "exit 0 only on all-PASS, and HOLE
(never PASS) for anything it could not measure". Left as the pre-existing behaviour rather
than changed under two films in flight; a HOLE currently needs a human to read the summary.
