# ARAG Proof-of-Value Playbook

**For:** the ARAG overlay sellers and solutions engineers, run live from qualification
through to a commercial proposal. **Owner:** sales-enablement. **Version:** 1.0. **Date:**
5 September 2026.

**Grounding:** `content/positioning/messaging-house.md` (positioning, pillars, Locked
Facts), `content/positioning/operating-inside-progress.md` §6 (the field record this
playbook is built to close), `content/enablement/discovery-qualification-framework.md`
(the qualification this playbook picks up from), `content/enablement/roi-value-model.md`
(the business-case model this playbook's measured POV numbers feed), and
`content/enablement/objection-handling-guide.md` §1-3 (the three deal-killers this
playbook is structurally designed to defuse). Every ARAG capability claim below is
verified against `nuclia-mcp`.

**The honesty rule, read before anything else:** a POV proves what actually happened on
the buyer's own content, not a promise about what will happen. Never quote an accuracy
percentage or a target REMi score - none is published, and none should ever be promised as
a pass mark [field rule 5; messaging-house.md §6]. Never claim a capability beyond what the
messaging house documents. Where a POV finds a genuine gap or limit, say so in the exit
review - a POV that only ever reports success is not credible and will not survive a
technical buyer's scrutiny.

---

## 1. What a POV is (and is not)

A Proof-of-Value is a scoped, time-boxed, measured run of **one feature**, on the buyer's
own content, that produces two things: a working answer surface the buyer's own people can
react to, and a set of real numbers - REMi trend, cited-answer quality, measured
consumption - that become the buyer's own business case
[roi-value-model.md §1, §4]. It is not a generic platform demo, not a free trial left to
run unattended, and not a pilot that needs a second approval to go live once it succeeds.

**The structural design choice that answers the field's own named deal-killer** ("we don't
see a path to production" [operating-inside-progress.md §6; objection-handling-guide.md
§3]): the POV's one feature **is** production release one. Scope it, from day one, as the
thing that goes live if it succeeds - not a sandbox exercise that gets rebuilt later.

---

## 2. Qualification handoff - what must already be true before a POV starts

A POV is expensive in SE time and buyer attention. Do not open one on hope. Confirm every
line below is already true, using `discovery-qualification-framework.md` §2 and §6:

| Must already be confirmed | Source |
|---|---|
| A nameable first feature, in the buyer's own words | discovery-qualification-framework.md §4 |
| Real content exists today that the POV can point ARAG at | discovery-qualification-framework.md §6 (disqualifier: no real content estate) |
| A named owner who can plausibly take the feature live | discovery-qualification-framework.md §2 category 5 |
| An identified existing budget line the spend would sit inside | discovery-qualification-framework.md §5, §6 |
| The decision process and any competitive evaluation already visible | discovery-qualification-framework.md §2 category 4 |

**If any of these is still unconfirmed, that is the next discovery call, not a reason to
open the POV anyway.** A POV run against an unqualified deal produces a technically
successful demo with nowhere to land - exactly the pattern the field record already names
as a loss reason.

---

## 3. The one-feature-first scoping template

Fill this out live with the buyer before the POV starts. Use their own words for the
feature, not a category:

| Field | What goes here | Example (illustrative only) |
|---|---|---|
| **Feature** | The one thing being proved, in the buyer's own words | "Members can get a direct, cited answer to a CPD rules question instead of searching policy PDFs" |
| **Corpus slice** | The specific, real content the POV ingests - never sample or seeded data | The association's published CPD policy documents, current version only |
| **Users** | Who interacts with the POV during the run, and how many | 3-5 association staff who currently field these questions by phone/email |
| **Success metric, agreed before day one** | The one thing being measured, stated as a question, not a target number | "Can a cited, correct answer to these 20 real questions our own staff are asked weekly be returned directly, versus today's manual search?" |

**Three qualification tests before this scope is locked** (mirrors
`discovery-qualification-framework.md` §4):
- **Nameable** - a specific pain in specific words, not a category.
- **Provable** - real content exists today that the POV can point ARAG at.
- **Ownable** - the named owner from section 2 is genuinely in or reachable from the room.

