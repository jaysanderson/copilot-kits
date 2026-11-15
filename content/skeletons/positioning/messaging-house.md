# Progress Agentic RAG - Messaging House

**Owner:** the lead (PMM). **Created:** 8 Aug 2026 (v1). **Status:** living document -
refresh when the product or category moves, and tell the org what changed.
**Sources:** every product claim below is verified against the `nuclia-mcp` knowledge
box (hard rule 3) unless flagged otherwise; pricing figures carry their own provenance
because the KB's pricing page is stale (see Locked Facts). Strategy this serves:
`gtm-strategy.md`. Progress-internal constraints: `operating-inside-progress.md`.

---

## 1. Positioning statement

For **teams building AI products and knowledge workflows on their own data** - product
builders and ISVs embedding retrieval into their software, and enterprise
architects putting agentic AI over governed knowledge - **Progress Agentic RAG** is the
**RAG-as-a-service platform** that turns any body of unstructured and structured data
into grounded, cited, quality-measured answers and agents.

Unlike **DIY retrieval stacks assembled from frameworks and vector databases** (months
of pipeline engineering, no quality instrumentation) and **hyperscaler AI bundles**
(cloud lock-in, stacked metering, retrieval as a side feature), ARAG is **purpose-built
for retrieval end to end** - ingestion through answer - with **per-query quality
measurement (REMi)** and **a deployment choice rather than one cloud - SaaS, private
cloud, or hybrid with inference and the index in ours**.

**The one differentiated value, in a sentence (DAM canon v5, 8 Oct 2026, verbatim):**
*Retrieval you can trust and prove - grounded, cited answers with native per-query quality
metrics, and a deployment choice rather than one cloud: SaaS, private cloud, or hybrid with
inference and the index in ours.*

> The previous local sentence ended on a deployment over-promise - the exact clause canon v4
> removed and v5 refined again. It is described rather than quoted, for the reason given under
> pillar 3. It survived here for eleven days in the single most reused sentence in the house.

## 2. Messaging pillars

### Pillar 1 - Genuinely agentic retrieval, not a chatbot on a vector store
ARAG's agents do real work at both ends of the pipeline: ingestion agents (labelling,
generation, graph extraction, Q&A generation) enrich content as it lands, and the
Retrieval Agent (RAO) plans multi-step retrieval, navigates knowledge graphs, and calls
external tools over MCP with the caller's permissions enforced.
**Proof (KB-verified + shipped):** task-specific and multi-step agents documented
platform capabilities; knowledge-graph extraction and navigation; the RAO reference
architecture and live demos in the DAM (Plant-demo ERP, Operator Fleet, Ignition) showing
an ARAG agent driving an app's own MCP tools under RBAC.

### Pillar 2 - Trust you can measure, per query
ARAG ships REMi, a purpose-built RAG evaluation model, natively in the platform: every
answer can be scored for answer relevance, context relevance and groundedness, in the
dashboard and via SDK, in real time. Low scores diagnose the failure (retrieval versus
generation). Answers are grounded and cited back to source.
**Proof (KB-verified):** REMi metrics and real-time integration; "the only RAG platform
with native quality metrics" is the vendor's own positioning claim - usable, but always
attributed, never presented as independent. Never quote an accuracy percentage; prove
quality live with REMi and cited answers (field rule 5).

### Pillar 3 - Run it where your governance allows, at a price you can start on
**SYNCED FROM DAM CANON 12 Oct 2026 (pillar v4, changed 8 Oct 2026). The previous local text was
11 DAYS STALE and asserted all three deployment modes this product does not have, plus a claim
about where customer storage sits in hybrid.** The excluded wording is not reproduced here, because
a record of a withdrawn claim that quotes it has republished it - which is how this same defect was
found in another file tonight, and the author of this note then committed it in the fix for it. The
DAM was corrected on 8 Oct; this working copy was not, and agents read this file. That is the correction-to-a-generator failure one level out: the canon was fixed and the
copy people actually consume was not.

Three deployment modes: SaaS, private cloud, and hybrid, where only inference and the index run in
the cloud - and in hybrid the index rests in Progress's cloud, so it persists there rather than
passing through. **Confirmed with Progress 8 and 9 Oct 2026 and not published on any Progress
page**, so a seller states the date and offers to get it in writing. Entry is self-serve with
published pricing and a free trial; consumption is usage-based, not per-seat. The structural counter
to hyperscaler lock-in and to enterprise-search vendors with no self-serve entry.

