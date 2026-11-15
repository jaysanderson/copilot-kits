---
applyTo: "**/*.html,**/*.css,**/render_pdf.py,**/build_*.py"
description: "How the whitepaper and report templates are built, styled and rendered to PDF"
---
# HTML reports and whitepapers

## Files
- `skeletons/whitepaper/lego-set-for-builders.template.html`: self-contained A4 whitepaper, styles inline in `<head>`, `{{TOKEN}}` placeholders for the logo (`LOGO_DARK`), the Hex Loop crop (`HEXLOOP`) and six screenshots (`SHOT_*`).
- `skeletons/whitepaper/build_lego_whitepaper.py`: replaces each `{{TOKEN}}` with a base64 data URI, asserts none is left, writes the final HTML, then renders PDF with Playwright (Chromium, print media, `prefer_css_page_size=True`, backgrounds on). Its `ROOT`, `BRAND` and `SHOTS` paths point at the source machine: set them to this repo before running.
- `skeletons/whitepaper/report-style.css` plus `render_pdf.py`: the external-stylesheet variant. `render_pdf.py` runs two Playwright passes (page 1 full-bleed, then the body with a running footer carrying `pageNumber` / `totalPages`) and merges them with pypdf. Edit the `FOOTER` string per report; the shipped text names a previous report and date.

## Page model
- `@page { size: A4; margin: 0 }`. Each page is a `.sheet` (template) or `.page` (CSS variant), `210mm` wide, `page-break-after: always`, with its own padding (17mm 18mm 16mm in the template). Nothing may rely on the browser adding margins.
- Dark pages (`.sheet.dark`, `.cover`) are Blue P1 `#00216B` with white headings and Blue P5 `#DCECFF` for secondary copy. Light pages are white or Light Grey S4 `#F4FAFF` (`.sheet.light`) with black text.

## Brand tokens (from `brand/progress-official.json` and the template `:root`)
- Blues: P1 `#00216B` (dark ground), P1 shade `#00123C`, P2 `#2B2BB2` (links, buttons, eyebrows on light), P3 `#4B4BF7`, P4 `#5777EA` (large text and UI only), P5 `#DCECFF`.
- Greens: P2 `#00B563` (primary accent), P3 `#00D364` (section rules and kickers on dark), S3 `#90EF8E`, S4 `#CDFFCA`. Yellow S1 `#FFD000` for warnings only. Border `#C9D9EE`, muted text `#3D3D42`.
- Colour is an accent. Body text is black on light and white on dark; never coloured body text.

## Fonts
- Headings `"Progress Sans Display"`, body `"Progress Sans Text"`, code `"Roboto Mono"`. Neither the template nor `report-style.css` declares `@font-face`, so both currently render in Arial, which is the only approved fallback.
- To render the real faces, add `@font-face` rules pointing at `brand/fonts/ProgressSansDisplayVF.woff2` and `brand/fonts/ProgressSansTextVF.woff2` with `font-weight: 100 900`. Never substitute a Google font for either face. Roboto Mono is for code only.

## Logo and Hex Loop
- Logo: `brand/progress-logo-dark.svg` on light pages, `brand/progress-logo-white.svg` on dark pages. Never reference `logo-black.png` or `logo-white.png`; those are per-campaign slots that may hold another company's mark (`brand/LOGO-SLOTS-README.md`).
- The Hex Loop is always cropped off a page edge (`.hexcrop` with `.hex-tr`, `.hex-br`, `.hex-bl`), never shown whole, never recoloured. The SVG is not in this kit; fetch it from the Progress Brand Bank.
- Screenshots: no hosting-region strings, other customers anonymised, every visible figure checked against the live product before use.

## Rendering checklist
`pip install playwright pypdf` then `playwright install chromium`. Run the build, open the PDF, view every page. Check for overflow past the sheet, orphaned headings and any `{{` left in the HTML. `pdfinfo` (poppler) is optional; `render_pdf.py` calls it only to print a page count.
