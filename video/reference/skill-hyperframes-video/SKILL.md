---
name: hyperframes-video
description: >
  Produce a "produced, not captured" motion-first video (kinetic typography, numbered builds, metric
  beats, smooth eases, real scene transitions) with HeyGen's HyperFrames engine - the write-HTML-render-
  deterministic-MP4 framework - inside THIS factory's locked-down corporate environment. Use for
  capability/explainer/launch videos and title-and-motion segments where the visuals are invented or
  typographic (NOT screen-capture of a live demo - that stays on the Python pipeline / video-production
  skill). Covers the install workaround for the blocked public npm, the composition and timeline
  contract, the full data-attribute surface, sub-compositions and variables, the motion and transition
  vocabulary, the 386-item registry, live brand capture, ElevenLabs narration with no music, the CLI
  commands worth knowing, and a verification protocol that a frozen, blank, silent or dead-air render
  cannot pass. Self-contained.
---

# HyperFrames video (factory environment)

HyperFrames renders video from HTML. A composition is an HTML file whose DOM declares timing with
`data-*` attributes and whose single paused GSAP timeline is seekable. The engine seeks the page frame
by frame in headless Chrome and encodes with FFmpeg. Deterministic, reproducible, agent-authorable -
two renders of the same composition were byte-identical in testing.

**When to reach for it:** invented or typographic motion - capability explainers, launch videos, stat
and metric beats, animated title cards, kinetic-type segments, and title-and-motion sequences that top
and tail a demo walkthrough. **Not** for compositing a real recorded demo or screen capture: that stays
on `record_demo.py` + `assemble.py` and the `video-production` skill. Section 10 draws the boundary.

**Read in this order.** This file is the operating manual. `PLAYBOOK.md` beside it is the GM's binding
creative doctrine (4 Sep 2026) and outranks the craft guidance here - the mechanics below serve it.
`reference/motion-and-transitions.md` is the motion vocabulary. `reference/cli-and-engine-map.md` is the
command surface and where the engine's own 20-skill library lives.

> **Everything stated as fact below was tested against `hyperframes@0.8.15` on 29 September 2026.**
> Anything not tested is labelled UNTESTED. Several long-standing entries in the previous version of
> this skill were measured to be wrong and are corrected in place, with the measurement shown.

---

## 0. Prove feasibility BEFORE authoring (hard gate)

Install, then `check`, then render a 3s trivial clip, then verify it with
`reference/verify_render.py`. A clean 3s MP4 with genuinely distinct frames is the green light. If it
cannot render after real effort, STOP and report the exact blocker - do not force it for hours.

---

## 1. Install (public npm is blocked; the mirror has a cooldown)

`registry.npmjs.org` is refused. Install from the corporate Harness mirror, which enforces a ~14-day
cooldown: the newest `hyperframes` and fresh transitive deps return **403 Forbidden** on the tarball
even though metadata resolves. Pin the newest already-approved versions.

Work in a dedicated build dir (keep `node_modules` there, never in the factory root). Copy this skill's
`template/.npmrc` and `template/package.json`, and install with the Bash tool's
`dangerouslyDisableSandbox: true` (network is sandbox-blocked by default):

```bash
mkdir -p videos/<name>/hf && cd videos/<name>/hf
cp <SKILL_DIR>/template/.npmrc .
cp <SKILL_DIR>/template/package.json .
export npm_config_registry="https://pkg.harness.io/pkg/ct8onj8YTdaXtKaFsYCRLg/org-marklogic-npm/npm/"
npm install                                # hyperframes@0.8.15 + gsap + sharp override 0.34.2
./node_modules/.bin/hyperframes doctor     # expect green: FFmpeg, FFprobe, system Chrome
```

- **Pin `hyperframes@0.8.15`.** 0.8.15 and older serve HTTP 200 on the mirror; 0.8.20+ returned 403.
  Before bumping, test the tarball: `curl -so /dev/null -w '%{http_code}' "$R/hyperframes/-/hyperframes-<v>.tgz"` (200/302 ok, 403 still in cooldown).
- **Override `sharp` to `0.34.2`** (`"overrides": {"sharp": "0.34.2"}`). `sharp@0.35.4` is 403. Its
  platform binary installs as an optional dep even with postinstall skipped.
- Install scripts are skipped and it still works: rendering uses **system Google Chrome via
  `puppeteer-core`**, so there is no chromium download to unblock. If Chrome is ever missing, point at
  the factory Playwright chromium via `PUPPETEER_EXECUTABLE_PATH` before concluding it cannot render.
- No `timeout`/`gtimeout` on this mac - omit them.
- **`gsap` must be a dependency**, not just assumed. The install needs `node_modules/gsap/dist/gsap.min.js`
  to copy into each project.
- Run every command as `./node_modules/.bin/hyperframes`, with `export HYPERFRAMES_TELEMETRY=off`.

**A reusable install already exists** at `videos/tourism-experience/hf/` (0.8.15, doctor green). Reuse it
rather than reinstalling, unless another session is actively building there.

---

## 2. The silent-freeze failure class - two causes, one shape

This is the most dangerous failure the engine has, so it gets its own section. **A render whose
timeline never ran still succeeds**: valid MP4, exactly the right duration, exactly the right frame
count, **exit code 0**, and every frame identical. Nothing in the exit code, the duration or the file's
validity says anything is wrong.

There are **two independent causes** that produce an indistinguishable result. Both measured.

### Cause A - the timeline is registered on the wrong hook

The contract is `window.__timelines["<composition-id>"] = tl`, keyed by the root's
`data-composition-id`. Anything else (`window.__TIMELINE__`, a mismatched key, registering before an
async build finishes) means the runtime never finds the timeline.

**Good news: `lint` catches this one, statically, for free.** Verified - two explicit errors:

