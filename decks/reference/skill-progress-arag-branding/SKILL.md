---
name: progress-arag-branding
description: Apply and enforce Progress Agentic RAG brand guidelines — exact color palette, Progress Sans typography, logo lockups, and Hex Loop rules — when creating or reviewing any customer-facing or partner-facing asset. Use this skill whenever building demo UIs, landing pages, HTML/React artifacts, PowerPoint decks, one-pagers, partner enablement courses, diagrams, or marketing copy for Progress Agentic RAG (also called ARAG or PARAG), and whenever asked to check, audit, fix, or "make on-brand" an existing asset. Trigger this even when the user does not say the word "branding" — if the deliverable will be seen by a customer, prospect, or partner, the brand rules apply. Also use when the user asks for brand colors, hex codes, the Progress green, logo sizing, or clear-space rules.
---

# Progress Agentic RAG Branding

Enforce the Agentic RAG product-specific brand system on every asset. Two modes: **generate** on-brand assets from scratch, and **audit** existing assets against the rules.

The Progress Visual Brand Identity guidelines are the primary benchmark; the Agentic RAG rules below are the product-specific layer on top.

## Start here

1. Identify the asset type: web/demo UI, deck, document, diagram, or copy.
2. Read the relevant reference file — don't work from memory, the hex values matter:
   - `references/color.md` — full palette with hex/RGB/CMYK/Pantone, contrast data
   - `references/typography.md` — the Progress Sans Display/Text system, weights, spacing, substitutes, licensing
   - `references/logo.md` — lockups, clear space, minimum size, misuse rules, sourcing
   - `references/hex-loop.md` — the product graphic device: color, cropping, prohibitions
   - `references/copy-standards.md` — product naming, ® usage, tone, approved boilerplate
3. For code-based assets, pull in `assets/arag-tokens.css` rather than hardcoding hex values. For themed artifacts, use `assets/arag-theme.json`.
4. **Use the real asset files.** Logo lockups are in `assets/logos/` (eight variants, SVG and PNG) with `assets/logos/manifest.json` describing which to pick. The Hex Loop graphic device is at `assets/hex-loop/hex-loop-rgb.svg` with its own `assets/hex-loop/manifest.json`. Never draw, trace, or approximate either — reference the bundled files.
5. Before delivering, run the audit checklist at the bottom of this file.

## The six rules that break assets most often

These are the ones worth internalizing, because they're the ones people get wrong:

