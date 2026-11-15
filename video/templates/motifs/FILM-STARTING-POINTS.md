# Film starting points

Five rules that a film build BEGINS with. They are not findings to arrive at.

Derived from the Kuraray research-portal pair (17 Oct 2026), where they took nine
rounds and three paid asks to reach. The first cut of that pair had no product
motion, no function seen working, and an authored diagram standing in for the
library. That was not a gating failure - the gates did the work the build should
have done. These five exist so the next build does not repeat it.

Sibling of `GRAMMAR.md`, which governs what a drawing may assert. This governs
how a film of a real product is built and how its numbers are trusted.

---

## 0. Measure the DELIVERED artifact, not the plan that produced it

**This one sits above the other four, because they are craft and this one decides
whether you can trust your own numbers.**

A film pipeline is a chain of representations - scene spec, storyboard, retimed
board, rendered frames, encoded mp4 - and every step rewrites the one before it.
A measurement taken anywhere but the end describes something you are not shipping.

The instance: a check for "does this cut land while the picture is still moving"
compared each capture clip's length against its beat's duration, read from the
storyboard. But `retime.mjs` rewrites every beat afterwards from the measured TTS
audio, so those were PROVISIONAL durations. The check called four Japanese beats
short when exactly one was, and missed two English ones.

**A proxy that errs in both directions at once is worse than one that errs
consistently, because neither direction warns you.** A check that always flatters
can at least be corrected for; one that is wrong both ways looks like signal.

So: name the measurement layer in every verdict, and prefer the layer closest to
the thing you hand over. Where a cheap upstream proxy is genuinely useful, mark it
ADVISORY in its own output and say which downstream check is binding.

Corollary that is easy to miss: this also applies to your own measuring code. A
rewrite of an instrument IS a change to the measurement - re-prove it against a
case whose answer you already know.

## 1. Drive the interaction, and capture per step

A walkthrough IS the transitions. A beat built from a still screenshot of an end
state shows that the product HAS a feature; it never shows the feature working.

**No beat that shows a product function may be a static end state.**

Practically: drive the real UI, capture one frame per driven state, and keep the
two provenance classes distinct on the certificate -

- **real time** - each frame held for the interval it actually represented
  (ffmpeg concat demuxer with per-frame durations)
- **driven step by step** - one screenshot per driven state, played at a chosen fps

Never blend them silently. Head and tail holds use `tpad=stop_duration=N:stop_mode=clone`,
which clones a real frame; never an invented still.

And let the move finish before you cut. A beat carrying a clip must outlast that
clip's movement, or the cut reads as a mistake. An authored camera push is a
different class from the product's own motion - it may run to the cut, and it is
excluded BY NAME in the check's output rather than silently.

## 2. Check a citation marker's target before building a beat on it

Enumerate first, compose second. A marker that looks like proof may resolve to a
source the product itself badges `weak match`, or to a passage that does not carry
the figure in the sentence the marker sits on.

If the target does not support the claim, the beat does not get built. Do not go
hunting for a second option.

## 3. Compose the frame, do not crop the live page

Cropping a live page means the page's chrome, rails, footers and customer marks
decide your framing, and they move. Compose the frame and capture into it.

Clip by GEOMETRY, never by masking. A mask that matches neither real state is not
anonymisation - if a surface shows "Operator ✓" to one viewer and "Operator key"
to another, a frame showing neither is less honest than either.

Pick the browser width where the layout reflows in your favour rather than fighting
it: on the Kuraray portal, 1100px collapses the source rail and removes the customer
mark from every ask frame, which no crop could have done cleanly.

Pin the page state you are asserting. Playwright's own `.click()` auto-scrolls to
focus an off-screen element, so drive via DOM `.click()` plus an explicit
`window.scrollTo(0,0)`, and REFUSE any frame whose `scrollY` is not what you expect.

## 4. Evidence-class text is never the smallest type in the film

Audit legibility BY CLASS OF CONTENT - claims, qualifications, evidence - never as
an aggregate, because the failure correlates with the class. The asymmetry is the
finding: if headlines and reassuring badges are legible while figures, citations,
disclosures and qualifications are not, that is what a procurement team catches a
vendor on.

Include text inside CAPTURED PLATES in the population. A legibility floor applied
to authored type cannot reach text inside a recording, and the evidence usually
lives in the recording. No font size reaches into a plate - the remedies are plate
scale and a punch cropped to the phrase.

Remedy ladder, in order: what cannot be PUNCHED is SET as a stage card; what cannot
be SET is SPOKEN. Put a caveat in the voice only when the picture at that timecode
is not asserting something else.

---

## Instruments built for this class

All four are in `videos/kuraray-portal/`. Each carries its own controls and refuses
to report clean when a control fails.

| instrument | measures | controls |
| --- | --- | --- |
| `cut_settle.py` | settle before every cut in the DELIVERED mp4; PSNR between consecutive frames, >=50 dB frozen | frame against itself; motion present somewhere; a still built from the film's own pixels must read fully frozen; still-under-push beats excluded by name |
| `clip_motion.py` | the timestamp after which each capture clip never moves again - the number a beat must outlast | every clip is a driven interaction so each must show motion; a frame against itself must read frozen |
| `silence_motion.py` | every silence run, labelled MOVING / part-moving / STILL underneath | synthetic 2s digital silence must be detected; the film must not read as silent throughout |
| `tofu_check.py` | missing-glyph (tofu) boxes by connected-component modal-size dominance | the real broken preview fires; the real clean preview stays quiet |

**Not yet reusable, and this is the honest state.** Per CLAUDE.md's own rule that a
fixture living in one build's folder is not shared, these belong in the root
`scripts/`. Three of them are coupled to this project's layout and would need a
small generalisation pass first:

- `cut_settle.py` and `silence_motion.py` read `w<lang>/storyboard.json` and expect
  scenes with `start`, `end`, `capture` and `focusKeyframes`
- `clip_motion.py` globs `captures/*.mp4` relative to its own directory
- `tofu_check.py` resolves its two controls relative to its own directory

`tofu_check.py` is the closest to generic and the most broadly useful - OCR cannot
detect tofu at all, returning zero characters for a broken preview and a clean one
alike, so nothing else in the factory can currently see this defect.

## Two traps worth carrying forward

**ffmpeg `-ss` before `-i` snaps to the nearest keyframe**, so any timecode quoted
from such a frame may be wrong by up to a second. Put `-ss` AFTER `-i` for anything
whose timecode you will cite, and say which form you used.

**An assertion that each edit applied cannot show the edit LIST was complete.**
Nine replacements with nine passing assertions still left the old term in the
opening title card - the first string a viewer meets. The per-edit assert answers
"did my change land"; only a sweep for the OLD term across the whole authored
population answers "did I find every target". It costs one command. And note which
instance survived: the explicit restatement got corrected, and the one sitting
where it reads as background did not.
