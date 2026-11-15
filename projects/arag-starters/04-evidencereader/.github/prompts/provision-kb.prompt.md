---
mode: agent
description: Collect a corpus, provision a Knowledge Box, ingest and verify it with the kb-pipeline scripts
---

# Provision a Knowledge Box

Scripts: `templates/kb-pipeline/python/` (scrape_site, audit_corpus, provision_kb, ingest, build_resource_cache, generate_catalog_copy, verify) or `templates/kb-pipeline/node/` (create-kb, provision, ingest, create-retrieval, configure-refusal, create-da-agents, verify). Read a script's docstring before running it; each records what it corrected. Credentials come from `.env` only.

## 1. Collect
- Public site: `scrape_site.py` (real browser, sitemap-driven), then `audit_corpus.py`: drop thin pages, nav boilerplate, duplicates and utility pages (privacy, terms, sitemap, contact). Record the before and after counts.
- Synthetic corpus: write it from `research/<slug>.md`. Fictional people and brands only. Keep entity names out of compound titles. Trademark-check invented names.
- Done when: a corpus folder plus manifest exists and the exclusion list is written down.

## 2. Provision
- New KB: `provision_kb.py` or `node create-kb.mjs --title <t> --slug <s>`. It writes the KB coordinates to `.env`. Never print them, never commit them.
- Register labelsets for the facets the app uses (doc type, site, audience, lifecycle). Register one named search configuration per app surface with the friendly decline wording and a completeness instruction in its system prompt (`configure-refusal.mjs`, `create-retrieval.mjs`). Pin the generative model in the config.
- Done when: `GET /kb/{id}/labelsets` and `GET /kb/{id}/search_configurations` list what you registered.

## 3. Ingest
- Text: `POST /kb/{id}/resources` (`ingest.py` or `ingest.mjs`). Binaries only: `POST /kb/{id}/upload`. Apply labels at creation.
- Do not start any graph, labeler or generator task yet; a task registered before ingest completes stalls all processing.
- Poll `metadata.status` with a 15 minute budget. Reconcile the PROCESSED count with the count sent.
- Read three resources back with `show=extracted&extracted=text`; confirm title and prose are yours, not a hash or JSON.
- Done when: PROCESSED count equals sent count and the readback is clean.

## 4. Augment (only after every resource is PROCESSED)
- Estimate first, in the chat: resources x paragraphs x per-call price. Over a few dollars: stop and report.
- Pin `llm.model` on every task to the cheapest capable tier. Register with `apply=EXISTING`. Count real output afterwards; `completed: true` is not coverage.
- Graph coverage short? Set `top_k: 500` and `undirected: true` before re-running anything.
- Done when: each task shows output on a sampled resource and the cost estimate is in the README.

## 5. Verify
- `verify.py` or `verify.mjs`: resource count reconciliation, readback, eight real `/ask` probes plus one out-of-corpus negative control that must decline.
- First `/ask` after ingest: retry with backoff. `/find` working does not prove `/ask` grounds yet; allow 10 to 15 minutes on a fresh KB.
- Done when: every probe returns a cited answer, the negative control declines, the model is pinned, and no credential appears outside `.env`.
