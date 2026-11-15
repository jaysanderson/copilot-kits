# ValueCase - always-on rules (starter 10 of the ARAG series)

## What this repo is
- One small, finished product on Progress Agentic RAG (ARAG). `BRIEF.md` is the plan; `README.md` is the promise; `ARTICLE.md` is the post. Read `BRIEF.md` before any code.
- Base: The app is the finished value-case tool, copied whole (FastAPI, SQLite, exports, scenarios, sensitivity). It has no ARAG client yet; that is the finishing touch.
- Copy, do not generate: clients, renderers, Dockerfiles and pipelines already exist in this repo. Point at the file to copy.
- The three items under "Where to take it next" are deliberately unbuilt. Never build them.

## Secrets and the call path
- ARAG is called server-side only. The browser talks to this app's own `/api/*` routes; the app calls ARAG with `X-NUCLIA-SERVICEACCOUNT: Bearer <token>`.
- Token, KB id and zone host live in `.env` (gitignored) or Fly secrets. Never in client code, logs, README, ARTICLE or git. `.env.example` has empty values.
- No zone, KB id, `/ask`, `/find` or `Knowledge Box` string in any customer-facing view; the How this works panel is the only place mechanics appear.

## The standard
- `STANDARD.md` is what finished means: sections 0 to 6, blockers marked (B), a status column. Nothing ships or posts with an open (B) line.
- Order: `/finish-starter` per BRIEF step, then `/audit-standard` once, then `/raise-standard` per open line, then `/qa-gate` on the live URL, then `/write-article`.
- `python smoke_test.py` must pass before and after every change to `app.py` or `arag.py` (base apps: the equivalent test named in STANDARD C5).

## Gates (the short list; STANDARD.md is the full one)
1. All AI text renders through the markdown renderer in this repo. Literal `**` or `#` on screen is a FAIL.
2. Every outbound HTTP call has an explicit timeout.
3. Every citation is clickable and opens the source at the cited passage, page or second.
4. Every route renders clean at 390x844 and 1440x900; `scrollWidth === 390`.
5. Confidence is a qualitative badge, never a raw numeral; a withheld answer carries no sources.
6. Fictional people and brands only; the footer discloses synthetic content.
7. `fly.toml` app name is changed from `CHANGE-ME-*` before any deploy; `min_machines_running = 1`.

## Cost rule
- Pin the cheapest capable generative model via env var on every call. Before any loop over a corpus, print the estimate (items x calls) and stop above a few dollars.

## Verification rule
- A PASS needs evidence in the reply: a screenshot viewed, grep output, a response body, a URL opened. "Looks fine" is a FAIL. A check that cannot fail is a FAIL.

## Language
- Australian English. No em dashes; a spaced hyphen " - ". Banned words: delve, leverage, unlock, seamless, game-changing.

## Working style
- One step of `BRIEF.md` per chat. State the step, do it, show evidence, stop.
- Mechanical edits go to the cheapest model. The premium model only for the step `README.md` calls hardest.
- Prompts: `/finish-starter`, `/audit-standard`, `/raise-standard`, `/qa-gate`, `/write-article`, `/provision-kb`, `/capture-shots`. Agents: `qa-reviewer`, `demo-tester`.