**Be careful which half you are sure of.** CONFIRMED: what runs in Progress's cloud is inference
and the index, and the index rests there. INFERRED, not stated: that the source documents stay
solely with the customer - that is our reading of the word "only", Progress has not said it, and
what executes and what is retained are different questions to a security team. **So never promise a
customer their documents stay with them.** Also UNCONFIRMED: whether that index holds extracted text
as well as vectors, which a security team reads as a different disclosure. **Never tell a customer
their data stays in their environment until it is answered in writing.**

**There is no on-premises mode, no offline mode and no air-gapped mode.** Any artifact saying
otherwise is wrong and is being corrected.

**Approved lines (what a seller says aloud):**
- Three deployment modes - SaaS, private cloud, or hybrid with inference and the index in the cloud
- Start at published pricing, not a platform RFP
- In hybrid, inference and the index run in our cloud and the index rests there - confirmed with
  Progress in October 2026, not yet published, and we will put it in writing for you
- What we have not been told is where your source documents end up, so I will not promise you they
  stay with you - I will get it in writing

**Proof:** fact `deployment_modes` (v6 - no on-premises, offline or air-gapped;
documents-stay-with-you is inferred, not stated); facts `pricing_starter` ($700/mo) and
`pricing_pro` ($1,925/mo), live-verified 11 Oct 2026; the Sinequa battlecard for the
no-self-serve contrast.

## 3. Message by persona

> **The canonical persona roster lives in the Kitforge Personas & Positioning
> section, not this file (as of 10 Aug 2026).** Eight field-grounded personas:
> CIO, Marketing Professional / Digital Experience Owner, Solutions Architect,
> Product Manager (ISV & direct), ICT & Digitalisation Leader, Research
> Professional, Partner (Reseller/SI/Agency), and Divisional CTO (Enterprise
> Function IT) - each with message, objections, proof links and vocabulary,
> maintained as versioned objects. The three sketched below were the founding
> set and remain valid; consult the DAM pages as the source of truth.

- **CIO (economic buyer):** "Grounded AI over your knowledge without betting the
  estate on one cloud - deploy where your governance requires, measure answer quality
  per query, and start at published pricing instead of a seven-figure platform RFP."
  Leads with: risk (groundedness + REMi), deployment choice (SaaS, private cloud or hybrid -
  NOT on-premises and NOT air-gapped; neither exists), TCO
  (usage-based versus stacked hyperscaler metering or per-seat).
- **CMO / digital-experience owner:** "Your content becomes answers customers can act
  on - search that understands questions, recommendations that understand your
  catalogue, on your own site and brand." Leads with: customer experience, conversion,
  personalisation (Bioeconomy, PUG Tube, Home-two demos as proof).
- **Solutions Architect (champion):** "A retrieval platform you integrate, not a
  framework you assemble - one API from ingestion (OCR, extraction strategies, DA
  agents) to answer (cited, scored), agents that call your MCP tools under your RBAC,
  and REMi to tell you which layer failed when quality drops." Leads with: the RAO
  reference architecture, the server-side proxy pattern, honest limits (the
  solution-architecture reveal standard).

## 4. Category narrative (the TOFU frame)

Enterprise AI's real bottleneck is not the model, it is trustworthy retrieval over the
knowledge an organisation actually has. Single-shot RAG answered lookup questions;
agentic RAG - retrieval that plans, traverses relationships (knowledge graphs), uses
tools and proves its grounding - is what makes AI dependable enough for work that
matters. The knowledge-graph franchise (podcast, decks, Spanish edition) carries this
narrative without naming the product; it earns the vertical conversations the wedge
campaigns harvest. (Hard rule 13 TOFU exception applies.)

## 5. What we displace, and what we concede

- **Displace: DIY pipeline assembly** (framework + vector DB + glue). Argument:
  engineering months, no quality instrumentation, every capability hand-built.
- **Displace: "use what's in our cloud" inertia** (Bedrock/Q, Gemini Enterprise, Azure
  Foundry/Copilot). Argument: stacked real cost, cloud lock-in, retrieval as a side
  feature; ARAG meets data where it is. (Battlecards carry the numbers.)
- **Concede honestly** (per battlecards, do not contest): Glean's connector breadth
  for company-wide search; Sinequa's named regulated-industry certifications; A2A and
  compliance-list breadth of the hyperscalers. We win platform/product-embed deals and
  sovereignty deals, not generic workplace-search bake-offs.

## 6. Locked facts (the numbers artifacts may use)

