# AkademDocs Pre-Check

A synchronous document-review API/portal demonstrating Progress Agentic RAG (ARAG) as the
engine behind a government submission portal's pre-submission document check - built against
the target PRD, "AI Agent for Document Review at the Degree Equivalency Application Submission
Stage" (Israel-shaped, entirely synthetic content).

**Frontend rebuild, 3 Sep 2026.** The 3 Sep 2026 demo-estate audit graded the prior officer
console **C**: raw internal enum strings rendered straight to users ("NAME_CHANGE_CERTIFICATE",
"DIPLOMA, UNRECOGNISED"), a single plain unstyled table as the whole experience, no Progress
Agentic RAG presence beyond one footer line, and a sparse below-the-fold page. The backend
pipeline below is unchanged (it was never the problem) - this rebuild replaces the entire
`static/` frontend to the current world-class demo bar: a Progress Agentic RAG-branded rail
console (this is a GENERIC vertical demo, not a named account, so Progress ARAG *is* the "own
system" per the brand-fork rule), five real routes/use cases, inline numbered citation markers
that open the real source page with the grounding passage highlighted, a qualitative
extraction-confidence badge on every document (never a raw retrieval score), and a new
Insights page charting real per-document extraction output (document types, legibility issues,
language mix, name-match outcomes, classification source) - all derived from what Agentic RAG
actually read off unstructured scans, never hand-entered.

**Declared persona (Standard B7):** built for an **ICT Leader** and **Solutions Architect**
evaluating how Agentic RAG integrates into an existing case-management system - the whole app
is framed around a real wire API contract (see below), the honest disclosure of which parts are
ARAG's own mechanism vs. this app's surrounding engineering, and a from-the-Knowledge-Box-console
verifiable configuration (the real Labeler DA task). This is deliberately an integration/
architecture story, not a policy or caseworker-productivity pitch.

**B39 - real REMi trust read, added 3 Sep 2026.** The one gradable grounded output in this app
is the per-page classify/extract answer (`app/arag_client.py::classify_page`) - a real LLM
answer, grounded in the page's OCR'd text, that drives the document type and every extracted
field. `app/arag_client.py::score_remi()` scores that exact answer with a live call to
`POST {kb}/predict/remi` (KB service-account token), against the FULL retrieved page context -
never the truncated display citations - following the single-concatenated-context pattern from
the one working REMi implementation in the estate (`reference-repos/rwa-intel-demo/app.py`).
`app/pipeline.py::_assemble_document` aggregates a multi-page document to its WORST-scoring page
(min, not average) and drives the existing qualitative confidence badge directly from REMi's
0-5 groundedness score (>=4.0 High, >=2.5 Moderate, else Low) - never a raw numeral in the UI.
When REMi is genuinely unavailable for a document (a failed call, no context to score), the
badge falls back honestly to the pre-B39 signal (independent Labeler-task confirmation + field
completeness) rather than fabricating a score - `/api/analytics`'s `remi_scored_documents` count
shows how many documents in the corpus got a real live REMi read. The Insights page's "Answer
trust - REMi groundedness" chart shows the real High/Moderate/Low distribution across every
processed case. Every other route (queue, codes, and the aggregation-only parts of Insights) has
no gradable grounded ANSWER of its own to score - they render or count structured data, not a
generated response - so REMi does not apply there.

Applicants upload every document for their application (a single messy multi-page PDF, or
several files). The service splits it into individual pages, classifies each page into one of
five document types, extracts the applicant's name, institution, degree type and date, and
authenticity indicators (apostille, notarisation, certified-copy stamp, signature - all
indicative only, never authoritative), flags legibility problems (blur, darkness, cropping,
rotation), checks the applicant's declared name against the name found in the documents
(including a Cyrillic-to-Hebrew transliteration check), and returns a structured,
closed-vocabulary verdict in the applicant's language. **The check is always advisory -
`CanSubmit` is always `true`. It never blocks a submission; it only tells the reviewing officer
what to look at first.**

## API contract (PRD section 12)

`POST /api/submit` request and response fields follow the PRD's exact section 12.1/12.2 names -
this is the real wire contract, not a demo-only shape translated somewhere else. Request:
`files`, `RequestId` (optional, server-generates if absent), `ApplicantId`, `ApplicantName` (or
`ApplicantFirstNameHebrew`/`ApplicantLastNameHebrew`), `ResponseLanguage`,
`DocumentSourceLanguage`, `InstitutionCountry`, `DegreeType`, `DocLanguage`. Response:
`RequestId`, `ProcessingStatus`, `DetectedDocuments`, `SplitDocuments`, `MissingDocuments`,
`DocumentValidationResults`, `StampsValidationResults`, `CandidateMessages`, `CanSubmit`,
`RecommendedAction`, `ProcessingDateTime`, `EngineVersion`, `SplitDocumentFiles`,
`NameMatchingResults`, `ResponseLanguage`. `InstitutionCountry`/`DegreeType`/
`DocumentSourceLanguage`/`DocLanguage` are accepted and echoed but not yet consumed by any real
check - see "Known gaps" below rather than assuming they drive logic they don't.

The officer console - five routes, five distinct use cases (Standard B4) - is a **demo
convenience layer** built on top of this API for visual walkthroughs - the PRD itself specifies
an API-only agent with no UI (section 2/3). The console is optional scaffolding; the API
contract above is the actual deliverable.

1. **`/` - Submission queue.** Every pre-checked case, grouped by how much officer attention it
   needs (needs human review / needs attention / ready), each group a horizontal row of case
   cards with real document-type chips and counts. Triage prioritisation.
2. **`/submit` - New submission.** A manually-stepped wizard (applicant details -> documents ->
   run pre-check) - this is the route where Agentic RAG actually reads the uploaded pages.
   Automated document intake and structuring.
3. **`/submission/{id}` - Case detail.** The full structured verdict: documents, extracted
   fields, authenticity indicators, and numbered citation markers next to every grounded fact
   that open the real source page image with the exact passage highlighted. Auditable per-claim
   verification.
4. **`/insights` - Program analytics.** Real charts aggregated from every processed case's
   Agentic RAG output (document types, legibility issues, language mix, name-match outcomes,
   which classification path produced each result) - never hand-entered figures. Program-level
   policy/resourcing signal.
5. **`/codes` - Feedback code catalogue.** The closed, versioned, five-language vocabulary every
   applicant-facing message comes from, filterable by severity, with live-detection status shown
   honestly per code. Consistent, auditable, translated applicant communication.

## Architecture

- **ARAG Knowledge Box** - every uploaded page is ingested as its own resource. ARAG's own
  visual-extraction pipeline (no third-party OCR vendor anywhere in this pipeline) reads the
  page.
- **A real, configured Labeler DA task** runs on this Knowledge Box (registered via
  `POST /kb/{id}/task/start`, applied to both existing and future resources) - genuinely
  classifying every page into the same six-type vocabulary this app uses. This is inspectable
  directly via the ARAG/Nuclia admin console (`GET /kb/{id}/tasks` shows it in the `configs`/
  `running`/`done` arrays, not just the always-populated type catalogue) - not decoration. See
  "Two real classification paths" below for how it fits alongside the live synchronous path.
- **FastAPI orchestration layer** (`app/`) - **a meaningful share of this demo's output is
  custom application code wrapped around ARAG, not configuration of an off-the-shelf agent.**
  ARAG itself does two things: OCR/visual-extraction ingest, and a grounded classification/
  extraction call (plus, in the background, real Labeler DA-task classification - see below).
  Everything else - page splitting, legibility scoring, name/institution fuzzy-matching,
  completeness and duplicate detection, and final structured-verdict assembly - is this app's
  own engineering, not something ARAG provides natively. Budget accordingly if this moves toward
  a real production build: the surrounding logic is real work, not a thin wrapper.
  - `pdf_split.py` - splits an uploaded multi-page PDF into individual pages with real page
    numbers (not inferred), each becoming its own KB resource.
  - `legibility.py` - local, deterministic blur/darkness/crop/rotation checks (Laplacian
    variance, mean brightness, border-content ratio, aspect ratio) - kept local rather than
    asked of the model so the same page always gets the same verdict in a live demo.
  - `transliteration.py` - a phonetic Cyrillic-to-Hebrew transliteration table, a
    Levenshtein-based fuzzy name match (whole-name and positional first/last-token), and the
    same fuzzy-match machinery reused for cross-document institution-name consistency.
  - `pipeline.py` - orchestrates validate -> split -> legibility -> ARAG ingest+classify ->
    merges same-typed pages into a logical document -> completeness/duplicate/institution
    consistency checks -> assembles the PRD-shaped, closed-vocabulary verdict. This file is the
    largest single piece of custom engineering in the app.
  - `pdf_split.py` - splits an uploaded multi-page PDF into individual pages with real page
    numbers (not inferred), each becoming its own KB resource.
  - `legibility.py` - local, deterministic blur/darkness/crop/rotation checks (Laplacian
    variance, mean brightness, border-content ratio, aspect ratio) - kept local rather than
    asked of the model so the same page always gets the same verdict in a live demo.
  - `transliteration.py` - a phonetic Cyrillic-to-Hebrew transliteration table plus a
    Levenshtein-based fuzzy name match.
  - `pipeline.py` - orchestrates validate -> split -> legibility -> ARAG ingest+classify ->
    merges same-typed pages into a logical document -> completeness/duplicate checks ->
    assembles the PRD-shaped, closed-vocabulary verdict.
  - `codes.py` - the closed feedback-code catalogue: the PRD's exact 24 codes (section 10), full
    HE/RU/EN/UK/FR translation, each flagged honestly `implemented: true/false` (see "Known
    gaps"). The pipeline only ever emits codes from this catalogue, never free text.

## Two real classification paths, not one dressed up as two

- **Live/synchronous path** (what a request actually waits on): a scoped, synchronous
  grounded-answer call classifies the document and extracts fields, with citations back to the
  source text. A background DA task cannot bound a synchronous HTTP request's latency, so this
  is the only mechanism that can return within one call.
- **Background/audit path**: the real Labeler DA task above independently classifies the same
  pages asynchronously. When it has already labelled a page by the time a request runs (true for
  every pre-seeded/backfilled resource, and possible for a fresh upload if the worker is fast
  enough), its real classification is preferred over the live path's guess - see
  `arag_client.labeler_classification()` and `pipeline._process_one_page()`. Each document's
  `pages[].classified_by` field in the API response says which path actually produced its
  classification (`labeler_da_task` or `ask_grounded_query`), and the officer console's document
  cards show this too - never claimed as one thing when it was the other.

## A known platform gap, routed around (not re-discovered)

Nuclia's Data Augmentation **Generator** `json:true` output path (`kv_schema_id` / structured
JSON extraction as an async DA task) is a confirmed platform bug as of August 2026 - it 422s on
every schema shape tested, including Progress's own documented example. This is distinct from
the Labeler task above (which has no documented bug and is genuinely registered and running).
Field **extraction** (name, institution, degree, date, stamps) uses a **synchronous, plain-text
`/ask` call** with a strict labelled-line output format (`app/arag_client.py::CLASSIFY_SYSTEM`),
parsed server-side into the closed-vocabulary JSON - ARAG still does the actual reading and
reasoning; only that one output-shaping step is this app's own code, and the in-app "How this
works" reveal (top-right on every route) says so explicitly, by name, rather than burying it in
this README alone.

One more thing worth knowing if you extend this: a KB resource's `metadata.status` can report
`PROCESSED` a few seconds before the resource is reliably reachable by `/ask`'s retrieval-scored
search (observed live, worse under concurrent page processing). `classify_page_with_retry`
retries with backoff to cover this.

## What's demonstrated

1. **Multi-doc split** - the flagship bundle (`seed/corpus/flagship-bundle-sidorov.pdf`) is one
   3-page PDF containing a diploma, a transcript, and a name-change certificate, split into three
   logical documents with correct page ranges.
2. **Closed-vocabulary structured JSON** - the PRD's exact 24 feedback codes, full HE/RU/EN/UK/FR
   translation, `/codes` shows exactly which codes have live detection today vs catalogued-only.
3. **Planted defects caught** - the flagship bundle's diploma has **no apostille**
   (`DOC_STAMP_MISSING`) and its transcript page is **blurred beyond legibility**
   (honestly reported `Unidentified`/`DOC_UNKNOWN_TYPE` rather than a confident wrong guess).
4. **Name transliteration mismatch** - declared name in Hebrew vs. a different Cyrillic name on
   the diploma, correctly flagged `DOC_NAME_TRANSLATION_MISMATCH`.
5. **`EngineVersion` + `ProcessingDateTime` in every response**, for audit trail.
6. **No third-party OCR vendor** anywhere in the pipeline.
7. **Document completeness** - a required type (diploma/transcript) missing anywhere in the
   submission is a distinct `MissingDocuments` entry (`DOC_MISSING_DIPLOMA`/
   `DOC_MISSING_TRANSCRIPT`), not a silent pass.
8. **Duplicate-type detection** - two documents of the same type in one submission are flagged
   `DOC_DUPLICATE_TYPE`, status `Duplicate`.
9. **Real ARAG configuration behind the reveal** - a genuinely registered Labeler DA task, not
   just an in-app explainer (see "Two real classification paths" above).

## Coverage evidence (rev 3, 8 Aug 2026)

All 24 PRD codes now have live detection (`app/codes.py`'s `implemented` flag is `true` for
every code). `seed/verify_coverage.py` individually confirms every PRD section 9 status and
every "live" section 10 code against a real test fixture run through the actual pipeline (not a
code read) - `data/coverage_report.json` is the machine-readable evidence, one entry per target.
Result: **15/16 targets PASS, 1 honest gap.**

- **`DOC_FIRST_NAME_MISMATCH` / `DOC_LAST_NAME_MISMATCH`** - implemented as a **positional token
  comparison** (first whitespace-separated token vs first, last vs last on the same
  declared/extracted pair `DOC_NAME_TRANSLATION_MISMATCH` already computes) - not a
  linguistically-aware name-order detector. Reliably splitting first/last across Hebrew,
  Cyrillic and Latin scripts with different conventions (Slavic surname-first vs.
  Hebrew/English given-first) is genuinely hard; this is a disclosed simplification, not a claim
  of solving name-order detection. Verified live with two dedicated fixtures (first-only and
  last-only mismatch).
- **`DOC_MISSING_INSTITUTION_NAME_APPRO` / `DOC_INSTITUTION_NAME_MISMATCH`** - implemented:
  extracted institution names are fuzzy-compared pairwise across every document where the field
  applies; a mismatch with no institution name-change certificate present in the submission
  raises the former, a mismatch with a certificate present raises the latter. Verified live with
  both scenarios.
- **`DOC_STAMP_NOT_CLEAR`** - the one honest gap. Attempted with a dedicated fixture (a page with
  an overlapping, illegibly-labelled second seal graphic next to a genuine apostille stamp) -
  the model still read the genuine apostille as `PRESENT` rather than reporting ambiguity.
  Translated and catalogued, `implemented: true` (the detection logic exists and is exercised
  the same way as the others), but not proven to reliably trigger - this is a model-behaviour
  limit, not something the app can force deterministically the way the local legibility checks
  can.
- **`InstitutionCountry` / `DegreeType` / `DocumentSourceLanguage` / `DocLanguage`** request
  fields are accepted and echoed but don't drive any check yet.
- The submission store (SQLite + a Fly volume, see "Deploy") is real persistence for a demo, not
  production-grade infrastructure (no backups/replication beyond Fly's own volume snapshots).
- File-size/page-count limits (10MB/8 pages, PRD section 4.1), true concurrent-load behaviour,
  and a real Back Office handoff integration (section 4.4/11) are validated at the unit level
  (`_validate_files` rejects an oversized/over-length file) but not load-tested or integrated
  with any external system - out of scope for this demo per the GM's own framing of what a real
  production build would need to budget separately.

## Seeded demo narrative (what to click)

1. Open `/` - the queue, five submissions seeded across the three review-priority groups, with
   real counts on every stat tile and group header.
2. Click into the "Needs human review" group's flagship case (applicant `איוואן איוואנוב`).
   Point out: the `CanSubmit: true` banner + `RecommendedAction`, the three split documents with
   page ranges and PRD-exact statuses, the qualitative confidence badge on each document, the
   missing-stamp flag, the unidentified/illegible page, and the name-mismatch flag with its
   transliteration shown. Click a numbered citation marker next to a document's status - it opens
   the real source page image with the grounded excerpt highlighted alongside it. Click a page
   thumbnail directly for the same view.
3. Click "How this works" (top-right, every route) - a real labelled diagram of THIS page's own
   flow, what it's doing, and why it matters; the content is different on every route.
4. Switch the "Feedback language" toggle between HE/RU/EN/UK/FR - the same codes re-render
   instantly from `/api/codes`.
5. Go to `/submit` - step through the wizard, or "Load the demo bundle" to re-run the same
   pre-check live end to end.
6. Visit `/insights` - real charts built from every processed case's Agentic RAG output: document
   types, legibility issues, language mix, name-match outcomes, and the Labeler-DA-task-vs-live-
   query split.
7. Visit `/codes` - the full 24-code catalogue, filterable by severity, with live-detection
   status shown honestly per code.

## Local development

```bash
python3 -m venv .venv   # or use the factory root .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python seed/provision_kb.py     # one-time: creates the KB + service token in .env
.venv/bin/python seed/seed.py             # seeds the demo submissions
.venv/bin/python -m uvicorn app.main:app --reload --port 8811
```

`seed/generate_corpus.py` is a **build-time-only** script (needs a Unicode TTF with Cyrillic
glyphs - not guaranteed present in the Fly deploy container) that produces the PDFs already
committed under `seed/corpus/`. Only re-run it locally if you change the corpus design;
`seed.py` just uploads the pre-built PDFs at runtime.

## 30-second reset

```bash
.venv/bin/python seed/seed.py --purge
```

Deletes every resource in the Knowledge Box and the local submission history, then re-seeds the
demo submissions fresh. Safe to run mid-demo if something gets into a bad state. This does not
remove the registered Labeler DA task (it's KB-level configuration, not submission data).

## Deploy

```bash
fly apps create akademdocs-precheck
fly volumes create akademdocs_data --region syd --size 1 --app akademdocs-precheck
fly secrets set ARAG_KB_URL=... ARAG_SERVICEACCOUNT=... --app akademdocs-precheck
fly deploy --app akademdocs-precheck
```

The volume is mounted at `/app/data` (see `fly.toml`'s `[mounts]`) so the SQLite submission
store and page thumbnails survive machine restarts/stops - `auto_stop_machines` is enabled, so
without the volume a routine idle-stop would silently revert to whatever the deploy image last
baked in. The ARAG service-account token is a Fly secret, never in the image or the repo.
`min_machines_running = 1` (fixed 3 Sep 2026, was `0`) keeps one machine always warm so the
first hit after idle serves real content, not an API-cold-start empty shell.

**Typography note:** the design system is built to Progress Sans (Display/Text), but the actual
font files aren't bundled in this repo per the `progress-arag-branding` skill's licensing terms
(proprietary, Brand-Bank-sourced only) - the live app renders in Arial, the documented compliant
fallback. Swap in the real webfont files under a confirmed licensing position before a
public-facing showing where exact typography matters.

## Synthetic content

Every document, applicant, institution and identifier in this demo is fictional. Institution
names were deliberately chosen or renamed to avoid any resemblance to real universities or
government agencies (see `seed/generate_corpus.py`).
