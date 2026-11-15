# ARAG Objection-Handling Guide

**For:** the ARAG overlay sellers and solutions engineers, live in deals. **Owner:**
sales-enablement. **Version:** 2.0 (full rebuild). **Date:** 5 September 2026.
**Supersedes:** v1.0, 12 August 2026 (retired per GM directive - rebuilt from the ground
up, not patched, to close gaps found on review and bring it current against the
3 September 2026 battlecard refresh).

**Grounding:** `content/positioning/operating-inside-progress.md` §4b, §6 (the field
record every deal-killer objection traces to), `content/positioning/messaging-house.md`
(positioning, pillars, Locked Facts), the battlecards under
`content/enablement/battlecards/` (re-verified 3 Sep 2026, including the home card's MCP
re-sequencing correction), and `nuclia-mcp` for every ARAG capability claim used below.
Cross-referenced with `discovery-qualification-framework.md` (where these objections
should be surfaced early, not waited for) and `roi-value-model.md` (the numbers behind
the commercial answers).

---

## How to use this guide

**Read this section before the objections, not after** - it is the one move that makes
every entry below actually work in a room.

**The single biggest fact in the field record: capability wins the room almost every
time. Deals die on the commercial path** - no clear path to production, no budget line for
"RAG anything," and "we can build it ourselves" - almost never on whether ARAG can do the
job [operating-inside-progress.md §6]. That reframes what most objections actually are.
Something that sounds like a capability objection ("is it accurate," "will it
hallucinate," "what about our cloud") is very often a risk or commercial objection wearing
a technical costume. Answer the technical question honestly and briefly - then find the
commercial question underneath it.

**The meta-move is the one-feature-first doctrine.** Most buyers meeting us want to
implement AI and are not sure where to start [operating-inside-progress.md §6]. Arguing
capability in the abstract does not help them start; naming one feature does. Every
objection response below should end pointed at a single, named, small next step - never
at "let me prove the platform can do everything"
[discovery-qualification-framework.md §4].

**Never argue capability at length - sell the path.** The move, every time: (1) answer the
honest version of the technical question in one or two sentences, with real proof, (2)
pivot to the commercial or path question underneath it, (3) land on a specific next
step - almost always the one-feature POV that produces its own business case
[roi-value-model.md §1, §4]. The POV's one feature becomes production release one, which
is also the direct answer to "no path to production" (objection 1 below).

**Never fabricate to win a moment.** No accuracy percentage exists to quote - none is
published, and quality is proven live with REMi and a cited answer, never asserted as a
number [messaging-house.md §2; field rule 5]. Progress/Nuclia states on
`nuclia.com/security/` that it holds ISO 27001 and SOC 2 Type 2 - this is vendor-stated,
not independently verified by us, and no certification claim beyond this vendor statement
may appear in any material or any conversation without confirming current status first
[messaging-house.md Locked Facts - Certifications; field rule 5]. Where this guide cannot
ground an answer, it says so plainly rather than inventing one - a seller caught
improvising a fact loses
more credibility in the room than one who says "let me confirm that and come back to
you."

**Order matters.** The first three objections below are the field's own named deal-killers
[operating-inside-progress.md §6] - work these before any competitor-specific objection,
because a technically flawless competitive win still stalls if these three are unresolved
underneath it.

---

## 1. "We can build it ourselves."

**What it sounds like:** "We've got engineers, we've already got a vector database
running - why would we pay for this?"

**What it usually means:** confidence that a framework plus a vector database gets a team
most of the way there - usually from a team that has not yet built the parts that stay
invisible until production: quality measurement, citation, multi-format ingestion, access
control, and an eval harness nobody plans for until an answer is wrong in front of a real
user.

**The honest answer:** don't argue DIY can't work - it can, slowly, and often does get
most of the way there. The honest counter is time and instrumentation. DIY retrieval
stacks assembled from frameworks and vector databases cost real engineering months, with
no quality instrumentation built in unless the team builds one too
[messaging-house.md §5]. ARAG's ingestion agents (Labeler, Generator, Graph Extraction,
Generate Q&A) and REMi ship out of the box [nuclia-mcp KB, `ingestion-ai-agents` and
`rag-quality` pages, re-queried 5 Sep 2026] - a one-feature POV produces a working, cited,
quality-scored answer inside the scope of a proof-of-value, priced from US$700/month
[roi-value-model.md §2 (Lever 3), §3], against an internal build with no comparable
time-to-first-answer and no native way to measure whether an answer is grounded once it
ships [roi-value-model.md §7].