**1. Never put brand green on a light background as text or a small UI element.** Green P2 (#00B563) hits only 2.7:1 on white — it fails WCAG AA outright. The greens are *accent and background* colors in this system, not foreground colors on light. They pass beautifully on the dark blues. Full contrast matrix is in `references/color-and-type.md`.

**2. The Hex Loop is always cropped, never shown in full, never standalone, and never recolored.** It bleeds off an edge of the layout. A complete hexagon sitting inside a slide is a violation, and so is rotating it off the 30° isometric grid. For multi-product or cross-sell material, don't use two Hex Loop crops — use the Progress Helix instead. **Use the bundled SVG at `assets/hex-loop/hex-loop-rgb.svg`** — never draw or approximate the device. See `references/hex-loop.md` for cropping guidance and `assets/hex-loop/manifest.json` for file metadata.

**3. Blues and greens must predominate.** Yellow S1, Red S3, and the Progress corporate palette are accents for illustrations only — they never become the dominant color of a layout.

**4. Progress Sans is two fonts, not one — Display and Text.** Display for headlines, hero areas, and anything read at a glance from a distance. Text for body copy, all UI elements, captions, and labels. Never mix the two within a single sentence, paragraph, or title, and never reverse their roles. When Progress Sans isn't available, **Arial is the only approved substitute** — not Helvetica, not Inter, not a system stack. Roboto Mono for code, and only for code. Details in `references/typography.md`.

**5. Type is predominantly black and white.** Color in typography is a selective accent for emphasis, navigation, and highlights — never the default treatment for headings and body. Set headlines black on light and white on dark; spend the palette on links, states, data, and graphic elements. Typography is the constant; color is the accent.

**6. The logo carries Progress corporate colors, not the Agentic RAG palette.** Progress Logo Green is `#5CE500` (Pantone 375) and Progress Logo Gray is `#4B4E52` (Cool Gray 11) — neither appears in the Agentic RAG palette. Never substitute Green P2 or Green P3 into the symbol to "match" the design; altering the mark breaches trademark guidelines, not just brand ones. Use the supplied file from `assets/logos/`, never a redrawn or re-typeset version, and keep digital and print files in their own domains.

## Generating assets

**Web / demo UI / HTML artifacts** — Start from `assets/arag-tokens.css`. Default layout: Light Grey S4 (`#F4FAFF`) page background with black headings and body, or invert to a Blue P1 (`#00216B`) section with white headings and Blue P5 (`#DCECFF`) body text. Headings use the Display face, everything else uses Text. Primary buttons use Blue P2 (`#2B2BB2`) with white text. Use green for success states, data-positive indicators, and accent fills on dark — not for links or body copy on white.

**Decks** — Title slides use a dark blue field with a cropped Hex Loop bleeding off one corner. Body slides run light (Light Grey S4 or white) with dark blue headings. Place the horizontal logo lockup consistently; use stacked only if the space genuinely won't take the horizontal.

**Word documents (two-pagers, guides, playbooks, whitepapers) — one treatment, held across the whole library (lead ruling, 1 Oct 2026, after four documents reached the gate on the same day with four different header and heading treatments).** The stacked lockup (`assets/logos/primary-stacked.png`) sits in a real Word header, 0.85in high, repeating on every page, with a clear gap of at least 0.25in between the bottom of the lockup and the first element on the page - a lockup flush against the title or the first heading reads as a header collision and fails the lead's gate. Headings black (rule 5 and the checklist govern documents; the dark-blue heading allowance above is for deck body slides only), body Arial. Confirm by rendering and viewing every page, never by reading the build script.

**Diagrams and architecture visuals** — Blue for infrastructure and flow, green for data and success paths, yellow and red sparingly for callouts and error states. Keep the isometric 30° angle if you're using angular graphic devices, matching the Hex Loop grid.

**Partner enablement course material** — Same rules; consistency across modules matters more than variety. Pick one section-header treatment and hold it across the whole course.

## Auditing assets

When reviewing an existing asset, report findings as a table with severity, not as prose. Use these three levels:

- **Violation** — breaks an explicit brand rule (recolored Hex Loop, wrong logo file, non-palette color, missing ® on first use)
- **Accessibility** — passes brand but fails WCAG AA (this is where the greens usually land)
- **Recommendation** — compliant but weaker than it could be

Always cite the specific rule and give the concrete fix, including the replacement hex value. An audit that says "colors feel off-brand" is useless; one that says "the CTA uses #00D364 at 1.9:1 on #F4FAFF — swap to #2B2BB2 for 9.55:1" is actionable.

### Audit checklist

Colors
- [ ] Every color traces to the Agentic RAG palette or the Progress corporate palette
- [ ] Blues and greens predominate; yellow/red confined to accents
- [ ] Body text meets 4.5:1; large text and UI components meet 3:1
- [ ] No green foreground on a light background

Typography
- [ ] Display used for headlines, Text for body/UI/captions — roles not reversed
- [ ] Display and Text never mixed inside one sentence, paragraph, or title
- [ ] No adjacent weights mixed in a block (Light with Regular, Bold with Extra Bold)
- [ ] Text never set below 6.5pt
- [ ] Tracking and leading tuned, not left at defaults
- [ ] Type is black or white; color used only as selective accent
- [ ] Fallback is Arial only — no Helvetica, Inter, or system stacks in the font chain
- [ ] Roboto Mono confined to code; not used decoratively
- [ ] Heading hierarchy is consistent and doesn't skip levels
- [ ] Font files not redistributed or bundled into shared/partner deliverables

Logo
- [ ] Sourced from `assets/logos/`, not redrawn or traced
- [ ] Correct tier (primary vs. secondary) and background variant (standard vs. alternate)
- [ ] Horizontal used unless space genuinely forces stacked
- [ ] Symbol green is `#5CE500`, not an Agentic RAG palette green
- [ ] Clear space = 1/2 symbol height on all sides (0.42x lockup height horizontal, 0.21x stacked)
- [ ] Rendered at ≥ 75px (screen) or ≥ 0.85in (print) in height, verified at the smallest breakpoint
- [ ] Aspect ratio preserved — not stretched, skewed, angled, or rotated
- [ ] No effects: no shadow, bevel, gradient, outline, stroke, or reduced opacity
- [ ] No elements removed; product name weight and size unchanged
- [ ] Background provides enough contrast and isn't visually busy

Hex Loop
- [ ] Sourced from `assets/hex-loop/hex-loop-rgb.svg`, not drawn or approximated
- [ ] Cropped, bleeding off an edge — never a complete hexagon in layout
- [ ] Not used as a standalone graphic
- [ ] Original Agentic RAG blues, unrecolored
- [ ] Not rotated off the 30° isometric grid
- [ ] Only one crop — multi-product material uses the Helix instead
- [ ] Not competing with the logo for attention

Copy
- [ ] "Progress® Agentic RAG" on first prominent use
- [ ] Product name never abbreviated to "ARAG" in customer-facing copy
- [ ] Claims are substantiated

## Known defect in the source guidelines

The brand page states the Agentic RAG Hex Loop "uses its primary oranges." This contradicts both the supplied artwork and the stated palette, which contain no orange — the bundled Hex Loop SVG (`assets/hex-loop/hex-loop-rgb.svg`) is rendered in Blue P2 (`#2B2BB2`) with `#001433` gradient overlays. This is almost certainly copy inherited from another product's page.

**Follow the artwork, not that sentence: the Hex Loop is blue.** The bundled file confirms this definitively. Flag the discrepancy to the brand team rather than silently designing around it. If a genuinely orange Hex Loop variant is ever supplied, this skill needs updating.