```
x missing_timeline_registry: Missing `window.__timelines` registration.
x gsap_timeline_not_registered: GSAP timeline is created but never registered in
  window.__timelines. The runtime discovers timelines from this registry - without
  registration, animations will not play during preview or render.
```

Render it anyway and you get a perfect-looking 3.0s / 90-frame MP4 with **1 distinct frame**.

### Cause B - GSAP itself never loads

Referencing GSAP from a CDN that is unreachable at render time. `lint` cannot see this (the file is
syntactically fine), but **`check` catches it** with three runtime findings at once: `request_failed`,
`page_error: gsap is not defined`, and `sweep_static: Timeline did not advance under seek`.

A CDN reference is not *always* fatal here - in a shell with network it loaded and rendered
byte-identically to a local copy. That is worse, not better: the failure is environment-dependent and
will not reproduce when you go looking for it. **Vendor GSAP locally, root-relative** - copy
`node_modules/gsap/dist/gsap.min.js` into the project's `assets/` and reference
`src="assets/gsap.min.js"`. A `../` path trips lint `invalid_parent_traversal_in_asset_path`.

### The tells, measured on both causes

| Signal | Frozen | Healthy | Note |
| --- | --- | --- | --- |
| Distinct frames (3s at 1080p) | 1-2 of 90 | 84 of 90 | The reliable one. |
| File size | 16.7 KB | 146.8 KB | Roughly 9x. |
| Wall-clock render | **97s** | **6s** | Counter-intuitive: the broken one is *slower*, because static-frame dedup cannot engage and it waits out the timeline-readiness timeout. A short composition taking minutes is a red flag. |
| Render-log strings | `sub_timeline_readiness_timeout`, `no GSAP tweens (non-GSAP animation)`, `static-frame dedup: disabled`, `timelines not registered after`, `sub_timeline_script_failure`, `Failed to download CDN script` | absent | `verify_render.py` greps for all of these. |

**So: `lint` catches cause A, `check` catches cause B, and `render` catches neither.** Run both, always,
and then verify the encoded file - because a third cause nobody has hit yet would slip past both.

---

## 3. Fonts - the previous instruction in this skill was wrong

**Declaring `font-family: Arial` does NOT render Arial. It renders Inter, fetched from Google Fonts.**

The compiler carries a hardcoded `FONT_ALIAS_MAP` that rewrites system fonts to bundled Google webfonts
and localises them at compile time. Extracted from `node_modules/hyperframes/dist/cli.js`:

```
arial -> inter        helvetica -> inter        "helvetica neue" -> inter
verdana, tahoma, calibri, "trebuchet ms", geneva, optima, "noto sans" ... -> inter
georgia, palatino, times, "times new roman", cambria ... -> eb-garamond
menlo, monaco, consolas, "sf mono", "andale mono" ... -> jetbrains-mono
```

Measured: three separate renders declaring `Arial`, `Inter` and `"Helvetica Neue"` produced
**pixel-identical frames** (same md5). Declaring `Georgia` fetched EB Garamond; `Courier New` fetched
JetBrains Mono. Every run logged `Fetched N font face(s) ... from Google Fonts`. No opt-out env var or
flag was found.

So the old rule ("author in Arial, the sanctioned Progress Sans substitute") was delivering Inter to
every video the factory has shipped through this engine.

**The fix, verified end to end: declare a local `@font-face` with a real font file inside the project,
under a family name that is not in the alias map.**

```css
@font-face {
  font-family: "BrandDisplay";                       /* not in the alias map */
  src: url("assets/BrandDisplay.woff2") format("woff2");
  font-weight: 100 900; font-style: normal; font-display: block;
}
```

The compiler then logs `Embedded local font file: assets/BrandDisplay.woff2 (44 KB -> data URI)`, makes
**no Google Fonts request for that family**, and renders the real typeface. This is also the only
air-gap-safe path.

**For Progress-branded work this is a straight brand upgrade.** `hyperframes capture
https://www.progress.com/agentic-rag` downloads the genuine `Progress Sans Display VF` and
`Progress Sans Text VF` as `.woff2` files (see section 8). Wired through a local `@font-face`, factory
videos render **real Progress Sans** rather than an Arial-shaped stand-in that was silently Inter.
Proven: rendered and viewed. Use it.

If no real font file is available, state plainly in the build report which typeface actually rendered.
Do not claim Arial.

---

## 4. The composition contract

### Root and timeline

```html
<div id="root" data-composition-id="main" data-start="0"
     data-width="1920" data-height="1080" data-duration="12">
```

1. **Standalone root sits directly in `<body>`, with no `<template>` wrapper.** Wrapping it hides
   everything and lint rejects it (`standalone_composition_wrapped_in_template`). Sub-composition files
   are the opposite - they MUST be wrapped. See section 5.
2. **The root needs an explicit pixel box and an opaque background.** Without a resolved height on every
   ancestor, a `height:100%` child collapses to ~0 and content piles into the top-left. The opaque
   background doubles as the seam guard between scenes.
3. **Exactly one paused timeline**, registered at `window.__timelines["<id>"]` where the key equals the
   root's `data-composition-id`. You do not need `window.__timelines = window.__timelines || {}` - the
   runtime creates the registry before inline scripts run. **This exact hook is load-bearing**: any
   other global (`window.__TIMELINE__`, a mismatched key) renders a valid, correct-length, completely
   frozen MP4 at exit code 0. `lint` catches it as `missing_timeline_registry` +
   `gsap_timeline_not_registered` - see section 2, cause A.
4. **Root `data-duration` is the render length, and it is read once at compile time.** Verified: a script
   calling `root.setAttribute("data-duration","12")` on a root authored at `6` rendered exactly 6.000s.
   A `--variables` value cannot change it either. To vary length per output, author it directly. A
   *clip's* `data-duration` is different - it is re-read from the live DOM, so scripts and variables can
   drive clip lengths.
