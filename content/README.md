# Content kit for GitHub Copilot

Written-content skeletons and recipes for Progress Agentic RAG sales and marketing, harvested from a larger Claude Code project. The always-on Copilot instructions stay under 50 lines; the recipes live in prompt files that load only when you invoke them.

## What is here
Enablement (`skeletons/enablement/`):
- `security-data-sovereignty-two-pager.md`: deployment modes, residency, isolation, audit, and what we do not claim. Use for a CIO or security review.
- `objection-handling-guide.md`: 14 objections, each with what it sounds like, what it means, the honest answer, the trap, when to concede. Use for reps and SEs live in deals, and as the shape for battlecards.
- `discovery-qualification-framework.md`: six question categories, persona-mapped questions, a scorecard and disqualifiers. Use before a first meeting.
- `pov-playbook.md`: qualification handoff, one-feature scoping, success criteria, a 30-day timeline, exit criteria. Use when a prospect asks to try it.
- `roi-value-model.md`: five value levers, the cost side, one worked illustrative example that is not a benchmark. Use to build a business case in a call.
- `partner-landing-page-template.md`: a vendor-neutral prompt that generates a partner landing page. Use when onboarding a partner.
Marketing (`skeletons/marketing/`):
- `tofu-maintenance-treadmill-onepager.md`: one-page leave-behind brief with copy blocks and layout notes. Use for top-of-funnel conversations.
- `association-wedge-nurture-sequence.md`: four-touch email nurture with placeholders and a locked-facts record. Use for a vertical campaign.
- `tofu-linkedin-series.md`: four standalone posts on one theme. `linkedin-research-tech-agentic-rag.md`: a long-form article with a verification record.
Positioning (`skeletons/positioning/`):
- `messaging-house.md`: positioning, pillars, persona messages and the locked facts table other pieces cite.
- `brand-guidelines-seed.md`: palette, type and motif paste-blocks. `narrative-spine.md` and `talk-track-v1.md`: a 15-minute keynote, arc then verbatim script.
Whitepaper (`skeletons/whitepaper/`): an A4 HTML template with a Python builder, plus a report stylesheet and a two-pass PDF renderer. Use for anything over four pages that ships as PDF.

## How to start
1. Open the repo in VS Code with Copilot Chat. The always-on rules in `.github/copilot-instructions.md` load by themselves; `.github/instructions/` rules load by file type.
2. If there is no brief for the account, run `/locked-brief` and answer its questions. It writes `content/<slug>/BRIEF.md`.
3. Run `/new-piece` with the type, audience, purpose and brief. It copies the nearest skeleton, checks facts, shows an outline and waits for your yes.
4. When the draft is in, open the file and run `/de-ai-pass` (edit mode), then `/content-gate` for a PASS/FAIL walk against `DEFINITION-OF-PASS.md`.
5. For a battlecard or one objection entry, run `/battlecard` instead of `/new-piece`.

## Prerequisites
- Python 3.10 or later and `pip install python-docx`. The docx tool needs nothing else (no pandoc). Its `__main__` block carries the source machine's paths and job list, so call `build_docx(md_path, docx_path, title)` from Python, or edit that block once.
- Whitepaper only: `pip install playwright pypdf` then `playwright install chromium`. `pdfinfo` from poppler is optional. Fix `ROOT` and the asset paths in `build_lego_whitepaper.py` before the first run; the Hex Loop SVG and the screenshots are not in this kit.
- Brand: tokens in `brand/progress-official.json`, fonts in `brand/fonts/`, logos `brand/progress-logo-dark.*` and `progress-logo-white.*`. Read `brand/LOGO-SLOTS-README.md` before touching any logo path.

## Token discipline
- Always-on instructions stay under 60 lines. New rules go in a prompt file or a scoped instruction file, not in `copilot-instructions.md`.
- Prompts load on demand. Point Copilot at a path instead of pasting reference files into chat.
- Start from a skeleton, never a blank page. The structure is already paid for.
- One piece per chat. A new piece gets a new chat.
- Draft with the cheapest capable model. Move up only for the de-AI pass or a rewrite the cheap model failed twice.
