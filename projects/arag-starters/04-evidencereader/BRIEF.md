# BRIEF: EvidenceReader (day 4 of the series)

> "The AI summary looked fine until someone asked 'where does it say that?' and nobody could show them."

**Who shares this.** Compliance, legal, anyone who signs off.

**Promise.** Drop in your documents, ask, and click any claim to land on the exact page that supports it.

**The one job.** Drag PDFs onto the page; they are uploaded and processed. Ask a question; every sentence carries a marker; clicking it opens the PDF at the cited page with the passage highlighted.

**Why ARAG is load-bearing.** `POST /kb/{id}/upload` for binaries; `/ask` with `citations: true` keyed by paragraph id; paragraph positions from `GET /resource/{id}?show=extracted` give the page; `place_citations` in `arag.py` puts the markers at the claim. Remove ARAG and this is a summary nobody can check.

**Base.** The chassis (`CHASSIS.md`): `app.py`, `arag.py`, `static/`, `product.json`. Add product routes under `# --- product routes` in `app.py` and a panel in `static/`. Nothing in the chassis is rewritten.

**Knowledge Box.** New KB, writer token. Seed with three public PDFs (standards, a public contract template, an annual report).

**Finishing steps, in order (one Copilot chat each).**
1. Upload: `/api/upload` streams the file to `/upload` (binary, `X-Synchronous: true`), records rid and filename in `data/docs.json`. `/api/status` polls `/resource/{rid}?show=basic` until PROCESSED (pattern in `reference/kb-pipeline/`).
2. Pages: extend `/api/ask` sources with `page` taken from the cited paragraph's position metadata (`show=extracted`); confirm the key names in `reference/arag-platform-quirks.md` first.
3. Viewer: pdf.js from a pinned CDN version; open at `page`, highlight by searching the excerpt text. Layout ideas in `reference/pdf-citations/IntakePage.tsx`; marker logic in `reference/citationMarkers.ts`.
4. Drop zone and document list above the ask bar; a withheld answer when the documents do not hold it (already in the chassis).

**Done when** (these lines are section 0 of `STANDARD.md`; every (B) line there must also be done):
- Three PDFs uploaded through the app and listed with their processing state.
- One answer whose marker opens page N with the passage highlighted.
- A question the documents do not answer returns a withheld answer with no sources.
- 390 px render clean; zero raw markdown.

**Deliberately not built (the article's "where to take it next").**
- Folders and per-folder scopes with `filter_expression`
- Share links to a question and its evidence
- Saved highlights and notes

**Copilot prompts.** `/finish-starter` for each step above, `/qa-gate` at the end, `/write-article` last. Cheapest model for renames and copy; the premium model only for the step marked hardest in `README.md`.

**Token rule.** Copy from `reference/` and the chassis; never generate a client, a renderer or a Dockerfile. If a step needs a mechanism not confirmed in `.github/instructions/arag-api.instructions.md` or `reference/arag-platform-quirks.md`, stop and flag it; do not invent an endpoint.
