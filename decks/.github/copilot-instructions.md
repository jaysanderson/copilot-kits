# Progress deck kit

This repo builds Progress-branded 16:9 decks by populating the corporate master template through the Python builders in `builders/`. Never hand-draw a slide in PowerPoint, never create a new template, never patch an old deck in place: rebuild from the template.

## Template and layouts
- The only template is `templates/progress-corporate-fy26.pptx` (46 MB, 1 master, 68 layouts). `builders/build_from_template.py` defaults to `brand/templates/...`, which does not exist here: always pass `--template templates/progress-corporate-fy26.pptx`.
- Layout index map (verified from the template XML, 14 Nov 2026): 2 Title Slide Green No Photo, 3 Title Slide Blue No Photo, 7 Title Slide Blue No speaker info, 8 Segue 1, 14 Statement slide 1, 15 Statement Slide 2, 17 Title and Content with Bullets, 19 Title Only, 24 Title + Body Left Helix, 27 Section 1, 30 Two columns, 31 Three columns, 32 Four columns, 37 Quote slide, 41 3 items list, 43 6 items list, 48 Gallery 1, 52 2_Product Slide - Agentic RAG, 66 1_Closing Slide. Re-probe with `--inspect` after any template update.
- Prefer native layouts (Statement, Quote, columns, item lists) over a white Title Only canvas with hand-drawn cards. 81% of past slides were Title Only or Blank and were judged boring for it.
- Mechanism: open the template, drop every sample slide (drop the relationship AND the sldIdLst entry), add slides by layout, fill placeholders, save, then `sanitise_package()` and `audit_package()` strip the template's embedded author names. A deck that skips the audit is not done.

## Exec discipline
- Max 25 words of body copy per slide. One idea per slide. The title states the point ("Cut support cost, not quality"), never a topic label ("Features").
- End on one clear ask, centred on the closing layout, text box bottom at or above 6.5 in.
- Speaker notes carry the talk track. No text-only filler slides, no accent stripes or bars under titles.

## Render and view
- `soffice --headless --convert-to pdf --outdir out deck.pptx` then `pdftoppm -jpeg -r 150 out/deck.pdf out/slide`.
- Open and look at every slide image before claiming done. Fix overflow, overlap, low contrast and title-body collisions, then re-render the whole deck. Any copy edit is a layout change: re-render everything, not the slide you touched.
- Also run `checks.py` (geometry, footer band, word count, banned words). A check that does not report how many items it examined is not a check.

## Screenshots
- Thin neutral border (#C9CCD3, 0.75 pt), subtle shadow, 11 pt muted caption underneath, aspect-fit never stretched.
- Match the customer's industry. Crop or blur other customers' names, account IDs and hosting-region strings before the image goes on a slide.

## Brand
- Tokens from `brand/progress-official.json`: ink #00216B (Blue P1), #2B2BB2 (Blue P2), accent #00B563 (Green P2), #F4FAFF light grey. Never type #00206B; it is a known typo.
- Fonts: Arial and Arial Bold only, from the template theme. Never embed Progress Sans in a pptx.
- Green text on white fails contrast: use Green P2 and P3 on dark fields only. Large stat numerals on white use #008963 at 32 pt or larger.
- Logo: `brand/progress-logo-dark.{svg,png}` on light, `brand/progress-logo-white.{svg,png}` on dark, both extracted from the template. Never use `logo-black.png` or `logo-white.png` (campaign slots, see `brand/LOGO-SLOTS-README.md`). The template's logo, copyright and page number must stay visible on every slide.
- Product name is "Progress Agentic RAG" in customer-facing copy, never "ARAG".

## Truth and language
- No fabricated numbers. Every statistic is from a named independent source, cited on the slide, under five years old. Demo figures carry "not a product performance claim".
- Pricing in USD only. Certifications named only when verified outside the product docs.
- Australian English. Spaced hyphen, never an em dash. Banned words: delve, leverage, unlock, seamless, game-changing.
- Never write secrets, keys or tokens into any file.

## Cost and verification
- Use the cheapest capable model for mechanical work (filling a spec, re-rendering, running checks); use a stronger model only for the outline and copy.
- PASS requires the rendered slide image, viewed. python-pptx geometry or "looks fine" is not evidence.
