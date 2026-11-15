# BRIEF: TriageDesk (day 5 of the series)

> "Two hundred applications a week, each read by a person, each decided slightly differently, nobody can explain why."

**Who shares this.** Operations manager, service delivery lead.

**Promise.** Every case read the same way: a decision, a confidence and the evidence, in seconds, with a human in charge.

**The one job.** Submit a case (form fields or a PDF). The pipeline returns a structured decision (outcome, confidence, reasons, evidence) as JSON and as a card, and a dashboard lists every decision.

**Why ARAG is load-bearing.** `answer_json_schema` on `/ask` for schema-constrained decisions, with the instructions carried in the schema's property descriptions (a system prompt is ignored beside a schema) and provenance from `retrieval_results`; `filter_expression` scopes each case to the policy documents. All of it already runs in `app/pipeline.py` and `app/arag_client.py`. Remove ARAG and this is free text someone re-keys.

**Base.** The app is the finished triage demo, copied whole. It is already a product: pipeline, SQLite store, dashboard, PDF split, structured decisions with retries. Nothing that already works is rewritten.

**Knowledge Box.** New KB from `seed/`; the seed scripts provision it. Account-level key needed once to create the KB (see `.env.example`).

**Finishing steps, in order (one Copilot chat each).**
1. Identity purge: `grep -rniE "akadem|degree|credential|university" .` and decide per hit: product copy becomes generic (case, policy, decision); domain modules (`codes.py`, `transliteration.py`, `legibility.py`) stay but are driven by `data/case_types.json`.
2. Seed: replace `seed/corpus/` with a generic policy set (eligibility rules, a fee schedule, a service standard) and re-run `seed/provision_kb.py` and `seed/seed.py`.
3. Keep the pipeline, the store and the dashboard. Rename routes only where the degree domain leaks into URLs.
4. Brand from `brand/`; footer disclosure that the policy set is synthetic.

**Done when** (these lines are section 0 of `STANDARD.md`; every (B) line there must also be done):
- Five cases submitted (two as PDF) return a decision, a confidence and cited evidence.
- The dashboard lists them; one case shows a schema-validation retry in the log.
- No degree-specific copy remains outside `data/case_types.json`.
- 390 px render clean.

**Deliberately not built (the article's "where to take it next").**
- A review queue with SLA timers
- An override log with the reviewer's reason
- Batch upload of a day's cases

**Copilot prompts.** `/finish-starter` for each step above, `/qa-gate` at the end, `/write-article` last. Cheapest model for renames and copy; the premium model only for the step marked hardest in `README.md`.

**Token rule.** Copy from `reference/` and the chassis; never generate a client, a renderer or a Dockerfile. If a step needs a mechanism not confirmed in `.github/instructions/arag-api.instructions.md` or `reference/arag-platform-quirks.md`, stop and flag it; do not invent an endpoint.
