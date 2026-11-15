---
mode: agent
description: "Turn a deck's speaker notes into a narrated MP4 with tools/narrate_deck.py, then check it."
---
# Narrate a deck

Speaker notes are the talk track and the single source of truth; the video is the deck, narrated. Do not add
claims the notes do not carry.

## Prepare
1. Read every slide's notes. Fix in the deck, not the script: US spellings, em dashes, banned words, digits that
   should be words for TTS. `clean_note()` strips only pure stage-direction parentheticals and the leading
   `[0:00-0:45] LABEL` line, so leave spoken content out of parentheses.
2. Render frames: `pdftoppm -jpeg -r 150 deck.pdf work/slides/s` (crisper than reused QA images).
3. Choose one voice from `brand/voices.json` by audience and register; write the reason into the run note. Pass
   `--voice <name>` so the pool rotation does not switch voices between slides.
4. Estimate cost: total characters of cleaned notes before the first API call.

## Run
`python tools/narrate_deck.py --deck deck.pptx --slides "work/slides/s-%d.jpg" --voice <name> --motion alternate
--out out/<account>-<label>-<date>.mp4`
- No `--captions` and no `--music` unless the brief says so in writing (music: never).
- Ken Burns goes through `tools/motion.py` (the default); never a hand-rolled zoompan.
- Every later iteration adds `--reuse` so cached takes and alignments are reused with no API calls.
- A short cut narrates a subset of the same frames so visuals never diverge from the deck.

## Checks (evidence, not assertion)
- `ffprobe`: 1920x1080, stereo 48 kHz; integrated loudness -14 LUFS within 0.5 LU (two-pass loudnorm is applied).
- Duration against the sum of take lengths plus gaps and crossfades, within one frame.
- No silence at t=0 (`silencedetect` at `-loglevel info` over the first 12 s).
- Per-line level spread under 1.5 LU after normalisation; no internal gap over 2.0 s inside any take.
- View frames at the start, middle and end, and the first frame of three slides chosen at random: no judder on
  text, no clipped slide edge, the correct slide under its narration.
- Australian English, no em dashes, no banned words in the spoken text (grep the cleaned notes).
- Report: duration, voice and reason, source deck path, md5 of the output, frames viewed.
