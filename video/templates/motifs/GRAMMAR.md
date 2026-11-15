# The shared visual grammar

**Canonical. This file is the grammar; a film's DESIGN.md points here rather than
restating it.** Both the solution-architect film (`videos/sa-use-cases`) and the
executive film (`videos/exec-use-cases`) compose from these rules, so a change here is a
change to both and is reported to the lead.

Moved out of `videos/sa-use-cases/DESIGN.md` on 9 Oct 2026, when rule 6 was added: a
treatment needed by both films should not live inside one film's own file.

---

## 1. A product is a solid object with a verb it performs

Three objects, and only three, each identifiable by silhouette alone at phone width:

- **OpenEdge** - a record store. A stack of ruled rows in a closed frame. Verb: HOLDS,
  rows settle and stay put.
- **Progress Agentic RAG** - a reader. A rounded card that takes documents in and emits a
  lit passage with a thread back to its source. Verb: FINDS AND SHOWS ITS WORKING.
- **Domo** - a chart. An axis with bars. Verb: DRAWS, bars rise to height.

A product never changes silhouette between shots or between films.

## 2. A join is a LINE BETWEEN two product objects, and the stroke IS the state

**Three states of the architecture, drawn as strokes. A fourth LABEL that is not a
state.** Four labels, three states, matching the reference and `primer.md:21`:

| Stroke | `stroke-dasharray` | State |
|---|---|---|
| solid | none | AVAILABLE TODAY |
| long dash | `20 12` | ISV BUILDS |
| short dash | `6 10` | NOT BUILT |

**The scales are measured, not chosen, and they are a library constant.** On a 1920px
frame downscaled to a 390 CSS-px phone, a stroke's ON element has to survive as at least
about 1.5 DEVICE pixels or it smears into a continuous line. `NOT BUILT` was `3 9`, whose
ON element resolves at 0.61 / 1.22 / 1.83 device px at 1x / 2x / 3x - so it only read as
broken at 3x, and below that the only thing separating it from `ISV BUILDS` was being
dimmer and a different colour, which is not a separator when the grammar's whole point is
that the STROKE carries the state.

`6 10` resolves at 1.22 / 2.44 / 3.66 and separates from the long dash by an ON ratio of
3.33 and a period ratio of 2.00. `8 12` was ruled first and then changed: it clears the
floor at 1x too, but at an ON ratio of only 2.50, and **1x was already a two-state
grammar** - at 1x a 120px swatch is 24 device pixels of line and shows no pattern
difference at any scale. Paying separation at 2x and 3x to rescue a density where the
grammar does not work anyway is the wrong trade.

**It reads as a SHORT DASH at desktop, not a dot, and that is accepted.** A true dot
cannot survive the downscale. The grammar names the STATE and not the shape, so nothing
is renamed - but do not describe this stroke as "dotted" anywhere, because a rule whose
prose stops matching its artwork is how `3 9` comes back.

**Separation is fixed by the authored geometry and cannot change with DPR.** Both scales
shrink by the same factor, so the ON ratio and period ratio are identical at 1x, 2x and
3x. DPR decides whether each stroke RESOLVES; it can never decide whether two of them
SEPARATE. That makes the separation check a one-time authoring assertion rather than a
per-render one, and it retires "do they converge at 2x" as a question that cannot have a
yes.

Stated limit: at 1x the grammar is two states, continuous and broken. 1x phones are
effectively extinct and this is recorded rather than chased.

Scope of the measurement: the 120px legend swatch, which is the worst instance. Field
joins are 588px, nearly five times longer, so they are substantially better off and were
not separately measured.

The three strokes are **reserved**: nothing else in either film uses them, so a dashed
line is never decoration.

**UNCONFIRMED is not a fourth stroke.** It is a state of our KNOWLEDGE, not of the
architecture, and it is drawn as a question-mark glyph set ON the line, over whatever
stroke the architecture actually has - or over no stroke where even that is unknown.
Wherever the legend appears it writes in **two groups separated by a rule**: the three
strokes together, then the rule, then UNCONFIRMED beneath it.

An architect reads "nobody has established this" differently from "this is not built". A
test you have not run and a seam nobody has joined are different problems with different
costs, and the rule in the legend is what stops a film collapsing them.

## 3. Green is the platform's. Amber is the ISV's own code

The single colour decision the films rest on, because the thesis is that the joins are
yours: every time amber appears the viewer is looking at their own work.

- green `#008963` structure, bright green `#00B563` live accent
- **amber `#C9821F` ISV-owned**, `#E09A33` its lit form
- dead grey `#6B7280` outside a boundary, or not reached

## 4. A gate is a gap in a boundary with a token passing through it

- an **OPEN** gate is a boundary whose stroke is visibly **BROKEN** - and when the break
  is a silent permissive failure, nothing turns red and nothing stops
- a **REFUSAL** is a boundary that stays closed with a token stopping dead against it
- a gate that has **never been tested** is drawn with its stroke present but PALE

## 5. Data that crosses a boundary TRAVELS

Drawn as an object moving across, with the boundary it crosses visible at both ends of
the move. Nothing crosses by fading, and nothing important changes state off screen.

## 6. An object whose state we were never told is UNRESOLVED on screen

