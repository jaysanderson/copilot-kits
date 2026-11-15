# ARAG Discovery & Qualification Framework

**For:** the ARAG overlay sellers and solutions engineers. **Owner:** sales-enablement.
**Version:** 2.0 (full rebuild). **Date:** 5 September 2026. **Supersedes:** v1.0,
10 August 2026 (retired - too thin to run a real discovery call from; rebuilt from the
ground up, not patched).

**Grounding:** `content/positioning/messaging-house.md` (positioning, pillars, personas),
`content/positioning/operating-inside-progress.md` §6 (the field record this framework is
built on), `content/positioning/gtm-strategy.md`, the battlecards under
`content/enablement/battlecards/`, and `nuclia-mcp` for every product-capability claim
used in a question or a defusing line. Cross-referenced with `roi-value-model.md` (the
POV this framework hands off into) and `objection-handling-guide.md` (the objections this
framework is built to surface early, not dodge).

---

## 1. The premise - what this framework is actually solving for

The single fact that should shape every discovery call: **capability wins the room almost
every time. Deals die on the commercial path** - no clear path to production, no budget
line for "RAG anything," and "we can build it ourselves" [operating-inside-progress.md
§6]. Discovery's job is therefore not to prove ARAG works. It is to:

1. Find the **one feature** worth starting with - never pitch the whole platform.
2. Confirm there is a **real budget line** it can sit inside.
3. Confirm there is a **named owner** who can take the first feature into production.
4. Surface the **three loss reasons** early enough to defuse them, not discover them at
   the eleventh hour of a stalled pilot.

The buyer psychology behind this: most people an ARAG seller meets **want to implement AI
and are not sure where to start** [operating-inside-progress.md §6]. A good discovery call
does not argue them into believing AI works - it hands them a specific, small, fundable
starting point. That is the whole method.

**The target-profile signal, verbatim from the field:** "any org that is content heavy and
personnel light" [operating-inside-progress.md §6] - medium-size enterprises, government
authorities, research bodies, professional associations. Screen for this signal in the
first minute of any call: does this organisation have more content than people to process
it? If yes, the rest of this framework applies directly. If the org's problem is genuinely
structured-data analytics rather than unstructured knowledge, this is a different
conversation - see the disqualifiers in section 6.

---

## 2. The framework - six categories, asked in this order

This is a MEDDIC-style structure, adapted to what actually kills or saves ARAG deals. Work
through all six on every real opportunity; do not skip ahead to a demo because the first
two feel strong - the commercial categories (4-6) are where deals actually die.

| # | Category | What you are confirming | Where it shows up later |
|---|---|---|---|
| 1 | **Content & personnel profile** | Genuinely content-heavy/personnel-light; real content exists to point ARAG at | Qualifies the target-profile fit itself |
| 2 | **Pain and use-case shape** | A specific, nameable pain in the buyer's own words - not "we want to explore AI" | Becomes the ONE feature (§4) |
| 3 | **Economic buyer and budget anchor** | Who owns the money, and which existing line the spend fits | roi-value-model.md §5 |
| 4 | **Decision criteria and process** | How they will actually choose - competitive evaluation, technical bake-off, procurement gate | objection-handling-guide.md, battlecards |
| 5 | **Champion and path to production** | A named owner who takes the first feature live, and someone internally who will carry the message when you are not in the room | roi-value-model.md §4 |
| 6 | **Build-inclination / competitive posture** | Is engineering already building, or is a named competitor already in the room | objection-handling-guide.md §1, §4 |

Score each category **strong / developing / weak** as you go (section 5 turns this into a
go/no-go). A category scored weak is not a reason to walk away on the spot - it is the
thing you work on before the next call, using the disqualifiers in section 6 to tell the
difference between "needs more work" and "not this deal."

---

## 3. Persona-mapped qualifying questions

Three personas carry almost every ARAG discovery call: the **CIO** (economic buyer), the
**Solutions Architect** (technical champion), and the **ICT & Digitalisation Leader**
(the buyer archetype the field record names most often - a real title from one deal,
generalised as the archetype for a similarly-scoped leadership role in a medium
organisation, government authority, research body or association)
[operating-inside-progress.md §6]. The full eight-persona roster (adding the Marketing
Professional, Product Manager, Research Professional, Partner and Divisional CTO
personas) lives in the Kitforge Personas & Positioning DAM pages - open the specific
persona page before any call where you know who you are meeting.

### CIO (economic buyer)

Leads with risk, sovereignty and total cost - not features.

- "Where does your organisation currently store more knowledge than your people can
  practically search - policies, case files, records, correspondence, recordings?"
- "If your board or executive has an AI mandate already, what has actually shipped under
  it, and what is still stuck at 'exploring'?"
- "What can never leave your environment - and does that mean storage location, or does
  it mean the model itself must never process your data outside your walls?" (This
  distinction decides whether the answer is hybrid or full on-premises - confirm which
  before promising a deployment shape.)
- "If two vendors claimed equally good answers, how would you actually tell which one was
  telling the truth?" (Opens the door to REMi - a live, per-query, measurable answer, not
  a claim [messaging-house.md pillar 2].)
