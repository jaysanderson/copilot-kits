# DESIGN - Use case film for the Progress C-suite (concept film)

Work item `2d0c0949d232456583ec189c2852c04d`. Written 9 Oct 2026.

**Film type: CONCEPT** (settled by the GM, not a judgement call here). No screen capture,
no framed app plate carrying a beat. Bespoke animated illustration performs each idea
while the voice says it. Type carries labels, the state markers and the closing line,
never the explanation.

**Audience: the Progress Software executive team. Internal.** They are not evaluating
whether retrieval works. They are deciding where the company spends attention. So the
axis is reach and outcome, where the solution-architect film built from the same primer is
mechanism.

**Source: `apps/isv-primer/sections/primer.md` only** (2,148 words, frozen). The full
reference at `apps/isv-reference/sections/` was read to understand the material and is
cited below as evidence, never as a source of beats.

Build: HyperFrames, 1920x1080, 30 fps. One ElevenLabs voice (cast by audition, below),
music-free, no captions.

Output: `videos/progress-exec-use-cases-<build date>.mp4`.

---

## The one thing they should be able to say afterwards

> "There are three different jobs this thing does, they get progressively more valuable
> and progressively more work, and we have a counted map of exactly where the work is."

The brief's test is that an executive can name three places the product belongs that they
had not previously connected, and FEELS the breadth rather than being told about it. Both
halves are designed for:

- **Name three.** The three shapes are numbered out loud (First, Second, Third). Numbering
  is the cheapest memory aid there is and it costs three words.
- **Feel, not be told.** There is no breadth statistic in the narration. The feeling comes
  from the picture, where the field of real builds lights up, and the count appears as a
  small sourced caption underneath it. A number read aloud is being told; a field lighting
  up is being shown. This is a deliberate inversion of the instinct to open on "21 demos
  across 13 industries".

---

## The hard judgement: my position on thirteen of fifteen

The lead's instinct was that the count becomes the reason the category is open: the joins
are where the value is, we have mapped them, and nobody else has. **I am not building that
framing, for two reasons, and I think the second one matters more than the first.**

**1. Half of it is an unverifiable claim.** "Nobody else has mapped them" is an absence
claim about competitors that this factory has not checked. Hard rule 3 and the
verify-absence-claims rule both bite, and an internal audience is the worst possible room
in which to assert something a colleague can puncture with one question. "The category is
open" has the same problem in softer form, and it additionally sounds like the category
pitch this audience has heard from every vendor. The brief's own warning is that an
internal audience detects marketing aimed at itself instantly. A category-creation line is
exactly what that detector is tuned for.

**2. The lead's framing is defensive, and it does not need to be.** It answers the
objection "the product is unfinished". But that objection only arises if the film has
already implied the joins SHOULD have shipped from us. If the film never promises
integration, the count is not a confession, it is information. Framing it as a rebuttal
concedes the premise.

**What I am building instead: the count is the agenda item, not the caveat.** Thirteen
joins that nobody has shipped, named and counted, in a reference a customer can price
against. For an audience whose job is allocating attention, a counted list of unshipped
joins between products already in the picture is the single most actionable thing in the
film. It converts the honest fact directly into the brief's own call to action, "where
should we point this next", because the count IS the list of candidate answers.

**So: not hidden, and not the lead, but not a mid-film honesty beat either. It is the
hinge.** Structure is breadth, then the count, then the question. The count is the turn
from "here is what it does" to "here is the decision in front of you", which is the only
reason this audience is still watching at 90 seconds.

**And the hero shape is deliberately one of the thirteen.** Beat 4, documents turned into
rows beside a chart, is the shape nobody has connected and it is NOT available today. That
is not a flaw in the choice, it is why the choice works: the strongest image in the film is
a join being authored, so when the count lands five seconds later the viewer has already
watched one of the thirteen and does not need the fact explained. Honesty becomes
structural rather than appended. A film that put the hero on an available-today pattern and
then disclosed the count would be doing the thing the lead rightly says is worse than
arguing.

### One thing the lead's framing and mine both got wrong

**I cannot find any support for Domo being a Progress-owned product, and my first draft of
the hinge said "thirteen joins between products this company already owns".** That line is
now cut. The evidence against it, all from the source material:

- The reference's own title is "Progress OpenEdge, Domo and Progress Agentic RAG". Two of
  the three carry the Progress prefix and Domo does not. The lead wrote that title.
