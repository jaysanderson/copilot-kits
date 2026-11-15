---
name: arag-kb
description: Provision and populate a Progress Agentic RAG Knowledge Box and query it correctly - with the eleven API gotchas that each cost real hours to find (graph-before-ingest stalls all processing, scope every query, pin the model, citations vs schema, audio timestamps, strict schemas, DA task model pinning, DA output field-key naming, the DA Generator JSON-schema platform bug, one stuck resource 500ing the whole KB, PROCESSED-status vs. actually-searchable lag) - plus the search-configuration no-answer message that delivers a friendly, on-brand honest decline instead of a hardcoded refusal string. Use whenever a demo/app needs a KB stood up, seeded and queried. Self-contained.
---

# Provision, seed and query an ARAG Knowledge Box

**Prerequisites (set up once):** an ARAG/Nuclia account with KB-management rights and a credential
you can mint tokens with; a way to make HTTP API calls (curl / a script). Note which **zone(s)**
your credential can provision in - it governs residency (see the zone note below).

## Provision
- A KB is created under an account, in a zone, via the account KB-create API; then mint a service
  token (owner-scoped) to read/write it. Keep the account id, host and token; the token is a
  Bearer service-account key used as `x-nuclia-serviceaccount: Bearer <token>` (or per the
  current spec). Store server-side only.
- **Zone matters for residency.** If your credential provisions in only one zone, the `zone`
  param on create may be ignored - the KB lands in that zone regardless. Don't host a
  residency-sensitive live demo on a wrong-zone KB (a visible host string fails the demo gate);
  use a region-correct KB or get a region-appropriate key first.

## Seed / ingest
- **PICK THE RIGHT ENDPOINT, and this one silently corrupts a whole corpus if you get it wrong
  (Studycity, 29 Sep 2026).** `POST /kb/{id}/resources` with `title` + `texts.body.body` +
  `origin.url` for TEXT you are supplying yourself. `POST /kb/{id}/upload` ONLY for a genuine
  binary (PDF, image, audio, video). Posting a JSON resource-creation payload to `/upload` does
  NOT error - it accepts the JSON as a generic file, OCRs the raw JSON as though it were the
  document, and sets every resource title to a random hash. **Retrieval still works**, so a smoke
  test passes: answers come back and citations resolve. What breaks is invisible until it is
  expensive - the real ARAG console shows hundreds of hash-titled resources (the exact console
  walkthrough the sales motion depends on), and citation-highlight offsets index into the JSON
  rather than the prose, so highlights land in the wrong place. A 234-resource corpus had to be
  purged and re-ingested.
- **VERIFY THE TITLE, not just that retrieval answers.** After any ingest, read a few resources
  back and confirm the title is what you set and the extracted text is the real prose. Use
  `show=extracted&extracted=text` TOGETHER - `show=values` alone returns only the file pointer
  with no text, which looks like success and contains nothing.
- Poll each resource's status and **wait for `PROCESSED`** before caching goldens or enabling any
  augmentation - a resource that's still `PENDING` returns nothing. Reconcile the PROCESSED COUNT
  against what you sent; a completion status is not coverage.
- Synthetic/public content only for demos; fictional participants; badge anything invented.
- **A GENERATIVE SUMMARISER FABRICATES BY MERGING TWO TRUE FIGURES (29 Sep 2026).** Card copy over
  a page stating undergraduate fees of AUD 25-45k and postgraduate fees of AUD 30-50k produced
  "AUD 25,000-50,000" - a range appearing nowhere on the source, misstating both. Every component
  number was real; the combination was invented, and no citation check catches it because the card
  still cites the right page. Any prompt generating copy over numeric content must forbid merging,
  spanning or combining separately-stated figures, and QA must spot-check generated NUMBERS
  against the source page, not merely confirm a source exists.

## The seventeen gotchas (each cost real time - do these right the first time)