---

## 4. Success criteria - measured, never assumed

**Never an accuracy percentage. Never a target REMi score.** Both are explicitly ruled out
[field rule 5; messaging-house.md §6] - a POV that promised either would be promising a
number that does not exist. Success is demonstrated two ways, together:

1. **REMi as a trend, not a threshold.** REMi scores every answer in real time on Answer
   Relevance, Context Relevance and Groundedness [nuclia-mcp KB, `rag-quality` page,
   re-queried 5 Sep 2026]. Show REMi scoring across the POV's real question set as a
   running measure the buyer can watch improve as ingestion and configuration are tuned -
   never as a single pass/fail number on day one. **REMi is sensitive to outright
   fabrication but measures groundedness holistically, not clause-by-clause, and it can
   under-score a genuinely well-synthesised answer that correctly draws on more than one
   source** - treat a lower score on a synthesised answer as a prompt to inspect the
   answer, not proof it is wrong. Where the feature involves an agentic (RAO/MCP)
   surface, score REMi against the full retrieval context the agent actually grounded on,
   not a single excerpt, or the score will read unstable for reasons that have nothing to
   do with answer quality.
2. **Cited-answer spot checks with the buyer's own people.** Run the POV's real question
   set with the users named in section 3, live, and have them judge each answer against
   two things they can see for themselves: does the citation actually support the claim
   (click through to the source), and would this have answered their real question faster
   than today's method. This is a human judgement panel, not a scored benchmark - it is
   what makes the exit review defensible without a number to hide behind.

Both together - a REMi trend moving in the right direction, and a panel of the buyer's own
people confirming citations hold up - is the evidence base for the exit review in section
7. Neither alone is sufficient.

---

## 5. The 30-day POV timeline, with owners on both sides

A POV that drifts past 30 days without a clear reason loses momentum and the sense of
urgency that got it approved. Scope every week with an owner on each side named at kickoff:

| Week | ARAG-side owner (SE) | Buyer-side owner (named champion) | What happens |
|---|---|---|---|
| **1 - Scope and stand up** | Confirms the scoping template (section 3), provisions the Knowledge Box, agrees the success metric in writing | Provides real content access, confirms the 20-or-so real questions to test, confirms which residency/deployment constraints apply | Feature scope locked; KB provisioned; ingestion begins |
| **2 - Configure and answer** | Configures ingestion (the DA agents the feature actually needs - see the Solutions Architect discovery question on this [discovery-qualification-framework.md §3]), tunes retrieval, runs the first pass of the real question set | Reviews first-pass answers, flags anything that reads wrong or incomplete | A working, cited answer surface exists on the buyer's real content |
| **3 - Measure** | Runs the REMi trend and the cited-answer panel (section 4) with the named users | Sits the panel, gives honest feedback, surfaces any question the POV should have covered but didn't | The evidence base for the exit review is captured |
| **4 - Exit and propose** | Completes the path-to-production checklist (section 6), drafts the commercial proposal (section 7) | Confirms the production owner and the target go-live surface | Exit review held; proposal handed over as the buyer's next decision, not another meeting to schedule |

**If a genuine competitive evaluation is in play, section 8's bake-off module runs inside
this same 30 days**, not as a separate cycle - schedule it in week 2 or 3 once the POV's
own answers are stable enough to compare fairly.

---

## 6. Path-to-production checklist

Complete every line below before the exit review - an unanswered line here is exactly what
turns a successful POV into a stalled pilot [objection-handling-guide.md §3]:

- **Deployment mode confirmed.** Cloud (EU or US), hybrid (Nuclia's cloud handles
  processing, the customer's own NucliaDB instance handles storage), or full on-premises
  including the generative model itself, for offline/air-gapped operation [nuclia-mcp KB,
  `nuclia-deployment-options` page, re-queried 5 Sep 2026]. Confirm which one the buyer
  actually needs in production - it is sometimes different from what was convenient for
  the POV itself.
- **Data residency confirmed, specifically.** Which country, which data class, and whether
  the constraint is storage location or that the model itself must never process the data
  outside the buyer's environment - these call for different deployment shapes (hybrid
  versus full on-prem) [objection-handling-guide.md §6]. Do not carry an assumption from
  the POV's own hosting into the production plan without asking.
