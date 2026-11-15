# Definition of Pass - demo apps

Trimmed from `reference/DEFINITION-OF-PASS.full.md` to the lines that apply to a demo app. Line ids are stable; prompts and agents cite them. One FAIL on a line marked (B) means not done. A PASS without evidence is a FAIL.

## 1. Truth
- **T1 (B)** Every ARAG capability claim maps to a real mechanism documented in `reference/skill-arag-kb/SKILL.md` or `templates/portal/docs/ARAG-API.md`. Nothing from memory. Unconfirmed claims are flagged, never kept silently.
- **T2 (B)** Nothing is faked. Every capability shown runs on a real ARAG call at run time. Synthetic corpus data is allowed and disclosed; a mocked, hardcoded, pre-canned or staged capability is a critical FAIL.
- **T3 (B)** No silent substitute. A workaround that still routes through a real ARAG call may ship, and the `How this works` reveal states which mechanism was used and which was unavailable. With no ARAG call involved, the capability does not ship as a feature.
- **T4 (B)** No fabricated numbers: no accuracy, adoption, ROI or benchmark figure. Quality is shown with REMi and cited answers. Demo figures are labelled as demo figures.
- **T5** Certifications (SOC 2, ISO and similar) named only if verified outside the KB.
- **T6 (B)** Locked facts hold: every number on screen matches `BRIEF.md` LOCKED FACTS exactly.
- **T7** Statistics come from named independent sources, cited; nothing older than five years without a date; market sizing is a named provider plus a range; never the prospect's direct competitor as a source.
- **T8** Pricing in USD; no legible geo-localised price anywhere, even in a crop.
- **T9 (B)** Commerce-critical figures (prices, dates, capacities, terms) are parsed deterministically server-side and injected as ground truth; five repeats of a price question across three phrasings never produce a figure absent from the seeded content.
- **T10** Generated copy never merges two separately stated figures into one range. Generated numbers are spot-checked against the source page.
- **T11** Every on-screen count is derivable from live data (corpus size, facet counts, retrieved and cited counts); three counts spot-checked.

## 2. Safety and hygiene
- **S1 (B)** No secret, key or token in client code, any artefact, `demo.config.json`, logs or git. `.env` is gitignored; `.env.example` has empty values.
- **S2 (B)** No hosting-region, zone or infra string in any customer-facing view or screenshot.
- **S3 (B)** Other customers' names and identifiers anonymised everywhere.
- **S4** No real third-party brand used as if owned; no real personal identifiers; fictional entities and neutral demo logins only; invented names trademark-checked.
- **S5 (B)** Any cached or fallback answer path is gated on the caller's role; every role tested under a forced timeout.
- **S6** Every outbound HTTP call carries an explicit timeout.

## 3. Language and voice
- **L1 (B)** Australian English. No em dashes; a spaced hyphen " - " instead. Dash scrubbing matches dash codepoints only, never a character range containing a space.
- **L2 (B)** Banned words absent from UI copy, seed corpus and config: delve, leverage, unlock, seamless, game-changing.
- **L3** De-AI pass done: no hedging, filler, symmetrical triads or corporate fluff.
- **L4** Room test: it survives a CIO, CMO or Solutions Architect in the room.
- **L5** Refusals are warm and in the product's voice. The platform's fixed first sentence is handled at the UI layer; the decline decision stays ARAG's.