5. Building the timeline inside `document.fonts.ready` is supported; what is banned is registering the
   key **before** the build finishes (lint: `gsap_timeline_registered_before_async_build`).

### Clips

**`data-start` is what makes an element a clip.** The runtime collects `[data-start]` and drives
visibility off it. `class="clip"` is a convention the runtime never reads, but keep writing it: the
shared `.clip { position:absolute; inset:0 }` rule is what gives a scene its full-frame box, Studio uses
it as an edit hint, and lint warns without it. Omit it on `<video>` and `<audio>`.

The visibility window is **half-open: `[start, start + duration)`**. A clip is hidden at exactly
`t = start + duration`, so land an animation's end state slightly *before* `data-duration`, never on it,
or its last frame never renders.

Direct children of the root that carry `data-start` get automatic layout (forced `position:absolute`,
anchored top-left, sized to 100%). Elements **without** `data-start` are skipped entirely - an untimed
full-bleed background needs its own `position:absolute; inset:0` or it collapses to zero height.

### The full attribute surface

| Attribute | Where | Meaning |
| --- | --- | --- |
| `data-composition-id` | root, sub-comp host | Unique id; must match the `window.__timelines` key. |
| `data-width` / `data-height` | root | Pixel frame size. |
| `data-duration` | root | Render length, compile-time. On a clip: its visible window. |
| `data-fps` | root | Frame-rate hint; CLI flags override. |
| `data-composition-variables` | `<html>` | JSON **array** of declarations. |
| `data-start` | any | Seconds, or a clip-id reference. Marks the element as timed. |
| `data-track-index` | any | **Studio display lane only.** The render never reads it. It does NOT control paint order (use `z-index`) and does not prevent overlap. |
| `data-media-start` | media | Offset into the source file. |
| `data-volume` | media | Static gain. `1` = 0 dB, up to `3.98` (+12 dB). |
| `data-has-audio` | `<video>` | Declare an audio track auto-detection would miss. |
| `data-composition-src` | host | Path to a sub-composition file. |
| `data-variable-values` | host | JSON **object** of per-instance overrides. |
| `data-var-text` / `data-var-src` | any | Declarative variable binding, no script needed. |
| `data-hidden` | any | Hides in preview AND render, overriding its window. Reversible. |
| `data-layout-allow-overflow` / `-overlap` / `-occlusion` / `-caption-zone` / `data-layout-ignore` | any | `check` escape hatches - see `reference/motion-and-transitions.md` section 6. |

Legacy names still seen in old files: `data-layer` is now `data-track-index`; `data-end` is now
`data-duration`.

### Relative timing, and its three silent failures

`data-start` accepts a clip id meaning "start when that clip ends", with `+ N` / `- N` offsets. Nothing
in lint checks any of it, and every failure resolves silently to **0**:

- **Spaces around the operator are required.** `data-start="intro - 0.5"` is 0.5s before `intro` ends.
  `data-start="intro-0.5"` is parsed as a reference to an element with that literal id, which does not
  exist, so the clip starts at 0. Verified: a clip written this way landed at t=0 and the layout audit
  caught it only indirectly, as a `content_overlap` against the scene that genuinely was at 0.
- **An unresolved reference resolves to 0**, it does not error.
- **If the target has no resolvable duration, the reference lands on the target's START, not its end.**
- A cycle resolves to 0. Lookup is document-wide, so a reference can reach into another composition.

Snapshot any reference-timed composition and confirm the clip actually starts where you meant.

### Determinism bans

No render-time clocks (`Date.now`, `performance.now`), no unseeded `Math.random`, no render-time network
fetches, no hover/scroll/pointer state, no `repeat: -1`. For a finite repeat use
`repeat: Math.max(0, Math.floor(duration / cycle) - 1)` - **floor, not ceil** (ceil overshoots
`data-duration` and trips `gsap_repeat_ceil_overshoot`).

Never tween `display` or raw `visibility` **on a clip element** - the framework owns clip visibility and
lint rejects it. Use `autoAlpha`, or a zero-duration `tl.set()` at an explicit beat boundary. No `<br>`
in body text; use `max-width` and let it wrap.

### The lint traps that cause a guaranteed first-build failure

- Never pair a CSS initial `transform` with a GSAP tween on the **same** property
  (`gsap_css_transform_conflict`). Set the start inside `gsap.fromTo(el, {x:-40}, {x:0})`.
- Never put `crossorigin` on `<video>`/`<audio>` (`media_crossorigin_breaks_preview`, error, no suppression).
- Never give a `<video data-start>` an ancestor that also carries `data-start`
  (`video_nested_in_timed_element`). Time the wrapper **or** the video, never both. Sub-composition hosts
  are exempt.
- Every `<audio>` needs an `id` (`media_missing_id`).
- Ghost/outline text (`color:transparent` + `-webkit-text-stroke`) reports `text_not_painted`. Use
  gradient-clipped text instead: `background:linear-gradient(...); -webkit-background-clip:text;
  background-clip:text; -webkit-text-fill-color:transparent;`.

**A lint ERROR switches off the layout and contrast audits.** Verified: a composition with one lint error
reported `Layout: 0 issues across 0 sample(s)` and `Contrast: 0/0 text checks`, which reads like a clean
file and means nothing ran. A healthy run shows 9 samples. Clear lint before trusting `check`.

---

## 5. Sub-compositions, variables and a template library

PLAYBOOK sections 10-12 ask for reusable compositions rather than one-off files. This is the mechanism.

**Go modular** once the piece has three or more scene cuts, when a scene is large or reusable, or when a
continuous audio track spans several visual segments (audio at the root, scenes as sub-comps). Keep
`index.html` thin: slots, timing, audio, and a near-empty root timeline. All scene animation lives inside
the sub-comps.

