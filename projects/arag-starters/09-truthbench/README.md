# TruthBench

> "The AI pilot demoed beautifully and we have no way to know whether it's making things up in production."

**Paste ten questions. See which answers your knowledge base can actually back up, before a customer finds out.**

Paste up to 25 questions. For each: the answer, a groundedness score, how many sources were cited, and whether retrieval alone agrees with the answer. Weak rows expand to show the passages. Export CSV.

## What Progress Agentic RAG does here
`/predict/remi` groundedness against the full retrieved context (`groundedness` in `arag.py`; enterprise KBs), `contexts_from_ask`, and a `/find` versus `/ask` agreement check. Remove ARAG and this is a spreadsheet of vibes.

## Run it
```
cp .env.example .env        # fill ARAG_HOST, KB_ID, KB_TOKEN
pip install -r requirements.txt
uvicorn app:app --port 8080  # http://127.0.0.1:8080
```

## Where to take it next
Three things left out on purpose so this stays a starting point:
- **Regression history: diff two runs**
- **CI gate: non-zero exit when a score drops**
- **Generate the question set from the KB itself**

## Hardest step
Step 1, the overlap metric: define it before coding and keep it explainable in one sentence.

## Series
Day 9 of ten ARAG starters. Each one is small, finished, and built on a Knowledge Box rather than a vector store. `BRIEF.md` is the build plan; `ARTICLE.md` is the LinkedIn piece.

## The standard

`STANDARD.md` defines what finished means for this product, line by line with blockers marked. `/audit-standard` reports against it; `/raise-standard` fixes one line per chat; `/qa-gate` is the independent check before anything goes public.