## 4. Demo app gates
- **D1 (B)** Seeded end to end: realistic domain data on first paint of every view. No empty states, lorem or placeholder shell.
- **D2 (B)** Presents as the customer's or vertical's own system. Named prospect: their captured brand, no Progress header. Generic: Progress brand. No "powered by" chrome, no capability-tour hero, no `/ask`, `/find`, `/graph`, `Knowledge Box` or `nuclia` in customer-facing views outside the reveal.
- **D3 (B)** One route per use case, five use cases minimum, each on its own URL.
- **D4 (B)** A visible cited answer reachable in the seeded narrative. Every citation is clickable and opens the source scrolled to the highlighted passage, verified on every scope or KB.
- **D5 (B)** Inline superscript citation markers in the prose at the claim, numbered to the sources panel; markers placed server-side from offsets.
- **D6 (B)** A qualitative confidence badge visible by default on every answer, REMi-derived with groundedness primary. Never a raw numeral, never absent, never "Low" on a demonstrably grounded answer. Below threshold it names an action.
- **D7 (B)** All AI text on every surface (answers, citation modals, detail pages, cards, tooltips, tours, reveals) renders through a real markdown renderer. No raw markdown anywhere. Tested with a multi-item numbered answer.
- **D8 (B)** The rendered answer prose is read: no hyphen between every word, no shattered wrapping, no doubled punctuation, on at least two routes.
- **D9 (B)** A working ask round-trip through the server-side proxy. The browser never calls ARAG.
- **D10 (B)** A documented reset that runs in about 30 seconds (`seed.py --purge` style); the script regenerates every id-keyed file after a reseed.
- **D11 (B)** A `How this works` reveal, top-right on every route, page-specific and three-part (this route's real flow, what the page does, why it matters), drawn as a labelled diagram. The only place ARAG branding and mechanics appear.
- **D12 (B)** Fully responsive. Every route verified at a real 390x844 render (`is_mobile=True`): drawer or hamburger nav, opaque overlays with backdrop, no floating control over content, `scrollWidth === 390`. Desktop verified at 1440x900.
- **D13 (B)** Visible polish: zero broken assets, zero console errors, zero failed network responses, designed empty and error states, no raw error pages, no error or fallback banner on a customer surface.
- **D14 (B)** Every chip, suggested question, follow-up and card click does something, and its content is relevant (no sitemap, terms or contact pages as suggestions).
- **D15** Discreet synthetic-content disclosure in the footer only, never the headline.
- **D16** Anti-slop floor (`reference/skill-unslop-ui/SKILL.md` checklist) passes: no icon-in-square, no emoji icons, no glassmorphism, no gradient text or buttons, no glow shadows, no card-in-card, no entrance animations.
- **D17** Brand through the whole app, header to footer, with high-contrast legible controls and inputs. Palette as named `--color-*` tokens on `:root`.
- **D18** Catalogue cards carry a real per-item visual, generated title and description, and structured chips; three sampled cards differ in all three.
- **D19** Discovery uses category rails with live facet counts from `/catalog`; a flat grid as the only discovery surface fails.
- **D20** The answer and its sources use the full width. Every person shown has a role in brackets. Journeys step manually by default.
- **D21** Charts, not tables, for metrics; charts show ARAG extracting structure from unstructured text, with a legend and axes scaled to the data.
- **D22** A customer-facing experience drives a business outcome: a real call to action deep-linked to the real purchase or booking flow, never a processed transaction.
- **D23 (B)** Deployed to its own Fly machine with `min_machines_running = 1`; `tools/predeploy_check.py` passed from a clean checkout and its `--control` run failed; static asset URLs versioned.
- **D24 (B)** Independent gate: `tools/demo_qa_gate.py --url <live>` exits 0 against the live URL, plus a separate `/qa-gate` or demo-tester pass. A known FAIL never ships with a note.
- **D25 (B)** Admin-console verification: every mechanism the README or reveal names exists on the KB (`/search_configurations`, `/tasks`, `/labelsets`, `/extract_strategies`).
- **D26** Backend breadth: labelsets applied, a named search configuration per surface, and the DA tasks the corpus justifies; or a recorded cost exception with the estimated call count and cost written in the README.
- **D27** Agentic routes ground on both MCP tools and KB documents and show both. ARAG is the agent; the app does not run its own planner.
- **D28** README carries the demo narrative, the reset command and time, and a self-declaration mapping each capability to the real ARAG call that powers it.
- **D29** The demo is added to `tools/estate_health.py` `TARGETS` with its real answer route.

## 5. Evidence
- **E1 (B)** A PASS is only a PASS with evidence attached: the screenshot viewed, the grep output, the KB API response, the live round-trip body, the URL opened. "Looks fine" is a FAIL.
- **E2 (B)** A relayed verdict is not evidence. The reviewer sees the output or redoes the check.
- **E3 (B)** A check that skips itself or cannot fail is a FAIL. Scanners run their selftest before the sweep.
- **E4** Reused screenshots are re-verified against the live app before use; a stale figure is a FAIL. Final rounds are marked `FINAL-`.
