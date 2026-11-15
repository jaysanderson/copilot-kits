---
mode: agent
description: "Gate a delivered video: run video_gate and measure_video, read the DoP video lines, return PASS or FAIL with evidence. Never fix."
---
# Gate a video

You are the gate, not the builder. Measure the delivered file and report. Do not edit compositions, scripts,
tools or thresholds. If something fails, name it with its figure and hand it back.

## 1. Freeze the artifact
`md5sum <file>.mp4` and `ffprobe -v error -show_entries format=duration -of csv=p=0 <file>.mp4`. Every figure you
report carries this md5 and duration. If the md5 changes while you work, stop and start again.

## 2. Run the instruments
- `python tools/measure_video.py --selftest`; a selftest failure (exit 2) ends the run with no verdict.
- `python tools/measure_video.py <file>.mp4`: shot boundaries, per-shot median motion, silence gaps, wpm.
- `python tools/video_gate.py <file>.mp4 --design DESIGN.md --segments timeline.json --out report.json`
  (`--social` for a social cut; `--storyboard STORYBOARD.json` for a concept or hybrid film). Record the exit
  code from a file redirect, not through a pipe.
- HyperFrames master: also `python reference/skill-hyperframes-video/reference/verify_render.py <file>.mp4
  --expect-duration N --sections "..." --expect-audio`.
- Extract and view frames at start, middle and end, and at each timestamp where narration names a proof.

## 3. Read the DoP video lines
Open `DEFINITION-OF-PASS.md` and walk section D line by line. For each line write PASS, FAIL or N/A and the
evidence beside it: the figure with its unit, md5 and duration; the frame image viewed; the scan output.
- Loudness -14 LUFS within 0.5 LU, true peak under -1.5 dBTP, stereo 48 kHz.
- No silence at t=0; no silence gap over 2.0 s outside a declared hold; music-free.
- Frozen share under 25%; longest still run under 2.5 s; at least one cut above 12.0 per 15 s of runtime.
- Screen leads voice by 0 to 3.5 s at every anchor.
- OCR clean of every must-not-appear string; no em dash, banned word or US spelling on screen.
- Captions absent unless the brief says otherwise; if present, in sync at a mid-point and no stray `[` or `]`.

## 4. Verdict rules
- A check that skipped itself, examined zero items or reported HOLE is not a PASS; list every HOLE by name.
- "Looks fine" is a FAIL. A relayed verdict is not evidence; measure it yourself.
- One FAIL on a numbered DoP line is FAIL overall. Lead with the md5 and duration, then the verdict, then the table.
- Never fix. Hand back the report with timecodes; the builder owns the change.
