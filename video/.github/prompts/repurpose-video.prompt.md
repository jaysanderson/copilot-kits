---
mode: agent
description: "Cut a social cut, short, vertical or silent loop from an existing final and its project, without re-rendering."
---
# Repurpose a finished video

Inputs: the delivered master `.mp4`, its project folder (`SCRIPT.md`, `timeline.json` or the segment list, cached
voice takes) and the brief line that asks for the variant. Record the master's md5 and duration first; every figure
below is stamped with them. Never re-render the master; cut, re-time and re-mux what exists.

## Pick the variant
- Social cut (60 to 90 s): hook, one proof beat, CTA. Slice segments at sentence boundaries read from the take
  alignment (`assets/voice-el/NN.align.json`); write a CTA that stands alone.
- Short (15 to 30 s): one beat and the lockup. Same rule: cut on words, never mid-clause.
- Vertical (1080x1920) or square: recompose, do not crop. On the HyperFrames path author a new root at the target
  size reusing the sub-compositions; on the Python path re-frame the plate inside a vertical brand stage with
  ffmpeg `scale` and `pad`, logo and copy in clear space. Larger type, fewer simultaneous elements.
- Silent loop: the most striking 6 to 12 s of product motion, no audio stream, first and last frame matched so the
  loop seam is invisible; no narration text left on screen mid-sentence.

## Build
- Python path: `python tools/assemble_segments.py --segments seg-01.mp4:vo-01.mp3 seg-03.mp4:vo-03.mp3 --brand
  progress --title "..." --cta "..." --out out/<name>-social.mp4`, then a two-pass loudnorm to -14 LUFS, -1.5 dBTP.
- Trim a segment with `ffmpeg -i seg.mp4 -ss <t>` (`-ss` after `-i` for a frame-accurate cut you will cite).
- Keep every segment's audio and video the same length (`apad`); verify per segment with separate
  `-select_streams v` and `-select_streams a` probes.
- Captions only if the brief for this variant says so: `tools/captions.py` functions (`words_from_alignment`,
  `cues_from_words`, `build_strip`, `burn`), lower-third safe zone `MARGIN_BOTTOM = 132`, Progress Sans Text; print
  every cue and grep for a stray `[` or `]`. Music is never added.
- Delete orphan segments from a renamed beat before cutting; a cut refuses stale segment names.

## Thumbnail
One per variant, per `templates/storyboards/thumbnail-spec.md`: a real frame from the film or a designed card
carrying the film's own title, the Progress mark and brand tokens, at the variant's aspect. Never a blank card, a
generic icon or an unrelated image. Name it `<name>-thumb.jpg` beside the cut and view it at phone size.

## Gate and hand back
`python tools/video_gate.py out/<name>-social.mp4 --social --design DESIGN.md --out out/social-report.json` and
`python tools/measure_video.py out/<name>-social.mp4`. View first, middle and last frames; check no caption or
card copy is clipped by the new aspect. Report: variant, duration, md5, source master md5, segments used, voice,
loudness, thumbnail path.