A sub-composition file is the mirror image of a standalone one:

```html
<body>
  <template>                      <!-- the transport container, not decoration -->
    <style> #root { position:absolute; inset:0; } .title { font-size:120px; } </style>
    <div id="root" data-composition-id="scene-a" data-width="1920" data-height="1080" data-duration="3">
      <h1 class="title" id="scene-a-title">...</h1>
    </div>
    <script>
      const tl = gsap.timeline({ paused: true });
      tl.fromTo("#scene-a-title", { y:80, autoAlpha:0 }, { y:0, autoAlpha:1, duration:1.2 }, 0.1);
      window.__timelines["scene-a"] = tl;
    </script>
  </template>
</body>
```

The runtime clones **only the `<template>` contents**. Everything outside it, including the entire
`<head>`, is discarded.

**The three documented pitfalls, with what actually happens on 0.8.15:**

1. **`<style>` in `<head>` instead of inside `<template>`.** Real and nasty. Lint reports **0 errors**;
   `check` failed only incidentally, via a contrast error (1.14:1, because the text rendered as tiny
   unstyled defaults) and some `canvas_overflow` infos. The render completed at **16 KB against 271 KB**
   for the correct version. A composition that happened to stay legible would have passed clean. Grep for
   it: the first `<style>`, `<script>` and `<div data-composition-id>` must all appear AFTER `<template>`.
2. **Host `data-composition-id` not matching the inner one.** The docs describe a 45-second-per-scene
   stall and static frames. **This did not reproduce.** Tested with one sub-comp and again with two (one
   correct, one deliberately mismatched): `check` passed clean, the render was byte-identical to the
   correct version, and both scenes animated. The assembler falls back to the first root in the file.
   Keep matching the ids anyway - lint, Studio and the tooling assume it - but do not burn a cycle
   chasing this as a suspected cause.
3. **Styling the root by a class instead of `#root`.** Confirmed a lint **error**
   (`subcomposition_root_styled_by_class`), and it renders correctly since the producer preserves the
   authored root as an inner wrapper. Treat it as a lint constraint to satisfy, not a render bug. This is
   also the cleanest live demonstration of the "lint error kills the audits" rule above.

Other sub-comp rules: prefer `fromTo()` over `from()` for entrances (the host re-seeks the sub-comp
whenever its clip becomes visible, and `from()` can desync). Never `master.add(child)` a sub-comp
timeline into the host - the runtime drives them independently and nesting causes double-seeks. **A
sub-comp timeline cannot reach host elements**, and vice versa; drive host-root media from the main
timeline at global time. The host clip's `data-duration` is the slot's visible window and takes
precedence over the sub-comp's internal timeline length - shorter and the slot goes blank
(`subcomposition_blanks_before_host`); longer and the slot simply holds the final frame, so there is no
need to pad a timeline with empty tweens. Prefix inner element ids with the scene id to avoid collisions
on the assembled page.

**Variables** turn a composition into a template. Declare an **array** on `<html>`, pass an **object**.
Bind with `data-var-text` / `data-var-src`, or read `window.__hyperframes.getVariables()`. Every scalar is
exposed as a `--{id}` CSS custom property on the root automatically. Per-render `--variables`, per-instance
`data-variable-values`, per-row `--batch`. Full worked example and the `--strict-variables` batch gotcha:
`reference/cli-and-engine-map.md` section 4.

---

### 5a. The motif library - `videos/_motifs/` (GM directive, 4 Oct 2026)

A concept film (video-production skill 0c) is composed from reusable animated illustrations of the
ideas ARAG films keep needing, not invented from scratch each time. Each motif is a sub-composition
with variables in its own directory under `videos/_motifs/<motif>/` with a short README (what idea
it performs, the variables, the beat length it was built for, the film that proved it). Seed set,
first built for the "What is Progress Agentic RAG?" film: `body-of-knowledge` (a disordered pile
of the organisation's content snaps into a labelled, bounded body; open-internet tiles are pushed
out), `retrieval-narrowing` (a question arrives, ~200 passage tiles collapse to the few that answer
it, an answer writes itself from those), `threads-and-quality` (threads draw from answer sentences
back to source tiles; a qualitative quality badge fills), `one-engine-every-door` (one engine mark,
doors arrive one per phrase - website, service desk, phone, CMS, portal - and the same cited answer
appears inside each). Rules: compose a motif rather than redrawing the idea; extend the library when
a film needs a new idea, gate it once in that film; keep each motif in the Progress visual language
(palette, Progress Sans) with texture and travel the eye can see, because a flat shape on a flat
stage measures as still; never fill an illustration slot with the banned generic look.

## 6. Narration - ElevenLabs, one voice, NO music

- **Voice matches the brief.** `hope` (`WZlYpi1yf6zJhNWXih74`, US/neutral) for a US or neutral piece,
  `david` for an Australian audience, and the full ElevenLabs library for any other market or language.
  State the chosen voice and why in the build report. Read `ELEVENLABS_API_KEY` from the factory `.env`
  (strip any trailing `# comment`). Never use a profile whose `voice_id` is a placeholder (`jay`, `john`).
  Never use `hyperframes tts` - that is a local Kokoro model, not our voice.
- **NEVER add music.** Binding GM directive: every factory video ships music-free. A brief's own
  "add music" line is not authority - flag the conflict back. This makes the engine's whole
  music-bed-carving surface, and the `beats` command, irrelevant here.
- **No captions or subtitles unless Jay explicitly asks** (GM directive, 4 Sep 2026).
- Generate narration in **per-scene segments**, `ffprobe` each segment's real duration, then lay the
  scenes out to fit each segment plus a short lead-in. That gives natural sync and lets the piece land on
  a target length.