| Fact | Value | Source / date | Status |
|---|---|---|---|
| REMi metrics | answer relevance, context relevance, groundedness; real-time, dashboard + SDK | nuclia-mcp KB (rag-quality page) | Verified (vendor capability) |
| "Only RAG platform with native quality metrics" | vendor positioning claim | nuclia.com via KB | Use only attributed to Progress/Nuclia |
| Deployment modes | THREE modes: SaaS; private cloud; hybrid, where only inference and the index run in the cloud and the index RESTS there. NO on-premises, NO offline, NO air-gapped - those are claimed nowhere and the 10 Aug 2026 record of them is SUPERSEDED, not stale. UNCONFIRMED: where the source corpus is stored in hybrid ("documents stay with you" is our INFERENCE from "only", never stated by Progress), and whether the cloud-side index holds extracted text as well as vectors | Confirmed with Progress 8 and 9 Oct 2026; canon `deployment_modes` v6 | CONFIRMED BUT UNPUBLISHED - attribute to Progress, give the date, say it is not published, and tell the reader to get it in writing. Never promise a customer their documents stay with them |
| Certifications | Progress/Nuclia states ISO 27001 and SOC 2 Type 2 (nuclia.com/security) | vendor security page, via KB, 5 Sep 2026 | VENDOR-STATED, NOT independently verified by the factory. Field rule 5: never assert a named certification as fact in customer-facing material without verification OUTSIDE the KB - frame as vendor-stated and confirm current status before external use. Concede broader lists honestly (e.g. Elastic FedRAMP/HIPAA) |
| Current self-serve pricing | Starter $700/mo, Pro $1,925/mo, Enterprise custom; Starter and Pro include up to 10,000 tokens/mo | live pricing page, re-verified 11 Oct 2026 | Verified live 11 Oct 2026 (Starter $700, Pro $1,925, Enterprise custom; 10,000 tokens/mo included, $0.008/token over). Starter is TEXT-BASED FILES ONLY, 750MB/file; Pro all types, 1.5GB/file. Pro includes 2 knowledge boxes, up to 8 total, extras $750/mo. KB page STALE (old Fly $600/Growth $1,500) - never quote KB figures |
| Consumption model | subscription + usage-based consumption (Nuclia Token), not per-seat; overage $0.008/token | live pricing page, re-verified 5 Sep 2026 | Verified live 5 Sep; token rate DRIFTED from $0.007 (6 Aug) to $0.008 - re-verify live before quoting |
| Free trial | 14-day free trial | live pricing page, 5 Sep 2026 | Live page 5 Sep does not state a card requirement (6 Aug read: no card) - re-verify before quoting in outbound |
| Pro QuickStart offer (limited time) | 100k complimentary tokens/mo for the first 3 months on Pro; end date EXTENDED to 30 Nov 2026 (was 30 Sep) | live pricing page, re-checked 1 Oct 2026 (battlecard refresh w40 and the budget-source build both saw it live) | Time-boxed - check it is still live before quoting; drop after 30 Nov 2026. Structural documents (budget guide, path to production) leave it out regardless |
| ARR context | ~$1M ARR, $10M mission | Jay / operating-inside-progress.md | Internal only - never in artifacts |
| Accuracy percentage | none published | field rule 5 | Never fabricate; prove with REMi live |

## 7. Launch-narrative slots

When a capability launches, its narrative gets one entry here (positioning + message
spine) so decks, content and enablement launch consistently. Current: none pending.

## Change log
- **2026-10-01** - Pro QuickStart offer end date corrected from 30 Sep to 30 Nov 2026 (extended,
  confirmed live on progress.com/agentic-rag/pricing during the w40 battlecard refresh and the
  budget-source build). Overage billing precision added (quarterly in arrears). Tier prices and
  token allowance re-verified unchanged. DAM canonical asset synced same session.
- **2026-09-05** - Pricing locked-facts re-verified live against progress.com/agentic-rag/pricing
  (lead check, prompted by the overview-doc rebuild). Drift found and corrected: token overage
  $0.007 -> $0.008/token; added the 10,000-token/mo base allowance on Starter and Pro; added the
  time-boxed Pro QuickStart offer (100k complimentary tokens/mo for 3 months).
  Tier prices unchanged (Starter $700, Pro $1,925, Enterprise custom). DAM canonical asset synced
  same session.
- **2026-08-08** - v1. Written as the strategy's first sequencing item. Claims
  KB-verified same day; pricing corrected against the 6 Aug live-page check from the
  Vectara battlecard refresh (KB pricing page confirmed stale).
