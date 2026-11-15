# ARAG platform quirks (extracted from the PMK-1 rulebook, CLAUDE.md lines 3289-3734, as at 26 Oct 2026)  Measured behaviours, each dated in the text. Read on demand; do not load into always-on instructions. 
### ARAG platform quirks (checkable core; full findings in the lesson)

Credentials: `ARAG_NUA_KEY` + `ARAG_ACCOUNT` are the only two required (fresh KB per
demo; `ARAG_API_KEY`/`ARAG_KB_ID` only for binding a fixed KB); strip trailing
`# comment` text when reading `.env` values. Verify the dashboard account via
`https://rag.progress.cloud/at/progress-jay-geo`, not the `/select` picker. The
account-level NUA key 403s on KB-scoped writes - write through the KB's own
service-account token, whose header needs a literal `Bearer ` prefix INSIDE it
(`X-NUCLIA-SERVICEACCOUNT: Bearer <token>`); without it the platform 403s with
"Invalid Authorization header format", which reads like a scoping problem rather than a
header-shape one. An `ARAG_HOST` that already ends in `/api/v1` 404s when code appends it
again, which reads like a wrong resource id - check the value before debugging the id. (lesson: content/sop/lessons/arag-platform-quirks.md)

Known platform fragility (reported, do not re-diagnose as build-side): dashboard saves
that silently fail to persist (RAO node graph, fresh Retrieval Agent save), and the DA
Generator's `json:true` path, which 422s regardless of schema shape - the honest
fallback is a plain-text `ask` DA task with a strict labelled-line format, parsed
server-side. Query-time structured JSON WORKS: `POST {rag-host}/api/v1/kb/{kb}/ask`
with `answer_json_schema`, authenticated `X-NUCLIA-SERVICEACCOUNT` - but never with
`citations: true` in the same call (backend 500s, 3/3); read
`retrieval_results.resources` or fire a parallel citations-only ask. Detail: the
`arag-kb` skill.

