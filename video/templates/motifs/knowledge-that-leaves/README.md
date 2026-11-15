# Motif: knowledge that leaves with the person (`m-rt`)

Five desks in a receding row, each carrying a stack of six document cards and a name plate with a ruled name, each with a cluster of twelve knowledge tiles above it connected by fine threads. All present and already threaded at frame zero

**Performs:** The documents did not leave. The ability to find them did. The shot ends mid-cascade with two desks stripped and three still threaded.

**When to use:** Any tacit-knowledge, succession or key-person pain. Also the general shape of 'the asset stayed and the access went'.

**Built 9 Oct 2026** for `videos/university` segment S7, on the Progress navy
stage with the Progress palette. Eye-read at preview resolution before use; frames under
`videos/university/preview/knowledge-that-leaves/`.

## What it performs

The front desk's stack riffles once; three threads pulse desk-to-tile-and-back so the viewer sees the FINDING runs through the desk; the name plate goes BLANK with nothing else changing; the twelve threads snap in a 70ms cascade, each leaving both stubs with a 6px recoil gap, each tile going dead grey and drifting out of frame; the document stack does not move

## Interior (184 child elements)

| id | kind | count | must read |
|---|---|---|---|
| `desks` | work surface | 5 | texture |
| `document_cards` | document card | 30 | texture |
| `name_plates` | plate with ruled name | 5 | texture |
| `knowledge_tiles` | tile | 60 | texture |
| `threads` | svg stroke | 60 | texture |
| `thread_stubs` | svg stroke stub | 24 | texture |

**Must read at or above 54px authored:** nothing - no counter and no words; the plates are ruled marks, which is why one going blank reads as absence rather than as text disappearing. No illustrated people in a beat about retirement.
**Texture, exempt by name:** name_plates
**Subject present at t=0** (GRAMMAR rule 7): desks, document_cards, name_plates, knowledge_tiles, threads

**Timing:** internal timeline 11.5s, read from the composition's own
`data-duration` and NOT from the storyboard - the storyboard carries the beat's planned
window, the composition carries the fact. Event constants are at the top of the script;
re-derive them from the host's own narration alignment when reusing.

## Things that are the argument, not the styling

1. NO ILLUSTRATED PEOPLE, in a beat about people leaving. The name plate going blank carries it, and it is less maudlin than a figure would be.

2. THE DOCUMENT STACK DOES NOT MOVE while the threads snap. That is the entire distinction the motif exists for: the documents did not leave, the ability to find them did.

3. Each snapped thread leaves BOTH STUBS with a recoil gap rather than vanishing. A thread that fades has ended; a thread that snaps has been broken.

4. The shot ends MID-CASCADE with two desks stripped and three still threaded. Do not finish them - an unfinished cascade is the honest picture of a slow loss.

## Grammar

`videos/_motifs/GRAMMAR.md` is canonical. This motif inherits its structural rules - rule 4
(a broken stroke is a broken thing), rule 5 (things TRAVEL, they do not fade), rule 7 (the
subject is on screen from t=0) and the banned set. It does NOT use rule 2's three reserved
strokes: no motif in this film uses a dashed state stroke, so a dashed line here can never
be mistaken for an architecture state.
