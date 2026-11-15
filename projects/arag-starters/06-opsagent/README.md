# OpsAgent

> "Chat tells us what to do; a person still logs in to five systems to do it. The AI saved nobody any time."

**Give it a goal. Watch it read your documents, call your systems and show its work before anything happens.**

Type one goal. A Retrieval Agent reads the Knowledge Box and calls this app's own tools (two demo tools, dry-run) over MCP. The trace shows every step, tool call and cited document, then the result and the action it would take.

## What Progress Agentic RAG does here
The Retrieval Agent is ARAG's (configured on the data-platform host; the app runs no planner, Definition of Pass D27). This app exposes tools over MCP (`reference/mcp-rao/`) and forwards the user's JWT (`reference/skill-rao-workflow/`). Remove ARAG and this is function calling with no evidence.

## Run it
```
cp .env.example .env        # fill ARAG_HOST, KB_ID, KB_TOKEN
pip install -r requirements.txt
uvicorn app:app --port 8080  # http://127.0.0.1:8080
```

## Where to take it next
Three things left out on purpose so this stays a starting point:
- **More tools: calendar, ERP, email**
- **Approval step before any write**
- **Memory across runs per user**

## Hardest step
Step 2, configuring the Retrieval Agent and JWT forwarding; do it from the skill file, not from memory.

## Series
Day 6 of ten ARAG starters. Each one is small, finished, and built on a Knowledge Box rather than a vector store. `BRIEF.md` is the build plan; `ARTICLE.md` is the LinkedIn piece.

## The standard

`STANDARD.md` defines what finished means for this product, line by line with blockers marked. `/audit-standard` reports against it; `/raise-standard` fixes one line per chat; `/qa-gate` is the independent check before anything goes public.
