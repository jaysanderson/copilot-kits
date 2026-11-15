# ValueCase

> "We built a business case for AI from guesses. The prospect's own documents held the real numbers and nobody looked."

**A business case where every number came from the prospect's own documents, with the citation to prove it.**

The existing value-case tool (levers, scenarios, provenance, sensitivity, exports) plus a Propose from documents step: point at a Knowledge Box of the prospect's documents and every lever input arrives with a proposed value and a citation; you accept or edit.

## What Progress Agentic RAG does here
`ask_structured` with a per-lever schema (`value`, `unit`, `source_title` as an enum of the retrieved titles, `quote`), scoped to the prospect's KB; the claim-check route in `reference/clinic-app.py` (lines 1002 to 1074) is the pattern for checking a figure against documents. Remove ARAG and this is a calculator.

## Run it
See the source app's README below for the run commands; secrets go in `.env` (Python) or `.env.local` (Next.js), both gitignored.

## Where to take it next
Three things left out on purpose so this stays a starting point:
- **Portfolio view across prospects**
- **Export the case to a slide deck**
- **Re-propose when the documents change**

## Hardest step
Step 2, the per-lever schema: `source_title` must be an enum of titles actually retrieved, or the citation is decoration.

## Series
Day 10 of ten ARAG starters. Each one is small, finished, and built on a Knowledge Box rather than a vector store. `BRIEF.md` is the build plan; `ARTICLE.md` is the LinkedIn piece.

## The standard

`STANDARD.md` defines what finished means for this product, line by line with blockers marked. `/audit-standard` reports against it; `/raise-standard` fixes one line per chat; `/qa-gate` is the independent check before anything goes public.

## Source app
The copied app's own README is `README.source.md` (run commands, reset, narrative). Its customer names are fictional and are purged in BRIEF step 1.

## Not copied (locked in the source tree)
These files were unreadable when harvesting. They are Progress logo and token assets; use `brand/` in this folder instead.
- `static/arag-tokens.css`
- `static/assets/logo-primary-horizontal.svg`
- `static/assets/logo-secondary-horizontal-alternate.svg`
