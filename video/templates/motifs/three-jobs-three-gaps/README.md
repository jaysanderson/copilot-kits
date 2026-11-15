# Motif: three jobs, three gaps (`m-3j`)

Three product objects take the thirds of the frame and each PERFORMS ITS OWN VERB ONCE -
rows drop into a closed store and settle, a reader takes documents in and lights a passage
with a citation thread back to its source, bars rise on an axis. Then each object dims and
an empty amber notch opens on its own edge: the thing it does not do. The three notches
hold lit as the motif ends. Performs: "each product does its own job, and each one's gap is
why the next is in the picture".

**When to use:** the establishing beat of any film about the three-product estate. It
teaches the viewer the three silhouettes and the three verbs, and it must run before any
beat that assumes them. The notches it leaves lit are where `m-jy` draws its joins.

**Grammar.** This motif establishes rule 1 of the shared grammar (a product is a solid
object with a verb it performs) and rule 3's amber (the notch is the ISV's problem, so it
is amber from the first shot). Full grammar: `videos/_motifs/GRAMMAR.md`.

**Silhouettes are fixed and must not change between shots or between films:** store =
ruled rows in a closed frame; reader = rounded card emitting a lit passage; chart = axis
with bars.

**Variables** (declare on the host `<html>`, bound by `data-var-text`):
`tjLabel0..tjLabel2` (product names, defaults OpenEdge / Progress Agentic RAG / Domo),
`tjVerb0..tjVerb2` (the single-word verbs, defaults Holds / Finds / Draws). The voice
carries "shows its working"; the screen deliberately does not repeat it.

**Timing:** internal timeline 15.2s. Event constants at the top of the script, named
`AT_OPEN` 0.00, `AT_HOLD` 1.50, `AT_FIND` 3.22, `AT_WORK` 6.23, `AT_DRAW` 7.88,
`AT_GAP` 9.89 - these are the `sa-use-cases` B1 word events rebased to motif zero.
**Re-derive them from the host's own narration alignment when reusing**: each object must
arrive on its own spoken name.

Host slot id `m-3j`. Four document cards are visible at frame zero so the host's first
frame is a designed poster rather than an empty stage.

Fonts: expects `ProgDisplay` / `ProgText` `@font-face` in the host (brand/fonts woff2).

**Gated by:** the `sa-use-cases` render (shot B1). All phases are rendered there.
