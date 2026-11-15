> **REVISION, 16 October 2026 - the palette in this document is SUPERSEDED.**
> The film was rebuilt on the Progress Agentic RAG brand. The near-white stage and the
> indigo accent described below are gone; every authored surface now reads:
>
> | role | was | now |
> |---|---|---|
> | stage ground | `#F4FAFF` cream | **`#00216B`** Progress ink navy (Blue P1) |
> | accent (type, strokes, lit marks) | `#2B2BB2` cobalt | **`#00B563`** Green P2 |
> | structural green (card hairline) | - | **`#008963`** Green P1 |
> | primary type | `#101828` ink | **`#FFFFFF`** |
> | secondary type | `#00123C` | **`#C6D5EB`** Light Grey S1 |
> | tertiary type | `#9A9A9A` | **`#9EAEC3`** Dark Grey S4 |
> | card ground | 4% cobalt | 5.5% white |
> | borders | 20% cobalt | 26% Light Grey S1 |
> | positive | `#059669` | **`#00B563`** |
> | negative | `#dc2626` | **`#FF9AA8`** Red S3 |
> | type | system stack | ProgressSansDisplay / ProgressSansText (`@font-face`, local) |
>
> The bookend panel stays `#00123C` and gains a `#008963` hairline, because on navy its
> edge otherwise disappears. CAPTURED SCREENSHOTS ARE UNTOUCHED - they are recordings of
> a product; the stage around them is Progress, the plates are not. Applied by
> `tools_rebrand.py`, which asserts a hit count per rule and refuses to write on a
> mismatch. All timings below are also superseded: see `timeline.json`.

