# ARAG GTM Factory - Definition of Pass (DoP)

**This is the lead's document (ownership transferred by GM directive, 8 Aug 2026 -
supersedes the 19 Jul 2026 "GM's document" rule).** The lead, operating as the factory's
product marketing professional, owns, amends and maintains this bar on professional
judgment. Jay is the major stakeholder: his feedback - in chat or as DAM review
decisions - is binding input the lead encodes here, and every material change to the bar
is reported to him in one line when it is made. The lead no longer waits for his
amendment to raise the bar. Every deliverable is walked line by line against this file
before it is called done -
qa-reviewer records an explicit **PASS / FAIL** per line, with evidence attached. **One FAIL
on a blocking line = not done.** PASS = certified into `approved-assets/` (apps instead get an
`APPROVED.md` badge in the app root) and shipped via `dam_submit_work` (hard rule 12) - see
`CLAUDE.md`. "Approved" clears the DoP gate; it does not by itself clear outbound use - hard
rule 10 and any PRD-specific livery rules still apply on top.

**A PASS without evidence is a FAIL.** "Looks fine" is not evidence - attach the rendered
images actually viewed, the grep/scan output, the KB query that confirmed a claim, the live
round-trip response, the URL that was actually opened.

*v1 - 31 Jul 2026: built from the standing hard rules and Workflow rules in `CLAUDE.md`
plus the `grounded-artifact` skill template.*
*v2 - 8 Aug 2026 (first edition under lead ownership): ownership header updated; the
lead's PMM gate added as section 6 (the final gate before submission); the Videos
script-pre-approval line removed (superseded by the 31 Jul "don't gate on chat approval"
directive); Demo apps brought current with the eleven table-stakes gates, the independent
automated QA gate (`scripts/demo_qa_gate.py`) and the admin-console verification
requirement (GM directives, 8 Aug 2026).*

## 1. Truth gates (every deliverable)

- Every ARAG product claim traces to the `nuclia-mcp` knowledge box (hard rule 3). Nothing
  from memory. Claims the KB cannot confirm are flagged, never silently kept.
- No silent substitute for a broken/missing ARAG capability (hard rule 3 corollary, GM
  directive 8 Aug 2026). If a demo/artifact needed a capability ARAG's own mechanism can't
  currently deliver, check: did the workaround still route through a real ARAG call
  (retrieval, `/ask`, a Retrieval Agent)? If yes, it's fine to ship - but the artifact must
  visibly say which ARAG mechanism was actually used and which one wasn't available and why
  (the solution-architecture reveal on a demo app, gate 11, is the designed place for this -
  not just a README line). If no ARAG call was involved at all, that capability should not
  ship dressed as a feature - a visible marker stating ARAG can't currently do this, not a
  polished illusion of completeness.
- No fabricated numbers - no invented accuracy %, adoption %, ROI figure or benchmark. The KB
  publishes no accuracy percentage; prove quality with REMi and a cited-answer demo, never a
  made-up figure. Demo figures are labelled as demo figures, never as measured product
  performance.
- Certifications (SOC 2 / ISO / PIPEDA etc.) named only if verified outside the KB.
- Locked facts hold everywhere - the account's `account-brief.md` LOCKED FACTS table is the
  single source; the same numbers appear identically across deck, video and posts in a kit.
- Statistics: authoritative independent sources only, cited on-slide or in-text (hard rule 4).
  No vendor-sourced number presented as independent. Anything older than ~5 years is dated or
  replaced. Market sizing = named provider + range. Never the target account's direct
  competitor as a proof source.
- All pricing in USD (GM, 7 Jul 2026) - no legible geo-localised price anywhere, even in a
  crop.
- Cross-artifact consistency - every number matches the account brief / messaging house
  exactly, across every artifact in a kit.