**The trap to avoid:** do not contest whether their engineers *could* build it - they
probably could. Contesting the wrong claim (capability) instead of the real one (the time
and opportunity cost of engineering hours, priced honestly in Levers 3 and 4 of the ROI
model) loses credibility with a technical buyer and skips past the argument that would
actually move the deal.

**When to concede:** if the team has dedicated retrieval engineers already staffed with
real runway and no urgency, concede the build is genuinely achievable and reposition ARAG
as the fast benchmark to build against - run the one-feature POV in parallel with their
build and let it set the bar for time-to-first-cited-answer and measured quality
[roi-value-model.md §4], rather than arguing they should not build at all.

---

## 2. "There's no budget line for this."

**What it sounds like:** "I like it, but where does this even get paid for? We don't have
an 'AI' budget."

**What it usually means:** not a competing purchase decision - usually no purchase
decision has been framed at all, because "RAG" does not map to a line item anyone owns
[operating-inside-progress.md §6]. This is the second-most common deal-killer in the field
record.

**The honest answer:** the purchase fits a line the organisation already funds. Starter is
self-serve at US$700/month, and the one-feature pattern maps onto service improvement/
digital operations budget, web and content budget, product roadmap/COGS for an ISV, or an
existing AI mandate looking for its first defensible step - entry under US$1,000/month in
every case [roi-value-model.md §6]. The ask is never "approve a new AI programme," it is
"reallocate inside a line you already have."

**The trap to avoid:** do not propose a "pilot budget" as a new, separate ask - that
recreates the exact problem (a novel line item with no owner). Always anchor to an
existing, named budget line before proposing next steps
[discovery-qualification-framework.md §5].

**When to concede:** if genuinely no budget line exists anywhere in the organisation that
the one-feature cost could sit inside, that is a real disqualifier, not a framing problem
to argue past [discovery-qualification-framework.md §6].

---

## 3. "We don't see a path to production."

**What it sounds like:** "Even if the demo's great, how does this actually become
something our users touch?"

**What it usually means:** past AI pilots that impressed in a demo and then stalled with
no owner, no route to a live surface, or sample data that never became a real
deployment - the third named deal-killer in the field record [operating-inside-progress.md
§6].

**The honest answer:** the POV is not a throwaway pilot - it is designed so its one
feature **is** production's first release, run on the buyer's own content with the metric
agreed before it starts [roi-value-model.md §4]. This answers the objection structurally,
not rhetorically: there is no separate "now build it for real" step after the POV
succeeds.

**The trap to avoid:** do not promise a project-plan duration this guide, or any
enablement asset, cannot know - scope the POV in the specific deal's own plan, not with an
invented timeline [roi-value-model.md §3].

**When to concede:** if no one in the room can name who would own the feature in
production, the deal genuinely is not ready - a pilot with no owner is an explicit
discovery-framework disqualifier [discovery-qualification-framework.md §6]. Name the gap
directly and ask who the production owner would be, rather than proceeding as if a good
demo alone resolves it.

---

## 4. "We'll just use what's already in our cloud" (AWS / Azure / Google)

**What it sounds like:** "We're already an AWS/Azure/Google shop - why buy something new
when it's already in our cloud bill?"

**What it usually means:** inertia, not a considered build-vs-buy evaluation - this is our
own positioning's other named displacement target, alongside DIY: hyperscaler AI bundles
bring cloud lock-in, stacked metering, and retrieval treated as a side feature rather than
the product itself [messaging-house.md §5].

**The honest answer, general shape:** do not argue the hyperscaler option is broken -
argue the total cost is not one number. Offer to build the account's actual stacked cost
live in the call using the vendor's own published rates, side by side with ARAG's single
subscription, rather than asserting a percentage.

**Per-cloud notes:**
- **AWS (Bedrock Knowledge Bases + Amazon Q Business):** a working deployment spans index
  storage, retrieval calls, a separate Bedrock model-inference charge, Q Business per-seat
  fees, index-capacity units and connector-hours - at least seven independently-scaling
  meters versus ARAG's single subscription plus one consumption meter. A 100-seat Q
  Business Pro deployment floors above US$2,200/month before a document syncs
  [aws-bedrock-q-battlecard.md §2, §7]. Trap question: "has anyone actually added that up
  into one number, or is 'it's already in our AWS bill' untested?"
