# GraphBuilder

> "The same customer, product or supplier is named six different ways across our documents. Nobody can see how anything connects."

**Point it at your documents and see how your customers, products and suppliers actually connect, then export a taxonomy your systems can use.**

Connect to a Knowledge Box, generate a taxonomy grounded in its content, review and edit the tree, export SKOS. New: a graph view of the entities and relations ARAG extracted.

## What Progress Agentic RAG does here
Taxonomy proposals come from `/ask` with a JSON schema, validated and repaired (`lib/engine/`). The graph view reads `/graph` (pass `top_k` explicitly and `undirected: true`) after a knowledge-graph extraction task has run on the KB. Remove ARAG and this is a mind map.

## Run it
See the source app's README below for the run commands; secrets go in `.env` (Python) or `.env.local` (Next.js), both gitignored.

## Where to take it next
Three things left out on purpose so this stays a starting point:
- **Edit and merge entities back into the graph**
- **Governance workflow with approvals**
- **Push the taxonomy to a semantic platform**

## Hardest step
Step 2, porting the graph route; keep the list view before attempting a force layout.

## Series
Day 7 of ten ARAG starters. Each one is small, finished, and built on a Knowledge Box rather than a vector store. `BRIEF.md` is the build plan; `ARTICLE.md` is the LinkedIn piece.

## The standard

`STANDARD.md` defines what finished means for this product, line by line with blockers marked. `/audit-standard` reports against it; `/raise-standard` fixes one line per chat; `/qa-gate` is the independent check before anything goes public.

## Source app
The copied app's own README is `README.source.md` (run commands, reset, narrative). Its customer names are fictional and are purged in BRIEF step 1.

## Not copied (locked in the source tree)
These files were unreadable when harvesting. They are Progress logo and token assets; use `brand/` in this folder instead.
- `public/brand/progress-agentic-rag-lockup-alt.svg`
- `public/brand/progress-agentic-rag-lockup.svg`
