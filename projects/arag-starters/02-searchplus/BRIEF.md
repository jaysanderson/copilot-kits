# BRIEF: SearchPlus (day 2 of the series)

> "Our site search returns the wrong product first and we can't change it without a dev ticket. Every bad result is a lost sale."

**Who shares this.** Ecommerce manager, digital lead.

**Promise.** Site search that shows its evidence and its relevance, and lets the business pin, boost and bury results without a developer.

**The one job.** A search box over a product catalogue. Every result shows the matching passage and its relevance score. A rules panel (pin, boost, bury, synonyms) is applied server-side after retrieval and every result says why it ranked where it did.

**Why ARAG is load-bearing.** `/find` with `features: [keyword, semantic]` returns paragraph-level scores per resource (`resources_from_find` in `arag.py`), which is what makes a visible relevance score and a passage snippet possible. Label filters give facets. The rules re-rank the retrieved set in the app, so the index is never touched, which is what makes the rules safe for a non-developer. Remove ARAG and this is a keyword box with no passages and no semantics.

**Base.** The chassis (`CHASSIS.md`): `app.py`, `arag.py`, `static/`, `product.json`. Add product routes under `# --- product routes` in `app.py` and a panel in `static/`. Nothing in the chassis is rewritten.

**Knowledge Box.** New KB seeded from `seed/corpus/` (synthetic fishing-tackle catalogue from a finished retail demo). Reader token is enough after seeding.

**Finishing steps, in order (one Copilot chat each).**
1. Seed: load `seed/corpus/` (a synthetic retail catalogue) into a new KB with `reference/kb-pipeline/`; confirm with a `/find` round trip.
2. Route: `/api/search` = `arag.find(query, top_k=20)` then `apply_rules()` from `data/rules.json` (`pin: [rid]`, `boost: {rid: 1.5}`, `bury: {rid: 0.5}`, `synonyms: {term: [terms]}`; synonyms expand the query before `/find`). Return `reason` per result.
3. UI: results list with score bar, passage, reason chip; the ask bar stays for grounded answers.
4. Rules panel: GET/PUT `/api/rules` behind an `OPERATOR_KEY` env header (shape in `.env.example`). A product can be pinned from its result card.
5. Optional facets: category chips from the GET form of `/catalog`.

**Done when** (these lines are section 0 of `STANDARD.md`; every (B) line there must also be done):
- Ten queries return passages with scores; `reference/portal-retrieval/RETRIEVAL.md` explains the scoring you show.
- Pinning a product moves it to position 1 with reason `pinned`; burying drops it; a synonym query finds the product.
- Rules survive a restart (`data/rules.json`) and the operator key is required to change them.
- Zero raw markdown, zero zone strings; 390 px render clean.

**Deliberately not built (the article's "where to take it next").**
- Synonyms learned from zero-result queries
- A/B rule sets with a split and a report
- Search analytics: top queries, zero-result queries

**Copilot prompts.** `/finish-starter` for each step above, `/qa-gate` at the end, `/write-article` last. Cheapest model for renames and copy; the premium model only for the step marked hardest in `README.md`.

**Token rule.** Copy from `reference/` and the chassis; never generate a client, a renderer or a Dockerfile. If a step needs a mechanism not confirmed in `.github/instructions/arag-api.instructions.md` or `reference/arag-platform-quirks.md`, stop and flag it; do not invent an endpoint.
