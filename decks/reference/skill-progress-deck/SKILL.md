---
name: progress-deck
description: Build a sales/vision deck on the official Progress corporate template - genuine Progress branding (real logo, ribbon motif, footer) from the template master, exec-audience discipline, and a mandatory QA render loop. Use for "build/renovate a deck on the Progress template". Encodes the unpack/edit/repack mechanism, the layout-index map, palette, screenshot treatment and the render-and-view-every-slide loop. Self-contained.
---

# Build a deck on the Progress corporate template

Produce a deck with genuine Progress branding - the real logo, the green/blue ribbon motif, the
copyright footer and page numbers all come from the template master, not redrawn. Populate the
template (unpack, edit content, repack); scratch-build with a slide library only when no
template exists (customer- or event-branded decks). 16:9.

**Prerequisites (set up once in your environment):**
- **Your own copy of the official Progress corporate template `.pptx`** - the skill can't ship it;
  get the current FY corporate deck from your brand/marketing source and keep it somewhere stable.
  This file IS the branding; everything else is populated onto it.
- `python-pptx` (build), a PDF renderer for the QA loop (**LibreOffice `soffice`** headless, or
  installed PowerPoint via `osascript` on Mac), and `pdftoppm` (from **poppler**) to rasterise.
- The `.pptx` and `.pdf` will be large-ish (~10 MB with media) - that's expected for the template.

## The template mechanism (the reusable core)
Work from the official Progress corporate `.pptx` as the single source. In `python-pptx`:
1. Open the template, then **clear the sample slides cleanly** - drop each slide's relationship
   AND remove its `sldIdLst` entry. A bare `sldIdLst.remove` orphans the parts and PowerPoint
   throws duplicate-name errors; dropping the rel also excludes the media so the file shrinks
   dramatically (tens of MB -> ~10 MB).
2. **Add slides on the native layouts by index** (`prs.slide_masters[0].slide_layouts[i]`), set
   the **title placeholder (idx 0)** for authentic Progress title styling, and draw body content
   (stat numbers, cards, diagrams) on the clean `Title Only` canvas in the Progress palette.
3. Hero moments use the native full-bleed layouts (a blue "Statement" slide, a green one, a
   "Segue" centred slide, a "Section" slide). Note: a Statement title placeholder is often
   **bottom-anchored** - for a short single-line title, reposition it to the top.
- **Re-verify the layout indices** after any template update with a probe: clear slides, add one
  slide per candidate layout, label its placeholders, render, and read off which index is which.
- **Title-slide contrast trap (found 5 Aug 2026, present in both `experian-isv-confident` and the
  first pass of `arag-sales-l1`):** on the `Title Slide Blue/Green No Photo` layouts (indices 2/3),
  the title (idx 0, top ~2.3in), subtitle (idx 16) and eyebrow (idx 12) placeholders sit in the
  **white left column** of the slide, not on the coloured ribbon graphic (which only covers the
  right ~55%). Setting these to WHITE text - the natural choice given the layout name - renders
  invisible white-on-white. Only the two lower placeholders (idx 14/15, further down at ~5.3-6.3in)
  happen to still show because they were set to a pale muted tone with faint contrast. **Set idx
  0/12/16 to a dark colour (navy title, green eyebrow, dark/muted subtitle) that reads on white**,
  not white - verify by rendering, don't assume from the layout's "Blue/Green" name. Re-check any
  existing deck built on this layout if it hasn't been re-rendered since this was found.

## Design ceiling - use the design system, never white-bg-plus-bordered-cards as
## the default (binding, GM directive 29 Sep 2026, after two same-day "boring" kickbacks)

**Measured, not assumed: 81% of every slide this factory has ever shipped is
"Title Only" or "Blank" - a white canvas with hand-drawn python-pptx shapes**
(234 + 90 of 400 layout uses counted across all 32 built decks). Meanwhile the
template's own full-bleed Statement/Quote/Gallery/Team/column layouts - which
carry real Progress brand geometry baked in for free - were used a combined
handful of times, several never at all. "Boring" was substantially a design
**choice**, proven in pixels: the same content on the same template, built with
`scripts/build_deck.py`'s old card pattern versus `scripts/deck_design.py`'s
primitives, is a different tier of craft on identical copy.

**The white-bg-plus-bordered-rounded-rect-card-row pattern (a flat card, thin
grey border, plain drop shadow, one-letter circle badge) is BANNED as the
default fallback.** Before building any custom (non-native-layout) slide:

