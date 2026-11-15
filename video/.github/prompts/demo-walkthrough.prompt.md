---
mode: agent
description: "Record and narrate a product walkthrough: storyboard, step-timing JSON, record_demo --warmup, voiceover, assemble, gate."
---
# Demo walkthrough

A walkthrough is the transitions. No beat that shows a product function may be a static end state. The app on
screen must itself be at the bar (sharp, on-brand, no raw markdown); fix the app first, then record.

## 1. Storyboard
Copy the shape of `templates/storyboards/pay-co-pay-walkthrough-storyboard.md`: header (source URL, audience,
voice and reason, length, English variant, music none, captions off), then one table per beat with sub-beat, on
screen or crop, exact VO line and value, and an anchor phrase per beat (the phrase that makes the claim, not the
one that cues it). Hook first, the refusal or cited answer as the climax, no route tour.

## 2. Steps JSON and narration
Write `steps.json` as `templates/storyboards/plant-demo-erp-steps.json` and `narration.txt` as
`templates/storyboards/plant-demo-erp-narration.txt` (one paragraph per beat, `[pause]` tags allowed).
- `type` steps carry `"delay": 55` so the question is typed on camera.
- `scroll` `y` is an absolute destination; destinations strictly increase; `goto` resets to 0.
- A scroll whose target exists only after an answer follows `{"action": "waitfor", "selector": "<answer>"}`.
- Record generously: `wait` steps give head and tail to trim.

## 3. Record
`python tools/record_demo.py --url <url> --steps steps.json --out work/clip-01.mp4 --warmup` (add `--auth` for a
storage state file). One clip at a time; remove `_rec_raw` between runs. Then per clip: first-frame mean
luminance (near 250 is a white screen), `ffprobe` duration, and a frame at each anchor to measure its event time.
Probe hero queries against the live app before recording. Keep the synthetic-data footer visible; crop or
neutralise any region or host string.

## 4. Voiceover
`python tools/voiceover.py --file beat-01.txt --voice <name> --out work/vo-01.mp3` per beat, one voice from
`brand/voices.json` with the reason stated. Numbers as words. Check the audio shows a real gap at each tag.
Budget footage against narration: `clip_duration - trim >= audio_duration` per beat, or re-record longer.

## 5. Assemble
`python tools/assemble_segments.py --segments work/clip-01.mp4:work/vo-01.mp3 ... --brand progress --title "..."
--cta "..." --out out/<name>.mp4`, then two-pass loudnorm to -14 LUFS, -1.5 dBTP, stereo 48 kHz. Footage sits in
a device frame on the brand stage; title and end cards use the lockup from `brand/`. Captions off, no music.

## 6. Gate
`python tools/video_gate.py out/<name>.mp4 --design DESIGN.md --segments timeline.json --out out/report.json`.
Sync is the most-rejected defect: measure each anchor in the finished file; screen leads voice by 0 to 3.5 s.
View frames at start, middle, end and at every anchor's spoken time. Deliver a long cut and a 60 to 90 s social
cut from the same segments (see `repurpose-video.prompt.md`). Then the certificate per `DEFINITION-OF-PASS.md`.