- **Integration pattern confirmed.** The standard server-side proxy pattern for a
  browser-facing answer surface, or - where the feature calls the buyer's own systems -
  an ARAG Retrieval Agent driving the buyer's own MCP tools under the caller's RBAC, never
  a homegrown planner in front of it [messaging-house.md pillar 1]. Confirm which shape
  the production surface actually needs; it is not always the shape the POV used for
  speed.
- **Knowledge Box ownership confirmed.** A Knowledge Box's user roles (SOWNER, SMEMBER,
  SCONTRIBUTOR) are managed per-KB [nuclia-mcp KB, Knowledge Box & Zone REST API,
  re-queried 5 Sep 2026] - confirm before go-live that the KB used in the POV is owned
  (SOWNER) by an account the buyer's own production team controls, not left owned by the
  account that stood the POV up. A production system owned by someone outside the buyer's
  organisation is not a production system.
- **Tier confirmed against measured consumption.** Use the POV's own measured token
  consumption (visible in Nuclia's usage dashboard and analytics [nuclia-mcp KB, RAG
  quality/analytics pages, re-queried 5 Sep 2026]) to estimate the production tier, rather
  than guessing from the POV's small scope. See section 7.

---

## 7. Exit criteria that convert into the commercial proposal

The exit review is not a "did it work" conversation alone - it is where the measured POV
becomes a proposal the buyer can act on immediately:

1. **Present the evidence from section 4** - the REMi trend and the cited-answer panel
   results - honestly, including anything that did not fully land, with what would fix it
   at production scale.
2. **Confirm the path-to-production checklist (section 6) is complete.** An exit review
   held with an open checklist line is not yet an exit review - go back to whichever owner
   holds that line first.
3. **Size the commercial proposal from measured consumption, not a guess.** Starter
   (US$700/month) is the default entry tier for a single-feature production release; Pro
   (US$1,925/month) applies for a larger indexed estate or the fuller AI-task set; Enterprise
   (custom) applies once deployment mode, scale, or a genuine on-premises requirement is in
   play [messaging-house.md §6 Locked Facts - re-verify these figures live at
   `progress.com/agentic-rag/pricing` before quoting; they carry their own provenance
   because the KB's own pricing page is confirmed stale]. Where the Pro QuickStart offer
   (100,000 complimentary tokens/month for the first three months on Pro) is still live,
   it is a genuine incentive to move the proposal now rather than defer - but it is
   time-boxed to 30 September 2026 and must be re-verified live and dropped from any
   proposal after that date.
4. **Anchor the proposal to the existing budget line named in discovery**
   [roi-value-model.md §6] - the proposal is a reallocation inside a line the buyer
   already funds, never a request for a new one.
5. **Hand over the filled ROI model as the buyer's own document**
   [roi-value-model.md §1] alongside the proposal, built from the POV's own measured
   numbers - a business case the buyer can defend upward without the seller in the room.
6. **Name the production go-live date and owner explicitly** - the POV's feature becomes
   the production release, not a separate project waiting on a second approval
   [objection-handling-guide.md §3].

---

## 8. Competitive bake-off module

Where a named competitor is genuinely in the evaluation, invite the comparison rather than
avoid it [discovery-qualification-framework.md §7] - this is the same motion that has
already decided at least one real enterprise deal on measured quality rather than a claim
[operating-inside-progress.md §6].

**How to run it, inside the same 30-day POV:**

1. **Identical inputs, both platforms.** The same real content set from section 3, the
   same question set, ingested into both ARAG and the named competitor's platform under
   comparable configuration. An uneven comparison (richer content on one side, a smaller
   question set on the other) is not a fair bake-off and will not survive scrutiny.
2. **Pull the named competitor's battlecard first** - `content/enablement/battlecards/` -
   for the specific claims, trap questions and honest concessions that apply to that
   vendor, before the bake-off session. Never improvise a competitive claim live; if the
   battlecard does not cover it, say so and follow up rather than guess.
3. **Measured quality decides, not a marketing claim.** Run the same cited-answer panel
   from section 4 blind where practical - the buyer's own people judging both platforms'
   answers to the same questions against citation accuracy and whether the answer actually
   helps, without being told which platform produced which answer until after judging.
4. **Where ARAG's own architecture no longer differentiates on paper** (for example,
   MCP-based tool-calling is now shipping across several rivals
   [objection-handling-guide.md §8]), do not lead the bake-off with that claim - lead with
   REMi (no confirmed equivalent in the current competitive set) and deployment breadth
   (on-premises including the generative model, which no hyperscaler Copilot/Foundry
   offering matches) [progress-agentic-rag-home-battlecard.md §2].
