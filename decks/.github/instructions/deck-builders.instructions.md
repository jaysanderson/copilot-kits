---
applyTo: "**/build*.py,**/*spec*.json,**/checks.py"
description: How the deck builders consume a spec, address template layouts and placeholders, and prove the result with checks and a render loop.
---

# Deck builders

## Two ways to build
- Spec path: `python builders/build_from_template.py --template templates/progress-corporate-fy26.pptx --spec <spec>.json --out decks/<name>.pptx`. Run `--inspect` first to list the 68 layouts with their placeholder idx and names. Examples: `builders/deck-spec.json`, `builders/sitefinity-connector-spec.json`.
- Script path (custom slides): copy `builders/anz-sales-meeting/` (`head.py` constants and helpers plus `body.py` slides, concatenated into `build_deck.py`; `checks.py` alongside). Its `ROOT`, `TEMPLATE`, `OUT` and font paths are Mac paths from the source project: repoint them to this kit and to `C:/Windows/Fonts/arial.ttf` before running. It imports `deck_design` (`txt`, `add_shadow`), which is not in this kit: replace with the `tbox` and `shot` helpers in `builders/build.py`.

## Spec format
- A JSON list, one object per slide: `{"layout": <name or index>, "text": {<placeholder name or idx>: <string or list>}, "image": {"path", "left", "top", "width"} (inches), "notes": "<talk track>"}`.
- A list value (or a string with `\n`) becomes one paragraph per line, so bullet layouts render real bullets.
- A text key that matches no placeholder prints `warning: no placeholder` to stderr and is skipped: treat that warning as a build failure.
- The build ends with `sanitise_package()` and `audit_package()`; a non-zero exit (`PACKAGE AUDIT FAILED`) means personal data from the template survived.

## Layout and placeholder map (idx)
- Title is idx 0 on every layout that has one. Body is idx 10 on 17, 20, 24 and 25 (Title and Content with Bullets, Title and Content, Title + Body Left Helix); subtitle idx 16 on title slides 2 and 3 and on product slides 50 to 65; idx 1 on 7 (Title Slide Blue No speaker info).
- Columns: 30 Two columns idx 11, 12; 31 Three columns idx 10, 11, 12; 32 Four columns idx 11 to 14. 41 3 items list: heads 10, 23, 25 and bodies 13, 28, 29. Image Slide 35 and 36: pic idx 10, body idx 13.
- 14 and 15 (Statement) have only idx 0, bottom-anchored: move it up for a one-line title. 8 Segue 1 has one centred title. 66 1_Closing Slide has no placeholders: add a centred text box with its bottom at or above 6.5 in.
- Title slides 2 and 3: idx 0, 12 and 16 sit on the white left column, so set them navy or dark, never white.

## Placeholder rules
- When repositioning a placeholder set all four of left, top, width and height; setting only top and height writes zero width and renders a blank slide.
- Remove unused placeholders (`drop_ph`) or they render as "Click to add text".
- Set `font.name = "Arial"` on every run you create. Grid: left margin 0.79 in, content width 11.75 in, title top 0.59 in, body top 1.85 in, nothing below 6.7 in. Type scale: 60, 36, 26, 18, 14, 12 pt only.

## checks.py pattern
- Every check prints `PASS <name> :: <detail>` or `FAIL <name> :: <detail>`, where detail includes how many items were examined (zero of zero is not a pass). Collect FAILs and `sys.exit(1)` if any. Read the deck path from the `DECK` env var.
- Standing checks: slide count; every spec figure present in deck text; zero em dashes; zero banned words (delve, leverage, unlock, seamless, game-changing); zero "ARAG"; no zero-size or off-slide shape; title left and top identical on slides 2 onward; no text box bottom below 6.9 in (footer band); first panel left edge 0.79 in; every run size on the six-step scale.
- Add for each deck: body word count per slide at or under 25; no placeholder left empty; no two text frames whose bounding boxes intersect; then any composition rule specific to that deck (colour counts, grid edges).

## Render loop
- `soffice --headless --convert-to pdf --outdir decks/qa decks/<name>.pptx` then `pdftoppm -jpeg -r 150 decks/qa/<name>.pdf decks/qa/slide`.
- View every `slide-NN.jpg`. Fix, rebuild, run checks, re-render the whole deck. One fix-and-verify cycle, then stop and report.