- **Azure (Microsoft Foundry / Copilot):** Copilot only reaches what is already inside
  Microsoft 365; Foundry gives building blocks (Azure AI Search, enrichment skills,
  orchestration) but the managed-pipeline experience is assembled, not bought
  [azure-ai-foundry-copilot-battlecard.md §7]. Trap question: for knowledge outside
  M365 - PDFs, wikis, recorded calls, third-party systems - what is the actual
  engineering plan and timeline to index it in Foundry?
- **Google (Gemini Enterprise):** bought as a per-seat suite (four editions, US$21-US$60+/
  seat/month) plus separately metered Agent Compute and Agent Storage once agents run at
  scale - no equivalent to a single flat monthly line item
  [google-gemini-enterprise-battlecard.md §6]. Trap question: what is the fully loaded
  monthly cost once seat count, Agent Compute and Agent Storage are added for the
  equivalent workload, not just the headline per-seat number?

**The trap to avoid:** do not claim any hyperscaler lacks model choice, on-prem options,
or citations - each battlecard confirms these are real for at least one hyperscaler
(Bedrock's multi-model catalogue, Google's Distributed Cloud air-gapped path, Q Business's
cited responses). Overclaiming here is the fastest way to lose a technical buyer's trust.

**When to concede:** if the account's data and auth already live entirely inside one
cloud with no material knowledge outside it, the integration lift genuinely is lower with
the hyperscaler's native option - concede it and reposition ARAG as the layer for what the
hyperscaler stack does not reach, not a rip-and-replace.

---

## 5. "How accurate is it? Prove it."

**What it sounds like:** "Give me a number - what's your accuracy rate?"

**What it usually means:** a reasonable ask for proof before trusting AI answers in front
of real users, sometimes shaped by a competitor or analyst report that quoted a
percentage.

**The honest answer:** no accuracy percentage exists to quote - none is published.
Quality is proven live: REMi scores every answer in real time on Answer Relevance,
Context Relevance and Groundedness - a specialised evaluation model (a fine-tuned adapter
on Mistral 7B v0.3 Instruct), not a generic LLM eval, open-sourced on Hugging Face and via
the `nuclia-eval` Python library so a technical buyer can inspect it directly rather than
take a marketing claim on faith [nuclia-mcp KB, `nuclia.com/developers/
remi-open-source-rag-evaluation-model/`, re-queried 5 Sep 2026]. REMi diagnoses *why* an
answer is wrong - a retrieval miss versus a generation error - not just whether it is
[messaging-house.md §2]. The honest move is to run the demonstration on the buyer's own
content in the room or in a POV, never to hand over a slide with a number on it.

**The trap to avoid:** never fabricate or estimate a percentage to satisfy the question in
the moment - this is a hard rule, not a style preference [field rule 5;
messaging-house.md §6]. Do not let "we don't have a number" sound like evasion - reframe it
as the stronger position: a live, per-query, diagnosable score beats a static benchmark
number that tells the buyer nothing about their own content.

**When to concede:** if the buyer's procurement process genuinely requires a published
benchmark percentage before any vendor can be shortlisted, say so plainly - that is a real
qualification gate ARAG's current answer does not clear, not one to argue around in the
room [discovery-qualification-framework.md §6]. Escalate rather than improvise a figure.

---

## 6. "Our data can't leave [country / premises]."

**What it sounds like:** "Everything has to stay on our own infrastructure / in our
region - is that even possible with an AI platform?"

**What it usually means:** a genuine governance or regulatory constraint, often the actual
blocker behind a vaguer "AI mandate" the organisation has not yet acted on.

**The honest answer:** ARAG deploys three real ways today - cloud (Europe or US
infrastructure), hybrid (Nuclia's cloud handles processing, the customer's own NucliaDB
instance handles storage, so nothing persistent is stored in Nuclia's cloud), or fully
on-premises - **including the generative model itself** - for offline and air-gapped
operation [nuclia-mcp KB, `nuclia.com/nuclia-deployment-options/`, re-queried 5 Sep 2026].
This is one of ARAG's structural counters to both hyperscaler lock-in (no hyperscaler
Copilot/Foundry offering has an on-premises edition at all) and enterprise-search vendors
with no self-serve, low-commitment entry [messaging-house.md pillar 3]. Nuclia is also
independently a European business offering EU and US data centres, GDPR-aligned, and
sitting in the EU AI Act's low/minimal-risk category [nuclia-mcp KB,
`nuclia.com/security/`, re-queried 5 Sep 2026] - a useful data point for a residency
conversation that has not yet reached the on-prem question.

