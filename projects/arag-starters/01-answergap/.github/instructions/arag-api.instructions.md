---
applyTo: "**/arag*.py,**/arag*.ts,**/server/**,**/scripts/**"
description: Progress Agentic RAG REST gotchas for server-side clients and pipeline scripts
---

# ARAG REST rules (server-side code only)

## Auth and hosts
- KB calls: one header, `X-NUCLIA-SERVICEACCOUNT: Bearer <KB_TOKEN>`. Also sending `Authorization` makes the request fail. Strip a pasted `Bearer ` prefix and quotes before use.
- Account PAT and NUA key use `Authorization: Bearer`. Only a PAT creates a KB. A NUA key cannot create a KB; a KB token cannot call the account-level predict route.
- Base URL `https://<zone>.rag.progress.cloud/api/v1/kb/<kb-id>`; retrieval agents live on `<zone>.dp.progress.cloud`. Both come from env vars, never literals.
- Dashboard sessions and PATs expire quickly (about 90 seconds observed). A service-account token is a JWT; on a sudden 401 decode its `exp` before debugging code.

## /ask vs /find
- `/find` is retrieval only (paragraphs with scores). `/ask` retrieves and generates. `/find` returning hits does not prove `/ask` grounds yet; a fresh KB can lag 10 to 15 minutes.
- Set `generative_model` and `reranker` explicitly on every `/ask`, from env vars. Never rely on the KB default.
- Scope every `/ask`, `/find` and REMi call to this demo's own resources with `filter_expression` or `resource_filters`.
- Send `X-Synchronous: true` to get one JSON body (resource creation, uploads, scripted asks). Omit it to stream NDJSON for the UI.
- NDJSON events: `item.type == "answer"` (append text), `item.type == "retrieval"` (index paragraphs by id), `citations` (character spans into the answer keyed by paragraph id). Join citations to the retrieval index for titles and excerpts; group by document.
- A named `search_configuration` is authoritative; drop `prompt`, `rag_strategies` and `top_k` when you pass one.
- Citation attachment is non-deterministic on a one or two resource scope. Ground a per-scope panel on `retrieval_results`, not `citations`.

## Citations vs answer_json_schema
- Never send `citations: true` and `answer_json_schema` in the same call; it 500s. Run two calls, or read `retrieval_results.resources` for provenance in schema mode.
- Beside a schema, `prompt.system` is ignored. Put the instruction in the schema's property `description` fields.
- Schema in OpenAI function style (`name` plus `parameters`). A strict schema lists every property in `required`.

## Filters, facets, graph
- Label filter paths start with `/` (`/classification.labels/<labelset>/<label>`); a missing slash 412s. Normalise in one shared helper.
- Exclude stuck resources with a `{none: [...]}` term in the filter expression.
- Facet counts come from `/catalog` only; `/find` and `/ask` do not aggregate. Prefer the GET form of `/catalog` (the POST form has a recorded cross-tenant leak).
- `/graph`: pass `top_k` explicitly (the default is far below the 500 cap) and `undirected: true` when exploring an entity. Only then suspect the extraction task.
- `GET /resource/{id}`: repeat `show` params (`?show=basic&show=extracted`), never comma-join. `show=values` returns field bodies; `computedmetadata` appears only with `show=basic` alone or no `show`.
- A resource `thumbnail` is a path relative to the zonal host; proxy it server-side with the KB token.

## Ingest and processing
- Text you supply goes to `POST /kb/{id}/resources` with `title`, `texts.body.body`, `origin.url`. `POST /kb/{id}/upload` is for genuine binaries only; JSON posted there is accepted and silently garbles titles.
- After ingest read a few resources back with `show=extracted&extracted=text` and confirm title and prose.
- `PROCESSED` is not the same as searchable. Poll with a 15 minute budget, add a buffer, retry the first `/ask` with backoff.
- One resource stuck in `ERROR` or `PENDING` can 500 `/ask` and `/find` for the whole KB. Check for stuck resources before blaming app code.
- Never start a graph or augmentation task before every resource is `PROCESSED`; it stalls all processing. Register afterwards with `apply=EXISTING`.
- A purge and reseed gives every resource a new id. Regenerate every id-keyed file (manifests, caches, teasers) as the last ingest step.
- `/resources` paginates on `pagination.last`; `/catalog` on `fulltext.next_page`. Both truncate at 50 otherwise.

## Data augmentation tasks
- Pin `llm.model` on every DA task; an unpinned task returns 200 and fails silently at run time.
- The `task/start` payload shape differs per KB: fields at top level or under `parameters`. Try one, read the 422, then the other. Count real output; `completed: true` is not coverage.
- DA output is stored as `da-<destination>-f-<fieldId>`, not the plain destination key.
- The ingest-time Generator JSON-schema path is a confirmed platform bug. Use query-time `/ask` with `answer_json_schema` instead.

## REMi
- REMi exists on enterprise KBs only. Score against the full retrieved context sorted by rerank score, never cited excerpts or dict order. Derive a badge with groundedness primary; never show the raw numeral.
