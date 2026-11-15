# Definition of Pass - decks

Trimmed from the factory's full DoP (`reference/DEFINITION-OF-PASS.full.md`) to the lines a deck can fail. The gate walks every line and records PASS or FAIL with evidence. One FAIL on any line means not done. A PASS without evidence is a FAIL: attach the rendered images viewed, the check output, and the source that confirmed each number.

## Truth
1. Every product claim traces to source material Jay supplied or the product documentation, with the source named. Nothing from memory. A claim that cannot be confirmed is flagged on the slide or removed, never kept silently.
2. No fabricated numbers: no invented accuracy, adoption, ROI or benchmark figure. The product publishes no accuracy percentage.
3. Demo figures are labelled as demo figures on the slide ("not a product performance claim"), never presented as measured performance.
4. Statistics come from authoritative independent sources, cited on the slide, under about five years old. Market sizing names the provider and gives a range. No vendor number presented as independent; never the target account's competitor as a proof source.
5. Certifications (SOC 2, ISO, PIPEDA) are named only when verified outside the product docs.
6. All pricing is USD. No legible localised price anywhere, including inside a screenshot crop.
7. Locked facts hold: the same number appears identically on every slide and in every companion asset.
8. Reused screenshots are checked against the live product before use; a stale figure in a screenshot is a FAIL.

## Safety
9. No secrets, keys or tokens in any file, slide, note or commit.
10. No hosting-region or infrastructure string visible in any screenshot on a customer-facing slide.
11. Other customers' names and account identifiers are cropped or blurred in every screenshot.
12. No real third-party brand used as if owned; no real personal identifiers; fictional entities and neutral demo logins only.
13. Anything outbound (sent to a customer or partner) is a draft until Jay signs off.

## Language
14. Australian English throughout.
15. No em dashes; use a spaced hyphen.
16. Banned words absent: delve, leverage, unlock, seamless, game-changing.
17. De-AI pass done: no hedging, filler, symmetrical triads or corporate fluff.
18. "Progress Agentic RAG" on customer-facing slides, never "ARAG". "Progress® Agentic RAG" on first prominent use.
19. The room test: the deck survives a CIO, CMO or solutions-architect room without a caveat.

## Deck
20. Built on `templates/progress-corporate-fy26.pptx` through the builders (unpack, edit, repack). No hand-drawn deck, no new template, no old deck patched in place.
21. Max 25 words of body copy per slide, counted from the rendered slide.
22. One idea per slide; the title states the point, not the topic.
23. The deck ends on one clear ask, centred under the closing logo with the text box bottom at or above 6.5 in.
24. Native template layouts used where one fits; a Title Only canvas with drawn cards is the exception, not the default.
25. Fonts are Arial and Arial Bold only; no faked or embedded brand font.
26. Colours trace to `brand/progress-official.json` or the corporate palette; no green text on white below 32 pt; navy is #00216B.
27. Logo, copyright line and page number from the template are visible and unobstructed on every slide; any added logo is the template's own or `brand/progress-logo-dark` or `-white`, never a campaign slot file.
28. Screenshots: thin neutral border, subtle shadow, 11 pt muted caption, aspect-fit, industry matched to the audience.
29. Title slides on layouts 2 and 3 use dark text in placeholders 0, 12 and 16 (the white column), verified in the render.
30. No text frame ends below 6.9 in; no zero-size or off-slide shape; titles share one left margin and top across content slides.
31. Speaker notes carry the talk track on every slide that is spoken to.
32. `checks.py` exits 0 and every check reports how many items it examined.
33. The package audit (`audit_package`) reports 0 findings: no template author names, emails or GUIDs survive in the pptx.
34. The render loop ran after the last edit: every slide converted to an image and viewed; overflow, overlap, contrast and title-body collisions fixed in one cycle; then the whole deck re-rendered and viewed again.
35. Brand audit (`.github/prompts/brand-audit.prompt.md`) run with no open Violation.

## Evidence
36. The gate report lists the slide images viewed, the checks output, the audit line and the source for every number. A relayed verdict is not evidence; the reviewer sees the images themselves.
37. The gate views every slide. A sampled gate is itself a FAIL.
