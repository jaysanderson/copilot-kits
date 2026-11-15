---
mode: agent
description: "Write one new content piece from the nearest skeleton, gated by locked facts, a de-AI pass and a room test"
---
# New piece

Write exactly one piece in this chat. Ask for any missing input below, one question at a time, then stop asking.

## Inputs
- **Type**: one of the skeleton types mapped in Step 1.
- **Audience**: the person who reads it (CIO, CMO, solutions architect, ICT lead, partner, rep).
- **Purpose**: the single thing the reader should do or believe after reading.
- **Source brief**: a `content/<slug>/BRIEF.md` with a LOCKED FACTS table, or `skeletons/positioning/messaging-house.md` section 6. If neither exists, stop and tell the user to run `/locked-brief` first.

## Step 1: pick the skeleton
Security two-pager: `skeletons/enablement/security-data-sovereignty-two-pager.md`. Objection guide: `objection-handling-guide.md`. Discovery framework: `discovery-qualification-framework.md`. POV playbook: `pov-playbook.md`. ROI model: `roi-value-model.md`. Partner landing page: `partner-landing-page-template.md`.
One-pager: `skeletons/marketing/tofu-maintenance-treadmill-onepager.md`. Email sequence: `association-wedge-nurture-sequence.md`. LinkedIn post or series: `tofu-linkedin-series.md`. LinkedIn article: `linkedin-research-tech-agentic-rag.md`.
Messaging house, brand seed, keynote spine, talk track: the matching file in `skeletons/positioning/`. Whitepaper: `skeletons/whitepaper/` (then the HTML instructions apply).
Copy the skeleton to `content/<slug>/<type>.md`. Keep its section order and header block (For, Purpose, Grounding, Date, Version). Strip the old body, the old change log and every real customer name; say "the account" instead.

## Step 2: locked-facts check
List every number, product claim and certification the piece will need. Mark each FOUND (quote the brief row) or MISSING. A MISSING item is written around, never guessed. Show this list before drafting.

## Step 3: outline, then WAIT
Give the one-line job of each section or paragraph in order, plus the single call to action. End with: "Reply yes to draft, or change the outline." Do not draft until the user replies yes.

## Step 4: draft
Write into the copied file under the rules in `.github/instructions/writing-voice.instructions.md`. Use the reader's vocabulary, not internal shorthand. Every fact carries its source in a short bracket or a numbered source line.

## Step 5: de-AI pass
Apply the `/de-ai-pass` checklist to the file. Report what changed in one short list.

## Step 6: room test
Read it as the audience. Would a CIO, CMO or solutions architect take this as written by a practitioner who has done the work? Name the weakest paragraph and fix it or cut it. Confirm every price is USD and no other customer is named.

## Step 7: export
For document types (two-pager, guides, playbooks, one-pagers, messaging house): run Python and call `build_docx(Path("content/<slug>/<type>.md"), Path("content/<slug>/<type>.docx"), "<title>")` from `tools/md_to_docx_enablement.py`. Open the .docx and confirm headings, tables, bold and italics rendered without literal asterisks. Posts and emails stay markdown with a DRAFT status line.

## Done when
- The file exists under `content/<slug>/` with its header block filled in and a dated change-log line.
- Every number and claim in it appears in the LOCKED FACTS table, or the piece does not state it.
- `grep -n -i -E "delve|leverage|unlock|seamless|game-changing|\{\{|TODO" <file>` and `grep -n -P "\xE2\x80\x94|\xE2\x80\x93" <file>` (em and en dashes) both return nothing; paste both results.
- The de-AI pass and room test are recorded in the chat with what changed.
- Document types have a .docx that has been opened; outbound pieces carry a DRAFT status line.
- The user has been told the one thing a human must still verify before this leaves the building.
