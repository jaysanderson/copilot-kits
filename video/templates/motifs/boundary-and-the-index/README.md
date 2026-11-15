# Motif: the boundary and the index (`m-bd`)

Four phases on one object vocabulary - a corpus block, an index block, an inference block,
and labelled boundaries. Performs the residency argument: query in place is true of the
table and not of the answer, and in hybrid the derived index crosses into Progress's cloud
while **where the source documents live is left unresolved**, because that is a thing
Progress has not stated (grammar rule 6; DAM fact `deployment_modes` v6).

**When to use:** any residency, data-location or deployment-mode beat.

## What each phase performs

**NO WINDOWS IN THIS TABLE, DELIBERATELY.** This README used to carry two phase tables -
this hand-written one and the generated one further down - and they had already drifted:
`/notclaimed` was documented here as ending at 33.10 and in the code at 31.35. A second
table is a second source of truth, and the generator cannot protect a table it does not
own. Timings live in the generated block ONLY; this one says what the phase DOES.

| Phase | What it performs |
|---|---|
| `/table` | query in place is true of the table, not of the answer |
| `/hybrid` | the source documents sit UNRESOLVED in the neutral gap carrying a question mark and never move; an index forms OUT of them, travels across, and SETTLES with weight in the Progress boundary, staying linked back by a solid derivation line. The customer boundary holds the one thing confirmed to be in it - the application, asking |
| `/notclaimed` | three ghost panels, one per phrase, each taking a short-dash NOT BUILT outline and each FILLED with the three objects that mode would have held, so the panel says "this does not exist" rather than "this is unfinished" |
| `/modes` | three panels, SaaS / private cloud / hybrid, each carrying the SAME object set so the only difference is WHERE the objects are |

## The fact this motif carries, and must not drift from

**The index rests on the PROGRESS side.** Confirmed with Progress 8 Oct 2026, the index
resting there on 9 Oct, and published nowhere - which is why `bdDate` is not optional. A
superseded version of this claim ("entirely inside your own environment") is still in the
audio of at least two delivered films; do not reintroduce it here.

**THE DOCUMENTS' OWN POSITION IS NOT OURS TO DRAW, and this is the rule-6 instance that
the treatment exists for.** The confirmed statement says what RUNS in Progress's cloud. It
says nothing about where the source corpus is STORED. "Hybrid keeps your documents with
you" is an INFERENCE from the word "only" - it reached an approved pillar line and survived
two correction passes because it is the half of a corrected fact that sounds safe. Canon:
DAM fact `deployment_modes` v6, UNCONFIRMED (a).

So the documents sit in the NEUTRAL GAP between the two boundaries, carrying the question
mark, and **they never move**. An earlier version settled them inside the customer boundary
using the record store's weight-and-stay gesture; that gesture IS the assertion, so it was
removed rather than softened. **Do not reinstate any movement on `#bd-corpus`** - no drift,
no lean, no settle. A direction is a claim. The stage and the question mark's own pulse keep
the shot alive instead.

**The derivation line is SOLID, and that is a grammar requirement, not a style call.**
It carried `stroke-dasharray="10 9"` until 9 Oct 2026. The three strokes in
`GRAMMAR.md` are reserved and `10 9` is none of them - it sits between the `20 12` ISV
BUILDS and `6 10` NOT BUILT scales and is separable from neither. A viewer cannot
measure a dasharray; they read "dashed" as one of the two non-available states, and this
derivation is CONFIRMED, so both available readings were wrong. The motion the dash
march was supplying moved to a DRAW-ON at `AT_BUILT`, which is the beat where the index
is said to be built. Do not reinstate a repeating dash offset here.

**The derivation line is load-bearing, not decoration.** It stays drawn after the index
crosses, which is what keeps the shot informative rather than merely blank: something
genuinely built from the documents still draws from them, even though where they live is
unresolved.

