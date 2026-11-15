# STORYBOARD - Use case film for the Progress C-suite

Concept film. Work item `2d0c0949d232456583ec189c2852c04d`. Written 9 Oct 2026.

**Every shot is illustration-led; there is no type-only shot in the film.** Per
video-production skill 0c each shot carries the THING on screen, the ACTION it performs and
the RESULT the viewer sees while the line plays. On-screen copy stays under about 8 words per
element and never restates the line's noun-verb content (skill rule 17).

Grammar, stage, palette, type, transition rule and the engine-mark continuity convention are
inherited from `videos/sa-use-cases` unchanged. Nothing here invents a second visual
language.

## WINDOWS ARE MEASURED, 9 Oct 2026

Every window below is DERIVED from this film's own ElevenLabs takes, not borrowed.
Voice `ca-maria`, `eleven_v3`, eleven takes in `vo/`, measurements in
`vo/manifest.json` (md5 `23d559be9be0`). Window = lead (0.8s on the first shot, 0.5s elsewhere) +
measured take duration + a 0.35s tail on the LAST shot of each parent beat, with a
declared 3.0s end hold on B7.

**Total runtime 142.61s (2:22.6)**, inside the brief's 1 to 3 minute bucket.
**326 words over 131.36s of speech = 148.9 wpm measured**, spread 129.0 to 159.6.
Worst internal narration gap 0.84s against a 1.5s ceiling, with a planted 3s hole
proving the check can fail.

### The borrowed prediction, checked against the measurement

The provisional windows were computed from the sibling film's pace. That borrowed figure
went stale once mid-build, which is why it was replaced by a RANGE rather than re-pinned
to another point estimate. The range is kept here because a prediction nobody checks
afterwards is not a prediction:

| | Predicted from the borrowed range | Measured |
|---|---|---|
| Fastest case | 2:03.7 | |
| **Film-mean case** | **2:22.2** | **2:22.6** |
| Slowest case | 2:37.5 | |

The range held and its film-mean case was accurate to 0.4 seconds. Asserted by
`check_crossfile.py` section 8b, which fails if the measurement falls outside the range
or more than 5s from the mean case.

### Two takes were re-recorded on PACE grounds, not rewritten for length

The first pass measured two beats reading well above the film mean, and
words-per-sentence predicted it: **r = +0.54** across eleven beats, longer sentences
reading faster. Both were fixed with more sentence boundaries, never by compressing the
writing.

- **B1b read at 187.5 wpm**, 34.7 above the mean and the fastest in the film, on the beat
  that carries the opening pivot. **The fix restored the line I had cut.** "Now notice what
  each one does not do" was dropped to buy seven words back, and the measurement showed the
  beat was the one place in the film short of air. It now reads 153.3 wpm, at the film mean,
  and the restored line also resolves the B1b risk the lead had converted into a fresh-eyes
  question. That question is still worth asking, but it is no longer carrying the pivot
  alone.
- **B5b read at 165.4 wpm**, the hinge, and the beat I flagged for this before recording.
  Its closing 16-word sentence was split in two: "Which of those joins is worth closing.
  That is a decision this room gets to make." Now 158.9 wpm, 10 above the mean, which is
  deliberate - it is the CTA arriving and a touch of forward motion is right there.

**B2 is the slowest line at 129.0 wpm and that is correct, not an outlier:** it is a list
of corpus types doing its work through full stops. Recorded so the figure is not read as a
miss at the gate.

| # | Shot | Window (s) | Dur | Kind | Mech | Motif | Words | wpm |
|---|---|---|---|---|---|---|---|---|
| 1 | B1a three jobs | 0.00-8.48 | 8.48 | illustration | no | `m-3j` (shared) | 18 | 140.6 |
| 2 | B1b three gaps | 8.48-27.33 | 18.85 | illustration | no | `m-3j` gaps phase (shared) | 46 | 153.3 |
| 3 | B2 answers over documentation | 27.33-45.86 | 18.53 | illustration | YES | `m-rn` + `m-tq` (library) | 38 | 129.0 |
| 4 | B3 the live fact | 45.86-59.91 | 14.05 | illustration | YES | `ltc` (local, built here) | 35 | 159.1 |
| 5 | **B4a the letters beside the numbers (HERO)** | 59.91-73.29 | 13.38 | illustration | YES | `documents-to-rows` (local) | 33 | 153.7 |
| 6 | **B4b rows, and the gap (HERO)** | 73.29-85.82 | 12.53 | illustration | YES | `documents-to-rows` phase 2 | 30 | 154.1 |
| 7 | **B5a the count (HINGE)** | 85.82-96.00 | 10.18 | illustration | YES | `m-jy/count` | 22 | 136.4 |
| 8 | **B5b the turn (HINGE)** | 96.00-113.09 | 17.09 | illustration | YES | `m-jy/authors` | 43 | 158.9 |
| 9 | B6a three modes | 113.09-121.11 | 8.02 | illustration | YES | `m-boundary/modes` | 20 | 159.6 |
| 10 | B6b what is not claimed | 121.11-128.92 | 7.81 | illustration | YES | `m-boundary/notclaimed` | 17 | 146.6 |
| 11 | B7 the question | 128.92-139.61 (+3.0 hold) | 10.69 | illustration | no | stations + lockup | 24 | 146.3 |

