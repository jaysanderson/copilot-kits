# CallSense

> "Hundreds of recorded calls a month and the only person who knows what customers are saying is the one who was on the call."

**Upload the recordings. Ask what customers are actually saying. Get answers with the timestamp to prove it.**

A calls explorer with categories, a per-call ask with timestamps, a dashboard of themes, and (new) upload through the app.

## What Progress Agentic RAG does here
Native audio ingestion and transcription through `/upload`; per-call `/ask` scoped with resource filters; REMi confidence (`lib/confidence.ts`); category labelsets via `/labelsets`. Remove ARAG and this is a transcript search box.

## Run it
See the source app's README below for the run commands; secrets go in `.env` (Python) or `.env.local` (Next.js), both gitignored.

## Where to take it next
Three things left out on purpose so this stays a starting point:
- **Call libraries per team**
- **Speaker tags and talk-time**
- **Push themes to the CRM**

## Hardest step
Step 2, producing five believable synthetic calls. The code is already there.

## Series
Day 8 of ten ARAG starters. Each one is small, finished, and built on a Knowledge Box rather than a vector store. `BRIEF.md` is the build plan; `ARTICLE.md` is the LinkedIn piece.

## The standard

`STANDARD.md` defines what finished means for this product, line by line with blockers marked. `/audit-standard` reports against it; `/raise-standard` fixes one line per chat; `/qa-gate` is the independent check before anything goes public.

## Source app
The copied app's own README is `README.source.md` (run commands, reset, narrative). Its customer names are fictional and are purged in BRIEF step 1.
