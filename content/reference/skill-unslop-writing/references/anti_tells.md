# Anti-Tells

Use this file when you need concrete pattern checks at the sentence and phrase level. For paragraph-level slop see `paragraphing.md`. For rhythm see `rhythm.md`. For overused vocabulary see `word_watchlist.md`.

## High-value cuts

Cut or rewrite these first:

- explanation after an image, quote, artifact, or action already made the point
- `not X but Y` / `it's not X, it's Y` / `that's not X, that's Y`
- `Not X. Not Y. Just Z.` (escalating-fragment countdown before a mundane reveal)
- rhetorical Q&A
- automatic groups of three
- decorative metaphor that does not change the scene
- named emotion where action would do more work
- `despite its challenges` / `while X, Y also` / `of course` / `on the other hand` (counterpoint reflex — every claim auto-hedged)
- `here's the kicker` / `what nobody's saying` / `here's the truth` (manufactured suspense)
- `imagine a world where` / `think of it as` (unsolicited futurism, patronizing analogy)
- `it's important to note` / `it's worth noting` / `it bears mentioning` (editorial commentary openers)
- `Certainly!` / `Great question` / `I hope this helps` / `Let's break this down` (sycophantic / collaborative residue)

## Stock AI patterns

Watch for:

- repeated sentence openings (`The`, `She`, `He`, `I`)
- too many short declaratives in a row
- mirrored clause pairs
- "performed exhaustion" prose made of fragments and clipped statements
- body-language shorthand:
  - jaw tightened
  - breath caught
  - heart pounded
  - stopped chewing
  - lips parted
- artifact then gloss:
  - dashboard / log / quote lands
  - narrator explains what it "really means"
- magic adverbs (`quietly`, `deeply`, `fundamentally`, `remarkably`, `arguably`) — manufactured significance modifiers
- false ranges (`from X to Y`) where X and Y aren't actually on a spectrum
- inflated significance vocabulary (`pivotal moment`, `marks a shift`, `reflects broader trends`, `testament to`, `serves as a reminder`)
- vague attributions (`experts argue`, `observers note`, `studies suggest`) with no name
- invented concept labels (`the X paradox`, `the Y trap`) without rigor
- elegant variation: swapping a noun for a synonym every other sentence rather than reusing it
- bold-first bullets where every list item begins with a bolded label and colon

## Sentence-level structural tells

These are statistically over-represented in LLM prose (Reinhart et al., PNAS 2025):

- **Nominalization stacks** (LLMs ~2× human rate): "the implementation of the optimization of" → "we built". Convert noun-phrase abstractions back to verbs.
- **Present participial pile-up** (LLMs ~5× human rate): "Bryan, leaning on his agility, dances..." Cap at one `-ing` clause per paragraph; recast the rest as separate sentences.
- **`That`-clauses as subjects** (LLMs ~3× human rate): "That she came was surprising" → "She came, which surprised me."
- **Perception markers**: "She could hear the door open" → "The door opened." Strip "I could see", "She heard", "He felt", "I noticed" — give the reader the perceived world directly, not the apparatus perceiving it.
- **"Serves as / stands as / marks"** as a pompous substitute for "is/are." Replace with "is" or with the actual verb of doing.
- **Static copulas in series**: if three sentences in a row use a form of "to be" as the main verb, rewrite at least one with a kinetic verb.

## Punctuation and formatting fingerprints

- **Em-dashes**: LLMs use ~3–4× the human rate. Cap at ≤2 per 1,000 words. Replace with comma, period, or colon.
- **Curly quotes / unicode arrows / non-spaced em-dashes** in informal text are an unedited-LLM fingerprint.
- **Contractions**: LLMs use them at ~60% of human rate. Aim for ≥1 contraction per paragraph in any non-formal register.
- **Numeric-modifier hedges** (`approximately 3`, `roughly two`, `around five`): cut hedge-y precision; round or omit.
- **First-person pronouns**: LLMs use them at ~62% of human rate. Restore "I/we" where the author is the agent; strip the agentless cover.

## Replace with

Prefer:

- a visible action
- an object changing state
- a procedural step
- a specific sensory handhold
- a sentence-length shift

## Vocabulary

For overused LLM vocabulary, see `word_watchlist.md`.

A single occurrence of "delve" or "tapestry" proves nothing. Three or more watchlist words in proximity = strong tell.

## Quick rhythm repairs

For sentence shapes and prosody techniques, see `rhythm.md`.

Quick fixes:

- combine two short sentences where the second merely completes the first
- replace one repeated opener with a prepositional or participial opening
- keep one blunt sentence, then follow it with a more elastic one
- remove one of any mirrored pair unless both halves are truly necessary

## Ending check

Ask:

1. Does the piece already land one sentence earlier?
2. Is the last line doing new work or just pointing at the existing echo?
3. Can I cut the final explanatory clause without losing comprehension?

If the answer to 1 or 3 is yes, cut.

## What not to fix

- a single occurrence of any watchlist word (clusters matter, not atoms)
- contractions in a deliberately formal register
- one mirrored pair if both halves carry distinct work
- repetition that is doing real load-bearing work (motif, rhythm, anaphora)
- passive voice on reflex — LLMs actually under-use passives; the real tic is nominalization
