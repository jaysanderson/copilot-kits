# logo-black.png / logo-white.png are PER-CAMPAIGN OUTPUT SLOTS - never "the Progress logo"

`deck-factory/scripts/render_logo.py` writes the CURRENT campaign's captured brand logo to
`brand/logo-black.png` and `brand/logo-white.png`. Whatever sits at those names is the LAST
campaign's customer brand, not a Progress mark. Real incident (22 Sep 2026): the ROI
case-tool build reached for "the generic logo" by filename and nearly shipped Tangerine
Telecom's logo in its branded exports - caught only because the builder rendered the export
to pixels and looked. The stale Tangerine renders are preserved as
`tangerine-logo-black.png` / `tangerine-logo-white.png`.

Rules:
- Need the Progress mark? Use the verified Progress assets (the corporate template's own
  media, or a build's verified SVG lockup) - never these slot filenames.
- After any campaign, prefer renaming the rendered pair to `<campaign>-logo-*.png` so the
  slots do not hold a stale brand.
- Any export/deck path that embeds a logo verifies the rendered RESULT by eye (render to
  image and look), per the verify-in-the-user's-medium rule.

## The real Progress mark, permanently (29 Sep 2026)

`progress-logo-dark.{svg,png}` and `progress-logo-white.{svg,png}` in this folder are the
GENUINE Progress lockup, extracted directly from the corporate template
(`brand/templates/progress-corporate-fy26.pptx`) - never redrawn, never approximated:
- `progress-logo-dark` = `ppt/media/image2.svg` inside the template, used by the master and
  every light-background layout (e.g. "Blank - no text boxes").
- `progress-logo-white` = `ppt/media/image12.svg` inside the template, used by dark-background
  layouts (e.g. "Statement slide 1", bg `#4A41FC`) - confirmed by matching its exact position/
  size to the dark-layout logo placeholder and rendering it to check contrast.

These are permanent, campaign-independent assets - unlike `logo-black.png`/`logo-white.png`
above, they never get overwritten by a campaign's brand-capture step. `scripts/deck_design.py`
uses these two for its brand-furniture primitive (logo + copyright + page number), which every
custom full-bleed background/ribbon primitive must paint on top of, on the correct-contrast
variant for whatever sits behind it.