- **Every `<audio>` needs a unique `id`.** Lint errors with `media_missing_id` and warns that the render
  will be silent. **Correction:** on 0.8.15 an id-less `<audio>` still mixed - measured identical levels
  to the same file with an id. So obey the rule (Studio and the documented mixer selector both depend on
  it) but do not use "audio is present" as evidence the wiring is right, and do not hunt for a missing id
  when chasing a genuinely silent render.
- Verified: `data-start` and `data-duration` on `<audio>` are honoured exactly. A tone placed at
  `data-start="0.5" data-duration="4"` measured -91 dB before 0.5s, -25 dB across 0.5-4.5s, and -91 dB
  after. Audio and video container durations matched to 0.000s.
- For fades, tween `volume` on the timeline rather than swapping `data-volume`. A tween's values
  **replace** the static baseline rather than scaling it, so on a clip whose gain is not `1` you scale
  the tween's target instead (lint warns with `audio_volume_tween_overrides_gain`).
- To level drifting narration segments, use `hyperframes normalize-audio --reference <id> --target <id>
  --write` (integrated LUFS matching) rather than guessing gains. UNTESTED here.
- Keep every product claim KB-verifiable (`nuclia-mcp`). For a REMi or metric beat, show the metric NAMES
  as a measured capability, never fill-to-full bars or ticks - full bars read as an unsubstantiated "full
  marks" claim (Field Rule 5: the KB publishes no accuracy number).

---

## 7. Motion, transitions and the craft bar

Full vocabulary in **`reference/motion-and-transitions.md`**. The load-bearing points:

- **FRAMING REAL CAPTURED TEXT: containment beats magnification, and the band comes from the LINE.**
  Two sentences, learned by failing a gate on the Cinema-group film (29 Sep 2026) where five shots
  clipped the very text they existed to show:
  **A magnification floor is a property of a PUNCH, not of an evidence shot. Frame the content first
  and let magnification fall out; where a shot cannot reach the floor and stay contained, containment
  wins and it is a reveal.**
  **Measure the emphasis band from the LINE, never from the phrase - a superscript sits high inside
  its line, so a band drawn from the phrase box reaches into the line above.**
  Canonical text, with the three geometric assertions and the measurements: the `video-production`
  skill's punch traps (a) to (f). Do not re-state them here - read them there before framing any
  evidence shot.

- **Define the motion system once** on the timeline's `defaults` (`{ duration: 0.6, ease: "power3.out" }`),
  then deviate deliberately. Smooth beats bouncy - vary energy within `sine`/`power1`/`power3`/`power4`,
  and treat overshoot as a playful register you will almost never use in a CIO room.
- **Entrances use `fromTo` with explicit from-states.** `from()` against CSS `opacity: 0` is a 0-to-0 noop
  and the element never appears.
- **Exit animations are BANNED except on the final scene. The transition IS the exit.** This **supersedes**
  the previous instruction in this skill ("entrances with `.from`, exits with `.to`"): fading scene A out
  and then animating scene B in is a jump cut with a dip in it. Move both halves at the same timeline
  position. This is the single biggest reason factory pieces have read as assembled rather than produced.
- Pick ONE primary transition for 60-70% of scene changes plus one or two accents. Medium energy
  (push slide / staggered blocks, 0.3-0.5s, `power2`/`power3`) is the factory default register.
- **Search before you hand-author.** `hyperframes catalog --query "<the beat in plain English>"` ranks
  386 registry moves, and the engine's `hyperframes-animation/rules-index.md` holds ~45 atomic recipes
  plus 18 multi-phase blueprints. Verified reachable and installable from this environment.
- **Animate transforms and paint, never layout.** `width`/`height`/`top`/`left` tweens are forbidden. A
  transformed element must be block-level and sized, or a `scaleX` bar renders as nothing at all.
- **Do not animate a wrapper's `autoAlpha` to reveal a group** - animate the leaf elements individually.
  **Status correction:** the catastrophic version of this (a whole section rendering blank in the mp4
  while snapshots looked fine, the 8 Sep 2026 kickback) **did not reproduce** on 0.8.15 - a wrapper
  `autoAlpha` reveal rendered correctly. Keep animating leaves, because it also gives better motion, but
  treat the blank-section risk as unconfirmed on this version rather than certain.

---

## 8. Live brand capture (Field Rule 8)

`hyperframes capture <url>` pulls a named account's real brand into the build: the exact palette sampled
from the live DOM, a computed design system (typography roles with real sizes and weights, spacing,
radius, shadows, cards, nav), the real logo SVG and imagery, labelled page contact sheets, and **the real
font files as `.woff2`**. That is precisely what Field Rule 8 demands instead of approximation.

```bash
./node_modules/.bin/hyperframes capture https://<account-site>/<page> \
  --output ./capture/<account> --skip-vision --timeout 60000 --json
```

Takes about two minutes - run it in the background. Full output map, the Progress example, and the
`--max-screenshots` caveat: `reference/cli-and-engine-map.md` section 3.

---

## 9. Gate, render, verify

```bash
HF=./node_modules/.bin/hyperframes
export HYPERFRAMES_TELEMETRY=off

$HF lint  ./app                                   # fast, while authoring
$HF check ./app > /tmp/check.log 2>&1; rc=$?      # THE gate - see the piping trap below
$HF keyframes ./app                               # the motion map: what animates, when, from/to
$HF snapshot ./app --frames 6                     # writes snapshots/contact-sheet.jpg - LOOK at it
$HF render ./app --quality high --output <ABS_OUT>.mp4 2>&1 | tee /tmp/render.log
.venv/bin/python <SKILL_DIR>/reference/verify_render.py <ABS_OUT>.mp4 \
    --expect-duration <sec> --sections "0:12,12:28,28:45" --expect-audio --render-log /tmp/render.log
```