- **Memory check at the three trigger moments (added by the lead, 26 Aug 2026).** Before this
  deliverable ships, query the agent-memory KB
  (`.venv/bin/python memory-kb/scripts/ask.py "<what I am about to do>"`) at each of these
  three points, and record the result in the certificate:
  1. **Any number that appears in the artifact** - is it on the real scale, with real units,
     from a real source?
  2. **Any invented name** - brand, product, publication, person, podcast - has a collision
     check actually been run?
  3. **Any claim that a check was performed** - was it genuinely run, or asserted?

  **Why these three and not "consult memory generally":** all three are real failures from a
  single day. A fabricated groundedness score of 9.4 on an invented 0-to-10 scale nearly
  shipped in a keynote; a demo competitor was named after a real chocolate brand then launching
  in Coles; and a world bible asserted that name collisions had been checked when they had not.
  A vague "check your memory" step would fail exactly as the original knowledge did - the
  problem was never recall, it was that nothing forced the question to be asked. **The trigger
  is the gate, not the retrieval.**

  Retrieval quality is not the issue and is not what this step is testing: the memory KB
  returns the right record cleanly on all three probes. This step exists because a fact being
  available has repeatedly not been the same as it surfacing when it mattered.

## 2. Safety + hygiene gates

- No secrets, keys or tokens client-side, in any artifact, or in git (hard rules 5, 6, 9).
- No hosting-region / infra string visible in any screenshot or customer-facing view, checked
  against the target customer's data-residency requirement (hard rule 8; demo KBs are
  synthetic so any region is fine internally, but the *string* still can't show on a
  customer-facing surface).
- Other customers' names and account identifiers anonymised in every screenshot (hard rule 7).
- No real third-party brand used as if owned; no real personal identifiers anywhere - fictional
  entities, neutral demo logins only.
- Outbound (posts, emails) is a DRAFT until Jay signs off (hard rule 10). Only reversible,
  internal jobs run autonomously.

## 3. Language + voice gates

- Australian English. No em dashes (use a spaced hyphen " - ") - except Jay's own personal
  LinkedIn posts/articles (Workflow 4, `jay` voice), which may keep true em dashes.
- Banned words absent: delve, leverage, unlock, seamless, game-changing.
- De-AI pass: remove hedging, filler, symmetrical triads, corporate fluff.
- The room test: would this survive a CIO / CMO / Solutions-Architect room? If not, it is not
  finished.

## 4. Per-type gates

**Brand compliance (added 1 Aug 2026):** for anything customer/partner-facing - demo UI, deck,
one-pager, diagram, copy - run the `progress-arag-branding` skill's audit checklist (colour
contrast, logo sourcing, Hex Loop cropping, Progress Sans Display/Text roles) alongside the
truth/safety/voice gates above. A visually off-brand asset fails this gate the same as an
unverified claim does.

### Decks (Workflows 1-2)
- Exec discipline: max 25 words of body copy per slide, one idea per slide, outcome-led
  titles, one clear ask.
- Template path used when a brand template exists (unpack/edit/repack); scratch-build only
  when none exists. Safe fonts only (Calibri body) - never a faked brand font.
- Screenshots: thin neutral border, subtle shadow, 11pt muted captions, vertical/industry match
  to the customer.
- QA render loop completed - every slide rendered to image and actually viewed, overflow/
  overlap/contrast fixed, one fix-and-verify cycle.

### Demo apps (Workflow 5)
- All eleven binding table-stakes gates in `CLAUDE.md` Workflow 5 / the `arag-demo-app`
  skill (the eleventh is the top-right solution-architecture reveal, present on every route,
  showing this demo's real request/data flow - complete enough to stand alone without the
  admin console): seeded end to end (no empty/
  lorem/placeholder states); presents as the customer's/vertical's own system (no "powered by
  Agentic RAG" chrome, no capability-tour framing, no exposed endpoint names or "Knowledge Box"
  nomenclature); one route per use case; a visible cited/grounded answer reachable in the
  seeded narrative; no hosting-region/infra string anywhere customer-facing; discreet
  synthetic-content disclosure (footer only, never the headline); no real personal/third-party
  identifiers; visible polish (no broken assets, no console errors, no raw error pages,
  designed empty/no-result states); a working ask round-trip through the server-side proxy
  (ARAG key never client-side); a documented 30-second reset.