- "What existing budget line would a knowledge-retrieval capability sit inside, if we
  found the right first feature together?"

### Solutions Architect (technical champion)

Leads with architecture, integration and honest limits - never a features list.

- "Walk me through what your current search or retrieval experience actually returns
  today - documents, or answers?"
- "If you were building this yourselves, what would your stack look like - and where
  would your own team spend the most engineering time you'd rather not?" (Surfaces the
  DIY-build-cost value lever directly [roi-value-model.md §2].)
- "Do you need the AI to just answer questions, or does it need to take action - call your
  own systems, trigger a workflow? If the latter, under whose permissions?" (Opens the
  RAO/MCP conversation - ARAG's agent calls your own tools under your RBAC, not a
  homegrown planner [messaging-house.md pillar 1].)
- "How would your team currently know if a generated answer was wrong, and diagnose
  *why* - a retrieval miss, or a generation error?" (Opens REMi's diagnostic value, not
  just its score [messaging-house.md pillar 2].)
- "What does your ingestion actually need to handle - PDFs, recordings, structured
  records, all three? Do you need entities and relationships extracted, or just search?"
  (Scopes which ingestion agents - Labeler, Generator, Graph Extraction, Generate Q&A -
  matter for this build; source: nuclia-mcp KB, ingestion-ai-agents page, re-queried
  5 Sep 2026.)

### ICT & Digitalisation Leader

Leads with the show-and-tell motion the field record proves works
[operating-inside-progress.md §6] - discuss use cases like a lego kit, then land on one.

- "Where does your team lose the most real time today - finding documents, records,
  systems, or recordings, rather than acting on what they find?"
- "If one search box across your whole estate could answer a question instead of listing
  files, where would that help first?"
- "What has your leadership actually said about AI - is there a mandate, and has anything
  shipped under it yet, or is it still a slide?"
- "What can't leave your environment, and what are the governance and residency lines you
  are already working inside?"
- "If we picked ONE feature to prove this on in the next few weeks - not the whole
  platform - what would you want it to be?" (This is the one-feature-first question every
  call should reach - see section 4.)

---

## 4. Surfacing a fundable first feature - the one-feature-first doctrine

**The sales motion that works, verbatim from the field:** show ARAG as a lego kit,
discuss use cases openly, and always suggest **one feature to start with, never
everything at once** [operating-inside-progress.md §6]. This is not a simplification for
the buyer's benefit alone - it is what makes the deal fundable (fits a small existing
budget line, entry under US$1,000/month - see `roi-value-model.md` §5) and what makes it
provable (a scoped POV can actually measure one thing well).

**How to find it in the call, not after it:**

1. Listen for the pain named **in the buyer's own words** during category 2 discovery,
   not a feature you proposed. "Members can't find our CPD rules" is a real first
   feature. "We want to explore AI" is not - it has no feature in it yet.
2. Ask directly: **"If we proved this on one thing in the next few weeks, what would you
   want it to be?"** If the buyer cannot answer, propose one back from what they told you
   earlier in the call, and ask them to react to it rather than generate it cold.
3. Check the feature against three tests before treating it as qualified:
   - **Nameable** - a specific pain in specific words, not a category.
   - **Provable** - real content exists today that a POV can point ARAG at.
   - **Ownable** - someone in the room (or reachable) could plausibly own it live.
4. Write the feature down in the call notes in the buyer's own language, not yours - you
   will use these exact words in the POV plan and, later, in the ROI business case
   (`roi-value-model.md` §1).

---

## 5. Early defusing of the three loss reasons

Do not wait for these to surface as objections late in the deal - raise them yourself,
early, while they are still cheap to fix. Full response detail lives in
`objection-handling-guide.md` §1-3; this section is what to do about each **inside
discovery itself**, before it becomes a stalled deal.

**"No clear path to production."** Ask directly in the first call: "If this works, who
takes it live, and what would that actually look like?" If nobody can answer, that is not
a reason to keep pitching - it is the thing to fix before proceeding. The fix is
structural, not persuasive: design the POV so its one feature **is** production release
one, not a throwaway pilot that needs a second approval to go live
[roi-value-model.md §4].

**"No budget line for 'RAG anything'."** Ask which existing line the spend would sit
inside **before** proposing next steps - service improvement, web/content budget, product
roadmap/COGS for an ISV, or an AI mandate looking for its first defensible step
[roi-value-model.md §5]. If you cannot name an existing line by the end of discovery, you
do not yet have a qualified deal - you have an interested buyer with no path to a
purchase order.

**"We can build it ourselves."** Do not treat this as a threat to argue down. Ask how far
along their own build actually is, and take the build-vs-buy conversation head-on using
the honest engineering-time and quality-instrumentation argument, never a claim that DIY
is impossible [objection-handling-guide.md §1]. Where a team is genuinely staffed,
resourced and already building, the strongest discovery move is proposing the ARAG POV as
a parallel benchmark for their own build to beat, not a competitive replacement for it.

---

## 6. Qualification scorecard and disqualifiers

### Scorecard

