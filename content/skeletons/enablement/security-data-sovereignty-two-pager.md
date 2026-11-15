# Progress Agentic RAG - Security and Data Sovereignty

**For:** CIOs and security/architecture reviewers evaluating Progress Agentic RAG (ARAG).
**Purpose:** how ARAG actually handles deployment, data residency, isolation, access
control and audit - so a security review starts from the real architecture, not a sales
claim. **Grounding:** every mechanism below is verified against Nuclia's own published
documentation (`nuclia-mcp` knowledge base); section 8 states plainly where this document
draws an honest line. **Date:** 5 September 2026.

---

## 1. Deployment modes - choose where your data and models run

ARAG is not a single-cloud service. Three deployment modes exist:

- **Cloud** - Nuclia's managed infrastructure, hosted in the EU or US. Nuclia handles
  processing, storage, ingestion and answer generation; you configure search, generative
  behaviour and UI.
- **Hybrid** - processing runs in Nuclia's cloud, but the resulting knowledge base
  (NucliaDB) is stored on your own infrastructure. Useful where processing effort should
  stay managed but the data itself must not leave your environment at rest.
- **Full on-premises** - the entire pipeline runs inside your own infrastructure,
  including NucliaDB and the generative model itself. This is the mode for strict
  data-residency requirements, regulated industries and genuinely air-gapped
  environments with no outbound connectivity.

Choose the mode by requirement, not by default: a public-facing product can run cloud; a
regulated internal knowledge base can run hybrid; an air-gapped estate can run fully
on-premises, model included.

## 2. Data flow, ingestion to answer

1. **Ingestion** - a document, recording, image or structured record is submitted to a
   Knowledge Box. Extraction (OCR, transcription, structured parsing) and optional
   enrichment (labelling, summarisation, knowledge-graph extraction) run at this stage.
2. **Indexing** - extracted content is chunked and indexed for retrieval (vector and
   full-text) inside NucliaDB.
3. **Retrieval** - a query, direct or from a Retrieval Agent, searches the index and
   returns the passages that ground the answer.
4. **Generation** - the configured generative model composes an answer from the retrieved
   passages only, with citations back to source.
5. **Scoring (optional)** - REMi can score the answer for groundedness, context relevance
   and answer relevance before it is shown or logged.

Every step above happens inside the deployment mode you have chosen - there is no
implicit round-trip to a different region or a different vendor's infrastructure
mid-flow.

## 3. Where data rests versus where it is processed

| Mode | Data at rest | Processing (extraction, indexing, generation) |
|---|---|---|
| Cloud | Nuclia infrastructure (EU or US) | Nuclia infrastructure (same region) |
| Hybrid | Your infrastructure (NucliaDB) | Nuclia's cloud pipeline |
| Full on-premises | Your infrastructure | Your infrastructure, including the generative model |

## 4. Tenant and Knowledge Box isolation

Every Knowledge Box is an isolated container - resources in one Knowledge Box are not
visible to a query against another. This is the isolation boundary the platform actually
enforces, and the one we recommend building on: **provision a separate Knowledge Box for
every audience, customer or confidentiality tier that must never see another's content.**
Nuclia states a strict no-data-usage policy for training its own models on customer
content.

A Knowledge Box does **not** provide granular, per-document access control inside
itself: content within one Knowledge Box is visible to any party authorised to query
that box. Use separate Knowledge Boxes as the real security boundary; treat in-box
filtering as a convenience for organising content, never as an access-control mechanism
for anything that must not leak.

## 5. Permission-scoped retrieval (the Retrieval Agent pattern)

Where ARAG acts as an agent over your own application - calling your application's own
tools rather than a generic connector - it forwards the calling user's own authorisation
token with every call. Your application's existing permission model, not a parallel
system inside ARAG, decides what that agent may retrieve or do. Retrieval never gains
more access than the user already has in your system. This is the pattern behind every
reference agent integration this team has built.

## 6. Integration pattern - keep API keys server-side

ARAG credentials are never appropriate in client-side code. The standard integration
pattern routes every call through your own server-side proxy, which holds the API key
and forwards only the request and response the browser needs. This is a build
discipline on your side, not a feature of ARAG itself, and it is the pattern behind
every reference integration.

## 7. Audit and observability

Every Knowledge Box maintains activity logs covering resource processing, edits,
searches, questions asked and answers generated - each entry timestamped and attributed
to the user who triggered it. Logs are queryable via API and downloadable as monthly
audit files, and activity metrics (search and ask volume) are available by hour, day,
week, month, quarter or year.

## 8. What we do not claim

- **Certifications are vendor-stated, not independently audited by us.** Progress/Nuclia
  states ISO 27001 and SOC 2 Type 2 on its own security page. Confirm current
  certification status and scope directly before citing it in a regulated procurement
  process; do not assume a specific compliance framework (for example FedRAMP, HIPAA, or
  a government-specific accreditation) unless a current, named document confirms it.
- **No published accuracy percentage.** Answer quality is proven live, per query, with
  REMi and a cited answer - never a headline number.
- **No granular in-Knowledge-Box access control.** See section 4: the isolation
  boundary is the Knowledge Box, not a permission layer inside one.
- **The server-side proxy is your responsibility to build.** ARAG does not enforce this
  for you; an integration that skips it is a self-inflicted exposure, not a platform gap.

Certification status, current identity/SSO integration options and region availability
change - confirm the current state with your Progress contact before a procurement
deadline depends on it.
