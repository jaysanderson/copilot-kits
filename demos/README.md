# ARAG demo kit

Copyable Progress Agentic RAG (ARAG) demo-app scaffolds, harvested from working builds. GitHub Copilot customisation lives in `.github/`. The bar is `DEFINITION-OF-PASS.md`.

## What is here
| Folder | Use it when |
|---|---|
| `templates/minimal-proxy` | One `/api/answer` route, vanilla `static/chat.js`, multilingual, embeddable widget (`embed.py`), `predeploy_check.py`. Fastest public-site demo. |
| `templates/fastapi-static` | FastAPI plus httpx proxy (`arag.py`), vanilla static, several routes, crawl and provision scripts. A knowledge desk over a public site. |
| `templates/dealer-dms` | FastAPI with a system-of-record seed (`seed.py`), corpus manifests and media. Structured plus unstructured fusion; operations or ISV-embed demo. |
| `templates/portal` | Vite, React, TypeScript, Tailwind, Radix, Kendo; Express proxy in `portal/server`, `src/lib/arag.ts`, `Citations.tsx`, `theme.ts`, `docs/ARAG-API.md`. Rich multi-route workbench. |
| `templates/kb-pipeline/{python,node}` | Scrape or generate a corpus, provision a KB, ingest, configure refusal and search configs, verify. Used by `/provision-kb`. |
| `templates/mcp-rao` | An app `/mcp` server for ARAG's own Retrieval Agent (Python and Node). Agent-over-business-data demos. |
| `templates/widget`, `templates/concierge-widget` | Embeddable iframe ask widget, and a persistent multilingual concierge with inline citations. Add to any template. |
| `tools/` | `demo_qa_gate.py`, `estate_health.py`, `brand_capture.py`, `shot.py`, `clone_kb.py`, `predeploy_check.py`. |
| `brand/` | `progress-official.json`, `progress-hyperframes-brand.md`, Progress Sans fonts, the real Progress logos, `LOGO-SLOTS-README.md`. |
| `reference/` | The source skills, agent definitions and the full Definition of Pass. Read, never edited. |

## Start a project
1. Copy one template folder to your project path, or run Jay's harvest script, which does the copy and the name swap.
2. Open the folder in VS Code with Copilot. The always-on rules load from `.github/copilot-instructions.md`; file-scoped rules load when you touch matching files.
3. Run `/new-demo` in Copilot Chat and answer its inputs one at a time. It hands off to `/provision-kb`, `/qa-gate`, `/capture-shots` and `/locked-brief` as steps.
4. Fill `.env` from the template's `.env.example`. Nothing else holds a credential.

## Token discipline (Copilot is billed per token)
- Always-on instructions stay under 60 lines. Recipes live in `.github/prompts/` and load only when invoked.
- Copy, do not generate. The templates already have the ARAG client, chat UI, citation renderer and Dockerfile.
- One task per chat. Start a new chat for the next task.
- Mechanical edits (renames, token swaps, copy) go to the cheapest model. Use the strongest model only for research and QA judgment calls.
- Pin the cheapest capable ARAG model on every call and estimate before any corpus-wide run.

## Hygiene
- Never commit `.env`. Commit `.env.example` with empty values only. Every template's `.gitignore` lists `.env`.
- Never paste a token, KB id or zone host into chat, README, config or a prompt file. Refer to env var names.
- Never open or copy a `.env` from `templates/` or `reference/`.

Notes (14 Nov 2026): templates/widget is the whole web/ folder of the experience site (widget.html, js/widget.js and the modules it imports). templates/portal is missing portal/public/brand/progress-arag-logo.svg and -alternate.svg because those two files are deny-read for this Windows account in the source; drop the logos from brand/ in their place before building. The ARAG platform quirks extracted from the old rulebook are in reference/arag-platform-quirks.md (447 lines): read on demand, never load into always-on instructions.