Score each category from section 2 **strong / developing / weak**. A deal with two or
more **weak** commercial scores (categories 3, 5 or 6) will stall even when categories 1
and 2 are strong and the demo lands well - fix the commercial score before investing more
selling time, not after.

| Category | Strong | Weak - fix before proceeding |
|---|---|---|
| Content & personnel profile | Genuinely content-heavy, personnel-light; real content available | Structured-data-only problem, or no real content to point ARAG at |
| Pain and use-case shape | A specific pain in the buyer's own words | "We want to explore AI," no nameable first feature |
| Economic buyer & budget | An existing, named budget line | Needs a brand-new line item approved from nothing |
| Decision criteria & process | Clear evaluation process, ARAG genuinely in it | No visible process, or a rubber-stamp "just checking the market" |
| Champion & path to production | A named owner who can take the first feature live | A pilot with no owner, or "innovation team" custody with no route to a live surface |
| Build-inclination / competitive posture | Named and addressed directly, not avoided | Engineering already deep into a build with no appetite to evaluate alternatives |

### Disqualifiers - walk away early, kindly

- **No real content estate.** The value levers this framework and the ROI model rely on
  need actual unstructured or mixed content to point ARAG at - a purely structured-data
  analytics ask is a different product conversation, not an ARAG opportunity forced to
  fit.
- **Wants a strategy engagement, not a working feature.** Consultancy-shaped asks
  ("help us think about our AI strategy") stall inside this framework - leave the door
  open for when they have picked a use case, rather than trying to sell a strategy
  engagement ARAG is not built to be.
- **Demands a guaranteed accuracy percentage before any evaluation.** No accuracy
  percentage is published or ever quoted [field rule 5; messaging-house.md §6] - if a
  procurement gate requires one before shortlisting, that is a real, current gate this
  answer does not clear, not a framing problem to argue past
  [objection-handling-guide.md §5].
- **No conceivable owner, anywhere.** If nobody in or near the room can plausibly own the
  first feature in production, there is no champion to build and no path to close -
  disqualify rather than keep running a demo loop against an unowned pilot.

---

## 7. The next-step map - from qualified to moving

1. **Matched demo, not a generic one.** Pull the right proof from the Field Kit
   demo-to-install-base map for this buyer's vertical and use case - a cited answer on
   screen in their world, not a generic showcase.
2. **One-feature POV with the metric agreed first.** Hand off to `roi-value-model.md` §1
   and §4: agree the metric before the POV starts, run it on the buyer's own content, and
   treat the POV's one feature as production release one.
3. **Invite the competitive evaluation, don't dodge it.** Where a competitor is genuinely
   in play, propose a head-to-head on the buyer's own content and let measured quality
   decide - this is the same motion that won the one enterprise deal on record where ARAG
   was directly evaluated against rivals [operating-inside-progress.md §6]. Pull the
   named competitor's battlecard from `content/enablement/battlecards/` before that call.
4. **The champion question, every time, before leaving the room:** "Who else do you know
   facing this same problem?" Professional associations and referral networks are where
   the warmest paths into new deals have actually come from
   [operating-inside-progress.md §4b]. Win the person, not just the deal in front of you.

---

## Source map

- **Field record (three loss reasons, capability-wins-the-room, buyer psychology,
  one-feature-first doctrine, target-profile signal, champion/referral dynamic)** -
  `content/positioning/operating-inside-progress.md` §4b, §6.
- **Positioning statement, pillars, persona message shapes** -
  `content/positioning/messaging-house.md` §1-3.
- **Budget anchoring, POV-as-production-release-one, value levers** -
  `content/enablement/roi-value-model.md` §1, §2, §4, §5 (this rebuild).
- **Objection detail for the three loss reasons and beyond** -
  `content/enablement/objection-handling-guide.md` §1-3 (this rebuild).
- **Ingestion agents (Labeler, Generator, Graph Extraction, Generate Q&A, LLM Security,
  Content Safety)** - `nuclia-mcp` knowledge box, `nuclia.com/ingestion-ai-agents/`,
  re-queried 5 September 2026.
- **REMi, RAO/MCP architecture** - `nuclia-mcp` knowledge box, `nuclia.com/rag-quality/`
  and `nuclia.com/rag-agents/`, re-queried 5 September 2026, consistent with
  `content/enablement/battlecards/progress-agentic-rag-home-battlecard.md` §2.
- **The eight-persona roster** - Kitforge Personas & Positioning DAM pages (canonical;
  not duplicated here).

---

## Change log

- **2026-09-05** - v2.0. Full rebuild per GM directive (5 Sep 2026): v1.0 was too thin to
  run a real call from. New six-category MEDDIC-style structure, persona questions
  rewritten and expanded for the three named personas (CIO, Solutions Architect, ICT &
  Digitalisation Leader), the one-feature-first doctrine given its own worked section, a
  scorecard with explicit strong/weak criteria, and every product-capability question
  re-verified against `nuclia-mcp` (ingestion agents, REMi, RAO/MCP) rather than asserted
  from the prior draft.
- **2026-08-10** - v1.0 (superseded). First draft, built from the GM field interview.
