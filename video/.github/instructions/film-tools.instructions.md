---
applyTo: "**/tools/**,**/tools_*.py"
description: "How the film gates and pipeline tools are used and extended, their exit codes, and the no-weakening rule."
---
# Film tools and gates

Read the module docstring before running or editing any tool; each states what it measures and what it cannot see.

## Use
- Shared pipeline: `tools/record_demo.py`, `voiceover.py`, `assemble.py`, `assemble_segments.py`, `narrate_deck.py`,
  `motion.py`, `captions.py` (a library with no CLI; opt-in only). `music_bed.py` is kept for reference and is
  never run on a delivery.
- Shared gates: `tools/video_gate.py` (one command for every film), `measure_video.py` (`--selftest` first),
  `check_rendered_overlap.py`, `filmkit/gate.py <project-dir>` (pre-render; nothing needs rendering).
- Per-project gates: the `tools_*.py` in a copied `templates/launch-film` run from that project's root and read its
  own `SCRIPT.md`, `timeline.json`, `typescale.json` and `assets/voice-el/*.align.json`. Copy them with the project.
- Pass the delivered file, never an upstream proxy: a gate measures the artifact, not the plan.
- Every figure carries the md5 and duration of the file it was measured on and states its unit (for example
  grey levels 0 to 255 at 390 px).
- Run measuring ffmpeg filters at `-loglevel info`; under `-v error` loudnorm, silencedetect and freezedetect
  print nothing and the empty result reads as clean.

## Exit codes
- `video_gate.py`: 0 all checks PASS (HOLEs allowed and named); 1 any FAIL; 2 any control or selftest failure,
  meaning no verdict printed is worth anything. A HOLE exits 0, so read the summary, not only the code.
- `measure_video.py`: 2 when its selftest fails; it refuses to measure.
- `verify_render.py`: 1 on any FAIL. `filmkit/gate.py`: non-zero on any fail; holes are listed by name.
- A process that prints FAIL and exits 0 is decoration; fix the tool, not the report.

## Extend, never weaken
- Add a check to the shared gate (`video_gate.py` or `filmkit/checks/`) with a positive and a negative control
  that run on every invocation. Never write a new `gate.py`, `sweep.py` or `measure.py` for one film.
- A new filmkit check exposes `run(project_root, verbose=False)`, returns `fails` (and optionally `candidates`,
  `warns`, `holes`), prints its population count, and declares by name what it cannot see.
- Never raise a threshold, lower a floor, exclude a file or mark a segment `motion_exempt` to get a PASS. Narrow a
  pattern that over-fires; never shrink the population it covers. Zero of zero is not a pass.
- Prove a new check fires on the real defect it was written for before trusting its first clean run.
- No secrets in any tool: `ELEVENLABS_API_KEY` is read from the environment only.
