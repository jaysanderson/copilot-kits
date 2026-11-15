# The chassis (shared by the starters that are not already a finished app)

Six files, about 450 lines, copied from finished Progress Agentic RAG apps. Do not rewrite any of them; add to them.

| File | Lines | Came from | Change it? |
|---|---|---|---|
| `arag.py` | 252 | a finished FastAPI demo (verbatim) | No. It already has `find`, `ask`, `ask_structured` (JSON schema), `groundedness` (REMi), `place_citations`, `label_filter`. |
| `app.py` | ~130 | written once for the series | Add product routes under `# --- product routes`. Leave the chassis routes alone. |
| `static/index.html`, `app.css`, `app.js` | ~60 / ~90 / ~80 | written once for the series | Add your product's panel; keep the ask bar, badge, sources list and "How this works". |
| `static/mdlite.js` | 92 | a finished demo (verbatim) | No. Every piece of AI text renders through `MuMd.md`. |
| `product.json` | ~15 | per product | Yes: name, promise, suggested questions, how-it-works steps. |

Run it: `cp .env.example .env`, fill the three values, `pip install -r requirements.txt`, `uvicorn app:app --port 8080`, open http://127.0.0.1:8080.

Facts the chassis relies on, all confirmed in `.github/instructions/arag-api.instructions.md`:
- Server-side only; header `X-NUCLIA-SERVICEACCOUNT: Bearer <token>`; `X-Synchronous: true` for one JSON body.
- `/ask` with `citations: true` and `retrieval_results` for provenance; `/find` for scored retrieval.
- `answer_json_schema` never together with `citations: true`; provenance then comes from `retrieval_results`.
- `/predict/remi` groundedness exists on enterprise KBs only; the badge degrades to "Support not scored" elsewhere.
- Always `filter_expression`, never the legacy `filters` array.