---
format: 1920x1080
duration: 164s
message: "Handwritten application forms go in; structured JSON with a confidence score comes out, checkboxes included, and nothing persists. Powered by Progress Agentic RAG."
arc: Bookend open → The sample pack → The hard page → Five pipeline steps (split, identify, ask with the image, regroup and score, delete) → The real output → Measured across models → The messy samples hold up → Bookend close
audience: ISVCO Holdings (Johan Delport, Kelly O'Donnell) and, through them, ISVCO's own customers: health-scheme and insurance operations teams
mode: autonomous
music: none
---

## Video direction

- **Palette system** (from `frame.md`, by role): canvas `bg` pale blue-white; ink `text` near-black; secondary `text-muted` deep navy; one accent `primary` cobalt for keywords, numerals, progress fills, badges and the step rail; `positive` green only for a verified or passed mark, `negative` red only for a failed or struck item; cards are `card-tinted` (4% cobalt fill, 20% cobalt border, 14px radius, no shadow); pills are `tag-pill`. The two bookends (Frames 1 and 12) are the only frames that use the deep navy `text-muted` (#00123C) as a full card ground, because the captured Progress Agentic RAG wordmark is white and green and must sit on navy; the `atmosphere` concentric rings are allowed on those two frames only. Captured screenshots and scanned pages sit inside a `card-tinted` window with a thin border, never raw on the canvas. Type: display ramp (`h1`, `h2`, `stat-num`, `metric-value`) for the spoken keyword of a beat, `body` for supporting lines, `h4-eyebrow` cobalt uppercase for the small labels ("STEP 1 OF 5", "MEASURED"). Every pipeline frame (4 to 8) carries the same top-left step rail: five `step-circle` dots with the active step filled cobalt and its label beside it, so a viewer can pause anywhere and know where they are. Australian English, no em dashes on screen, no "AI" language.
- **Motion grammar + reveal model**: long-tail settles (power3 default; expo.out only on a fast arrival); nothing bouncy. Every frame reveals on the spoken cue: at t=0 only the thing the VO is saying is on screen; each further card, row, pill or number arrives when the narration names it, with most reveals in the back half. Held reads at the end of each frame; the only aliveness during a hold is a very low-amplitude jitter on the hero, never breathing, never a back-half pan or push. Within-frame seams are velocity-matched cuts. Keyword emphasis = the cobalt accent snapping onto the word as it is spoken (a timeline color set), not scale. One world across the pipeline: the same four page cards (Example 1 pages 1 to 4) persist in the same slots from Frame 4 through Frame 8, so each step reads as an operation on the same documents.
- **Rhythm / held frames**: Frame 3 (the hard page) and Frame 8 (the deletion) are deliberate breathers: one restrained move, then stillness. Frame 7 (regroup and confidence) and Frame 10 (the scoreboard) are the busiest frames. Frame 9 is a slow push into the real result screen. Frame 12 ends on the held wordmark.
- **Negative list**: no purple-blue "AI" gradients, no bokeh, no drop shadows on cards, no browser chrome or cursors except the app's own captured UI, no stock icons standing in for the real form, no confetti or particle bursts, no infinite loops or random motion, no URL, key or token on screen. Both failure modes banned: slideshow (dump everything then freeze) and screensaver (independent floating elements).
- **Caption band**: all content planned into the top ~83% of the canvas (above y = 896px); the bottom band is the caption pill's.

## Frame 1 — Powered by Progress Agentic RAG

- scene: A navy card carries the Progress Agentic RAG wordmark under a small "POWERED BY" eyebrow; the title "Handwritten forms in. Structured data out." arrives beneath on the pale canvas.
- voiceover: "Fin-demo Health membership forms. Scanned, photographed, filled in by hand, boxes ticked by hand. Here's how Progress Agentic RAG turns them into structured data you can trust."
- duration: 12.608s
- transition_in: cut
- status: animated
- src: compositions/frames/01-powered-by.html
- type: hook
- persuasion: Brand anchor then outcome
- beat: intrigue
- blueprint: titlecard-reveal (Adapt)
- focal: assets/logo-progress-arag.svg
- roles: logo-progress-arag = hero (inside the navy card); title typography = supporting
- sfx: none
- asset_candidates: assets/logo-progress-arag.svg — the Progress Agentic RAG wordmark, white and green, needs a navy ground

narrativeRole: Open as a branded product showcase, not a message to anyone: name the brand, then the promise.
keyMessage: Handwritten forms in, structured data out, powered by Progress Agentic RAG.

Adapt: keep the card-chain contract (one restrained move per state, then hold) but the hero card is the captured wordmark inside a navy `card-tinted`-shaped panel (navy #00123C fill, 14px radius, no shadow) rather than parts flying in; the only atmosphere is two faint concentric cobalt rings behind the card (`atmosphere`, cover-only). Camera locked.
Scene 1 (0.0–3.6s): the navy card (about 880×260, centred, y≈300) fades up with a 0.97→1 scale settle (restrained in); the wordmark inside it fades in a beat later; the eyebrow "POWERED BY" in cobalt sits above the card. Two concentric rings draw outward once behind the card (`svg-path-draw`) and settle at 10% opacity.
Scene 2 (3.6–8.4s): on "filled in by hand", the `h1` title "Handwritten forms in." fades in centred under the card at ~60% width; on "boxes ticked by hand", the second line "Structured data out." appends as a whole-line state swap (`discrete-text-sequence`), with "Structured data" tinting cobalt as it is spoken.
Scene 3 (8.4–end): on "you can trust", a small `h4-eyebrow` "MEASURED ON THE REAL SAMPLE PACK" fades in under the title; hold, the card keeps only a subtle low-amplitude sine jitter.

## Frame 2 — The sample pack

- scene: Seven document cards assemble into a row across the canvas, each a real page: a clean scan, a three-page stack with a gap, four pages out of order, a faded blue-ink page, a Word file card, a skewed phone photo, and a thick stack badged "28 pages".
- voiceover: "It starts with a real sample pack. Clean scans. A missing page. Pages out of order. Faded blue ink. Word files. Phone photos. And one scanner batch with seven applicants in a single twenty-eight page file."
- duration: 14.421s
- transition_in: crossfade
- status: animated
- src: compositions/frames/02-sample-pack.html
- type: context
- persuasion: Concrete evidence of real-world input
- beat: recognition
- blueprint: grid-card-assemble (Adapt)
- focal: assets/ex1-page1.png
- roles: ex1-page1, ex1-page2, ex1-page3, ex1-page4, ex4-page1, ex10-page1, form-page1 = cutouts (the seven document cards); labels = supporting
- sfx: none
- asset_candidates: assets/ex1-page1.png — Example 1 page 1, clean scan; assets/ex1-page2.png — Example 1 page 2 (undertaking); assets/ex1-page3.png — Example 1 page 3 (disclosure A); assets/ex1-page4.png — Example 1 page 4 (disclosure B); assets/ex4-page1.png — faded blue-ink page; assets/ex10-page1.png — skewed phone photo of the form; assets/form-page1.png — page 1 of the 28-page scanner file

narrativeRole: Establish that the input is real and awkward, one kind per beat, so the later pipeline is believable.
keyMessage: Seven kinds of real input, from clean scans to a 28-page batch.

Adapt: keep the staggered assemble into a grid, but the items arrive one per spoken beat (not as one burst) into a single row of seven slots (card width ~200px, 1.4cqw gaps, row centred at y≈470); each card is a `card-tinted` frame holding the page render, with a small `body` label beneath. No zoom-out reveal. Camera locked.
Scene 1 (0.0–2.4s): canvas with the `h4-eyebrow` "THE SAMPLE PACK" and `h2` "Nine files. Seven kinds of trouble." top-left (~45% width); nothing else.
Scene 2 (2.4–12.0s): on each cue the next card arrives into its slot with a power3 scale-settle (`spring-pop-entrance`, zero overshoot), left to right: "Clean scan" (ex1-page1) on "Clean scans"; "Missing page" (a stack of three cards with a dashed empty fourth slot drawn by `svg-path-draw`) on "A missing page"; "Out of order" (pages 3, 1, 4, 2 fanned with their numbers) on "Pages out of order"; "Faded blue ink" (ex4-page1) on "Faded blue ink"; "Word file" (a `card-tinted` card with a large "DOCX" `h3` and a thin page outline) on "Word files"; "Phone photo" (ex10-page1 at a 4° tilt inside its card) on "Phone photos"; "Scanner batch" (form-page1 as a thick stack, a cobalt `tag-pill` "28 pages · 7 applicants") on "twenty-eight page file".
Scene 3 (12.0–end): hold the row; the pill keeps a subtle jitter (`sine-wave-loop`).

## Frame 3 — The hard page

- scene: The scanned medical disclosure page large in a card on the left; cobalt rings land on a checkbox left of one label and right of another; a monospace OCR panel on the right shows the garbled text where the ticks should be.
- voiceover: "The hard page is the medical disclosure. A body diagram, two columns, and the checkboxes sit left of some labels and right of others. Ticked by hand. Run it through OCR alone and the ticks are gone before any question is asked."
- duration: 15.296s
- transition_in: push-slide LEFT
- status: animated
- src: compositions/frames/03-the-hard-page.html
- type: pain_point
- persuasion: Show the failure mode before the fix
- beat: tension
- blueprint: comparison-split (Adapt)
- focal: assets/form-page3.png
- roles: form-page3 = hero (left card, the page top-anchored so both columns are visible); OCR panel = supporting (right, authored); rings and labels = supporting overlays
- sfx: none
- asset_candidates: assets/form-page3.png — the scanned medical conditions disclosure page, two body-diagram columns with checkboxes beside the labels, handwritten X marks

narrativeRole: Make the viewer see why plain OCR fails on this page, so the image-at-ask step later lands as the answer.
keyMessage: Boxes sit on both sides of the labels, and OCR text loses the handwritten ticks.

Adapt: keep the left/right comparison contract (PAGE on the left, OCR TEXT on the right, a 160px gap, the two cards entering mirrored) but no 3D book-open; both cards are flat `card-tinted` windows. The page card is a CSS crop of the two body-diagram columns (the region around the diagrams and their checkbox lists). Camera locked.
Scene 1 (0.0–3.0s): `h4-eyebrow` "THE HARD PAGE" and `h2` "Medical disclosure" top-left; on "body diagram" the page card slides in from the left into the left ~48% (x 96–920, y 200–860) with a power3 long-tail settle.
Scene 2 (3.0–8.6s): on "left of some labels" a cobalt ring draws (`svg-path-draw`) around a checkbox on the left of its label; on "right of others" a second ring draws around a checkbox on the right of its label; on "Ticked by hand" a third ring lands on the handwritten X beside "Bone / Injury conditions" and a small `tag-pill` "handwritten X" fades in beside it.
Scene 3 (8.6–13.2s): on "OCR alone" the OCR panel slides in from the right into the right ~44% (x 1080–1824) as a monospace `card-tinted` panel; its lines reveal as whole-line states (`discrete-text-sequence`), real garbled OCR: "Serious ear conditions [}- Serious eye conditions", "Lung conditions {]", "Bone / Injury conditions é Mf"; on "the ticks are gone" a `negative`-red dashed outline draws around "é Mf" and a small red label "NO TICK HERE" fades in.
Scene 4 (13.2–end): hold both cards; badges "PAGE" and "OCR TEXT" sit at the top of each card.

## Frame 4 — Step 1: split into pages

- scene: The step rail lights "01 SPLIT"; a single PDF card splits into four page cards that slide apart into four slots, and each gets a cobalt "→ Knowledge Box" pill.
- voiceover: "Step one. The file is split into pages, and each page goes into the Knowledge Box as its own resource. The model only ever looks at one page at a time."
- duration: 10.496s
- transition_in: push-slide LEFT
- status: animated
- src: compositions/frames/04-step-1-split.html
- type: feature_showcase
- persuasion: Mechanism, plainly
- beat: clarity
- blueprint: grid-card-assemble (Adapt)
- focal: assets/ex1-page1.png
- roles: ex1-page1, ex1-page2, ex1-page3, ex1-page4 = cutouts (the four page cards, which persist in these slots through Frame 8); step rail + pills = supporting
- sfx: none
- asset_candidates: assets/ex1-page1.png — page 1; assets/ex1-page2.png — page 2; assets/ex1-page3.png — page 3; assets/ex1-page4.png — page 4

narrativeRole: First pipeline step: one page per resource, so the model is never asked about more than one page.
keyMessage: Split the file, upload each page on its own.

Adapt: keep the assemble-into-a-grid contract but the "grid" is one row of four page slots (card width ~300px, slots centred at x≈420, 780, 1140, 1500; y 300–740), and the cards start stacked as one PDF card and separate into the slots (`center-outward-expansion`, short path). The step rail (five `step-circle` dots, 28px, with the first filled cobalt and labelled "SPLIT") sits top-left under the `h4-eyebrow` "STEP 1 OF 5". Camera locked.
Scene 1 (0.0–2.0s): eyebrow and step rail fade in; a single `card-tinted` card labelled "example-1-complete.pdf · 4 pages" sits centred, showing page 1.
Scene 2 (2.0–6.2s): on "split into pages", the stack separates into the four slots with a power3 long-tail (`center-outward-expansion`), each card revealing its page render and a small "page 1" to "page 4" label.
Scene 3 (6.2–9.4s): on "its own resource", a cobalt `tag-pill` "→ Knowledge Box resource" pops under each card in sequence (`spring-pop-entrance`, 0.2s apart).
Scene 4 (9.4–end): on "one page at a time", a thin cobalt outline draws around the first card (`svg-path-draw`) and holds.

## Frame 5 — Step 2: identify each page

- scene: The step rail lights "02 IDENTIFY"; the same four page cards each receive a type label drawn from their printed headings: APPLICATION, UNDERTAKING, DISCLOSURE A, DISCLOSURE B; a fifth, smaller phone-photo card gets its label from a vision pass instead.
- voiceover: "Step two. Each page is identified from its printed headings. When the headings don't read, like on a phone photo, a vision model names the page from the image instead."
- duration: 10.539s
- transition_in: crossfade
- status: animated
- src: compositions/frames/05-step-2-identify.html
- type: feature_showcase
- persuasion: Mechanism with a fallback
- beat: clarity
- blueprint: fixed-anchor-cycle (Adapt)
- focal: assets/ex1-page3.png
- roles: ex1-page1, ex1-page2, ex1-page3, ex1-page4 = cutouts (same four slots as Frame 4); ex10-page1 = supporting (the fallback case, smaller, lower right); labels = supporting
- sfx: none
- asset_candidates: assets/ex1-page1.png — page 1; assets/ex1-page2.png — page 2; assets/ex1-page3.png — page 3; assets/ex1-page4.png — page 4; assets/ex10-page1.png — the phone photo

narrativeRole: Second step: the system knows which form page it holds before it asks anything.
keyMessage: Pages are typed from headings, with a vision fallback.

Adapt: keep the fixed anchors (the four slots never move) and cycle the labels onto them one per beat; the phone-photo card is a fifth, smaller anchor at lower right (x 1560–1760, y 560–840). Step rail top-left with the second dot filled and labelled "IDENTIFY". Camera locked.
Scene 1 (0.0–1.6s): the four page cards are already in their slots (continuity cut from Frame 4); the eyebrow reads "STEP 2 OF 5".
Scene 2 (1.6–6.0s): on "printed headings", a cobalt underline draws (`css-marker-patterns`) under the heading area of each page in turn, and a `tag-pill` label pops above each card in sequence: "APPLICATION", "UNDERTAKING", "DISCLOSURE A", "DISCLOSURE B" (`spring-pop-entrance`, 0.3s apart).
Scene 3 (6.0–9.6s): on "phone photo", the ex10-page1 card slides in at lower right with a 4° tilt; on "a vision model names the page", a `tag-pill` "APPLICATION · from the image" pops above it with a small cobalt eye glyph drawn by `svg-path-draw`.
Scene 4 (9.6–end): hold.

## Frame 6 — Step 3: one ask per page, with the image

- scene: The step rail lights "03 ASK"; a request card types out a structured ask for page 3: a schema for that page and the page image attached; the answer streams back as checkbox fields read from the page.
- voiceover: "Step three. One structured ask per page. It carries a schema written for that page, and the page image travels with the question. So the checkboxes come back ticked or not, read from the pixels, not from text."
- duration: 13.675s
- transition_in: push-slide LEFT
- status: animated
- src: compositions/frames/06-step-3-ask.html
- type: feature_showcase
- persuasion: The core mechanism, demonstrated
- beat: relief
- blueprint: prompt-type-submit-generate (Adapt)
- focal: assets/ex1-page3.png
- roles: request panel (authored, monospace) = hero; ex1-page3 = cutout (the attached page, left of the panel); answer fields = supporting
- sfx: none
- asset_candidates: assets/ex1-page3.png — Example 1 page 3, the disclosure page the ask is about

narrativeRole: The heart of the showcase: the page image goes with the question, so the ticks are read from pixels.
keyMessage: Schema per page plus the page image equals checkboxes read correctly.

Adapt: keep the signature loop (the ask types in, the machine answers) but no cursor, no chrome beyond a light `card-tinted` monospace panel; the request is a few key lines, not a full payload, and the answer is a short field list. Layout: the page 3 card (ex1-page3, ~300px wide) sits left (x 160–460, y 260–690) with a cobalt connector line drawn to the panel; the panel occupies x 560–1800, y 220–860. Step rail top-left with the third dot filled and labelled "ASK". Camera locked.
Scene 1 (0.0–2.4s): eyebrow "STEP 3 OF 5" and rail; the page 3 card is already in place; the panel rises in with a power3 long-tail settle.
Scene 2 (2.4–8.4s): on "structured ask per page", the first line types: `POST /ask  · resource: page 3`; on "a schema written for that page", the line `answer_json_schema: disclosure_a` types and "disclosure_a" tints cobalt; on "the page image travels with the question", the line `rag_images_strategies: [{ name: "page_image" }]` types and the cobalt connector line draws (`svg-path-draw`) from the page card into the panel, the card gaining a thin cobalt outline.
Scene 3 (8.4–13.4s): on "come back ticked or not", a divider draws and three answer lines stream in one per beat (`discrete-text-sequence`): `bone_injury_conditions: true`, `sugar_diabetes: true`, `vehicle_accident: true`, each `true` tinting cobalt with a small drawn tick (`svg-path-draw`); on "not from text" a muted `body` footnote "read from the page image" fades in bottom-right of the panel.
Scene 4 (13.4–end): hold.

## Frame 7 — Step 4: regroup and score

- scene: The step rail lights "04 SCORE"; the four page cards slide together into one application card headed "JACOB SMITH · ID 8201025089084"; beside it a checklist ticks on, one check per beat, and a pill explains the review list.
- voiceover: "Step four. The pages regroup into one application by the ID number written on them. Then every field earns its confidence score: the South African ID checksum, the date of birth and gender encoded in that ID, whether the ID agrees across the pages, and the format of every date, email and cell number. Anything under seventy percent goes on a review list."
- duration: 23.317s
- transition_in: crossfade
- status: animated
- src: compositions/frames/07-step-4-score.html
- type: feature_showcase
- persuasion: Confidence is earned, not claimed
- beat: trust
- blueprint: grid-card-assemble (Adapt)
- focal: assets/ex1-page1.png
- roles: ex1-page1, ex1-page2, ex1-page3, ex1-page4 = cutouts (collapse from their slots into one stack); application card + checklist = supporting (authored)
- sfx: none
- asset_candidates: assets/ex1-page1.png — page 1; assets/ex1-page2.png — page 2; assets/ex1-page3.png — page 3; assets/ex1-page4.png — page 4

narrativeRole: Fourth step: the pages become one record, and every field's confidence is justified by named checks.
keyMessage: Regroup by ID, then score every field with real checks; under 70% goes to review.

Adapt: keep the assemble contract in reverse: the four cards in their Frame 4 slots converge into a single stack at the left (x 160–560, y 260–760) with a power3 long-tail (`center-outward-expansion`, reversed), and an application header card lands above the stack. The checklist is a `card-tinted` panel on the right (x 700–1800, y 220–760). Step rail top-left, fourth dot filled, labelled "SCORE". Camera locked.
Scene 1 (0.0–3.4s): the four cards converge into the stack on "regroup into one application"; on "ID number written on them", the header `h3` "JACOB SMITH" with a cobalt `tag-pill` "ID 8201025089084" pops above the stack (`spring-pop-entrance`), and the ID digits tint cobalt.
Scene 2 (3.4–14.2s): the right panel fades in with the `h4-eyebrow` "CONFIDENCE CHECKS"; one row per cue, each a drawn cobalt tick (`svg-path-draw`) and a `body` line: "South African ID checksum" (on "checksum"), "Date of birth and gender encoded in the ID" (on "encoded in that ID"), "ID agrees across the pages" (on "agrees across the pages"), "Date, email and cell formats" (on "every date, email and cell number"); beside each row a `stat-num` value in cobalt counts in (`counting-dynamic-scale`): 0.94, 0.95, 0.95, 0.90.
Scene 3 (14.2–end): on "under seventy percent", a `split-highlight` row appears at the bottom of the panel: "under 70% → review list", its "70%" tinting cobalt; hold.

## Frame 8 — Step 5: delete and verify

- scene: The step rail lights "05 DELETE"; the four page resources fade out one by one, each replaced by a thin "deleted" outline, and a stamp lands: "4 / 4 page resources deleted · verified".
- voiceover: "Step five. Every page resource is deleted from the Knowledge Box, and the deletion is verified. Nothing persists. The document was never kept."
- duration: 9.643s
- transition_in: crossfade
- status: animated
- src: compositions/frames/08-step-5-delete.html
- type: feature_showcase
- persuasion: Privacy by design, shown
- beat: reassurance
- blueprint: titlecard-reveal (Adapt)
- focal: assets/ex1-page1.png
- roles: ex1-page1, ex1-page2, ex1-page3, ex1-page4 = cutouts (back in their four slots, then removed); stamp = supporting (authored)
- sfx: none
- asset_candidates: assets/ex1-page1.png — page 1; assets/ex1-page2.png — page 2; assets/ex1-page3.png — page 3; assets/ex1-page4.png — page 4

narrativeRole: Fifth step and a breather: the privacy promise, shown as the pages leaving.
keyMessage: Every page resource deleted, deletion verified, nothing persists.

Adapt: keep the card-chain contract (one restrained move per state, hard seams) but the "cards" are the four page slots emptying in sequence, then the stamp. Step rail top-left, fifth dot filled, labelled "DELETE". Camera locked.
Scene 1 (0.0–1.6s): the four page cards are in their Frame 4 slots; eyebrow "STEP 5 OF 5".
Scene 2 (1.6–6.0s): on "deleted from the Knowledge Box", each card's page render fades to the empty `card-tinted` frame in sequence (0.35s apart), a small muted "deleted" label settling in each; on "verified", a `positive`-green tick draws (`svg-path-draw`) in each empty frame.
Scene 3 (6.0–9.0s): on "Nothing persists", a stamp card scales up centred under the slots (`spring-pop-entrance`, weighty, zero overshoot): a green drawn check, `stat-num` "4 / 4" in cobalt, "page resources deleted", second line "deletion verified".
Scene 4 (9.0–end): hold, still.

## Frame 9 — The output

- scene: The live app's result page in a window: four page thumbnails with their types, then a slow push into the application card (overall confidence, pages 4/4, needs review) and the field table with its confidence bars.
- voiceover: "And here's what comes back. The schema, filled in. A confidence on every field. Four pages found, none missing. One JSON document, ready for whatever system comes next."
- duration: 11.648s
- transition_in: zoom-through
- status: animated
- src: compositions/frames/09-the-output.html
- type: demo
- persuasion: Show the real artefact
- beat: payoff
- blueprint: device-surface-showcase (Adapt)
- focal: assets/screen-result.png
- roles: screen-result = hero (the real result screen inside a `card-tinted` window); callout pills = supporting
- sfx: none
- asset_candidates: assets/screen-result.png — the live app's result page for a finished Example 1 run: page thumbnails with types, the application card with overall confidence, pages 4/4 and needs-review count, and the field table with per-field confidence bars

narrativeRole: The payoff: the real output, not a mock.
keyMessage: Schema filled, confidence per field, pages complete, JSON ready.

Adapt: keep the device-surface contract (the real screen as the surface, camera moves to the feature) but the device is a plain `card-tinted` window with a thin border, no bezel or chrome. Window occupies x 160–1760, y 120–880 initially. 3 depth layers: canvas, window, callouts.
Scene 1 (0.0–3.0s): the window with screen-result.png fades up with a 0.97→1 settle; the `h4-eyebrow` "THE OUTPUT" sits top-left above it.
Scene 2 (3.0–8.0s): on "The schema, filled in", a slow push-in (`coordinate-target-zoom`, scale ~1.5) onto the application card region (the heading "JACOB SMITH · ID 8201025089084" and the overall-confidence, pages, needs-review tiles); on "A confidence on every field", a cobalt outline draws (`svg-path-draw`) around the field table's confidence column.
Scene 3 (8.0–12.0s): on "Four pages found, none missing", a `tag-pill` "pages 4 / 4" pops beside the window's edge (`spring-pop-entrance`); on "One JSON document", a second pill "Copy JSON · Download" pops below it.
Scene 4 (12.0–end): hold on the pushed-in view.

## Frame 10 — Measured, not assumed

- scene: A scoreboard table builds row by row: five vision models on the same four pages, overall scores and checkbox F1, the top three ticked; a line beneath: any of the 75 models, compared on the same scan.
- voiceover: "It's measured, not assumed. Five vision models on the same four pages score ninety-two to ninety-nine percent, and the top three read every checkbox right. Any of the seventy-five models on the account can be compared on the same scan, in one click."
- duration: 16.363s
- transition_in: push-slide LEFT
- status: animated
- src: compositions/frames/10-measured.html
- type: proof
- persuasion: Statistical proof
- beat: confidence
- blueprint: dataviz-countup (Adapt)
- focal: assets/screen-scoreboard.png
- roles: authored scoreboard table = hero; screen-scoreboard = background (ghosted at ~25% behind the table, slightly tilted, for provenance)
- sfx: none
- asset_candidates: assets/screen-scoreboard.png — the real bake-off scoreboard on the live app

narrativeRole: The proof beat: numbers from a real comparison, with the real screen behind them.
keyMessage: 92 to 99 percent across five models; the top three read every checkbox right; any model can be compared.

Adapt: keep the count-up contract (bars fill and numbers count on the same ease) but the chart is a `card-tinted` table, five rows, with a cobalt `bar-track` fill per row and `tabular-nums` numerals. Table at x 160–1400, y 220–620 (36px header, 64px rows). Camera locked. Data (exact): chatgpt-azure-5.5 99% F1 1.00 61.7 s; claude-5-5-sonnet 99% F1 1.00 15.1 s; claude-4-6-sonnet 97% F1 1.00 17.1 s; gemini-2.5-flash 93% F1 0.94 12.4 s; gemini-3.1-pro 92% F1 0.88 18.4 s.
Scene 1 (0.0–2.6s): `h4-eyebrow` "MEASURED, NOT ASSUMED" and `h2` "Five models. Same four pages." top-left; the ghosted scoreboard screenshot settles behind at 25% opacity, tilted 3°.
Scene 2 (2.6–9.4s): on "Five vision models", the table header fades in and the five rows arrive one per 0.5s; each row's bar fills (`stat-bars-and-fills`) while its overall number counts 0→value (`counting-dynamic-scale`); on "ninety-two to ninety-nine", a cobalt bracket draws (`svg-path-draw`) spanning the overall column with the label "92 to 99%".
Scene 3 (9.4–13.2s): on "top three read every checkbox right", the three F1 "1.00" cells tint `positive` green in sequence with a small drawn tick each, and a `tag-pill` "every checkbox right" pops beside them.
Scene 4 (13.2–end): on "seventy-five models", a `metric-value` "75" counts in at the right of the table (x 1480–1760) with the `h4-eyebrow` "MODELS ON THE ACCOUNT" and the `body` line "compared on the same scan, in one click"; hold.

## Frame 11 — The messy ones hold up

- scene: An outcome list builds on the left, one line per sample kind with its result pill; on the right the bulk-scan result screen in a window, 28 thumbnails and the first application card.
- voiceover: "And the messy ones hold up. The missing page is flagged. The shuffled scan is reassembled. Word files convert. Phone photos read, with the doubtful fields flagged. And the twenty-eight page scanner batch comes back as one application per applicant."
- duration: 16.448s
- transition_in: crossfade
- status: animated
- src: compositions/frames/11-messy-ones.html
- type: proof
- persuasion: Robustness across the whole pack
- beat: confidence
- blueprint: grid-card-assemble (Adapt, Benefits vertical-list build)
- focal: assets/screen-bulk-result.png
- roles: screen-bulk-result = cutout (inside a `card-tinted` window, right ~52%); outcome list = supporting (authored, left); form-page1 = background (ghosted behind the window at ~25%)
- sfx: none
- asset_candidates: assets/screen-bulk-result.png — the bulk-scan result on the live app, 28 thumbnails and the first application card; assets/form-page1.png — page 1 of the bulk scanner file

narrativeRole: Close the proof: the same pipeline on every awkward input in the pack.
keyMessage: Missing page flagged, shuffled reassembled, Word converted, phone photos read, 28 pages → one application per applicant.

Adapt: keep the staggered build, but as a vertical list on the left (x 96–800), one line per cue: a cobalt marker pops, a drawn tick, the text wipes in, and an outcome `tag-pill` lands at the line end. The window (screen-bulk-result.png) slides in from the right into x 850–1824, y 190–750 with a long-tail settle at the start; form-page1 ghosted behind it. Camera locked.
Scene 1 (0.0–2.6s): `h4-eyebrow` "THE WHOLE PACK" and `h2` "The messy ones hold up" top-left; the window slides in.
Scene 2 (2.6–12.0s): lines arrive on cue: "Missing page · FLAGGED", "Shuffled scan · REASSEMBLED", "Word files · CONVERTED", "Phone photos · READ, doubtful fields flagged", "28-page scanner batch · ONE PER APPLICANT".
Scene 3 (12.0–14.6s): on "one application per applicant", a cobalt outline draws (`svg-path-draw`) around the first application card's heading in the window ("JACOB SMITH · ID 8201025089084"), and a `stat-num` "28" with the label "PAGES IN · ONE APPLICATION PER APPLICANT OUT" lands under the list.
Scene 4 (14.6–end): hold.

## Frame 12 — Powered by Progress Agentic RAG

- scene: Three short lines land one per beat: "Submit the document." "Get JSON back, with confidence." "Keep nothing." Then the navy card with the Progress Agentic RAG wordmark returns under "POWERED BY" and holds.
- voiceover: "Submit the document. Get structured JSON back, with a confidence score on every field. Keep nothing. Powered by Progress Agentic RAG."
- duration: 9.877s
- transition_in: blur-crossfade
- status: animated
- src: compositions/frames/12-powered-by-close.html
- type: cta
- persuasion: Promise restated, brand anchor
- beat: resolve
- blueprint: titlecard-reveal (Adapt)
- focal: assets/logo-progress-arag.svg
- roles: logo-progress-arag = hero (inside the navy card, final lockup); three lines = supporting
- sfx: none
- asset_candidates: assets/logo-progress-arag.svg — the Progress Agentic RAG wordmark

narrativeRole: Restate the promise in three lines, then close on the brand; a still a sales engineer can leave on screen.
keyMessage: Submit, get JSON with confidence, keep nothing. Powered by Progress Agentic RAG.

Adapt: keep the card-chain contract (one restrained move per state, then hold) and mirror Frame 1: the same navy card with the wordmark, the same two faint rings. Camera locked. Final frame: ends on a held still, no exit.
Scene 1 (0.0–6.2s): three `h2` lines arrive centred, one per cue, each as a whole-line state (`discrete-text-sequence`) with a 0.5s settle: "Submit the document." (0.2s), "Get JSON back, with confidence." (on "structured JSON"), "Keep nothing." (on "Keep nothing"); "confidence" tints cobalt as it is spoken.
Scene 2 (6.2–9.6s): on "Powered by", the three lines ease up by 120px and the navy card with the wordmark fades up beneath them with a 0.97→1 settle, the `h4-eyebrow` "POWERED BY" above it; the two rings draw outward once (`svg-path-draw`) and settle at 10%.
Scene 3 (9.6–end): hold, still.
