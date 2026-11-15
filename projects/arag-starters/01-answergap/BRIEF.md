# BRIEF: AnswerGap (day 1 of the series)

> "Ask ChatGPT about our category and it recommends our competitor. We don't know why, or what to publish to change it."

**Who shares this.** Head of marketing, founder.

**Promise.** See which brand the AI recommends for your buyers' questions, and what to publish to change it.

**The one job.** Enter your domain and up to two rivals. The app crawls each (cap 40 pages), loads every page into one Knowledge Box with a `source` label per domain, generates the 20 questions a buyer asks in your category, asks each one, and shows who gets cited per question plus the questions where you are absent, each with a suggested piece to publish.

**Why ARAG is load-bearing.** One KB, one labelset `source`, one label per domain (`label_filter` in `arag.py`). The cited resources in each `/ask` response decide the winner per question; a question where your label never appears in `retrieval_results` is a gap. Question generation and the publish suggestions use `ask_structured` (JSON schema; never with `citations: true`). Remove ARAG and this is a scraper with opinions.

**Base.** The chassis (`CHASSIS.md`): `app.py`, `arag.py`, `static/`, `product.json`. Add product routes under `# --- product routes` in `app.py` and a panel in `static/`. Nothing in the chassis is rewritten.

**Knowledge Box.** New KB, writer token (the app uploads). Nothing to seed; the crawl seeds it.

**Finishing steps, in order (one Copilot chat each).**
1. Crawl: copy `reference/semanticsite-server/crawler.py` and `robots.py` into the app as `crawl.py`; drop the SemanticSite config object, keep the politeness and page cap.
2. Ingest: one `POST /kb/{id}/resources` per page with `title`, `texts.body.body`, `origin.url` and a `source` classification label (shape in `reference/semanticsite-server/knowledge.py`; rules in `.github/instructions/arag-api.instructions.md`). Store rid to domain in `data/manifest.json`. Poll until PROCESSED (`reference/kb-pipeline/`).
3. Questions: one `ask_structured` call with schema `{questions: [{text, intent}]}` (prompt pattern in `reference/question-generation/prompts.ts` and `generateTopLevel.ts`). Save to `data/run.json`.
4. Scoring: for each question `arag.ask`; collect rids from `citations` keys and `retrieval_results`; map to domains via the manifest; winner = most cited domain; gap = your domain absent.
5. Suggestions: for each gap one `ask_structured` call returning `{title, outline[3], why}` grounded on the rivals' pages.
6. UI: a panel above the ask bar with three domain inputs, a progress line, the results table (question, winner, cited title) and the gap list. Print the cost estimate (pages x calls) before the run.

**Done when** (these lines are section 0 of `STANDARD.md`; every (B) line there must also be done):
- Three domains crawled (cap 40 pages each) and visible as labelled resources on the KB.
- `data/run.json` holds 20 generated questions and a winner per question with the cited source title.
- The gap list shows at least one question with a suggested title and outline.
- Nothing in the UI names a zone, KB id or `/ask`; the How this works panel carries the mechanics.

**Deliberately not built (the article's "where to take it next").**
- Content briefs exported as docx from each gap
- Scheduled re-runs with a trend line per question
- Probing external LLM APIs for the same questions and comparing

**Copilot prompts.** `/finish-starter` for each step above, `/qa-gate` at the end, `/write-article` last. Cheapest model for renames and copy; the premium model only for the step marked hardest in `README.md`.

**Token rule.** Copy from `reference/` and the chassis; never generate a client, a renderer or a Dockerfile. If a step needs a mechanism not confirmed in `.github/instructions/arag-api.instructions.md` or `reference/arag-platform-quirks.md`, stop and flag it; do not invent an endpoint.
