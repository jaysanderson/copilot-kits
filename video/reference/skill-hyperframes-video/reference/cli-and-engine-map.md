# The CLI surface and the engine's own skill library

Two things the factory owned and never opened: 29 CLI commands (we had used two), and a
20-skill authoring library shipped with the engine clone. This file maps both.

Everything below was run against the real install (`hyperframes@0.8.15`,
`videos/tourism-experience/hf/`) on 29 September 2026 unless marked UNTESTED.

---

## 1. The commands that matter

Run as `./node_modules/.bin/hyperframes <cmd>` from the build directory. Always
`export HYPERFRAMES_TELEMETRY=off` first.

### The authoring loop - use all five, every build

| Command | What it is for | Verified behaviour |
| --- | --- | --- |
| `lint` | Fast static pass while writing. Run after the first HTML pass. | Catches `media_missing_id`, `subcomposition_root_styled_by_class`, `gsap_css_transform_conflict`, `media_crossorigin_breaks_preview`. |
| `check` | The real gate. Runs lint, then one Chrome session sweeping lint + runtime + layout + motion + WCAG contrast. | Exits 1 on error, 0 on clean. Catches an unreachable GSAP as three separate findings (`request_failed`, `page_error`, `sweep_static`). |
| `keyframes <dir>` | Prints the whole motion map - every animated selector, its window, its from/to values. | The cheapest way to answer "does this section actually animate, and when". Add `--json`, `--shot out.png` (onion-skin trajectory overlay), `--layout strip`, `--ghost` (canvas/WebGL). |
| `snapshot --frames N` | Writes N stills plus `snapshots/contact-sheet.jpg`, explicitly labelled "grid view for AI review". | One image showing the whole piece. Look at it before rendering. `--zoom "#sel"` crops one element at 3x density across the sampled times. |
| `render` | The encode. | **Exits 0 on a completely frozen video.** Never treat a successful render as proof of anything. |

### Commands worth reaching for

| Command | Use |
| --- | --- |
| `capture <url>` | **Field Rule 8's brand capture, done properly.** See section 3. |
| `catalog --query "<the beat in plain English>"` | Search 386 registry moves before hand-authoring motion. Query in English always. |
| `add <name>` | Install a registry block or component. Needs network per install (manifests cache, files do not). |
| `compositions <dir>` | Lists every composition, its duration, size and source file. Fast structural sanity check on a modular project. |
| `info <dir>` | Resolution, duration, element and track counts, project size. |
| `normalize-audio --reference <id> --target <id> [--write]` | Matches one audio element's loudness to another by integrated LUFS. Use it to level multi-segment ElevenLabs narration instead of guessing `data-volume`. |
| `media-treatment --capabilities` | Deterministic looks on `img`/`video` - correction, grading, presets, finishing (vignette, film grain). This is the colour-grade pass the UI polish standard asks for. |
| `grade-compare --for frame.png --grades grades.json` | Renders candidate grades onto one reference frame as a labelled sheet. Choosing a look, not applying one. |
| `compare <a> <b> ... --at <s> --labels a,b` | Same timestamp from several project dirs into one labelled contact sheet. Good for before/after on a revision. |
| `render --batch rows.json --output "renders/{name}.mp4"` | Variant renders from one composition. See section 4. |
| `doctor --json` | Environment check. Always exits 0 - gate on the payload: `doctor --json \| jq -e '.ok'`. |
| `docs <topic>` | Inline docs: `data-attributes`, `examples`, `rendering`, `gsap`, `troubleshooting`, `compositions`. Thin; this skill and the engine skill library are better. |

### Commands the factory should not use

| Command | Why not |
| --- | --- |
| `tts` | Local Kokoro-82M model. The factory's narration is **ElevenLabs**, always. Do not substitute. |
| `beats` | Detects beats in a music track. **The factory never adds music.** No use case. |
| `validate`, `inspect`, `layout` | Deprecated aliases for `check`. |
| `events` | Telemetry endpoint. Exits 0 whatever you pass. |
| `publish` | Uploads the project to a public URL. Outbound - hard rule 10. Do not run. |
| `feedback --file-issue` | Publishes a repro publicly. Do not run. Plain `feedback --rating` is anonymous and harmless but optional. |
| `cloud`, `lambda`, `cloudrun` | Hosted/AWS/GCP rendering. Local render works and is ~6s for 3s of 1080p. No reason. |