**0. COST SAFETY FIRST (binding, CLAUDE.md hard rule 15 - a real US$25,000 incident).** Graph
extraction and every ingest-time DA task run an LLM call PER PARAGRAPH across the WHOLE corpus,
so cost = per-call model price x corpus size. **ALWAYS pin the cheapest CAPABLE model** (mini /
flash / haiku / lite tier - e.g. a `*-mini`, Gemini `*-flash` or Haiku-class model) on the graph
task, on every DA task, and as the KB's generative model - NEVER a premium/frontier model over a
corpus, and never blindly inherit a KB's premium default. For a demo the output only has to be
good enough to SHOW. Estimate cost (resources/paragraphs x per-call price) before ANY corpus-wide
run; if it is not a few dollars, STOP and flag the estimate to Jay. Scope graph extraction to the
smallest subset that makes the point, not the whole dataset. This governs gotchas 1, 3 and 7 below.

1. **NEVER enable an llm-graph / augmentation task BEFORE ingest completes - it stalls ALL
   processing.** Order: ingest -> wait for every resource `PROCESSED` -> THEN add the graph/
   augmentation task, applied to existing content (`apply=EXISTING`). If you already stalled it:
   delete the task, `/reprocess` each resource, then re-run the task after PROCESSED.
2. **Hard-scope EVERY `/ask`, `/find` and REMi call to this KB's own resources via
   `resource_filters`** (or the current scoping mechanism). A single KB can hold several demos'
   content; an unscoped query leaks another demo's data into the answer. Scope by the resource ids
   / labels belonging to THIS demo.
3. **Pin the generative model on every call.** A fresh KB's default generative model may refuse
   everything - set `generative_model` explicitly (e.g. a known-good chat model). Compose/
   augmentation tasks that use a custom user template MUST keep the `{context}` placeholder or
   grounding breaks; the `prompt` field is system-only - a custom `prompt.user` without `{context}`
   silently drops the retrieved context.
4. **NEVER send `citations: true` AND `answer_json_schema` in the SAME `/ask` call - it crashes
   the backend (500/503), not a clean error** (reproduced 3/3 live, 17 Aug 2026). They are
   mutually exclusive in practice. For provenance in schema mode, two workarounds: (a) read the
   `retrieval_results.resources` block, which IS populated even with `citations: false`, or
   (b) fire a second parallel `/ask` with `citations` on and no schema. If you need both a cited
   answer AND a structured result, run them as two separate calls.
5. **`/ask` drops `start_seconds` on audio results.** For clickable transcript timestamps, get the
   timestamps from `/find` and merge them into the answer's citations.
6. **Strict answer schemas need EVERY property in `required`.** A strict `answer_json_schema` with
   optional properties can fail validation; list every field as required (use empty/nullable
   values rather than omitting).
7. **Every Data Augmentation task needs its own `llm.model` pinned explicitly, separately from
   gotcha 3.** This is a different failure mode from the `/ask`-call model pin above: an
   unpinned DA task (Labeler, Generator, etc.) returns a clean 200 on `task/start` and looks
   registered fine, then fails silently during actual execution with no obvious error surfaced -
   easy to mistake for a content or schema problem when it's really just a missing model pin.
8. **DA-generated output is NOT stored under the plain destination field key you registered.**
   Nuclia stores it as `da-<destination>-f-<fieldId>` - reading back the plain destination
   string you specified will silently return nothing. Check the resource's actual field list to
   get the real key before writing any code that reads DA-generated output.