**THE `/modes` PANELS CARRY THE OBJECTS, and that was the phase's missing half.**
Until 9 Oct 2026 the phase had three boundaries, three tabs and one question mark and
**no objects at all** - `bd-corpus`, `bd-idx` and `bd-inf` are declared inside
`#bd-hybridphase`, which `/modes` hides on entry, so the three panels rendered as empty
rectangles. The sentence above - the only difference is WHERE the objects are - was the
phase's whole argument and the shot asserted nothing. Nine objects are now authored in
the phase itself: SaaS with all three inside; private cloud with corpus and index inside
and INFERENCE OUTSIDE under rule 6 (canon v6 UNCONFIRMED (c)); hybrid with index and
inference inside and THE SOURCE DOCUMENTS OUTSIDE under rule 6 (canon v6 UNCONFIRMED
(a)). Do not seat either outside object in a boundary to tidy the layout.

**The ghosts are cleared at `AT_MODES - 0.4`, and they are a SPLIT PARENT.** The ghost
panels' words live in the `#bd-notclaimed` div; their short-dashed NOT BUILT outlines are SVG
`<rect>` elements (`bd-gr0/1/2`) in the svg layer, outside that div. Clearing the div
alone hid the labels and left three dashed rectangles standing over the mode panels for
the whole shot. **This is the second instance of that shape in this library**, after
`m-jy`'s legend where the text was dismissed and the stroke swatches were orphaned: the
words read as "the thing", so the artwork is the half nobody clears. Any future clear in
this motif clears BOTH parents.

**`/modes`' private-cloud panel carries its own unresolved marks**, for the same reason:
canon v6 lists as UNCONFIRMED (c) where inference runs in private cloud and (d) what a
private cloud boundary is and who operates it. Drawing inference seated inside that
boundary would assert the same class of thing the hybrid correction removed. Do not "tidy"
those marks away.

**`/table` is one frame holding a distinction**, which is why the boundary must stay intact
and visibly so while the results leave. Nothing is violated and the data still left. That
is what makes the wording reassuring and wrong.

## Grammar

Uses rule 5: data that crosses a boundary TRAVELS, drawn as an object moving with the
boundary visible at both ends of the move. Nothing crosses by fading. Also rule 2's short-dashed
stroke for NOT BUILT in `/notclaimed`. Full grammar: `videos/_motifs/GRAMMAR.md`.

