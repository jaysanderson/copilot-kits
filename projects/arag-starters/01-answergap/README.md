# AnswerGap

> "Ask ChatGPT about our category and it recommends our competitor. We don't know why, or what to publish to change it."

**See which brand the AI recommends for your buyers' questions, and what to publish to change it.**

Enter your domain and up to two rivals. The app crawls each (cap 40 pages), loads every page into one Knowledge Box with a `source` label per domain, generates the 20 questions a buyer asks in your category, asks each one, and shows who gets cited per question plus the questions where you are absent, each with a suggested piece to publish.

## What Progress Agentic RAG does here
One KB, one labelset `source`, one label per domain (`label_filter` in `arag.py`). The cited resources in each `/ask` response decide the winner per question; a question where your label never appears in `retrieval_results` is a gap. Question generation and the publish suggestions use `ask_structured` (JSON schema; never with `citations: true`). Remove ARAG and this is a scraper with opinions.

## Run it
```
cp .env.example .env        # fill ARAG_HOST, KB_ID, KB_TOKEN
pip install -r requirements.txt
uvicorn app:app --port 8080  # http://127.0.0.1:8080
```

## Where to take it next
Three things left out on purpose so this stays a starting point:
- **Content briefs exported as docx from each gap**
- **Scheduled re-runs with a trend line per question**
- **Probing external LLM APIs for the same questions and comparing**

## Hardest step
Step 4, the scoring loop: mapping cited rids back to domains and deciding a winner honestly when two domains tie. Use the premium model once, here.

## Series
Day 1 of ten ARAG starters. Each one is small, finished, and built on a Knowledge Box rather than a vector store. `BRIEF.md` is the build plan; `ARTICLE.md` is the LinkedIn piece.

## The standard

`STANDARD.md` defines what finished means for this product, line by line with blockers marked. `/audit-standard` reports against it; `/raise-standard` fixes one line per chat; `/qa-gate` is the independent check before anything goes public.
