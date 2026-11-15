---
mode: ask
description: Severity-rated brand audit of a deck or slide images against the Progress Agentic RAG brand rules (colour, type, logo, Hex Loop, copy).
---

# Brand audit

Audit the deck, slide images or spec provided in context. Report findings as a table, not prose. Do not rewrite the asset.

## Severity levels
- Violation: breaks an explicit rule (non-palette colour, redrawn or wrong logo file, Hex Loop shown whole or recoloured, missing ® on first prominent use, "ARAG" on a customer-facing slide).
- Accessibility: on brand but under WCAG AA (body text under 4.5:1, large text or UI under 3:1). Green text on white lands here: #00B563 on white is 2.7:1.
- Recommendation: compliant but weaker than the rules allow (Title Only canvas where a native layout exists, colour used as the default heading treatment).

## Checks
- Colour: every hex traces to `brand/progress-official.json` or the Progress corporate palette (#00216B, #2B2BB2, #4B4BF7, #008963, #00B563, #00D364, #F4FAFF; #FFD000 as accent only). Blues and greens predominate; yellow and red are accents only. Flag #00206B as a typo for #00216B.
- Type: Arial or Arial Bold only in a pptx; no Helvetica, Inter, Calibri or system stack. Headings black or navy on light, white on dark; colour in type only as a selective accent. Nothing under 6.5 pt. The six-step scale 60/36/26/18/14/12 held across the deck.
- Logo: from the template or `brand/progress-logo-dark.*` and `progress-logo-white.*`, never `logo-black.png` or `logo-white.png`. Logo green is #5CE500, not a palette green. Clear space half the symbol height; no stretch, rotation, shadow or opacity change; present and legible on every slide.
- Hex Loop: only the bundled SVG (`reference/skill-progress-arag-branding/assets/hex-loop/hex-loop-rgb.svg`), cropped so it bleeds off an edge, blue, on the 30 degree grid, one crop per layout.
- Copy: "Progress® Agentic RAG" on first prominent use, then "Progress Agentic RAG"; claims substantiated; Australian English; no em dashes; no delve, leverage, unlock, seamless, game-changing.

## Output
- Table: `# | severity | slide | finding | rule | fix (with replacement hex, file or wording)`.
- One line at the end: count by severity, and whether any Violation blocks shipping.