- The primer calls them "three products from different lineages".
- The reference treats Domo's material as a third party's throughout: "Domo's own
  documentation", "Domo's own FAQ", "Domo's own sample", and at
  `apps/isv-reference/sections/30-patterns.md:184`, "Whether Domo has a first-class
  OpenEdge connector is not confirmed", which is not a sentence anybody writes about two
  products in the same portfolio.

Saying "products this company already owns" to the Progress executive team would be
punctured in the room by the first person to hear it. **It also made the film better to fix
it**, which is why I am reporting it as a finding rather than a near miss:

Once Domo is outside the portfolio, the three shapes form an ascending ladder that was not
visible before. Shape one needs Progress Agentic RAG alone. Shape two needs Progress
Agentic RAG and OpenEdge, both ours. Shape three crosses to a third party. Reach and work
both increase at every rung, and the count then tells you where the work sits. The film
becomes an argument rather than a list, and the executive question separates cleanly into
joins we could close ourselves and joins we could not close unilaterally.

**This is not a blocker and I have not stopped on it.** The narration asserts no ownership
either way, so it is correct under both answers.

### Resolved by the lead, 9 Oct 2026, and the conclusion holds for a firmer reason

The fact was not in the material I read. **Progress signed a definitive agreement on 22 July
2026 to acquire Domo's operating business, with close expected before 30 November 2026.
The close is NOT confirmed:** progress.com uses "Progress Domo (formerly Domo)" and states
no status, and the lead corrected his own overstatement on this point on 8 Oct 2026 after
describing the acquisition as complete when it was not.

So the ownership line stays cut, and the reason is now stronger than "unsupported":
**the GM has twice rejected acquisition specifics on Domo material.** Binding on this film:

- **No reference to the acquisition at all, in any direction.** Not as fact, not as pending,
  not as "formerly Domo", not hedged. The film is silent on it.
- Labelled `Domo` on screen. Never `Progress Domo`.
- The three product panels in B1 **must not sit inside a single Progress boundary**, because
  that composition asserts ownership in a picture even when the voice does not.

The ascending ladder is confirmed and survives either answer, so it stays: Progress Agentic
RAG alone, then with OpenEdge, then crossing to a third party.

---

## Beat list and narration budget

**The budget is derived, not assumed.** The sibling film's cast (`arthur`) measures at
157.5 words per minute across 472 words and 179.76 seconds of speech
(`videos/sa-use-cases/beats.json`, nine beats, read 9 Oct 2026), giving 0.381 seconds per
word. Its film total of 190.36s against 179.76s of speech is 10.6s of lead and hold across
nine beats, about 1.18s per beat.

For seven beats: 318 words x 0.381 = 121s of speech, plus 8.3s of overhead, = **about
2 minutes 10 seconds.**

**The overage was declared at 325 words against the brief's "roughly 250 to 300", located
entirely in B5, and approved by the lead on 9 Oct 2026** on the grounds that both cuts I
offered would weaken the film. It then came down to 318 on its own, because the lead's B6
tighten removed a repeated "cloud" and seven words with it. Every beat other than B5 is at
or below its share.

| Beat | Job | Words | Approx window |
|---|---|---|---|
| B1 | Three jobs, and the three gaps between them | 56 | 0:00 - 0:23 |
| B2 | First shape: the question the help centre cannot find. Available today | 38 | 0:23 - 0:39 |
| B3 | Second shape: the live fact the Retrieval Agent fetches rather than copies | 35 | 0:39 - 0:54 |
| B4 | **HERO.** Third shape: documents turned into rows beside the chart | 63 | 0:54 - 1:20 |
| B5 | **HINGE.** The count, and the turn into the decision | 65 | 1:20 - 1:47 |
| B6 | Where it runs, and what is not claimed | 37 | 1:47 - 2:02 |
| B7 | The question | 24 | 2:02 - 2:13 |

Windows are indicative only. **Final beat durations are derived from the measured takes**,
never from this table, per the production rules.

B4 carries the hero window and the slowest read: it is the shape the brief's test turns on.
B5 carries the longest window because it is the turn. B6 is required and precise rather
than interesting, and is read briskly on purpose.

---

## Every beat traced to the primer

Line numbers are `apps/isv-primer/sections/primer.md`. "Lifted" means the primer's own
words survive into the narration; the primer was written to work read aloud and most of
this is its own prose.

