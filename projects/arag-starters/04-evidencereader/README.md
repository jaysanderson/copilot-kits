# EvidenceReader

> "The AI summary looked fine until someone asked 'where does it say that?' and nobody could show them."

**Drop in your documents, ask, and click any claim to land on the exact page that supports it.**

Drag PDFs onto the page; they are uploaded and processed. Ask a question; every sentence carries a marker; clicking it opens the PDF at the cited page with the passage highlighted.

## What Progress Agentic RAG does here
`POST /kb/{id}/upload` for binaries; `/ask` with `citations: true` keyed by paragraph id; paragraph positions from `GET /resource/{id}?show=extracted` give the page; `place_citations` in `arag.py` puts the markers at the claim. Remove ARAG and this is a summary nobody can check.

## Run it
```
cp .env.example .env        # fill ARAG_HOST, KB_ID, KB_TOKEN
pip install -r requirements.txt
uvicorn app:app --port 8080  # http://127.0.0.1:8080
```

## Where to take it next
Three things left out on purpose so this stays a starting point:
- **Folders and per-folder scopes with `filter_expression`**
- **Share links to a question and its evidence**
- **Saved highlights and notes**

## Hardest step
Step 2, page numbers from paragraph positions, then the pdf.js highlight. Everything else is plumbing.

## Series
Day 4 of ten ARAG starters. Each one is small, finished, and built on a Knowledge Box rather than a vector store. `BRIEF.md` is the build plan; `ARTICLE.md` is the LinkedIn piece.

## The standard

`STANDARD.md` defines what finished means for this product, line by line with blockers marked. `/audit-standard` reports against it; `/raise-standard` fixes one line per chat; `/qa-gate` is the independent check before anything goes public.