**GATE RESULT, 9 Oct 2026, run with its controls first.** `video_gate.py`'s own
`eval_storyboard` returns **PASS** on this file: concept film, 11 beats, illustration-led
**100 per cent of 127.3s** against a 60 per cent floor, longest type-only run **0.0s**
against a 3.0s ceiling, **no mechanism beat unillustrated**.

Three controls were planted and run BEFORE the real board, and all three FAILED correctly:
(a) a sub-floor share, relabelling seven shots to type, returned 0.38; (b) an over-ceiling
type-only run, relabelling B6a and B6b, returned 14.95s with the share left legal at 0.88 so
only the run check could fire; (c) **the discriminator** - B5a alone relabelled to type, with
share 0.93 and run 8.88s both inside their limits, so the only thing that could catch it was
the mechanism-not-illustrated check, which did.

**Two things this result is NOT.** It is `eval_storyboard`, the pure evaluator, not a full
`video_gate.py` run, which needs a rendered master that does not exist yet. And the gate's
other storyboard check, which disproves a `kind` label by measuring per-shot motion, cannot
run without a master and is a **declared HOLE** until then, not a PASS. The share is also
measured over 127.3s of shot duration rather than the 130.4s film, because the 3.0s end hold
is not a beat.

---

## The writer lock, honoured

**I have created, edited and moved nothing in `videos/_motifs/` and nothing named `m-*`.**
The sibling owns that library until it reports done. Everything below is either a reuse of a
motif exactly as the sibling specified it, a precisely stated REQUEST, or a shot built inside
my own composition using the shared vocabulary without touching a shared file.

### Reused exactly as specified, no change asked for

- **`m-rn` and `m-tq` (library)** - B2. Compressed, see B2.
- **`m-jy/count` (sibling phase B)** - B5a. Verbatim through the thirteen-amber wave.
- **`m-boundary/modes` and `/notclaimed` (sibling)** - B6a and B6b. `/modes` was added for this film's three-panel row rather than leaving me to rebuild the hybrid geometry; `/notclaimed` is the surviving ghost tail, verbatim.

### Both requests resolved, 9 Oct 2026

**Request 1, `m-as` phase A with a suppressible left side: RESOLVED by the lock being
released for it.** The sibling's new spine has zero instances of that motif, so it would have
been building blind to my requirements and gating nothing. **I own it outright and built only
the half I need**, as `ltc` in `motifs-local/live-tool-call/`. The suppressible-left-side
request is moot: there is no contract page and no split answer card, because my B3 has no
document half.

**Request 2, a label slot on `m-jy`'s enlarged marker: NOT BROKERED, as I recommended.** The
tenant gate line is overlaid in my own composition. A host should own its own captions.

### One genuinely new motif, specified rather than drawn

**`documents-to-rows`** - B4, the hero. There is no existing motif for it: `m-jy/authors` draws a
join being authored but has no documents, no rows and no chart, and nothing in the library
turns unstructured content into structured data. Full specification below under B4.

**BUILT, 9 Oct 2026, per the lead's ruling: locally now, promoted to `_motifs/` once the
sibling reports done.** Same work, no collision, no waiting.

- `motifs-local/documents-to-rows/composition.html` - composition id `dtr`, class prefix
  `dtr-`, deliberately not `m-*` so it cannot collide with the locked set. 24.9s internal
  timeline across both phases, continuous so the B4a/B4b boundary does not break the picture.
- `motifs-local/documents-to-rows/README.md` - when to use, the seven variables, the event
  constants, and the promotion note (the id becomes `m-dr` in three places).