| Beat | Primer source | How it was handled |
|---|---|---|
| B1 | L13-19, "Three products, three jobs" and "Notice what each one does not do" | Lifted almost whole. The three jobs are the primer's own sentences. The three gaps are L19 verbatim, except that "In anything we read, Domo has no component that shows a citation" is rendered as "We found no Domo component that shows a citation", keeping the scope from L87's "we found no Domo component that renders a citation". Dropping the scope would turn a finding about our search into a flat absence claim about a third party's product |
| B2 | L83, "Answers over documentation" | "reads the manuals, release notes and closed tickets, and answers with citations" is verbatim. "the one pattern available today" and "the cheapest first step" are the primer's own. The hard part at L83 (ticket history brings customer data into the corpus) is cut, see omissions |
| B3 | L85, "Answers over live application data" | "the answer is a live fact in your database, and copying it makes it stale" and "calls your application's own tools instead, and nothing is stored" are lifted. "Retrieval Agent" kept as the mechanism's real name. The two hard parts (the ABL service layer is the project; identity reads as a service account) are cut, see omissions |
| B4 | L89, "Documents turned into rows" | "the letters, notes and incident reports around them", "Nobody puts them next to the chart", "can return structured rows from documents", "can then join those rows to your tables on a shared key" all lifted. The primer's modal "can" is KEPT on both halves, because this pattern is not available today and the indicative would assert that it is. "An ERP" becomes "your system of record", which L13 establishes as OpenEdge's role, rather than introducing a term the primer does not use in that beat |
| B5 | L35, the thesis, and L29 | "fifteen applied patterns. One is available today. One is not built. Thirteen need you to build the join" is the primer's count verbatim with "you" to "the customer". "price it before you commit" (L35) becomes "a reference a customer can price against". The turn into the decision is mine and is the editorial position argued above |
| B6 | L69, L71, L75 | "only inference and the index run in Progress's cloud" is L69 verbatim and is the lead's 9 Oct tighten, which removed a repeated "cloud". L69's second sentence, "the index built from them rests in Progress's cloud", moves to the on-screen layer: the GM elevated "rests" on 9 Oct 2026, and "run" can read as transient processing where "rests" says the index persists there, which is the distinction a security reader cares about. L71's "We confirmed this with Progress on 8 October 2026. It is not published anywhere" becomes "Confirmed, unpublished, so it carries its date" in the voice, with the full date and the not-published note on screen. L75's three unclaimed modes lifted |
| B7 | Work item `call_to_action` | "Where should we point this next." The brief's own CTA, given the film's own setup |

Nothing in the narration is invented. The only non-primer sentences are B5's turn and B7's
CTA, and both are flagged above.

---

## Use case to real build mapping (hard rule 3, must_show)

Each shape traces to something genuinely built. **Evidence is inherited, not re-measured.**
The sibling film verified this estate on the 8 Oct 2026 `estate_health.py` sweep and I am
quoting that run rather than re-probing: `scripts/estate_health_last_run.json`,
`run_at 2026-10-08T10:37:05Z`, 39 probed, `pass_count` 37, `fail_count` 2,
`coverage.denominator` 60, `coverage.real_answer_path` 35. Verified by reading that file
today. **No metered Progress Agentic RAG answer calls were made for this film** (hard rule
15c: live verification is metered, and the account carried a budget block on 5 Oct).

