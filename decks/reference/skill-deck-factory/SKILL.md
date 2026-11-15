---
name: deck-factory
description: >-
  Build or renovate customer-branded sales decks for an AI platform (Progress
  Agentic RAG / Nuclia), grounded in verified claims, as a 16:9 .pptx.
  CREATE mode: "build a deck for <customer-domain>, demo at <demo-url>".
  RENOVATE mode: "renovate <path.pptx> as <brand> for <audience>".
  TEMPLATE mode: build on the official Progress corporate template (native
  Progress branding/layouts) — "build/create <deck> on/using the Progress template".
  Use for any sales/pitch/proof deck, or to rebuild an existing deck for a new
  brand or audience. Triggers: deck, slides, pitch, proof deck, renovate, rebrand,
  Progress template, corporate template.
---

# Deck Factory

Two modes. Scripts live in `scripts/` next to this file; outputs go to `brand/`,
`shots/`, `decks/` in the current working directory.

## Environment
Each Bash call is a fresh shell — activation does **not** persist. Call the venv
python directly: `.venv/bin/python <script>`. One-time setup if missing:
`python3 -m venv .venv && .venv/bin/pip install playwright python-pptx pillow
requests && .venv/bin/playwright install chromium` (+ `poppler` via brew for pdftoppm).

## Brand kits
`brand/<name>.json` is a reusable kit; select it when building with env
`DECK_BRAND=<name>` (e.g. `DECK_BRAND=progress .venv/bin/python scripts/build_deck.py …`).
Customer domains still work via live capture (default writes `brand/brand.json`).
- `primary` = brand accent (saturation-weighted). `ink` = dark colour for
  full-bleed slides/headings; `build_deck.py` auto-uses `ink` when `primary` is
  too light for white text.
- **Always VIEW the capture and confirm `primary` is the brand identity, not a
  background or photo colour; fix manually.** (Progress green `#5ce500` sampled
  from the logo, not the navy site.)
