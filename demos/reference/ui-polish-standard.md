# UI polish standard - the "CorpusKit / FRDC" bar

**Status:** canon, living. Created 1 Sep 2026 (GM directive). The GM handed the factory a
real, third-party-polished version of factory-created code as the standard for
"professional, not vibe-coded": **https://frdc.corpuskit.org/t/frdc** (CorpusKit, FRDC
Knowledge Hub). He does NOT want it cloned - he wants every build to reach THIS level of
craft and finish. Consult this before shipping any UI (demos, the Field Kit seller
experience, the DAM, any front end).

**Why it's a direct bar, not an aspiration:** FRDC is the SAME class of app the factory
builds - a Library / Ask / Graph / Tools experience over an ARAG-ingested corpus. So this
is apples-to-apples with our knowledge-hub demos and the seller experience. The gap between
it and a "vibe-coded" build is entirely CRAFT - restraint, consistency, real metadata
density, quantified everything, familiar patterns executed cleanly. Nothing on the site is
exotic. It is disciplined. Match the discipline.

## The meta-lesson (read first)
Polish here is NOT novelty or cleverness. It is: one tight palette, generous whitespace,
hairline borders, a confident type hierarchy, a single consistent card system, real
metadata on every card, a number on everything, and familiar patterns done cleanly. If a
surface looks "vibe-coded," it is almost always failing on those fundamentals, not on
missing a flashy feature.

## A. Global craft (every surface)
- **Restraint.** One tight palette (FRDC: brand navy + white + a single accent), generous
  whitespace, thin hairline borders, subtle shadows. Busy = amateur. Let content breathe.
