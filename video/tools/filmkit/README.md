# filmkit - the pre-render film gate

```bash
.venv/bin/python scripts/filmkit/gate.py <project-dir>        # one command, one verdict
.venv/bin/python scripts/filmkit/gate.py <project-dir> -v     # every ok line too
```

Run it the moment compositions and captures exist, and again after any change.
Nothing needs to be rendered.

## Why it exists

The cost of a film here is **rounds**, not hours: render, gate, cold viewer, fix
list, re-render. The research portal walkthrough took seven rounds to reach a
viewer's YES. The Fin-demo showcase came back from two independent cold viewers
with a ten-item list and a verdict of NO, and **every one of those ten items was
reachable before a single frame existed**:

| viewer's finding | what it actually was |
|---|---|
| green rings on empty checkboxes | marker coordinates hand-authored instead of derived from the extraction result |
| "8 applications" against a voiced seven | a figure on a capture contradicting the narration |
| two unexplained confidence numbers | two figures for one subject with nothing distinguishing them |
| soft, hard-cropped screenshots | a 1920x1080 capture drawn 2447px wide - 1.27x |
| callout pills occluding a validation note | rectangle arithmetic |
| four outcome pills with no result frame | a claim with no proof frame |
| three fields TRUE, one visible | a crop that does not contain the data the claim rests on |
| bare frames at handovers | a timeline reading |

Meanwhile the instruments that catch these were being rebuilt per film:
`fin-demo-showcase` holds **24** `tools_*.py` written in one evening,
`videos/kuraray-portal` five more, and `videos/sa-use-cases/checks/` carries a
**copy** of `scripts/frame_measures.py` rather than an import. Thirteen of those
24 are pre-render instruments, so the capability existed in exactly one project
and protected exactly one film. A fixture that lives in one project's folder is
not shared. This one lives in root `scripts/`, which hard rule 16 backs up.

## What it cannot do

It cannot tell you whether the film is any good. Pacing, drift, whether the idea
lands, whether a room keeps watching - those need a finished cut and fresh eyes.
**The point of this gate is that a cold viewer never spends a round on a crop.**

## The two primitives

Every check is a function over one of these. Import them; never copy them.

**`stage.py`** - mount a composition, seek its paused timeline, read what renders.

```python
import sys; sys.path.insert(0, 'scripts')
from filmkit.stage import FilmStage

with FilmStage('fin-demo-showcase') as st:
    for c in st.compositions():
        st.mount(c)
        d = st.duration()
        for tb in st.text_boxes(d * 0.5):
            print(tb.text, tb.at_delivery(1920))     # glyph height at 390 CSS px
        for ib in st.image_boxes(d * 0.5):
            print(ib.src, ib.upscale)                # >1 means enlarged
        st.visible_strings()                         # union across the timeline
        st.beats()                                   # the REGISTERED timeline
        st.callback_beats()                          # beats dead on a seek
```

Geometry is after layout and after every transform, at device scale 1, so a CSS
pixel is a rendered pixel. A failed asset request is fatal, never a warning: a
frame missing its images measures cleaner than it is. Every instance gets a
private temp directory, so any number of checks may run against one project at
once.

**`plate.py`** - read the text *inside* a captured plate, in composition
coordinates.

```python
from filmkit import plate
ok, found, missed = plate.ocr_control()              # prove the OCR path first
rows, unresolved = plate.plate_words(st, 'fin-demo-showcase', t)
```

This exists because no font-size rule reaches into a screenshot, and the
recorded half of a film is where the evidence and the qualifications live. The
asymmetry has been found on three films now: headlines legible, evidence and
disclosures not. `09-the-output.html` - the Fin-demo payoff beat - carries **zero
authored text and one image**, so its entire proof is pixels an authored-type
check cannot see.

## Rules for a new check

1. Put it in `checks/`, expose `run(project_root, verbose=False)`, return an
   object with `fails` and optionally `candidates`, `warns`, `holes`. `gate.py`
   discovers it automatically and reports a module it cannot run as a **hole by
   name** - never a silent skip.
2. **Print the population count.** Zero of zero is not a pass.
3. **Declare by name what the check cannot see.** A declaration converts a
   silent hole into a stated one. It does not fill it, so say what will.
4. **Ship specimens, each declaring FIRE or QUIET, each derived from an observed
   defect** - never from what a failure might look like. Include the nearest
   legitimate look-alike as a discriminate control. When a check over-fires,
   narrow the pattern, never the population: excluding a file to silence a
   pattern removes the population the check exists to cover.
5. **Where a check must estimate, report a CANDIDATE, never a FAIL.** Exact
   arithmetic fails; a judgement gets printed and counted for a human.
6. **Prove it fires on the real defect it was written for**, not on a synthetic
   input. Where the real pre-fix artifact is unreachable, record the firing run
   and say a synthetic control carries it forward.
7. A check that prints FAIL without failing the run is decoration. Route every
   verdict through one function and exit non-zero.
8. **Sample a moving thing densely.** A plate that scales across its beat has a
   worst case at one instant; three fixed fractions missed a 1.27x enlargement
   that sits near t=0.75.

## Lessons already paid for, recorded in the code

- `capturefidelity.py` documents three defects found in its own first version by
  reading its output against the film: fixed-fraction sampling missing a moving
  worst case, failing an ordinary card edge that needed an eye, and reading
  elements mid-transit as clipped.
- `stage.py` documents the harness collision: a fixed filename in the project
  root meant four agents running stages at once deleted each other's harness.
  The discharge for shared mutable state is isolation, not a convention about
  who cleans up.
- `plate.py` declares tesseract's blindness to white-on-green and
  orange-on-cream, and that `4 / 4` fails its own positive control. A pass means
  nothing was **recognised**, never that nothing is present.
