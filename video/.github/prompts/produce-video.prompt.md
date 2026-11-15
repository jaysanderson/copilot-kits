---
mode: agent
description: "Produce a film end to end: brief, script, storyboard, footage, voiceover, assemble, gate, certificate."
---
# Produce a video

Work the stages in order and stop at any FAIL. One film per chat. Paths are relative to the kit root.

## 1. Brief (decide the film type here)
Copy `templates/launch-film/BRIEF.md` and fill its front matter: `workflow`, `flow`, `storyboard`, `message`
(one sentence the viewer should repeat), `destination`, `aspect`, `language`, `audience`, `length`, `angle`,
`style_preset`. Then write Intent, Assets, Customizations and Notes. Add one line `film_type: demo | concept | hybrid`:
- demo: a real product surface is the hero; produced treatment goes around real footage.
- concept: no product surface; bespoke animated illustration performs each idea (start from `templates/exec-film`).
- hybrid: both, declared beat by beat in the storyboard.
Record facts that must stay exact, strings that must not appear on screen, captions (off unless written here)
and music (never). Every claim traces to a source you hold; nothing from memory.

## 2. Script
Write `SCRIPT.md` as `templates/launch-film/SCRIPT.md`: voice, model, settings and direction at the top, then one
numbered line per beat with its frame. Arc: hook in the first five seconds, problem, capability, proof, CTA. No
route tour. Numbers as words. On-screen copy under eight words; the voice never reads the screen. Australian
English, no em dashes, no banned words. Target 150 to 180 wpm for an explainer, 100 to 140 for a trailer.

## 3. Storyboard
Write `STORYBOARD.md` as the template: per frame `scene`, `voiceover`, `duration`, `transition_in`, `src`,
`type`, `focal`, `roles`. Concept and hybrid beats carry THING, ACTION and RESULT. For a walkthrough use
`templates/storyboards/pay-co-pay-walkthrough-storyboard.md` (per-beat table with an anchor phrase per beat).
A concept storyboard also gets a `STORYBOARD.json` (`film_type`, `beats[]` with `kind` and `mechanism`) so
`python tools/video_gate.py --storyboard-only --storyboard STORYBOARD.json --design DESIGN.md --out sb.json`
can fail it before anything is built.

## 4. Footage
- Live app: steps JSON as `templates/storyboards/plant-demo-erp-steps.json`; `python tools/record_demo.py --url <url>
  --steps steps.json --out work/clip-01.mp4 --warmup`. Serially, one clip at a time; `type` steps carry `"delay": 55`;
  scroll destinations strictly increase; gate any post-answer scroll with `waitfor` on the answer's selector.
  Check the first frame's mean luminance per clip (near 250 is a white screen).
- Produced motion: copy `templates/launch-film`, build frames under `compositions/frames/`, follow
  `.github/instructions/hyperframes.instructions.md`. Compose concept beats from `templates/motifs`.
- Mobile footage sits in a phone bezel; every product plate sits in a window on the brand stage, never full-bleed.

## 5. Voiceover
Choose the voice from `brand/voices.json` by audience and register and write the reason into SCRIPT.md. One voice.
Estimate characters across all lines before the first call. `python tools/voiceover.py --file line-01.txt
--voice <name> --out assets/voice-el/01.mp3`, one take per line, cached. Measure each take with ffprobe; derive
every beat time from the measured take (`tools_align.py`, `tools_retime.py`, `tools_build_index.py`), never
hand-typed. Normalise every line to one speech RMS before assembly. Fail any internal silence over 2.0 s; write
the pause into the script instead of trusting an ellipsis.

## 6. Assemble
- Python path: `python tools/assemble.py --demo work/demo.mp4 --voice work/vo.mp3 --brand progress --title "..."
  --cta "..." --out out/<name>.mp4`, or `tools/assemble_segments.py --segments clip:vo ...` for per-beat pairs.
  `assemble_segments.py` has no loudnorm pass; run the two-pass loudnorm (I=-14, TP=-1.5, LRA=11) after it.
- HyperFrames path: `hyperframes check`, low-quality preview, contact sheet, then one `hyperframes render --quality high`.
- Audio and video in every segment end together (`apad`, never `-t`). Mono voice is panned to stereo at unity.

## 7. Gate
`python tools/video_gate.py out/<name>.mp4 --design DESIGN.md --segments timeline.json --out out/report.json`,
`python tools/measure_video.py --selftest` then `python tools/measure_video.py out/<name>.mp4`, and
`python tools_delivery_gate.py` from the project. Exit 1 or 2 stops the work. View frames at start, middle, end
and at every proof beat; confirm the named thing is on screen and the screen leads the voice by 0 to 3.5 s.

## 8. Certificate
`python tools_certificate.py` prints the figures from the file. Write `<name>.dop-pass.md` shaped like
`reference/plant-demo-plant-showcase-2026-08-07.dop-pass.md`: header table with md5, duration, voice and source, then
one row per numbered line of `DEFINITION-OF-PASS.md` with PASS, FAIL or N/A and the evidence beside it. A single
FAIL on a numbered line means not done. Submit as a draft with known weaknesses written into the note.
