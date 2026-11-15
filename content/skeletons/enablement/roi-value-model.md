# ARAG ROI & Value Model

**For:** the ARAG overlay sellers, built to be walked through live in a call with the
buyer. **Owner:** sales-enablement. **Version:** 2.0 (full rebuild). **Date:**
5 September 2026. **Supersedes:** v1.0, 10 August 2026 (retired - too thin; rebuilt from
the ground up, not patched).

**Grounding:** `content/positioning/messaging-house.md` (pillars, Locked Facts),
`content/positioning/operating-inside-progress.md` §6 (the field record this model
answers), the `progress-agentic-rag-home-battlecard.md` (pricing re-verified 6 Aug 2026),
and `nuclia-mcp` for every underlying capability claim. Cross-referenced with
`discovery-qualification-framework.md` (where these inputs get asked) and
`objection-handling-guide.md` §2-3 (the objections this model directly answers).

**The honesty rule, read before anything else:** nothing in this document is a benchmark.
Every input on the buyer's side is theirs to supply, not ours to assume, and every figure
in the worked example is explicitly marked **illustrative**. No accuracy percentage
appears anywhere in this model, because none is published [field rule 5;
messaging-house.md §6] - answer quality is proven live with REMi and a cited-answer demo,
never asserted as a number. This model's credibility comes precisely from arriving
**empty**, not pre-filled with vendor numbers - the POV is what fills it in with the
buyer's own.

---

## 1. How to use this in a call

1. **Qualify first.** This model assumes discovery has already found a nameable first
   feature and a real budget line (`discovery-qualification-framework.md` §3-4). Do not
   open this model cold in a call where that has not happened yet.
2. **Pick the lever that matches the deal shape** (section 2) - one, not all five. A
   single, well-measured lever produces a more defensible business case than a hand-wavy
   pass across all of them.
3. **Fill every input with the buyer's own number**, asked as a discovery question. Where
   they genuinely do not know a number, write "measure in POV" - that line becomes the
   POV's agreed success metric (section 4), not a gap you paper over with an assumption.
4. **Anchor the cost to an existing budget line** (section 6) so the purchase is a
   reallocation, never a request for a brand-new line item.
5. **Hand them the model, filled with their numbers, as their own document.** The goal is
   a business case the buyer can defend to their own budget owner without you in the
   room - not a slide you presented once.

---

## 2. The five value levers

Every lever below maps to a real, named commercial pattern already proven in the field
record [operating-inside-progress.md §6, §4b]. Pick the one that matches the deal in
front of you.

### Lever 1 - Time-to-answer (internal knowledge work)

For organisations that are content-heavy and personnel-light: staff spend real, countable
time hunting through documents, wikis, tickets, case files and recordings for answers
that already exist inside the organisation's own content.

**Inputs (all buyer-supplied):**
- Number of people doing knowledge lookups regularly
- Lookups per person per week
- Minutes saved per lookup when the answer is returned directly, cited, instead of a list
  of documents to open and read (measure in POV - never assume this number)
- Loaded hourly cost per person

**Formula:** `people × lookups/week × minutes saved ÷ 60 × hourly cost = value per week`

### Lever 2 - Deflected effort (customer- or member-facing self-serve)

For service desks, member associations and citizen-facing services: a grounded, cited
assistant on the public-facing site answers questions that today generate a call, an
email, or a support ticket.

**Inputs:**
- Monthly contacts of the types a retrieval-grounded assistant can genuinely answer
  (not all contact types - be specific about which ones)
- The fraction realistically deflected (measure in POV; never assume a deflection rate)
- Fully loaded cost per contact (call, email or ticket)

**Formula:** `contacts/month × deflected fraction × cost per contact = value per month`

### Lever 3 - Faster path to production (versus a DIY build)

This lever prices the **time** side of build-vs-buy, distinct from Lever 4's engineering
**cost** side. A DIY retrieval stack - framework, vector database, chunking, reranking,
citation, all hand-integrated - takes real engineering months before it answers a single
grounded question in production [messaging-house.md §5]. ARAG's Starter tier is
self-serve and live inside a 14-day trial, with ingestion agents (Labeler, Generator,
Graph Extraction, Generate Q&A) and REMi quality measurement built in, not built by the
buyer [nuclia-mcp KB, ingestion-ai-agents and rag-quality pages, re-queried 5 Sep 2026].

