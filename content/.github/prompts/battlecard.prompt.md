---
mode: agent
description: "Build a battlecard or objection-handling entry: claim, proof, trap question, counter, with a source on every competitor claim"
---
# Battlecard / objection guide

Build one card (one competitor) or one objection entry per chat. Start from `skeletons/enablement/objection-handling-guide.md`: its numbered entries give the shape, its "How to use this guide" section gives the stance. Ask for missing inputs one at a time: the competitor or objection, the audience (rep or SE), the `BRIEF.md` or messaging house to cite, and any competitor source material the user holds.

## Stance (from the field record in the skeleton)
- Capability usually wins the room; deals die on the commercial path (no path to production, no budget line, "we can build it"). Answer the technical question briefly and honestly, then find the commercial question under it.
- Every entry ends pointed at one small named next step, never at proving the whole platform.
- Concede where the competitor is genuinely better. A card with no concession is not believed.

## Battlecard shape (one competitor)
1. **Who they are**: two lines, factual, sourced.
2. **Where we win**: 3 to 5 rows of claim / proof / trap question / counter. Claim is our position; proof is a brief row or verified capability with its source; trap question is what the rep asks the buyer to surface the gap; counter is what to say when the competitor's rep answers it.
3. **Where they win**: 2 to 3 honest lines and when to walk away.
4. **Pricing posture**: only values in LOCKED FACTS, USD, dated.
5. **Sources**: numbered, with the date each was read.

## Objection entry shape (one objection)
**What it sounds like** (a sentence a buyer actually says) / **What it usually means** / **The honest answer** (3 to 6 lines, plain) / **Proof** (brief rows or sources) / **The trap to avoid** / **When to concede** / **Next step** (one line).

## Source rule for competitor claims
- Every statement about a competitor carries a source line: the competitor's own page, a named analyst report, or named press, with the date read. A roundup blog or a vendor ranking its own product is marked "vendor self-description" and is never presented as independent.
- No source, no claim. Drop it or move it to a "To verify" list at the foot of the card.
- Never state a competitor's certification, pricing or customer count from memory. Never name a certification for our own product unless the brief marks it verified.
- Never use the account's direct competitor as a proof source.

## Before finishing
- Apply the `/de-ai-pass` checklist. Australian English, no em dashes, no banned words.
- `grep -n -i -E "%|x faster|leader|SOC|ISO" <file>` and check every hit against the brief; paste the result.
- If the card ships as a document, export with `build_docx()` from `tools/md_to_docx_enablement.py` and open the .docx. Date and version the file header.
- Report: claims kept with sources, claims dropped and why, and the one thing a human must verify.