- **Confident type hierarchy.** Large, calm section headings ("What would you like to
  explore?", "Explore by region", "Research and development"), each with ONE quiet
  supporting subhead line. Big type used sparingly and deliberately, not everywhere.
- **One consistent card system.** Every card shares frame, padding, corner radius, shadow.
  Cards are metadata-rich: title + type/topic chips + date - NEVER a bare title.
- **Real, on-theme imagery.** A full-bleed photographic hero tinted to the brand colour so
  overlaid text stays legible (FRDC: a fishing-boat photo under navy). Not a flat colour
  block; not a generic stock gradient.
- **Quantify everything.** A number builds credibility: corpus scale ("3,940 resources"),
  per-category counts ("2821", "334", "415"), answer counts ("15 retrieved | 5 cited |
  2000-2021"), per-source relevance ("97%"). If you have a count, show it.
- **Every state is designed** - empty, loading, hover. Nothing renders as a raw default.

## B. Discovery (home / Library)
- **Multi-row, category-led browse (the Netflix/Spotify pattern).** Each row = a category
  heading + a count badge + "See all ->" + a horizontal rail of cards. NOT one flat grid.
  FRDC home: "Research and development 2821", "Carp control 334", "Stakeholder engagement
  415", each its own rail. (This is exactly the seller-experience design-critic's top fix.)
- **A left-rail facet with LIVE counts.** Library TOPICS: checkbox filters each with its
  count (Research and development 2821, Governance and reporting 169, Standards 94 ...).
- **Real catalogue controls.** Grid/List toggle + a card-density slider + a sort dropdown
  ("Newest added"). These read as a real product, not a demo.
- **An engaging non-list entry point.** FRDC's "Explore by region" is an interactive Australia
  SVG map + state chips - a spatial way into the same corpus. Give discovery more than one
  door.
- **A "Recently added" rail** on the hero (real ingested items, icon + title + arrow) - a
  freshness signal.
- **Card thumbnails - REFINES the demo skill's "never a placeholder icon" rule.** FRDC
  proves the real rule: prefer a genuine **page-1 document thumbnail** (it renders real
  report covers where it has them); where none exists, fall back to a **CONSISTENT branded
  placeholder** - a type tag ("Report") top-left + a centered doc glyph + a subtle diagonal
  fold - which reads as intentional. The defect is an INCONSISTENT or mismatched one-off
  icon, not a placeholder per se. Consistency is what makes a placeholder look designed.

## C. The Ask / answer surface (the trust surface - most directly comparable to our demos)
- **Familiar chat scaffold.** Left session sidebar ("+ New session", history entries showing
  "N messages | just now"); a suggested-question grid (real domain questions) as the empty
  state; an input with keyboard hints ("Enter to send | Shift+Enter for a new line"); a
  "Deep research" mode toggle; an "Export" action on the finished answer; a Stop control
  while streaming.
- **Inline superscript citation markers** ([1][2][4]) placed IN the prose exactly at the
  grounded claim - academic-paper credibility. This is far stronger than a generic
  "grounded in ..." chip row bolted under the answer. Adopt inline markers wherever an
  answer cites.
- **A qualitative confidence badge, NOT a raw score - and DEFAULT-VISIBLE (sharpened
  2 Sep 2026, vibe-coded audit).** FRDC shows an amber "Low confidence" badge on the
  answer - a coarse, honest label, never a bare number. This independently validates the
  factory's own call (see [[feedback_remi_penalises_synthesized_answers]]): show a coarse
  confidence label + resolvable citations, never a misleading REMi numeric on a
  synthesized answer. The badge sits visible by default beside every answer - hiding it
  behind an opt-in link, showing a bare "5/5/5" numeral, or showing nothing at all are the
  three failure modes the 2 Sep audit found live across the estate (now binding as
  `arag-demo-app` B34, with inline markers as B33 and rails/numbers as B35/B36).
- **Answer action bar:** thumbs up / thumbs down (feedback), copy, regenerate, view.
- **A collapsible retrieved-sources panel** that does trust properly: a numbered cited-source
  pill row (matching the inline [n] markers) + a counts line ("15 retrieved | 5 cited |
  2013-2018") + a full list where each source card carries a **relevance %**, the REAL
  retrieved excerpt, a "Show more" expander, and a **Save** action. Collapsed by default so
  it never clutters, one click to full transparency.

## D. Consumer / experience demos - study the category's best, inject its sensibility
FRDC is the bar for knowledge-hub/catalogue apps. For a CONSUMER experience demo (a theme-park
concierge, a retail advisor, a tourism planner), the bar is world-class EXPERIENCE design - immersion, delight, wonder - not brand-accurate chrome on a functional tool. A demo that hits
the functional bar (grounded, cited, multilingual) but reads as "a chatbot/form wearing the
client's logo" FAILS (named anti-pattern). The fix (GM directive, 1 Sep 2026, on the Village
Roadshow rebuild): **open the category's best-in-class real digital experience, take design
cues, and inject that sensibility - in the CLIENT's real brand** (never clone the exemplar's
assets; capture the client's real ones per Field Rule 8).
- **Theme parks / attractions → Disney** (disneyworld.disney.go.com, studied 1 Sep 2026). The
  transferable sensibility: a cinematic video-first full-bleed hero (imagery dominates, chrome
  recedes); WONDER in the copy (invitational headers, warm 2nd person, an italic/script accent
  word - "Enter a Land Where Fantasy Reigns", not "Rides"); themed decorative ornaments
  (sparkle dividers, medallions) used sparingly; a "plan your day" flow as the hero moment
  (not a dropdown + chatbox); rich photographic content cards; soft rounded friendly forms;
  tasteful motion; gracious warm microcopy (never a cold "Not enough data").
- The principle generalises: pick the domain's gold-standard consumer experience, name the
  specific transferable cues, and reach that LEVEL in the client's identity. The Holidayisle build
  is the proof it works; the first two Cinema-group attempts failed by stopping at
  brand-accurate chrome without the experience craft.

## E. Video craft - the same bar applied to film (added 2 Sep 2026, vibe-coded audit)
The discipline above has a film equivalent: **produced, not captured.** A video whose demo
footage is raw full-bleed screen capture pasted into a concat, book-ended by two static
cards, is the video form of "vibe-coded" - the 2 Sep 2026 audit found all six recent
videos there. The bar (binding detail in the `video-production` skill, section 0b):
- **Footage sits in a composed floating browser/device frame** on one consistent branded
  stage - never butted raw against the frame edges.
- **Kinetic-typography statement/kicker beats carry the film**, not a single static title
  card and CTA card.
- **One palette world.** A colour-grade/tint pass ties the cards, stage and captured app
  footage together - continuity is designed, never an accident of the app's own colours.
- **Step reveals build in progressively** on the beat, not as a pre-rendered static list.
- The starting primitives already exist in `scripts/build_effects_showreel.py`
  (`kinetic_title`, `framed_shot`, `grade_seg`); generalise, do not rebuild.

## F. Quantification, provenance and honesty as design (added 1 Oct 2026, Better Together Library)
The GM named https://better-together-library.vercel.app/ - a Progress-themed site built entirely
by an agent - as the bar for Progress-themed applications and explainer videos: "the same
quality bar, if not higher". Audit: `content/audits/better-together-library-quality-bar-2026-10-01.md`.
It clears A-C and adds three things A-C never named, all checkable (encoded as B38-B46 in the
`arag-demo-app` skill and as the illustration, cut-rate and silence floors in `hyperframes-video`):
- **The number on screen is the number in the artifact.** "467 connections" in the header; 467
  `<path>` elements in the graph. Never render a count you cannot derive from live data at render
  time; measure the claim against the artifact once per build.
- **Honesty is a designed element, dated and sourced** - not a footer disclaimer. A disclosure line
  under the input, one under every answer, a benchmark claim carrying its source, its date AND its
  volatility ("rankings change over time"), an inline amber beta chip on the one card whose feature
  is in beta, and a dogfood statement set as a full-width band. Field Rule 4 and hard rule 3 done as
  design rather than as compliance.
- **Invent the discovery metaphor; do not reach for the rail or the grid.** Nine isometric filing
  cabinets whose drawers open in 3D, driven by cursor position, quantified per cabinet, keyboard
  reachable, with state-aware microcopy. The B "Netflix pattern" is a floor, not a ceiling, and this
  reference is the evidence that a bespoke metaphor is reachable by an agent build.
- **What it gets wrong, so nobody copies it:** it ships Arial while its subject is Progress (we load
  the real Progress Sans - keep that lead), its cursor-follow rail moves the click target out from
  under the pointer, its answer denominator (39) disagrees with its own header (42), and its films
  carry a continuous audio floor the GM's no-music rule would not permit.
- **Against E:** the reference frames real product UI in a window on the brand stage in every
  product beat of all seven films measured. E already requires this; this is the first external
  confirmation of what meeting it looks like.

## How to use this
1. Before shipping any UI, walk it against A-C and F and name where it falls short of the bar.
2. It is a STANDARD, not a template - do not copy FRDC's navy or its map. Reach its level of
   restraint, consistency, metadata density and quantification in the build's own identity.
3. Feeds and is referenced by the `arag-demo-app` skill (visual-excellence bar) and Field
   Rule 9 in CLAUDE.md. Related: [[feedback_demo_is_a_useful_product_not_an_arag_showcase]],
   [[feedback_remi_penalises_synthesized_answers]].