1. **Check whether one of the template's own native layouts already does this
   job** - see the table below. It costs zero build code and carries genuine
   full-bleed brand geometry. Re-probe layout names/indices after any template
   update (`scripts/build_from_template.py --inspect`).
2. **If the slide is genuinely custom, build it with `scripts/deck_design.py`**
   - the standing primitives: `freeform_ribbon()` (brand-geometry motif, zero
   images), `gradient_card()` / `icon_card()` (vertically-centred content by
   default - no dead space), `index_numeral()`, `accent_rule()`, and
   `composed_bg()` (a cairosvg full-bleed background layer for hero/opening
   moments only - not the everywhere-default, see its docstring caution about
   reading as generic dark-SaaS if overused).
3. **Brand furniture (logo, copyright, page number) must survive on every
   slide, legible, on the correct-contrast variant.** `deck_design.py`'s rule 1
   covers exactly when to call `brand_furniture()`/`redraw_logo()` versus
   leaving the layout's own inherited furniture alone - read it before writing
   any full-bleed or corner-covering treatment; get this wrong and the Progress
   logo silently disappears or duplicates.

**Native layouts worth using directly** (name -> what it's for; verified by
rendering each blank via the probe pattern, template as of 29 Sep 2026 - 68
layouts under 1 master, not 136 as earlier noted here):
- `Statement slide 1` / `Statement Slide 2` - full-bleed colour-block hero
  statement, bold single claim.
- `Quote slide` / `Quote with pic` / `Quote full page 1` / `Quote full page 2` -
  full-bleed with built-in quote-mark iconography; customer proof points.
- `Title/Cover Slide with Helix` - a ribbon/helix motif crossing the whole
  slide; strong section-opener.
- `Gallery 1` - six picture placeholders, pre-laid-out grid.
- `Team slide 2` - accent header band + four image-placeholder frames.
- `Two columns` / `Three columns` / `Four columns` / `Comparison` /
  `Three column with subhead` - genuine multi-column layouts, not a
  build-your-own grid.
- `3 items list` / `4 items list` / `6 items list` - numbered-item layouts with
  their own placeholder structure.

## Palette + fonts
- Navy `#00216B` (Blue P1 - headings/dark cards; NOT `#00206B`, a one-digit typo that had
  propagated through this skill into shipped decks - authoritative value is
  `brand/progress-official.json`, captured from the live brand site), green `#008963` +
  bright `#00B563` (stat numbers,
  accents), blue for section backgrounds, yellow as a pop on blue. Big stat numbers go **green on
  white**. (Use the corporate-template palette, not a stale brand-kit green.)
- Fonts: **Arial / Arial Bold** (installed, from the template theme). NEVER install or fake a
  brand's real fonts - safe fonts only.

## Exec-audience discipline (when the audience is execs / CMOs / leadership)
- **<=25 words of body copy per slide** - the screenshot or the number carries it.
- **One idea per slide**; **outcome-led titles** ("Cut support cost, not quality", not "ARAG Features").
- **Always end with a single clear ask.**
- Anchor to the audience's own language and outcomes, not vendor/IT infrastructure.
- No accent stripes, no bars under titles, no text-only slides. One attribution line for us; no other vendor branding.

## Screenshots on slides
- Thin neutral border + a subtle drop shadow + an 11pt muted caption under each.
- Keep the vertical matching the customer's industry (never a mismatched-industry screenshot).
- Aspect-fit within the content box, never stretch. If the deck approaches the template's ~10 MB
  media floor, downscale the PNGs (aspect-preserving) rather than distort.
- Body copy on narrow product/segue layouts: keep to ~4 lines (those placeholders overflow into
  the artwork); split bulleted content one paragraph per line.

## The QA render loop (MANDATORY, one cycle)
1. Convert to PDF: `soffice --headless --convert-to pdf <deck>.pptx` (if `soffice` is absent, use
   installed PowerPoint via `osascript` - quit PowerPoint first, it serves a stale cached copy).
2. Rasterise: `pdftoppm -jpeg -r 150 <deck>.pdf <out>/slide`.
3. **VIEW every slide.** Fix overflow, overlap, low contrast, title/body collision (a title that
   wraps to 2 lines crowding the content below is the classic bug - shorten it or push the body
   down). One fix-and-verify cycle, then stop.
