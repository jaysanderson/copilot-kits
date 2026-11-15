# TriageDesk

> "Two hundred applications a week, each read by a person, each decided slightly differently, nobody can explain why."

**Every case read the same way: a decision, a confidence and the evidence, in seconds, with a human in charge.**

Submit a case (form fields or a PDF). The pipeline returns a structured decision (outcome, confidence, reasons, evidence) as JSON and as a card, and a dashboard lists every decision.

## What Progress Agentic RAG does here
`answer_json_schema` on `/ask` for schema-constrained decisions, with the instructions carried in the schema's property descriptions (a system prompt is ignored beside a schema) and provenance from `retrieval_results`; `filter_expression` scopes each case to the policy documents. All of it already runs in `app/pipeline.py` and `app/arag_client.py`. Remove ARAG and this is free text someone re-keys.

## Run it
See the source app's README below for the run commands; secrets go in `.env` (Python) or `.env.local` (Next.js), both gitignored.

## Where to take it next
Three things left out on purpose so this stays a starting point:
- **A review queue with SLA timers**
- **An override log with the reviewer's reason**
- **Batch upload of a day's cases**

## Hardest step
Step 1, deciding what is domain and what is product. Everything else is a rename.

## Series
Day 5 of ten ARAG starters. Each one is small, finished, and built on a Knowledge Box rather than a vector store. `BRIEF.md` is the build plan; `ARTICLE.md` is the LinkedIn piece.

## The standard

`STANDARD.md` defines what finished means for this product, line by line with blockers marked. `/audit-standard` reports against it; `/raise-standard` fixes one line per chat; `/qa-gate` is the independent check before anything goes public.

## Source app
The copied app's own README is `README.source.md` (run commands, reset, narrative). Its customer names are fictional and are purged in BRIEF step 1.

## Not copied (locked in the source tree)
These files were unreadable when harvesting. They are Progress logo and token assets; use `brand/` in this folder instead.
- `static/assets/brand/primary-horizontal-alternate.svg`
