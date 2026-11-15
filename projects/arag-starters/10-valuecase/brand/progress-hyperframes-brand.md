# Progress Brand - Design Direction for Hyperframes (CANON)

Source: brand.progress.com (Progress Visual Identity guidelines), extracted 2 Sep 2026, handed to the
factory by the GM 3 Sep 2026. **BINDING for every Progress / Progress Agentic RAG HyperFrames video and
motion asset.** Hyperframes has no separate token file - brand lives as CSS custom properties in `:root`
of `index.html`. Section 1/2 are the paste-in blocks; the rest is the rulebook the producer must obey.
The `video-producer` and `hyperframes-video` skill must apply this on every Progress-themed build.

## 1. Paste-in `:root` block (corporate Progress)

```css
:root {
  --bg: #FFFFFF; --bg-dark: #00216B; --bg-soft: #F4FAFF;
  --ink: #000000; --ink-on-dark: #FFFFFF; --muted: #6C7589; --muted-dark: #3B424C;
  --logo-green: #5CE500; --logo-gray: #4B4E52;               /* accent only, never dominant */
  --green-p1:#008963; --green-p2:#00B563; --green-p3:#00D364; --green-p4:#62DE7F; --green-p5:#DEF6E1;
  --blue-p1:#00216B; --blue-p2:#2B2BB2; --blue-p3:#4B4BF7; --blue-p4:#5777EA; --blue-p5:#DCECFF;
  --accent:#00D364; --accent-2:#4B4BF7; --accent-dim:#008963; --accent-2-dim:#2B2BB2;
  --highlight:#FFD000; --highlight-2:#FF9AA8; --line:#C6D5EB;
  --font-display:"Progress Sans Display",Arial,Helvetica,sans-serif;
  --font-text:"Progress Sans Text",Arial,Helvetica,sans-serif;
  --font-data:"Roboto Mono",monospace;                       /* code / technical only */
  --iso-angle:30deg; --radius:8px; --stroke-icon:2px; --stroke-illustration:1px;
}
```

Font loading: Progress Sans is proprietary (from the Progress Brand Bank font pack). Load via `@font-face`
from local files; do NOT substitute a Google Font. If the files are unavailable, **Arial is the ONLY
approved fallback**. Roboto Mono (Google Fonts fine) only for code/CLI - never as display/accent.

```css
@font-face { font-family:"Progress Sans Display"; src:url("./fonts/ProgressSansDisplay-VF.ttf"); font-weight:300 800; }
@font-face { font-family:"Progress Sans Text";    src:url("./fonts/ProgressSansText-VF.ttf");    font-weight:300 800; }
```

## 2. Paste-in `:root` overrides (Progress Agentic RAG)

On top of section 1 when the composition is for ARAG. ARAG palette must be the PREDOMINANT set; corporate
Progress palette only as supplementary accents in illustration.

```css
:root {
  --bg-dark:#00216B; --bg-soft:#F4FAFF;
  --brand-deep:#00123C;      /* Blue P1 +45% shade - ARAG primary 1, Hex Loop colour */
  --brand:#2B2BB2;           /* Blue P2 - ARAG primary 2, Hex Loop colour */
  --accent:#00D364; --accent-dim:#00B563; --accent-2:#4B4BF7; --accent-2-soft:#5777EA;
  --tint-green:#90EF8E; --tint-green-2:#CDFFCA; --tint-blue:#DCECFF;
  --highlight:#FFD000; --highlight-2:#FF9AA8;
}
```