- **Filters:** access scoping goes through `filter_expression`, never the legacy
  `filters` array (silently returns zero on label paths, and a malformed shape fails OPEN
  as no filter at all); `/ask` honours filters less reliably than `/find`, so RBAC-scoped
  answers get a server-side grounding cross-check that withholds anything grounded
  outside the entitlement. Express an entitlement as ONE axis wherever one exists (an OR
  across axes is satisfied by coincidence); sanity-check a scope by listing and READING
  what is inside it. A guard that has never fired is indistinguishable from a broken one -
  plant a positive control (remove the first layer, confirm withheld). **But the RECORD of
  that control inherits the sensitivity of what the control exposed (live leak, Bank-co, 5
  Oct 2026):** a check that deliberately removes the filter produces out-of-scope content by
  construction, so writing its output to an unauthenticated endpoint re-exposes exactly what
  the guard exists to withhold - a public GET returned four hardship document titles on a
  deployed demo whose central claim is that they are unreachable. Evidence about a guarantee is
  not safe to publish merely because it is evidence: record check names, verdicts, states,
  labels, counts and a digest, never the titles or excerpts the checks touched. The surface
  that renders such a record omits it when absent, which is correct and also hides a moved
  route - so freeze the path and assert post-deploy that the record reaches the page.
  **AND ASKING FOR A WITHHOLDING TO BE MADE VISIBLE CREATES A NEW PLACE FOR THE WITHHELD THING TO
  APPEAR (11 Oct 2026, the lead's own instruction).** A resource was excluded from retrieval because
  it carried a claim the GM has held, and the lead asked for that deliberate exclusion to be made
  VISIBLE - "a count, a named exclusion, something" - on the sound ground that an invisible
  intentional discrepancy is indistinguishable from a bug six weeks later. The exclusion REASON then
  quoted the held claim onto a public endpoint. **The record of a withheld claim re-published the
  claim**, and the governance gate caught it on its own author. The instruction was right and
  incomplete: **say the FACT of the exclusion, never the CONTENT excluded.** "Makes a deployment
  statement this site does not make" tells a reader exactly what happened and quotes nothing. Any
  time you ask for a suppression, a refusal or a guard to be surfaced, name in the same breath what
  **SECOND INSTANCE, 12 Oct 2026, AND A CLEARED SCAN HIT IS A HOLE WEARING A PASS.**
  `corpus/lenses.json` recorded a dropped deployment clause by QUOTING it - "and a deployment story
  through to air-gapped" - at `._filtering[1]`, in a file that ships inside the submission zip. The
  rule above was written the previous day, from the lead's own instruction, and did not fire. What
  makes this enforcement rather than a restatement: the governance scan over all 109 resources
  reported **"0 real hits (1 lead-cleared)"**. A cleared hit is not a pass, it is a hole carrying a
  human's name - and the one field a clearance must never sit on is one whose whole job is to
  DESCRIBE an exclusion. So **withholding records, exclusion reasons and guard-output notes are
  scanned as their own named population**, and every clearance states a reason the next reader can
  disagree with. Found by scanning the file, after a builder independently found the sibling in
  `claim-scan.json`, which quotes dropped sentences verbatim: two instances in two files means the
  class is findable, and neither was found by a check that claimed to cover it.
  may be said about it. The expression key
  is `{resource: ...}` on `/catalog` but `{field: ...}` on `/find`/`/ask`. Native faceted
  aggregation costs 40+ seconds - paginate and count.
- **Never use faceted aggregation - POST or GET - to define a KB's labels or counts
  (cross-tenant leak, corrected 3 Sep 2026):** register labelsets deterministically, drop
  unregistered facet keys, and re-derive counts from individually `filters`-scoped
  queries (FE-19 in `content/field-engineering/report-02.md`).
- **Graph:** anchored `/graph` queries are source-only unless `undirected: true` (5-9x
  coverage difference, partial results silent; separate from the ~500 `top_k` cap). The
  graph misses facts `/ask` can answer - design graph beats to degrade to the source
  document via `metadata.field_id`/`paragraph_id`. Strip boilerplate from
  graph-extraction scope. Relational models: write FKs as explicit
  `usermetadata.relations` at create time (zero LLM cost); they index but do NOT read
  back off the resource (the graph endpoint is the only read-back); allow-list by your
  OWN relation-label vocabulary; traversal is application-driven (one anchored query per
  hop, undirected), passing walked relations as `extra_context`; past the first hop
  expand only along FK-owning tables, never through shared reference data; measure,
  never assert, that the graph improves retrieval. Full rules:
  `content/field-engineering/relational-sync-findings-2026-09-28.md`.
- **SUPPLYING `prompt.user` ON `/ask` REPLACES THE PLATFORM'S OWN GROUNDING
  SCAFFOLDING, AND THE MODEL THEN INVENTS (measured 21 Oct 2026, Forge-co).** One
  question whose only correct answer is a product code, same box, same model, four
  variants: no custom prompt returned the code correctly; `prompt.user` with a
  `{question}` placeholder invented `DPC6002`; `prompt.user` with the question inline
  invented `A30S and A36S`; `prompt.system` returned the code correctly AND obeyed the
  instruction. Three fluent, confident, wrong product codes, and none of it is visible
  unless you assert that a KNOWN identifier survived into the answer. **Put a language,
  tone or format instruction in `prompt.system`. Never replace `prompt.user`.** The
  guard that belongs beside it: any identifier in an answer that appears in no
  retrieved passage withholds the WHOLE response.
- **THE `consumption` BLOCK ON AN `/ask` RESPONSE READS ZEROS; THE MODEL TOKENS LIVE AT `metadata.tokens`
  (input, output), AND THE SCHEMA-CALL LANGUAGE QUIRK IS NARROWER THAN THE ENTRY BELOW STATES (measured 25
  Oct 2026, 49 calls, Home-two viewer-language work).** A cost measurement that read `consumption` would
  have reported every answer as free; the real figures sat one key over, as the 11 Oct structured-extraction
  memory already recorded for a different route. Measured with them: a Spanish answer costs about 5 per cent
  more total tokens than the English one over three questions. And the negative control for the entry below
  (language in `prompt.system` only, beside a schema) came back in SPANISH at N=1, so `prompt.system` is not
  simply ignored: the brief and the sources handed in that way were dropped on the content page, while a
  language instruction may survive for the answer field. Keep the schema-description placement, which gave 3
  of 3 with English provenance intact. RESOLVED 25 Oct 2026 09:33Z at N=4: language in `prompt.system` only, beside a
  schema with English descriptions, returned ENGLISH 4 of 4 (detector en 13 to 18 against es 0), so the N=1 Spanish
  did not reproduce and `prompt.system` beside a schema is not a reliable channel; the schema descriptions carry the
  language. Read cost from `metadata.tokens`, never from `consumption`, on this route.
- **`prompt.system` IS IGNORED WHEN `answer_json_schema` IS PRESENT; THE SCHEMA'S FIELD DESCRIPTIONS ARE
  THE INSTRUCTION CHANNEL AND `extra_context` IS HONOURED (measured twice, 25 Oct 2026, Home-two
  content page).** A probe asking for Spanish in `prompt.system` got English, and the first live build
  ignored its whole brief and the ERP rows handed to it the same way. Putting the language and the brief
  into the schema's field descriptions worked; putting the sources into `extra_context` worked. So on a
  structured call: instructions live in the schema descriptions, sources live in `extra_context`, and
  `prompt.system` is sent but never relied on. This narrows the 21 Oct rule above (language in
  `prompt.system`, never `prompt.user`), which holds for a plain `/ask` and not for a schema call. Guard it:
  a draft labelled Spanish that reads as English is refused server-side, because the instruction can be
  silently dropped.
- **A `maxItems` ALONGSIDE ITEM ENUMS MAKES THE WHOLE `/ask` 400 (measured 21 Oct 2026,
  Forge-co).** An `answer_json_schema` whose array items carried two enums - a field
  label and a document title - plus `maxItems: 24` returned HTTP 400 from the generative
  backend: *"The specified schema produces a constraint that has too many states for
  serving"*. Identical payload with the cap removed, 200. The cap was tidiness; the enums
  are the structural guarantee and the response is bounded by them anyway. **The cost was
  not the 400, it was the caller**, which returned an empty result on any non-200, so a
  refused call rendered as "no field disagrees with another document" - zero-of-zero
  wearing a tick, for a whole deploy, across 8 measured runs. A constrained-decoding
  rejection is a REFUSAL and must be its own state, never folded into the empty case; and
  where a human gate sits downstream it leaves that gate CLOSED, because unchecked is not
  cleared.
- **THE RERANKER SCORE IS NOT COMPARABLE ACROSS QUERY LANGUAGES, SO ANY FLOOR ON IT IS A
  LANGUAGE FILTER (measured 21 Oct 2026, Forge-co; filed as platform feedback
  ec9d9db7).** One question, six languages, one English-only corpus, identical `/find`
  calls, and **every paragraph in every response reporting `score_type: RERANKER`** - so
  this is one quantity and not a mix of reranker and RRF scores, which was the first thing
  to rule out. Top paragraph score: **EN 0.8372, JA 0.8384, ZH 0.0693, ES 0.0130, FR
  0.0061, DE 0.0002.** Four orders of magnitude. Meanwhile the retrieved SET barely moves -
  6 to 8 of 8 passages shared with the English result, Japanese 8 of 8 - and all six
  languages return a CORRECT answer naming the right product code. **So ordering and
  membership are usable and the absolute score is not.**
  Because retrieval never returns empty, the application floor IS the decline decision, so
  a 0.1 threshold tuned on English answers English and Japanese and declines German, French
  and Spanish **with the right documents in the retrieved set** - silently, and presenting
  as a content gap rather than a scoring artefact. Threshold on rank or membership, never on
  this score across languages, and never display it beside a refusal: the same figure reads
  0.84 in English and 0.006 in French for the same question, so a buyer sees "the corpus
  holds nothing" where it holds the answer. Not punctuation, ruled out explicitly - French
  with the space before the question mark, without it, straight apostrophe, typographic
  apostrophe and no terminal punctuation all land between 0.0025 and 0.0062.
  **The sharper half is what it says about a fix made one hour earlier.** The refusal copy
  had just been changed FROM a false claim about the corpus TO "the closest scoring 0.66",
  which was the right move on the evidence then available and became a worse one the moment
  a second language was measured. **A figure is only an honest replacement for a claim while
  it means the same thing in every case the surface will meet** - so when you replace prose
  with a number, ask which populations that number has been measured on, which is the
  measured-on-one-population rule pointed at your own repair.
- **WHERE A GATE SCORES MODEL OUTPUT, A PROMPT CHANGE IS A CHANGE TO THE GATE'S INPUT -
  AND THE MODEL WILL FILL A FREE-TEXT FIELD WITH WHATEVER IT HAS NO OTHER PLACE TO PUT
  (22 Oct 2026, Forge-co).** Hard rule 3's `prompt.user` finding was applied to two
  files and not to the third, which was the demo's front door. Measured over 20 calls,
  moving the instruction to `prompt.system` was decisively right on the MODEL: under
  `prompt.user` it gave a boutique winery four confident recommendations 2 of 2 - a room
  the corpus does not describe - and returned exactly four picks in 8 of 8 matching
  trials, which is the schema's `maxItems` rather than a judgement. Under `prompt.system`
  it declined the winery 2 of 2 and returned one to three.
  **And the same change broke the gate, because the gate scores the model's own English
  restatement.** Asked about a suburban bowls club the model returned "This refers to an
  independently owned business that was formerly part of a larger group" - a RETRIEVED
  DOCUMENT'S description with the room discarded - and that scored **0.9971** against the
  corpus, higher than every genuine match. The corpus matching itself. Two things follow.
  **(a) Any veto computed from model output inherits every prompt change**, so a prompt
  edit re-derives the threshold rather than inheriting it; the measurement REFUSED to pick
  a floor when no gap separated the classes, which is the only reason a number was not
  chosen there. **(b) The cause was a missing FIELD, not a missing instruction**: the
  restatement was the only free-text place to put the archetype the model had found, so it
  went there. Giving the archetype its own field - constrained to a title retrieval
  actually returned - took bowls to 0.0128 and restored a 6.0x separation. **Ask of any
  contaminated field what the model had no other place to put.**
  Three corollaries worth more than the fix. The model's own confidence flag went from
  agreeing with almost anything to agreeing with the expectation on 8 of 8 cases, so a
  flag that looked like a second veto had been decorative and the score was carrying the
  whole burden - **count your vetoes by measuring them, not by reading the code.** The
  honest line is SUBSTITUTION rather than echo: a restatement that paraphrases the corpus
  while still describing the room is legitimate, and the non-match scores (0.0002 to
  0.0128) are what bound the circularity. And **both measurement scripts had rebuilt the
  request instead of calling production's**, one silently dropping `top_k`, the other
  pinning the superseded prompt field - so each was measuring a population it was not
  reporting on. One shared `ask_body()`; a measurement that constructs its own request is
  a second implementation and drifts.
- **THE TOOL SCHEMA YOU PUBLISH OVER MCP IS THE ONLY INSTRUCTION THE AGENT HAS, SO A PARAMETER WITH NO
  DESCRIPTION AND NO ENUM IS AN INSTRUCTION TO INVENT (24 Oct 2026, two of eighteen demo pages failing
  their own first chip).** Conversational commerce returned "No answer" after 23 s and triage named nobody
  after 28 s, on a live build that had passed 908 tests and two seller walks. Both were our own tool
  definitions: the schema builder read only a parameter's top-level type, so an `Optional[bool]` was
  published as a string with an empty description and the agent put its search words into it (422 on
  every product lookup, then eight iterations of nothing); and a job `status` parameter published no
  values, so the agent invented "waiting on parts" from the enquiry's wording and retried invented values
  on five of eight iterations. **Every parameter we published had an empty description.** The other
  three agent pages worked by luck of which parameters their first chips happened to need. Not the
  platform, not the seed data, and invisible to every test, because tests call the route and the agent
  reads the schema. So: derive the published type from the full annotation (the non-null branch of
  `anyOf`), publish a description on every parameter and the real value set as an enum wherever the
  route has one, and gate it with a test over the live tool list that fails on a planted bare parameter.
  A tool that 400s with the list of valid values is not a mitigation, because the agent does not adapt
  to it. Found by driving the agent directly and printing its step stream; Fly keeps 100 log lines and
  in-process tool calls log nothing, so the live window was gone - log tool outcomes.
- **A MALFORMED BEARER IS NOT AN ABSENT ONE ON `/session/ephemeral` (21 Oct 2026).**
  Passing `headers: {"authorization": "Bearer "}` with an empty token returns
  `Error in context` in 0.3 seconds with zero tool calls; OMITTING the header entirely
  answers normally in ~15s. An app that builds the header unconditionally therefore
  breaks every signed-out request, and if an honesty gate sits downstream it reports
  "I could not read anything from the system" - a message that reads as TRUE while
  covering a client bug, which is why nobody investigates it.
- **A DA TASK'S SCOPE LIVES AT `parameters.on`, NOT INSIDE THE OPERATION, AND SILENTLY
  DEFAULTS TO 0 (21 Oct 2026).** Set inside the `operations[].label` block it is
  ignored. The enum is `[0, 1]` and the schema does not say which is which; the task
  describes itself as labelling "text blocks or resources", so 1 is taken to be
  resource scope. On a 10-resource / 107-paragraph corpus that is the difference
  between 10 model calls and 107. Rule 15 already says to read `llm.model` back off
  the stored object - **read `on` back too**: verifying one pinned field and not the
  other is the same defect one field over.
- **RE-REGISTERING A TASK IDENT THAT IS RUNNING RETURNS 422 "Already running an
  operation of type `label` with ident `x`" - A CONFLICT, NOT A SCHEMA ERROR.** It
  reads like a validation failure, so a corrected registration looks rejected on its
  merits while the OLD, wrong configuration stays live and keeps running. Stop
  (`POST /kb/{kb}/task/{id}/stop`) then delete (`DELETE /kb/{kb}/task/{id}`) before
  re-registering, and make the provisioning step idempotent so this cannot bite twice.
- **Search configurations** are free to register and are what makes the admin-console
  half of the sales motion possible: `POST /kb/{kb}/search_configurations/{name}` with
  `{"kind": "find"|"ask", "config": {...}}`, read back with a plain GET. Generate them
  from the application's OWN access model rather than writing them by hand, so a
  registered configuration cannot describe a scope the product does not have -
  registering something impressive the app never issues is the console's version of a
  staged capability.
- **DA tasks:** pin `llm.model` on every task (unpinned tasks fail silently after a 200);
  **but on an EXTRACT STRATEGY `llm.model` is silently IGNORED and the platform substitutes
  its own default - the key that works there is `llm.generative_model` (measured, Bank-co,
  5 Oct 2026). Same failure shape as an unpinned task and harder to see, because the strategy
  reads back looking correct. Read the model back from the stored object and confirm it is the
  one you set, never that the field you sent was accepted.**
  Also:
  output lands at `da-<destination>-f-<fieldId>`, and Labeler output at
  `computedmetadata.field_classifications[].classifications` (not `usermetadata`;
  `GET /labelsets` returns `{}` for implicit labelsets - facet the catalogue instead).
  `completed: true` is not coverage - count via facets against the resource total and
  re-run when short. An LLM Labeler types media by what it DEPICTS: intrinsic axes
  (format, mime, provenance) are set deterministically at ingest, never inferred; cancel
  wrong computed labels with `cancelled_by_user`.
- **Ingest:** `POST /kb/{id}/upload` is for genuine binaries ONLY - it silently corrupts
  self-supplied text (OCRs the JSON, hash titles) while retrieval keeps working; text
  goes to `POST /kb/{id}/resources` with `title` + `texts.body.body` + `origin.url`, and
  after any ingest read titles back. The two-step create+PUT pattern 500s on PDFs - use
  single-call `/upload` for binaries, then PATCH metadata. Pagination: `/resources` keys
  **A METADATA PATCH ON A RESOURCE REPLACES THE WHOLE METADATA BLOCK, AND THE CORPUS DIGEST CANNOT SEE IT
  (25 Oct 2026).** A one-field correction (a call's branch code) was sent as a PATCH carrying only that field,
  after a read with the wrong parameter had returned an empty block; for about a minute the call resource lost
  its agent, customer, company, queue, audio flag and duration. The builder caught it because the read-back
  looked wrong, rebuilt the full block from the source files the ingest builds it from, and patched again. The
  stored-body digest read identical before, during and after, because it covers body text and status and not
  metadata. So: read the full object first with the parameter that returns it, send the whole block with one
  field changed, read it back and compare key for key against a sibling, and never cite the digest as
  evidence about metadata. Same family as `dam_update_battlecard` replacing the whole card.
  **A RE-INGEST IS TRANSIENTLY VISIBLE AS EXTRA RESOURCES, SO A COUNT READ MID-MOVE EXCEEDS THE TRUE
  POPULATION (12 Oct 2026).** An agent verifying an all-clear read the box a few minutes later and
  got **112 resources with 2 PENDING where the all-clear said 109**, with nothing in the working tree
  to explain it. It stopped, produced four reads over two minutes, killed nothing and escalated it as
  a possible unattributed write - which was the correct response. The box held 109, all PROCESSED:
  during a replace the new resource and the original are both briefly present, so N re-ingests read
  as up to N extra rows before settling. Same cause as a digest script raising `KeyError` while a
  resource is being replaced. **So a resource count taken during a corpus move is not evidence about
  the population** - the two-read settle is what makes a count meaningful, and an all-clear that
  names a count without it is naming a sample. Tell every agent that can see a shared box who owns
  it and what is about to move, because an agent that cannot distinguish an authorised write from an
  intrusion must treat it as an intrusion, and the cost of this one was minutes.
  on `pagination.last`, `/catalog` on `fulltext.next_page` - never `.more`. Extracted
  text needs `show=extracted&extracted=text` together. A resource's `title` is NOT
  searchable body text - names that must ground go in the body. Corporate npm enforces a
  ~14-day cooldown on new versions - pin from the reference lockfile.
- **Media:** generate demo videos at >=20s stereo AND check each video's paragraph kinds
  include `TRANSCRIPT` post-ingest, every video, every time (the floor is necessary, not
  sufficient; build the check into the ingest script - and make it EXIT NON-ZERO, because a
  recorded `transcript_present: false` that the build walks past is decoration). No speaker
  diarisation exists - ingest a companion transcript with speaker names in body text.
  **A video's transcript has no usable granularity (measured 5 Oct 2026, Bank-co):** the
  whole video yields ONE `TRANSCRIPT` paragraph, spanning the whole file
  (`start_seconds=[0] end_seconds=[27]` on a 27.6s video), holding ONE `sentences` entry whose
  `start_seconds`/`end_seconds` are both null. So "land on the spoken moment" is NOT buildable -
  deriving an offset from character position is a fabricated timestamp (hard rule 3). Alongside
  it sit ~7 `OCR` and ~7 `INCEPTION` paragraphs, so retrieval over a video field runs ~14:1
  AGAINST returning spoken text, and a video citation surfaces a frame description by default.
  Ground spoken-content answers on the COMPANION TRANSCRIPT text resource instead: it paragraphs
  normally, cites a passage, covers videos whose own transcript is missing, and spells names the
  speech-to-text mishears (it heard "Waddle Bank" for Bank-co, in the extracted text).
  **QUALIFIED 24 Oct 2026 (Forge-co calls, measured): the one-untimed-paragraph shape is a
  property of SHORT media.** A 69-second synthetic call ingested as audio came back with FOUR
  timed TRANSCRIPT paragraphs of 14 to 21 seconds each, so a citation CAN seek a player to a
  paragraph's `start_seconds` at that length, and call-analysis's cite-to-seek on 54 to 99 second
  files was never contradicting the 27-second finding - the two measured different lengths.
  Read the paragraph shape back after ingest at YOUR file length before designing either way;
  note the platform merges about two speaker turns per paragraph, so a passage can hold two
  speakers and the page should say so.
- **Calls:** send `X-Synchronous: true` on EVERY non-streaming call (NDJSON otherwise,
  and the bug bites per-call - grep the other call sites when fixing one). Retrieval
  never returns empty (scored hits trail to 0.000) - threshold client-side; "no results"
  can never prove absence. **RETRIEVAL RANK CARRIES NO INFORMATION ABOUT WHETHER A
  DOCUMENT CONTAINS THE ANSWER (measured 9 Oct 2026, University vet corpus).** With the
  reranker off, three questions the product could not answer all returned the correct
  document at an IDENTICAL 0.033 - the RRF score for rank one in both the keyword and
  semantic lists. Rank said "most related document" and nothing about answerhood. The
  RERANKER separates them: on the same corpus it scored 0.038, 0.034 and 0.074 for
  documents that were about the subject and did not contain the answer, against 0.877
  for one that did. **So a low reranker score over a top-ranked document is a CONTENT
  finding** - the corpus is topically adjacent and answers something else - and the fix
  is corpus depth, not a threshold. After rewriting those documents the same question
  went 0.038 to 0.999. Ten documents averaging 374 words cannot answer what a
  practitioner types; the same ten at 800 to 1100 words can. Derive a seeded corpus from
  the questions a real user would type, and verify by asking them. **And an application
  floor tuned for a different corpus SIZE is the second cause with the same symptom:**
  because retrieval never returns empty, the application's floor IS the decline
  decision, so read it before concluding anything about the corpus.
  **AND CUTTING AN OVERCLAIM CAN DELETE THE ONLY TEXT THAT ANSWERED A QUESTION (11 Oct 2026, a whole
  buyer journey vanished from a live public site).** The lead ruled an unsupportable absolute out of
  a canonical document - "with no further integration work per customer". That sentence was the
  document's ONLY text carrying the phrase a buyer searches with. The suggested question "How much
  integration work is there per end customer?" fell to a retrieval score of **0.015 against a floor
  of 0.015**, its path dropped from three chips to two, below the minimum, and the entire partner
  lens disappeared from the public payload - recorded only at an operator-key endpoint, by a
  deliberate design ruling that a withdrawn path is not announced to visitors. **The correction was
  right and its cost was unmeasured.**
  So: **a content correction is a RETRIEVAL event.** After cutting or rewording any sentence in a
  retrieved corpus, re-score the questions that depended on it - the suggested set is the cheap
  population and it is exactly the one a visitor meets. Nobody thinks of retrieval as "depending on"
  a sentence, which is why hard rule 11's sweep misses it.
  **And fix it in the DOCUMENT, never by rewording the question.** The tempting repair is to reshape
  the chip until it matches the corpus's new vocabulary; one candidate scored 0.96 that way. That is
  the tail wagging the dog, and it inverts the standing rule to derive a corpus from the questions a
  real user would type. Here the document still ANSWERED the question and had merely lost the words
  a reader would search with, so the repair is one honest sentence restating what the document
  already says, in the buyer's vocabulary - asserting nothing new. Re-score and SHOW THE FIGURE; if
  it does not clear the floor convincingly, withdraw the path rather than tune anything.
  Timing note worth copying: this was free because it was caught BETWEEN a corpus release and the
  warm, when approvals are already stale. The same edit after the warm costs a second warm and a
  second full read.
- **REMi:** score via `POST {kb}/predict/remi` with the KB service-account token (not the
  NUA key), against the FULL retrieved context (up to ~8 by score), never only cited
  excerpts (thin context swings 0/5 to 5/5 on good answers). REMi is holistic: a small
  unsourced addition still scores ~4/5, so pass every fused fact's source as an explicit
  context item by construction. It under-scores non-English answers against English
  content - never surface raw per-language REMi; show resolvable citations instead. On
  short-record corpora build context from cited record BODIES; `answer_relevance` is
  unstable - do not surface it; disclose that groundedness measures support for the
  wording, not correctness.
  **AND A GROUNDED ANSWER CAN ATTRIBUTE A FAILURE MODE TO THE PRODUCT ITSELF (11 Oct 2026, the
  worst sentence of the build).** Asked "what stops it inventing an answer?", a pre-warmed answer
  served: "It can fill gaps with invention, but then it calls that invention truth; the honest
  behaviour is to withhold when not supported." Groundedness 5. The corpus says that about systems
  WITHOUT a decline floor - an honest document explaining why a floor must exist - and the model
  moved the subject. **AND IN A MULTI-PRODUCT CORPUS IT WILL OFFER ANOTHER
  PRODUCT'S UI AS YOURS (11 Oct 2026).** A grounded answer on a self-serve site ended "Use the
  /audit-trail view to see the citation and confidence score for each answer." There is no such
  route or view anywhere in that app; it came from a corpus entry describing a DIFFERENT demo's
  page. With 48 public assets each documenting its own routes, views and tabs, any of them can be
  handed to a visitor as if it were this product's, and groundedness scores it 5 because the words
  are genuinely supported. **This one is fully deterministic to guard:** derive the app's real
  route list FROM THE APP, never a hand-typed list, and hold any sentence naming a slash-path or a
  "the X view/page/tab" that is not in it, with legitimate cross-references kept quiet. **Any document that describes the failure mode your product avoids is a
  document a generated answer can read as a description OF your product**, and the sentences most
  at risk are the vivid ones written to make the failure memorable. Groundedness cannot see it,
  because the words really are supported.
  **AND TWO TRUE HALVES JOINED BY A FALSE CONNECTIVE ARE INVISIBLE TO EVERY CHECK THAT SCORES SPANS
  (12 Oct 2026).** A generated answer said *"keep the API key server-side **so** permissions you
  already have apply to the agent."* Both halves are true and separately grounded - a server-side
  key does not reach a browser, and permissions apply to an agent because the caller's token is
  passed over MCP - and **the "so" asserts a causal link that does not exist.** A reader
  implementing it would believe server-side key storage grants permission inheritance.
  Groundedness scores support for the CLAUSES and both are supported, so no span-based measure can
  see it. **Read the CONNECTIVES in any generated mechanism explanation, not only the clauses: so,
  therefore, which means, this is why.** Sibling of the mischaracterised concept scoring 5 on both
  axes, one level down: there the claim is wrong, here each claim is right and the JOIN is wrong.
  The discharge is not to delete the honest half, which
  is what earns the sale: it is to recognise that a question whose answer must distinguish "we do
  this" from "others do this" is a question a short generative answer will eventually get
  backwards, and to serve it from deterministic copy instead. That question's chip was retired on
  its third distinct failure while the document stayed.
  **AND A PER-ANSWER QUALITY SCORE CANNOT GATE CONCEPTUAL CORRECTNESS, WHICH IS EXACTLY
  WHAT A PRODUCT'S EXPLANATION OF ITS OWN MEASUREMENT NEEDS (11 Oct 2026, self-serve
  site).** The chip "how is answer quality actually measured?" warmed under two scopes and
  BOTH answers scored groundedness 5 AND context relevance 5 - top marks on both axes -
  while one asserted "a ground truth score called groundedness", which this product does
  not have, and the other called it "a confidence (or trust) score", conflating the answer
  score with the per-extraction confidence belonging to a different feature. Groundedness
  rates support for the WORDING against the retrieved passages, so a confident
  mischaracterisation of a concept scores perfectly whenever the passages loosely support
  the words. A groundedness floor on a warm-answer gate is therefore not a gate on this
  class, and nothing but a read catches it. **The discharge after five reads failing five
  different ways was not a sixth corpus round - it was to RETIRE THE QUESTION as an offered
  chip.** A suggested question is a promise that we are confident in the answer, and a
  corpus carrying three vocabularies for one score cannot keep that promise inside one
  generated paragraph; the canonical document still answers it when a visitor types it,
  where the whole document is retrieved and nothing has to be compressed. Retiring a
  question the corpus answers well in prose is cheaper than publishing a wrong sentence
  about your own measurement.
- **Citations and derived surfaces:** a free-text provenance field in an
  `answer_json_schema` is hallucinated even when retrieval is grounded - fire `/find`
  first and constrain the source field to an `enum` of the real retrieved titles,
  mandatory for any structured surface claiming provenance. The enum proves the source
  exists, not that the card is about it: derive a card's heading from its cited resource,
  bind card-to-source structurally (no two cards share a source id), and take the excerpt
  from the resource's own OPENING content, not the query's best-matching fragment. A
  context-expanding RAG strategy can cite paragraphs retrieval never listed - resolve
  raw-key fallbacks against the resource endpoint; derived counts are suspect until every
  citation resolves. **Anything derived from a citation list (CTA, card, badge, price,
  count) keys off what the ANSWER NAMED, never retrieval-score order, on EVERY path** -
  re-derive only when the prose named nothing; N named products means N CTAs in prose
  order, zero means zero (never force the answer to commit). When a generated element
  keeps contradicting a deterministic fact beside it, stop generating it - real source
  text cannot lie - then verify the real copy that renders and enumerate the lookup
  against the corpus's real values (tie-break on document order, never raw text).
  Enumerate the SURFACES a mechanism must reach, not its paths, and state the count. Ask
  agents what they DID (a named yes/no list), never what could happen. A deterministic
  measure is displayed AS the measure, through typography, never a colour verdict - with
  the qualitative badge still the default-visible headline (B34) and the count beneath as
  evidence. Citation presence varies per question and per RUN, not by language - retry or
  degrade honestly. Read a ranked evidence panel as the buyer will: the top-scoring
  source is routinely not the one the answer used - teach the signal or crop it.
  **THE EVIDENCE UNIT IS A SENTENCE, A TABLE ROW OR A LIST ITEM** (8 Oct 2026, one
  root cause surfacing three times in one build): a claim-to-source matcher keyed
  on sentences cannot see tabular data, so a price plainly present as
  `Lantern Blend | Espresso blend | 250g | A$15.50` was reported as having no
  source page - and the same narrowness had already discarded 12 true
  relationships whose object sat in the row rather than the sentence. Fix it in
  the SHARED matcher and name the call sites found. **And after replacing a
  permissive measure with a strict one, measure the NEW false positives on the
  content type the product handles best** - removing false reassurance created
  false alarm on the most checkable content there was.
  (lesson: content/sop/lessons/citations-and-derived-surfaces.md)
- **Summarisers:** a generative summariser fabricates by merging two true figures -
  forbid merging separately-stated numbers in the prompt and spot-check generated numbers
  against the source page. Group generated cards on (source resource, quote) with the
  source's own designation wording and date - splitting one statement into N cards
  asserts N independent positions. (lesson: content/sop/lessons/declines-and-no-fake.md)
- **Field Kit data:** `dam_update_battlecard` REPLACES the whole card - every call
  supplies the complete payload; the LIVE stored card is the refresh baseline (download
  via `GET /api/assets/<id>/file?download=1`, verify every section at or above live
  counts); after submitting confirm a card-sized `deliver_size` (tens of KB, never a few
  hundred bytes). (lesson: content/sop/lessons/fieldkit-and-dam.md)

---