- **Agent/AI answer text renders through a real markdown renderer - never raw markdown
  syntax visible on screen** (binding, GM directive 2 Aug 2026, real defect caught in
  Operator Fleet's live "Watching the agent work" panel: literal `**Unit 14**` and
  `1. **Unit 14**` text shown to the user instead of bold/formatted list output). ARAG's
  streamed answers routinely contain markdown (bold, numbered/bulleted lists) - any UI that
  dumps that text into a plain `<p>`/text node instead of a markdown component will show
  this defect. Check every answer-rendering surface (not just the happy-path screenshot
  used for the deck/demo capture) before shipping.
- **Preview mechanism (binding, GM directive 31 Jul 2026): every demo is pushed to its own
  GitHub repo and deployed to a new Fly.io machine before it goes to review.** This is how the
  demo gets previewed prior to DoP approval - a local-only build is not sufficient to submit
  for review, even though local build/QA still happens first per Workflow 5. Concretely:
  `gh repo create` (private) + push the built app, then `flyctl apps create <slug>` +
  `flyctl deploy` - a genuinely new machine per demo, never redeployed over an existing one
  unless it's an update to that same demo.
- **DAM delivery format (binding, GM directive 31 Jul 2026): submit a `.zip` of the built app**
  (source only - never `node_modules`, `.env`, or any secret/license file) via the DAM's
  `submit-file` raw-HTTP route (see `CLAUDE.md` hard rule 12's "DAM file-delivery rules") -
  never `file_base64`, a zip is always too large for that. Live `<slug>.fly.dev` URL goes in
  `source_url`, set with `dam_update_asset` AFTER submitting because the `submit-file` query
  param does not stick (measured 9 Oct 2026, came back null). The GitHub repo URL, reset
  instructions and provenance go in the **NOTE**, never the description: the server REJECTS
  a description containing a repo URL with HTTP 400, which is the 4 Sep 2026
  seller-facing-copy rule enforced in code, and `description` truncates silently at 500
  characters. The description is seller-facing card copy - what the asset is and its field
  value. (Amended by the lead, 23 Oct 2026: this line said repo URL and reset instructions
  go in `description` and had been stale for over a month. The server caught it, not a
  reader, which is the argument for putting a rule somewhere executable.)
- Claims KB-verified per hard rule 3; ARAG is the agent (calls the app's own `/mcp`), not a
  homegrown planner, per the 21 Jul 2026 directive.
- **Independent QA gate, not builder self-cert (GM directive 8 Aug 2026):**
  `scripts/demo_qa_gate.py --url <live-url>` run against the deployed URL exits clean
  (every route: no 4xx/5xx, zero console/page errors, zero failed network responses, no
  leaked secret/region/ARAG-endpoint string, no raw unrendered markdown), plus a genuinely
  separate qa-reviewer pass for the judgment calls. Any FAIL from either layer loops back
  to the builder - a demo never ships with a known FAIL and a note. In a solo session with
  no separate reviewer, the cert says so explicitly and the automated gate is mandatory.
- **Admin-console verification (GM directive 8 Aug 2026):** every ARAG mechanism the
  demo's narrative/README/architecture-reveal claims is confirmed as a real object on the
  KB via the API (`/tasks` configs, `/search_configurations`, `/extract_strategies`)
  before delivery - the console walkthrough is part of the sales motion, so it must
  genuinely back up what the demo claims. Platform-blocked capabilities (the confirmed
  Generator DA bug) get the visible-marker treatment, never a claim.
- **Backend breadth gate (binding approval criterion, GM directive 20 Aug 2026):** a demo
  package is not complete until the Knowledge Box it runs on visibly demonstrates the
  BREADTH of Progress Agentic RAG - so that after the app demo a seller can log into the
  ARAG admin console and walk the prospect through a genuinely RICH, configured KB, not a
  bare one. This hardens the admin-console-verification bullet above from "each claimed
  mechanism exists" to "the platform's range is on show wherever the content warrants it."
  The current failure mode this fixes: builds create a very basic backend (one search
  config, one or two DA tasks) that makes for a thin, unimpressive console walkthrough. The
  backing KB must carry REAL, console-visible, API-verifiable instances of, at minimum, each
  capability the corpus sensibly justifies:
  - **Labels / label taxonomy** - multiple labelsets applied across resources (by customer,
    document type, site, hazard class, lifecycle, etc.), never an unlabelled corpus. Verify:
    labelsets exist and resources actually carry them.
  - **Data-augmentation agents, across TYPES - not one:** where the content warrants, a
    Labeler (classification), a Generator/Ask task (field generation, summaries), Graph
    extraction (entities/relations), Q&A generation (synthetic questions, doubling as an
    eval set), Ask/summarize. Each registered AND run to completion. Verify:
    `GET /kb/{id}/tasks` (running/configs/done, not just the type catalogue).
  - **Search configurations** - a named config per app surface with its baked-in
    filter/prompt. Verify: `GET /kb/{id}/search_configurations`.
  - **Custom extraction methods / extract strategies** - where the content warrants (visual/
    OCR for scanned docs, table extraction for rate schedules, split strategies). Verify:
    `GET /kb/{id}/extract_strategies`.
  - **Other where sensible** - entity/NER groups, synonyms, etc.
  **COST-SAFETY EXCEPTION (lead's amendment, 9 Oct 2026, first applied to SemanticSite).**
  Where a build's corpus is large enough that ingest-time agents would breach hard rule 15,
  their ABSENCE is correct design and this gate is cleared by a RECORDED EXCEPTION rather
  than by adding them. One model call per paragraph across a 500-page site is roughly 10,000
  calls per task type per run, and this factory has twice paid for that lesson - US$25,000,
  then an account-wide budget block that took down 33 of 39 live demos and the Field Kit
  queue with it. **The exception is not a waiver and it is not silent.** It requires all of:
  the estimated call count and cost that justify it, stated as a figure; the zero-cost
  breadth that IS present, because deterministically registered labelsets, search
  configurations and explicit `usermetadata.relations` cost nothing and must still be there;
  and the reason written into the app's own README so it travels with the build rather than
  living only in a certificate. A bare KB with no exception recorded still FAILS - the
  difference between a deliberate omission and a thin backend is whether the number was
  worked out.

  "Where it makes sense" is the judgment call both ways: do NOT bolt on components the
  content doesn't justify (gratuitous config is its own anti-pattern and reads as padding),
  but a KB showing only one `/ask` + one search config FAILS this gate - that is not a
  walkthrough.
  **ARCHITECTURAL-ABSENCE EXCEPTION (lead amendment, 8 Oct 2026, SemanticSite).** A
  component may be absent, and the gate still PASS, where its absence is a deliberate
  architectural decision, that decision is stated visibly in the solution-architecture
  reveal with its reason, and the walkthrough is scripted around what IS registered.
  The case: SemanticSite runs no ingest-time augmentation task, because such a task costs
  one model call per paragraph across the corpus and the product's entire economic
  argument - two measured calls per page, about 1,000 for a 500-page site rather than
  30,000 - depends on not running one. Its reveal says so in those words: "Not used:
  per-paragraph extraction at ingest, a separate graph database, or any other AI
  provider." Registering a task to satisfy a breadth count would make the demo contradict
  its own strongest claim, which is the opposite of what this gate is for.
  The exception is NARROW and does not become a general excuse: it requires (a) a stated
  reason in the reveal, not a README; (b) a cost, residency, authenticity or
  platform-limitation argument, never "we did not get to it"; (c) genuine registered
  objects covering every mechanism the demo DOES claim, verified via the API; and (d) the
  absence named to the GM when the artifact ships. A component missing because nobody
  built it still FAILS. Every component must be genuine per hard rule 3 (a platform-blocked
  capability, e.g. the Generator JSON path, is disclosed, never faked). The README and the
  solution-architecture reveal name each configured component so the console walkthrough is
  scripted, and qa-reviewer verifies the breadth via the API before the package passes.
- **Integration is the hero where the data warrants it (GM directive, 21 Aug 2026):** for any
  demo whose vertical has BOTH unstructured content AND structured business data/functions, the
  MAJOR theme is INTEGRATION - ARAG reasoning over structured data + business functions via MCP -
  and the hero/wow moment is unstructured and structured data working TOGETHER in a single
  grounded answer (e.g. one question answered by fusing a scanned contract clause with a live
  billed rate pulled from the business system's own MCP server, citing both). The pure-
  unstructured use cases are the supporting cast, not the headline. The solution-architecture
  reveal foregrounds the MCP integration. Honesty unchanged (hard rule 3): where ARAG's own
  Retrieval-Agent orchestration of the MCP calls is platform-blocked (the confirmed
  `/session/ephemeral` bug), the app orchestrates the same genuine live calls with that one
  nuance disclosed in the reveal - kept OUT of the wow beat, never apologetic. Resolving that
  platform bug is the priority that upgrades the hero from app-orchestrated to fully
  ARAG-agent-driven.

### Videos (Workflow 3)
- Script quality is judged at DAM review time like every other artifact - no chat
  pre-approval gate (GM directive 31 Jul 2026, superseding the original v1 line here).
- Narration timed to the walkthrough/deck playback; claims KB-verified.
- QA: playback duration checked against script timing; frames viewed at start, middle and end
  for rendering defects.

### Written content (Workflow 4)
- Hook in line one for LinkedIn/social; short paragraphs; no hashtag spam; ends with a question
  or a concrete take, never "thoughts?".
- Battle cards: claim / proof / trap question / counter, each claim KB-verified.
- Blogs, one-pagers, email sequences consume the locked account brief with zero drift from it.

## 5. Evidence rule

A PASS is only a PASS with evidence attached: the rendered slide/frame images actually viewed,
the grep/scan output for region strings and banned words, the KB query that confirmed a claim,
the live ask round-trip response, the deployed URL that was actually opened and clicked
through. "Looks fine" is a FAIL.

**A relayed verdict is not independent evidence (added 2 Aug 2026 - a real routing gap found
this session: qa-reviewer's output landed with the lead instead of the artifact's own
producer).** If a QA finding reaches you second-hand - summarised or forwarded by the lead
or anyone else - that is not, by itself, grounds for a PASS. Either see the reviewer's own
output directly, or do your own equivalent first-hand check (view the frames/slides yourself,
run the grep, make the live call) before submitting. A relay is fine as a *cross-check* against
work you already did yourself; it is not a substitute for having done it. The producer who
built the artifact carries the certification, not whoever happened to relay a summary of it.

## 6. The lead's PMM gate (final gate, before `dam_submit_work`)

After every gate above passes, the lead reviews the artifact personally as the product
marketing professional (binding, GM directive 8 Aug 2026 - full mandate in `CLAUDE.md`,
"The lead's PMM mandate and gate"). The checklist gates above are the floor; this gate is
the bar:
- **On-message** - consistent with the positioning and messaging house, no drift.
- **Audience fit** - genuinely right for the buyer it claims (CIO / CMO / Solutions
  Architect), as a judgment call, not just rule-compliance.
- **Mission fit** - ships because it moves the $1M-to-$10M mission, not merely because it
  was briefed and built.
- **Defensible live** - nothing in it the lead could not stand behind in the room.

A FAIL here returns the artifact to the owning role like any other gate failure. The
verdict is recorded in one line in the DoP certificate or the DAM submission note.

## Screenshot-currency check (a repeat offender)

Reused screenshots go stale - a figure that changed after a code/data fix will silently
contradict the live product. Before trusting any reused shot, verify its key figures against
the live app/API; recapture if they differ. A stale number in a screenshot is a FAIL.
