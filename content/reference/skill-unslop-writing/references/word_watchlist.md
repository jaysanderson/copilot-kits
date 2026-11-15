# Word Watchlist

Empirically over-represented in LLM prose. Use as a find-and-flag pass — but with judgment.

## How to use

A single occurrence of any of these proves nothing. They appear in good human writing too. **The tell is clustering**: three or more in proximity, especially in close paragraphs, is a strong signal. Treat this as a flag list, not a banlist.

When you flag a word, choose:

1. **Replace** with a more specific, less hedge-y alternative
2. **Delete** the sentence (often the slop word is propping up a sentence that has no real content)
3. **Keep** if it is genuinely the right word for what you mean

Don't reflexively replace. Reflexive replacement just rotates the slop into different vocabulary.

## Highest-confidence verbs

Statistically over-represented in LLM-generated text (Kobak et al., *Science Advances*, 2025; n=14.2M PubMed abstracts):

- **delve / delving** — extreme outlier (~25× expected rate)
- **showcase / showcasing**
- **underscore / underscores**
- **leverage** (as verb)
- **navigate** (as verb, for non-physical "navigation")
- **harness**
- **streamline**
- **utilize** — almost always: use *use*
- **enhance** — almost always: use a specific verb
- **embrace**
- **foster**
- **bolster**
- **align with**
- **resonate**
- **garner**
- **reimagine**
- **elevate**
- **captivate**
- **exhibit / exhibited**

The 2024 LLM lexical fingerprint is **verbs**, not nouns — 66% of excess style words in 2024 corpora were verbs. Watch verb choice first.

## Highest-confidence adjectives

- **crucial**
- **pivotal**
- **comprehensive**
- **intricate**
- **robust**
- **vibrant**
- **dynamic**
- **rich** (as in "a rich cultural heritage")
- **diverse** (as in "a diverse range of")
- **meticulous / meticulously**
- **breathtaking**
- **profound**
- **unique** (when not actually unique)
- **innovative**

## Magic adverbs

These manufacture significance without earning it.

- **quietly** ("quietly reshaping")
- **deeply**
- **fundamentally**
- **remarkably**
- **arguably**
- **notably**
- **particularly**
- **importantly**
- **across** (in non-spatial uses: "across industries")

## Filler nouns

- **landscape** (as metaphor)
- **tapestry**
- **realm**
- **insights** (when used as count noun)
- **potential**
- **findings**
- **testament**
- **journey** (especially as metaphor)
- **fabric** (as metaphor)
- **synergy**
- **paradigm**

## Phrasal templates

Whole phrases that signal LLM scaffolding:

- **It's important to note that...**
- **It's worth noting that...**
- **In this article, we will...**
- **In conclusion**
- **In essence**
- **At its core**
- **Ultimately**
- **Moreover** / **Furthermore**
- **In a world where...**
- **Navigating the complexities of...**
- **In the realm of...**
- **A testament to...**
- **The intricate dance of...**
- **A rich tapestry of...**
- **A diverse range of...**
- **From X to Y** (when X and Y aren't on a spectrum)
- **Despite its challenges...**

## Surprising findings

- LLMs do **not** overuse passive voice. They under-use it (~53% of human rate). The "AI tone" is driven by **nominalization stacking**, not passives. Don't reflexively passive-bust.
- LLMs often have **higher** lexical diversity than humans, not lower. The "samey" feeling comes from flat sentence-rhythm and predictable POS patterns, not vocabulary repetition.
- LLMs **under**-use contractions (~60% of human rate) and first-person pronouns (~62% of human rate). Restoring these often unsticks an over-formal passage faster than rewriting.

## Source

For full empirical methodology and ranked word lists: Kobak et al., "Delving into LLM-assisted writing in biomedical publications through excess vocabulary," *Science Advances*, 2025 (arXiv:2406.07016). Cross-reference: Reinhart et al., "Do LLMs write like humans? Variation in grammatical and rhetorical styles," *PNAS*, 2025 (arXiv:2410.16107).
