# Content kit: how to work here

This repo holds written-content skeletons for Progress Agentic RAG (ARAG) sales and marketing: enablement documents, marketing pieces, positioning and an HTML whitepaper template. Every new piece starts from the nearest file under `skeletons/`, never from a blank page. Copy it, keep its section shape, replace the content.

## Voice (full rules load for *.md from .github/instructions/writing-voice.instructions.md)
- Australian English (organise, colour, programme). No em dashes anywhere: use a spaced hyphen " - ", a comma or a full stop.
- Banned words: delve, leverage, unlock, seamless, game-changing. Also avoid utilise, robust, comprehensive, navigate, harness, streamline, landscape, journey, "it's worth noting", "at its core".
- No AI tells: at most one "not X but Y" per page, no reflex groups of three, no rhetorical question answered in the next line, no bridge sentences, no summary paragraph at the end.
- Rhythm: in any five sentences, one under 8 words and one over 25. Paragraphs run 1 to 4 sentences; one paragraph per page may run longer. Use contractions in anything that is not a formal document.
- First person, humble practitioner, plain declarative sentences. State the reasoning in ordinary words, never as a slogan or internal shorthand.

## Truth
- Use only facts from a LOCKED FACTS table (the piece's BRIEF.md, or `skeletons/positioning/messaging-house.md` section 6). Never invent a number, percentage, benchmark, ROI figure or customer quote.
- Product claims are verified or dropped. Name a certification (SOC 2, ISO 27001) only when the brief marks it verified, and say who states it.
- Statistics need an authoritative independent source cited in-text, dated if older than five years. Vendor numbers are labelled as vendor numbers. Market sizing is a named provider plus a range.
- All prices in USD. Other customers are anonymised ("a state agency", "the account"). Never cite the account's direct competitor as proof.
- Outbound (emails, LinkedIn posts, anything sent or published) carries a DRAFT status line until the owner signs it off.
- Never write secrets, API keys, tokens or internal URLs into any file.

## Before delivery
1. Run the de-AI pass (`/de-ai-pass`): watchlist words, structural tells, rhythm, paragraph shape, ending.
2. Room test: would a CIO, CMO or solutions architect accept this as written by a practitioner? If not, it is not finished.
3. Gate with `/content-gate` against `DEFINITION-OF-PASS.md`. A PASS needs evidence; "looks fine" is a FAIL.

## Delivery
- Documents ship as .docx via `tools/md_to_docx_enablement.py` (python-docx only). Call `build_docx(md_path, docx_path, title)` from Python; the `__main__` job list carries the source machine's paths. Markdown is the working format, not the deliverable.
- HTML and PDF outputs use the tokens in `brand/progress-official.json` and the rules in `.github/instructions/html-reports.instructions.md`. Logos: `brand/progress-logo-dark.*` and `brand/progress-logo-white.*` only, never the `logo-black.png` / `logo-white.png` slots.

## Cost
- Draft with the cheapest capable model; move up only for the de-AI pass or a rewrite the cheap model failed twice.
- One piece per chat. Start a new chat for the next piece so context stays small.
- Load recipes with the prompt files in `.github/prompts/`. Point at file paths; do not paste reference files into chat.
