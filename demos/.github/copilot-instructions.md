# ARAG demo kit - always-on rules

## What this repo is
- Copyable Progress Agentic RAG (ARAG) demo-app scaffolds under `templates/`, shared tools under `tools/`, brand assets under `brand/`, source material under `reference/`.
- A new demo starts by copying one template folder, then swapping brand, Knowledge Box (KB) and app name. Never write a new ARAG client, chat UI, citation renderer or Dockerfile; the templates carry working ones.
- Read the chosen template's README and its `arag.py` or `src/lib/arag.ts` before proposing any code.

## Secrets and the call path
- ARAG is called server-side only. The browser talks to this app's own `/api/*` routes; the app calls ARAG with `X-NUCLIA-SERVICEACCOUNT: Bearer <token>`.
- Token, KB id and zone host live in `.env` (gitignored) or Fly secrets. Never in client JS, `demo.config.json`, logs, README or git.
- `.env.example` documents every key with an empty value. Never paste a real token, KB id or zone hostname into any file; refer to the env var name.

## Build gates (each is pass or fail)
1. All AI answer text renders through the template's markdown renderer (`static/mdlite.js`, `src/lib/markdown.ts` or `answer-render.js`). Literal `**`, `#` or `[text](url)` on screen is a FAIL.
2. Every outbound HTTP call carries an explicit timeout. No timeout is a FAIL.
3. A documented reset that runs in about 30 seconds exists (`seed.py --purge` or `scripts/reset.py --purge` style) and is in the README.
4. Every route passes at a real 390x844 mobile render and at 1440x900. Menus and modals are opaque; nothing overlaps content.
5. No hosting-region, zone or infra string in any customer-facing view or screenshot.
6. Other customers' names and identifiers are anonymised; fictional people and brands only.
7. `fly.toml` keeps `min_machines_running = 1`. Never 0.
8. Every citation is clickable and opens the source at the cited passage.

## Cost rule
- Pin the cheapest capable generative model on every `/ask` and every DA task via env var (templates default to a flash or mini tier). Never inherit a KB default.
- Before any corpus-wide run (graph, labeler, generator) write the estimate: resources x paragraphs x per-call price. Over a few dollars: stop and report the figure.

## Verification rule
- A check that skips itself, or cannot fail, is a FAIL. Run a tool's selftest first (`tools/demo_qa_gate.py` and `tools/estate_health.py` have one).
- PASS needs evidence in the reply: a screenshot path you viewed, grep output, a URL you opened, or the live response body. "Looks fine" is a FAIL.

## Language
- Australian English. No em dashes; use a spaced hyphen " - ".
- Banned words: delve, leverage, unlock, seamless, game-changing. Grep for them before finishing.

## Working style
- One task per chat. State the task in one line, do it, report evidence.
- Read the template before proposing code. Copy, do not generate.
- Mechanical edits (renames, token swaps, copy) go to the cheapest model available.
- Recipes are prompt files: `/new-demo`, `/provision-kb`, `/qa-gate`, `/capture-shots`, `/locked-brief`. Agents: `qa-reviewer`, `demo-tester`.
