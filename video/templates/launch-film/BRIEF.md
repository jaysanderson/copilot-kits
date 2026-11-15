---
workflow: product-launch-video
flow: automation
storyboard: no
message: "Handwritten application forms go in; structured JSON with a confidence score comes out, checkboxes included, and nothing persists. Powered by Progress Agentic RAG."
destination: embed
aspect: 1920x1080
language: en
audience: "ISVCO Holdings (Johan Delport, Kelly O'Donnell) and, through them, ISVCO's own customers: health-scheme and insurance operations teams"
length: 150s
angle: narrative
style_preset: blue-professional
---

## Intent

A showcase of a working system, not a reply to an email. The video breaks down how Progress
Agentic RAG reads the Fin-demo Health membership application sample pack: the documents, the
hard page (the body-diagram checkboxes), then the pipeline step by step (split into pages,
identify each page, one structured ask per page with the page image attached, regroup and
score confidence, delete everything), the real output, the measured result across models,
and the messy samples holding up. It must give ISVCO the confidence to take it to their own
customers as a sales asset. Bookended with "Powered by Progress Agentic RAG". Tone: confident,
concrete, practitioner; a showcase of something that is working. Australian English. No hype,
no "AI magic" language; every claim on screen is one that was measured.

Created 2026-10-16 as a redo of `videos/fin-demo-walkthrough` (same workflow and aspect); the
walkthrough's captures, design spec and staged screens are reused, plus fresh captures of
live process runs.

## Assets

- assets/logo-progress-arag.svg — the Progress Agentic RAG wordmark captured from the app's
  header (white + green on dark); bookends.
- assets/screen-process.png — the live app's Process tab (sample picker, model, modes, "How it
  reads a page" card).
- assets/screen-scoreboard.png — a finished bake-off run: scoreboard table + field matrix.
- assets/screen-bulk-result.png — the bulk-scan result: 28 thumbnails and the first application card.
- assets/screen-bakeoff-top.png, assets/screen-bakeoff-models.png — the bake-off tab's model catalogue.
- assets/form-page3.png — the scanned medical conditions disclosure page (body diagram, two columns of checkboxes).
- assets/form-page1.png — page 1 of the bulk scanner file (handwritten member details, fictional).
- Fresh captures (this run): the result page of a live process run on Example 1 (per-page
  cards, the assembled JSON with confidence), and the page images of the samples
  (Example 1 pages 1–4, Example 10 phone photo, Example 4 faded blue ink).
- Bake-off result (live run, 16 Oct 2026, Example 1): image at ask: chatgpt-azure-5.5 99% F1 1.00
  61.7 s; claude-5-5-sonnet 99% F1 1.00 15.1 s; claude-4-6-sonnet 97% F1 1.00 17.1 s;
  gemini-2.5-flash 93% F1 0.94 12.4 s; gemini-3.1-pro 92% F1 0.88 18.4 s.
- Sample-pack outcomes (chatgpt-azure-5.5, image mode): Example 2 missing undertaking page
  flagged; Example 3 shuffled pages reassembled; Example 4 faded single page, three pages
  flagged missing; Example 6 Word file converted; Example 8 bulk scanner file, 28 pages, seven
  complete applications; Example 10 phone photos, complete application, fields flagged for review.

## Customizations

- Feature the captured screens of the live app and the real scanned pages (show-it-as-is);
  rebuild only the pipeline diagram and the bookends.
- Narration throughout, male narrator (ElevenLabs sa_peter, a native South African English
  male - the audience is South African; "Australian English" in this brief governs SPELLING,
  not accent), Jay's writing voice but
  third person: "the system", "Progress Agentic RAG", never "I built" or "your email".
- Captions OFF (GM, 16 Oct 2026): a clean frame so a player's own auto-captioning has
  nothing to collide with, and the speech left unmasked so ASR can read it.
- Open and close on a "Powered by Progress Agentic RAG" card using the captured wordmark.
- A numbered step structure for the pipeline (five steps) so a sales engineer can pause on any one.

## Notes

- Facts that must stay exact: pages are uploaded one at a time; the ask carries a schema per page
  and the page image (`rag_images_strategies: page_image`); confidence checks are the South
  African ID checksum, date of birth and gender from the ID, cross-page ID agreement, date,
  email and cell formats; fields under 70% go to a review list; every page resource is deleted
  and the deletion verified; 75 generative models on the account; scores vary a little run to run.
- Do not show the fly.dev URL, the API key or the admin token: this is a customer-facing asset.
- Do not frame it as a reply to Johan; no "your question", no "I".
- No em dashes on screen. Australian spelling. Sample applicants are fictional (Jacob Smith).

---

## Sample-pack provenance - MEASURED, 16 Oct 2026 (lead)

The viewer gate asked whether the sample pack is fabricated or consented. The brief
asserted "fictional" twice; an assertion is not evidence, so it was measured.

Every 13-digit candidate in the project (23 of them, from the extraction captures and
the frame packets) was tested against the South African ID checksum (Luhn):

- **21 of 23 FAIL the checksum.** A real South African ID is valid by construction, so a
  pack of real member forms would pass at essentially 100 per cent. This is near-conclusive
  evidence of fabrication.
- Two pass. `1983062100801` has month 83, so it is not an SA ID shape at all and passes
  Luhn by coincidence. `9304044244082` is structurally valid (4 Apr 1993 + valid checksum).
  With 22 plausible-DOB candidates, random fabrication predicts about 2 accidental passes;
  one is below that, not above it.
- Decisive corroboration: `2004044244082`, `9304044244082` and `9804044244082` share the
  tail `4244082` with only the date prefix varying. Three "people" cannot share the last
  seven digits of an SA ID. This is generated test data.

**Conclusion: the pack is fabricated. The question is closed and does not need re-asking.**

Residual, recorded rather than actioned: `9304044244082` is structurally valid and could
coincidentally match a real person, which is true of any synthetic identifier. It is not
legibly visible in the film - the only ID readable on screen is `8201025089084`, which
fails. If that ever changes, re-check this line.