- Photography-heavy / HubSpot sites: sample the **hero/nav crop**, not the photos;
  palette must come from the **screenshot**, not CSS (image CTAs aren't in CSS).
  Grab `og:image` and referenced design assets (dot-motifs, banners) as brand assets.

## 1. Brand capture — [scripts/brand_capture.py](scripts/brand_capture.py)
`brand_capture.py <domain> [kit-name]` → `brand/<kit>.json` (logo, fonts, palette,
saturation-weighted `primary`) + logo file. Then
[scripts/render_logo.py](scripts/render_logo.py) `<logo.svg>` makes white/black
PNGs; crop the logo mark for a faint watermark + icon tiles (Pillow). Do **not**
install/fake the brand's real fonts — the deck uses Calibri.

## 2. Demo exploration — [scripts/shot.py](scripts/shot.py)
- Map first: `shot.py --url <demo-url> --links`.
- Screenshot promising pages/states (`--full`, `--wait <ms>`, `--click "<css>"`).
  Interactive states may need a click then a wait.
- **VIEW every screenshot** — never select blind.
- **Editorial CIO/exec test:** keep only 4-6 shots worth showing — problem space,
  the ask experience, an answer *with citations*, anything impressively live.
  Rename picks `shots/demo-01.png…` with a one-line caption each.

## 3. Backend capture (if a dashboard URL is given)
- Auth: [scripts/save_auth.py](scripts/save_auth.py) `<dashboard-url>` opens a
  **headed** window; user logs in **there**; auto-detects the "Resources list"
  nav and writes `brand/arag-auth.json` (**gitignored**, **expires** — re-run if a
  later capture redirects to an empty root).
- Capture: `shot.py --auth brand/arag-auth.json --url <page> --wait 5000`. SPAs
  race `networkidle`; if a page comes back blank, wait for real content (e.g. a
  Playwright wait for the "Showing … out of" row text) before shooting.
- Ask playground: [scripts/ask_capture.py](scripts/ask_capture.py)
  `<kb-base-url> "<question>" out.png` waits for the **"Ask more"** end marker (not
  early "Sources" text) so the cited answer is fully streamed.
- REMi: [scripts/remi_capture.py](scripts/remi_capture.py) `<remi-url> out.png`
  sets the period to its **max (last 30 days)** — Health-status bars only populate
  then. Crop out header/sidebar.
- Rename picks `shots/backend-01.png…`.

## 4. Anonymise + region check (mandatory)
- **Never ship other customers' or account names.** Navigate straight to the
  customer's box; crop headers/sidebars/switchers; blur stray names (Pillow) or drop the shot.
- **Data residency:** read hosting/region strings in backend shots (e.g. "Europe
  (GCP)", "<zone>"). Flag them against the customer's stated residency
  requirement *before* including the shot.

## 5. Ground the copy — nuclia-mcp
Before writing any capability claim, `search_documents` the KB for what you
assert: retrieval/citations, enrichment (Data Augmentation) agents, REMi (RAG
Triad: Answer Relevance, Context Relevance, Groundedness), deployment/hosting.
**Only claim what the KB confirms.** Name the product as the customer sees it.

## 6. Build — [scripts/build_deck.py](scripts/build_deck.py)
A **template**: auto-loads the selected kit's `primary`/`ink` + logo assets; edit
customer name, KB-verified copy, chosen shots, contacts per deck.
`DECK_BRAND=<kit> .venv/bin/python scripts/build_deck.py decks/<name>.pptx`.
Structure (16:9): **1** title · **2** problem · **3** answer (KB-verified) ·
**4-6** demo shots · **7-9** backend shots · **10** next steps. Pick the strongest
4-6 shots overall — don't use all.

Design rules:
- Brand primary/ink dominates title + closing (subtle gradient + faint logo-mark
  watermark + a "Presented by / Powered by" pill); content slides white.
- Headings **bold UPPERCASE Calibri**; body Calibri. Never fake uninstalled fonts.
- Motifs: circle number-badges (problem), brand-mark icon tiles (answer), white
  cards with a soft drop shadow. No accent stripes, no bars under titles.
- Screenshots get a thin neutral border + subtle drop shadow; 11pt muted caption
  under each; small footer (wordmark + page number) on content slides.
- Match the customer's locale spelling; no em dashes; no text-only slides.

## 7. QA loop (mandatory, one cycle)
1. `soffice --headless --convert-to pdf decks/<name>.pptx`; if `soffice` absent,
   use installed **Microsoft PowerPoint** via `osascript` (`save … as save as PDF`)
   — **quit PowerPoint first**, it serves a stale cached copy otherwise.
2. `pdftoppm -jpeg -r 150 decks/<name>.pdf decks/qa/slide`.
3. **View every slide.** Fix overflow, overlap, low contrast — one fix-and-verify
   cycle, then stop. Deliver `decks/<customer>-<platform>-<date>.pptx` + slide images.

---

# RENOVATE mode
"renovate `<path.pptx>` as `<brand>` for `<audience>`". Rebuild, never patch.

1. **Inventory the source.** Convert to PDF + `pdftoppm` images and **VIEW every
   slide**; extract all text (`unzip -p … ppt/slides/*.xml`, or `pdftotext`).
   Produce an **audit table**: `slide | keep / rewrite / cut / merge | what's missing`.
2. **Show the audit + the proposed new outline. WAIT for approval before building.**
3. **Rebuild from scratch** with `build_deck.py` into a fresh template — never edit
   the old file in place. Salvage usable assets (screenshots, charts, logos) by
   extracting media from the unpacked deck: `unzip -j <path.pptx> 'ppt/media/*' -d shots/salvage/`; VIEW and keep only what passes the editorial test.
4. **Re-verify every product claim** against nuclia-mcp before it survives into the
   new deck. **Flag claims the KB can't confirm** — do not silently keep them.
5. **Fill gaps** to an outcome-led exec arc: situation → cost of inaction → the
   answer → proof → commercial path → next step. Draft missing slides and mark them
   **[NEW]** in the audit.
6. **Full QA loop** as create mode.

---

# TEMPLATE mode — build on the official Progress corporate template
Trigger: "build/create `<deck>` on the Progress template" (or "corporate
template"). Produces a deck with **genuine Progress branding** — the real logo,
the green/blue "ribbon" motif, the copyright footer and page numbers all come
from the template master, not redrawn.

**Template asset:** `brand/templates/progress-corporate-fy26.pptx` (the FY26
corporate deck). This is the single source; to **update it**, drop a newer
Progress `.pptx` there under the **same filename** and rebuild. If Progress
reorders the master, re-verify the `LAYOUTS` indices (below) with the probe.

**Builder:** [scripts/build_progress.py](scripts/build_progress.py) — the worked
example (John Menagh's "AI That Delivers"). Edit its content/notes per deck, like
`build_deck.py`. Run: `.venv/bin/python scripts/build_progress.py decks/<name>.pptx`.

**How it works (the reusable mechanism):**
1. `Presentation("brand/templates/progress-corporate-fy26.pptx")`, then
   **clear the sample slides cleanly** — drop each slide's rel *and* remove its
   `sldIdLst` entry (see `clear_slides`). A bare `sldIdLst.remove` orphans the
   parts and PowerPoint throws duplicate-name errors; dropping the rel excludes
   the media so the file also shrinks (~46MB → ~10MB).
2. **Add slides on native layouts** by index (`prs.slide_masters[0].slide_layouts[i]`),
   set the **title placeholder** (idx 0) for authentic Progress title styling,
   and **draw body content** (stat numbers, cards, diagrams) on the clean
   `Title Only` canvas in the Progress palette.
3. Hero moments use native full-bleed layouts: `Statement slide 1` (blue) /
   `Statement Slide 2` (green) / `Segue 1` (blue, centred) / `Section 1`.
   Note: the **Statement title placeholder is bottom-anchored** — for a
   short single-line title, reposition it to the top (see slide 16).

**Progress palette** (from `theme1.xml`; fonts are **Arial / Arial Bold**, installed):
navy `#00216B` (Blue P1; `#00206B` was a one-digit typo) · green `#008963` + bright `#00B563`
(stat numbers, accents) · blue `#4B4BF7` (section bg) · yellow `#FFD000` (pop on
blue). Big stat numbers go **green on white** to echo the corporate "Progress
Strength" stat slide.

**LAYOUTS map** (index → layout name, verified FY26): 2 `Title Slide Green No
Photo` · 3 `Title Slide Blue No Photo` · 8 `Segue 1` · 14 `Statement slide 1` ·
15 `Statement Slide 2` · 19 `Title Only` · 27 `Section 1`. To re-verify after a
template update: clear slides, add one slide per candidate layout, label its
placeholders, and render (the probe pattern).

**Design ceiling - never default to white-bg-plus-bordered-cards (binding, GM
directive 29 Sep 2026).** Measured across all 32 decks ever built: 81% of every
slide shipped is `Title Only` or `Blank` - a white canvas with hand-drawn
shapes - while the template's `Statement`/`Quote`/`Gallery`/`Team`/column
layouts (real full-bleed brand geometry, built in) were used almost never.
"Boring" was proven in pixels to be a design-choice problem, not a python-pptx
ceiling problem. Before building a custom slide: (1) check whether a native
layout above already does the job - it's free; (2) if genuinely custom, build
it with **`scripts/deck_design.py`**'s primitives (`freeform_ribbon`,
`gradient_card`/`icon_card` - vertically centred by default, no dead space -
`index_numeral`, `accent_rule`, `composed_bg` for hero moments only); (3) never
call its `brand_furniture()`/`redraw_logo()` without reading the module's rule
1 first - get it wrong and the Progress logo silently disappears (painted over
by a full-bleed treatment) or duplicates (redrawn on top of a layout's own
still-correct inherited copy). Full detail, the native-layout list and the
measured numbers: `progress-deck` skill's "Design ceiling" section.

**Still applies:** the exec-audience rules below, the mandatory QA loop, AU
spelling, no em dashes, one attribution line for us. Speaker notes (if present)
are shared with the source builder so voice stays consistent.

## Exec-audience rules (encode when audience is execs / CMOs / leadership)
- **≤25 words of body copy per slide** — the screenshot or the number carries it.
- **One idea per slide**; **outcome-led titles** ("Cut support cost, not quality",
  not "ARAG Features").
- **Always end with a single clear ask.**
- Anchor to the audience's own language/themes; lead with their outcomes (findability,
  self-service, on-brand answers), not vendor/IT infrastructure. One attribution line
  for us; no other vendor branding.