5. **Concede honestly where the honest answer favours the competitor** - connector breadth
   against Glean, named regulated-industry certifications against Sinequa, compliance-list
   breadth against a hyperscaler [messaging-house.md §5]. A bake-off won by
   over-claiming does not survive the production phase that follows it.

---

## Source map

- **Field record (three deal-killers, one-feature-first doctrine, the enterprise deal
  decided by measured quality)** - `content/positioning/operating-inside-progress.md` §6.
- **Positioning, pillars, DIY/hyperscaler displacement, Locked Facts (pricing,
  certifications)** - `content/positioning/messaging-house.md` §1, §2, §3, §5, §6.
- **Qualification categories and disqualifiers** -
  `content/enablement/discovery-qualification-framework.md` §2, §4, §6, §7.
- **Value levers, budget anchoring, POV-as-production-release-one** -
  `content/enablement/roi-value-model.md` §1, §4, §6.
- **The three deal-killer objections, MCP-parity concession, connector-breadth
  concession** - `content/enablement/objection-handling-guide.md` §1, §3, §8, §9.
- **REMi metrics and diagnostic behaviour** - `nuclia-mcp` knowledge box, `rag-quality`
  page, re-queried 5 September 2026.
- **Deployment modes (cloud/hybrid/on-prem including the generative model)** -
  `nuclia-mcp` knowledge box, `nuclia-deployment-options` page, re-queried 5 September
  2026.
- **Knowledge Box user roles (SOWNER/SMEMBER/SCONTRIBUTOR) and per-KB ownership
  management** - `nuclia-mcp` knowledge box, Knowledge Box & Zone REST API documentation,
  re-queried 5 September 2026.
- **Usage dashboard and token-consumption analytics underlying tier-sizing at exit** -
  `nuclia-mcp` knowledge box, RAG quality/analytics documentation, re-queried
  5 September 2026.

**Could not ground / flagged gaps:**
- No accuracy percentage or target REMi score appears anywhere in this playbook - a
  deliberate omission per field rule 5, not an oversight.
- Specific Knowledge Box capacity ceilings (indexed GB, resource counts) are not carried
  here - the only source found for them is the KB's own pricing page, already confirmed
  stale elsewhere in this factory's canon [roi-value-model.md §3]. Re-verify current tier
  capacity live at `progress.com/agentic-rag/pricing` if a specific ceiling number is
  needed in a real deal; do not infer one from this document.

---

## Change log

- **2026-09-05** - v1.0. Built fresh per the lead's brief, cross-referencing the same-day
  v2.0 rebuilds of the discovery framework, ROI model and objection guide. New content:
  the qualification handoff gate, the one-feature-first scoping template, REMi-as-trend
  success criteria (with the synthesis-under-scoring caution folded in from field
  experience), the 30-day timeline with named owners both sides, the path-to-production
  checklist (including Knowledge Box ownership, verified against the Nuclia API
  documentation), exit criteria into the commercial proposal, and the competitive bake-off
  module.
