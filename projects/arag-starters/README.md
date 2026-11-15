# arag-starters

Ten Copilot-ready projects, one per folder, each a small finished product on Progress Agentic RAG with a LinkedIn article to match. Harvested on 15 Nov 2026 from the PMK-1 corpus so that Copilot copies instead of generating.

## How to use one
1. Open the folder (for example `01-answergap`) in VS Code. Nothing else in this tree needs to be open.
2. Read `BRIEF.md` (two minutes). It has the problem line, the one job, why ARAG is load-bearing, the finishing steps, done-when and the three extensions you must not build.
3. `cp .env.example .env` and fill the Knowledge Box values. Run it (`README.md`).
4. In Copilot chat: `/finish-starter`. One step per chat. Evidence each time.
5. `/qa-gate` when the done-when lines pass. `/write-article` last. Record the 45-second clip.

## What is in every folder
- `.github/` - a 50-line always-on rulebook, on-demand prompts (`finish-starter`, `audit-standard`, `raise-standard`, `qa-gate`, `write-article`, `provision-kb`, `capture-shots`), two agents.
- `brand/` - Progress tokens, logos, fonts. Neutral product brand by default.
- `BRIEF.md` (the plan), `STANDARD.md` (what finished means, with blockers and a status column), `README.md`, `ARTICLE.md`, `tools/` (shot, gate, predeploy check), `.gitignore`, `.env.example` (empty values).
- Either the chassis (`app.py`, `arag.py`, `static/`, `product.json`, `CHASSIS.md`) or a finished app copied whole, plus `reference/` with the exact modules to copy from.

## The series
`SERIES.md` (the ten problems and who shares them), `BUILD-ORDER.md` (build order, token rules, pre-publish checks), `ARTICLE-SKELETON.md`, `_chassis/` (the shared starter, kept here as the master copy).

## Hygiene
No `.env`, token, KB id, account id or zone host is in this tree; `.env.example` files were blanked on copy. Fly app names are `CHANGE-ME-<slug>` on purpose. Synthetic data only; the source demos' fictional customers still appear in some copy and are named in each BRIEF's purge step.