| Beat | Shape | Build | Live URL | Evidence |
|---|---|---|---|---|
| B2 | Answers over the organisation's own published material, cited, with an honest refusal where the evidence does not reach | `clinic-knowledge-desk` | your-app.fly.dev | 8 Oct sweep PASS with a real grounded answer preview; DAM demo `e0008a0f` |
| B2 | One question read across formats an analyst cannot read: advertisements, podcasts, filings, press | `intel-co-intel` | your-app.fly.dev | 8 Oct sweep PASS; DAM demo `7cdd0844` |
| B3 | A document value fused with a live system value through a real tool call | `cartwright-freight-demo` | your-app.fly.dev | 8 Oct sweep PASS with a real grounded answer preview; DAM demo `3fb67082` describes the signed contract rate fused with the live billed figure via a real MCP call |
| B3 | The Retrieval Agent over the application's own tool source with the caller's permissions enforced | `operator-fleet` | your-app.fly.dev | 8 Oct sweep PASS; DAM demo `4f57a998`; code read by the sibling at `portal/server/agent-proxy.mjs`, `mcp.mjs`, `domain-handlers.mjs` |
| B4 | Structured rows returned from documents by schema-constrained retrieval, exported as data | `arag-taxonomy-builder` | your-app.fly.dev | 8 Oct sweep PASS; DAM demo `50894217`: "generates a hierarchical taxonomy from its content with schema-constrained retrieval calls" and exports SKOS-XL Turtle plus JSON. This is the extraction half of B4 and it is genuinely built |
| B4 | The Domo half | **NOT BUILT, and the film says so** | n/a | Primer L101: the Retrieval Agent cannot query Domo today. B4's narration keeps the primer's modal "can join" and closes on "Today the customer writes it", and the illustration shows the join being authored rather than running |
| B5 | Fifteen applied patterns, one available, one not built, thirteen the customer joins | ISV architecture reference | your-app.fly.dev | `apps/isv-reference/sections/10-opening.md:56-58`, read 9 Oct 2026: "Of the fifteen applied patterns later in this page, one is available today, one is not built, and thirteen need you to build the join" |
| B6 | Three deployment modes, two not claimed | n/a, a stated fact | n/a | Work item objective and messaging house pillar 3. Confirmed with Progress 8 Oct 2026, published nowhere, so the film carries the date on screen |

**Breadth caption population, stated precisely.** The field that lights up in B1 and B5 is
the Field Kit published demo library, listed 9 Oct 2026: **21 published demo entries across
13 industries carrying at least one entry**, behind 17 distinct deployed hosts (three
entries share `your-app.fly.dev`, two share `your-app.fly.dev`,
two share `your-app.fly.dev`). The caption states the population and the date.

**It does not state the 60/39/37/35 estate figures in the same frame as the 21/13 library
figures**, because those are two different populations and a viewer who sees them adjacent
will divide one by the other. One population per frame, named.

---

## Messaging house pillar mapping (must_show)

| Pillar | Carried by | How |
|---|---|---|
| 1. Genuinely agentic retrieval, not a chatbot on a vector store | B3, B4 | B3 is the Retrieval Agent calling the application's own tools rather than reading a copy, which is the sharpest single instance of the pillar. B4 is schema-constrained structured output, not prose |
| 2. Trust you can measure, per query | B1, B2 | B1's "finds things and shows its working" is the pillar compressed to the product's one-line job, in the primer's own words. B2's "answers with citations". The qualitative badge is carried by the ILLUSTRATION in B2 (`threads-and-quality`), with no narration spent on it, and never as a numeral (B34, Field Rule 5) |
| 3. Run it where your governance allows | B6 | Three modes named; hybrid stated precisely as only inference and the index running in Progress's cloud WITH the index resting there; **and where the source documents end up stated as not told to us**, in the voice and as a boundary-straddling marker in the picture; the two unclaimed modes shown as absent |

**Declared gap, not an oversight: the ingestion half of pillar 1 is not in this film.**
Ingestion agents labelling, generating question and answer pairs and extracting a graph is
mechanism, and mechanism is the sibling film's axis, where it is beat 2. Spending 25 words
of a 325-word budget on it would cost one of the three shapes the brief's test depends on.
The sibling carries it; this film does not claim it.

---

## What I left out of the primer, and why

The brief says this choice is the film. The primer is 2,148 words and the narration is 325,
so roughly 85 per cent of it is gone. The cuts are not even: two whole sections are out.

**CUT ENTIRELY: tenancy, the gate is yours (L37-59).** This is the primer's own "if you
take one thing from this page, take this one", and it is the longest section. It is cut
because it is implementation risk an executive cannot act on in a two-minute film, and
because presenting a cross-tenant disclosure behaviour to this room without the architect's
mitigating detail would alarm without informing. It is the sibling film's hero beat and it
belongs there.

I want to be explicit about the risk rather than bury it: **if the executive team sees only
this film, they do not learn that the tenant gate is the customer's to build.** My judgement
is that the fact survives at the altitude this audience works at, because B4 closes on
"Today the customer writes it" and B5 is a counted statement that the joins are the
customer's work. That is the same fact without the incident detail.

