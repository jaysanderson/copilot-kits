---
mode: agent
description: Clone a template into a new ARAG demo and deploy it
---

# New demo from a template

Work one step at a time. Report evidence after each step before starting the next.

## Inputs (ask for any that are missing, one question at a time)
1. Prospect name, or "generic" plus the vertical.
2. Vertical and five use cases (one route each). Fewer than five: propose adjacent ones.
3. Template: `templates/minimal-proxy` (one answer route, multilingual, embeddable widget), `templates/fastapi-static` (FastAPI, several routes, vanilla static), `templates/dealer-dms` (FastAPI with a system-of-record seed and corpus manifests), `templates/portal` (Vite, React, TypeScript, Tailwind, Radix, Kendo, Express proxy).
4. Knowledge Box: new (provision) or existing (env vars supplied by Jay). Zone and account come from env; never ask for them in chat.
5. Fly app name (`<slug>.fly.dev`) and whether a GitHub repo is wanted.

## Step 1 - Research (before any code)
- Named prospect: from the project folder run `python tools/brand_capture.py <domain>`; read the `brand/<slug>-home.png` screenshot and `brand/brand.json` it writes. Match the site's default rendered state (light or dark), not only the tokens.
- Classify the prospect: ISV (embed or OEM story) or operating company (ARAG inside a mock of their own system).
- Collect the real vocabulary, document types, roles and identifiers for the vertical. Write them to `research/<slug>.md`. The seed corpus is built from this file.
- Done when: `research/<slug>.md` lists five diverse use cases with the document types each needs.

## Step 2 - Copy and swap
- Copy the template folder to the project path Jay gives. Never edit the template in place.
- Swap, by grep then edit: app name and fly `app =`; brand tokens in the template's token file (`brand/tokens.css`, `static/css/*.css`, `src/lib/theme.ts` or `demo.config.json`); logo files; page copy; suggested questions and chips; footer synthetic-content line; the `How this works` text per route.
- Grep for the source demo's names (clinic, ignition, coppermill, revolution, university, publisher, studycity, cartwright) and purge every hit, including `/r/` detail pages and reveal specs.
- Write `.env.example` with every key the app reads, values empty. Confirm `.env` is in `.gitignore`.
- Done when: the grep returns nothing outside `reference/`, and the app starts locally against `.env`.

## Step 3 - Knowledge Box
- Run `/provision-kb` for a new KB, or bind the existing one through env vars.
- Done when: a scoped `/ask` returns a cited answer from this corpus and an out-of-scope question declines.

## Step 4 - Seed and reset
- Make the reset work end to end (`seed.py --purge` or `scripts/reset.py --purge`). Time it. Write the command and the time in the README.
- Done when: purge and reseed run clean and the script regenerates every id-keyed file itself.

## Step 5 - Local gate
- Run the app. Shoot every route at 1440x900 and 390x844 with `python tools/shot.py --url <url><route> --out qa/<route>-<width>.png` and view each shot.
- Ask a multi-item question and read the rendered prose. Click every chip and citation.
- FastAPI templates: `python tools/predeploy_check.py` from the app root must print `subset import ok`; run `--control` once and it must FAIL.
- Done when: every shot viewed, zero console errors, predeploy check passes and its control fails.

## Step 6 - Deploy
- `flyctl apps create <slug>`, `flyctl secrets set` for every key in `.env.example`, `flyctl deploy`. Keep `min_machines_running = 1`.
- Done when: every route returns 200 on `https://<slug>.fly.dev` and a typed question answers in a real browser.

## Step 7 - Independent gate
- `python tools/demo_qa_gate.py --url https://<slug>.fly.dev --routes <every route> --json qa/gate.json` must exit 0. Then run `/qa-gate`.
- Add the demo to `tools/estate_health.py` `TARGETS` with its real answer route.
- Done when: gate exit 0, `/qa-gate` reports no critical, blocker or major, and the README carries the narrative, the reset, and the list of which real ARAG call powers each capability.

## Never
- Write a new ARAG client, chat UI, citation renderer or Dockerfile.
- Fake, mock or pre-can a capability. If ARAG cannot do it, remove it or disclose it in the reveal.
- Put a token, KB id or zone host anywhere but `.env` or Fly secrets.
