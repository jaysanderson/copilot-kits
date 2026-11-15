---
name: arag-demo-app
description: Build a Progress Agentic RAG demo web app that presents as the CUSTOMER'S OWN system (their brand, domain language, UI), with ARAG working invisibly underneath - not an ARAG brochure. Use for "build a demo / POV / vertical demo". Encodes the 11 non-negotiable table-stakes gates (including a top-right "how this works" solution-architecture reveal) and the 22 binding standards added 17 Aug 2026 - now covering a hyperscaler-grade visual excellence bar (the exemplar is a polish bar, NOT a layout to clone), the Progress brand carrying through the WHOLE app not just the header, Progress-brand high-contrast controls and legible inputs, a friendly on-brand refusal via the ARAG search configuration, layout/archetype variety (not every demo is a top-menu app), rich catalogue surfaces (real thumbnails - never a placeholder icon - plus DA-generated copy + structured chips), the 2 Sep 2026 vibe-coded-audit standards (B33 inline superscript citations at the claim, B34 default-visible qualitative confidence badge - never a raw REMi number, B35 multi-row category-rail discovery with live counts, B36 a number on everything), a rich NDJSON-driven RAO "watch it work" surface, page-specific "how this works" reveals covering flow + what + why, charts-not-tables for any metrics surface, and a research-depth bar that must surface five genuinely diverse use cases - alongside measured anti-sameness, the Progress-branded header, vertical/horizontal anchoring, a minimum of five use cases, the mandatory pre-build research phase, responsive/mobile-first delivery verified at real phone width, per-demo persona selection, personalisation, manual journey stepping, single-voice-use-case default, prominent legible guided tours, and the leading-slash label-filter rule. Also encodes the named anti-patterns, the server-side-proxy pattern, seeded-synthetic content, the 30-second reset, and the independent automated QA gate (scripts/demo_qa_gate.py) required before delivery. Self-contained; pairs with the arag-kb and rao-workflow skills.
---

# Build a credible ARAG demo app

The bar: the buyer must feel they're looking at **their own product with AI already in it**,
not a Progress demo reel. ARAG works invisibly underneath. A capability tour, a vendor
showcase, or an empty shell fails. Incident detail behind every rule lives in
`content/sop/lessons/` (linked per standard); the verbatim prior edition is archived at
`content/sop/skill-archives/arag-demo-app-SKILL-2026-10-03.md`.

## Before building - the mandatory research phase (binding - Standard B5, GM directive 17 Aug 2026, extending the 2 Aug 2026 rule)

Research is the FIRST step of every demo build, before a line of code - named company and
vertical-only brief alike. Gather the anchor's real language, workflows, document/data
types, entities, roles and edge cases; that output feeds the seeded content. Realism is
researched, not improvised.

Classify a named company first, because it changes what the demo shows:
- **ISV selling software** - show an integration/OEM story: API-first, embeddable, their
  product's UI with ARAG-powered features inside, a path to "you ship this to your customers".
- **Operating company** - show ARAG solving their specific problem inside a mock-up of THEIR
  environment (the standard pattern in this skill).
