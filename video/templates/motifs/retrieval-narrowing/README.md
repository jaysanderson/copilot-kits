# Motif: retrieval narrowing (`m-rn`)

A question pill enters; ~200 passage tiles fill the frame; the field dims and collapses
toward the question; six tiles stay lit and slide into a source stack; an answer card
writes itself bar by bar with a green stream pulse from the stack per line. Performs:
"finds the few passages that actually answer it, and writes a response from those only".

**When to use:** any agentic-retrieval / precision beat - many become few, few become
the answer.

**Variables:** `rnChip` (answer card chip, default "Grounded response"). The question
line and its highlighted keywords are authored in the file (spans `#rn-kw1/2`) - edit
there, keep it under 8 words.

**Timing:** internal timeline 12.3s; field 0.2-1.4 (bright slate ramp, opacity 0.95), question 0.5, underline+keywords+scan wave 3.3-4.6,
collapse 4.9-6.8 (survivors brighten at 1.5x), stack 6.45-7.1, card 7.55, bars+streams 7.85-10.9. Survivor indices and
timing constants at the top of the script.
Host slot id `m-rn`. Ends in the same card/stack geometry `m-tq` opens with.
