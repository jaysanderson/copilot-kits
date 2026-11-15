# Reference repos - index

Cloned per Workflow 5's one-time setup (`gh repo clone`), refreshed on "re-mine repos". One
paragraph per repo: what it demonstrates, which ARAG endpoints it calls, its auth pattern, and
reusable modules. This is the OpenEdge-ERP-shaped reference set: SQLite/structured DB + REST
API + web frontend + auto-generated MCP surface, with ARAG's own Retrieval Agent driving that
MCP as the agent (the RAO pattern) so structured ERP data and unstructured KB documents get
mixed in one grounded answer. We do not build an actual OpenEdge platform underneath - these
repos model the same shape (DB + API + MCP) so a demo reads like a real OpenEdge-adjacent
business system without depending on real OpenEdge infrastructure.

## plant-demo-erp (`jaysanderson/plant-demo-erp`, private)
**What it demonstrates:** a full plant/production ERP (Plant-demo Components) - production runs,
quality, traceability, parts, AP - built Python/FastAPI + SQLite (`data/plant-demo.db`), with a
vanilla-JS static frontend (`static/app.js`, `static/shell.html`) consuming its own REST API.
This is the working build referenced throughout `rao-workflow` and `arag-demo-app`; it has an
`APPROVED.md` badge and shipped video (`DAM f5a9c93b...`).
**ARAG endpoints / pattern:** `ai.py` exposes 45 grounded `/api/ai/*` features across three
modes - `kb` (retrieval + cited answer over the plant document set), `erp` (generation grounded
in a live ERP data digest queried at call time), and `hybrid` (retrieval + live digest injected
into generation) - this is the structured+unstructured mixing pattern in its simplest form,
predating the full RAO/MCP agent pattern. `mcp.py` hosts `POST /mcp` (Streamable HTTP,
stateless JSON-RPC 2.0), with the tool catalogue **auto-generated from the app's own OpenAPI
document** - MCP never reimplements business logic, every `tools/call` dispatches back through
the REST handlers in-process (httpx `ASGITransport`), so RBAC/validation apply to agents exactly
as to humans, with the caller's `Authorization: Bearer` JWT passed straight through.
**Auth pattern:** `X-NUCLIA-SERVICEACCOUNT: Bearer <key>` for the KB-scoped `/api/ai/*` calls
(`ai.py`); the MCP surface forwards the end user's own bearer JWT, not a service credential.
**Reusable modules:** `mcp.py`'s auto-generate-from-OpenAPI tool-catalogue pattern and
`tool_name_for()` naming convention; `ai.py`'s three-mode (kb/erp/hybrid) grounding split as a
simpler alternative to a full RAO agent when a lighter build is what's needed.

## maintenanceOS (`jaysanderson/maintenanceOS`, private) + maintenanceOS-web (public)
**What it demonstrates:** a TypeScript/Node ERP for maintenance businesses - accounts, sites,
work orders, quotes, invoices, inventory, employees, vehicles, assets, reports, recurring plans
- Prisma-backed API (`apps/api`) with a separate MCP server app (`apps/mcp`) and a React/Vite
SPA frontend (`maintenanceOS-web`) consuming the API independently. This is the more mature,
production-shaped twin of `plant-demo-erp`'s pattern (`mcp.py` is explicitly documented as plant-demo's
"twin of maintenanceOS mcp-core").
**ARAG endpoints / pattern:** `apps/api/src/lib/arag.ts` + `apps/api/src/lib/aiFeatures.ts` are
the integration surface - "ARAG is the ONLY AI gateway, no OpenAI/Gemini SDKs anywhere" per the
module's own header comment. Wraps `packages/arag-client` (a hand-rolled TS client:
`client.ts`/`types.ts`/`index.ts`) exposing `aragKbFromEnv()`, `aragAgentFromEnv()`,
`aragConfigured()`, `aragAgentConfigured()`. The MCP tool catalogue (`packages/mcp-core`, shared
by both the Streamable-HTTP (`https://your-app.fly.dev/mcp`) and stdio transports) is - like
plant-demo - auto-generated from the API's own OpenAPI document (`/docs/json`), excluding DELETEs,
`/api/system/*`, binary endpoints and the login route; ~60 tools, read + write, no destructive.
**Auth pattern:** env-driven service config - `ARAG_BASE_URL`, `ARAG_KB_ID`, `ARAG_KB_KEY`
(service-account key, WRITER+/MANAGER), `ARAG_AGENT_ID`, `ARAG_AGENT_KEY` (the Retrieval Agent's
own credential) - this is the canonical env shape the `rao-workflow` skill's
`ARAG_AGENT_KEY`/`ARAG_AGENT_KB_ID`/`ARAG_AGENT_BASE_URL` naming is modelled on.
**Reusable modules:** `packages/arag-client` as a drop-in pattern for any TS/Node app needing an
ARAG KB + Agent wrapper; `packages/mcp-core`'s OpenAPI-to-MCP generator; `docs/MCP.md` as the
canonical write-up of the tool-naming convention (`accounts_list_accounts`,
`work_orders_status`, `quotes_approve`, etc.) other builds should match for consistency.

## How this maps to an "Agentic RAG + OpenEdge ERP" demo request
Jay's brief (2 Aug 2026): we do NOT stand up a real OpenEdge platform. We build a demo shaped
like an OpenEdge-style structured-data business system - SQLite (or equivalent), a REST API, a
web frontend consuming that API, and an MCP surface auto-generated from the API - exactly the
plant-demo-erp / maintenanceOS shape above. ARAG's own Retrieval Agent then drives that MCP as the
agent (the `rao-workflow` skill's pattern), mixing the structured ERP data (via MCP tool calls,
RBAC'd through the same REST handlers real users hit) with unstructured data (manuals, policies,
SOPs - a seeded KB corpus) in one grounded, cited answer. Both reference repos above are
directly reusable templates for this - clone the shape, reskin for the target company/vertical,
follow `rao-workflow` for the ARAG-as-agent wiring and `arag-demo-app` for the demo-quality gates
(including the company-research step now required before any named-company build).