- Both at once: build the stronger, more specific value story and say so in the brief.
(lesson: content/sop/lessons/demo-research-and-content.md#research-and-company-classification)

## Stack (in order of preference)
1. **Single-file HTML + vanilla JS + CDN imports** - fastest to demo.
2. **A small backend (e.g. FastAPI) serving a static frontend** whenever the ARAG API key
   must stay server-side - the default for anything shared externally. The key NEVER appears
   in client JS; the browser calls your backend, the backend calls ARAG.
Per-app secrets in a local `.env`; commit an `.env.example`, never the real keys.
Prerequisites: an ARAG account + service credential, Python for the proxy stack, hosting
(e.g. Fly.io). Stand up the Knowledge Box with the `arag-kb` skill.

## The 11 TABLE-STAKES gates (binding - no demo ships until every one passes)
1. **Seeded end to end** - realistic, domain-specific data on first paint of EVERY view. No
   empty states, no lorem, no placeholder shell.
2. **Chrome brand FORKS on named-vs-generic** (the old always-on Progress header is RETIRED -
   see B2). NAMED account: the account's OWN brand, NO Progress header. GENERIC: Progress
   Agentic RAG-branded + vertical-focused. Either way the body reads as the real product; no
   capability-tour hero; no exposed ARAG endpoint names (`/ask`, `/find`, `/graph`) or
   "Knowledge Box" in customer-facing views; full Progress mechanics only in the gate-11
   reveal. (lesson: content/sop/lessons/brand-and-polish.md#b2-chrome-brand-fork)
3. **One route per use case** - its own page and URL, never a tab-SPA. Shared nav is fine.
4. **A visible cited / grounded answer reachable in the seeded narrative** - and every
   citation clickable, navigating to the source's own view (deep-linked to the cited
   moment/section where the content type supports it). A citation that links nowhere is a
   real defect (Mediaportal, 5 Aug 2026).
5. **No hosting-region or infra string in any customer-facing view** - crop or neutralise.
6. **Discreet synthetic-content disclosure** - a small footer line only, never the headline.
7. **No real personal or third-party identifiers** - fictional brand (trademark-check the
   name), neutral demo logins.
8. **Visible polish** - zero broken assets, designed empty states, and ALL agent/AI answer
   text renders through a real markdown component, never raw syntax on screen (GM directive
   2 Aug 2026). Loose-list trap: ARAG returns numbered lists with a blank line between items;
   a hand-rolled renderer that closes the list on any blank line renders "1. 1. 1. 1. 1." -
   peek past blank lines, or use a real markdown library. Verify with a real multi-item
   numbered answer. (lesson: content/sop/lessons/demo-qa-and-reveals.md#the-11-table-stakes-gates-full-text)
9. **A working ask round-trip through the server-side proxy** - live answer, key never in
   client code.
10. **A documented 30-second reset** (seed/purge) so a botched live demo recovers fast.
11. **A solution-architecture reveal** - a small top-right button on every route ("How this
    works") opening a modal with THIS demo's actual request/data flow (browser -> app proxy ->
    the real ARAG mechanisms -> the rendered answer), visually engaging. The one deliberate,
    opt-in place ARAG branding and mechanics ARE shown.

## The 22 BINDING STANDARDS (added 17 Aug 2026, GM directive - apply to EVERY demo)

Each is a pass/fail check confirmed by the independent qa-reviewer at review time. Full
original text with incident history: the lesson files linked per standard.

- **B1. Anti-sameness, measured.** At review the demo is compared against the estate and the
  default config-shell skeleton; rendering as the default shell, or as a visual twin of an
  existing demo, FAILS.
- **B2. Chrome brand forks on named-vs-generic (GM directive 3 Sep 2026 - supersedes the
  17 Aug always-on Progress header).** NAMED account/lead: the account's own real CAPTURED
  look (use `anydesign`; palette colour-picked from the live site, real fonts/imagery/chrome),
  NO Progress header, ARAG only in the reveal + disclosure; bar = Holidayisle; Field Rule 8.
  GENERIC/unnamed: Progress Agentic RAG-branded + vertical-focused, built to the
  `progress-arag-branding` skill. Both kinds: a STUNNING experience to the unslop-ui floor +
  the CorpusKit/FRDC bar, never the generic scaffold.
  (lesson: content/sop/lessons/brand-and-polish.md#b2-chrome-brand-fork)
- **B3. Anchored to a specific horizontal or vertical** - concrete, never a generic
  "AI assistant" demo.
- **B4. Minimum five use cases per demo.** If the brief gives fewer, add the most appropriate
  ADJACENT use cases for the vertical to reach five; pairs with gate 3 (five real routes).
- **B5. Mandatory pre-build research phase** - the section above; research feeds the seed.
- **B6. Fully responsive, mobile verified at real phone width.** Internal-app demos get an
  app-like mobile experience (bottom tabs or a real drawer, touch targets, genuine reflow,
  not a shrunk desktop grid). Verification is a REAL phone-width render in a fresh tab (a
  resize does not reflow); desktop-only FAILS.
- **B7. Persona selection - required, configurable, per demo.** Declared from the DAM
  personas (CIO, Solutions Architect, ISV Product Manager, ICT Leader, Developer / builder;
  ground via `dam_list_personas` / `dam_get_persona`). No declared persona, or framing that
  does not match it, FAILS.
- **B8. Visual excellence bar - hyperscaler-grade, never monotone.** A real per-demo design
  system: palette with genuine range, intentional type scale, real depth, disciplined spacing,
  purposeful motion. "Passes the 11 gates" is the floor; the bar is "would a hyperscaler ship
  this". Build to the `artifact-design` and `progress-arag-branding` skills; knowledge-hub /
  catalogue / Ask demos walk `content/positioning/ui-polish-standard.md` (the CorpusKit/FRDC
  bar, https://frdc.corpuskit.org/t/frdc). The exemplar is **"The Courthouse Bid"**
  (`shots/reference-standard/courthouse-bid-hero.png` and
  `shots/reference-standard/courthouse-bid-document-viewer.png`) - a POLISH bar, NOT a layout
  to clone: **a demo that copies the exemplar's layout or motif FAILS, even beautifully
  executed.** Its nine transferable principles: immersive on-brand art direction; the CONTENT
  is the hero visual (the corpus is the beautiful object); narrative framing; a guided staged
  journey; high-fidelity seeded documents (a raw-text detail view is a FAIL); a tight palette
  with ONE accent; interactive affordances; honesty designed in as a visible element; on-brand
  throughout. (lesson: content/sop/lessons/brand-and-polish.md#b8-visual-excellence-and-the-courthouse-exemplar)
- **B8a. Ship-clean self-check (GM directive 1 Sep 2026).** Run the full DoP + table-stakes +
  `ui-polish-standard.md` section D checklist YOURSELF (automated gate + a real 390px render +
  every route) before the gate - the gate confirms, never discovers. The six recurring
  first-time misses to check at build time: ARAG invisible in the ambient chrome (grep the
  rendered chrome for "Progress"/"Agentic RAG"/"Nuclia"/"Knowledge Box"); per-item REAL
  imagery, no borrowing between entities, no repeats (a shared `used` set); grounded stats
  DETERMINISTIC (parsed server-side from the resource's own text, byte-identical across
  probes); warm refusals (strip the cold "Not enough data to answer this." at the shared
  server ask() choke point); the reveal is a real labelled DIAGRAM, not a numbered list;
  controls sized for their longest content at desktop AND 390px.
- **B9. Layout variety - not every demo is a top-menu app.** The archetype is a required,
  no-default scaffold input (parts bin: `content/positioning/demo-factory-package-upgrade.md`
  Section 2). The default top-menu skeleton when the archetype called for something else
  FAILS (and usually B1 with it).
- **B10. Catalogue/listing pages: real thumbnails + DA-generated copy + structured chips.**
  Per item: (a) a REAL visual preview of the resource itself (prefer the platform-extracted
  thumbnail/frame - Nuclia produces one for video); a bare icon, blank tile or repeated
  file-type glyph FAILS; (b) title/description GENERATED by a DA Generator from the item's own
  content - one Generator per content type drives listing AND detail; (c) JSON-schema
  structured fields as scannable chips. Named FAILs from the 2 Sep 2026 audit: the same
  description/icon repeated on every card; empty grey placeholder bars; a card image carrying
  browser chrome. Pass check: read three cards - each differs in title, description AND
  visual. (lesson: content/sop/lessons/brand-and-polish.md#b9-and-b10-layout-variety-and-catalogue-cards)
- **B11. RAO "watch it work" - a rich surface driven by the REAL NDJSON stream** (planning,
  iterations, tool calls with name + arguments, tool results, final answer - surface what the
  stream carries, never invent stages). A dreary flat undifferentiated log list is a DEFECT.
  Streamed markdown renders per gate 8.
- **B12. "How this works" reveal - page-specific, three-part, correctly placed trigger.**
  Per route: (1) this route's real technical flow, (2) what the page is doing, (3) the value.
  A generic app-wide flow, or tech-only with no what/why, FAILS. The trigger sits cleanly
  top-right, never straddling the header/content boundary. One shared component fed per-route
  specs. (lesson: content/sop/lessons/demo-qa-and-reveals.md#b11-and-b12-rao-surface-and-page-reveals)
- **B13. Reports/metrics = charts, not tables** (build to the `dataviz` skill); a table only
  for genuinely tabular data. A wall of numbers where charts would read better is a DEFECT.
- **B14. Personalisation - name PLUS role/persona in brackets** wherever a person appears
  ("Dana Whitfield (Fleet Operations Manager)"). A bare name is a DEFECT.
- **B15. Journeys default to MANUAL stepping** (next/back); auto-advance is opt-in only -
  a journey auto-advancing by default FAILS.
- **B16. One voice-interaction use case per demo by default**; more is a deliberate,
  brief-driven choice.
- **B17. Research depth must surface five genuinely DIVERSE, high-value use cases** - not
  five thin variations, and never missing an obvious flagship use case for the vertical (a
  call/voice demo missing call analysis). An obvious omission is a RESEARCH FAILURE and goes
  back to research, not forward to build.
- **B18. Guided tour - prominent, Progress-themed, high-contrast.** A barely-visible docked
  bar, white-on-white, or low-opacity text over a busy background is a FAIL.
- **B19. Label-filter paths MUST start with "/" in `filter_expression`** (e.g.
  `"/doc_type/compliance-bulletin"`) or the call 412s. Normalise in the shared `catalog()` /
  `useCatalog()` helper, never per call.
  (lesson: content/sop/lessons/arag-platform-quirks.md#b19-leading-slash-filters-and-integration-basics)
- **B20. Progress-brand controls, legible inputs.** Limited corner rounding (no large rounded
  "pills"), high contrast; a faint hairline outline with white text on near-black FAILS. Field,
  placeholder and typed text all clearly legible; faint input text is a FAIL.
- **B21. The brand carries through the WHOLE app.** An on-brand header over a generic
  dark-mode body is a FAIL - palette, type and art direction run from header to footer.
- **B22. Friendly, on-brand refusal via the ARAG search configuration's no-answer message**
  (see the `arag-kb` skill) - a blunt hardcoded "Not enough data to answer this." is a FAIL.
  The honest-decline behaviour never changes; the wording is warmed where ARAG configures it
  (which also shows in the console per gate 11).
  (lesson: content/sop/lessons/declines-and-no-fake.md#b22-friendly-refusal)
- **B23. A cited source opens scrolled to, and highlighting, the exact contributing passage.**
  Opening the document at the top with nothing marked is a FAIL. Retailer traps (3 Sep 2026):
  Nuclia indexes `title`, `summary` and `body` as THREE separate citable fields - render and
  match all three independently; extraction is inconsistent about bullet glyphs and quote
  marks - canonicalise excerpt AND body through the IDENTICAL transform, and verify across
  many doc shapes. (lesson: content/sop/lessons/citations-and-derived-surfaces.md#b23-and-b23a-citation-highlighting-and-raw-keys)
- **B23a. Raw-key citations are the COMMON case** (measured 3/4 to 5/5 of citations per
  answer with context-expanding strategies). In ONE shared code path: recover the rid with
  `pid.split("/")[0]` - NEVER `pid.split("/f/")[0]`, because title/summary citations have
  shape `<rid>/a/title/0-30` - fetch the real title + mime server-side, patch the card; if
  resolution fails, DROP the citation. Recompute derived counts after resolution. Gate:
  repeat the SAME question several times per ask surface - zero blank/generic cards, zero
  404ing citation links.
- **B24. The grounded answer + sources use the FULL width** - answer full-width, source tiles
  ACROSS the page. A short answer in a narrow column beside a tall vertical stack with a blank
  void is a FAIL (the GM "really dislikes" it).
- **B25. Related rails are genuinely related, with a human reason** ("Same category - floor
  care"), titled "Related products" / "Related documents". A YouTube-style "Up next" vibe or a
  raw relation label like `shares "product"` is a FAIL.
- **B26. Agentic orchestration grounds on structured (MCP tools) AND unstructured (KB)
  sources and shows BOTH** - the tool trail plus the KB documents beside it. Tools-only
  orchestration understates the product.
- **B27. Re-skin EVERY component reused from another demo** - grep for the source demo's
  brand/product/person names and purge every hit; and the visual QA pass must open the `/r/`
  (citation-target and list-detail) pages, which the automated gate does not brand-check.
- **B28. Charts showcase ARAG extracting STRUCTURED INSIGHT from UNSTRUCTURED data.** A chart
  a plain GROUP BY on existing record fields could build is a FAIL for this surface. Every
  "extracted by ARAG" claim is backed by a GENUINE extraction (a real DA task or `/ask` +
  `answer_json_schema` over the free text), tested live - relabelled authored values are a
  hard-rule-3 violation. (lesson: content/sop/lessons/declines-and-no-fake.md#b28-and-b29-genuine-extraction-and-disambiguation)
- **B29. Realism - seeded questions, tool contracts and agent behaviour survive "would this
  actually happen this way?".** Seeded questions carry the real identifiers ("status of repair
  booking RMA-10482", never a product line with many units); an under-specified query gets
  honest DISAMBIGUATION, never one confident answer as if exactly one record existed.
- **B30. Chart legibility.** No colliding inline series labels (use a proper LEGEND); axes
  scaled to the data's actual range (a REMi trend at 4.3-5.0 never on a 0-8 axis - REMi's real
  scale is 0-5). VERIFY in the rendered pixels at real size.
- **B31. REMi trust panels are stable and never DISPLAY a low value on a good answer.** Score
  against the FULL retrieved context (~8 paragraphs by score via an onContexts handler), never
  the thin cited excerpts; floor/smooth the count-up so no misleading low number renders
  mid-animation. Verify the settled score AND every animation frame.
- **B32. Mobile QA is a REAL 390px Playwright render** (`viewport={"width":390,...}`,
  `is_mobile=True`) - the claude-in-chrome tool clamps at ~485px, and "by-construction"
  reasoning is banned. Screenshot home, the OPENED menu and key routes, and VIEW them: opaque
  overlay backgrounds with backdrop + z-index; no floating control over content. Viewport
  blowout: a grid/flex item holding wide content balloons the layout viewport and breaks every
  `position:fixed` element site-wide - give it `min-width:0` + its own `overflow-x:auto`, and
  assert `document.documentElement.scrollWidth === 390` on every route before trusting any
  click-interception diagnosis.
  (lesson: content/sop/lessons/demo-qa-and-reveals.md#b6-and-b32-real-mobile-verification)
- **B33. Inline superscript citation markers IN the prose, at the grounded claim**, numbered
  to the source panel - a sources block with no inline markers is a FAIL. Proven
  implementation: inject `[[n]]` tokens SERVER-SIDE at the end of the sentence containing each
  kept citation's title mention (never let the model place markers); the client swaps them for
  `<sup>` links AFTER markdown rendering. Traps: skip abbreviation periods (Bros/Mr/Dr/St/vs/
  etc/single capital); CJK enders (。！？) take no following whitespace - match them bare;
  SNAP a mid-word char-offset to the next word boundary and group co-located markers into one
  insertion; do any length-changing cleanup (em-dash strip) AFTER insertion; strip the model's
  own em dashes to " - " at the render layer. Verify programmatically: zero mid-word splits,
  zero glued markers.
  (lesson: content/sop/lessons/citations-and-derived-surfaces.md#b31-b33-b34-remi-and-markers-and-badges)
- **B33a. Bespoke-composition builds ship DEAD scaffold pages - delete them, and don't
  false-FAIL them.** Delete the unused scaffold pages/defaults; a source-grep gate confirms a
  file is reachable from the bespoke `composition.tsx` render path before calling a string
  customer-facing - dead-code hits are lower-severity hygiene, never a blocking FAIL.
  (lesson: content/sop/lessons/demo-scaffold-quirks.md#b33a-and-b33b-dead-pages-and-manifest-drift)
- **B33b. A static slug->resource-id `manifest.json` DRIFTS on reseed** - new ids 404 every
  `/r/` page on fresh load. Resolve slugs LIVE, or regenerate the manifest as the LAST step of
  the ingest script itself. Verify with a Playwright DIRECT nav (not an in-app click) after
  any reseed.
- **B34. A default-visible QUALITATIVE confidence badge on every answer** - never a raw REMi
  numeral, never behind an opt-in, never absent. Derive with GROUNDEDNESS primary - never
  min()/equal-weight, which reads "Low confidence" on a correct narrow answer (REMi's
  answerRelevance penalises precise scope). A demonstrably grounded, correct answer NEVER
  reads "Low confidence"; keep it honest, don't force everything High.
- **B35. Discovery is multi-row category rails with LIVE facet counts** (the Netflix pattern,
  `ui-polish-standard.md` section B) - a flat grid or list as the only discovery surface is a
  FAIL. Counts come from the real KB (`/catalog` GET form only, per the cross-tenant POST leak
  in CLAUDE.md) and must reconcile to the corpus.
- **B36. A number on everything** - corpus scale on the hero, live counts per category/facet,
  retrieved-vs-cited counts and per-source relevance % on the answer surface. Numbers are real
  (queried or counted), never invented. A headline surface with no real number where the data
  has one is a FAIL.
- **B37. Run the `unslop-ui` skill as a binding design gate** - the anti-slop FLOOR beneath
  the CorpusKit/FRDC bar; a demo that trips its checklist FAILS. The AMBITION bar is Maison
  Vellier (`content/mockups/maison-experience.html`).
  (lesson: content/sop/lessons/brand-and-polish.md#b35-b36-b37-rails-numbers-unslop)

**B38-B46, the measured audit set (binding, lead, 1 Oct 2026, from the Better Together
Library audit, `content/audits/better-together-library-quality-bar-2026-10-01.md`; the GM:
"the same quality bar, if not higher"). Every one is a MEASUREMENT with a threshold. NOTE:
these numbers collide with the 3 Sep GM acceptance set below - both kept as sourced.**
(lesson: content/sop/lessons/brand-and-polish.md#b38-to-b46-measured-audit-set)

- **B38. The H1 reflows, measured:** computed `font-size` at 1440x900 vs genuine 390x844
  (`is_mobile=True`) - mobile at least 20% smaller, hero inside the first 844px; equal values
  are an automatic FAIL.
- **B39. No nav label wraps, counted by LINE BOXES** via `Range.getClientRects()` grouped by
  distinct `top` (never box height divided by line-height). Zero labels over one line box at
  1440x900; at 390px the nav is a drawer or hamburger.
- **B40. The palette is named `--color-*` tokens on `:root`:** at least 6 named tokens, 4
  distinct painted background values, 4 text values, two hue families - distinct hexes, not
  one hue at several opacities.
- **B41. Quantification floor:** at least 25 numeric tokens in `document.body.innerText` on
  the primary discovery route, at least 8 on every other; every on-screen count derivable from
  live data, three spot-checked.
- **B42. A low-confidence badge shows an ACTION:** below threshold, drop every numeral and
  name the verb ("REMi · check the sources"); a badge reading only "Low confidence" is a FAIL.
- **B43. Price the latency on the control** ("Quick answer ~3s" / "Research agent ~10-20s")
  for any multi-mode or >3s-to-first-token affordance; the stated figure sits inside the
  measured p50-p90 over 5 runs.
  (lesson: content/sop/lessons/demo-timeouts-and-regimes.md#b43-price-the-latency)
- **B44. A citation card states its MODALITY** (`SPOKEN`, `ON SCREEN`, `IN DOCUMENT`) + the
  verbatim retrieved text + a deep link, before the click, on 100% of cards across 3
  differently-shaped questions.
- **B45. The provenance line names the denominator** ("Answered in 3.2s from all 39 videos ·
  12 passages from 6 videos"); the corpus figure matches the surface's own published count or
  the gap is explained on the page.
- **B46. Microcopy is state-aware:** rest and active instruction lines differ, the active one
  names the exit, a live region announces the change.

**The GM demo acceptance bar (binding, GM directive 3 Sep 2026 onward - the GM approves only
a demo with NONE of these; the lead's gate drives every surface for them):**

- **B38 - no error/fallback banner on a customer surface.** A legitimate fallback is
  disclosed ONLY in the "How this works" reveal, never as ambient chrome - and VERIFY the
  named mechanism is real and actually invoked before disclosing (a disclosed RAO fallback
  when the code never calls RAO is itself a false claim; describe the real mechanism
  accurately instead). SECURITY: any golden-cached-trace fallback MUST be gated on the
  CALLER'S role, or a timeout serves another role's confidential answer past RBAC (the MARTY
  VDR leak) - test every role under a FORCED timeout.
  (lesson: content/sop/lessons/demo-qa-and-reveals.md#acceptance-b38-fallback-banners-and-rbac)
- **B39 - REMi visibly demonstrated, and REMi-DERIVED.** "No raw numeral" (B34) never means
  removing REMi; stripping it is a FAIL, and a non-REMi proxy badge is a FAIL. On a RAO/
  tool-grounded surface, pass the agent's TOOL-RETURNED records as the REMi context or it
  intermittently returns nothing - "Trust read unavailable" on a successful ask is a FAIL;
  verify across several repeat runs. A tool-sources panel shows human copy ("Fault records for
  Unit 14 - 3 entries"), never raw field names.
  (lesson: content/sop/lessons/citations-and-derived-surfaces.md#acceptance-b39-and-b45-remi-and-per-scope-click-through)
- **B40 - perfect navigation** at desktop AND genuine 390px; separate primary nav from
  utility/role controls - it reads as designed, not assembled.
- **B41 - a real, crafted logo** - a letter/glyph in a rounded or gradient square is
  vibe-coded slop, not a logo.
- **B42 - no vibe-coded / "dark coding" / generic dark-SaaS gestalt** - a taste judgment the
  lead makes on the live build, not a checklist item.
- **B43 - EYEBALL the rendered answer prose on the live Ask surface.** An answer + citations
  + badge can still render garbled ("The - Klingon - Empire - ..." passed every gate); READ
  the prose for spurious separators, shattered wrap, raw markdown and doubled punctuation, on
  more than one route. "The ask worked" is not the check.
- **B44 - dash regexes match ONLY dash codepoints by explicit escape:**
  `String(s).replace(/\s*[—–]\s*/g, ' - ')`. A class like `[ - –]` is a RANGE (space..en-dash)
  that replaces every SPACE and hyphenates every word. Grep every build for `replace(/[ - `
  (server AND client copies). The scrub's SCOPE is every customer-facing string - static copy,
  reveal specs, seeded corpus - verified by a LIVE grep of every deployed route and opt-in
  endpoint, never a local file grep alone.
  (lesson: content/sop/lessons/demo-scaffold-quirks.md#b44-b46a-b49-input-and-render-bug-classes)
- **B45 - verify citation click-through on EVERY universe/scope/KB** - prefer a direct
  endpoint probe (curl the manifest's resource id against the endpoint the detail page
  actually calls); one scope resolving is never proof the others do.
- **B46 - NO unrendered markdown anywhere in the app, EVER.** GM: "we should never ever see
  unrendered Markdown within the application, whether it's citations or otherwise. It looks
  ugly and unsightly." Every text surface - answer, citation modals, detail pages, cards,
  tooltips, tours, reveals - renders through the shared markdown renderer. The automated
  gate's RAW_MARKDOWN_RE cannot see behind a click, so the demo-tester opens citation/source
  modals and secondary surfaces and reads them. Grep the seed corpus too.
- **B46a - a CSS `display` rule on a class silently DEFEATS the `hidden` attribute** (two
  live instances in one day). Every app stylesheet carries `[hidden]{display:none!important}`;
  no `display` on a class JS toggles via `.hidden`. Gate: a real coordinate/locator click on
  elements a backdrop could cover, plus a CSS grep.
- **B46b - an inline reveal-spec object is NOT opt-in to the leak scanner or view-source.**
  Serve reveal specs from a server endpoint (`GET /api/reveal/{page}`) fetched in the click
  handler, so mechanism strings do not exist in any page's markup until the interaction.
- **B47 - CRITICAL, SHIP-STOPPING: NOTHING is faked without explicit GM permission; a demo
  may never show a capability Progress Agentic RAG cannot genuinely do (GM directive 4 Sep
  2026).** GM: "nothing should ever be faked without explicit permission. If we show something
  that is not possible with Progress Agentic RAG, we are in big trouble, and this is a massive
  failure." Every apparent capability runs on a real ARAG call at run time; faking, mocking,
  hardcoding, pre-canning or staging one is the single worst failure, above every other gate.
  NOT a violation: disclosed synthetic corpus DATA, and the disclosed honest fallback of hard
  rule 3's corollary. If a capability isn't genuinely possible: REMOVE it, or show it behind a
  visible honest marker ONLY with explicit GM permission. Enforced at every layer: the builder
  self-declares which real ARAG call powers each capability; the demo-tester probes the
  round-trip; qa-reviewer maps claims to mechanisms; the lead's gate ships nothing faked. When
  in doubt, treat it as faked until proven real; a needed non-ARAG shortcut means STOP and ask
  the GM first. Currency corollary: research/capture evidence that a seeded item is retired or
  changed is RESOLVED before ship (verify live, reseed or exclude-and-disclose), never
  stranded in a build-side file.
  (lesson: content/sop/lessons/declines-and-no-fake.md#b47-and-b50-no-fake-fabrication-and-drift)
- **B48 - a customer-facing experience must DRIVE A BUSINESS OUTCOME (GM directive 8 Sep
  2026).** Conversion (buy / book / sign-up / captured lead) or deflection, with a clear REAL
  call-to-action at the natural moment, deep-linked to the real purchase/booking flow. The
  demo links OUT - it never fakes or processes a transaction - and recommended items are
  grounded in real KB data. FAIL if it only answers nicely with no conversion or deflection
  path. Checked by demo-tester and the lead's gate; see CLAUDE.md Field Rule 10.
- **B49 - live-editing inputs:** never rewrite/recreate the node under edit during its own
  input event (a lone "-" parses NaN and clears the field mid-keystroke; normalise on BLUR,
  visibly); a blur handler rebuilds ONLY its own field, never a full renderAll (a race -
  test sequential fills 3x); prefer `type="text"` + `inputmode="decimal"` + a keydown filter
  over `type="number"`. Gate: per-key "-", "-5", "-50" hold then clamp on blur; three-field
  sequential fill 3/3; caret click-insert. Tester trap: Chromium 151 ignores Home/End/Arrow
  caret keys in any input below the initial scroll offset - reproduce on a bare-input control
  page before failing the app.
- **B50 - a perfectly scoped retrieval can still INVENT figures, and a prompt line alone does
  not stop it.** For commerce-critical figures (prices, dates, capacities, terms):
  deterministically parse the real figures server-side and INJECT them verbatim as ground
  truth at the single shared ask choke point, forbidding any other figure (a two-tier price
  survives as both numbers); CTA/card figures stay deterministically parsed, never
  model-generated. Gate: repeat price-intent questions at least 5x across 3 phrasings - any
  figure not verbatim in the seeded content on ANY run is a CRITICAL FAIL (no-fake class).
  Corollary: seeded REAL commerce data DRIFTS (4 of 7 live prices moved in a week) - every
  gate re-checks seeded figures against the LIVE site (real browser; such sites 403
  automation) and the surface carries a discreet in-voice freshness line.

## Named anti-patterns (do NOT copy these - they're why demos fail the room)
- "POWERED BY <vendor>" header + exposed endpoint names in customer views. Narrow GM-directed
  exception: a demo whose entire premise IS the vendor's own product/community (PUG Tube) can
  carry the real vendor logo in the header - scoped per item, never a general licence.
- A capability-tour hero; an unseeded default installation page; a real third-party brand used
  as if owned; a prefilled real email; a visible hosting-region/host string; the tab-SPA.
- Theming against a real live brand site: match the DEFAULT RENDERED STATE (light vs dark,
  ambient/decorative chrome), not just scraped colour/font tokens - byte-accurate tokens on
  the wrong base mode still read as "generic AI startup". When a reviewer repeats "doesn't
  match the brand" after a token-accurate pass, do a live side-by-side screenshot comparison
  before re-scraping. (lesson: content/sop/lessons/brand-and-polish.md#named-anti-patterns-and-brand-mode-matching)

## Excellence markers (aim for; don't gate on)
Persona/audience switching that changes the answer register; an in-product quality signal
(prove quality with REMi/citations, NEVER a fabricated accuracy number); honest failure
surfacing; the live process shown; faceted navigation over seeded data; multilingual
answering.

## Content
- **Build order (binding - B5):** research FIRST, then design the seeded corpus from it, then
  build. **Scaffold inputs fixed before scaffolding:** the anchor (B3), the archetype, a
  minimum of five use cases (B4), the persona(s) (B7).
- Seeded synthetic corpus per use case, credible for the vertical; fictional people/brands
  only; **trademark-check** any invented name; ship a **seeded demo narrative** (what to
  click, what to ask, the wow moment per route) and the **30-second reset** in the README.
- **Don't hardcode logic to the seed count** (Mediaportal, 5 Aug 2026): Jay bulk-uploads real
  content after approval - 5 seeded items became 219 and broke a catalog scan capped at
  page_size 60, seed-slug-only thumbnails and a stale disclaimer. Resolve by resource id and
  work at arbitrary corpus size from day one.
- Thumbnails: prefer the platform-extracted thumbnail/frame (automatic for video) - it covers
  every future upload; hand-generated ones only cover the items you made them for.
- KB-driven listings: one DA Generator per content type produces title/summary/highlights/
  pull-quote, driving listing AND detail.
(lesson: content/sop/lessons/demo-research-and-content.md#content-and-seeding)

## ARAG integration
- Check the current endpoint spec against a live reference before writing any call; working
  code beats docs.
- Auth header: `x-nuclia-serviceaccount: Bearer <key>` (or per the current spec), server-side
  only.
- **Hard-scope every `/ask`, `/find` and REMi call to this demo's own resources** - a KB can
  hold several demos' content (see the `arag-kb` skill).
- ARAG as the agent over the app's live data: the `rao-workflow` skill. Provision/seed with
  `arag-kb`.

## Region / residency (binding)
If the credential provisions KBs in only one zone, do NOT host a live demo for a customer
whose residency differs - a wrong-region host string fails gate 5. Synthetic/public demo KBs
can be any zone; crop the region string regardless.

## Deploy + verify
- **Version every static asset URL** (`chat-widget.js?v=2`, bumped per deploy) plus
  `Cache-Control: no-cache, must-revalidate` - a verifiably shipped JS fix can still run OLD
  code via a URL-keyed code cache (Bay-co Bay, 2 Sep 2026: fresh curl AND a fresh tab both
  showed the new source while the DOM ran the old closure). Only driving the real interactive
  DOM element proves a fix landed.
  (lesson: content/sop/lessons/demo-scaffold-quirks.md#stale-code-cache-and-asset-versioning)
- Deploy (e.g. Fly.io) with the ARAG key as a server-side secret. Verify EVERY gate: load each
  route (seeded first paint), a live cited ask round-trip, grep the client bundle + API
  responses for key/host/region strings, view every screen, confirm the reset. Then an
  independent reviewer gates it (the `grounded-artifact` skill).
- Per-standard checks on the live build: real phone-width mobile in a fresh tab (B6); declared
  personas match the framing (B7); controls and inputs on-brand and legible (B20); brand
  through the whole app (B21); drive a no-data query and check the refusal wording (B22); grep
  rendered pages AND corpus/config source for "Knowledge Box", "Nuclia", "KB", `/ask`,
  `/find`, `/graph` outside the reveal; inline markers, qualitative badge and real numbers on
  the answer surface (B33/B34/B36) and category rails with live counts (B35); every reveal
  page-specific and three-part (B12).
  (lesson: content/sop/lessons/demo-qa-and-reveals.md#deploy-and-verify-checklist)
- **Run `scripts/demo_qa_gate.py --url <live-url> [--config apps/<slug>/demo.config.json]`
  against the LIVE deployed URL before delivery, and it must exit clean (binding, GM directive
  8 Aug 2026)** - it drives the live app in a real browser and catches what a code read misses
  (routes 401ing in production). Fix-and-recheck loop on any FAIL; see CLAUDE.md Workflow 5's
  independent QA gate (automated gate + demo-tester + qa-reviewer, all three).

## Four live-only bug classes from the Next.js/Docker/Radix stack (taxonomy builder, 23 Sep 2026)
All four shipped clean through build, typecheck and lint, and were only caught by driving the
LIVE deployed app. Check them on any Next.js or Radix build:
1. **Next.js standalone Docker builds BAKE env values into static routes at image build
   time** - runtime Fly secrets never reach them; read env in a dynamic route/handler.
2. **Radix ScrollArea's internal `display: table` wrapper defeats `truncate`**; grid children
   default `min-width: auto` and refuse to shrink - set `min-w-0` on the track that must
   truncate.
3. **Per-component store hooks are not shared state** - two tabs calling `useXStore()` get
   two copies; cross-tab state goes in one Context Provider.
4. **Sequential mutator calls across an async gap clobber via stale closures** - commit
   through a ref-backed updater or one reducer action.
(lesson: content/sop/lessons/demo-scaffold-quirks.md#nextjs-docker-radix-live-only-bug-classes)

## A shipped demo stays under standing health monitoring, not just a one-time gate
Every gate here fires once at submission. Clinic passed all of them, was submitted at
07:59 on 29 Sep 2026, the platform's generative models started failing at 08:02, and the GM
opened it in front of a customer and got errors. `scripts/estate_health.py` is the standing
watch: it probes every live demo's REAL answer path (a 200 on the SPA shell proves nothing),
asserts HTTP 2xx + a non-empty answer + latency under threshold + no known error string riding
a 200, never fails a genuine honest decline, carries an explicit timeout on every request (a
stalled connection with no timeout never rejects), and runs its own `selftest()` against
planted good/bad samples before trusting the sweep.
Run: `.venv/bin/python scripts/estate_health.py` (`--only slug1,slug2` to scope,
`--selftest-only` to prove the checker, `--json-out <path>` for the machine summary);
non-zero exit on any FAIL. **Add a new demo the moment it ships** - one `TARGETS` entry,
built by reading the app's own server code for its real answer-path route and shape (streamed
NDJSON, flat JSON, SSE, cookie or bearer auth all appear in the estate, never guessed). The
script's Fly-apps discovery pass prints any live app not claimed by `TARGETS` - check that
list. (lesson: content/sop/lessons/demo-qa-and-reveals.md#standing-health-monitoring)
