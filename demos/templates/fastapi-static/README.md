# Clinic Knowledge Desk

A working demonstration built on **Progress Agentic RAG** over **Clinic Limited's
own published website content** (clinic.com), in Clinic's own brand.

Live: https://your-app.fly.dev

---

## What it is

Six genuinely different working surfaces over one body of content - 249 pages read
from clinic.com, including product pages, instructions for use, surgical
technique, the OrthoATI clinical evidence summary, patient information, patient
stories and 196 market announcements published between 2011 and 2026.

| # | Surface | Who it is for | The job it does |
|---|---------|---------------|-----------------|
| 01 | Surgeon desk | Surgeons, theatre teams, clinical specialists | Clinical questions answered from the published material, with the source behind every sentence |
| 02 | Market access positions | Regulatory affairs, market access, country managers | Every market position Clinic has actually published for a product, plus an explicit list of what has not been stated |
| 03 | Claim substantiation check | Marketing, medical affairs, regulatory review | Paste a drafted sentence, find out whether the published content supports it, get wording that stays inside the evidence |
| 04 | Investor signal | Investor relations, corporate affairs | Fifteen years of announcements grouped by theme, with a grounded briefing over any theme |
| 05 | Patient guide | Patients and carers | Plain-language answers from the patient pages only, always returning the reader to their clinician |
| 06 | Evidence library | Anyone who needs the underlying document | The whole set, browsable by product, document type and audience, with semantic search |

## The demonstration narrative

Roughly seven minutes. Each beat lands a different thing.

1. **Home.** 249 pages, 196 announcements, five products. "Nothing here was written
   for the demonstration. It read your website this morning."
2. **Surgeon desk** - click *"What is Remplir made from and how does it support nerve
   repair?"* The answer names purified porcine collagen and the epineurium mechanism,
   with a numbered marker at each claim. Click a marker; it jumps to the source card
   and highlights it. The support badge reads qualitatively, never as a score.
3. **The decline - this is the beat that matters in this industry.** In the right-hand
   rail, click *"How does Remplir compare with a competitor nerve wrap in a head-to-head
   randomised trial?"* The desk returns **Answer withheld** and states plainly that the
   published content does not say. Point out that a system which refuses is the only
   kind a regulated manufacturer can put in front of a surgeon.
4. **Market access** - Remplir is preselected. Seven markets come back with the real
   published position for each, the status chosen from a fixed list, and the
   announcement it was stated in - the same seven, in the same order, every time you ask.
   Then the *Not stated* panel underneath. Switch to
   OrthoATI and the special-access limitation appears rather than an approval.
5. **Claim check - the surface most likely to start the conversation.** Click
   *"Remplir has been shown to restore full sensation in the majority of patients
   within six months."* Verdict: **Not supported by published content**. It quotes the
   real published figure (the 81.1% real-world-evidence result), lists the three
   specific parts of the sentence that overreach, and offers a rewrite that stays
   inside the evidence. Ask the room how long that check takes today.
6. **Investor signal** - fifteen years of announcements as a real stacked count by
   theme. Click a theme for a grounded briefing over just those announcements.
7. **Patient guide** - the same content, a different register and a deliberately
   smaller slice. Note the safety rail and the route back to a clinician.
8. **"How this works"** - top right of every page. Shows the actual request flow for
   that surface, which part is Progress Agentic RAG and which part is application code.

## What is real, and what is not

- **Every answer is generated live** by Progress Agentic RAG at the moment it is asked.
  Nothing on any surface is pre-written, cached or staged.
- **The content is Clinic's own published website.** Nothing was invented,
  summarised or authored for the demonstration.
- **No clinical outcome, efficacy figure, approval, clearance, indication or safety
  statement is generated that the published content does not state.** Every surface is
  instructed to decline instead, and the decline is a designed outcome.
- **No patient data of any kind**, real or synthetic.
- **Classification is deterministic.** Product, document type, audience and region come
  from each page's own address and title, not from a model. The announcement themes are
  keyword rules over real titles. Both choices are stated in the "How this works" panel.
- **Counts are counted, not estimated.** The chart, the facet counts and the corpus
  numbers are arithmetic over the loaded record.

## Progress Agentic RAG mechanisms used

