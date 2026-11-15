# One-pager brief - "The RAG Maintenance Treadmill"

**Purpose:** field-usable leave-behind / email attachment for TOFU conversations - the
category argument, not a product pitch. Light ARAG mention in the footer only. Designed
as a **brief** (copy + described layout) for the design pass; not yet built as a final
.docx/PDF artefact.

**Audience:** CIO / architect / engineering lead evaluating build-vs-buy on retrieval.

**Format:** single page, portrait, Progress brand palette and Progress Sans typography
per the `progress-arag-branding` skill. No screenshots, no product UI - this is a concept
page, not a demo proof point.

---

## Layout description

**Header band** (top ~15% of page, full-width, dark background per brand palette)
- Small Progress wordmark, top-left, modest scale (not dominant - this is category
  content, not a product sheet).
- Headline, large, set in two lines for rhythm:
  **"Building RAG takes a weekend."**
  **"Maintaining it takes a team."**
- Small kicker line under the headline, lighter weight: "What actually happens after the demo ships."

**Hero visual** (centre third of page, the dominant graphic element)
- A circular "treadmill" motif: a ring of 10 labelled nodes running clockwise around a
  centre point, connected by a continuous looping arrow (never-ending, not a linear
  process - the visual point is that this list has no finish line).
- Node labels, in order around the ring: **Connectors -> Ingestion & parsing -> Chunking
  & indexing -> Retrieval -> Reranking -> Evaluation -> Monitoring -> Security &
  permissions -> Governance -> Scaling**, then looping back to Connectors, with a
  thirteenth callout node sitting slightly outside the ring labelled **"Model upgrades
  reset half of this"** connected by a dotted line (it doesn't fit neatly in the loop -
  visually treat it as the disruptor, not part of the steady rotation).
- Centre of the ring: short label in bold, "No finish line."

**Left column, below hero** (roughly 55% width) - "The cost of doing it yourself"
- Short intro line: "None of this shows up in the demo. All of it shows up on the
  on-call roster twelve months later."
- Bulleted list (concise, one line each):
  - Every connector needs to keep working as source systems change
  - Parsing has to survive scans, spreadsheets, slides and video, not just clean text
  - Chunking and indexing decisions quietly decide what's even retrievable
  - Retrieval and reranking need constant tuning against real queries
  - Quality drift is silent until a customer notices it first
  - Permissions and governance have to hold as the system scales
  - Every model upgrade is a small re-architecture

**Right column, below hero** (roughly 45% width, visually distinct panel - lighter
background block) - "What measurable trust looks like"
- Short intro line: "You cannot improve what you cannot measure."
- Three compact metric cards stacked vertically, each with an icon placeholder, a label
  and a one-line description:
  1. **Groundedness** - is the answer actually supported by the source material
  2. **Context relevance** - did retrieval find the right material in the first place
  3. **Answer relevance** - does the answer address what was actually asked
- Small caption under the three cards: "Scored per query, not sampled monthly - so a
  quality drop is a number you act on, not a complaint you hear about later."

**Footer band** (bottom ~12% of page, full-width, light background)
- One line, restrained, no hard sell: "Progress Agentic RAG treats ingestion-to-answer as
  one governed platform, with quality measurement built in and deployment anywhere your
  data has to live - cloud, hybrid, or fully on-premises."
- Small call-to-action, right-aligned: "Ask to see quality measured, live." with a field
  contact / QR code placeholder (populate per rep, not hardcoded).
- Fine print, smallest type, left-aligned: category context line, e.g. "A perspective on
  agentic RAG from Progress Software" - keeps the page honest about being POV content,
  not a spec sheet.

---

## Copy blocks (verbatim, ready to place)

**Headline:** Building RAG takes a weekend. Maintaining it takes a team.

**Kicker:** What actually happens after the demo ships.

**Ring centre label:** No finish line.

**Left column intro:** None of this shows up in the demo. All of it shows up on the
on-call roster twelve months later.

**Left column bullets:**
- Every connector needs to keep working as source systems change
- Parsing has to survive scans, spreadsheets, slides and video, not just clean text
- Chunking and indexing decisions quietly decide what's even retrievable
- Retrieval and reranking need constant tuning against real queries
- Quality drift is silent until a customer notices it first
- Permissions and governance have to hold as the system scales
- Every model upgrade is a small re-architecture

**Right column intro:** You cannot improve what you cannot measure.

**Metric card 1:** Groundedness - is the answer actually supported by the source material.

**Metric card 2:** Context relevance - did retrieval find the right material in the first place.

**Metric card 3:** Answer relevance - does the answer address what was actually asked.

**Right column caption:** Scored per query, not sampled monthly - so a quality drop is a
number you act on, not a complaint you hear about later.

**Footer line:** Progress Agentic RAG treats ingestion-to-answer as one governed platform,
with quality measurement built in and deployment anywhere your data has to live - cloud,
hybrid, or fully on-premises.

**Footer CTA:** Ask to see quality measured, live.

**Fine print:** A perspective on agentic RAG from Progress Software.

---

## Notes for the build pass

- Ten-node ring count matches the article's list minus the two-item merges (ingestion +
  parsing combined, security + permissions combined) so the visual reads clean at one-page
  scale - don't try to fit all twelve granular items from the article as separate nodes.
- The three REMi metric labels (groundedness, context relevance, answer relevance) are
  KB-verified against the `nuclia-mcp` rag-quality documentation - do not rename or
  reorder them in the final build.
- Keep the footer ARAG mention to the one line specified. This is a TOFU asset; a heavier
  product pitch here would break the category-authority framing the whole page is built on.
- No em dashes anywhere in this piece (not `jay`-voice content) - spaced hyphens only,
  already applied throughout.