- `selftest_direction.py` - the no-fake constraint, below.

**The no-fake constraint is now machine-checkable rather than eye-only.** Every connector is
a row in a declared `CONNECTORS` table with `from` and `to`, so direction is data rather than
draughtsmanship; the composition THROWS at build time if any connector has
`from[0] >= to[0]`; and `selftest_direction.py` asserts on the source that every connector
runs outward, every join stops short of the chart's left edge at 1286px, the chevron is
anchored at the `to` end only, the guard is present, and the chart markup holds no citation.
27 checks, 0 failures. `--selftest` plants five positives (reversed connector, join reaching
past the edge, chevron moved to the `from` end, emptied table, removed guard) and all five
fire, with the clean source quiet as the negative control.

**It is still blind to four things and the eye check stays mandatory:** a rendered arrowhead
whose marker geometry points the wrong way, a path bowed backwards by its control points,
anything the host overlays on top, and every other shot in the film.

**`three-jobs-three-gaps`** - B1. The lead asked me to say what it must PERFORM rather than
draw it, so that is what the B1 entries below do.

---

## 1. B1a - three products, three jobs (0.00-7.66)

> "Progress OpenEdge holds the data. Progress Agentic RAG finds things and shows its working.
> Domo draws the numbers."

**THING.** Three panels across the navy stage, equal weight, equal size, **no shared
boundary around them** and no boundary around any pair. Labels in Progress Sans Display:
`Progress OpenEdge`, `Progress Agentic RAG`, `Domo`. Nine content tiles are already on stage
at frame zero, drifting, so the first frame is a designed poster rather than an empty field
(the sibling's B1 convention).

**WHAT IT MUST PERFORM.** Each panel does its own job once, in a single gesture, while its
clause is spoken. Not three icons appearing: three jobs being done.

- OpenEdge: loose records settle into ordered ranks and lock. Holding.
- Progress Agentic RAG: a question arrives, a few tiles light, an answer card forms and takes
  two source chips. Finding, and showing its working. The second half of that gesture is the
  pillar, and it is why this panel gets the only citation chips in the shot.
- Domo: values rise into a chart. Drawing.

**RESULT.** The viewer meets three peers doing three different jobs, and meets the answer
card and source chip vocabulary four seconds in, so B2 lands as recognition rather than
introduction.

**Binding.** The three panels never sit inside one boundary, because that composition asserts
ownership in a picture even where the voice does not (DESIGN.md, the Domo finding, and the
lead's ruling of 9 Oct 2026). No citation ever appears on the Domo chart, per B1b's own
finding. No reference to the acquisition in any form.

## 2. B1b - and the three gaps (7.66-22.49)

> "OpenEdge does not search a pile of letters. Progress Agentic RAG is not a charting tool.
> We found no Domo component that shows a citation. Each of those gaps is why a second
> product is in the picture."

**THING.** The same three panels, holding position.

**WHAT IT MUST PERFORM.** A **dead-grey hole with a SOLID edge opens inside each panel, one
per clause** (a hole is a void, not a join, so it takes none of the three reserved strokes), at
the place where that product's job stops, and the thing the panel cannot do is shown trying
to enter the hole and not fitting:

- Into OpenEdge's hole, a drift of letters and notes arrives and will not rank.
- Into Progress Agentic RAG's hole, a chart form arrives and will not render.
- Into Domo's hole, a source chip arrives and will not attach.

Then on the last clause, **a connector reaches from each hole toward a neighbouring panel and
stops short, unjoined.** Three reaches, no completions.

**RESULT.** The viewer sees three products that each stop somewhere, and sees the stopping
point as a shape rather than a sentence. The three unjoined reaches are the film's thesis
planted at 22 seconds, and the reaches are drawn in the LONG-DASHED AMBER that `m-jy` uses for
`NOT BUILT`, so B5 inherits the eye.

**This shot carries the narration's pivot, which the voice deliberately does not.** The
primer's "Now notice what each one does not do" was cut from the script to buy seven words
back; the holes opening IS that pivot. If the holes do not read, the pivot is lost and the
line must come back.

**That risk is now a MEASUREMENT, not a judgement to be argued at the gate** (lead's ruling,
9 Oct 2026). The fresh-eyes viewer is briefed with this specific question, asked after
watching B1 only and before seeing the rest of the film:

> Having watched just this opening, can you say that each product has a gap that the next one
> fills, without having been told so?

**If they cannot, the line comes back and I spend the seven words.** The budget has 48
seconds of headroom, so restoring it costs nothing but length. Recorded here so the
condition is explicit and expires visibly: this is the one place in the film where a cut
line is load-bearing on an illustration carrying it alone.

**Scope, and it matters.** The Domo clause is "we found no Domo component that shows a
citation", which is a finding about our search, not a flat absence claim about a third party's
product. The picture must match: the source chip fails to attach **to the component on
stage**, and no on-screen string asserts that no such component exists anywhere.

## 3. B2 - first shape: the question the help centre cannot find (22.49-37.84) - MECHANISM

> "First. A customer asks a question the help centre technically answers but cannot find.
> Progress Agentic RAG reads the manuals, release notes and closed tickets, and answers with
> citations. Available today. And the cheapest first step there is."

**THING.** Motif `m-rn` into `m-tq`, library geometry unchanged, shared card and stack
coordinates (card 830,330 at 730x460; stack x388, y400+66i). The Progress Agentic RAG panel
from B1 expands to fill the stage; the other two panels dim and hold at the edges, which is
the first rung of the ladder.

**ACTION.** `m-rn` runs compressed to about 8s of its 12.3s internal timeline: the question
pill enters, the passage field fills, the field collapses, survivors slide into the source
stack, the answer card writes itself. `m-tq` then runs compressed to about 6s: threads draw
from answer sentences back to source tiles, one per visible source chip, and the quality badge
rings in on its qualitative label. An `AVAILABLE TODAY` pill in green sets on the panel at
`Available today`.

**RESULT.** The first rung: one product, working alone, today. The badge carries messaging
house pillar 2 with no narration spent on it.

**`m-tq` ends on the BADGE, not on the refusal.** The sibling uses the same motif's refusal
end state as its climax. This film does not use that end state anywhere, and the two must not
be confused when the motif is shared.

**Corpus labels** are `Manuals`, `Release notes`, `Closed tickets`, the primer's own three.
The badge is qualitative and never a numeral (B34, Field Rule 5). Grounded in
`clinic-knowledge-desk` and `intel-co-intel`.

## 4. B3 - second shape: the live fact (37.84-51.99) - MECHANISM

> "Second. A customer inside your product asks what their open order position is. A live
> fact. Copying it makes it stale, so the Retrieval Agent calls your application's own tools
> instead, and nothing is stored."

**THING.** Motif `ltc`, built locally. The engine mark at centre, 280x216 at
centre 960,560, **crossfaded from B2's position without moving**, which is the sibling's
engine-continuity rule. A live system panel at frame right with three small moving rows so it
reads as RUNNING rather than stored, labelled `Your application`. The OpenEdge panel from B1
rises back in behind it: this is the second rung, and both products on it are ours.

**ACTION.** At `open order position` a question pill arrives at the engine. At `A live fact`
the right panel's rows move visibly, once, on their own. At `Copying it makes it stale` **a
ghost copy of one row detaches, drifts toward the corpus and visibly goes stale in flight,
greying and softening, then dissolves before arriving.** At `calls your application's own
tools` a labelled tool call draws from the engine into the panel and returns carrying one
value, which seats in an answer card with a green source chip.

**Then the tail, which is the part phase A does not have.** At `nothing is stored` the body
of knowledge is present at frame left and the returned value **passes over it without being
absorbed**: a dead-grey SOLID outline opens where it would have landed, holds for a beat, and
closes empty. A negative, performed.

**RESULT.** The viewer sees a live value answered without a copy being kept, and sees the
copy that was not kept. The staling ghost and the unfilled dashed outline are the two
gestures that make "copying makes it stale" and "nothing is stored" pictures rather than
assertions.

**No numeral in the answer card.** The value is a bar, not a figure: the real number is only
obtainable from a metered live call and a plausible-looking one would breach hard rule 3.
Labels: `Your application`, `Live`, `Not stored`. Grounded in `cartwright-freight-demo` and
`operator-fleet`.

## 5. B4a - the letters beside the numbers (51.99-65.06) - MECHANISM, HERO

> "Third. The one most people have not connected. Your system of record holds the numbers. It
> also holds the letters, notes and incident reports around them. Nobody puts those next to
> the chart."

**THING.** New motif `documents-to-rows`, phase 1. All three B1 panels are on stage for the
first time since B1: this is the third rung and it is the only one that crosses to a third
party. A chart at frame right with one point visibly higher than its neighbours. The system
of record at frame left.

**ACTION.** At `holds the numbers` rows flow from the system of record into the chart and the
chart draws. At `It also holds the letters` a second, untouched body of content surfaces
BENEATH the rows, in the same panel: letters, notes and incident reports as tiles, drawn in
the slate ink ramp rather than lit, so they read as present and unread. At `Nobody puts those
next to the chart` the letters **lift toward the chart and are stopped by the chart's own
edge**, settling back. The high chart point takes a small question mark.

**RESULT.** The recognition the whole film is built to produce: the explanation for the number
is already in the building, in the same system, and it cannot get to the chart. The question
mark on the high point is what makes the viewer want the next shot.

**Labels:** `Numbers`, `Letters, notes, incident reports`. Nothing names a real company and
no chart axis carries a figure.

## 6. B4b - rows, and the gap (65.06-76.84) - MECHANISM, HERO

> "Progress Agentic RAG can return structured rows from documents. Domo can join them to your
> tables on a shared key. The catch is the join. Today, the customer writes it."

**THING.** `documents-to-rows`, phase 2, continuous from phase 1.

**ACTION.** At `structured rows from documents` the Progress Agentic RAG panel reaches the
stopped letters and **each document yields one structured row**, a ruled bar with three
labelled key cells: `order number`, `part`, `supplier`. At `on a shared key` the rows travel
toward the chart's DATA side and a key column lights on the chart's own tables, the two key
columns aligning.

**Then the two things that make this shot honest.** One row's key cell **stays visibly empty**
and that row does not align: the key is in the tables, and on the document only if somebody
put it there. And at `The catch is the join` the rows stop short of the chart's data side with
**a gap left unbridged**, which takes an amber `ISV BUILDS` pill. At `the customer writes it`
the gap holds, unfilled, into the transition.

**RESULT.** The viewer sees the mechanism and the missing piece in one frame, and the missing
piece is amber, which is the state language B5 is about to multiply by thirteen.

**The join is NOT drawn in this shot.** `m-jy/authors` authors a join in B5b and showing the gesture
twice would spend the film's best moment early. B4b plants ONE gap; B5a pulls back to fifteen.
That scale change is the B4 to B5 transition and it is why the hero shape being one of the
thirteen reads structurally rather than needing to be explained.

**NO-FAKE CONSTRAINT, ship-stopping.** **Rows flow OUT to Domo's data side. Nothing reaches
INTO Domo, ever, in any frame of this shot.** The Retrieval Agent cannot query Domo today
(primer L101), so an arrowhead pointing the wrong way claims a capability that does not exist.
Every connector in this shot is checked for direction at the gate, by eye, on the delivered
frames. No citation appears on the chart. Grounded in `arag-taxonomy-builder` for the
extraction half; the Domo half is `ISV BUILDS` and the picture says so.

## 7. B5a - the count (76.84-85.72) - MECHANISM, HINGE

> "We counted. Fifteen applied patterns between these products. One available today. One not
> built. Thirteen need the customer to build the join."

**THING.** Motif `m-jy/count` (phase B), verbatim. A 5 x 3 field of fifteen seam markers, each a pair of
component blocks with the join between them left blank. Caption: `15 applied patterns`.

**ACTION.** The single amber gap from B4b **pulls back and becomes one marker in a field of
fifteen**, which is the transition. Then `m-jy/count` as the sibling specified it: all fifteen
present and unmarked; one join draws solid green and takes `AVAILABLE TODAY`; one stays blank
and takes a short-dash `NOT BUILT`, enlarging slightly rather than hiding; the remaining
thirteen take amber `ISV BUILDS` pills in one 80ms-staggered wave.

**RESULT.** The distribution, in one picture, with the not-built one named rather than buried.
Labels are the reference page's own strings. Source on screen:
`Progress Agentic RAG ISV architecture reference. Fifteen applied patterns.`

## 8. B5b - the turn (85.72-102.45) - MECHANISM, HINGE

> "Read that again. Thirteen joins, named and counted, in a reference a customer can price
> against. Not an unfinished product. A map of where the work is. And which of those joins is
> worth closing is a decision this room gets to make."

**THING.** `m-jy/authors`. The field of fifteen, holding.

**ACTION.** At `Thirteen joins, named and counted` one of the thirteen enlarges and **the join
itself draws between its two component blocks, stroke by stroke, as something being authored**
(the sibling's own gesture in `m-jy/authors`, reused exactly, and the only place in this film it appears). The
enlarged marker carries the lead's ruling as an overlay label in my own composition:
`The tenant gate. Every customer builds it, three times, three different routes.`

At `in a reference a customer can price against` the authored join resolves into a short
ruled line with three unnumbered segments, reading as scope rather than as a schedule.

At `Not an unfinished product` **the field does not change**, deliberately: nothing is struck
through, nothing is defended, and the only motion is the stage drift. The line refuses a
premise and the picture refuses to illustrate the premise.

At `A map of where the work is` the fifteen markers **re-lay into a map**: the grid loosens
into a routed plan with the thirteen amber joins as the routes between components, the counts
set beneath the three state labels, `1` / `13` / `1`. At `a decision this room gets to make`
three of the amber routes brighten in turn and hold, unchosen.

**RESULT.** The count stops being a disclosure and becomes an agenda. The tenant gate label
makes "a decision this room gets to make" concrete instead of abstract, at no cost in the word
budget. The three brightening routes are the CTA arriving one shot early, as a picture.

**The tenant gate line says the work exists and recurs, and nothing more.** No incident
detail, no filter behaviour, no disclosure language. That is the whole of what the lead's
ruling authorised and the whole of what appears.

**No struck-through glyph here.** The sibling strikes a tick through for its "Not a verdict";
this film's equivalent line is a refusal of a premise rather than a correction of a judgement,
and striking something through would illustrate the objection the line declines to answer.

## 9. B6a - where it runs (102.45-110.57) - MECHANISM

> "Three modes. Software as a service. Private cloud. And hybrid, where only inference and the
> index run in Progress's cloud."

**THING.** Motif `m-boundary/modes`, verbatim, compressed to about 8s from the sibling's 20.26s. Three
panels, each a boundary with one consistent object set: a corpus block, an index block, an
inference block.

**ACTION.** As the sibling specified: three empty boundaries draw; the first fills with all
three objects inside a single Progress boundary; the second with all three inside a
single-tenant boundary; the third draws TWO boundaries, the customer's at left and Progress's
at right. **The corpus block does NOT settle inside the customer boundary** (see the
correction note below). At `only inference` the
inference block travels across and seats. The index block follows and **SETTLES, with the
weight-and-rest gesture**, and a thin line links it back to the corpus it was derived from so
nobody reads the index as the corpus having moved.

**RESULT.** The viewer sees exactly which objects cross in hybrid.

**The index is on the PROGRESS side, in the picture and on screen.** The voice now carries
both "only" (the load-bearing word) and the index resting there. On screen:
`Three modes confirmed with Progress 8 October 2026.`,
`The index rests in Progress's cloud. Confirmed 9 October 2026.` and
`Where the source documents are stored: not stated.` plus `Not published.`

**Two dates, not one.** The earlier caption said 8 October only. The primer records the
three modes and the only-inference-and-index fact as confirmed on 8 October and the index
resting there on 9 October, so a single date was incomplete the moment the second
confirmation landed. Labels: `SaaS`, `Private cloud`,
`Hybrid`, `Progress cloud`, `Corpus`, `Index`, `Inference`. **`Your environment` is
removed from the label set**: naming a boundary as the customer's and seating the corpus in
it is the assertion this beat must not make.

### FACT CORRECTION, 9 Oct 2026, and it changed the picture more than the words

**"Hybrid keeps your documents with you" is not something Progress has told us.** What is
confirmed is that only inference and the index run in Progress's cloud, and that the index
rests there. That is a statement about what RUNS in Progress's cloud. **What executes
somewhere and what is retained somewhere are different questions**, and the primer now
marks the document-storage reading as ours rather than Progress's (`primer.md`, residency
section: "That is our reading, not something Progress has stated").

Two defects in this beat, and the second was the worse one:

1. **The voice implied it.** "Only inference and the index run in Progress's cloud" is
   literally true and confirmed. But "only X and Y are in the cloud" invites a listener to
   complete the thought with "so Z is not", which is the reassuring version arrived at by
   implicature rather than assertion. For an audience who might repeat it externally that is
   exactly what the hard limits exist to stop. **Fixed in the voice, not on screen**, because
   the implicature is created in the voice: the line now continues "The index rests there.
   Where the source documents end up, Progress has not told us." The clause was NOT deleted,
   per the lead's instruction - a viewer fills a hole with the reassurance by default - and
   b6a was re-recorded (20 words to 35, 154.4 wpm, the only beat re-recorded for this).

2. **The picture ASSERTED it.** The inherited spec seated the corpus block inside a boundary
   labelled `Your environment`. That is not an implicature, it is a flat claim about storage
   location drawn as a fact - the same class as the B4a connector that asserted a confirmed
   Domo path in a line weight. **A picture makes the claim whether or not the voice does.**

**What the corpus does instead, and it needs the shared library's new treatment.** The
corpus block sits ON the boundary line itself, belonging to neither side, carrying the
**state-of-our-knowledge** marker the lead has asked `film-sa-usecases` to add to the shared
library - a state of our KNOWLEDGE, not a state of the architecture, so it must not borrow
any of the three reserved architecture strokes. Labelled `Not stated`.

A corpus straddling the boundary is the honest image: it says we have not been told which
side this is on, which is the fact. Seating it on either side would be a claim, and leaving
it out would be the hole the lead warns a viewer fills with reassurance.

**DEPENDENCY:** that treatment does not exist yet. Until it lands, B6a cannot be built -
the same blocking state as `m-boundary` itself. I am not inventing a local version, per the
work item.

## 10. B6b - what is not claimed (110.57-117.40) - MECHANISM

> "Confirmed, unpublished, so it carries its date. On premises, offline and air gapped we do
> not claim."

**THING.** `m-boundary/notclaimed`, verbatim. Three ghost panels in the same boundary-and-objects
vocabulary at 35 per cent opacity in dead grey.

**ACTION.** The date strip sets beneath the three real panels on the first clause. Then
**three** ghost panels rise, one per phrase, labelled `On premises`, `Offline` and
`Air gapped`, each immediately taking a short-dash `NOT BUILT` outline, and all three
HOLD to the end of the shot. The `Self serve · published pricing` entry marker sets
beneath the three survivors, which carries the remaining half of messaging house pillar 3 at
no word cost.

**Three panels, and the count is load-bearing.** The voice names three and the picture must
carry three. `NARRATION.md`'s on-screen table listed only two until the sibling read my
narration against my shot table on 9 Oct 2026: a viewer reading the frame and not the
subtitle would have learned that two things are not claimed and inferred the third was, which
on a residency beat is the worst available inference. The count is now asserted by
`check_crossfile.py` check 4, which parses the list out of the narration rather than
hardcoding it.

**RESULT.** Three named absences stated and removed. An executive leaves knowing which three
words are not ours to say.

**INHERITED INSTRUMENT HOLE, and it applies here identically.** The strings `On premises`,
`Offline` and `Air gapped` appear on screen in this shot, inside `NOT BUILT` markers, by
design. They therefore **cannot** go on the gate's OCR forbidden-strings list, because OCR
cannot tell a negated label from a claim. The gate reports a declared HOLE and the check
becomes a named manual one: confirm by eye and by OCR position that each of the three appears
only inside this shot's window and only inside a `NOT BUILT` marker, and nowhere else in the
film.

## 11. B7 - the question (117.40-127.35, then a 3.0s hold)

> "Three shapes, each already running. Thirteen joins nobody has closed. The question is not
> whether this works. It is where we point it next."

**THING.** Stations and lockup. Three small station marks across the stage, one per shape,
each a miniature of its own shot: the lit answer card, the tool call, the rows and the gap.

**ACTION.** At `Three shapes` the three stations set in order, left to right, and the ladder
reads as a ladder for the first time: each station sits slightly higher and wider than the
last. **The field of real builds lights up behind them**, with its caption
`Field Kit published demo library, 9 October 2026. 21 demos, 13 industries.` At `Thirteen
joins nobody has closed` the thirteen amber routes from B5b return as a faint layer over the
stations. At `where we point it next` the stations hold and the closing line sets in Progress
Sans Display.

**End lockup**, declared as the film's only held beat, still subject to the 2.5s still-run
ceiling and kept alive by a light sweep and the stage hex drift. It carries the pointer the
lead approved on 9 Oct 2026: a line naming the primer as the document that holds the limits.

**RESULT.** The viewer leaves with three things they can name, a count, and a question
addressed to them. The breadth is FELT here rather than stated: the field lighting up is the
feeling and the caption is the evidence, which is why no breadth number is read aloud anywhere
in the film.

**One population per frame, named.** The library caption's 21 and 13 appear here. The estate
figures (60 targets, 39 probed, 37 answered) appear nowhere in the film, because a viewer who
sees two populations adjacent will divide one by the other.

---

## Transitions

Inherited rule: outgoing slides and blurs up 12 per cent while incoming rises in at the same
timeline position, 0.45s.

- Blur-slide handoffs at 22.49, 37.84, 102.45 and 117.40.
- **Engine-mark continuity crossfade at 37.84.** The mark does NOT move between B2 and B3,
  which is what makes the first two rungs read as one system rather than two diagrams.
- **Card-and-stack continuity inside B2**, `m-rn` ending in the geometry `m-tq` opens with.
- **The scale change at 76.84 is the film's key transition**: B4b's single amber gap pulls
  back to become one marker in B5a's field of fifteen. Not a blur-slide. The gap is the same
  object at two scales.
- **Panel persistence as the ladder.** The three B1 panels never fully leave: one lit in B2,
  two in B3, three in B4. Dimmed panels hold at the frame edges. This is the only new
  compositional rule in the film and it carries reach and work rising together without a word
  being spent on it.
- Loop closures: B1b's long-dashed amber reaches return as the thirteen `ISV BUILDS` joins in B5a, and its dead-grey holes return as `NOT BUILT` short-dashed in B5a and
  B6b; the three station marks in B7 are miniatures of B2, B3 and B4.

## Motion floors (gate-read)

Inherited from DESIGN.md: lufs -14, frozen-share ceiling 0.25, still-run ceiling 2.5,
shot-median floor 0.05, illustration-share floor 0.60, type-only-run ceiling 3.0s.
`typography.bare_stage` ceilings deliberately not declared, with the classifier's own blind
class (flat vector on a flat brand stage reads as type on a bare stage) recorded as a HOLE.

Every shot keeps continuous motion: stage hex drift plus at least one content element in
travel at all times. The only declared hold is B7's end lockup. Tool calls, citation threads
and authored joins are SVG strokes drawn by dashoffset, never a fade. No layout property
tweens, transforms and paint only, and never a wrapper's autoAlpha.

## Two motifs this film gates alone

`m-jy/authors` and `m-boundary/modes` are phases **the sibling's film does not render**,
stated in both READMEs. Its gate therefore does not cover them, and mine is the only gate
they ever pass through. **That is the one place in this build where a gap could hide**, so
both get an explicit eye-read at named timestamps on the delivered frames, on top of every
automated check, and the certificate says which figures came from a gate the sibling also
ran and which came from mine alone.

`/authors` exists because the lead asked for it specifically to protect this film's
B4 to B5a to B5b structure: plant one unbridged gap, pull back to reveal it as one of
fifteen, then author the join. That only works if the motif still authors a join, and the
join-authoring gesture had moved out of the count phase when the sibling's spine changed.

## Checks this file commits to, with their failure modes

0. **`check_crossfile.py`**, which reads NARRATION.md, STORYBOARD.md and STORYBOARD.json
   together and never one alone. 45 checks, 0 failures, exit 0; `--selftest` plants a
   positive into each check's population and all six fire. Re-run after ANY edit to any of
   the three files, because its whole purpose is catching the case where each file is right
   on its own terms and they disagree with each other.
1. **Re-derive every window from my own takes** and rewrite this file. Until then no
   duration-dependent verdict is a PASS.
2. **`video_gate.py --storyboard`.** DONE on `eval_storyboard` with three controls, all
   FAILING first, including a discriminator. The motion-based disproof of the `kind` labels
   is a declared HOLE until a master exists. Re-run as the full gate on the master.
3. **Direction check on every connector in B4b.** `selftest_direction.py` now covers the
   source: 27 checks, 0 failures, five planted positives all firing and the clean source
   quiet. **The frame-by-eye check on the delivered frames is still mandatory**, because the
   script is blind to rendered arrowhead geometry, bowed control points, host overlays and
   every other shot. This remains the ship-stopping one.
4. **OCR presence AND absence** at named timestamps: the three not-claimed strings appear only
   inside B6b and only inside `NOT BUILT` markers; `Progress Domo`, `formerly Domo` and any
   acquisition language appear nowhere; no percentage appears anywhere.
5. **No shared boundary around the three panels** in B1a or B1b, confirmed on frames.
6. **Narration gap ceiling 1.5s**, `silencedetect` at -45dB/0.4s with a planted hole proving
   the check can fail, and no ellipsis anywhere in the script (the sibling measured a 5.33s
   unbounded pause from one ellipsis in `eleven_v3`).
7. **Music-free and caption-free proven, not asserted**, by the PCM gap check with a planted
   bed proving it can fail.
