# BRIEF: OpsAgent (day 6 of the series)

> "Chat tells us what to do; a person still logs in to five systems to do it. The AI saved nobody any time."

**Who shares this.** COO, head of operations.

**Promise.** Give it a goal. Watch it read your documents, call your systems and show its work before anything happens.

**The one job.** Type one goal. A Retrieval Agent reads the Knowledge Box and calls this app's own tools (two demo tools, dry-run) over MCP. The trace shows every step, tool call and cited document, then the result and the action it would take.

**Why ARAG is load-bearing.** The Retrieval Agent is ARAG's (configured on the data-platform host; the app runs no planner, Definition of Pass D27). This app exposes tools over MCP (`reference/mcp-rao/`) and forwards the user's JWT (`reference/skill-rao-workflow/`). Remove ARAG and this is function calling with no evidence.

**Base.** The chassis (`CHASSIS.md`): `app.py`, `arag.py`, `static/`, `product.json`. Add product routes under `# --- product routes` in `app.py` and a panel in `static/`. Nothing in the chassis is rewritten.

**Knowledge Box.** New KB seeded with an operations policy set; a Retrieval Agent configured in the console pointing at it and at this app's MCP endpoint.

**Finishing steps, in order (one Copilot chat each).**
1. Tools: copy `reference/mcp-rao/python/mcp_server.py` into the app; define `lookup_order(id)` and `create_ticket(summary)` over `data/demo.json`; `create_ticket` is dry-run unless `ALLOW_WRITES=1`.
2. Agent: configure the Retrieval Agent to use this app's MCP endpoint and the KB, following `reference/skill-rao-workflow/SKILL.md`. This is the one step done in the console, not the repo; record the agent id in `.env`.
3. Route: `/api/run` posts the goal with the forwarded token and streams trace events (shape in `reference/operator-server/`).
4. Trace UI: a step list (thought, tool call with arguments, documents cited) above the result; a dry-run banner.
5. Seed the KB with a small operations policy set and `data/demo.json` with ten orders and five units.

**Done when** (these lines are section 0 of `STANDARD.md`; every (B) line there must also be done):
- One goal produces at least one tool call and one cited document in the trace.
- Dry-run shows the ticket it would raise without raising it; `ALLOW_WRITES=1` raises it into `data/demo.json`.
- The browser never calls the agent or the KB directly.
- 390 px render clean.

**Deliberately not built (the article's "where to take it next").**
- More tools: calendar, ERP, email
- Approval step before any write
- Memory across runs per user

**Copilot prompts.** `/finish-starter` for each step above, `/qa-gate` at the end, `/write-article` last. Cheapest model for renames and copy; the premium model only for the step marked hardest in `README.md`.

**Token rule.** Copy from `reference/` and the chassis; never generate a client, a renderer or a Dockerfile. If a step needs a mechanism not confirmed in `.github/instructions/arag-api.instructions.md` or `reference/arag-platform-quirks.md`, stop and flag it; do not invent an endpoint.