| Capability shown | What actually powers it |
|---|---|
| Grounded clinical and patient answers | Grounded answer call with citations and neighbouring-paragraph context expansion |
| Inline citation markers | Sources come from the grounded answer call; this application aligns each sentence to its strongest matching source to place the marker |
| Confidence badge | Support scoring over the full retrieved context set, rendered qualitatively - never as a number |
| Market positions | Semantic retrieval only - every card is then built deterministically from the retrieved pages' own sentences, with no generative call in the loop for which markets exist |
| Market gaps panel, claim verdict | Structured answer call whose source field is an enum locked to the genuinely retrieved titles |
| Surface scoping (patient guide, announcements, library filters) | Label filter expressions on the retrieval call |

## Two things to know before changing this code

**Market attribution asks whether a sentence is ABOUT a market, not whether it names
one.** A sentence can name a market without stating its position: a coverage recap
listing several markets, a deictic "approval in this market" whose source is about a
different country, a cross-reference to an approval held elsewhere ("complements our
FDA approval"), or a country named only as the SITE of activity cited as evidence for a
position stated elsewhere. All four are rejected in `quote_is_about`, and a market with no
statement of its own is listed as mentioned-only rather than borrowing another market's
sentence. Related: `alias_hit` returns the EARLIEST match across all aliases, not the
first alias that matches - returning a late "Brazil" while "Brazilian" sat beside the
verb put the market 200 characters from its own status word and silently discarded the
real approval.

**The fourth shape (activity-site evidence) was found and fixed 30 Sep 2026, in the same
dispatch as the DACH fix below, and it took TWO passes to get narrow enough.** A U.S. DoD
hospital-network approval read "The approval also follows recent clinical use of Remplir
in 23 surgical procedures...in Ukraine" - Ukraine was never approved for anything; it is
cited as evidence supporting the U.S.'s OWN approval. No existing CROSSREF phrase caught
it, because "follows" governs "clinical use", not "approval". First attempt: reject any
market not named in a differently-titled document's own headline - too broad, and it also
rejected a genuine Singapore-titled document's real aside about Australia/New Zealand
distribution ("sales have grown rapidly since launch"), an independent fact, not evidence
FOR Singapore. Second attempt: reject the bare phrase "clinical use...in X" - also too
broad, and it rejected OrthoACI's own genuine restriction ("OrthoACI is not available for
sale, distribution, or clinical use in the United States"), which contains the identical
phrase with no evidentiary verb governing it - that sentence states the US's own status
directly. `ACTIVITY_SITE` now requires the EVIDENTIARY VERB ("follows", "supported by",
"based on", "demonstrated by") to introduce the activity phrase - present in the Ukraine
sentence, absent from both the ones it broke. Re-verified 15/15 stable on all five products
with both regressions gone and Ukraine correctly landing in mentioned-only, never a card.

**One statement makes one card.** The model can label a single announcement as two markets,
which SPLITS one regulatory position into two cards and implies two independent ones - both
cards individually true, the pair overstating, which on a medical-device regulatory surface is
the more serious direction. Cards are grouped on (source resource, quote) and a group is
collapsed to one card whose designation is the shortest VERBATIM span of the source that names
every market in the group - Clinic's own "EU and UK", not a synonym table. A table would be
false elsewhere in this same corpus: Remplir's EU/UK position is one combined submission to one
notified body seeking two marks, while Striate+ has a genuinely EU-only MDR re-certification.
Two guards on the collapse: a group whose statuses differ is NOT collapsed but reported, and a
span naming a mark, a route or an outcome rather than a territory (CE, UKCA, certification,
MDR, approval, notified body) is rejected in favour of a plain join, so the label can never read
as a regulatory term of art the source did not use as a market name.

**FIXED, 30 Sep 2026 (DAM 89dcd627) - the market SET is no longer the model's to decide, at
all.** The 29 Sep note below this one correctly diagnosed the shape of the problem
("the real fix is to derive the market set deterministically... that is a larger change than a
grouping key") but had not yet been built. It is now: `attribute_markets` takes only `retrieved`
- there is no `entries` argument, and the generative call's schema no longer has a `markets`
field at all. Every canonical market in `MARKET_ALIASES` is checked against the retrieved pages'
own sentences on every run, via `verbatim_sentence`. Same retrieved pages in, same cards out,
every time - verified 15 runs of 15 identical, byte for byte, on both Remplir and Striate+.

Root cause, once found: `verbatim_sentence` ranked candidate sentences by (settled, date, titled,
rank) and fell through to comparing the sentence TEXT itself whenever those tied - which happened
whenever more than one sentence sat near a status word for the same market. One of Remplir's
tied candidates was "...documentation required for MDR certification", a sentence about clinical
evidence that names no market position at all; it only ever won the tie because it happened to
sort later as a string, and when it won, the fix ran `status_from` on it, got nothing, and
correctly declined to add a card - which is how a real, stated EU position could disappear
outright depending on which sentence the tie-break happened to prefer. Fix: `verbatim_sentence`
now requires `status_from(sent)` to be non-empty before a sentence is even a candidate, and the
final tie-break is document order (earliest sentence wins), never sentence text. With the bad
candidate gone, Remplir's EU and UK entries resolve to the SAME real sentence every time and
merge into one card, exactly as they should for one combined submission.

The EU/EEA case needed one more thing: `MARKET_ALIASES` never had an "european economic area"
key. The old design could still show it, because the model was free to propose any market name in
free text and the verification fallback accepted an unrecognised name by searching for it
literally. Once the model is out of the loop entirely, a market absent from `MARKET_ALIASES`
can never be found - which silently dropped the EEA card the moment the fix landed, in EVERY run,
not intermittently. Added as its own key (`["european economic area"]`, no bare "eea" alias, to
avoid the kind of false hit the existing aliases already guard against). Confirmed after: both
`European Union` and `European Economic Area` render as two separate, correctly-dated cards on
Striate+, 15 of 15 runs.

**Everything in the two notes above this one still holds and is unchanged by the fix**: the
ABOUT-vs-names-in-passing discipline, the one-statement-one-card collapse and its two guards, and
the not-a-territory rejection on the merged label. They now run against a deterministically
chosen set of sentences instead of a model-chosen one, nothing else changed in how a card gets
built once a sentence is picked.

**Known side effect: card ORDER changed, and it is no longer arbitrary.** Cards now render in
`MARKET_ALIASES` dict order (United States, Australia, Canada, ... ), not whatever order a
generative call happened to list them in. Before this fix, Remplir's captured demonstration video
(`videos/clinic-overview`) shows Australia's card first because that is what the model
happened to return on the take that was filmed - `crops.json`'s `au_card` region is a
position-based crop, not a content-based one. United States now renders first for Remplir. The
shipped video file is a frozen render and is unaffected by this change, but a future recapture of
that beat will need `au_card` re-measured against the new first card, or re-targeted at whichever
card is actually Australia's now (second, not first). Flagged to the lead rather than fixed here,
since it is the video pipeline's file, not this application's.

**CLOSED, 30 Sep 2026, same dispatch (DAM 89dcd627) - the DACH gap above.** "First Sales of
Striate+™ in DACH Region" (2025-03-26) states first commercial sales in Germany, Austria and
Switzerland together, as one event. **The obvious fix - three country aliases - is the wrong
fix**: it would verify true against this one sentence three times and render three cards off one
statement, the same defect this file's EU/UK merge exists to prevent, in the opposite direction
(hard rule 3's "splitting one source statement into N cards overstates it"). Added instead as ONE
canonical key, `"dach region": ["dach"]`, taking its label from the source's own region name
("DACH Region") rather than a synonym table - the same discipline the EU/UK merge already
follows, for the same reason: this corpus already proves a country-to-region table is unsafe (a
sibling product traces to a genuinely EU-only announcement), and it would be exactly as unsafe the
other direction. If Clinic ever announces one of these three countries alone, that is a new,
separately dated document and a different card, never a relabelling of this one. `"dach"` appears
nowhere else in the 249-page corpus (checked), so the alias cannot pick up an unrelated page.

**Closing this also surfaced a genuine, separate retrieval defect - the alias alone would not
have shown the card.** The DACH page is correctly labelled `Product=Striate+` in the live KB, but
the market-access retrieval query (`_market_query`) did not return it at `top_k=26`: the same
query against the same filter returned 11 results at `top_k=26` and 17 at `top_k=50`, stable
across four calls each, with the DACH page (relevance 0.211, rank 14 of 17) absent below
`top_k=40` and present at and above it. This is not a truncation of one fixed ranked list -
raising `top_k` genuinely widens which candidates Nuclia returns, not just how many of a stable
list. Fixed by raising both market-access `find` calls to `MARKET_TOP_K = 50`, with margin above
the measured 40-result floor. Re-verified stable and unchanged on every OTHER existing card across
all five products at the new `top_k` (see the verification run below) - widening retrieval adds
lower-relevance pages to the candidate pool, none of which out-ranked an existing market's real
winning sentence.

**UPGRADED FINDING, same check:** the stray URL in this one document is not isolated. A corpus-wide
scan for embedded links outside clinic.com/ASX found **52 distinct non-Clinic domains across
38 of the 249 documents (15%)**, many in the shape of link-spam (`oyoslot4.com`, `ovodewa7.com`,
`slot88ku1.com`, `oyo88s.com` and similar), scattered through otherwise-genuine ASX announcements,
Q&A pieces and media pages - not concentrated in one crawl batch or one document type. This reads
as a crawl-time or source-side injection artefact rather than anything Clinic published, but the
scale is materially different from "one stray link" - the lead's original call was made on that
narrower finding. Left alone here regardless, per the same reasoning: none of the winning sentences
on this surface's cards contain one of these URLs (checked across all five products' cards this
session), hand-editing corpus text is a different and riskier change than a config addition, and it
is out of this fix's scope either way. Not checked: whether any OTHER desk (surgeon, investor,
evidence library) ever surfaces one of these URLs in a generated answer or excerpt - flagged for the
lead to route as a corpus-integrity item, not resolved here.

**Market access was deliberately NOT given the grounding cross-check, and that is a
judgment rather than an omission.** Its product filter is relevance scoping, not an
entitlement - no reader is excluded from another product's pages - and the surface already
carries a stronger guarantee than the cross-check would add: every card's quote is verified
verbatim against a genuinely retrieved page, the source is enum-constrained to real retrieved
titles, and the status is re-derived from the quoted wording. Adding an entitlement guard
there would check a weaker property than the one already enforced.

**Access-scoped surfaces carry a server-side grounding cross-check, not just a filter.**
The patient guide and the investor digest both pass a label `filter_expression`, and that is
layer one only: the grounded answer call does not honour a filter as reliably as retrieval
does, so an excluded page can ground an answer intermittently. `grounded_answer` takes an
`allowed` set of resource ids and, before composing anything, checks every citation AND every
retrieved resource against it. If anything outside the entitlement grounded the answer the
WHOLE response is withheld server-side - no answer, no sources, no sentences, no support
reading - in the decline's own register, revealing nothing about a filter having tripped.
The allowed set is derived from the same (labelset, label) pairs that build the filter, so the
two layers cannot drift apart.

The patient entitlement is ONE rule, `Audience = Patient`. It was an OR across audience and
document type, and that was leaky in the SCOPE DEFINITION rather than in the guard: a page at
`/practitioners/<product>/patient-information/` carries doctype "Patient information" while its
audience is Practitioner, so four such pages satisfied the OR on a document-type coincidence.
An entitlement on a single axis cannot be satisfied that way. Measured: 11 of 249 resources in
scope, 0 practitioner pages inside.

Proven both directions, because a guard that has never fired is indistinguishable from a broken
one: 20 of 20 runs of the filmed question served cleanly with zero out-of-scope grounding, and
5 of 5 runs with layer one removed were withheld with zero sources and zero sentences.

**A MODEL REFUSAL carried the full retrieved payload until 1 Oct 2026, and that was the
sharper half of this whole area.** The scope withhold above was built to return nothing from
the start. The model's own "NOT IN PUBLISHED CONTENT" refusal was not: the response was
composed in full, labelled `decline: "not_published"` perfectly honestly, and shipped every
retrieved card to the client. The patient desk then rendered them under a heading reading
*"Sources read for this answer"* - asked **"which hospitals near me offer this procedure?"**
it correctly refused, and beneath the refusal sat seven real patient pages whose excerpts
name Perth Children's Hospital, a named surgeon, and Perth. Nothing was fabricated and every
card was a real page; the composition did the lying, and a patient reads those cards as the
list they just asked for. Four surfaces shared it - patient guide, surgeon desk, VAC draft,
investor digest - because all four route through `grounded_answer`.

The fix is one function. `declined(answer, reason, scoped)` is now the ONLY way the
application emits a declined answer, and both decline reasons go through it, so no call site
*can* emit a decline that still carries sources, sentences, a support reading or a confidence
badge. The refusal returns at the same point the scope cross-check returns - before anything
is composed - so the citation alignment and the support score are never computed for a
refusal, which also made declines faster. The two events stay distinguishable
(`not_published` vs `scope`), because the client's footer is keyed on them and they mean
genuinely different things. Removing the option is what stops a fifth surface repeating it;
remembering the rule is not.

The claim check had no decline path at all. Retrieval never returns empty - it returns scored
junk trailing towards zero - so an off-topic claim produced a verdict plus six unrelated
"pages checked" cards reading as the evidence for it. It now thresholds the closest match at
0.35, the same threshold and reason as the submission reviewer, and declines below it with no
verdict, no quote and no cards. Deliberately NOT the "Not supported by published content"
verdict: that is a finding about the published content, and finding nothing to judge a claim
against is not evidence that the claim is unsupported.

**The second defect on that panel was found by asking what else was wrong, and nobody
reported it.** The patient safety rail read *"This is general information from Clinic's
published patient pages. It is not medical advice..."* - and on a decline there is no "this".
It told a patient that a reply they cannot see is general information from the patient pages.
Identical shape to the decline footer that asserted what the corpus contains: true when
written, because it was only ever written for the answer path. The clinician route matters
more on a decline, not less, so only the false half goes.

Controls, all live in `scripts/verify_release.py`: positive (the hospitals question - zero
sources, sentences, statements and support reading in the payload, zero `.sourcecard` nodes
in the rendered DOM), negative on the same surface (a real patient question still returns its
sources and still renders its cards - without which a fix that simply deleted the sources
payload would pass the positive control perfectly), look-alike (the unscoped practitioner
refusal also carries nothing, while the `scoped` flags stay distinct so the footer cannot go
wrong on one path), and an injected decline-that-still-carries-sources, because with the
server fixed the client's second-layer gate never has anything to hide and would otherwise be
indistinguishable from not existing. Proven failing: restoring the real regression produces 5
findings and exit 1 while every negative control still passes.

Worth recording how the false pass was caught, because it was in the new check rather than in
the app. The positive control asserted `"Sources read for this answer" not in text` - and
`innerText` reflects CSS `text-transform`, `.sect h4` is uppercase, so that string can never
match what renders and the assertion passed whatever was on screen. The NEGATIVE control
failed on its first run and that is the only reason it surfaced. Compared case-folded now via
`SRC_HEAD`: the unit was wrong, so the unit was converted rather than the assertion loosened.

**The VAC review is withheld by the CLIENT, not the server.** `/api/vac-desk/draft` and
`/api/vac-desk/review` are independent, so the review endpoint has no way to know the
draft declined and will still return its gaps. The UI suppresses the whole review when
the draft declines; there is no server-side guard. The gaps are honest content rather
than assertions, so this is safe - but do not assume a server-side check that is not
there. The server-side guard that DOES exist is on `strongest_point`, which must be
verbatim-verifiable against a retrieved page or it is dropped.

The reason for that suppression is worth keeping: a true sentence placed under a declined
answer reads as an answer. Not a fabrication - a correct statement made misleading by
where it sits.

QUEUED, deliberately not done before the 29 Sep 2026 customer meeting: give the review
endpoint its own server-side decline, so the guarantee does not depend on the client
withholding a panel. It was left because the gaps are generic committee asks rather than
claims about the product, the UI already withholds them with a line saying why, and the
fix costs an extra model call on a path no visitor can reach. It is still wanted - a
client-side withhold and a server-side decline are different guarantees.

| Library search | Semantic retrieval, thresholded application-side so an irrelevant query honestly returns nothing |

Cheapest capable generative tier throughout (`chatgpt-azure-4o-mini`), pinned explicitly
on every call. **No Data-Augmentation task and no graph extraction was registered** -
nothing in this build runs a model call per paragraph across the corpus.

## Running it

```bash
cp .env.example .env          # fill in the knowledge-base coordinates
pip install -r requirements.txt
uvicorn app:app --port 8099
```

The retrieval credential is read server side only. The browser talks to this
application's API and never to the retrieval service.

## Reset

```bash
python scripts/reset.py            # re-crawl clinic.com and re-ingest
python scripts/reset.py --purge    # delete every resource first, then re-ingest
flyctl deploy --ha=false --app clinic-knowledge-desk
```

A demonstration run never mutates anything, so a reset is only needed after the
published site changes.

## Brand

Palette, typography and shape were sampled from the live clinic.com DOM, not
approximated: display blue `#004D7E`, mid blue `#1D6390`, olive `#AFB936`, body grey
`#5F5F60`, the blue-to-olive gradient rule, 16px card radius, pill controls, and the
real Clinic logo, favicon and product photography taken from the site. Headings use
Poppins and body copy Source Sans 3, both loaded by clinic.com itself.

Built for Clinic's own field demonstration. Internal asset - not published as, or
on behalf of, Clinic.
