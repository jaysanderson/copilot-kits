---
applyTo: "**/compositions/**,**/index.html,**/timeline.json,**/hyperframes.json,**/*.composition.html"
description: "HyperFrames composition contract, verification protocol, motif usage, typescale and safe zones."
---
# HyperFrames compositions

Source of truth: `reference/skill-hyperframes-video/SKILL.md` sections 2 to 9 and its `PLAYBOOK.md`. Engine pinned
at `hyperframes@0.8.15`. Start from `reference/skill-hyperframes-video/template/starter/`, never from a blank file.

## Contract (every file)
- Root: `<div id="root" data-composition-id="main" data-start="0" data-width="1920" data-height="1080"
  data-duration="N">` with an opaque background. A standalone root sits directly in `<body>`; a sub-composition
  is wrapped in `<template>` with its `<style>` and `<script>` inside the template, root styled by `#root`.
- Exactly one paused GSAP timeline, registered as `window.__timelines["<data-composition-id>"] = tl` after the
  build finishes. Any other hook renders a valid, correct-length, frozen MP4 at exit 0.
- Vendor `gsap.min.js` into `assets/` and reference it root-relative. No CDN script at render time.
- Deterministic: no `Date.now`, `performance.now`, unseeded `Math.random`, network fetch, hover or scroll state,
  no `repeat: -1`. A finite repeat uses `Math.floor(duration / cycle) - 1`.
- Seek-safe: every state is a pure function of time. Entrances use `fromTo` with explicit from-states; never
  tween `display` or `visibility` on a clip; animate transforms and paint, never `width`, `height`, `top`, `left`.
- Clips carry `data-start` (seconds, or `"<clip-id> + 0.5"` with spaces around the operator) and `data-duration`;
  the window is half-open, so land an end state before `data-duration`, never on it.
- Fonts: local `@font-face` for `ProgressSansDisplay` and `ProgressSansText` from `assets/*.woff2`, under names not
  in the alias map (`Arial` renders Inter). Build the timeline inside `document.fonts.ready`. Prove the face by a
  canvas width measurement against `sans-serif`, never by `document.fonts.check()`.
- Every `<audio>` has a unique `id`; never `crossorigin` on media; never nest a timed `<video>` in a timed parent.
- Exit animations only on the final scene. A transition moves both scenes at the same timeline position.

## Verification protocol (in this order, every build)
1. `hyperframes lint` clean. A lint error switches off the layout and contrast audits, so clear it first.
2. `hyperframes check > check.log 2>&1; rc=$?` and read the exit code from the redirect, never through a pipe.
3. A `*.motion.json` sidecar with `keepsMoving` scoped to `#root`; `hyperframes keyframes`; `snapshot --frames 6`.
4. Low-quality review render, contact sheet read, then one master render.
5. `python reference/skill-hyperframes-video/reference/verify_render.py <master>.mp4 --expect-duration N
   --sections "a:b,b:c" --expect-audio --render-log render.log`. Run `--selftest` once per project. Run it twice:
   whole timeline with a high `--min-distinct-frames`, then `--sections` at the default floor.
6. Where a beat's meaning is a change in wording, `check_text_beat.py` on the delivered file, selftest first.
7. `tools/video_gate.py` on the master; frames viewed at start, middle and end.
`render` exiting 0 proves nothing. Distinct frame count catches a freeze; inter-frame difference does not.

## Motifs (`templates/motifs`)
- Compose a concept beat from a motif sub-composition (`body-of-knowledge`, `retrieval-narrowing`,
  `threads-and-quality`, `one-engine-every-door` and the rest) via `data-composition-src` and
  `data-variable-values`; the motif's README lists its variables and the beat length it was built for.
- `GRAMMAR.md` binds: a product is one solid object with a verb; stroke dash carries architecture state (solid,
  `20 12`, `6 10`); green is the platform, amber `#C9821F` is the ISV's code; a motif has its subject on screen
  from its own t=0; an element joins its phase's clear list in the same edit that adds it.
- Banned, enforced: glowing brains, node graphs, translucent cubes, particle swarms, blue circuitry, people.
- Run `templates/motifs/check_motifs.py` and `check_overlap.py`, then `tools/check_rendered_overlap.py` on
  rendered extents after any type change.

## Typescale and safe zones
- Brand scale: hero 96 to 140 px Display Bold; subhead 40 to 56 px Display Medium; body 24 to 32 px Text; labels
  18 to 20 px Text. Rules resolving at 40 px or more take Display; smaller inherit Text; never mix in one string.
- Delivery scale is 390 / 1920 = 0.2031. Phone-legible text needs 54 px authored; evidence-class text (figures,
  citations, qualifications) is never the smallest type in the film. Run `tools_typescale.py`, then `tools_overflow.py`.
- Content stays in the top 83% of the frame (above y = 896) so the caption band is free even with captions off.
  Logos and copy sit in clear space away from the device crop; product UI sits in a window on the brand ground.