**The trap to avoid:** do not claim a specific regional certification (FedRAMP, PIPEDA,
HIPAA, or any tier beyond what is verified) - a named certification never appears on a
card or in a conversation without independent verification outside the KB
[hard rule 3; messaging-house.md Locked Facts - Certifications]. Confirm the specific
residency requirement (which country, which data class) before promising a deployment
shape - "everything has to stay here" sometimes means storage location, sometimes means
the model itself must never leave the building, and those call for different answers
(hybrid versus full on-prem).

**When to concede:** if the requirement is specifically a named federal or defence
compliance tier such as FedRAMP High or DoD IL4/IL5, concede directly - the only
certifications Progress/Nuclia states it holds are ISO 27001 and SOC 2 Type 2
(vendor-stated, not independently verified by us; confirm current status before quoting
it to a customer), not that tier [messaging-house.md Locked Facts - Certifications;
aws-bedrock-q-battlecard.md §6; azure-ai-foundry-copilot-battlecard.md §6]. Flag it as a
real gap to close, not one to talk around.

---

## 7. "Nuclia's a small company - what happens if it disappears?"

**What it sounds like:** "Who even is Nuclia? What if you're gone in two years?"

**What it usually means:** vendor-viability risk, common with any specialist platform a
buyer has not heard of before this conversation.

**The honest answer:** Nuclia has been acquired by Progress Software, integrating its
agentic RAG capability into Progress's existing product portfolio [nuclia-mcp KB,
`nuclia.com` homepage and the Certainly case study, re-queried 5 Sep 2026]. The buyer is
not betting on an unproven standalone startup - they are buying a specialist RAG platform
now backed by an established enterprise software company with an existing customer base
and support infrastructure. Progress/Nuclia also states, on its own security page, that it
holds ISO 27001 and SOC 2 Type 2 - vendor-stated, not independently verified by us, so
confirm current certification status before quoting it to a customer
[messaging-house.md Locked Facts - Certifications] - but it is the kind of operational
posture a genuinely fragile vendor rarely bothers to claim.

**The trap to avoid:** do not overstate integration depth that has not shipped - the
honest claim is ownership and backing, not a specific roadmap promise about how deeply
ARAG is being woven into other Progress products (see the standing Sitefinity caution
[operating-inside-progress.md §3] for why roadmap promises beyond what has shipped are
risky).

**When to concede:** nothing to concede here - this is a straightforwardly strong answer.
The only discipline required is not embellishing it.

---

## 8. "Competitor X now supports MCP tool-calling too - doesn't that erase ARAG's agentic differentiation?"

**What it sounds like:** "I read that [Cohere / another vendor] can already call custom
tools over MCP - isn't that the same thing you're pitching?"

**What it usually means:** a genuinely informed buyer who has done real competitive
homework, most likely on Cohere North Automations, which has shipped comparable MCP-based
tool integration since July 2026.

