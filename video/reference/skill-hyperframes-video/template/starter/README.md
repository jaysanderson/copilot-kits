# Starter composition

A two-scene scaffold that renders clean and passes the full delivery gate. Copy it, do not
rebuild from scratch.

Proven on 29 September 2026 against `hyperframes@0.8.15`: `check` exit 0 (lint 0/0, runtime
0/0, layout clean, motion 0/0, contrast 10/10), `render --quality high` exit 0, and
`verify_render.py` returned **14 passed, 0 failed**.

## What it demonstrates

- A standalone root, sized in pixels, opaque background, one paused timeline.
- **Local `@font-face`** so the rendered typeface is the one you asked for. Declaring
  `Arial` silently renders Inter - see SKILL.md section 3.
- Variables (`data-composition-variables` + `data-var-text` + `var(--accent)`), so the same
  file is a template.
- **A correct scene transition**: outgoing and incoming both move at the same timeline
  position `T`. Not a fade-out followed by a fade-in.
- A slow hold-drift on each scene so no shot freezes on a settled frame.
- Narration wiring: two `<audio>` elements, each with a unique `id`, on a high track index.
- A `*.motion.json` sidecar with a root-scoped `keepsMoving` assertion - the only automated
  check that catches dead air.

## Setting it up

```bash
mkdir -p videos/<name>/hf && cd videos/<name>/hf
cp <SKILL_DIR>/template/.npmrc <SKILL_DIR>/template/package.json .
export npm_config_registry="https://pkg.harness.io/pkg/ct8onj8YTdaXtKaFsYCRLg/org-marklogic-npm/npm/"
npm install                                   # needs dangerouslyDisableSandbox: true

mkdir -p app/assets
cp <SKILL_DIR>/template/starter/index.html app/
cp <SKILL_DIR>/template/starter/index.motion.json app/
cp node_modules/gsap/dist/gsap.min.js app/assets/
```

Then supply the three asset groups the composition expects:

| File | Where it comes from |
| --- | --- |
| `assets/BrandDisplay.woff2`, `assets/BrandText.woff2` | `hyperframes capture <account-url>` writes the real fonts to `assets/fonts/`. For Progress work that is genuine Progress Sans. If you have no real font file, delete the two `@font-face` blocks and accept Inter - and say so in the build report. |
| `assets/vo_s1.mp3`, `assets/vo_s2.mp3` | ElevenLabs, per scene. See `reference/gen_narration_example.py`. One voice per piece, never music. |
| Palette | Edit the `:root` custom properties, or pass `--variables`. `hyperframes capture` writes the account's real palette to `extracted/tokens.json`. |

## The loop

```bash
HF=./node_modules/.bin/hyperframes
export HYPERFRAMES_TELEMETRY=off

$HF check ./app > /tmp/check.log 2>&1; rc=$?   # never pipe to tail - it destroys the exit code
$HF keyframes ./app                            # what animates, when
$HF snapshot ./app --frames 6                  # then LOOK at snapshots/contact-sheet.jpg
$HF render ./app --quality high --output out.mp4 2>&1 | tee /tmp/render.log
.venv/bin/python <SKILL_DIR>/reference/verify_render.py out.mp4 \
    --expect-duration 12 --sections "0:6,6:12" --expect-audio --render-log /tmp/render.log
```

## Adapting the timing

Scene windows overlap by the transition length: scene 1 runs `0 -> 6.5`, scene 2 starts at
`6`, and the handoff fires at `T = 6.0`. If you retime, keep three things aligned - the two
`data-start`/`data-duration` pairs, the `T` constant in the script, and the `bySec` values in
`index.motion.json` - or the sidecar will report the mismatch, which is the point of it.

Root `data-duration` is the render length and is **read once at compile time**; a script
cannot change it.
