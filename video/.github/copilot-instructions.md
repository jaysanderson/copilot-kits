# Video kit: how Copilot works here

This repo is a video-production kit harvested from a Progress Agentic RAG marketing project. Work by copying a
template project (`templates/launch-film`, `templates/exec-film`, `templates/storyboards`) and its gates, then
editing the copy. Never write a new render pipeline, a new gate script or new brand CSS: the tools in `tools/`,
the `tools_*.py` gates in `templates/launch-film` and the tokens in `brand/progress-hyperframes-brand.md` exist.
Recipes live in `.github/prompts/*.prompt.md`; load one per task instead of asking for the whole process here.

## Order of work
1. Brief first (YAML front matter as in `templates/launch-film/BRIEF.md`), and decide the film type at the brief:
   demo film (real product footage is the hero), concept film (animated illustration is the hero) or hybrid.
2. Script before footage. Narration is written and timed before any recording or composition is built.
3. Footage: `tools/record_demo.py --warmup` for a live app (always `--warmup`; record clips serially, never in
   parallel). HyperFrames compositions for produced motion. Never stock footage, never AI-generated imagery.
4. Voice: pick one voice from `brand/voices.json` by reasoned fit to the audience (accent, register), state the
   reason, and use one voice per piece. Never a profile whose entry says placeholder. Estimate TTS cost
   (characters) before the first API call; cache takes and reuse them (`--reuse` on `narrate_deck.py`).
5. Audio defaults: no captions and no music unless the brief says so in writing. A brief line is the only
   authority for captions; music is never added. Loudness is EBU R128: -14 LUFS integrated, -1.5 dBTP, stereo 48 kHz.
6. Assemble, then gate (`tools/video_gate.py`, `tools/measure_video.py`), then write the certificate.

## Livery and brand
- Progress livery surrounds the footage: a brand stage, device frame, title card and end card. Captured product
  frames are never recoloured. Tokens come from `brand/progress-hyperframes-brand.md` sections 1 and 2; fonts are
  the local `brand/fonts/*.woff2` via `@font-face`, never a Google Font substitute.
- One graphic device per piece (Hex Loop for Agentic RAG, cropped and on the 30 degree grid). Logo untouched, at
  least 75 px high, from `brand/progress-logo-*.svg`.

## Cost rule
- Render once. Preview at low quality, read a contact sheet, then render the master once.
- To change a cut, re-cut the existing master with `tools/assemble_segments.py` or ffmpeg; do not re-render.
- One task per chat. Load the matching prompt file; do not paste whole reference documents into the chat.

## Verification
- A gate that skips itself, or examines zero items, is a FAIL, not a PASS. A HOLE needs a human to read it.
- PASS needs evidence attached: the frame images viewed, the scan output, the md5 and duration of the file measured.
- Every score names the source file's md5 and duration. A figure without them is not a result.
- View frames at start, middle and end of every delivered file, plus the frame where narration names each proof.
- Never weaken a threshold or exclude a file to make a gate pass.

## Language
Australian English (optimise, centre, colour). No em dashes; use a spaced hyphen. Banned words: delve, leverage,
unlock, seamless, game-changing. On-screen copy under about eight words; the voice carries the context and never
reads the screen. "Progress Agentic RAG" in full in anything customer-facing; "ARAG" is internal only.
Never write a secret, API key or voice id into any file; `ELEVENLABS_API_KEY` comes from the environment.
