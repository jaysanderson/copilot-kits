---
mode: agent
description: Build a new Progress-branded deck from a brief - outline first, wait for approval, then spec, build, render, view, fix, re-render.
---

# New deck

Build one deck in this chat. Read `.github/instructions/deck-builders.instructions.md` once before touching a builder.

## 1. Inputs (ask for anything missing, one question at a time)
- Audience: who is in the room (CIO, CMO, solutions architect, sales team, exec sponsor) and what they already believe.
- Purpose: the decision or action the deck must produce, in one sentence.
- Source material: a brief, notes, approved claims, screenshots, or a demo URL to capture from. Numbers come only from here; nothing from memory.
- Constraints: slide count ceiling, deadline, internal or customer-facing, any locked facts.

## 2. Outline, then WAIT
- Propose the arc for the audience. Default exec arc: situation, cost of inaction, the fix, proof, path, one ask.
- Write one sentence per slide: the slide title as the point it makes, the layout index you will use, and what carries the slide (number, screenshot, quote, diagram). Mark anything you could not source as [UNVERIFIED].
- Prefer native layouts (Statement 14 and 15, Quote 37, columns 30 to 32, item lists 41 to 43, Gallery 48) over Title Only 19 with drawn shapes.
- Show the outline as a table and stop. Do not write a spec or run a build until Jay replies yes. On any other reply, edit the outline and show it again.

## 3. Build
- Spec path (default): write `decks/<name>/<name>-spec.json` from the approved outline, notes included, then run `python builders/build_from_template.py --template templates/progress-corporate-fy26.pptx --spec decks/<name>/<name>-spec.json --out decks/<name>/<name>.pptx`.
- Script path (only when a slide needs drawn geometry): copy `builders/anz-sales-meeting/` to `decks/<name>/`, repoint its paths, write slides in `body.py`, and keep `checks.py` current with the deck.
- Screenshots: border #C9CCD3 at 0.75 pt, subtle shadow, 11 pt muted caption, aspect-fit, no other customer names or region strings visible.
- The build must end with the package audit passing (`audit: 0 findings over N parts`).

## 4. Render, view, fix, re-render
- `soffice --headless --convert-to pdf --outdir decks/<name>/qa decks/<name>/<name>.pptx`
- `pdftoppm -jpeg -r 150 decks/<name>/qa/<name>.pdf decks/<name>/qa/slide`
- Open every slide image and look at it. List defects per slide: overflow, overlap, title wrapping into body, white-on-white on title slides 2 and 3, missing logo or page number, text in the footer band below 6.7 in.
- Run `checks.py` with `DECK=` pointing at the pptx. Fix the spec or script, rebuild, re-render the whole deck, view every slide again. One fix cycle, then stop and report what remains.

## 5. Done when (from DEFINITION-OF-PASS.md)
- Every slide has 25 words of body copy or fewer, one idea, and a title that states the point; the deck ends on one ask.
- Every number traces to the source material or a cited independent source; pricing is USD; demo figures are labelled; no [UNVERIFIED] item survived without Jay's say-so.
- Australian English, no em dashes, no banned words, "Progress Agentic RAG" never "ARAG" on a customer-facing slide.
- Fonts are Arial; logo, copyright and page number are visible on every rendered slide; colours trace to `brand/progress-official.json`.
- Every slide was rendered to an image and viewed after the last edit; `checks.py` exits 0; the package audit reports 0 findings.
- Report: slide count, layouts used, the rendered image folder, claims you could not place, and the checks output.
