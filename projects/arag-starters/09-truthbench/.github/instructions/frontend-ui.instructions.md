---
applyTo: "**/*.tsx,**/*.jsx,**/*.html,**/*.css,**/static/**"
description: UI rules for ARAG demo front ends - anti-slop floor, markdown and citations, widths, Progress brand tokens
---

# Front-end rules

## Anti-slop floor (reference/skill-unslop-ui, reference/ui-polish-standard.md)
- One tight palette: about 70% neutral, 20% supporting, 10% accent. If a squint shows one blob of similar hue, redo it.
- No icon inside a coloured rounded square. No emoji as a visual element. No `backdrop-filter: blur`. No gradient text or gradient buttons. No coloured glow shadows.
- Sans-serif by default. Never Instrument Serif, DM Serif Display or Playfair Display as a default heading face.
- No card nested in a card without a grouping reason. No entrance animations; transitions 150 to 300 ms on interactive elements only.
- No `border-left` combined with `border-radius` on a container. No floating chat bubble bottom-right unless the brief asks for one.
- Every card carries real metadata (title, type chip, date or count). A bare title is a FAIL. Show a real number wherever the data has one.
- Every state is designed: empty, loading, error, no-result.
- Controls: limited corner rounding, high contrast, legible placeholder and typed text. White text over a faint hairline on near-black is a FAIL.
- Every stylesheet carries `[hidden]{display:none!important}`; no `display` rule on a class that JS toggles with `.hidden`.
- A real crafted logo. A letter in a rounded or gradient square is not a logo.

## AI text and citations
- Every answer, citation excerpt, detail page, tooltip and tour string renders through the template's markdown renderer (`static/mdlite.js`, `src/lib/markdown.ts` or `answer-render.js`). Literal `**`, `#`, `|` or `[text](url)` on screen is a FAIL. Test with a multi-item numbered answer.
- Inline superscript citation markers sit in the prose at the claim, numbered to the sources panel; offsets come from the server, never the model.
- Citations are always visible and clickable, and open the source scrolled to the highlighted passage. A citation that links nowhere is a FAIL.
- Answer and sources use the full width. A narrow answer beside a tall source stack with a blank void is a FAIL.
- A qualitative confidence badge is visible by default on every answer. Never a raw REMi numeral. Below threshold it names an action ("check the sources").
- Dash scrubbing matches dash codepoints only: `replace(/\s*[\u2014\u2013]\s*/g, ' - ')` (the two escapes are the em and en dash codepoints). Never a class with a space in a range.

## Widths
- Every route passes at 390x844 (`is_mobile=True`) and 1440x900. Verify in rendered pixels, not by reading CSS.
- At 390 px: nav is a drawer or hamburger; drawers and modals are opaque with a backdrop; no floating control over content; `document.documentElement.scrollWidth === 390`.
- Wide grid or flex children get `min-width: 0` and their own `overflow-x: auto`. The H1 is at least 20% smaller at 390 px than at 1440 px.

## Brand
- Named prospect: the captured brand from `tools/brand_capture.py` output, no Progress header. Generic demo: tokens from `brand/progress-official.json` and the `:root` block in `brand/progress-hyperframes-brand.md`.
- Palette as named `--color-*` tokens on `:root`: at least six tokens, two hue families, distinct hexes.
- Fonts: `@font-face` from `brand/fonts/ProgressSansDisplayVF.woff2` and `ProgressSansTextVF.woff2`. Arial is the only approved fallback; never a Google Font substitute.
- Progress mark: `brand/progress-logo-dark.svg` on light, `brand/progress-logo-white.svg` on dark. Never `logo-black.png` or `logo-white.png`; those are per-campaign slots holding the last prospect's logo (`brand/LOGO-SLOTS-README.md`). Render and look.
- Never recolour, stretch, shadow or rotate a logo. Lockup minimum height 75 px.
