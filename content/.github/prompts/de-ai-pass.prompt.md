---
mode: edit
description: "Remove AI-shaped prose from the open file without changing its meaning; show the edits as a diff"
---
# De-AI pass

Edit the open file in place. Keep every fact, number, source and the author's argument. Prefer the smallest change that fixes the problem: delete a sentence before rewriting it, rewrite a phrase before rewriting a paragraph. Show the result as a diff with a one-line reason per hunk.

## Checklist, in this order
1. **First-line scan**: read the first sentence of every paragraph in sequence. Cut openers such as "It's worth noting", "At its core", "Here's the thing", "Ultimately", "Of course". If the openers do not carry the argument, reorder or merge paragraphs before touching sentences.
2. **Watchlist words**: delve, leverage, unlock, seamless, game-changing, utilise, enhance, harness, streamline, navigate, showcase, underscore, foster, robust, comprehensive, crucial, pivotal, landscape, journey. Replace with the specific word, or delete the sentence if it carried nothing.
3. **Structural tells**: "not X but Y" (keep at most one per page), reflex groups of three, a rhetorical question then its answer, "serves as / stands as / marks", nominalisation stacks ("the implementation of" becomes "we built"), vague attributions ("experts say") with no name, invented labels ("the X paradox").
4. **Hedging reflex**: cut "while X, Y also", "despite its challenges", "on the other hand" unless the qualification changes the reader's decision. Hold the position.
5. **Rhythm**: in any five sentences, one under 8 words and one over 25. Break repeated openers. End key sentences on a stressed word, not "-ation" or "-ing". Restore contractions where the register allows.
6. **Paragraphs**: 1 to 4 sentences, one longer paragraph per page allowed. Delete bridge sentences. Delete any paragraph that restates the one before it.
7. **Bullets**: remove the bold-label-colon pattern when every item has it. Lists hold facts, not slogans.
8. **Punctuation**: replace every em dash and en dash with " - ", a comma, a colon or a full stop (exception: the owner's personal LinkedIn posts). Straight quotes.
9. **Ending**: if the last paragraph summarises, cut it. The piece ends on its last useful fact, ask or image.
10. **Asymmetry**: leave one paragraph longer, one claim undefended, one detail too specific to be generic. Do not polish it flat.

## Do not
- Change a number, a source, a product name or a quoted line.
- Add adjectives, metaphors or flourishes to "improve" rhythm.
- Rewrite a sentence that is already specific and plain.
- Chase a single watchlist word in isolation. Clusters matter, not atoms.

## Report
After the diff, three lines: watchlist words removed (count), structural tells fixed (count), anything left on purpose and why.