9. **The DA Generator's *ingest-time task* JSON-schema output path is a known, confirmed platform
   bug - don't burn time on schema variants. This is a DIFFERENT mechanism from the WORKING
   query-time `/ask` `answer_json_schema` path (see "Structured JSON answers" below) - only the
   ingest-time task path is broken, not all JSON output.** This gotcha is about registering a
   Generator DA *task* (`task/start` with `json:true` / `store_as_key_value` + `kv_schema_id`) so
   it emits structured fields per resource at ingest time. Confirmed 5 Aug 2026, retested live and
   still broken 17 Aug 2026 (same 422 `Invalid JSON schema... Expecting value: line 1 column 1`):
   neither the `kv_schema_id` path nor an OpenAI-style function/tool-calling schema shape
   (`name`/`description`/`parameters`) works - a `kv_schema_id` created from a fully-populated
   schema is silently stored with zero fields, and referencing it in a task 422s identically
   regardless of schema shape or content. The 422 is in the task-execution code path, not a
   schema-shape problem on your side. This is the platform, not your config - see CLAUDE.md's
   "Known live platform fragility" note. Build the honest fallback: a plain-text `ask`-type DA
   task with a strict labelled-line output format, parsed server-side. **If you need structured
   JSON, use the query-time `/ask` `answer_json_schema` mechanism below instead of the DA task -
   that one works.**
10. **One resource stuck `ERROR`/`PENDING` in the processing queue can 500 `/ask` and `/find`
    across the ENTIRE KB, not just for that resource.** Found live 6 Aug 2026 (bioscience-demo):
    4 recently-ingested resources stuck mid-queue caused every unfiltered `/find`/`/ask` call to
    500; scoping the query away from that doc type worked instantly, proving the KB itself, not
    app code, was the failure point. Triggering `/reprocess` on the stuck resources did not clear
    them within several minutes, and resource deletion has no sanctioned MCP write path (and is a
    destructive action on a live shared KB regardless). **The honest workaround: add a
    `{none: [...]}` exclusion filter on the stuck resource ids to every `/ask` and `/search` call**
    as a resilience guard, remove it once the resources actually clear. If you hit a KB-wide 500
    on `/find`/`/ask` that isn't reproducible on a single scoped resource, check for stuck
    ERROR/PENDING resources first before assuming it's an app-side bug.
11. **A resource's `metadata.status == PROCESSED` does not mean it is reliably reachable by `/ask`'s
    retrieval-scored search yet.** Found live 7-8 Aug 2026 (akademdocs-precheck): under concurrent
    page/resource processing, a page that classified correctly in isolation came back `UNRECOGNISED`
    when run as part of the full pipeline - the resource had flipped to `PROCESSED` several seconds
    before it was actually indexed for retrieval, so an immediate `/ask` against it missed. This is
    a distinct failure mode from gotcha 10 (a genuinely stuck resource poisoning the whole KB) - here
    the resource finishes fine, the *status flag* just lags the real searchable state. **Fix: wrap
    the first `/ask` after ingest in a retry-with-backoff, and add a short buffer delay after
    `PROCESSED` before the first query** - reproducibly stable once added. If a resource looks
    correctly processed but its content intermittently doesn't show up in results right after
    ingest, suspect this lag before assuming a classification or scoping bug.
12. **`/find` and full `/ask` grounding can lag ingest by 10-15+ minutes on a fresh KB -
    much longer than `metadata.status` implies, and longer than most build scripts wait.**
    Found live 2 Sep 2026 (Bay-co Bay build, confirmed on TWO independently provisioned
    fresh KBs): right after ingest, `/find` returns real, correctly relevant results almost
    immediately, which reads as "the KB is ready." But `/ask` (which needs the paragraph-
    level augmented context, not just a resource-level match) kept returning `no_context` /
    `no_retrieval_data` on completely reasonable questions for the first ~11 minutes, on a
    trivially small 32-document corpus - then, with zero intervention, flipped to grounding
    5/5 and stayed stable from t+~11min onward. `metadata.status` on the resources tracked
    the SAME slow timeline, not a separately-broken field - it read `PENDING` for the whole
    slow window and only flipped to `PROCESSED` once grounding actually stabilised too. (An
    earlier version of this gotcha, written mid-investigation with only ~15 min of data,
    concluded the status field was permanently stuck/wrong while the KB was "actually fine"
    - that was premature; waiting longer showed status and grounding recover together.)
    **Practical fix: don't gate a build on a short timeout assuming `PROCESSED`-or-broken.**
    Poll `metadata.status` with a genuinely long budget (15+ minutes is not unreasonable for
    a fresh KB) rather than a 2-3 minute one. If you need a faster signal, `/find` returning
    results is real evidence the KB isn't dead, but it is NOT evidence `/ask` will ground yet
    - don't treat a working `/find` as proof `/ask` is ready, and don't conclude a KB is
    platform-broken from an `/ask` failure in the first ~10 minutes after ingest. Before
    escalating an "/ask never grounds" finding as a platform blocker, always re-test after a
    realistic wait (empirically, 10-15 min on a small corpus) - it may simply still be
    indexing.
