# Motif: the maze of everything (`m-mz`)

A menu tree of 180 ruled labels already drawn and full, a visitor disc with a question pill at top left, and one target label deep in the fourth level lit from frame zero

**Performs:** The viewer watches somebody miss a page that was marked and visible for the whole shot. It is still lit and unreached when the shot ends.

**When to use:** Any findability or navigation pain, in any vertical. It is the only motif in the library that performs a FAILURE TO ARRIVE rather than a mechanism.

**Built 9 Oct 2026** for `videos/university` segment S1, on the Progress navy
stage with the Progress palette. Eye-read at preview resolution before use; frames under
`videos/university/preview/the-maze-of-everything/`.

## What it performs

The tree ripples once so the scale reads as a count; a 343 counter sets; the lit target pulses; the disc descends four times, each branch opening without it, the fourth branch empty; the disc recoils to the top

## Interior (191 child elements)

| id | kind | count | must read |
|---|---|---|---|
| `menu_labels` | ruled label | 180 | texture |
| `section_headers` | ruled label | 6 | texture |
| `visitor_disc` | disc | 1 | texture |
| `question_pill` | pill with text | 1 | **yes** |
| `page_counter` | counter 64px | 1 | **yes** |
| `target_label` | ruled label, lit | 1 | texture |
| `empty_branch` | ruled row, empty | 1 | texture |

**Must read at or above 54px authored:** question_pill, page_counter
**Texture, exempt by name:** menu_labels, section_headers
**Subject present at t=0** (GRAMMAR rule 7): menu_labels, section_headers, visitor_disc, question_pill, target_label

**Timing:** internal timeline 10.0s, read from the composition's own
`data-duration` and NOT from the storyboard - the storyboard carries the beat's planned
window, the composition carries the fact. Event constants are at the top of the script;
re-derive them from the host's own narration alignment when reusing.

## Things that are the argument, not the styling

1. The target is lit FROM FRAME ZERO and the viewer tracks it the whole way. That is the cruelty and it is the shot - a page that was visible throughout and never reached. Never reveal the target late; the shot stops working.

2. The fourth branch opens EMPTY - a drawn, dashed, empty row rather than an absence. 'There was nothing there' has to be seen.

3. Pass one was six columns of bars and read as texture, not as a tree. The spines and the child-to-grandchild ticks are what make the nesting legible, and they are not decoration - remove them and the motif reverts to stripes.

4. The 186 labels are TEXTURE by declaration. Raising them to a legibility floor turns a site into a list and destroys the shot.

## Grammar

`videos/_motifs/GRAMMAR.md` is canonical. This motif inherits its structural rules - rule 4
(a broken stroke is a broken thing), rule 5 (things TRAVEL, they do not fade), rule 7 (the
subject is on screen from t=0) and the banned set. It does NOT use rule 2's three reserved
strokes: no motif in this film uses a dashed state stroke, so a dashed line here can never
be mistaken for an architecture state.
