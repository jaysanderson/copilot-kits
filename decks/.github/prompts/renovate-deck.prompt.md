---
mode: agent
description: Renovate an existing deck onto the Progress template - render and audit the source, wait for approval, rebuild from scratch salvaging media, render and view.
---

# Renovate deck

Input: the source `.pptx` path, the audience, and the purpose. Read `.github/instructions/deck-builders.instructions.md` once.

## 1. Inventory the source
- `soffice --headless --convert-to pdf --outdir renovate/src <source>.pptx` then `pdftoppm -jpeg -r 110 renovate/src/<source>.pdf renovate/src/slide`. View every slide image.
- Extract text: `pdftotext -layout renovate/src/<source>.pdf renovate/src/text.txt`.
- Salvage media: unzip `ppt/media/*` from the source into `renovate/salvage/`, view each file, keep only screenshots, charts and logos that pass the editorial test and carry no other customer's name or region string.

## 2. Audit table, then WAIT
- One row per source slide: `slide | title as rendered | keep / rewrite / cut / merge | gap`. Gap names what the slide lacks for this audience (no point in the title, over 25 words, unverified number, off-brand colour, no ask).
- Below the table, the proposed new outline: one sentence per slide, layout index, and `[NEW]` on every slide that has no source slide. Fill gaps to the exec arc: situation, cost of inaction, the fix, proof, path, ask.
- Every product claim carried over is marked verified (with its source) or [UNVERIFIED]. Never keep an unverified claim silently.
- Show the table and outline, then stop until Jay replies yes.

## 3. Rebuild from scratch
- Never edit the source file. Build a new deck on `templates/progress-corporate-fy26.pptx` through `builders/build_from_template.py` (spec) or a copy of `builders/anz-sales-meeting/` (script), per the builders instructions.
- Place salvaged media with the screenshot treatment (border, shadow, 11 pt caption). Recapture any screenshot whose figures may have changed since the source deck was made.
- Keep `[NEW]` at the start of the speaker notes on each new slide so the reviewer can see what was added.

## 4. Render and view
- `soffice --headless --convert-to pdf --outdir decks/<name>/qa decks/<name>/<name>.pptx`, then `pdftoppm -jpeg -r 150 decks/<name>/qa/<name>.pdf decks/<name>/qa/slide`.
- View every slide image, run `checks.py`, fix once, re-render the whole deck, view again.

## Done when
- The audit table decision for every source slide is reflected in the new deck; every `[NEW]` slide is marked.
- All Deck lines in `DEFINITION-OF-PASS.md` hold and the evidence (rendered images, checks output, package audit line) is in the report.
