# Publisher Mutual Claims Desk

A Progress Agentic RAG demo: a general insurer's **claims-handling workbench**. The product
being sold is Progress Agentic RAG; the insurance claims desk is the vehicle. Publisher Mutual
is a fictional Australian general insurer (home, motor, small commercial property) and every
claim, claimant, policy, document and figure is synthetic.

- **Live:** https://your-app.fly.dev
- **KB:** `bc0ea9ff-561b-49df-82e1-49bfd0828a8c`, account **progress-jay-geo**
  (`86d1adc8-64ef-499b-86d6-72e9fd684ab0`), zone `<zone>` (AU sandbox).
- **Personas:** CIO (primary - defensible, trust-scored decisions; data in your own
  environment) and Solutions Architect (secondary - the architecture reveal, the RBAC-carried
  agent-over-MCP, the honest disclosed gap).

## The layout

A queue + reading-room workbench, deliberately its own shape (not the sibling demos'):
a navy **module rail** on the left (the product's own nav), a bright **claims queue** pane on
the claim-scoped routes, and the **reading room** where the selected claim is worked. On a
phone the rail becomes a bottom tab bar and the queue a full-screen drawer. The Progress
Agentic RAG header frames it; the body carries the Progress brand throughout.

## The eight use cases (each on its own route)

1. **Claim Intake** (`/intake`) - ARAG reads the claim's own First Notice of Loss and policy
   schedule into structured, typed intake fields via the query-time `answer_json_schema` path,
   scoped to that claim's documents. Real generative UI, grounded in the paperwork.
2. **Coverage Q&A** (`/coverage`) - a grounded, cited answer from the actual policy wording;
   every citation opens the source document. REMi-scored live.
3. **Coverage Decision** (`/decision`) - payable / not-payable / needs-more-info with cited
   reasons AND a live REMi trust score.
4. **Exception Check** (`/exceptions`) - cross-checks the claim against its schedule and
   Publisher's integrity-indicators reference; cites each inconsistency (date-of-loss mismatch,
   premium in arrears at loss, over-sub-limit item).
5. **Portfolio** (`/reports`) - claim volumes, cycle time, status mix and peril breakdown as
   charts, computed live from a clearly-labelled synthetic portfolio of 52 claims.
6. **Claims Copilot** (`/copilot`) - the app exposes its live systems (policy master, claimant
   history, claim record) as MCP tools for ARAG's own Retrieval Agent. **The agent is a
   disclosed gap** in this build (see below); the app honestly declines rather than fake it.
7. **Underwriting Risk Summary** (`/underwriting`) - ARAG reads a new-business application's own
   submitted form, an independent inspection report and Publisher's risk-data feed summary
   together, via the same query-time `answer_json_schema` path as Claim Intake, and synthesises
   a typed risk rating, the specific risk factors and a recommended underwriting action - scoped
   to that application's own documents, never guessed from the product line alone.
8. **Broker Copilot** (`/broker-copilot`) - natural-language Q&A for the broker channel, scoped
   via a `doc_type` filter to Publisher's broker product sheets, rate card and compliance
   bulletins only - never a claim file or underwriting application. Cited and REMi-scored, same
   discipline as Coverage Q&A.

Plus a **friendly, on-brand refusal** on out-of-scope questions, delivered through the KB's own
ASK search configuration (`publisher-friendly-refusal`), not a hardcoded string.

## How to demo (the guided tour walks this)

1. Open on **Claims Desk** - the whole book of work on one screen; the flood claim
   CLM-2026-0501 is waiting on a decision.
2. **Claim Intake** on that claim -> ARAG reads the paperwork into structured fields.
3. **Coverage Q&A**: "Is riverine flood damage covered under this Home & Contents policy?" ->
   cited answer that opens the PDS clause.
4. **Coverage Decision** on the flood claim -> not payable, cited to the schedule's unselected
   flood option, REMi-scored.
5. **Exception Check** on the theft claim CLM-2026-0466 -> date-of-loss and arrears exceptions.
6. **Portfolio** -> the charts.
7. **Claims Copilot** -> the honest disclosed-gap state, and open **How this works** to see the
   real `/mcp` tools it exposes.
8. **Underwriting Risk Summary** on the Cheng bushfire application (UW-2026-1214) -> High risk,
   accept with conditions, cited to the application, inspection and risk-data documents.
9. **Broker Copilot**: "Is flood cover included by default under TideProtect Home and Contents?"
   -> cited answer that opens the broker product sheet.

Open **How this works** (top-right, every route) for that route's real request/data flow.

## The ARAG mechanisms (all real, verifiable in the admin console)

- `POST /ask` (cited, streamed) with the `neighbouring_paragraphs` grounding strategy.
- `POST /ask` with `answer_json_schema` (query-time structured JSON) for intake extraction and
  the underwriting risk summary.
- `POST /ask` (cited) with a `doc_type` `filter_expression` scoping the Broker Copilot away from
  claim files and underwriting applications.
- `POST /predict/remi` (RAG-triad trust score, KB service-account token, scored against the
  full retrieved context - stable 5/5 on a well-grounded answer).
- `POST /catalog` (faceted, `filter_expression`) and `GET /counters` for live counts.
- Search configurations on the KB: `publisher-friendly-refusal` (ASK), `grounded-hybrid`,
  `semantic-broad`, `keyword-precise`.
- `POST /mcp` on the app (get_policy_status, get_claimant_history, get_claim) - the tool source
  ARAG's Retrieval Agent would call.

**Honest disclosed gap (Copilot):** wiring ARAG's own Retrieval Agent to the app's `/mcp`
needs an agent Personal Access Token, and minting one requires an ARAG dashboard login this
factory does not perform (a standing credential constraint). Rather than substitute a homegrown
planner - which the rules forbid - the Copilot shows a visible "RAO not configured" state and
the reveal names the gap. The `/mcp` server itself is real and verified live.

## 30-second reset

- **Answer/decision log** (Desk activity, Portfolio) - "Reset desk" in the rail restores the
  seeded baseline (in-browser).
- **Knowledge Box** - `node scripts/provision.mjs --purge` deletes every resource; re-seed with
  `set -a && . ./.env && set +a && node scripts/ingest.mjs --corpus data/corpus --labelsets
  doc_type,product_line,claim_number,claimant,peril,claim_status,application_number,applicant
  --force`.

## Build / run

Server-side ARAG token only (`.env`, gitignored; on Fly as secrets). `UI_MODE=opensource`
(Radix + Recharts + Tailwind, no Kendo).

```
cd portal && npm ci && npm run build && npm start   # serves API + built SPA on :4000
# dev: npm run dev
```
