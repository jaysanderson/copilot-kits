# Video kit for GitHub Copilot

Video-production recipes, gates and templates harvested from a Progress Agentic RAG marketing project, arranged so
GitHub Copilot can produce a film without re-inventing the pipeline. Always-on guidance is small; recipes load on
demand as prompt files.

## What is here
| Path | What it is |
|---|---|
| `.github/copilot-instructions.md` | Always on, under 60 lines: the rules every request must honour |
| `.github/instructions/` | Loaded by file glob: HyperFrames compositions, film tools and gates |
| `.github/prompts/` | On demand: produce-video, demo-walkthrough, narrate-deck, repurpose-video, video-gate |
| `.github/agents/video-reviewer.agent.md` | A review-only agent: evidence, OCR at timestamps, motion, loudness |
| `DEFINITION-OF-PASS.md` | The 46 numbered lines a film is certified against |
| `tools/` | Shared pipeline (record_demo, voiceover, assemble, assemble_segments, narrate_deck, motion, captions) and gates (video_gate, measure_video, check_rendered_overlap, filmkit) |
| `templates/launch-film/` | A HyperFrames product-launch film project: BRIEF, SCRIPT, STORYBOARD, frame.md, index.html, timeline.json and 24 `tools_*.py` gates |
| `templates/exec-film/` | A concept film: DESIGN.md, NARRATION.md, STORYBOARD.md |
| `templates/motifs/` | GRAMMAR.md, FILM-STARTING-POINTS.md and 17 motif sub-compositions with READMEs |
| `templates/storyboards/` | Walkthrough storyboards, VO scripts, steps and narration files, film briefs, thumbnail spec |
| `brand/` | `progress-hyperframes-brand.md` (canon tokens), `voices.json` (voice registry), fonts, logos |
| `reference/` | The source skills, the full DoP and a sample pass certificate |

## Which template for which film
- Product launch, feature reveal, showcase of a working system with captured screens: `templates/launch-film`.
- Concept film (no product surface; animated illustration is the hero): `templates/exec-film` plus `templates/motifs`.
- Live app walkthrough recorded with Playwright: `templates/storyboards` (pay-co storyboard, plant-demo steps and narration).
- Narrated deck: no template; the `/narrate-deck` prompt and `tools/narrate_deck.py`.

## How to start
1. Copy `templates/launch-film` or `templates/exec-film` to `projects/<name>` (or run Jay's harvest script, which
   packages a project folder the same way), keeping the `tools_*.py` gates with it.
2. Open a chat, attach the matching prompt (`/produce-video`, `/demo-walkthrough`, `/narrate-deck`), and work one
   stage at a time: brief, script, storyboard, footage, voice, assemble, gate, certificate.
3. Review with `/video-gate` or the `video-reviewer` agent before anything is called done.

## Token discipline
- The always-on file stays under 60 lines; instruction files load only for matching paths; recipes load on demand.
- Render once, re-cut not re-render; estimate TTS characters before the first API call; cache takes (`--reuse`).
- One task per chat. Reference files by path; do not paste reference documents into the conversation.

## Prerequisites
- ffmpeg and ffprobe on PATH (the `drawtext` filter is not required; captions use Pillow).
- Python 3.11+ with Playwright (`playwright install chromium`), Pillow, numpy, requests, opencv-python-headless,
  cairosvg; pytesseract plus the tesseract binary for OCR checks; `pdftoppm` (poppler) for deck frames.
- `ELEVENLABS_API_KEY` set in the environment or a local `.env` that is never committed; no key in any file here.
- Node 18+ for HyperFrames (`npx hyperframes@0.8.15`), with GSAP vendored into each project's `assets/`.
- Progress Sans font files are in `brand/fonts/` for Progress marketing use only.