**Write a `*.motion.json` sidecar. This is the most valuable thing in the engine the factory was not
using.** `check` discovers it by basename with no flag, and its findings are gating errors. It is the only
automated check that catches a section settling early and holding a frozen frame - which `check` otherwise
passes with zero findings, because `sweep_static` fires only when the *whole* composition never moves.

Measured: a well-formed 8-second section whose content all landed by t=2.2s rendered bit-identical frames
from 2.2s to 8s and `check` passed it clean. With one `keepsMoving` assertion it failed with
`motion_frozen: nothing moves within #root between 2.2s and 8s (5.8s static)` - the section, the window
and the duration, before any render.

**Scope `keepsMoving` to `#root`, not to individual scenes.** It measures across the whole composition
duration, so a per-scene selector counts every second the scene is legitimately hidden as static and
false-fails. Root scope also gives strictly better coverage: when any scene freezes, nothing in the root
moves either. Template and worked assertions: `template/starter/index.motion.json`.

**Gating traps, both measured:**

- **Piping `check` to `tail` or `grep` destroys its exit code.** `check ... | tail -1; echo $?` printed
  `0` on a genuinely failing composition. Redirect to a file and read `$?`, or use `${PIPESTATUS[0]}`.
- **`render` exits 0 on a completely frozen video.** A successful render proves nothing. Ever.
- **NOTHING IN THIS SUITE READS TEXT, so a beat whose meaning is a CHANGE IN WORDING passes the
  whole gate while being broken.** Every instrument here reads geometry, motion, colour, level or
  duration. Real case (RAG explainer, 1 Oct 2026): a card was to change from "fourteen days" to
  "twenty-one days" under the line "update the material, and the answer updates", and the text
  cross-fade was scheduled 2.9s before the cards resolved - so the card was NEVER legible reading
  fourteen, and the picture was static under a narration line promising a change. `lint` rc 0,
  `check` rc 0, motion sidecar clean, three `verify_render` runs green at 11, 18 and 27 checks. The
  composition held the right string, which is why reading the source confirmed it and reading the
  frames refuted it. **Where meaning lives in words, use `reference/check_text_beat.py`** - it OCRs
  the crop out of the DELIVERED file at named timestamps, asserts each string in its own window AND
  that neither appears in the other's, and has a two-arm selftest. Run the selftest first.
  Underlying cause worth carrying past the tooling: the update time and the resolve time were each
  correctly placed against their own voiceover line, and nothing reconciled them against each
  other. **Two events correctly timed against a third thing are not thereby ordered relative to one
  another** - where one element must exist before another can change it, assert the ORDER.
- **`--max-static-run` is a DISTINCTNESS check and cannot see perceptual stillness at all.** A drift
  moving a faint element by a fraction of a level keeps consecutive frames distinct forever while
  moving nothing a person can see: it reported a healthy 0.6s longest run over two shots measuring
  86% and 89% perceptually static. Add a per-frame mean-absolute-difference measure PER SCENE, and
  **state the unit with the threshold** - 0.02 in 0-255 units and 0.02 in 0-1 units differ by a
  factor of 255, and quoting one without the other had a second agent reproduce "100% of the film
  static" and nearly report the original finding as broken. Per scene, not whole-film: 13% across
  140s reads as nothing until you see it is two specific shots and every other scene is zero.
- **NOTHING IN THIS SUITE ASKS WHETHER THE IDEA IS SHOWN, so an explainer made entirely of typeset
  statements passes every gate and the GM rejects it as "text on a background" (RAG explainer, GM
  rejection 30 Sep 2026 23:33Z).** Every instrument above passed that film, including a fresh-eyes
  viewer asked "did you understand what RAG is" - comprehension is not engagement, and only
  engagement predicts the GM's chair. A concept explainer teaches a MECHANISM, and a mechanism is
  explained by ANIMATING it: for every beat name the thing, the action and the result the
  illustration performs while the voice says it, and build that as bespoke motion in the brand's
  own visual language. Type carries labels; a card with the sentence on it is not an illustration of
  the sentence. **Measure it on the delivered master, per shot: the share of runtime in which an
  animated illustration (not type, not a card, not a UI plate) occupies at least a third of the
  frame, stated as a fraction, plus the longest type-only run in seconds.** The instrument is
  `scripts/measure_illustration.py` (run `--selftest` first - four controls, the load-bearing one
  is DENSE TYPE, the nearest legitimate look-alike to a diagram). **Floors, binding (lead, 1 Oct
  2026), set against the Better Together Library's seven films so that the reference's own weakest
  film FAILS - the GM's bar is "same or higher":** ILLUSTRATED >= 40% of runtime (coverage >= 1/3;
  reference median 67.0%, worst 35.6%), ANIMATED-ILLUSTRATED >= 15% (the region itself moves,
  mean abs diff frame n to n+6 >= 0.5 in 0-255; reference median 24.1%, min 16.9%), longest
  TYPE-ONLY run <= 20s (reference median 10s, max 26s), and within a mechanism beat no type-only
  hold over about three seconds. The rejected RAG explainer measured 0.0% / 0.0% / 140s. Known
  limits the gate prints beside its verdict: brand ornament (a large hex ribbon) counts as
  illustration, so it is generous to brand-heavy films; OCR reads a logo wordmark as text, so a
  rail of lockups scores as type; a framed UI plate counts as illustration. Read the TOP of the
  per-shot ranking, never the aggregate - the same discipline as the perceptual-motion floor
  above. The banned explainer aesthetic (glowing brains, node graphs, translucent cubes, particle
  swarms, blue circuitry) still binds; the fix is bespoke illustration, never generic AI imagery and
  never more motion on the type. Brief the fresh-eyes viewer with both questions - "did you
  understand it" and "would you keep watching" - and record the answers separately.
