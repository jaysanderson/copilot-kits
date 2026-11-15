# BRIEF: TruthBench (day 9 of the series)

> "The AI pilot demoed beautifully and we have no way to know whether it's making things up in production."

**Who shares this.** CIO, risk, the sponsor who signed.

**Promise.** Paste ten questions. See which answers your knowledge base can actually back up, before a customer finds out.

**The one job.** Paste up to 25 questions. For each: the answer, a groundedness score, how many sources were cited, and whether retrieval alone agrees with the answer. Weak rows expand to show the passages. Export CSV.

**Why ARAG is load-bearing.** `/predict/remi` groundedness against the full retrieved context (`groundedness` in `arag.py`; enterprise KBs), `contexts_from_ask`, and a `/find` versus `/ask` agreement check. Remove ARAG and this is a spreadsheet of vibes.

**Base.** The chassis (`CHASSIS.md`): `app.py`, `arag.py`, `static/`, `product.json`. Add product routes under `# --- product routes` in `app.py` and a panel in `static/`. Nothing in the chassis is rewritten.

**Knowledge Box.** Any existing enterprise KB (REMi). Reader token.

**Finishing steps, in order (one Copilot chat each).**
1. Route: `/api/bench` takes `questions[]` (cap 25); per question call `grounded_answer`, then `arag.find`; compute `remi`, `cited`, `overlap` (share of cited rids also in the top find results). Save the run to `data/runs/<timestamp>.json`.
2. UI: a textarea above the ask bar, a results table with the badge per row, expandable passages, and a Download CSV button.
3. Selftest: a deliberately unanswerable question must come back withheld or low; a check that cannot fail is a FAIL (`reference/demo_qa_gate.py` shows the pattern).
4. Cost line: print questions x 3 calls before running.

**Done when** (these lines are section 0 of `STANDARD.md`; every (B) line there must also be done):
- Ten questions scored in one run; one unanswerable question flagged.
- CSV downloads with question, answer, remi, cited, overlap.
- Runs persist in `data/runs/` and reload on the page.
- 390 px render clean.

**Deliberately not built (the article's "where to take it next").**
- Regression history: diff two runs
- CI gate: non-zero exit when a score drops
- Generate the question set from the KB itself

**Copilot prompts.** `/finish-starter` for each step above, `/qa-gate` at the end, `/write-article` last. Cheapest model for renames and copy; the premium model only for the step marked hardest in `README.md`.

**Token rule.** Copy from `reference/` and the chassis; never generate a client, a renderer or a Dockerfile. If a step needs a mechanism not confirmed in `.github/instructions/arag-api.instructions.md` or `reference/arag-platform-quirks.md`, stop and flag it; do not invent an endpoint.