4. **A LATE COPY INSERTION IS A LAYOUT CHANGE - re-render the whole deck, not the slide you think
   you touched (learned 28 Sep 2026, tourism deck).** Adding one sentence to a slide late in the
   cycle, to satisfy a reviewer's condition, pushed that slide's body copy straight into the
   footer band - the last line rendered on top of the Progress logo, the copyright line and the
   page number at once. It had passed a full visual gate minutes earlier. Every gate after a copy
   edit re-renders and re-views EVERY slide, because a rebuild also reflows anything else that
   shares the same vertical budget.
5. **Run a deterministic footer-collision sweep alongside the visual pass.** The eye misses a
   collision at the very bottom of a slide more often than one in the middle, and a reviewer will
   not. Estimate each text frame's REAL wrapped height from its font sizes and box width rather
   than trusting the declared box height (`python-pptx` reports the box you asked for, not the
   text that overflowed it), and flag anything whose estimated bottom passes ~6.88in on a 7.5in
   slide. Expect it to run conservative - it over-estimates small type, so verify a flag by eye
   before moving anything. Pair it with the geometry sweep (zero-size and off-slide shapes;
   note that setting only `top`/`height` on a placeholder makes python-pptx write explicit
   geometry with left and width of ZERO, which renders a silently blank slide).

## Renovate mode (existing deck -> Progress-branded)
1. Inventory the source: render to images, VIEW every slide, extract all text.
2. Produce an audit table (`slide | keep / rewrite / cut / merge | gaps`) and the proposed new
   outline; SHOW it and WAIT for approval before building.
3. Rebuild from scratch on the template - never patch the old file. Salvage usable media by
   unpacking the source pptx.
4. Re-verify every product claim before it survives; flag what can't be confirmed. Fill gaps to
   the exec arc: situation -> cost of inaction -> the fix -> proof -> path -> ask. Mark new slides `[NEW]`.
5. Same QA render loop.

## Closing / CTA slide (fixed 1 Aug 2026 - a recurring defect)

The template's "1_Closing Slide" layout supplies only the centred Progress logo (as a
picture baked into the layout) - it has **no text placeholder**, so any tagline/CTA text
is added by the build script as a plain textbox. This has repeatedly been added
left-aligned at a fixed position, which reads as visually unbalanced under a centred logo
and, when a deck is later turned into a narrated video (`narrate_deck.py` holds this frame
at the end), can sit close enough to the bottom edge to visually collide with the video
player's own control-bar chrome.

**Always centre the CTA text box to match the centred logo, with real bottom margin:**
- Horizontal: `PP_ALIGN.CENTER` (or the shared `add_text(..., align=PP_ALIGN.CENTER)`
  helper if the deck's build script uses one) - never left-aligned under a centred logo.
- Vertical: keep at least 1 inch of clear space below the text box to the 7.5in slide
  bottom edge (i.e. top + height <= 6.5in) - this is the margin that stays clear of a video
  player's control-bar overlay if the slide is ever narrated into a video.
- Width: centre the box itself on the 13.33in slide width (e.g. `left = (13.33 - width) / 2`),
  don't just centre the text within a box that's already offset left.

Verify by rendering the actual slide (QA loop below) and eyeballing logo/text alignment
together, not just checking the XML.

## Rules that always apply
- Match the audience's locale spelling; no em dashes (spaced hyphen).
- No fabricated numbers; verify product claims (see the `grounded-artifact` skill), and present
  any demo figure as a demo figure with an on-slide "not a product performance claim" line.
- Speaker notes carry the talk track per slide.
- Then an independent reviewer gates it before it ships.

## Domo-deck kickback lessons (22 Sep 2026, binding)

1. **Pillar-coverage check at every deck gate**: before qa-reviewer sign-off, explicitly
   map the deck's product story against ALL THREE messaging-house pillars - the v2 Domo
   deck told a "how the tech works together" story with pillar one's strongest mechanism
   (Retrieval Agents calling third-party systems over MCP, permissions enforced) entirely
   absent, and every automated gate passed it. A capability story missing a pillar is a
   content FAIL even when everything present is accurate.
2. **Alignment is verified geometrically, not just visually**: the render-and-view loop
   passed slides the GM saw as misaligned. Every deck now gets a deterministic geometry
   sweep from the pptx element positions (consistent title baselines and left margins
   across slides, card edges aligned within a slide, no element off-grid vs siblings) in
   addition to the full-res view of every slide.
3. **The lead's gate on a GM-facing deck views EVERY slide**, never a load-bearing
   sample - the sampled gate passed a deck with alignment defects on unsampled slides.