- **CUT RATE - nothing in the suite asks whether the frame ever changes decisively (same audit).**
  The rejected explainer's largest frame-to-frame mean-absolute-difference across 140.1s was
  **4.65 in 0-255 grey levels @480x270** - one continuous dissolve, no cut - while the reference
  flagship at the same duration reached 34.97 with 19 shots. `verify_render.py` passed it on every
  check because a slow dissolve keeps frames distinct and never holds still. Binding floors,
  measured by `scripts/measure_video.py` (six controls, `--selftest` first; control [b2] proves a
  continuous pan is NOT counted as a cut): **max frame diff >= 25.0** and **at least one boundary
  above 12.0 per 15s of runtime**, both in 0-255 @480x270, unit stated in the figure.
- **SILENCE IS FAILED BY ITS OWN LENGTH, NOT BY SECTION.** "Non-silent in every named section"
  passed a 7.57s hole inside a longer section; the reference's seven films carry 0-1 gaps over
  0.6s, longest 1.11s. Binding: **no silence gap over 2.0s** outside a declared held beat,
  measured with `silencedetect=noise=-50dB:d=0.6` at **`-loglevel info`** (at `-loglevel error`
  the filter prints nothing and the check reads clean - reproduced as a control). State the gap
  count and the longest gap in the build report.
- **PROVE THE TYPEFACE BY METRIC, never by declaration and never by `document.fonts.check()`** -
  it returned `true` for `Progress Sans Display VF` on a page that loads no such file. Measure a
  canvas string width at the declared family and compare against `sans-serif` and `serif`
  references; a match to a fallback is a FAIL. (This is the instrument that caught the reference
  site itself shipping Arial while its subject was Progress - the one dimension where our films
  are ahead, and only because `brand/fonts/` is loaded by `@font-face`.)
- **Every product beat frames real UI on the brand stage - 100%, counted.** Of the shots showing
  product UI, the fraction inside a window or device frame inset on the brand ground, never
  full-bleed. The reference meets this on every product beat of all seven films measured.
- **State the narration rate in the build report** - words over summed cue duration. Reference
  explainer band **151-181 wpm**; flag an explainer below 130 or above 195. (Trailer and
  atmospheric pieces keep the `video-production` skill's 100-140 band; the register sets the band,
  the number is still measured.)
- **A film that is one of a set declares its template and its variables by the third film.** The
  reference runs one 60s arc - problem, partner context, mechanism, lockup, proof, CTA - with the
  product, the dashboard, the clause and the two CTA cards as variables. PLAYBOOK sections 10-12
  ask for it; from now the build report names the shared sub-composition and its variable list, or
  says why this piece is not part of a set.

**Verify the ENCODED mp4, not the composition.** `reference/verify_render.py` is the gate and it runs
every check below with PASS/FAIL and the measured number:

1. Render log carries no timeline-failure signature (all six strings from section 2).
2. Duration matches the intended cut.
3. Video stream, codec and resolution present.
4. Bytes-per-second above a freeze floor.
5. **Distinct frame count across the whole timeline** - the freeze catch.
6. **Longest unbroken static run** - the dead-air catch, and the encoded-file mirror of the sidecar's
   `keepsMoving`.
7. Both of the above **per named section** - a whole-timeline figure stays healthy while one section
   is frozen, which is exactly the defect that has reached the GM before.
8. Audio stream present, non-silent overall, and non-silent **in every named section**.
9. Audio and video ending together.
10. Final frame matching the held frame.

It has a `--selftest` that synthesises a frozen file and confirms the scanner fails it. Run it once per
project - a gate you have never seen fail is not a gate. Verified against a real frozen render (3 FAILs
on independent signals), a good one (0 FAILs), and a legitimate held ending (0 FAILs).

### Measure a freeze by DISTINCT FRAME COUNT, never by inter-frame difference

The factory's usual motion instrument - mean absolute inter-frame difference on a downscaled greyscale
decode, built for the tourism film's footage motion floor - **cannot tell a frozen render from a working
one, and ranks them the wrong way round.** Measured on the two renders from section 2:

| Render | median diff @192x108 | max diff | distinct frames |
| --- | --- | --- | --- |
| Frozen (timeline never ran) | 0.0000 | **0.0145** | **2 of 90** |
| Working | 0.0000 | **0.0029** | **84 of 90** |

Both medians are zero, and the **frozen** render has the **larger maximum** - so a max-diff threshold
scores the broken file as the more animated of the two. Resolution is not the cause: at 480x270 the
medians are still 0.0000 and the ordering is unchanged. A mean over the whole frame is dominated by the
unchanged brand ground, and authored typographic motion only ever touches a small fraction of it. Do not
reuse the footage motion instrument on an authored composition.

Distinct frame count separates them cleanly with no threshold tuning, so that is what the gate uses.

**And a held end state is legitimately static**, so the question is never "is every frame different". It
is two separate questions with two separate thresholds, which is why the gate asks both:

- **How many distinct frames exist** (`--min-distinct-frames`, default 8). A frozen render sits at 1-2
  however long it is. An absolute floor beats a ratio here: measured, a 6s piece with a deliberate 4s
  hold scored 62% against a 50% ratio floor, so a slightly longer hold would have false-failed.
  **`--min-distinct-frames` is ALSO applied to every `--sections` window, halved - so raising it to
  suit a long timeline will false-fail every short section.** Measured on the tourism film: a floor of
  300 on a 112s master reported seven section FAILs reading `51 distinct of 51`, `19 of 19`, `13 of 13`
  - every one of them 100% distinct and perfectly alive. A section samples roughly 5 frames per second,
  so a 2.5s interstitial yields 13 samples and anything above a floor of 26 fails it. **Run the gate
  TWICE: once whole-timeline with a high floor and no `--sections`, once with `--sections` at the
  default floor.** Both runs are cheap and each is checking something the other cannot.
