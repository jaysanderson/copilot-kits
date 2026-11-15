# Motif: it answers in your name (`m-iv`)

Three source documents with ruled text at frame left, a reader card centre already taking two in, an answer card at right already holding two sentences with two threads drawn back to their sources

**Performs:** The invented sentence is not visibly different from the true ones and it is now published under the university's mark, with the alarm thread still hanging off the framed card.

**When to use:** The hallucination fear, and any brand-risk or reputational beat. It performs a FEAR rather than a friction, which is rare and is why it earns a climax position.

**Built 9 Oct 2026** for `videos/university` segment S3, on the Progress navy
stage with the Progress palette. Eye-read at preview resolution before use; frames under
`videos/university/preview/it-answers-in-your-name/`.

## What it performs

The two threads pulse so the viewer reads them as the working part; a third sentence writes itself in identical weight; its thread reaches back and lands on NOTHING, terminating in empty space with an alarm terminal; a boundary draws around the answer card with a tab carrying the institution's mark; the three sentences light in turn and nothing distinguishes the third

## Interior (38 child elements)

| id | kind | count | must read |
|---|---|---|---|
| `source_docs` | document card | 3 | texture |
| `doc_lines` | ruled line | 18 | texture |
| `reader_card` | card | 1 | texture |
| `answer_card` | card | 1 | texture |
| `answer_lines` | ruled line, 3 sentences | 9 | texture |
| `threads` | svg stroke | 3 | texture |
| `alarm_terminal` | dot | 1 | texture |
| `boundary` | boundary | 1 | texture |
| `wordmark_tab` | mark on tab | 1 | texture |

**Must read at or above 54px authored:** nothing - no counter and no label beyond the mark, which is artwork; all ruled lines stand for text rather than being text
**Texture, exempt by name:** doc_lines, answer_lines
**Subject present at t=0** (GRAMMAR rule 7): source_docs, doc_lines, reader_card, answer_card, answer_lines, threads

**Timing:** internal timeline 13.0s, read from the composition's own
`data-duration` and NOT from the storyboard - the storyboard carries the beat's planned
window, the composition carries the fact. Event constants are at the top of the script;
re-derive them from the host's own narration alignment when reusing.

## Things that are the argument, not the styling

1. THE THIRD SENTENCE IS AUTHORED IDENTICALLY to the two true ones - same weight, same colour, same spacing. Nothing marks it. Anything added that marks it destroys the argument, which is that an unsupported claim is not visibly different.

2. The unsupported thread MUST TERMINATE IN OPEN STAGE. Pass one ended it inside the reader card, so the frame read 'the third sentence came from the reader' instead of 'from nowhere' - the exact inverse of the meaning, in a frame that was populated, legible and high-ink. No instrument can catch that; only looking can.

3. The customer's mark goes on the whole thing LAST. The fear is not that the model is wrong, it is that the institution publishes it.

## Grammar

`videos/_motifs/GRAMMAR.md` is canonical. This motif inherits its structural rules - rule 4
(a broken stroke is a broken thing), rule 5 (things TRAVEL, they do not fade), rule 7 (the
subject is on screen from t=0) and the banned set. It does NOT use rule 2's three reserved
strokes: no motif in this film uses a dashed state stroke, so a dashed line here can never
be mistaken for an architecture state.