13. **`POST /kb/{id}/task/start`'s payload has NO top-level `parameters` wrapper - `name`,
    `on`, `operations`, `llm`, `filter` all sit at the top level, and a wrong wrapper is
    silently accepted, not rejected.** Found live 2 Sep 2026 (Bay-co Bay backend-breadth
    fix): a Labeler task registered with everything nested under a `parameters` key returned
    200/201, ran to `completed: true, failed: false` in a realistic ~3 minutes, and classified
    **zero of 32 resources** - because `operations`/`llm` inside the nonexistent `parameters`
    wrapper were silently dropped as unrecognised extra fields, so the task actually ran with
    an empty operation list against every resource and trivially "succeeded" at doing nothing.
    No error at registration time, no error at completion time - only counting the real output
    (gotcha about `completed:true` above) exposed it. **Get the real top-level shape from `GET
    /kb/{id}/tasks` -> `tasks[].validation.properties` before registering** (this is the
    correct source of truth for the CURRENT top-level fields - do not assume a wrapper key from
    an older working example, the shape can differ from what you'd guess). Sending an actually-
    unrecognised top-level key (confirmed by testing bare `on`/`operations`/`llm` with no
    wrapper) 422s with an explicit `extra_forbidden` error, which is the useful signal: if a
    payload is rejected outright, the SHAPE is at least being validated; if it's silently
    accepted and does nothing, suspect a wrapper-key mismatch that made your real fields
    invisible to that validation.
    **CORRECTION (found live 3 Sep 2026, Auto-co backend-breadth fix): `GET /kb/{id}/tasks`
    is NOT a reliable source of truth for `POST /task/start`'s real shape - the two can
    disagree on the SAME KB.** On this KB, `GET /tasks` -> `tasks[].validation.properties`
    reported the exact wrapper-free shape this gotcha describes (`name`/`on`/`filter`/
    `operations`/`llm`, no `parameters` key) - but sending that exact wrapper-free payload to
    `POST /task/start` 422d with `extra_forbidden` on `on`/`filter`/`operations`/`llm`, and
    only succeeded once wrapped in a top-level `parameters` key (confirmed two ways: the
    wrapper-free payload 422s as above, and a bare `{"name":"labeler"}` 400s with "Task
    labeler parameters must match the DataAugmentation model" - i.e. the wrapper key really is
    named `parameters` and really is required, on THIS KB, despite what `GET /tasks` says).
    So the original finding's diagnostic ("if wrapper-free is rejected outright, try the
    wrapper") still holds and is the thing to actually trust - but do not skip straight to
    trusting `GET /tasks`'s advertised shape as ground truth; treat it as a first guess, and
    when `POST /task/start` 422s that guess with `extra_forbidden` on your real fields, try the
    `parameters` wrapper next regardless of what the GET response claimed. Two KBs, two
    opposite answers to "does this KB want the wrapper" - the only way to know is to try
    `POST /task/start` itself and read its own validation errors.
14. **`GET /resource/{id}` with an explicit `show=basic,values` (or any explicit `show` list
    that omits it) silently returns `computedmetadata: null`, even when real DA output exists
    there.** Found live 3 Sep 2026 (LLM Economics pipeline rebuild) verifying a labeler task's
    real coverage: the exact same resource returned `computedmetadata: null` with
    `show=basic,values` and the real, populated `field_classifications` (a genuine label) with
    `show=basic` alone or no `show` param at all. This is a trap specifically because it looks
    identical to the OTHER documented gotcha (a task reporting `completed: true` while actually
    classifying nothing) - it cost a needless task re-run before the real cause (the READ
    params, not the write) was isolated. **Always read `computedmetadata` with `show=basic`
    alone, or no `show` param at all - never with `values` appended.**
15. **`show` on `GET /resource/{id}` must be REPEATED query params, never comma-joined**
    (`?show=basic&show=extracted`, not `?show=basic,extracted` - the comma-joined form 422s
    outright). Third variant of the `show=` gotcha family (ignition-dms, 11 Sep 2026).
16. **A resource's `thumbnail` field is a path relative to the ZONAL host - use it as-is**
    (no `/api/v1` prefix manipulation needed); proxy it server-side with the KB
    service-account token for catalogue cards (ignition-dms, 11 Sep 2026).
17. **Score REMi against retrieved paragraphs SORTED BY RERANK SCORE, never dict-iteration
    order** - unsorted, REMi can score a well-grounded answer against an arbitrary off-topic
    paragraph and produce a false low-confidence badge; the failure is intermittent and looks
    like REMi flakiness (ignition-dms, 11 Sep 2026 - stable across 6+ runs after sorting).
## Structured JSON answers at query time (the WORKING mechanism - use this for generative UI)

ARAG has a native, WORKING query-time structured-JSON answer mechanism (verified live 6/6 200s
on `progress-jay-geo`, 17 Aug 2026). This is the mechanism to reach for when a frontend needs to
render rich components programmatically from a structured answer ("generative UI") - NOT the
broken ingest-time DA Generator task (gotcha 9).

- **Endpoint:** `POST {rag-host}/api/v1/kb/{kb}/ask` - the query-time `/ask` call, on the
  **rag-host** (not the dp-host).
- **Auth:** the KB **service-account token**, header `X-NUCLIA-SERVICEACCOUNT`. (Not the account
  NUA key - that is account-level only.)
- **Schema:** pass `answer_json_schema` in OpenAI-function style - a `name` plus `parameters` as a
  JSON Schema object. Verified working with nested arrays and enums.
- **Returns:** a schema-conformant `answer_json` object, grounded in real retrieved content.
- This is the same shape `reference-repos/rwa-intel-demo` ships in production - the reference
  implementation to copy.

**Hard constraint (see gotcha 4):** never send `citations: true` AND `answer_json_schema` in the
same call - it crashes the backend (500/503), reproduced 3/3. For provenance in schema mode, read
the `retrieval_results.resources` block (populated even with `citations: false`), or fire a second
parallel `/ask` with citations and no schema.

**Do not confuse with the DA Generator task json path (gotcha 9)**, which is a separate,
ingest-time mechanism (`task/start` with `json:true` / `kv_schema_id`) and is still broken. If you
read "ARAG JSON output is broken" anywhere, it means that ingest-time task path only - this
query-time `/ask answer_json_schema` path works.

## Search configurations - the friendly, configurable no-answer message (use this, not a hardcoded refusal)

An ARAG **search configuration** on the KB carries a configurable message the platform returns
when a query has **no grounded answer / not enough data** to answer honestly. This is the
sanctioned place to phrase the honest decline - use it instead of a blunt hardcoded string in
app code.

- **Behaviour does NOT change - only the wording.** ARAG still declines honestly and never
  invents an answer it cannot ground; the search configuration only warms and brands the WORDING
  of that decline.
- **Configure the no-answer / not-enough-data message on the search configuration**, then have
  the demo render whatever the platform returns rather than substituting its own copy. A blunt
  hardcoded string like "Not enough data to answer this." is the anti-pattern this replaces (see
  the `arag-demo-app` skill, Standard B22 - a blunt hardcoded refusal is a FAIL there).
- **Bonus: it is genuine, so it shows in the admin console.** Because the friendly decline lives
  in ARAG's own configuration surface, it is real to demonstrate during the solution-architecture
  reveal / console walkthrough - not app-side sleight of hand.
- Check the current spec for the exact search-configuration field that carries the no-answer
  message against a live reference before wiring it; working config beats docs when they disagree.

> **HOW IT IS ACTUALLY DONE - answered by the GM, 26 Aug 2026.** There is no dedicated
> "no_answer_message" field, which is why searching for one found nothing and why an earlier
> version of this section could never name it. **You configure the decline wording through the
> search configuration's PROMPTS - the system prompt and related prompt fields.** You are
> shaping how the model is told to behave when it cannot ground an answer, not filling in a
> canned string. That is also why it shows genuinely in the admin console: it is real prompt
> configuration on ARAG's own surface.
>
> **THE ACTUAL BEHAVIOUR - measured live on a real KB, 26 Aug 2026, four controlled tests.
> It is a THREE-way split, and it corrects the older "short-circuits before the LLM" claim,
> which was wrong.**
>
> The four tests: a zero-relevance query with a search configuration active; a borderline query
> (partial context, insufficient to answer) with the configuration; the SAME borderline query
> with no configuration at all; and a well-grounded query. What they establish:
>
> 1. **The opening sentence is platform-fixed and unreachable.** `"Not enough data to answer
>    this."` leads every `no_context` response whether or not a search configuration exists -
>    proven by the identical wording appearing in the with-config and without-config runs of the
>    same query. An explicit prompt instruction NOT to use that phrasing does not suppress it.
> 2. **But the LLM still runs on a partial-context `no_context` result** - and adds genuine,
>    retrieved-content-aware reasoning AFTER that fixed lead, naming what evidence does exist and
>    what is missing. **This only happens when a search configuration is present**: the identical
>    query without one returned the bare sentence and nothing else. So the prompt configuration is
>    doing real, verifiable work - just never on the opening line.
> 3. **A genuinely zero-relevance query gets no elaboration even with the configuration active** -
>    there is nothing retrieved for the model to reason about.
>
> **What this means for a build.** Configure the prompt: it is load-bearing for the part that
> matters, which is what a partial-context decline actually says. Accept that the leading sentence
> cannot be branded through configuration at all. Handle that one sentence at the UI layer rather
> than surfacing the raw string - not as a workaround for something broken, but because it is a
> fixed platform string with no configuration surface, and the decline decision itself is
> genuinely ARAG's.
>
> **B22 is satisfied by doing both.** A blunt hardcoded refusal across the board is still a FAIL.
>
> Worth keeping as a lesson about this skill rather than about the platform: the original text
> asserted a capability confidently while quietly admitting it could not name the field, and that
> gap survived several builds. When a skill says "check the current spec for the exact field",
> that is a flag that nobody has done it - treat it as unverified until someone has.

## Quality signals
- **REMi (the RAG-triad: answer relevance, context relevance, groundedness) is enterprise-ARAG
  only** - it is NOT available on a lightweight/Context-Box tier. Prove quality there with cited
  sources only; NEVER show a fabricated accuracy percentage. Where REMi exists, it populates its
  health bars only at its max period (e.g. last 30 days).
- **REMi's `answer_relevance` penalises an INCOMPLETE answer, independently of groundedness -
  and the fix is in the search config, NOT a badge reweight (Thornfield, 3 Sep 2026).** A member
  chip ("what monitoring is required before starting doxorubicin...") returned an answer that was
  word-for-word accurate and well-grounded (`groundedness: [5,...]`, scored against the full
  retrieved context) yet badged Low, because `answer_relevance` came back 1 - deterministically,
  4/4 runs. Root cause isolated by freezing the question + context and varying ONLY the answer: the
  generated answer surfaced only ONE of two directly-relevant facts the SAME grounding paragraph
  listed under the same heading (cardiac monitoring, omitting the CBC/neutropenia item), when the
  question asked broadly "what monitoring is required." Give REMi the complete answer (both facts)
  and `answer_relevance` jumps to 5. So `answer_relevance` is measuring COVERAGE/completeness of the
  question, not just on-topic-ness - and a groundedness-primary badge (B34) correctly still won't
  rescue a genuinely incomplete answer. **Fix at the source, honestly:** add a completeness
  instruction to the KB's search-configuration system prompt - "when the retrieved context lists
  more than one relevant fact/step/requirement under the same heading or topic as the question,
  include ALL of them that genuinely answer it, not only the first." A real ARAG-config change
  (visible in the console reveal), applies to every answer, needs no redeploy (the deployed app
  references the search config by name), and tends to improve other answers too. NEVER reweight the
  badge or fake the score to hide an incomplete answer. Distinct from
  REMi-penalises-synthesis (echo-one-source) and REMi-under-scores-non-English - this is the
  answer-omits-a-listed-fact case.

**Citation ATTACHMENT is non-deterministic on a narrowly resource_filters-scoped /ask
(IWTV Contradiction Room, 19 Sep 2026):** with retrieval scoped to one or two resources,
measured 1 in 5 identical repeat calls returned ZERO citations even though
retrieval_results genuinely contained the resource every time. For any surface whose
grounding proof must be deterministic (a per-account/per-scope panel), ground the
provenance display on `retrieval_results` (populated reliably), not on `citations`;
keep citations for broad multi-document Ask surfaces where per-claim markers matter.

**A compound "why X and what Y" question can decline where a single-clause rephrase
answers 15/15 against the identical document (same build):** retrieval on the compound
phrasing missed the doc 3/3. For seeded show-piece questions, keep the DISPLAY question
as authored but send a tuned single-clause `retrievalQuery` override underneath; for
free-form input, ensure the decline path is warm and in-voice since compound phrasings
will genuinely decline more often.

**A compound TITLE merges entities in graph extraction (same build):** a doc titled
"Daniel's Notebook - Armand in the Room" extracted as ONE compound entity, and near-dup
merging then folded the real "Armand" node INTO it - the character never got his own
node. Keep entity names out of compound document titles (retitle + re-ingest fixes it).

## Graph endpoint notes (if you use the knowledge graph)
- `POST /kb/{id}/graph`; `top_k` silently caps (e.g. at 500) - a larger request is truncated, so
  for a full traversal anchor per-entity path queries and merge, rather than one big top_k.
- **The DEFAULT top_k is far below the 500 max - always pass it explicitly (FieldPilot, 12 Sep
  2026).** An unscoped query with no `top_k` returned 50 relations covering 5 of 9 resources;
  the SAME query with `top_k: 500` returned the real 385 relations covering 9 of 9. The symptom
  is identical to "the DA task silently skipped resources" (and to the source-only/undirected
  miss), so it sends you re-running a task that already worked - but the fix is opposite: just
  set the param. Rule of thumb when graph coverage looks short: (1) explicit `top_k: 500`,
  (2) `undirected: true`, (3) only THEN suspect the extraction task itself.
- **`task/start` shape for llm-graph on this deployment (third variant beyond gotcha 13's two):**
  the outer `"name"` is the TASK-TYPE enum (`"llm-graph"`), and the task's own params - including
  their OWN free-text `"name"` - nest entirely under `"parameters"`. Wrapper-free and
  parameters-only shapes both 422 with different errors. Working reference:
  `apps/telerik-kendo-embed/scripts/register_graph.py`.

## Verify
- Every resource `PROCESSED`; a scoped `/ask` returns a grounded, cited answer from THIS demo's
  content only (test that an out-of-scope term returns nothing); the model is pinned; no key
  client-side. Then the artifact using the KB goes through its own gate.

**A purge-and-reseed regenerates EVERY resource id - every app-side artifact keyed by
resource id is silently orphaned (cinema-group, 11 Sep 2026).** A full KB purge +
re-ingest gave all 77 resources new ids, so the app's `teasers.json` (keyed by old ids)
returned blank for every card lookup with no error - a whole-surface regression invisible to
gates that probe answers but not card copy. After ANY purge/reseed: regenerate every
id-keyed derived file (teasers, caches, id->route maps), and spot-check a card/derived
surface actually renders its copy, the same discipline as re-probing suggested chips after a
reseed.