### A gating trap, measured

`hyperframes check` exits **1** on failure - but piping it to `tail`/`grep` replaces the
exit code with the pipe's. Measured: `check ... 2>&1 | tail -1; echo $?` printed `0` on a
composition that genuinely failed. Redirect to a file and check the code, or read
`${PIPESTATUS[0]}`:

```bash
$HF check ./app > /tmp/check.log 2>&1; rc=$?
sed -n '/^Lint/,$p' /tmp/check.log
[ $rc -eq 0 ] || { echo "check FAILED"; exit 1; }
```

---

## 2. The engine's own skill library

Cloned at `reference-repos/reference-repos/hyperframes/skills/`. Twenty skills, ~900
files. Read the specific file, not the whole folder.

| Skill | Open it for |
| --- | --- |
| `hyperframes-core/` | The composition contract. `references/data-attributes.md` is the full attribute table; `references/determinism-rules.md` the bans; `references/sub-compositions.md` the three mount pitfalls; `references/composition-patterns.md` monolithic vs modular and the four sub-comp archetypes; `references/tracks-and-clips.md` relative timing. |
| `hyperframes-animation/` | **The biggest unused asset.** `rules-index.md` lists ~45 atomic motion recipes by trigger and tag (kinetic-beat-slam, stat-bars-and-fills, gradient-text-sweep, waterfall-entry, spring-pop-entrance, chart-scrub-readout, depth-of-field-blur, multi-phase-camera, svg-path-draw ...). `blueprints-index.md` lists 18 multi-phase scene templates. `transitions/overview.md` + `catalog.md` are the scene-transition doctrine. `adapters/gsap-easing-and-stagger.md` holds the easing vocabulary and a seek-safe closed-form spring ease. |
| `hyperframes-keyframes/` | Punch-ins, reframes, Ken Burns, camera moves on real footage; the creator-edit boundary table (what is a keyframe vs what is a clip edit); the CLI proof ladder. |
| `hyperframes-audio/` | `data-fx-chain` / `data-automation` JSON shapes - EQ, compressor, limiter, gate on a narration track. Most of the skill is music-bed carving, which the factory never needs. |
| `hyperframes-cli/` | Per-command contracts. `references/lint-validate-inspect.md` documents the `*.motion.json` sidecar. |
| `hyperframes-registry/` | `catalog` / `add`, block vs component, wiring. |
| `hyperframes-creative/` | Palettes, typography, beat planning, narration pacing, story spine. `references/house-style.md` and `references/video-composition.md` are the two it says to read first - they are the "stop building web pages" corrective. |
| `media-use/` | Sourcing, grading, LUTs, transcription, background removal. Grading is the relevant part; sourcing is not (our assets are real or captured). |
| `embedded-captions/` | Captions are OFF by default here (GM directive, 4 Sep 2026). `references/anti-patterns.md` is still worth reading for typographic craft. |
| `remotion-to-hyperframes/references/limitations.md` | The clearest statement of what the engine genuinely cannot do. |
| `product-launch-video/`, `faceless-explainer/`, `motion-graphics/`, `slideshow/`, `general-video/`, `pr-to-video/`, `figma/`, `music-to-video/`, `talking-head-recut/` | Workflow skills. `music-to-video` is dead to us (no music). |

These are also registered as Claude skills in this environment (`hyperframes-core`,
`hyperframes-animation`, and so on) - invoking one loads it properly. Prefer that over
reading raw files when you need a whole skill.

---

## 3. `capture` - the brand-capture tool Field Rule 8 has been asking for

Field Rule 8 requires a named account's demo and video to use "their actual logo/wordmark,
their real fonts, their EXACT palette (colour-picked from the live site, never guessed),
and their real imagery". `hyperframes capture` does exactly that in one command.

```bash
./node_modules/.bin/hyperframes capture https://www.example.com/page \
  --output ./capture/<account> --skip-vision --timeout 60000 --json
```

Verified against `https://www.progress.com/agentic-rag` (about two minutes; run it in the
background). It writes:

| Path | Contents |
| --- | --- |
| `extracted/tokens.json` | The real palette, sampled from the live DOM (17 hex values on the Progress page), plus `cssVariables`, `headings`, `ctas`, `svgs`, `sections`, `colorStats`. |
| `extracted/design-styles.json` | A computed design system: typography roles with exact size/weight/line-height/colour, spacing scale, radius, shadows, buttons, cards, nav, chips, backgrounds. |
| `extracted/fonts-manifest.json` | The real families, identified by fontkit. |
| `assets/fonts/*.woff2` | **The actual font files.** |
| `assets/*.svg`, `*.png`, `*.webp` | The real logo and imagery. |
| `screenshots/contact-sheet-*.jpg` | The whole page as labelled grids. |
| `AGENTS.md` | A written summary of the capture, including a brand summary line. |

On the Progress page it recovered `Progress Sans Display VF` and `Progress Sans Text VF`
as real `.woff2` files. Combined with the local-`@font-face` path in SKILL.md section 3,
that means factory videos can render **genuine Progress Sans** rather than the Arial
substitute. Proven end to end.

Notes: `--max-screenshots 4` did not reduce the scroll captures (14 were written); treat
the flag as advisory. A `lazy-scroll evaluate timed out` warning is normal and non-fatal.

---

## 4. Variables and batch renders

Declare the schema on `<html>` as an **array**; pass values as an **object**.

```html
<html data-composition-variables='[
  {"id":"headline","type":"string","label":"Headline","default":"Default"},
  {"id":"accent","type":"color","label":"Accent","default":"#5ce07a"}
]'>
```

Bind declaratively - no script needed:

- `data-var-text="headline"` substitutes the element's own text, preserving child nodes.
- `data-var-src="heroImage"` substitutes `src`; the authored `src` stays as the fallback.
- Every scalar is exposed as a CSS custom property on the root, so `var(--accent)` just works.
- `window.__hyperframes.getVariables()` for anything needing logic.

Override per render (`--variables '{"headline":"..."}'`), per sub-comp instance
(`data-variable-values='{...}'` on the host), or per batch row.

```bash
$HF render ./app --batch rows.json --output "renders/{name}.mp4" --strict-variables
```

**Measured gotcha, undocumented upstream:** the key used in the `--output` template
(`{name}`) is validated as a composition variable under `--strict-variables`, so a
`rows.json` whose `name` exists only as a filename aborts the whole batch with
`Variable "name" is not declared in data-composition-variables`. Two fixes, both verified:
declare `name` in `data-composition-variables`, or drop `--strict-variables`. Declaring it
is better - keep the strict check.

A batch writes `manifest.json` beside the outputs recording each row's variables, status,
output path and timing.

---

## 5. The registry - 386 ready-made moves

Reachable and installable from this environment (verified: `catalog` listed 386 items,
`add line-swap` fetched and wrote the file). This is the fastest route to the
"produced, not captured" bar, and to the reusable-template library PLAYBOOK sections 10-12
ask for.

```bash
$HF catalog --query "reveal a headline one line at a time"   # search by intent, in English
$HF catalog --type block --json                              # browse
$HF add line-swap --dir ./app --no-clipboard                 # install
```

Items arrive as fully parameterised sub-compositions with their own declared variables.
Mount one and pass your own copy - verified working, and it renders professionally-crafted
kinetic typography for about ten lines of host HTML:

```html
<div id="el-swap" data-composition-id="line-swap"
     data-composition-src="compositions/components/line-swap.html"
     data-start="0" data-duration="4" data-track-index="1"
     data-width="1920" data-height="1080"
     data-variable-values='{"line_a":"Every vendor promised you AI.",
                            "line_b":"Almost nobody promised you provenance.",
                            "swap_at":1.6,"underline_word":"provenance","accent":"green"}'></div>
```

Two things to know. A registry item paints **its own stage** - the `line-swap` block
rendered on black and overrode the host background, so either accept its look or restyle
its root. And a masked item legitimately overflows its clipping container, so `check`
reports `container_overflow` warnings that are correct behaviour; mark them with
`data-layout-allow-overflow` on the narrowest wrapper rather than fighting them.

Search is local and sends nothing. `--on-device` semantic ranking needs a consented 33 MB
download - offer it, never enable it silently. `add` needs the network every time.
