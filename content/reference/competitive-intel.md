# Competitive Intelligence Dossier - Progress Agentic RAG (ARAG)

**Owner:** market-analyst. **Status:** living document - refresh in place, do not fork.
**Last updated:** 2026-08-08 (news-sweep refresh - see change log).

This is the single competitive-intel source for the org. account-analyst pulls from this
for account-level competitive angles; the lead (PMM) decides positioning against it;
sales-enablement builds battle cards and kill-sheets from it; deck-builder, copywriter and
video-producer cite it rather than re-researching. Nothing in this file substitutes for a
KB-verified ARAG product claim - see hard rule 3.

**How to extend this file:** each competitor gets one row in its tier table now, and can
graduate to a full teardown section (template at the bottom) without restructuring the
file. Do not rewrite existing rows when adding a new competitor - append.

---

## 1. Category framing

There is no dedicated Gartner Magic Quadrant or IDC MarketScape specifically for
"agentic RAG platforms" as a named category yet (checked 2026-08-06). The closest
analyst coverage:

- **Forrester Wave: Cognitive Search Platforms, Q4 2025** - the closest formal analyst
  evaluation touching this space, covering Glean, Coveo, Sinequa and other "insight
  engine" vendors. Forrester's framing: the market has split into **platform-native**
  players (Microsoft Copilot, Google Gemini Enterprise) and **specialist platforms**
  (Glean, Coveo, Sinequa, Atolio), and the 2026 conversation inside this Wave has moved
  from "RAG" to "agentic retrieval and context engineering." [Forrester, Q4 2025](https://www.forrester.com/report/the-forrester-wave-tm-cognitive-search-platforms-q4-2025/RES186654)
- **Gartner Peer Insights - Insight Engines market** - Gartner tracks this adjacent
  category (Algolia, Elastic and others compared here) but ARAG/Nuclia's placement in it
  has not been confirmed - see COULD NOT CONFIRM below.
- **Gartner "Getting Started With Retrieval Augmented Generation"** - a methodology
  document, not a vendor ranking. [Gartner](https://www.gartner.com/en/documents/5415263)
- ARAG/Nuclia does not currently appear placed in any named Gartner MQ, Forrester Wave or
  IDC MarketScape found in this pass - **flagged, not confirmed absent**; worth a direct
  check next refresh rather than assumed.

**Working definition for this dossier:** ARAG competes for the same buying decision as
any vendor an enterprise or ISV would evaluate to answer "how do we ground an LLM/agent
in our own data, reliably and with citations, without building the retrieval stack
ourselves." That spans four tiers below, from closest substitute to build-it-yourself.

---

## 2. Competitor tiers

### Tier A - Direct: managed RAG-as-a-service / agentic retrieval platforms

The closest competitive set - vendors selling a hosted, full-pipeline RAG or agentic
retrieval product via API, the same buying motion as ARAG.

| Vendor | What it is | Positioning signal | Differentiator / gap (if evidenced) | Source |
|---|---|---|---|---|
| **Vectara** | Managed RAG-as-a-service: ingestion, embedding, retrieval, hallucination filtering and generation behind one API ("RAG in a box"). Ships its own MCP server (`vectara-mcp`, open source) and a Python agent-building library (`vectara-agentic`, built on the LlamaIndex agent framework, ReAct/OpenAIAgent/LATS/LLMCompiler agent types) | Fast time-to-value for narrow, well-bounded use cases; own embeddings and "Factual Consistency Score" hallucination metric; supports bring-your-own-LLM (OpenAI-compatible incl. Azure OpenAI and Anthropic Claude, plus Google Vertex AI/Gemini and the OpenAI Responses API for o1/o3) - customer supplies their own API key/credentials, confirmed against Vectara's own docs 2026-08-06 | Smaller vendor team than hyperscaler-backed rivals. Compliance: Vectara itself holds **SOC-2 Type II and HIPAA** directly - **ISO 27001 belongs to its cloud host (AWS/GCP), not to Vectara**, confirmed against Vectara's own security page 2026-08-06; don't conflate the two in a battle card. **Nuclia's own published benchmark** (vendor-sourced, not independent) shows Nuclia outscoring Vectara's default and Mockingbird configs on Answer Relevance, Context Relevance, Groundedness and Answer Correctness on the Docmatix 1.4k set - cite as ARAG's own claim, not third-party proof | [Atlan](https://atlan.com/know/enterprise-rag-platforms-comparison/); [Sphere](https://www.sphereinc.com/blogs/best-enterprise-rag-platforms-2026); [Nuclia developers - Nuclia vs Vectara](https://nuclia.com/developers/nuclia-vs-vectara-detailed-analysis-using-remi/); [Vectara docs - bring your own LLM](https://docs.vectara.com/docs/search-and-retrieval/bring-your-own-llm) (checked 2026-08-06); [Vectara security page](https://www.vectara.com/legal/security-at-vectara) (checked 2026-08-06); [vectara-mcp on GitHub](https://github.com/vectara/vectara-mcp); [py-vectara-agentic on GitHub](https://github.com/vectara/py-vectara-agentic) |
| **Ragie** | Managed RAG platform, transparent pricing tiers, clean REST APIs | Actively marketing itself as a migration target for Vectara customers | Newer, narrower ecosystem than Vectara | [Atlan](https://atlan.com/know/enterprise-rag-platforms-comparison/) |
| **Writer** | Vertically integrated platform: own Palmyra LLM family plus a Knowledge Graph RAG layer | 300+ enterprise customers cited incl. Accenture, Intuit, Salesforce, Uber, Vanguard, L'Oreal, Marriott; domain models (Med, Fin). Launched autonomous, event-triggered agents (30 Apr 2026) that act on business signals across Gmail, Gong, Google Calendar, Google Drive, SharePoint and Slack without a prompt - pitched directly against Amazon, Microsoft and Salesforce, marking a shift from "knowledge platform" to "does the work autonomously" | Locked to Palmyra models; no self-hosting option. The autonomous-agent push raises the objection-handling angle: an agent acting without a prompt is only as safe as the grounding behind it - worth asking a prospect what happens when Writer's agent acts on an ungrounded inference | [Sphere](https://www.sphereinc.com/blogs/best-enterprise-rag-platforms-2026); [VentureBeat, 30 Apr 2026](https://venturebeat.com/technology/writer-launches-ai-agents-that-can-act-without-prompts-taking-on-amazon-microsoft-and-salesforce) |
| **Cohere (North)** | Sovereign AI deployment platform bundling Command generative models, Compass search and customisable agents | Canadian sovereign posture (named live infrastructure partnerships - Bell/BCE, SAP Canada); UK is commercial-presence-and-certification only (UK Cyber Essentials, no confirmed named UK sovereign-cloud region); positioned as an alternative to Microsoft Copilot / ChatGPT Enterprise; strong reranking (Rerank 4, named dedicated-instance pricing); also holds ISO 42001 (AI management system) alongside SOC 2 Type 2 and ISO 27001 | No standing HIPAA certification/BAA on the hosted North product - Cohere's own Trust Center scopes its BAA to custom model-development engagements only, explicitly excluding hosted SaaS products. Corrected 2026-08-06 (was "HIPAA support on roadmap only" per a third-party roundup; Cohere's own primary source gives no roadmap commitment, just a narrow current exception) | [Sphere](https://www.sphereinc.com/blogs/best-enterprise-rag-platforms-2026) (original); [Cohere Trust Center](https://trustcenter.cohere.com/) and [cohere.com/pricing](https://cohere.com/pricing) (primary, fetched 2026-08-06); [RCR Wireless](https://www.rcrwireless.com/20250729/ai-infrastructure/bell-cohere-ai), [SAP Canada](https://news.sap.com/canada/2026/02/sap-and-cohere-expand-partnership-to-launch-sovereign-ai-solutions-globally-beginning-in-canada/), [Bloomberg](https://www.bloomberg.com/news/articles/2026-06-18/bce-teams-with-cohere-on-canada-ai-data-center-to-boost-sovereign-strategy) (Canada partnerships, independent/press, fetched 2026-08-06) |
| **SphereIQ** | Self-hosted, compliance-first RAG platform with an EU AI Act wizard and BYOK LLM support | Data-residency and regulatory control as the lead pitch | Newer ecosystem, smaller market presence. **Confidence caveat (checked 2026-08-08):** a targeted search for independent press coverage (Reuters, Bloomberg, TechCrunch, VentureBeat, The Register, CIO-tier outlets) found none - every discoverable source on SphereIQ, including this dossier's own characterisation, traces back to Sphere Inc.'s own marketing content (its blog ranks and describes its own platform). This is not evidence SphereIQ is failing - it is evidence the entire SphereIQ row rests on vendor self-description with no independent corroboration. Do not cite any SphereIQ claim as third-party-verified in a battle card or deal conversation | [Sphere](https://www.sphereinc.com/blogs/best-enterprise-rag-platforms-2026) (vendor's own site - self-description, weight accordingly) |
| **AI12z** | Managed, self-serve RAG + ReAct agent platform, but scoped specifically to a customer's own **public website/CMS content** - generates embeddable AI search boxes/chatbots from a sitemap, sold through CMS partner channels (Sitecore, Contentstack, Magnolia, RWS/Optimizely, WordPress, Drupal, 9+ more). Founded 2023 (Bill and Nicole Rogers, ex-Ektron). **Narrower scope than the rest of this tier** - no evidence of a general developer API/SDK for building non-website applications; competes for the "AI-powered website assistant" budget line, not general enterprise-knowledge or ISV-embedding RFPs | No-code single-URL agent generation ("Vibe Coding") marketed as production in hours; 13+ named CMS connectors with automated sync; a named 12-report GEO/AEO/AIO answer-engine-visibility suite with no equivalent found elsewhere in this dossier | No SOC 2/ISO 27001/FedRAMP named on its Trust Center (HIPAA, GDPR, PCI DSS, CCPA are named); no on-prem/air-gapped option found; no named enterprise customer, funding figure or analyst coverage found in this pass; entry pricing ($3,156/year Growth tier) is annual-upfront only despite a separate AI12z-owned page claiming "$99/month" - an unresolved inconsistency on AI12z's own site. **Confidence caveat (checked 2026-08-08):** same caveat as SphereIQ above - a targeted search for independent press coverage found none beyond a self-submitted PR Newswire release and CMS-partner directory listings (real, but not journalism). Tracxn lists AI12z at 9 employees with no funding raised as of 31 Jan 2026. Treat AI12z claims as vendor self-description, not independently verified | [ai12z.com/platform](https://ai12z.com/platform/); [ai12z.com/pricing](https://ai12z.com/pricing/); [ai12z.com/trust-center](https://ai12z.com/trust-center/); [docs.ai12z.net connectors](https://docs.ai12z.net/docs/connectors/connector-intro); [PR Newswire](https://www.prnewswire.com/news-releases/ai12z-automatically-generates-website-ai-agents-from-a-single-url-302587607.html); [CMSWire](https://www.cmswire.com/digital-experience/ai12z-launches-vibe-coding-for-no-code-ai-assistants/); independently corroborated as a real, current partner via [RWS](https://www.rws.com/partners/list/ai12z/), [Sitecore](https://www.sitecore.com/partners/isv/ai12z-ai-search-digital-assistants), [Contentstack](https://www.contentstack.com/marketplace/ai12z) and [Magnolia CMS](https://docs.magnolia-cms.com/ai12z/) partner listings - all fetched 2026-08-06 |

### Tier B - Enterprise/workplace search and insight engines expanding into RAG

Vendors with an established enterprise-search or "insight engine" product who have
layered generative/RAG answers on top. These compete for the same "ask a question of our
company knowledge" budget line, often from an incumbent-vendor position.

| Vendor | What it is | Positioning signal | Differentiator / gap (if evidenced) | Source |
|---|---|---|---|---|
| **Glean** | SaaS workplace search with 100+ connectors, permission-aware knowledge graph, generative answers | Wins on connector breadth, permission depth and UX; built for internal workplace search and agentic workflows. Independent reporting (Feb 2026) frames Glean's actual strategy as building an infrastructure/context layer that sits *beneath* every AI tool an enterprise uses, not just shipping a single search app - a broader land-grab than "workplace search vendor" | Per-user SaaS pricing (~US$50-75/user/month, ~US$50-60k minimum annual contract, 100+ seat minimums cited); not a platform you build on - retrieval strategy isn't customisable; Forrester Q4 2025 notes its connector ecosystem is narrower than some peers and contextual-enrichment depth is comparatively limited today. The "context layer" positioning is broad and horizontal - useful angle against ARAG's story of purpose-built, governable retrieval agents for specific high-stakes workflows | [Atlan](https://atlan.com/know/enterprise-rag-platforms-comparison/); [Sphere](https://www.sphereinc.com/blogs/best-enterprise-rag-platforms-2026); [Forrester Q4 2025](https://www.forrester.com/report/the-forrester-wave-tm-cognitive-search-platforms-q4-2025/RES186654); pricing per [ChapsVision market roundup](https://www.chapsvision.com/blog/enterprise-ai-search-compared/); [TechCrunch, 15 Feb 2026](https://techcrunch.com/2026/02/15/the-enterprise-ai-land-grab-is-on-glean-is-building-the-layer-beneath-the-interface/) |
| **Coveo** | Cognitive/insight-engine search platform, flat (not per-seat) pricing, relevance engine that learns from user behaviour | Purpose-built for external-facing search (customer/e-commerce) as well as internal; named a Leader in Forrester Wave Q4 2023 | Forrester Q4 2025 notes Coveo's agentic-AI vision still has "some catching up to do" against specialists | [Forrester Q4 2025](https://www.forrester.com/report/the-forrester-wave-tm-cognitive-search-platforms-q4-2025/RES186654); [Coveo Forrester blog](https://www.coveo.com/blog/leader-forrester-wave-cognitive-search/) |
| **Sinequa** | Cognitive search platform: 200+ connectors, NLP across 22+ languages, native neural search + RAG architecture | Ranked highest on "Current Offering" in Forrester Wave Q4 2023; serves regulated verticals (life sciences, financial services, defence, energy, manufacturing) | Price point cited at US$250k+, reflecting the regulated-industry specialisation - a high floor vs a self-serve platform | [Forrester Q4 2023 via Sinequa](https://www.sinequa.com/resources/assets/forrester-wave-cognitive-search-q4-2023/); pricing per [ChapsVision market roundup](https://www.chapsvision.com/blog/enterprise-ai-search-compared/) |
| **Elastic (A rival search product)** | Search/analytics platform with a relevance engine (lexical, vector, hybrid search, rerankers) marketed explicitly for RAG workloads | "Architectural latitude" positioning - build sophisticated retrieval yourself on top of Elastic rather than consume a packaged pipeline | Requires more in-house engineering than a managed RAG-as-a-service; closer to a DIY-stack component than a turnkey platform despite the RAG marketing push | [Elastic - RAG](https://www.elastic.co/a rival search product/rag); [Elastic - relevance](https://www.elastic.co/enterprise-search/relevance) |
| **Algolia** | Cloud search platform (NeuralSearch + generative features added 2025-2026), historically strongest in e-commerce/product search | "Working hybrid search faster" - optimised for speed-to-implement over architectural depth. Named a Leader for the third consecutive year in the **2026 Gartner Magic Quadrant for Search and Product Discovery** (confirmed 24 Jun 2026) | Narrower fit for general enterprise-knowledge RAG than for catalog/commerce search. **Category clarification:** Algolia's Gartner MQ leadership sits in the *Search and Product Discovery* category - commerce/site search - not an enterprise-knowledge or agentic-RAG category. Algolia's analyst credibility there doesn't automatically transfer to an enterprise-knowledge grounding deal; don't let "Gartner Leader" alone read as equivalent proof in that context | [contra collective comparison](https://contracollective.com/blog/algolia-vs-a rival search product-enterprise-commerce-search-2026); [BusinessWire, 24 Jun 2026](https://www.businesswire.com/news/home/20260624362619/en/Algolia-Recognized-as-a-Leader-for-the-Third-Consecutive-Year-in-the-2026-Gartner-Magic-Quadrant-for-Search-and-Product-Discovery) |

### Tier C - Cloud hyperscaler native RAG / agent platforms

The "just use what's already in our cloud" alternative - bundled into AWS, Azure or
Google Cloud spend, the default competitor for any account already committed to one
hyperscaler.

| Vendor | What it is | Positioning signal | Differentiator / gap (if evidenced) | Source |
|---|---|---|---|---|
| **AWS Bedrock Knowledge Bases + Amazon Q Business** | AWS-native managed RAG (Bedrock KB) plus a packaged enterprise knowledge assistant (Q Business, 40+ data-source connectors incl. S3, RDS, Salesforce, SharePoint) | FedRAMP High availability; strongest where the account's data already lives in AWS services. **Business-move update (checked 2026-08-08):** AWS moved roughly 20 older AI services, including Amazon Kendra, Q Business and Bedrock Agents ("classic"), into maintenance mode from 30 Jun 2026 - no new customer sign-ups from 30 Jul 2026, existing customers kept on security patches only. AWS is consolidating around the newer Bedrock Managed Knowledge Base, AgentCore and Amazon Quick Suite instead | Infrastructure cost opacity cited as a gap; best-fit is AWS-resident data, not a neutral cross-cloud position. The maintenance-mode move is a genuine migration-urgency trigger, not just a rebrand - any account still on Kendra or "classic" Q Business is being pushed onto a newer, less-proven stack whether they asked for it or not; a real opening for a competitive conversation in an AWS-incumbent deal | [Atlan](https://atlan.com/know/enterprise-rag-platforms-comparison/); [Sphere](https://www.sphereinc.com/blogs/best-enterprise-rag-platforms-2026); [Forbes, 24 Jul 2026](https://www.forbes.com/sites/janakirammsv/2026/07/24/aws-kills-the-ai-services-it-launched-just-two-years-ago/); [AWS, 30 Jun 2026 (primary)](https://aws.amazon.com/about-aws/whats-new/2026/06/aws-service-availability/) |
| **Microsoft Azure AI Foundry / Copilot** | Azure-native build-and-run agent layer (Foundry Agent Service, GA) plus Agent365 as a governance control plane; deep Microsoft 365/SharePoint integration with native ACL sync | 10,000+ customers on Foundry cited (2026); strongest compliance certifications (FedRAMP High, DoD IL5) among cloud-native options | OpenAI-model-first, Azure-bound; native ACL sync is a genuine RBAC strength worth tracking as a gap-closer against ARAG's own RBAC story | [Sphere](https://www.sphereinc.com/blogs/best-enterprise-rag-platforms-2026); [linesNcircles - Enterprise Agent Platforms 2026](https://linesncircles.com/Blog/Enterprise/Enterprise_Agent_Platforms_2026) |
| **Google Gemini Enterprise (rebranded Vertex AI Search)** | Google's RAG/agent platform, rebranded at Cloud Next 2026 into "Gemini Enterprise Agent Platform" (Agent Studio, Agent Runtime, Memory Bank, Agent Identity/Gateway) | Native BigQuery integration; 1M+ token context window; only major cloud platform citing native Agent-to-Agent (A2A) protocol support, 150+ orgs. **Business-move update (checked 2026-08-08):** the consolidation is a genuine platform retirement, not a relabel - Google confirmed the standalone Vertex AI product line ends, with all future roadmap delivered under the Gemini Enterprise brand. Google's own framing of the differentiator is governance (Agent Registry, Agent Gateway, semantic policy, audit logs) aimed at CIOs/CISOs, not retrieval or grounding quality | Gemini-first (model lock-in); frequent rebranding cited as a market-confusion gap. Google is explicitly leading with governance and control-plane features rather than grounding fidelity - a useful angle to reframe a Gemini Enterprise deal around retrieval/citation quality, where ARAG's story is comparatively stronger | [Atlan](https://atlan.com/know/enterprise-rag-platforms-comparison/); [Sphere](https://www.sphereinc.com/blogs/best-enterprise-rag-platforms-2026); [linesNcircles](https://linesncircles.com/Blog/Enterprise/Enterprise_Agent_Platforms_2026); [CIO Dive, 22 Apr 2026](https://www.ciodive.com/news/google-cloud-AI-agent-gemini-enterprise-platform/802404/) |

### Tier D - DIY stack: assemble-your-own-RAG components

Not a vendor competitor in the traditional sense, but the real alternative ARAG displaces
most often: an internal engineering team builds the pipeline from open-source or
point-solution parts instead of buying a platform. Relevant as "the status quo we're
selling against," not a single company.

| Component | Vendor(s) | What it is | Source |
|---|---|---|---|
| Orchestration framework | **LangChain / LangGraph** | Multi-agent orchestration with RAG as one node; 500+ integrations; largest ecosystem but a history of breaking changes | [Atlan](https://atlan.com/know/enterprise-rag-platforms-comparison/); [Sphere](https://www.sphereinc.com/blogs/best-enterprise-rag-platforms-2026) |
| Orchestration framework | **LlamaIndex** | Data-first RAG framework, 160+ connectors, hierarchical chunking, managed LlamaCloud add-on; Python-only | [Atlan](https://atlan.com/know/enterprise-rag-platforms-comparison/); [Sphere](https://www.sphereinc.com/blogs/best-enterprise-rag-platforms-2026) |
| Orchestration framework | **Haystack (deepset)** | Modular pipeline framework emphasising explicit control/auditability; built for regulated, air-gapped/on-prem deployment; steeper learning curve | [Atlan](https://atlan.com/know/enterprise-rag-platforms-comparison/); [Sphere](https://www.sphereinc.com/blogs/best-enterprise-rag-platforms-2026) |
| Document-parsing framework | **RAGFlow (InfiniFlow)** | Open-source, template-based chunking with chunk visualisation; 91,600 GitHub stars (verified 2026-10-01, up from the 80,000+ previously cited); Apache 2.0; A rival search product is now optional in the default stack - the project's own docs name Infinity as the alternative document engine - so "A rival search product-dependent" no longer holds; smaller English-language community | [GitHub - infiniflow/ragflow, verified 2026-10-01](https://github.com/infiniflow/ragflow); [Atlan](https://atlan.com/know/enterprise-rag-platforms-comparison/); [Sphere](https://www.sphereinc.com/blogs/best-enterprise-rag-platforms-2026) |
| Vector database | **A vector database** | Fully managed, serverless vector DB; multi-cloud. Also offers **Bring Your Own Cloud (BYOC)**: the data plane deploys inside the customer's own AWS/GCP/Azure account for data sovereignty, network isolation and regional residency, while A vector database still manages a separate control plane for auth/billing - so "no self-hosting option" no longer holds | [A vector database docs - Bring Your Own Cloud, verified 2026-10-01](https://docs.a vector database.io/guides/production/bring-your-own-cloud); [Atlan](https://atlan.com/know/enterprise-rag-platforms-comparison/) |
| Vector database | **Weaviate** | Open-source vector DB, semantic + BM25 + multimodal retrieval; SOC 2/HIPAA-ready | [Atlan](https://atlan.com/know/enterprise-rag-platforms-comparison/) |
| Vector database | **Vespa** | Enterprise-scale retrieval for billion-document corpora, native ML ranking, Apache 2.0 | [Atlan](https://atlan.com/know/enterprise-rag-platforms-comparison/) |
| Vector database / search | **Meilisearch** | Developer-focused open-source search, sub-50ms latency, adding a unified AI gateway in 2026 | [Atlan](https://atlan.com/know/enterprise-rag-platforms-comparison/) |

---

## 3. Market sizing

**No Gartner or IDC market-sizing figure specifically for "RAG" or "agentic RAG" was
found in this pass** - see COULD NOT CONFIRM. The estimates below are all from named
commercial market-research providers, presented as a range because methodology and
category definition vary between them (this is a genuinely new, loosely-bounded category
- treat convergence, not any single figure, as the signal).

| Provider | Category scope | Base year value | Forecast year value | CAGR | Date checked |
|---|---|---|---|---|---|
| MarketsAndMarkets | "RAG market" | US$1.94bn (2025) | US$9.86bn (2030) | 38.4% (2025-2030) | 2026-08-06 |
| Precedence Research | "RAG market" | US$1.85bn (2025) | US$67.42bn (2034) | 49.12% (2025-2034) | 2026-08-06 |
| Market.us | "Agentic RAG market" (narrower, agentic-specific) | US$3.8bn (2024) | US$165.0bn (2034) | 45.8% (2025-2034) | 2026-08-06 |

Sources: [MarketsAndMarkets](https://www.marketsandmarkets.com/PressReleases/retrieval-augmented-generation-rag.asp); [Precedence Research](https://www.precedenceresearch.com/retrieval-augmented-generation-market); [Market.us](https://market.us/report/agentic-retrieval-augmented-generation-market/).

**Reading this range:** the roughly 4x spread in the 2030-ish forecast values (Precedence
vs MarketsAndMarkets) reflects different scope definitions (some studies bundle in
adjacent vector-DB and MLOps tooling spend, others don't) rather than one estimate being
wrong - flag this spread rather than picking one figure to quote as if it were settled.
**Never present a single one of these numbers on a slide without the range and the named
provider** (hard rule 4). Two further named providers (Grand View Research, Mordor
Intelligence) also publish RAG market forecasts to 2030 but their exact figures were not
captured in this pass - pull before using either as a source.

---

## 4. Regulatory and buying-urgency signals

Dated, sourced facts that create buying urgency for grounded, governable,
residency-controlled AI - for sales-enablement objection handling and account-analyst
account framing. Not tied to a single competitor; cite alongside the relevant competitor
row when the conversation calls for it.

### Regulatory and compliance

- **Germany: chatbot operators held liable for AI hallucinations.** The Oberlandesgericht
  Hamm (Hamm Higher Regional Court) ruled, judgment of 12 May 2026, case 4 UKl 3/25, that a
  medical company is liable for its own chatbot's fabricated claims about physician
  qualifications - the ruling confirms an operator is responsible for what its AI says on its
  behalf, hallucination or not. Corroborated by three independent German legal-media outlets
  reporting the same court, date and facts: Legal Tribune Online (12 May 2026) and Anwalt.de
  (16 May 2026, the outlet citing the case number directly) at the time of judgment, and FAZ
  (16 Sep 2026) in a later follow-up. [Library of Congress, Global Legal Monitor, 9 Jun
  2026](https://www.loc.gov/item/global-legal-monitor/2026-06-09/germany-court-rules-chatbot-operators-are-liable-for-ai-hallucinations/)
  (this link 403s to automated fetch as at 2026-10-01; verify it resolves in a browser before
  citing it on a slide). Outlet coverage verified via [Google News
  aggregation, accessed 2026-10-01](https://news.google.com/rss/search?q=%22OLG%20Hamm%22%20Chatbot%20Haftung&hl=de&gl=DE&ceid=DE:de)
  - the publishers' own pages blocked automated fetch, so this aggregator result is the
  verifiable record; read the original outlets directly before using this as a sole citation
  on a customer-facing artifact.
- **FINRA's 2026 Regulatory Oversight Report adds a dedicated AI/GenAI risk section for the
  first time**, explicitly flagging hallucination risk for broker-dealers and calling for
  human-in-the-loop controls and hallucination-specific safeguards. [FINRA, 9 Dec
  2025](https://www.finra.org/media-center/newsreleases/2025/finra-publishes-2026-regulatory-oversight-report-empower-member-firm)
- **Australia: PM Albanese announced (15 Jul 2026) the government will legislate mandatory
  national AI standards**, targeting National Cabinet agreement in August 2026 and
  legislation in early 2027. Currently scoped to large data centres (power/water use) and
  creative-copyright in model training, not yet a broad AI-governance statute - real
  momentum, not yet in force; don't overstate it as an existing law. [Tech Xplore/AFP, Jul
  2026](https://techxplore.com/news/2026-07-australian-pm-laws-ai.html)
- **US state AI law patchwork - mixed status; Colorado is NOT in effect, correcting an
  earlier version of this entry.** Status per state as at 2026-10-01:
  - **Texas** (Responsible AI Governance Act / TRAIGA) - in force since 1 Jan 2026.
  - **Illinois** (HB 3773, AI use in employment decisions) - in force since 1 Jan 2026.
  - **California** - multiple AI-specific statutes (incl. the AI Transparency Act and the AI
    Training Data Transparency Law) in force since Jan 2026; a patchwork of several laws,
    not one single statute.
  - **Utah** (AI Policy Act, SB 149) - in force since 1 May 2024, predating this group; not
    newly effective in this cycle.
  - **Colorado - NOT in force.** Its original AI Act (SB 24-205) never took effect: the US
    District Court for the District of Colorado issued a stipulated order on 27 Apr 2026
    blocking its enforcement, sought by xAI (joined by the US Department of Justice) in a
    constitutional challenge. Governor Jared Polis then signed a narrower replacement, SB
    26-189, on 14 May 2026 - effective **1 Jan 2027**, so it is not yet in force. Do not cite
    Colorado's original anti-discrimination/impact-assessment obligations as current law.

  Separately, a December 2025 executive order seeks a uniform federal framework that would
  preempt inconsistent state laws; courts have not resolved that broader conflict. "Build for
  the strictest state law now" remains the defensible position for US enterprise accounts
  while this is unsettled. [McDermott Will & Schulte, 29 May
  2026](https://www.mcdermottlaw.com/insights/colorado-ai-law-in-flux-comprehensive-replacement-bill-signed-after-federal-court-blocks-predecessors-enforcement/);
  [Colorado General Assembly, SB26-189 bill page, verified 2026-10-01](https://leg.colorado.gov/bills/sb26-189);
  [King & Spalding LLP, Dec 2025/Jan
  2026](https://www.kslaw.com/news-and-insights/new-state-ai-laws-are-effective-on-january-1-2026-but-a-new-executive-order-signals-disruption)
  (original source for the Texas/Illinois/California/Utah dates above; pre-dates the Colorado
  court block, so no longer cite it for Colorado's status).

### Cautionary tales (cost of ungrounded AI)

- **Deloitte refunded the Australian government over $60,000 (roughly A$97,000) of a
  ~A$440,000 contract** after a report it produced using Azure OpenAI was found to contain
  fabricated citations and non-existent academic references attributed to real universities.
  One of the cleanest available examples of ungrounded AI costing money and reputation at
  government level in Australia. [CFO Dive, 7 Oct
  2025](https://www.cfodive.com/news/deloitte-refunds-60k-report-ai-errors-australian-government-accounting/803321/)
- **First US attorney licence suspension tied to AI-hallucinated citations.** The Nebraska
  Supreme Court suspended an Omaha attorney (16 Apr 2026) after a court brief was found to
  contain 57 of 63 defective citations, 20 fabricated outright; the attorney denied using AI
  before later admitting it. Escalates the cautionary-tale stakes from a fine to professional
  survival - strong for legal and professional-services accounts. [WOWT (NBC Omaha), 16 Apr
  2026](https://www.wowt.com/2026/04/16/nebraska-supreme-court-suspends-omaha-attorney-over-ai-use/)

### Sovereign AI momentum

- **Microsoft committed A$25bn (roughly US$18bn) through 2029** to Australian AI/cloud
  infrastructure, cybersecurity and workforce skilling, signed via a government memorandum
  of understanding - evidence the sovereign/local AI infrastructure build-out in Australia is
  accelerating. Use as market-momentum context for ARAG's residency-controlled positioning,
  not as an ARAG proof point in itself. [CNBC, 23 Apr
  2026](https://www.cnbc.com/2026/04/23/microsoft-expands-ai-footprint-in-australia-with-18-billion-investment.html)

---

## 5. COULD NOT CONFIRM

- ARAG/Nuclia's placement (or absence) in any named Gartner Magic Quadrant, Gartner Peer
  Insights Insight Engines ranking, Forrester Wave, or IDC MarketScape - not checked
  directly against Gartner/Forrester/IDC's own sites this pass, only inferred from third-
  party market roundups that didn't name ARAG/Nuclia either way.
- Exact figures from Grand View Research's and Mordor Intelligence's RAG market forecasts
  (titles found, figures not extracted).
- SphereIQ's claims are sourced only from its own site/self-description via a market
  roundup - not independently verified; weight accordingly, don't cite as third-party
  proof.
- Current ARR/revenue, headcount or funding figures for any competitor listed - none were
  pulled this pass; needed before any "we're bigger/smaller than X" claim.
- Whether Moveworks, Lucidworks, Atolio, Perplexity Enterprise, or Kore.ai belong in Tier
  A or B - each appeared in passing in source roundups but wasn't deep-researched this
  pass; candidates for the next refresh, not yet full rows.

---

## 6. Per-competitor teardown template (for future expansion)

Use this structure when a competitor graduates from a tier-table row to a full teardown
(e.g. when sales-enablement needs a battle card against a specific named competitor in an
active deal).

```
### <Competitor name>

- **Category / tier:** <A/B/C/D per above>
- **What they are:** <one paragraph>
- **Pricing signal:** <cited, dated>
- **Strengths (their own proof points):** <cited>
- **Gaps (independently evidenced, not assumed):** <cited>
- **Where ARAG wins:** <only claims KB-verified per hard rule 3, cited to KB source>
- **Where ARAG loses / must acknowledge:** <honest, cited>
- **Proof they publish:** <case studies, benchmarks, analyst mentions - cited>
- **Sources:** <full list, dated>
```

---

## Change log

- **2026-08-08** - News-sweep refresh (12 sourced items folded in, all verified public
  articles, none overlapping items already published to the DAM news feed as separate
  stories). Added a new section 4, "Regulatory and buying-urgency signals" (regulatory/
  compliance, cautionary tales, sovereign AI momentum - Germany hallucination-liability
  ruling, FINRA's 2026 AI risk section, Australia's announced AI-standards legislation, the
  US state-law patchwork post federal preemption attempt, Deloitte's Australian government
  refund, and the first US attorney licence suspension over AI-hallucinated citations).
  Updated four Tier rows with business-move news: AWS Bedrock KB + Q Business (Kendra/Q
  Business/Bedrock Agents moved to maintenance mode, a genuine incumbent migration-urgency
  trigger); Google Gemini Enterprise (confirmed Vertex AI's standalone line is retired, and
  that Google's own differentiator framing is governance, not grounding quality); Writer
  (launched autonomous, event-triggered agents - an objection-handling angle on ungrounded
  autonomous action); Glean (independent reporting frames its real strategy as an
  infrastructure "context layer" under every AI tool, not just a search app). Added a
  category clarification to the Algolia row: its 2026 Gartner Magic Quadrant leadership is
  in Search and Product Discovery (commerce/site search), not enterprise-knowledge or
  agentic RAG - don't let "Gartner Leader" read as equivalent proof in that context.
  Strengthened the confidence caveats on both SphereIQ and AI12z: a targeted search for
  independent press coverage (Reuters, Bloomberg, TechCrunch, VentureBeat, The Register,
  CIO-tier outlets) found none for either - all available characterisation of both vendors
  traces back to their own marketing content or self-submitted wire releases, not
  independent journalism. This is a caveat on source basis, not a claim either vendor is
  failing. Renumbered sections 4 and 5 to 5 and 6 to make room for the new section 4.
  Flagged by market-analyst, folding in a news-sweep the lead ran in parallel.
- **2026-08-06** - Added AI12z as a new Tier A row (sales-enablement, researched from
  scratch while building the AI12z battle card - no prior dossier entry existed). Confirmed
  AI12z is a real, currently operating company via multiple independent CMS/DXP partner
  listings (RWS, Sitecore, Contentstack, Magnolia), not just self-description - but it is a
  narrower, website/CMS-scoped AI-agent product, not a general-purpose enterprise RAG
  platform; flagged explicitly so the row isn't misread as apples-to-apples with the rest of
  Tier A. No analyst coverage, named customer or funding figure found. Full teardown in
  `content/enablement/battlecards/ai12z-battlecard.md`.
- **2026-08-06** - Correction: Cohere (North)'s Tier A row had a stale, imprecise HIPAA
  claim ("roadmap only, not shipped") sourced from a third-party roundup. Checked
  against Cohere's own Trust Center (primary source): no standing HIPAA certification or
  BAA on the hosted North/SaaS product - the BAA is scoped only to custom
  model-development engagements. Also split the combined "Canadian/UK sovereign posture"
  claim - Canada is strongly evidenced (named live infrastructure partnerships: Bell/BCE,
  SAP Canada), UK is commercial-presence-and-certification only (UK Cyber Essentials, no
  confirmed named UK sovereign-cloud region). Added ISO 42001 (AI management system) to
  Cohere's known certifications, and named Rerank 4's dedicated-instance pricing as
  primary-sourced. Flagged by sales-enablement while building the Cohere (North)
  battlecard.
- **2026-08-06** - Correction: Vectara's Tier A row had a stale "no BYO-LLM" gap claim.
  Vectara supports bring-your-own-LLM (OpenAI-compatible incl. Claude and Azure OpenAI,
  plus Google Vertex/Gemini and the Responses API for o1/o3), confirmed against
  docs.vectara.com. Added `vectara-mcp` and `vectara-agentic` (MCP server + agent
  library) and corrected compliance framing: SOC-2 Type II and HIPAA are Vectara's own
  certifications; ISO 27001 belongs to its cloud host (AWS/GCP), not Vectara directly.
  Flagged by sales-enablement while building the Vectara battlecard.
- **2026-08-06** - Initial build. Four-tier competitor list (direct RAG-as-a-service,
  enterprise search/insight engines, cloud hyperscaler native, DIY stack), market-sizing
  table from three named providers, category-framing note (no dedicated Gartner MQ/IDC
  MarketScape found for this category yet), COULD NOT CONFIRM list. No per-competitor
  teardowns yet - next pass should pick the two or three competitors most likely to show
  up in live deals (based on account-analyst's account work) and take them to full
  teardown depth.