**Added 9 Oct 2026. Rule 2 gives the knowledge-state glyph to a JOIN; this gives it to an
OBJECT, which is what rule 2's own logic requires once the stroke is the state.**

Where a product statement covers what RUNS somewhere but not what is RETAINED somewhere,
the retained thing's position is not ours to draw. So:

- the object is drawn **OUTSIDE every boundary**, in the neutral stage that belongs to
  nobody, carrying the UNCONFIRMED question mark
- it is **never drawn moving toward a boundary**, because a direction is a claim. No
  drift, no lean, no settle
- it **keeps whatever derivation lines are real** - something genuinely built from it
  still draws from it, which is how the shot stays informative rather than merely blank
- the boundaries themselves stay drawn and closed. What is unresolved is MEMBERSHIP, not
  the existence of the boundary

**Why this rule exists, recorded so it is not softened back.** "Hybrid keeps your
documents with you" is an inference from the word "only" in a confirmed statement about
what runs in Progress's cloud. It is not something Progress has stated. It reached a
pillar's approved line - the one place a claim is spoken aloud to a buyer - and survived
two correction passes, because it is the half of a corrected fact that sounds safe.
Canon: DAM fact `deployment_modes` v6, UNCONFIRMED (a).

**Dropping the object instead is wrong**, because a viewer fills the empty space with the
reassuring assumption. Drawing it hedged ("probably stays") is worse than either. The
honest frame is the open question, and for a solution-architect audience the open question
IS the payload: they are the person who will be asked both what executes somewhere and
what is retained somewhere, and those are different answers.

### A worked NON-example, because this rule is easy to over-apply

**An object whose location IS stated does not get this treatment, even when it moves
between boundaries.** The executive film's `documents-to-rows` lifts documents toward a
chart. That looks like a rule-6 violation and is not: those documents are in the system
of record, their location is a stated fact, and the gesture is about REACHABILITY, not
membership. Rule 6 is about an object whose position nobody has told us, not about any
object near a boundary.

The test is one question: **has anyone stated where this thing lives?** If yes, draw it
where it lives and move it freely. If no, it goes in the neutral stage with the question
mark and it does not move. "I checked and it is fine" is a different claim from "I did
not look", and that film checked.

**Current instances** (keep this list current - it is how a later pass finds every place
the treatment is load-bearing):

| Where | Object | What was never stated |
|---|---|---|
| `m-bd/hybrid` | the source documents | whether they stay with the customer in hybrid |
| `m-bd/modes`, private-cloud panel | the inference block | where inference runs in private cloud (canon (c)) |
| `m-bd/modes`, private-cloud panel | the boundary itself | what a private cloud boundary is and who operates it (canon (d)) |

## 7. A motif has its subject on screen from its own t=0

**Word events drive CHANGES to the subject, never its first appearance.**

Measured 9 Oct 2026: eight of eighteen shots opened on a blank stage for 0.4s or more,
**about 10.7 seconds across the film, 6.6 per cent of its runtime**, with one shot
opening on 2.7 seconds of bare navy while the voice was already talking. Every instance
had the same cause - the motif keyed its first element to its first word event, and a
word event can be seconds into a beat because the speaker has to reach that phrase.

So a motif opens with its subject already present, or arriving inside about 0.2s. The
first word event then changes it: lights it, moves it, labels it, breaks it. The viewer
meets each new idea at the moment the shot starts, which is when they decide whether to
keep watching.

**This is also why a per-shot measure must sample openings.** A measure taken at 25, 50
and 75 per cent of a shot cannot see a shot that opens empty, and will report a film
with ten seconds of blank stage as passing. Sampling is derived from where the defect
class lives, not from convenient fractions.

## 8. An element goes into its phase's CLEAR in the same edit that adds it

**Three times in one file, and the third was added by someone fixing the first two.**
`boundary-and-the-index` has now orphaned, in order: the ghost panels' dashed OUTLINES,
which were SVG rects while their words were divs; `m-jy`'s legend swatches, which were
artwork while its type was elsewhere; and the rule-6 question marks over the ghost
panels, added to the SVG layer the same day the other two were written up. All three
stood over the NEXT phase. One of them landed on a caption and rendered as "in?any mode".

The clause the first two did not teach: **if an element cannot live in its phase's own
parent, that is PRECISELY why it will be forgotten.** The split is not incidental to the
bug, it is the mechanism - a phase clear names the parent, and anything outside it is
invisible to the person writing that line. So it is not enough to remember; the element
goes into the clear list in the SAME EDIT that creates it, and a phase whose elements
live in two parents says so in a comment beside both.

Note also that the entry documenting the first instance was written while the second was
still live in the same file. **Twice now this document has described a trap it was itself
falling into**, which is the argument for a check rather than a paragraph: assert that
every element revealed inside a phase is named by that phase's clear, and throw.

**And the same shape has three other mechanisms, all of which appear to run and do
nothing:** a `.replace()` whose pattern does not match, a text override that resolves to
zero elements, and a tween list animating a selector that no longer exists. Every one of
them is silent. Each needs an assertion that the operation CHANGED something, not that it
was issued.

## Banned, enforced

No glowing brains, no node graphs, no translucent cubes, no particle swarms, no blue
circuitry, no illustrated people.