**Lead's ruling, 9 Oct 2026: the cut is accepted and the gate is named on screen in B5.**
The reasoning sharpens mine and I am adopting it. My own hinge says which joins are worth
closing is this room's decision, and **the tenant gate is the clearest example of a join
Progress could close unilaterally** - every customer builds it, three times, by three
different routes. At this altitude that is not implementation risk, it is the single most
actionable item the count contains. Naming it makes "a decision this room gets to make"
concrete rather than abstract.

So it goes on the seam marker that enlarges in `the-join-you-build`, as
`The tenant gate. Every customer builds it, three times, three different routes.` No
narration cost, no new geometry, and the same voice-to-image device as the B4 key labels.
The incident detail stays out: the on-screen line says the work exists and recurs, never
what happens when a filter is malformed.

**FACT CORRECTION, 9 Oct 2026 (canon `deployment_modes` v6).** "Hybrid keeps your documents
with you" is NOT something Progress has stated. Confirmed: only inference and the index run
in Progress's cloud, and the index rests there - a statement about what RUNS there, not where
the source corpus is RETAINED. B6a carried the error twice: the voice IMPLIED it ("only X and
Y are in the cloud" invites "so Z is not"), and the picture ASSERTED it by seating the corpus
inside a boundary labelled `Your environment`. Both fixed, b6a re-recorded, and the clause was
not deleted because a viewer fills a hole with the reassurance by default. Detail and the
blocking dependency are in STORYBOARD.md's B6a section.

**CUT: residency's "query in place is not data stays put" argument (L61-67, L73).** The Domo
caching caveat and the two open questions (whether the cloud-side index holds extracted text
as well as vectors, and where inference runs in private cloud) are out. B6 keeps the
deployment fact itself, precisely and with its date, which is what the brief says the film
must not undo. Omitting the open questions does not undo the fact. It does mean the film
carries no "unconfirmed" state, which is why the three-state marker system is sufficient
here, see the state marker note below.

**CUT: shape three, a cited answer beside an analytics surface (L87).** The weakest of the
five for this audience. It resolves to "the two products meet on your own page", which is a
build instruction rather than an outcome, and it occupies the same Domo territory as shape
four while being the less interesting of the two. Shape four supersedes it.

**CUT: the decision cases (L91-95).** One estate for many customers, and customers who
cannot upgrade. This is the cut I would restore first if the film grows: "Retirement dates
remove Progress's support. They do not remove your customers" is the best line in the
primer and it is genuinely an executive sentence. It is out because both cases are about how
the ISV runs its business rather than about where Progress points attention, and the film
has one axis.

**CUT: prompt injection (L105), and this is the cut I am least comfortable with.** No
defence is claimed, and text in a document reaches an agent that can call services. It is
out because for this audience it would be the most alarming eleven seconds in the film and
the least actionable, and because a two-minute film cannot carry the qualification the
primer gives it. **The residual risk is real: an executive who has seen only this film might
repeat an unqualified safety impression externally.** Three things hold against that, and I
would rather state them than assume them: the film never claims safety, in any beat; the
primer is the artifact that travels and it keeps the limit; and the end lockup carries one
on-screen line pointing at the primer as the document with the limits in it, which costs no
narration. **That pointer was approved by the lead on 9 Oct 2026** and is now a binding
storyboard item rather than a recommendation.

**CUT: no accuracy percentage (L107), correctly.** This is a required absence under the hard
limits, so the right handling is that the film never shows a percentage anywhere, not that it
says it has none.

**CUT: no prices or effort estimates (L109), and "when to open the full reference" (L111).**
Both are ISV reader instructions. B7 replaces them with the brief's own CTA.

**KEPT and recast:** the three jobs, the three gaps, three of the five shapes, the count, and
the deployment boundary. That is the spine the work item names, minus tenancy, at executive
altitude.

---

## Visual system

**Inherited whole from `videos/sa-use-cases`, which inherited it from
`videos/what-is-arag`.** I am not introducing a second visual language. Stage, palette,
type, tiles, engine mark, answer card, quality badge and estate grid are that film's, named
here so the storyboard has one source and the pair reads as one system.

The deliberate differences are register, not language:

- **Fewer objects per frame, held longer.** The sibling is an architect's film and its frames
  carry mechanism. An executive frame carries one idea. Same vocabulary, lower density.
- **The ladder is the one new compositional rule.** B2, B3 and B4 share a left-to-right stage
  position and each rung sits slightly higher and wider than the last, so reach and work
  both read as accumulation without a word being spent on it. The three rungs remain on
  stage, dimmed, as each new one arrives.
- **Domo is never inside a Progress boundary**, per the finding above.
- **The grammar is NOT copied here.** `videos/_motifs/GRAMMAR.md` is canonical; this film
  holds a pointer per rule and never a second copy, because two copies of a shared contract
  is how the two films drift. That is why rule 6 was moved out of the sibling's own
  DESIGN.md when it was written.

| Rule | What it governs | Where it binds in this film |
|---|---|---|
| 1 | a product is a solid object with a verb | B1a's three panels; silhouettes never change between shots or films |
| 2 | a join is a line and the STROKE is the state | B1b's amber reaches, B4b's gap, B5a's 1/13/1, B6c's short-dash NOT BUILT. The three strokes are RESERVED - an empty key cell borrowing one was a defect, not a style slip |
| 3 | green is the platform's, amber is the ISV's own code | the ladder argued in colour: B2 all green, B3 introduces amber on the tool call, B4 amber-dominant and ending on the gap |
| 4 | a gate is a gap in a boundary with a token through it | not used in this film; the permissions seam is the sibling's hero |
| 5 | data that crosses a boundary TRAVELS | B6b's index forms, crosses and settles with the derivation line kept |
| 6 | an object whose state we were never told is UNRESOLVED | **B6b's source documents and B6a's private-cloud inference block and boundary.** Outside every boundary, question mark, never moving, because a direction is a claim |

---

## Motifs

**Reused from `videos/_motifs/` and from the sibling's new set, unchanged in geometry:**

- `retrieval-narrowing` (`m-rn`) and `threads-and-quality` (`m-tq`) - B2. Paired, shared
  card and stack coordinates, run short. The badge appears here and carries pillar 2 with no
  narration.
- `agent-over-your-systems` (`m-as`), phase A only - B3. The contract page and the live
  system panel either side of the engine, one labelled tool call out and back, the two values
  meeting in one answer card. Phase B, the two callers and the permissions seam, is the
  sibling's hero and is NOT used here.
- `the-join-you-build` (`m-jb`) - B5, close to verbatim. Fifteen seam markers, one green, one
  short-dashed, thirteen long-dashed amber, then one of the thirteen enlarging as the join draws.
- `three-modes` (`m-3m`) - B6 verbatim, including the two ghost panels taking the `NOT BUILT`
  outline and leaving frame.
- `body-of-knowledge` (`m-bok`) reduced to the engine mark, as the hand-off object between
  beats, identical geometry to `one-engine-every-door` (280x216 at centre 960,560).

**Two motifs this film needs that do not exist yet. Both belong in the shared library, not
here**, per the work item's instruction that a missing motif is added to the shared library
rather than invented locally. I am naming them, not building them, and they are a request to
the lead:

- **`three-jobs-three-gaps`** - three labelled product panels; each performs its own job in
  one gesture (data settling into a store, a question becoming a cited answer, numbers
  becoming a chart); then a dead-grey hole with a SOLID edge opens in each panel where its
  gap is (a hole is not a join, so it takes no reserved stroke), and a long-dashed amber
  connector reaches from each hole toward a neighbour. Performs "each gap is why a second
  product is in the picture", and performs the pivot in B1 that the narration deliberately
  does not spend words on. Constraint: the three panels must not share one boundary.
- **`documents-to-rows`** - a chart with a number on it; a question mark; then documents
  beside it yielding structured rows, each row's key slot filling from the document only
  where the key is present and staying empty where it is not; the rows travelling to the
  chart's data side and joining on the key column. Constraint, and it is a no-fake
  constraint: rows flow OUT to Domo's data side. Nothing reaches INTO Domo, because the
  Retrieval Agent cannot query Domo today (primer L101), and an arrow pointing the wrong way
  would assert a capability that does not exist. And no citation appears on the chart, per
  B1's own finding.

Banned generic set, inherited and enforced: no glowing brains, no node graphs, no
translucent cubes, no particle swarms, no blue circuitry, no illustrated people.

---

## Voice

**One voice, cast by audition on reasoned fit, with measured pace as supporting evidence
only.** The audience is US-headquartered, so the register is neutral American and the
default is not assumed.

The register this film needs is NOT the sibling's. The sibling cast `arthur` for "a peer
with scar tissue", which is right for architects and wrong here. An executive read is
unhurried, declarative and low in affect: a colleague stating a position, with no lift at
the end of sentences and no explainer brightness. The brief's warning is that this audience
detects marketing aimed at itself instantly, and voice is where that detector fires first.

Shortlist, with the reasoning that puts each on it:

- **`ca-maria`** (Melanie, ElevenLabs shared library, American female, middle aged,
  descriptive "conversational, trustworthy"). My pre-audition lean. Middle-aged American and
  registered for trustworthy conversation rather than presentation, which is the closest
  available fit to a colleague briefing a room. The risk is that conversational reads as
  under-powered against a 1920x1080 brand stage, which the audition tests at a slightly
  firmer setting.
- **`arthur`** (American male, middle aged, confident, informative/educational). Carried
  because it is the strongest measured American voice in the registry and it is the sibling's
  cast, so it is the control for "does the pair want one voice". Its registry note records it
  beating `hope` for a room. The argument against is register duplication plus the keynote
  grandeur risk the sibling already flagged, which is worse here than there.
- **`bill`** (older American male, mature, measured, wry). The gravitas candidate. Genuine
  elder-statesman weight and an unhurried read. The argument against is that it is registered
  as THE deadpan voice and was cast for comedy, so it carries a known register risk that only
  the audition can clear.

**Declared control: `hope`**, the factory default, auditioned so the choice is measured
against it rather than compared to an assumption.

**Not eligible:** `jay` and `john` are placeholder voice ids. `david`, `brad_au`, `aimee` and
`milly` are Australian and this audience is not. `daniel` and `bigbill` are British, and
`daniel` is registered as THE voice for a British audience, which argues against it here.

**On sharing the sibling's voice.** I considered it and I am not deciding it in advance.
Sharing buys system coherence across a pair; differentiating buys register fit. Register fit
decides, because the brief names register as the failure mode for this room. If the audition
lands on `arthur` anyway, I keep it and say so. What I will not do is cast `arthur` because
the sibling did, or avoid it because the sibling did.

The audition synthesises one representative line (B5's turn, the hardest line in the film to
read without sounding like a pitch) across the shortlist plus the control, and reports
duration, words per minute and level. **The cast decision is made on the listen, never on a
single number.** Reasoning goes into the build report and the cast voice is confirmed in
`brand/voices.json`.

---

## Floors (gate-read)

- lufs-target: -14
- frozen-share-ceiling: 0.25
- still-run-ceiling: 2.5
- shot-median-floor: 0.05
- illustration-share-floor: 0.60 (concept film default, measured by `video_gate.py
  --storyboard`)
- type-only-run-ceiling: 3.0s

`typography.bare_stage` ceilings are deliberately NOT declared, the same lead decision as
`what-is-arag` (5 Oct 2026) and the sibling: that classifier's own declared blind class is
that flat vector illustration on a flat brand stage reads to it as type on a bare stage, and
this film is entirely flat vector. Its figures are reported as figures with a declared HOLE,
and the type-only question is measured instead by `storyboard.illustrated`, by OCR of the
words on the delivered frames, and by the fresh-eyes and lead eye reads.

Declared held beat: the end lockup, still subject to the 2.5s still-run ceiling, kept alive
by a light sweep and the stage hex drift.

Music-free and caption-free are PROVEN at QA rather than asserted: the PCM gap check at 0.4s
and -45dB must return real gaps in the narration pauses, and the check is proved able to fail
by planting a bed.

---

## Forbidden on screen, the rationale

This section is for a human reader. **The machine-readable list is the one further
down** - the gate triggers on a line containing "must not appear" and then reads only
immediately-following `- item` lines, so a single sentence of prose between the heading
and the list ends it. That is exactly what happened here: this section had a heading, a
sentence, and then the items, so **the gate read ZERO forbidden strings and the OCR
sweep never ran on a single frame.** Reported as a HOLE and correctly not a pass.

On screen or in the narration:

- ARAG as a bare acronym. Every instance is "Progress Agentic RAG"
- Nuclia, nuclia.cloud, Knowledge Box, rag.progress.cloud, aws-ap-southeast
- Any ARR figure, current or target. Any pipeline figure. The enterprise evaluation accuracy
  win. **Any accuracy percentage in any form.** Being internal does not exempt this film
- Any deal count, including the two signed association deals, whose referenceability is
  recorded as uncleared in `content/positioning/operating-inside-progress.md`
- "Progress Domo", "formerly Domo", or any composition placing Domo inside a Progress
  boundary
- **Any reference to the Domo acquisition, in any direction**: not as fact, not as pending,
  not hedged, no dates, no status (lead's ruling 9 Oct 2026; the GM has twice rejected
  acquisition specifics on Domo material and the close is not confirmed)
- A citation rendered on a chart
- on-premises, on premise, offline, air-gapped, except inside B6's explicit `NOT BUILT` ghost
  panels, which exist in order to state that they are not claimed
- delve, leverage, unlock, seamless, game-changing
- em dashes in any on-screen string or written asset

No music. No captions. Australian English in the written assets.

---

## Gates, in order

1. Simulated-authority gate. A separate agent, never this authoring context, simulating a
   Progress executive's lens as an **explicit composite built from the role's structural
   incentives**, never a real named person and never a fabricated quote. Commits to APPROVE,
   APPROVE WITH CONDITIONS or REJECT. A balanced both-sides review is a failed gate.
2. Fresh-eyes viewer gate. Zero build context, answering "would you keep watching" separately
   from "did you understand", and additionally "name three places this belongs", which is the
   brief's own test and the only one that decides whether the film worked.
3. qa-reviewer on the Definition of Pass.
4. The lead's PMM gate.

Then delivery through the queue with a meaningful thumbnail. No interim report reaches the GM:
all three deliverables are reported together (GM, 9 Oct 2026).

## Strings that must not appear
- ARAG
- Nuclia
- nuclia.cloud
- Knowledge Box
- rag.progress.cloud
- aws-ap-southeast
- Progress Domo
- formerly Domo
- acquisition
- acquire
- ARR
- pipeline
- accuracy
- delve
- leverage
- unlock
- seamless
- game-changing
- each already running
- a reference a customer can price against
- stays in your environment
- stay in your environment
- never leaves your
- your documents stay
- keeps your documents

**NARROWED 9 Oct 2026, with a replacement guard, and the reasoning is recorded because
this is a no-fake entry.** The list used to carry the bare string `Your environment`. That
was a PROXY for the real defect, which was never the words: B6a asserted a residency claim
by SEATING THE SOURCE CORPUS inside a boundary carrying that label. A literal string cannot
tell those two pictures apart. It fires on an HONEST frame - the boundary named, the corpus
deliberately OUTSIDE it under grammar rule 6, the membership question drawn in neutral
space - and it would stay SILENT on a dishonest frame that used any other wording for the
same geometry. False alarm and false pass from one entry.

Measured, not argued: `check_residency_geometry.py` samples the /hybrid phase at ten
timestamps and asserts that no corpus object is CONTAINED in a customer-labelled boundary.
It carries three controls - containment fires on a contained box, stays quiet on a
separated one and on a straddling one (membership, not overlap); a population control
requiring exactly one customer boundary, which is what caught the first version calling
the 1920x1080 stage a boundary and reporting 90 false violations; and an END-TO-END plant
that moves the corpus inside the boundary on the live page, proves it moved, and requires
the check to FAIL. It passes: md5 002a87fbeff4, corpus at x850 outside a boundary spanning
200 to 820.

The string entries that remain are the ones that ARE the claim however they are drawn. The
film still names the customer's side, because the hybrid picture needs two named sides to
say that membership is unresolved, and refusing to name it would leave the hole a viewer
fills with the reassuring version.

**Why these and not the others, stated so the list is not mistaken for the whole rule.**
Literal strings only: the prose section above carries rules an OCR sweep cannot test, such
as "no citation rendered on a chart" or "no composition placing Domo inside a Progress
boundary", and those stay with the eye-read.

**`on premises`, `offline` and `air gapped` are deliberately ABSENT from this list**, and
their absence is the inherited declared HOLE rather than an oversight: all three appear on
screen in B6c INSIDE `NOT BUILT` markers, by design, because the beat exists to state that
they are not claimed. **OCR cannot tell a negated label from a claim.** The check for them
is therefore a named manual one - confirm by eye and by OCR position that each appears only
inside B6c's window and only inside a `NOT BUILT` marker, and nowhere else in the film.

`ARAG` as a bare string will match inside "Progress Agentic RAG" only if the OCR reads the
words separately; a hit is a candidate to read, never a finding on its own.
