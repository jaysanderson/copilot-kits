# SearchPlus

> "Our site search returns the wrong product first and we can't change it without a dev ticket. Every bad result is a lost sale."

**Site search that shows its evidence and its relevance, and lets the business pin, boost and bury results without a developer.**

A search box over a product catalogue. Every result shows the matching passage and its relevance score. A rules panel (pin, boost, bury, synonyms) is applied server-side after retrieval and every result says why it ranked where it did.

## What Progress Agentic RAG does here
`/find` with `features: [keyword, semantic]` returns paragraph-level scores per resource (`resources_from_find` in `arag.py`), which is what makes a visible relevance score and a passage snippet possible. Label filters give facets. The rules re-rank the retrieved set in the app, so the index is never touched, which is what makes the rules safe for a non-developer. Remove ARAG and this is a keyword box with no passages and no semantics.

## Run it
```
cp .env.example .env        # fill ARAG_HOST, KB_ID, KB_TOKEN
pip install -r requirements.txt
uvicorn app:app --port 8080  # http://127.0.0.1:8080
```

## Where to take it next
Three things left out on purpose so this stays a starting point:
- **Synonyms learned from zero-result queries**
- **A/B rule sets with a split and a report**
- **Search analytics: top queries, zero-result queries**

## Hardest step
Step 2, the rule application: boosts and buries must re-rank without hiding the original score, and the reason string must be true.

## Series
Day 2 of ten ARAG starters. Each one is small, finished, and built on a Knowledge Box rather than a vector store. `BRIEF.md` is the build plan; `ARTICLE.md` is the LinkedIn piece.

## The standard

`STANDARD.md` defines what finished means for this product, line by line with blockers marked. `/audit-standard` reports against it; `/raise-standard` fixes one line per chat; `/qa-gate` is the independent check before anything goes public.