**Inputs:**
- Estimated months to a working, grounded, quality-measured DIY pipeline (the buyer's own
  estimate, or their engineering team's)
- Fully loaded monthly cost of the engineering team that would build and maintain it

**Formula:** `estimated DIY months × loaded monthly engineering cost = the time value of
starting now instead of building first` - a value that only accrues once, at the start of
the relationship, but is often the single largest number in the whole model for a
platform-team buyer.

### Lever 4 - Avoided DIY-build cost (the engineering opportunity cost)

Distinct from Lever 3: this lever prices what the buyer's engineers would otherwise spend
their time on, ongoing, not just the one-time build. A DIY stack has **no native quality
instrumentation** unless the team builds one - REMi ships this out of the box
[messaging-house.md §2].

**Inputs:**
- Number of engineers who would otherwise build and maintain retrieval infrastructure
  (ingestion, chunking, retrieval, reranking, citation, an eval harness)
- Fraction of their time this would consume, ongoing (not just at launch)
- Fully loaded cost per engineer

**Formula:** `engineers × time fraction × loaded cost = ongoing avoided cost` - this is
the honest "what would they otherwise be doing" number, and it is the number most DIY
conversations skip, because engineering time is rarely priced against a vendor bill
honestly [messaging-house.md §3, DIY comparison table].

### Lever 5 - Product economics (ISV embed)

This lever is revenue, not cost avoidance: an AI feature (cited search, a grounded
assistant, an in-product answer surface) that an ISV's own end customers pay for, or that
measurably improves retention.

**Inputs:**
- Number of end customers the feature would reach
- Monthly price uplift, or the retention effect, of the AI feature (the ISV's own
  pricing/retention assumption - never ours)
- Expected adoption rate among those end customers

**Formula:** `end customers × uplift × adoption = incremental revenue per month.` The
unit cost per end customer is not modelled here - it comes from measured consumption in a
pilot across two or three real end customers, never from a guess (see section 4).

**One consistent discipline across all five levers:** usage-based consumption
(section 3) means the cost side scales with actual measured use, not with a seat count
that grows independently of value delivered [messaging-house.md pillar 3]. This is the
structural argument every lever shares against a per-seat competitor - the model does not
need a sixth lever for it because it is already priced into every one of the five above.

---

## 3. The cost side - governed figures

- **Starter: US$700/month.** The entry tier; the first feature almost always starts here.
- **Pro: US$1,925/month** for larger indexed estates and the fuller AI-task set.
- **Enterprise: custom** - relevant once deployment mode, scale or an on-premises
  conversation starts.
- **Consumption is usage-based (Nuclia Token), not per-seat** - the token rate should be
  re-verified live before quoting; the messaging house's Locked Facts table carries the
  current verified figure. **Never quote the KB's own pricing page** - it is confirmed
  stale (still shows an old Fly $600/Growth $1,500 structure and a stale $0.007 token
  rate; re-checked live 5 Sep 2026, unchanged from the earlier finding) [messaging-house.md
  §6].
- **Free trial:** 14 days, no credit card required [nuclia-mcp KB, `nuclia.com/pricing/`,
  re-queried 5 Sep 2026 - the trial terms are one of the few figures on that page that has
  not gone stale; re-verify live before quoting regardless].
- **Integration effort:** the one-feature pattern is deliberately small in scope - one use
  case, one surface, the standard server-side integration pattern. Scope the actual
  duration inside the POV plan for the specific deal; this document does not know it and
  should never invent a project-plan timeline.

Re-verify every figure live at `progress.com/agentic-rag/pricing` before quoting in any
outbound artifact - this document's figures are a snapshot, not a substitute for that
check.

---

## 4. Measure, don't assume - the POV is the model's real data source

The inputs that matter most in every lever above - minutes saved, deflection rate,
consumption per query, adoption - should never be argued in a meeting. They should be
measured:

1. **Agree the one feature and its metric before the POV starts** (e.g. "time to a
   correct, cited answer on these 20 real questions our own staff ask today").
2. **Run the POV on the buyer's own content** - never sample or seeded data. A measured
   number from someone else's content proves nothing about this buyer's world.
3. **Measure before/after on real queries.** Answer quality is demonstrated live with
   REMi's per-query scoring and real citations - never claimed as a percentage
   [messaging-house.md §2; field rule 5].
4. **Fill this model with the measured numbers and hand the buyer their own business
   case** - a document built from their content, their staff, their numbers, that they can
   defend upward without needing you in the room.

This sequence is also the direct, structural answer to "we don't see a path to
production": the POV's one feature **is** production release one, not a separate pilot
that needs a second approval to go live afterward
[objection-handling-guide.md §3].

---

## 5. One worked illustrative example - not a benchmark

**Scenario (illustrative, not a real account):** a mid-size professional association -
content-heavy, personnel-light, matching the target-profile signal exactly
[operating-inside-progress.md §6] - qualifies a first feature: members can't easily find
answers to CPD (continuing professional development) rules buried across policy PDFs,
meaning the association's own staff field the same questions by phone and email every
week. Two levers apply at once: internal staff time (Lever 1) and member-facing
deflection (Lever 2).

**Lever 1 inputs (illustrative):** 6 staff handle CPD queries; 15 such lookups each per
week; 5 minutes saved per lookup once a cited answer replaces manually searching policy
documents (measure in POV); loaded cost $60/hour.
- 6 × 15 × 5 = 450 minutes = 7.5 hours saved per week
- 7.5 × $60 ≈ **$450 per week, roughly $1,950 per month** in staff time alone.

**Lever 2 inputs (illustrative):** 400 CPD-related member contacts per month; 40%
realistically deflected once members can self-serve the answer directly on the
association's own site (measure in POV - never assume a deflection rate); $12 loaded cost
per contact.
- 400 × 0.40 × $12 = **$1,920 per month** in deflected contact-handling cost.

**Combined illustrative monthly value: roughly $3,870/month**, against a Starter
subscription at $700/month plus measured consumption. Even allowing generously for the
measured numbers to land lower than these illustrative figures once the POV runs, the
value case clears the subscription cost by a wide margin - **which is exactly the
comparison the POV exists to make real, not assumed.**

**Every number above is illustrative and must be replaced with the buyer's own before
this model appears in front of them as a business case.** The arithmetic shape is shown
so a seller can rebuild it live in the room with the buyer's real inputs, not so this
example can be reused as if it were a proof point.

---

## 6. Budget anchoring - no new line item required

The purchase should fit a line the organisation already funds, not a new one requested
from scratch:

- **Service improvement / digital operations** - Levers 1 and 2 deployments.
- **Web and content budget** - a site-search replacement or member/citizen assistant is a
  website feature, not a standalone AI programme.
- **Product roadmap / COGS** - for an ISV, the platform is a component cost of a
  revenue-bearing feature (Lever 5).
- **An existing AI mandate with nowhere to start** - where the board has already
  allocated funds and the blocker is "where to start," the one-feature POV is the
  smallest defensible first step, entry under US$1,000/month.

---

## 7. Where the objections meet this model

- **"There's no budget line for this"** → section 6: it fits a line the organisation
  already funds; entry under US$1,000/month
  [objection-handling-guide.md §2].
- **"We don't see a path to production"** → section 4: the POV's one feature is the
  first production release, and it produces the business case as a by-product
  [objection-handling-guide.md §3].
- **"We can build it ourselves"** → Levers 3 and 4 price the time and engineering-cost
  side of that choice honestly, so the comparison is real rather than argued
  [objection-handling-guide.md §1].
- **"Every vendor claims ROI numbers like this"** → the honesty rule at the top of this
  document is the answer: this model arrives empty and is filled with the buyer's own
  measured numbers, not a vendor projection.

---

## Source map

- **Field record (target-profile signal, three loss reasons, one-feature-first
  doctrine)** - `content/positioning/operating-inside-progress.md` §4b, §6.
- **Positioning, pillars, DIY/hyperscaler displacement argument, no-accuracy-% rule,
  Locked Facts (pricing)** - `content/positioning/messaging-house.md` §1, §2, §3, §5, §6.
- **Pricing re-verification and staleness of the KB pricing page** -
  `content/enablement/battlecards/progress-agentic-rag-home-battlecard.md` §2 (Pillar 3),
  live-verified 6 Aug 2026; re-checked against `nuclia-mcp` 5 September 2026 (KB page
  confirmed still stale, showing Fly $600/Growth $1,500/$0.007-per-token).
- **Ingestion agents (Labeler, Generator, Graph Extraction, Generate Q&A) underlying
  Lever 3's time-to-production claim** - `nuclia-mcp` knowledge box,
  `nuclia.com/ingestion-ai-agents/`, re-queried 5 September 2026.
- **REMi underlying the quality-measurement claim in Lever 4 and section 4** -
  `nuclia-mcp` knowledge box, `nuclia.com/rag-quality/`, re-queried 5 September 2026.
- **Free trial terms** - `nuclia-mcp` knowledge box, `nuclia.com/pricing/`, re-queried
  5 September 2026.
- **Discovery hand-off (where these inputs get asked)** -
  `content/enablement/discovery-qualification-framework.md` §3, §4 (this rebuild).
- **Objection hand-off** - `content/enablement/objection-handling-guide.md` §1-3 (this
  rebuild).

**Flagged gap:** the KB's own pricing page remains stale as of this rebuild (still
showing Fly $600/Growth $1,500/$0.007-per-token) - every figure in section 3 should be
re-verified against the live `progress.com/agentic-rag/pricing` page before any outbound
use, exactly as the prior version of this document already required; this rebuild does
not resolve the staleness, only carries the warning forward accurately.

---

## Change log

- **2026-09-05** - v2.0. Full rebuild per GM directive (5 Sep 2026): v1.0 was too thin (3
  levers, no engineering-cost lever, a single worked example with no persona grounding) to
  serve as the field's actual ROI tool. New five-lever structure (time-to-answer,
  deflected effort, faster path to production, avoided DIY-build cost, product economics),
  each with an explicit formula; pricing figures and every underlying capability claim
  re-verified against `nuclia-mcp` and the home battlecard rather than carried over
  untouched; one new worked example combining two levers on a professional-association
  scenario, matching the field record's actual target-profile signal.
- **2026-08-10** - v1.0 (superseded). First draft, three levers, built from the GM field
  interview.
