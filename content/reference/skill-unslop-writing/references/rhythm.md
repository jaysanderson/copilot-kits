# Rhythm

Use this file when prose feels metronomic, when sentences trail off on weak syllables, or when paragraph rhythm is uniform.

## The Provost passage

> This sentence has five words. Here are five more words. Five-word sentences are fine. But several together become monotonous. Listen to what is happening. The writing is getting boring. The sound of it drones. It's like a stuck record. The ear demands some variety.
>
> Now listen. I vary the sentence length, and I create music. Music. The writing sings. It has a pleasant rhythm, a lilt, a harmony. I use short sentences. And I use sentences of medium length. And sometimes, when I am certain the reader is rested, I will engage him with a sentence of considerable length, a sentence that burns with energy and builds with all the impetus of a crescendo, the roll of the drums, the crash of the cymbals — sounds that say listen to this, it is important.
>
> So write with a combination of short, medium, and long sentences. Create a sound that pleases the reader's ear. Don't just write words. Write music.

— Gary Provost, *100 Ways to Improve Your Writing*

## The burstiness rule

LLM prose has roughly half the sentence-length variance of human prose. Concrete target:

- In any 5-sentence span, include at least one sentence under 8 words AND at least one over 25 words.
- Do not enforce variance evenly. Constant variation produces its own metronome. Establish a pattern, then break it once per paragraph.

The Provost crescendo structure is one good shape: three or four short declaratives, then one long sentence whose length is *earned* by the prior compression — not the default mode.

## Six sentence shapes to deploy

- **Right-branching / cumulative** — base clause, then trailing modifiers. *"She walked, hands in pockets, watching the light go."* Reads as human because it imitates noticing in real time — additive, not pre-planned.
- **Left-branching / periodic** — modifiers first, main clause last. *"After everything, after the years and the silence, he came back."* Use sparingly; a string of these signals planning, not voice.
- **Mid-branching** — modifier inside the kernel. *"He, having read the letter twice, set it down."* Forces a stutter-step.
- **Balanced** — two clauses of equal weight. *"Man proposes; God disposes."* Earn it; don't reach for it.
- **Segregating** — short independent clauses in a row. *"He sat down. He opened the book. He did not read."* Use for compression, not as default cadence.
- **Fragmentary** — deliberate non-sentence after a long sentence. *"...no engines, no voices, no clatter. No sirens. No footfalls on the cobbles. Not even gulls."* (Doerr) The fragment crash-lands the meaning.

## Three prosody moves

1. **End on a stressed syllable.** AI prose habitually trails off on weak endings (`-ation`, `-ity`, `-ment`, `-ing`). Compare *"We came to Looe by unimportant lanes"* (lands on stressed *lanes*) vs. *"We drove to Looe via the minor roads"* (trails on weak *roads*). Rewrite the final word of important sentences to land on a stress: prefer monosyllables, hard consonants, Anglo-Saxon endings.

2. **Move the verb.** AI defaults to subject-verb-object with a static or copular verb. Front the verb (*"Came the dawn"*), delay it (periodic), or replace it with a kinetic one (*"whispers"* not *"speaks softly"*; *"devours"* not *"eats hungrily"*). A high-octane verb shifts the stress profile of the whole sentence.

3. **Break one expectation per paragraph.** After establishing a rhythm — say, three subject-first declaratives — violate it once: a fragment, a participial opener, an inversion, a polysyndeton. Burstiness comes from one deliberate break, not from constant variation.

## Conjunctions: asyndeton vs. polysyndeton

- **Asyndeton** (no conjunctions) — speed, decisiveness, collision. *"I came, I saw, I conquered."* / *"I needed a drink, I needed a vacation, I needed a home in the country."*
- **Polysyndeton** (repeated *and*) — weight, accumulation, ongoing-ness. *"In the bed of the river there were pebbles and boulders, dry and white in the sun, and the water was clear and swiftly moving and blue in the channels."* (Hemingway)

LLMs default to neither — they use commas correctly, conjunctions correctly, neither for effect. Reach for one when the moment calls for it.

## Parataxis vs. hypotaxis pivot

- **Parataxis**: short equally-weighted independent clauses. *"There were no rooms at the inn. We drove farther. It was raining heavily."*
- **Hypotaxis**: subordinate clauses stacked. *"Although the rain had not let up, and because the inn was full, we drove on."*

Pivot from one to the other inside a paragraph to create a gear-change. Same content, different felt-tempo.

## Klinkenborg's stack test

Test any long sentence by reading it as separate short sentences. If they survive on their own, the join is real; if they collapse into mush, the long form was hiding weakness behind grammar. Lengthy sentences are short sentences joined — not bigger thoughts.

## Quick rhythm repairs

- combine two short sentences where the second merely completes the first
- replace one repeated opener with a prepositional or participial opening
- keep one blunt sentence, then follow it with a more elastic one
- after any mirrored pair, ask whether both halves carry distinct work — if not, cut one
- if a paragraph reads as iambic and end-stressed throughout, break the foot somewhere
