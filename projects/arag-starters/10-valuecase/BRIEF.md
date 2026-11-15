# BRIEF: ValueCase (day 10 of the series)

> "We built a business case for AI from guesses. The prospect's own documents held the real numbers and nobody looked."

**Who shares this.** CFO, sales leader, value engineer.

**Promise.** A business case where every number came from the prospect's own documents, with the citation to prove it.

**The one job.** The existing value-case tool (levers, scenarios, provenance, sensitivity, exports) plus a Propose from documents step: point at a Knowledge Box of the prospect's documents and every lever input arrives with a proposed value and a citation; you accept or edit.

**Why ARAG is load-bearing.** `ask_structured` with a per-lever schema (`value`, `unit`, `source_title` as an enum of the retrieved titles, `quote`), scoped to the prospect's KB; the claim-check route in `reference/clinic-app.py` (lines 1002 to 1074) is the pattern for checking a figure against documents. Remove ARAG and this is a calculator.

**Base.** The app is the finished value-case tool, copied whole (FastAPI, SQLite, exports, scenarios, sensitivity). It has no ARAG client yet; that is the finishing touch. Nothing that already works is rewritten.

**Knowledge Box.** New KB with three public documents about a fictional prospect. Reader token after seeding.

**Finishing steps, in order (one Copilot chat each).**
1. Client: copy `reference/arag.py` into the app root and add `ARAG_HOST`, `KB_ID`, `KB_TOKEN`, `ARAG_MODEL` to `.env.example` (blank values).
2. Route: `/api/propose` iterates `levers.py`; one `ask_structured` call per lever; returns value, unit, quote, source title. Provenance source type becomes `document`.
3. UI: a Propose from documents button on the inputs view (`static/js/levers-view.js`); each proposed input shows a citation chip with the quote.
4. Rename to the product; keep the passphrase gate (`auth.py`) and the SQLite store.
5. Seed a KB with three public documents for a fictional prospect (annual report extract, a press release, a job ad).

**Done when** (these lines are section 0 of `STANDARD.md`; every (B) line there must also be done):
- Five levers proposed with citations from a three-document KB; two edited by hand and saved.
- A case saved, closed and reopened at its URL with provenance intact.
- The passphrase gate still works; secrets only in `.env`.
- 390 px render clean.

**Deliberately not built (the article's "where to take it next").**
- Portfolio view across prospects
- Export the case to a slide deck
- Re-propose when the documents change

**Copilot prompts.** `/finish-starter` for each step above, `/qa-gate` at the end, `/write-article` last. Cheapest model for renames and copy; the premium model only for the step marked hardest in `README.md`.

**Token rule.** Copy from `reference/` and the chassis; never generate a client, a renderer or a Dockerfile. If a step needs a mechanism not confirmed in `.github/instructions/arag-api.instructions.md` or `reference/arag-platform-quirks.md`, stop and flag it; do not invent an endpoint.