**The honest answer:** say so plainly rather than pretend it isn't true - MCP-based tool
access is becoming table stakes across this category, not an ARAG-only architecture
[cohere-north-battlecard.md, re-confirmed in the home battlecard's 3 Sep 2026 refresh].
ARAG's agentic story is still real and shipping - the Retrieval Agent plans multi-step
retrieval, navigates knowledge graphs, and calls external tools over MCP with the caller's
RBAC enforced [messaging-house.md pillar 1] - but it should no longer be the opening line
of the pitch. Pivot immediately to REMi (objection 5) and deploy-anywhere (objection 6) -
neither has a confirmed equivalent anywhere in the current competitive set
[progress-agentic-rag-home-battlecard.md §2].

**The trap to avoid:** do not keep leading a pitch with "ARAG's agents call your own tools
over MCP" as the headline differentiator once this objection has actually surfaced in a
deal - continuing to lead with an eroding wedge after a buyer has already named the
counter-example reads as either uninformed or evasive.

**When to concede:** nothing to concede on the underlying architecture - concede only that
it is no longer uniquely ARAG's, and redirect the conversation to where the market has not
caught up.

---

## 9. "Your connector list is shorter than [competitor]'s - doesn't that mean more integration work?"

**What it sounds like:** "Onyx lists 40-50 connectors, Glean lists over 100 - you're
nowhere near that."

**What it usually means:** a genuine, fair comparison point for a buyer evaluating
workplace-search-style breadth, where ARAG is not the strongest fit to begin with
[messaging-house.md §5].

**The honest answer:** true, and don't contest it. Any API-reachable source can be
ingested via ARAG's API/SDK/CLI - a build step, not a click, the same limitation
acknowledged consistently across this battlecard library. Ask which specific sources this
deal actually needs on day one - the raw connector-count comparison matters far less than
whether the one or two sources this buyer actually cares about are reachable.

**The trap to avoid:** do not claim parity on out-of-the-box connector breadth - it isn't
there, and claiming otherwise is checkable and will be checked.

**When to concede:** for a genuine company-wide-search deal where dozens of named SaaS
connectors are the actual requirement (not a handful of specific systems), concede this is
not ARAG's strongest ground and say so - `glean-battlecard.md` names this gap directly.

---

## 10. "[Competitor]'s cheaper per seat."

**What it sounds like:** "[Vendor]'s only $20-30 a seat - isn't your pricing more
complicated?"

**What it usually means:** a headline per-seat number looks simple next to a
consumption-based model, and the buyer has not yet seen the comparison broken into every
meter.

**The honest answer:** never answer with a single "X% cheaper" claim - the pricing
structures usually are not directly comparable (a per-seat suite versus a
subscription-plus-token model). What is genuinely true and evidenced: ARAG is one
subscription (Starter US$700/month, Pro US$1,925/month) plus one consumption meter
[roi-value-model.md §3], while a per-seat competitor's real total usually stacks per-seat
fees with separate index-capacity, connector-hour, storage or compute meters - Amazon Q
Business Pro floors above US$2,200/month across four separately-scaling meters before a
document syncs at 100 seats [aws-bedrock-q-battlecard.md §2]. Ask to see the full quote
broken into every line item before accepting a headline per-seat number as "simple."

**The trap to avoid:** never quote a fabricated ratio ("we're 40% cheaper") - use the trap
question, not an invented number.

**When to concede:** for a very small, fixed named-user count with light usage, a genuine
per-seat model can legitimately be simpler and cheaper in total than a consumption
model - do not force the comparison where it does not favour ARAG. Reframe to
predictability and scope (one meter to forecast against) rather than disputing the raw
number.

---

## 11. "We already invested in A rival search product / our search platform."

**What it sounds like:** "We've already got Elastic running for search - why not just
build RAG on that?"

**What it usually means:** sunk-cost and incumbency - the platform is already paid for and
staffed, usually landed via a security or observability use case before any RAG
conversation started.

**The honest answer:** Elastic's own usage-based pricing is documented by independent
third-party TCO analysis (not by us) to run 1.3-1.5x standard rates for ML/vector
workloads specifically, with reported 300-400% month-over-month cost swings during
ingestion spikes - "already have it" does not mean "already budgeted for it at RAG scale"
[elastic-battlecard.md §2, §4]. ARAG's flat, published Starter/Pro tiers are the
structural counter to that unpredictability. Reframe as buy-vs-build at the RAG layer
specifically, not a wholesale replacement of the existing Elastic investment - ARAG can
sit alongside Elastic for logs/observability while owning the RAG-specific workload
[elastic-battlecard.md §7].

**The trap to avoid:** do not claim Elastic has no agent or MCP story - Agent Builder is
real and live in A rival search product 9.2+, running as both an MCP server and client
[elastic-battlecard.md §8]. Do not claim Elastic lacks meaningful compliance
certifications - its direct list (FedRAMP High/Moderate, HIPAA, PCI DSS, TISAX, IRAP
Protected B) is broader than ARAG's own.

**When to concede:** in a regulated-industry or public-sector deal where FedRAMP or HIPAA
is a hard requirement, concede Elastic's certification breadth directly rather than
contesting it. Ask which specific certification is the actual blocker, not the full list.

---

## 12. "AI answers hallucinate - we can't risk it."

**What it sounds like:** "How do we know it won't just make something up in front of a
customer or a board member?"

**What it usually means:** a real, well-founded risk concern about generative AI in
general, not necessarily informed by how grounded RAG differs from an ungrounded chatbot.

**The honest answer:** every ARAG answer is grounded and cited back to source, and REMi
scores groundedness on every query in real time, diagnosing whether a low score is a
retrieval problem (the right content was not found) or a generation problem (the model
answered without using what it found) [messaging-house.md §2; nuclia-mcp KB, REMi
documentation, re-queried 5 Sep 2026]. Grounding requires the model to be instructed to
use only retrieved context, not general knowledge - which is exactly what citation and
per-query groundedness scoring are built to verify, not merely promise.

**The trap to avoid:** do not claim hallucination is impossible - no RAG system can
promise zero, and overclaiming here is the fastest way to lose a risk-aware buyer's trust
the first time an edge case appears. The honest claim is detectable and diagnosable, not
eliminated.

**When to concede:** for a genuinely high-stakes use case with zero tolerance for any
ungrounded answer ever reaching an end user (an unreviewed customer-facing legal or
medical determination, for instance), say plainly that a human-in-the-loop review step
belongs in the workflow regardless of platform - that is an honest scoping conversation,
not a capability gap to argue past.

---

## 13. "We tried a RAG pilot and it disappointed."

**What it sounds like:** "We've been here before - we built something on [framework] and
it just wasn't good enough."

**What it usually means:** frequently the exact failure mode our positioning names as the
DIY displacement target: a framework-and-vector-database pipeline with no quality
instrumentation, stuck in engineering [messaging-house.md §5].

**The honest answer:** ask what broke it - almost always the answer is either that nobody
could tell *why* an answer was wrong (no per-query quality diagnosis) or the pipeline
never made it past a small sample of content into something real users touched. Both are
exactly what REMi and the POV-as-production-release-one model are built to prevent
[messaging-house.md §2; roi-value-model.md §4]. This time is structurally different, not
just a promise to try harder: the metric is agreed before the POV starts, it runs on real
content, and it produces the buyer's own measured numbers rather than a vendor claim.

**The trap to avoid:** do not dismiss the earlier attempt as "they did it wrong" - that
reads as arrogance to someone who spent real budget and credibility on it. Validate that
the failure mode is common and specifically named in how the market got here.

**When to concede:** if the previous pilot failed for reasons unrelated to
quality-instrumentation or production-path gaps (a genuine data-quality or
content-availability problem, for instance), say so honestly - a platform swap does not
fix a content problem, and promising otherwise sets up a second disappointment.

---

## 14. "Why not wait - this space changes monthly?"

**What it sounds like:** "AI is moving so fast, won't whatever we buy now be obsolete in
six months?"

**What it usually means:** reasonable caution about committing to infrastructure in a
fast-moving category, sometimes a polite way of saying "we are not ready to decide."

**Field-experience note:** this objection has no documented field frequency or tested
response in canon - the answer below is built from genuinely grounded facts, not
invented, but should be treated as first-draft until field experience confirms or refines
it.

**The honest answer:** two grounded points reduce the cost of waiting versus starting.
First, ARAG is model-agnostic - 30+ LLMs are natively selectable, so a buyer is not
locking into today's model generation; when a better model ships, it is a configuration
change, not a rearchitecture [messaging-house.md §1, pillar 1]. Second, the one-feature
POV is a small, reversible commitment - entry under US$1,000/month, scoped to one
feature, producing the buyer's own business case as a by-product
[roi-value-model.md §6, §4]. The category churning is a reason to start small and stay
flexible, not a reason to defer learning entirely - and the underlying need (staff and
customers who cannot find answers in what the organisation already knows) does not become
less real while the category matures [operating-inside-progress.md §6].

**The trap to avoid:** do not argue the category has stopped moving, or that ARAG is
immune to it - both are false and would not survive scrutiny from a buyer who reads the
same AI news. Do not manufacture urgency ("prices go up next quarter") without a genuine,
governed fact behind it.

**When to concede:** if the buyer's real position is that they are not ready to commit
budget or a POV owner right now, regardless of the technology conversation, that is a
timing and readiness issue the discovery framework's scorecard should surface honestly
rather than override with a sales push [discovery-qualification-framework.md §6].

---

## Source map

- **The three deal-killers, capability-wins-99%, buyer psychology, one-feature doctrine,
  champion/referral dynamic** - `content/positioning/operating-inside-progress.md` §4b,
  §6.
- **Positioning statement, pillars, DIY/hyperscaler displacement, no-accuracy-% rule,
  locked pricing/certification facts** - `content/positioning/messaging-house.md` §1, §2,
  §5, §6.
- **Budget anchoring, value levers, POV-as-production-release-one** -
  `content/enablement/roi-value-model.md` §2, §3, §4, §6 (this rebuild).
- **Discovery scorecard, disqualifiers** -
  `content/enablement/discovery-qualification-framework.md` §5, §6 (this rebuild).
- **Home card sequencing correction (REMi/deploy-anywhere lead, MCP demoted)** -
  `content/enablement/battlecards/progress-agentic-rag-home-battlecard.md`, v1.0,
  3 Sep 2026.
- **Hyperscaler objection language and trap questions** -
  `content/enablement/battlecards/aws-bedrock-q-battlecard.md`,
  `azure-ai-foundry-copilot-battlecard.md`, `google-gemini-enterprise-battlecard.md`.
- **Elastic incumbency, cost-unpredictability evidence** -
  `content/enablement/battlecards/elastic-battlecard.md`.
- **Connector-breadth concession** - `content/enablement/battlecards/glean-battlecard.md`,
  `onyx.md`.
- **MCP-erosion correction** -
  `content/enablement/battlecards/cohere-north-battlecard.md`, v1.1, 3 Sep 2026.
- **Nuclia acquisition by Progress Software; GDPR/EU AI Act posture** - `nuclia-mcp`
  knowledge box, `nuclia.com` homepage, Certainly case study, and `nuclia.com/security/`,
  all re-queried 5 September 2026.
- **Certifications (ISO 27001, SOC 2 Type 2) - vendor-stated, not independently verified**
  - `content/positioning/messaging-house.md` Locked Facts - Certifications, sourced to
  `nuclia.com/security/` via the KB, 5 September 2026; field rule 5 governs every use.
- **REMi model architecture (Mistral 7B v0.3 Instruct adapter), open-source availability**
  - `nuclia-mcp` knowledge box, `nuclia.com/developers/remi-open-source-rag-evaluation-
  model/`, re-queried 5 September 2026.
- **Deployment modes (cloud/hybrid/on-prem incl. generative model)** - `nuclia-mcp`
  knowledge box, `nuclia.com/nuclia-deployment-options/`, re-queried 5 September 2026.

**Could not ground / flagged gaps:**
- No canon source records the field frequency or a tested response for objection 14
  ("why not wait") - marked as first-draft synthesis in that entry, same status as the
  prior version of this guide.
- Nuclia's team size, founding date or other "how small" specifics were not found in the
  KB or local canon - the acquisition fact alone grounds objection 7; no claim about
  company size is made in either direction.
- No accuracy percentage appears anywhere in this guide - a deliberate omission per field
  rule 5, not an oversight. Every ISO 27001/SOC 2 Type 2 mention is framed as
  vendor-stated (Progress/Nuclia's own claim on `nuclia.com/security/`), never as
  independently verified, and no certification beyond that vendor statement is claimed
  anywhere - per field rule 5 and hard rule 3.

---

## Change log

- **2026-09-05 (v2.1)** - Field-rule-5 fix (lead's gate finding, same day): every ISO
  27001/SOC 2 Type 2 mention re-framed from "verified"/"accredited" to vendor-stated,
  not independently verified by us, matching the guide's own guardrail line (which
  previously contradicted the objection-6 and objection-7 wording). Citations updated to
  `messaging-house.md` Locked Facts - Certifications, the new entry the lead added the
  same day making this framing canon. No other content changed.
- **2026-09-05** - v2.0. Full rebuild per GM directive (5 Sep 2026): restructured to lead
  with the three field-named deal-killers before any competitor-specific objection (per
  brief), added two new entries (MCP-parity erosion against Cohere North, connector-
  breadth concession) that v1.0 did not carry, and re-verified every ARAG capability claim
  (REMi architecture and open-source availability, deployment modes, security/GDPR/EU AI
  Act posture, Nuclia acquisition) against `nuclia-mcp` this session rather than carrying
  the prior citations forward unchecked. Cross-references updated to the same-day v2.0
  rebuilds of the discovery framework and ROI model.
- **2026-08-12** - v1.0 (superseded). First draft, twelve objections, built from the field
  interview and the then-current battlecard set.