**ARAG Hex Loop:** dark-blue gradient (#00123C -> #2B2BB2) hexagonal loop on the 30 deg isometric grid.
Always a CROP bleeding off the frame edge, never whole, never rotated off-grid, never recoloured. Suggested
crops: top-left corner wedge, bottom-right band, diagonal strip behind a headline. Backgrounds: Blue P1
dark (#00216B) or Light Grey S4 light (#F4FAFF). Approved reference: dark-blue Hex Loop crop + white Display
headline + the Progress Agentic RAG lockup top-left.

**Logo:** "Progress(R) Agentic RAG" - Progress brand mark + wordmark, product name in Progress Sans,
left-aligned to the "P", offset one x-height. Horizontal lockup preferred; stacked only if forced. Minimum
height 75 px. Never recolour/gradient/shadow/bevel/stroke/skew/rotate the logo or resize the product name.

## 3. Brand essence
Core promise: "Innovative. Trusted. Proven. Progress that's built around you." Tone of the visual system:
confident, calm, restrained, high-contrast, geometric. Blues = stability/trust; greens = growth/
transformation. The brand "wraps around" people - subjects feel supported, never constrained.

## 4. Colour (summary - full palette in the source)
Primary greens P1-P5: #008963 #00B563 #00D364 #62DE7F #DEF6E1. Primary blues P1-P5: #00216B #2B2BB2 #4B4BF7
#5777EA #DCECFF. Primary palette carries the MAJORITY of content; secondary enhances, never overpowers.
Logo green #5CE500 only as tiny vivid accent. Illustration leads with Green P3, Light Green S3 (#90EF8E),
Blue P3, Blue P4; Yellow S1 (#FFD000) / Red S3 (#FF9AA8) fill small objects only.

## 5. Typography rules
Progress Sans = one system, two fonts. **Display** (impact/hierarchy) = headlines, hero, short titles;
Bold = primary headlines, Medium = secondary/multi-line, Regular = supporting/intro. Never for body.
**Text** (reading/clarity) = body, UI, captions, labels; Light/Regular for body, Bold/Italic emphasis only.
Never a headline substitute; never below 6.5 pt. Hard rules: never mix Display+Text in one string; never mix
adjacent weights in one block (one foundational + one emphasis weight); clear size separation headline/subhead/
body. Type is predominantly BLACK on white or WHITE on dark - colour is the accent, type is the constant.
Suggested video scale: hero 96-140px Display Bold (tracking -0.02em, lh 1.0-1.05); subhead 40-56px Display
Medium; body/caption 24-32px Text Regular (lh 1.4); labels 18-20px Text Regular (tracking +0.02em).

## 6. Graphic devices - ONE per piece, everything angular on 30 deg
- **Hex Loop** (single product, ARAG) - dark blues, cropped, fixed colour, never whole/rotated/recoloured,
  never combine two. Use for ARAG pieces.
- **Helix** (corporate/multi-product) - DNA-ribbon on 30 deg grid, rounded corners, crop only (no visible
  start/end), primary green (preferred)/blue/neutral only, max 3 accent colours on inner strips, never on
  front strips. Green Helix on blues/neutrals; blue Helix on greens/light-grey/white.
- **Motion:** animate device crops with slow drifts/reveals along 30 deg or 150 deg vectors, always bleeding
  off-frame, ease-out; never spin or squash a device.

## 6b. Helix and Hex Loop - the full device rules

Added 29 Sep 2026 from the GM's export of `brand.progress.com/graphic-devices`
(Progress Brand Guidelines | GRAPHIC DEVICES, 17pp). Section 6 above already had the
shape of this right; these are the specifics it did not carry. Nothing here contradicts
it.

**Device choice is BRAND LEVEL, not taste.** The Helix is the corporate device and
extends to the solution / multiproduct level - every cross-product activation. The Hex
Loop is the PRODUCT device, and Progress Agentic RAG is a listed product, so an ARAG
piece takes the ARAG Hex Loop. Stated from the other direction in the guidelines too:
**never use two or more Hex crops for a multi-product or cross-sell piece - reach for
the Helix instead.**

**Helix construction:** 30 deg isometric grid, the same grid the Progress Brandmark is
built on. Rounded corners throughout. Built from FRONT strips and INNER strips, and the
colour accents belong between the fragments of the INNER strips only.

**Helix, additional nevers** (beyond section 6):
- Never use Helix colours for the background behind it. The graphic must stay visible and clearly defined.
- Never stretch it. It must never look thin or resemble a line.
- Never apply a pattern on top of it.
- Never invert or use dark primary hues on the front-facing strips.
- Never extend the strips outside the isometric grid.

**Helix, additional shoulds:**
- Use large crops, but indicate it is part of a larger structure rather than just a green diagonal.
- Leave subjects space inside it - it should feel supporting and uplifting, never constraining. That is the point of the device: it echoes "Progress that's built around you".
- Leave clear space for the logo and copy.

**Backgrounds and patterns:** a background may carry a pattern from the illustrative
style library, and **the pattern colour always matches the background hue**. Backgrounds
and patterns always use the 30 deg angle, for continuity with the device.

**Hex Loop, additional nevers:** never standalone, never two or more crops in one piece,
never rotated off the isometric grid.

## 7-9. Icons / Illustration / Photography
Icons: flat geometric, 2px stroke, single colour per group (Blue S1 #0051D3, Blue S4 #76C1FF, black/white).
Feature icons on a Green P4 #62DE7F shape. Illustration: custom flat geometric, 1px strokes, fills lead lines
accent, no stock. Photography: candid, authentic, people-centric, diverse; narrative not "people staring at
screens"; no handshake/piggy-bank/binary-code/Minority-Report cliches; AI images only if they meet these rules
and are checked for hallucinated detail.

## 10. Layout / logo safe-area
16:9 video = 24-column grid, generous margins, logos + copy in clear space away from device crops. Combination
logo = green mark + gray wordmark (white wordmark on dark). Horizontal clear space = 1/2 mark height (min 14px);
ARAG product name min 75px. Never place the logo on busy/low-contrast backgrounds.

## 11. Producer checklist before render
1. Palette = primary greens/blues lead; secondary only as support; logo green only as tiny accent. ARAG:
   #00123C / #2B2BB2 lead, backgrounds #00216B or #F4FAFF.
2. Type = Progress Sans Display for headlines, Text for everything else; no mixing in a string; Arial only if
   font files absent.
3. ONE graphic device per piece: Hex Loop (ARAG, cropped, dark-blue, fixed) or Helix (corporate, cropped,
   green/blue/neutral). Everything angular on 30 deg.
4. Icons 2px stroke; illustration 1px stroke, flat fills; no stock.
5. Logo untouched, in clear space, above minimum size (ARAG >=75px).
6. Text is black/white; colour is the accent.

## Asset links (require Brand Bank access)
Progress Sans font pack: https://brandbank.progress.com/s/8v5pf7j3cpbsrpx9mc39j3b6
ARAG digital logos: https://brandbank.progress.com/s/htpxvnhpb5tr2qpmjnhwj7tm
ARAG print logos: https://brandbank.progress.com/s/2tcz4wpkcj3qj5hxnm4b7j
ARAG logo/Hex Loop image refs: AgenticRAG_Logo_Primary.png / _Secondary.png / _Hex_Loop_Crops.png (cdn.bfldr.com/JI444684)
Brand team: brand@progress.com