- **How long is the longest unbroken static run** (`--max-static-run`, default 3.0s). Raise it only for a
  deliberately long end-card hold, and say so in the build report.

**One measurement method matters enough to state on its own.** When checking windowed audio,
`-ss` MUST come **before** `-i`. With output seeking, `volumedetect` sees every frame and reports the
whole-file level for every window - measured, it reported -26 dB on a window that was genuinely -91 dB
silent. A per-scene audio check written the wrong way round passes a silent video.

**Status of two previously-asserted defects, both re-measured and both NOT reproduced on 0.8.15:**

- *Final frame loses the root background.* Tested on a flat background, a gradient root, and two modular
  sub-comp renders. The last six frames were identical luma every time (for example 41.4877 held vs
  41.487 final). Keep the check in the gate, since it is free and a reviewer will catch a real one, but do
  not reflexively drop a frame at delivery - verify per build.
- *AAC padding leaves audio ~100ms past the video.* Container durations matched to 0.000s; the extracted
  WAV ran 16ms long. Keep `-shortest` in any post-step as cheap insurance, not as a fix for a known defect.

---

## 10. Where this engine stops and the Python pipeline starts

| Work | Tool |
| --- | --- |
| Invented or typographic motion, kinetic type, stat beats, numbered builds, title cards, brand stings | **HyperFrames** |
| Screen-recording a live demo app | `record_demo.py` (always `--warmup`) |
| Compositing real captured footage, Ken Burns over screenshots, deck narration | `assemble.py`, `narrate_deck.py`, `video-production` skill |
| Framing real app footage inside a branded motion stage | **Either** - HyperFrames can place a `<video>` clip and animate a punch-in on a non-timed wrapper around it (see `hyperframes-keyframes`). Decide per build; do not split one piece across both pipelines. |

HyperFrames is a **complement** to the Python pipeline, not a replacement. It wins on produced,
motion-first, typographic work, and it brings a real pre-render QA gate (runtime, layout, motion,
WCAG contrast) the Python path does not have.

What the engine genuinely cannot do: source speed ramps (no playback-rate envelope - preprocess a derived
asset), arbitrary mid-source freeze frames (preprocess a still), automatic waveform sync or drift
correction, speaker diarisation, and any animation driven by state that accumulates between frames.

---

## 11. Australian English and brand hygiene

US-neutral spelling is fine for a US or neutral piece; otherwise Australian English. No em dashes (spaced
hyphen only), no banned words (delve, leverage, unlock, seamless, game-changing), no corporate fluff - in
on-screen copy AND narration. Spell out "Progress Agentic RAG" in anything customer-facing; "ARAG" is
internal only. Progress branding via the `progress-arag-branding` skill: dark Progress-blue field, green
as an accent on dark only, the official logo lockup, and "Progress® Agentic RAG" on first prominent use.

Keep on-screen copy under about eight words, one idea per frame. Screen carries the message, voiceover
carries the context - do not read the on-screen text aloud, but DO voice the query and answer when that
is the payload.

---

## 12. Creative methodology (binding) - follow the Playbook

Sections 0-11 above are mechanics. **`PLAYBOOK.md` in this folder is the CREATIVE methodology, it is
binding on every HyperFrames build (GM directive, 4 Sep 2026), and it outranks the craft guidance here.**
Read it before authoring anything multi-beat. Its non-negotiables, in brief:

- **Warm start, never invent.** Ground the video in real source material. This is the no-fake
  authenticity gate (hard rule 3) applied to video.
- **Artifacts before build:** `DESIGN.md` (the visual system as observable rules), `STORYBOARD.md`
  (explicit beats), `narration.txt`. Do not bury creative decisions in composition HTML.
- **A motion system defined once**, not per-scene invention.
- **First 5s earns attention; every scene advances the story** (Problem, Shift, Product, Mechanism,
  Proof, Outcome, CTA).
- **Preserve real product UI** - frame, zoom and annotate real captures; never redraw the demo.
- **Reusable compositions and variables become templates**; variants are re-composed, not cropped.
- **Full first pass, then review like an editor** (pacing with and without audio); iterate surgically;
  fix `STORYBOARD.md` for narrative problems and `DESIGN.md` for systemic ones.
- **Avoid generic AI aesthetics** - no brains, neon, particles or fake dashboards.
- The source PROJECT is the asset; the MP4 is an output.

---

## Files in this skill

| Path | What it is |
| --- | --- |
| `PLAYBOOK.md` | The GM's binding creative doctrine. Do not edit. Outranks this file on craft. |
| `reference/verify_render.py` | The delivery gate. Run on every MP4. Has `--selftest`. |
| `reference/check_text_beat.py` | The only instrument here that READS TEXT off the delivered file. Use on any beat whose meaning is a change in wording. Two-arm `--selftest`; run it first. |
| `reference/motion-and-transitions.md` | Motion system, easing, transition doctrine, the motion sidecar, layout escape hatches. |
| `reference/cli-and-engine-map.md` | The 29 CLI commands, the engine's 20-skill library, `capture`, variables and batch, the registry. |
| `reference/example-composition.html` | The proven ARAG showcase - a monolithic five-scene piece. Predates the transition and font corrections above; read it for structure, not as a style reference. |
| `reference/gen_narration_example.py` | ElevenLabs per-segment narration generation. |
| `template/.npmrc`, `template/package.json` | The pinned install. |
| `template/starter/` | A proven-rendering two-scene scaffold: local fonts, variables, a correct simultaneous transition, narration wiring, and a motion sidecar. Rendered clean and passed all 14 gate checks. |

Start a new build by copying `template/starter/` and `template/package.json` + `.npmrc`, then dropping
`gsap.min.js` and your real brand fonts into `assets/`.