**Variables:** `bdYourEnv` and `bdYourEnv2` (customer boundary tabs, default "Your
environment"), `bdProgCloud` (default "Progress cloud"), `bdQueryInPlace` (default "Query
in place"), `bdResults` (default "Results"), `bdCorpus` (default "Source documents"),
`bdIndex` (default "Index"), `bdInference` (default "Inference"), `bdDate` (the date strip),
`bdSaas` / `bdPrivate` / `bdHybrid` (the three mode tabs), `bdNot0..bdNot2` (the three
unclaimed modes, defaults On premises / Offline / Air gapped), `bdNotBuilt0..bdNotBuilt2`
(default "NOT BUILT"), `bdNotStated` (the rule-6 label under the documents, default
"Progress has not stated"), `bdPrivateUnknown` (the rule-6 label under the private-cloud
panel, default "Who operates this boundary"), `bdPrivateUnknown2` (the second rule-6
label in that panel), `bdApp` (the one object confirmed to sit inside the customer
boundary in `/hybrid`, default "Your application") and `bdAppRole` (its caption, default
"Confirmed here: it asks the question").

## On the three unclaimed strings

`On premises`, `Offline` and `Air gapped` appear on screen in `/notclaimed` ONLY, inside
short-dashed NOT BUILT markers, and a host's narration must name them only in the negative.
**These three strings therefore cannot go on a gate's OCR forbidden-strings list**, because
OCR cannot tell a negated label from a claim. A host declares that as a HOLE and runs a
named manual check instead: confirm each appears only within this phase's window and only
inside a NOT BUILT marker. See `videos/sa-use-cases/STORYBOARD.md`, shot B5c.

**All three ghosts are present, and all three HOLD.** A sibling storyboard was caught
listing only two of the three against narration that correctly named three; if you re-time
this phase, keep the count at three.

**Do not reinstate a push-off.** An earlier version swept the ghosts off frame right. Two
things were wrong with it. Measured: ghost 1 stayed legible 4.1s and ghost 3 about 0.5s,
because the push began before the third had finished landing - so the last named absence
was unreadable, and there is no room in this shot to both hold it and push all three. And
the gesture itself is borrowed from `body-of-knowledge`, where it means "excluded from the
corpus"; here the three are not dismissed, they are NOT CLAIMED, and stated-and-held says
that where swept-away says someone decided against them.

**Timing:** internal timeline 34.0s. Event constants at the top of the script: `AT_RESID`
0.50, `AT_QIP` 3.98, `AT_TABLE` 6.07, `AT_ANSWER` 8.31, `AT_HYBRID` 9.51, `AT_STAY` 11.19,
`AT_BUILT` 13.14, `AT_RESTS` 14.25, `AT_OCT` 18.05, `AT_NOPUB` 19.76, `AT_NOT0` 21.38,
`AT_NOT1` 23.06, `AT_NOT2` 24.51, `AT_MODES` 25.89. These are the `sa-use-cases` b5 word
events rebased to motif zero. **Re-derive from the host's own narration alignment when
reusing** - the index must settle on the word "rests".

A host may run any contiguous subset; the ids are stable.

Host slot id `m-bd`. Fonts: expects `ProgDisplay` / `ProgText` in the host.

## Phase windows are GENERATED from the constants, not described

The table above is produced from `AT_HYBRID`, `AT_NOT0`, `AT_MODES` and `data-duration`
in the composition. It was previously hand-written and had drifted badly: it said
`/modes` ran 25.89-34.00 where the composition says 33.50-42.00, so **a host seeking
`/modes` off this README would have rendered `/notclaimed` instead** - and this motif's
only renderer of `/modes` is the C-suite film, so no other gate could have caught it.
Regenerate rather than edit.

## Gate coverage, stated rather than assumed

**`/table`, `/hybrid` and `/notclaimed` are gated by the `sa-use-cases` render** (shots B5,
B5b, B5c).

**`/modes` is NOT rendered by `sa-use-cases` and is therefore NOT covered by its gate.** It
was built for the executive film, which states the three modes where this film states only
hybrid, and it is gated by that film's render. A green gate report on `sa-use-cases` is
evidence about 3 of 4 phases, not 4.

## Phases

<!-- PHASES:BEGIN (generated by gen_phase_tables.py - do not hand-edit) -->

| Phase | Window | Notes |
|---|---|---|
| `/table` | 0.00-9.54 | query in place is true of the table, not the answer |
| `/hybrid` | 9.54-25.99 | the index crosses and rests; the documents' own |
| `/notclaimed` | 25.99-31.35 | three named absences, stated and HELD to the end |
| `/modes` | 33.50-42.00 | three panels (host-driven; NOT in sa-use-cases) |

Internal timeline **41.02s**. The last phase may end before the declared duration; a host plays the window it needs.

Event constants, read from the composition:

- `AT_RESID` 0.5  -  "Residency catches people"
- `AT_QIP` 3.98  -  "Query in place"
- `AT_TABLE` 6.07  -  "true of the table"
- `AT_ANSWER` 8.23  -  "true of the answer"
- `AT_HYBRID` 9.54  -  "In hybrid"
- `AT_UNRESOLVED` 14.8  -  "Whether the documents themselves stay with you"
- `AT_NOTTOLD` 18.76  -  "Progress has not told us"
- `AT_BUILT` 11.24  -  "index built from them"
- `AT_RESTS` 13.05  -  "rests in Progress's cloud"
- `AT_OCT` 22.16  -  "eighth of October"
- `AT_NOPUB` 24.23  -  "published nowhere"
- `AT_NOT0` 25.99  -  "No on premises"
- `AT_NOT1` 27.67  -  "No offline"
- `AT_NOT2` 29.41  -  "No air gapped"
- `AT_MODES` 33.5  -  ---- CROSS-FILM GUARD, added 9 Oct 2026 after film-sa-usecases measured the

*Generated from the composition's own phase comments and `AT_` constants. A README that describes timings drifts on the next re-time; this one cannot.*

<!-- PHASES:END -->
