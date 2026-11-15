---
name: video-production
description: Produce a demo-walkthrough or deck-narration video - narrative arc first, then Playwright recording with the mandatory --warmup flag, ElevenLabs TTS, ffmpeg assembly with brand cards, Ken Burns motion, crossfades and EBU R128 loudness. TWO ABSOLUTE AUDIO RULES - captions/subtitles OFF by default (opt-in only when Jay explicitly asks) and MUSIC NEVER ADDED TO ANY VIDEO (GM directive 2 Sep 2026: every video ships music-free and the GM scores it himself; a brief's own "add music" line-item is NOT authority, and neither is a lead dispatch instruction - flag the conflict back instead; re-violated on Experience-co 11 Sep 2026 at two revision cycles' cost). Use for "make a video / narrate the deck". Encodes the warmup white-screen fix, the deck-to-narrated-video path, the measured ElevenLabs v3 API limits, and the no-stock-footage rule.
---

# Video production (Workflow 3)

**Input:** demo URL + topic, or a deck to narrate.

Everything in "The baseline" is the standard process, not an optional extra. A
video that skips it is not finished.

---

## 0. Video excellence bar (bleed the demo bar in) (binding)

Videos clear the same `arag-demo-app` B8 visual-excellence bar as the demos (GM
directive, 17 Aug 2026: "bleed the demo work into the videos"). Binding on every video.
(lesson: content/sop/lessons/video-gates-and-currency.md#bleed-the-demo-bar-into-the-videos-gm-directive-17-aug-2026)

1. **Single consistent narrator by default.** A brand, overview or walkthrough piece uses
   ONE narrator voice throughout by default - not pool-voice rotation. A polished single
   piece with the voice changing between segments reads as stitched-together, not
   produced. Pass `--voice <name>` to pin it. Rotation (`pool[i % 5]`, the multi-segment
   default described under "Deck-to-narrated-video") stays available and is the right call
   only when a brief explicitly wants multi-segment variety - it is no longer the default
   for a single polished piece.

2. **NEVER add music to any video - full stop (binding, GM directive 2 Sep 2026,
   supersedes all earlier music guidance).** No music bed on ANY video, ever, whatever a
   brief line-item says: "a real
   human being needs to listen to the right track and add it." Ship music-free (voiceover +
   diegetic/source audio only); the GM scores it himself. Never run `scripts/music_bed.py`
   in a delivery. QA the music-free state with the numpy PCM gap check
   (`videos/tourism-provocation/gate.py` pattern: at least 8 gaps of 0.4s or more at 20ms
   resolution) - `silencedetect` logs at ffmpeg's info level, so `-v error` swallows it and
   returns a false zero; if used, run at `-v info`, read stderr, pass `-nostdin`, and prove
   the check fails on a planted bed. Then LISTEN: digital-zero pauses mid-clause read as
   stitched - lay room tone, stagger audio gaps ~0.3s off picture cuts, trim dead head and
   tail. (lesson: content/sop/lessons/voices-and-audio.md#music-free-gate-traps-experience-co-and-cinema-group-29-sep-2026)

3. **On-brand throughout.** A Progress Agentic RAG branded **title card and end card**,
   the Progress brand palette and Progress Sans type (Display for headlines, Text for body
   and captions - see the brand-cards mechanism in section 3), and tasteful lower-thirds.
   Apply the `progress-arag-branding` skill, same as a demo. Nothing off-brand or
   template-default ships.

4. **The recorded demo must itself meet the demo bar.** For any demo-walkthrough video,
   the app on screen must show the **Progress Agentic RAG header** and be sharp and on-brand
   to the same standard as the `arag-demo-app` visual-excellence bar (**B8** / the
   "Courthouse Bid" reference in `shots/reference-standard/`). **A video is only as good as
   the demo it records.** If the demo on screen is not at the bar - flat, monotone,
   off-brand, missing the header, raw-text detail views - **uplift the demo first, then
   record.** Do not record a sub-bar demo and try to rescue it in the edit.

5. **Keep the narrative-arc discipline, and lead with the content.** The hook / problem /
   capability / proof / CTA arc in section 1 is reinforced, not replaced - a beautiful
   video that is still a route tour fails. Add the **content-as-hero** principle where it
   applies (B8 principle 2): the real retrieved data, documents and answers are the hero
   visual - push in on the corpus and the proof, not on chrome. The most striking real
   moment in the product carries the piece.

6. **VOICE the actual query and answer when they ARE the payload (GM directive, 4 Sep 2026,
   Curb trailer)** - the narrator speaks them out loud, and only what the live product
   actually returns (hard rule 3 / B47). (lesson: content/sop/lessons/voices-and-audio.md#voice-the-actual-query-and-answer-when-they-are-the-payload-gm-4-sep-2026)

---

## 0-gate. ONE shared gate, review before render, contact-sheet viewing (binding, 2 Oct 2026, GM golden rule: most value per token)

1. **The gate is one command, not a per-film script set.** Every film is gated with
   `.venv/bin/python scripts/video_gate.py <master.mp4> --design DESIGN.md --segments
   timeline.json [--reference-strings ref.txt] [--social] --out report.json` from the
   factory root. It runs identity and currency, loudness and music-free, freeze and
   per-shot motion ranking, flat-grey artefacts, OCR forbidden strings, swept-band crop
   edges, reference echo and bare-stage typography, with a positive and a negative control
   on every check, every figure stamped with the md5 and duration it was measured on, exit
   0 only on all-PASS, and HOLE (never PASS) for anything it could not measure. Declare
   the floors and the must-not-appear list in DESIGN.md and the crop windows in
   timeline.json so nothing reports HOLE for want of an input. Do not write a new
   gate.py, sweep.py, measure.py or motion_rank.py for a film; if the shared gate lacks a
   check your film needs, add it to `scripts/video_gate.py` with its controls and say so
   in the report. Film-specific manifests (capture intervals, i18n corpora) stay per-film.
   Read `scripts/video_gate_README.md` for the blind classes each check declares.
2. **Review before render.** Render the low-quality preview first; the builder, the
   fresh-eyes viewer and the lead read THAT (contact sheet plus transcript, see 3) and the
   master is rendered once, after the read. A master re-rendered to fix something visible
   at preview resolution is the expensive habit this rule removes.
3. **Fresh-eyes viewing is on contact sheets.** The viewer gets 1 frame per second
   assembled into sheets (12 frames per 30 seconds of runtime is the floor for a verdict)
   plus the transcript and the brief's words, not hundreds of individual frames. Native
   resolution crops are pulled only for a frame the sheet flagged.
4. **The lead reads the report, re-runs one claim per class.** A builder's evidence note
   with md5-stamped figures from video_gate.py is trusted after one spot-check per check
   class; the lead does not re-run the suite.

## 0c. Film type is decided at the brief, and a concept film is ILLUSTRATED, not typeset (binding, GM directive 4 Oct 2026)

GM, 4 Oct 2026: when a film is asked for on a topic and "there's not a demo site to use, I
want these to be more than just words with diagrams, animations, that kind of thing." The
RAG explainer he rejected on 30 Sep ("text on a background for the whole time") cleared every
gate because no gate measured whether the IDEA was shown. These rules make it a build input.

1. **Classify the film before anything is built, and write it in DESIGN.md.** One of:
   - **Demo film** - a real product surface is the hero; produced treatment goes AROUND real
     footage (0b governs). Type and cards are interstitials only.
   - **Concept film** - no product surface carries the piece (a what-is, a category POV, an
     architecture or value story). **Animated illustration is the hero.** Each idea is
     PERFORMED by bespoke motion in the brand's own visual language while the voice says it;
     type carries labels and the odd statement, never the explanation. Real captures may
     appear as framed evidence where they genuinely show the point.
   - **Hybrid** - both, beat by beat; the storyboard says which each beat is.
   A film with no demo site that ships as a sequence of typeset statements FAILS by
   definition, whatever else it passes.
2. **Concept and hybrid beats carry an illustration plan before they are built.** In
   STORYBOARD.md every such beat has three fields: the THING on screen, the ACTION it
   performs, the RESULT the viewer sees while the line plays (e.g. "two hundred passage
   tiles / collapse toward the question / six remain, each lit" under "it finds the few
   passages that actually answer"). A beat with empty fields cannot be built. On-screen
   copy stays under ~8 words; the voice carries context.
3. **Compose from the motif library, extend it when a film needs a new idea.** Recurring
   ARAG ideas are HyperFrames sub-compositions with variables under
   `videos/_motifs/` (see the `hyperframes-video` skill, section 5a): the body of knowledge,
   retrieval narrowing many to few, the answer drawing threads back to its sources, the
   quality score forming per answer, one engine plugging into many doors, running where the
   data lives. A new motif is built once, gated once, and documented with when-to-use. Never
   reach for the banned generic look (glowing brains, node graphs, translucent cubes,
   particle swarms, blue circuitry) to fill an illustration slot.
4. **Measured, not judged.** `video_gate.py --storyboard STORYBOARD.json` reports the
   illustration-led share of runtime per shot from the storyboard's per-beat `kind`
   (`illustration` / `plate` / `type`), asserts the concept-film floor (illustration-led
   runtime >= 60% of the piece, every mechanism beat illustration-led) and the type-only cap
   (no type-only run over 3.0s), and cross-checks declared illustration shots against
   measured per-shot motion (an "illustration" shot in the stillest decile is a FAIL, not a
   label). No storyboard manifest = HOLE, never PASS.
5. **Two viewer questions, recorded separately.** The fresh-eyes viewer answers "did you
   understand what this is" AND "would you keep watching". Comprehension is not engagement;
   only the second predicts the GM's chair. A concept film ships on a yes to both.

## 0a. HyperFrames builds follow the Playbook (binding, GM directive 4 Sep 2026)

Any video built with HyperFrames (the produced/typographic path - trailers, explainers, launch
and motion pieces) follows the **`hyperframes-video` skill's `PLAYBOOK.md`** as its binding
creative methodology: warm-start from real source (never invent claims/UI - the no-fake gate
applied to video); author `DESIGN.md` + `STORYBOARD.md` (+ `narration.txt`) BEFORE building any
multi-beat piece; a defined motion system; concise on-screen copy (<~8 words) with the voiceover
carrying context (not reading the screen); real product UI framed not redrawn; reusable
compositions + variables built up into a template library; full first pass then editor-review
(pacing with and without audio) then SURGICAL localised edits (fix STORYBOARD.md for narrative
problems, DESIGN.md for systemic ones); no generic-AI aesthetics; validate + a low-quality review
render before the master; variants re-composed not cropped. The source PROJECT is the core asset.
Read `PLAYBOOK.md` in full before a HyperFrames build; §0-6 of the `hyperframes-video` skill are
the environment mechanics.

## 0b. Produced, not captured (binding, vibe-coded audit 2 Sep 2026)

The 2 Sep 2026 audit of the six most recent videos found all of them reading as raw
screen-capture assembly rather than produced film - against a bar (the arag-seller-short
class of piece, and the FRDC-era reference cuts) that composes every element. **The
produced-not-captured bar: a video whose demo footage is raw full-bleed capture pasted
edge-to-edge into the concat, book-ended by static cards, FAILS QA** - it reads as a
recording, not a piece. Four binding requirements:

1. **Frame UI footage as a composed device on a consistent brand stage** - a floating
   browser/device frame on ONE branded stage, never raw full-bleed capture; the in-footage
   cursor stays. **Mobile captures sit inside a phone device frame, always** (GM kickback,
   tourism film cut4, 1 Oct 2026: "can you put some kind of mobile device Chrome around the
   site when it's shown on the screen, just to emphasize more that it is a mobile
   device?") - a genuine bezel designed once in DESIGN.md, on every mobile plate. (lesson: content/sop/lessons/video-crops-and-motion.md#device-frames-on-a-brand-stage-phone-bezel-for-mobile-captures-gm-kickback-tourism-cut4-1-oct-2026)
   **Hard limit the other way** (GM rejection, 18 Sep 2026: "I want videos of the actual
   demos only. At the same standard as almanac-co, but it's own uniqueness"): produced
   treatment goes AROUND real app footage, never instead of it; uniqueness is audited at the
   level of individual devices. (lesson: content/sop/lessons/video-gates-and-currency.md#produced-treatment-goes-around-real-footage-and-uniqueness-is-device-level-gm-18-sep-2026) Any piece built to a named reference runs a
   machine-captured, self-tested reference-echo diff before rendering. (lesson: content/sop/lessons/video-gates-and-currency.md#reference-echo-and-copy-echo-diffs-are-machine-run-and-self-tested-overbuilt-18-sep-2026) Never clinical:
   cast the voice for the register (Hope is the explainer default, not the trailer default),
   check narration wpm (trailer roughly 100-140), derive beat durations from measured takes.
   (lesson: content/sop/lessons/voices-and-audio.md#never-clinical-cast-the-voice-and-measure-the-pace-iwtv-kickback-18-sep-2026) A line that promises an action must show it; an "every" claim shows the whole set;
   frame the column that carries the claim. (lesson: content/sop/lessons/video-gates-and-currency.md#a-line-that-promises-an-action-must-show-it-and-every-needs-the-whole-set-29-sep-2026) **The image performs the line**: when the
   voice reads a thing it fills the frame, the spoken phrase emphasised as spoken.
   Engagement floors, checked like loudness: camera moves counted, frozen frames < ~25% of
   runtime, longest silent-static < ~2.5s, evidence legible at phone width, narration gaps
   < ~1.5s except deliberate holds. Punch traps (empty highlight boxes, non-unique targets,
   host-block crops, glyph-height gates passing clipped lines, cross-take continuity, the
   capture cursor, live footage supplying no motion): (lesson: content/sop/lessons/video-crops-and-motion.md#the-image-performs-the-line-and-the-punch-building-traps-molyneux-erp-reel-vr-clinic-sep-2026) A retired app term purges the
   video's copy - run the PURGED map (`videos/overbuilt-showcase/reference_echo.py`). (lesson: content/sop/lessons/video-gates-and-currency.md#vocabulary-drift-a-retired-app-term-binds-the-videos-copy-overbuilt-18-sep-2026)
   **FIRST DRAFT GOES TO THE REVIEW QUEUE - BINDING, GM, 17 OCT 2026, SUPERSEDING THE INTERNAL
   ITERATION LOOP FOR VIDEO.** Verbatim: "Just fast track the deliverable call it a draft put in
   review queue. If not good enough I will say so. Do that with all video creation from now on. I
   expect your skill has much to enable the first draft to be almost spot on."
   So: ONE internal pass, then submit as a draft with its known weaknesses written into the note.
   The GM is the taste gate. **What moves to him is TASTE; what stays with us is SAFETY**, and the
   distinction is not negotiable - still run and still report, every time, before submission: the
   leak and forbidden-string sweep with its controls, the no-fake and claim check, a citation-target
   enumeration before any beat is built on a citation, container metadata, and the audio spec. Those
   stop us shipping something false or something naming a customer; none of them is a matter of
   taste. A draft whose note says "the narration lags the picture by five seconds in the library
   beat" is worth more to him than a fourth cut that fixed it.
   **AND THE REASON HE SAID IT: the research-portal walkthrough took SEVEN gate rounds, and the
   first cut had no product motion, no function seen working, and a diagram standing in for the
   library.** That is a first-draft failure, not a gating failure - the gates were doing work the
   build should have done. So the things that round seven arrived at are the STARTING POINT of the
   next film, never its findings: drive the interaction and capture per step rather than
   screenshotting end states, check where a citation marker RESOLVES before building a beat on it,
   compose the frame rather than crop the live page, and never let a beat that shows a product
   function be a static end state. A walkthrough IS the transitions, and a transition cannot be
   composited from stills.
   **FRESH-EYES VIEWER GATE** (was mandatory pre-submission for GM-facing films; now used where the
   lead judges the risk warrants it, and always for a film carrying a claim nobody in the chain can
   verify): a zero-build-context agent watches the film as a VIEWER (file, brief/kickback words,
   dense frames + transcript only) and delivers a timecoded diagnosis.
   **THE VIEWER'S REPORT LEADS WITH THE md5 AND DURATION OF THE FILE IT WATCHED, AND THE
   HANDBACK GOES TO THE AGENT THAT CONSUMES IT (9 Oct 2026, both errors in one exchange).**
   A viewer delivered eighteen real defects and named no content identity, so its verdict
   could not be shown to be about the build the builder had just measured - the currency
   rule applies to an eye-read exactly as it does to a machine row, and the DISPATCHER is
   the one who must require it in the brief. Separately, that report handed back to the
   LEAD, which spawned it, and not to the builder waiting on it; the builder then read its
   own measurement of the viewer's token spend as evidence the gate could not run, and was
   about to commission two more viewers to re-review a film already reviewed. **Token spend
   is not an outcome.** Either spawn the viewer from the agent that needs the answer, or
   relay the report the moment it lands and say so - and never read an agent's cost as a
   verdict on whether its output exists.
   **NEVER DECLARE A SUSPECTED WEAK POINT TO THE VIEWER - SEND IT TO THE LEAD SEALED
   (9 Oct 2026).** A builder proposed putting "B1b runs at 3.55x and I expect it to read as
   sluggish" into the viewer package, with a caveat asking the viewer to answer honestly even
   if it suspected that was the wanted answer. **The caveat makes it worse: it names the
   suspicion out loud, and it cannot be un-named.** A viewer told where the weak point is
   either confirms it or over-corrects away from it, and afterwards you cannot tell which -
   so the timecode answer, which is the single most actionable thing the gate produces, is
   destroyed. The instinct to write the prediction down BEFORE the observation is right and
   its home is the LEAD: held unseen by the viewer and compared afterwards, it is a
   pre-registered test rather than priming. Independent agreement is then strong evidence;
   disagreement teaches you the proxy does not predict what you thought. The package carries
   the film, the transcript, the questions, and nothing that steers - including any
   "deliberately absent" note that names something a viewer could otherwise notice.
   **And convert the prediction into a measurement before acting on it:** a timeline STRETCH
   ratio is a proxy for "perceptually still", not an observation of it. Rank the shots by
   median frame difference and read the top; rebuild on the measurement, never on the ratio. **Playwright CANNOT record
   video at 2x** - record at 1x and take punch material from dsf=2 SCREENSHOTS.
   **A CONTACT SHEET CANNOT JUDGE PACING - IT HAS NO SOUND (lead error, OPAX, 5 Oct 2026).**
   The lead read eight seconds of a near-empty waiting screen off the sheets, called it dead
   air, and ordered it compressed - twice. The stretch was in fact narrated end to end,
   including a line that told the viewer the wait IS the product reading the record, which
   converts a pause into evidence. Measured after the fact: mean -17.6 dBFS over the window
   against a true-silence control at -80.3, longest internal gap 1.14s. Stills answer "what
   is on screen"; they cannot answer "what is the room experiencing", and a held frame with
   voice over it is a different artifact from the same frame in silence. Before any pacing
   verdict - yours or a reviewer's - either watch it with sound or MEASURE the audio across
   the exact window you are about to criticise (`volumedetect` plus `silencedetect` over the
   window, with a known-silent control in the same run). State which you did. A pacing
   complaint raised off silent stills is not a finding.

2. **A kinetic-typography beat SEQUENCE carries the film - not one static bookend card.**
   Statement/kicker text beats (word-by-word entrance, ease, an underline or accent
   swipe) alternate with and frame the footage. `assemble.py`'s `make_card()` (one static
   centred headline held for a fixed duration) is a bookend primitive only; a film whose
   only designed elements are its title and CTA cards fails this bar.
3. **A colour-grade/tint pass ties the card-world to the captured footage.** Derive the
   card/stage palette from the app being shown (or grade the footage gently toward the
   brand palette) so cards, stage and footage read as ONE world. The audit's named
   failure: navy/gold cards over a blue/orange app plus a third unrelated treatment in
   the same piece - continuity in the estate is currently accidental, make it designed.
4. **Progressive/numbered build-ins for step reveals.** A sequence of steps ("three
   things happen next...") builds in progressively on the beat, item by item - not a
   pre-rendered full list held static.

**Do not build these from scratch** - `scripts/build_effects_showreel.py` already
implements `kinetic_title()`, `framed_shot()`, `grade_seg()` and `lowerthird_seg()`; the
lift is generalising them into the shared `assemble.py` path. (lesson: content/sop/lessons/video-crops-and-motion.md#showreel-primitives-to-generalise-not-rebuild-aug-2026)

QA check for this section: extract three frames - one mid-footage, one mid-text-beat, one
at a punch - and confirm the footage sits in a device frame on the stage, the text beat is
a designed composition (not `make_card()` output), and all three share one palette world.

**A light app plate on a dark stage reads as full-bleed even when it isn't** - verify
plate geometry by sampling the actual edge pixels, and say which method you used. (lesson: content/sop/lessons/imagery-and-captures.md#a-light-plate-on-a-dark-stage-reads-as-full-bleed-check-the-pixel-edge-erp-keynote-19-sep-2026)

**The compliance scan covers the app UI rendered in-frame** - read the rendered strings at
every beat showing app text for em dashes, banned words and audience-wrong English; fix the
app and redeploy BEFORE recording. (lesson: content/sop/lessons/video-gates-and-currency.md#the-compliance-scan-covers-app-ui-rendered-in-frame-bioeconomy-3-sep-2026)

---

## 1. Structure before mechanics - the narrative arc (binding)

**Banned: the route tour.** Never walk the navigation in order with equal beats - a
sitemap read aloud is not a story. (lesson: content/sop/lessons/video-gates-and-currency.md#banned-the-route-tour-aug-2026-audit)

**Required arc:**

| Beat | Length | Job |
|---|---|---|
| **Hook** | 0-5s | Open on the single most surprising thing in the piece. No throat-clearing, no hedges, no title card first. |
| **Problem** | ~20s | The failure mode the audience recognises. |
| **Capability** | ~60s | How it actually works. Tightened, not exhaustive. |
| **Proof beat(s)** | 60-90s | The differentiated moments, pushed in and held (see hero-beat treatment). |
| **CTA** | ~20s | Specific. Not "contact us for a demo or more information." |

**Find the hook in the script you already wrote** - lead with the sharpest line, not the
most defensive one. (lesson: content/sop/lessons/video-gates-and-currency.md#find-the-hook-in-the-script-you-already-wrote-revolution-aug-2026)

**Hero-beat treatment.** Citation, REMi, knowledge-graph and refusal moments are the
differentiated proof - push in and hold, dim/blur the surrounds and punch out the panel,
slow the narration into it. An agent **refusing to answer** is usually the strongest moment
available - treat it as the climax, not a footnote. (lesson: content/sop/lessons/video-crops-and-motion.md#hero-beat-treatment-the-refusal-is-the-climax-aug-2026)

**Two-cut rule (binding).** Every video ships as two cuts from the same footage:
1. The full walkthrough (doubles as the sales-engineer script).
2. A **60-90s social cut** - hook, one proof beat, CTA.

The long cut is the wrong artifact for a feed. **Neither cut is captioned by
default** - see the captions rule below.

**No stock B-roll. No AI-generated imagery.** Every frame is real, reproducible product
footage. Narrow exception: abstract non-representational texture generated with
ffmpeg/Pillow. Anything beyond is a Progress brand and legal decision - route via Progress
Brand Bank / MyProgress. (lesson: content/sop/lessons/imagery-and-captures.md#no-stock-b-roll-and-no-ai-imagery-scope-and-routing-aug-2026)

---

## 2. The baseline pipeline

### Deck-to-narrated-video

Render frames first: `pdftoppm -jpeg -r 150 <deck>.pdf videos/slides/s` (crisper
than reusing QA jpgs). Then:

```bash
.venv/bin/python scripts/narrate_deck.py \
  --deck decks/<deck>.pptx \
  --slides "videos/slides/s-%d.jpg" \
  --out videos/<account>-<label>-<date>.mp4 \
  --captions
```

Speaker notes are the talk track and the single source of truth, so the video
can never drift from the deck. Defaults now applied automatically:

- **Voice-pool rotation** - `voices.json` has mandated rotating `pool[i % 5]`
  across multi-segment narration since 2026-07-06; it is now the default rather
  than opt-in. Pass `--voice <name>` to force a single voice.

- **Ken Burns** (`--motion alternate`) - slides alternate push-in/pull-out. **All
  zoompan/Ken Burns motion goes through `scripts/motion.py`, never a hand-rolled zoompan
  (binding, GM feedback 1 Sep 2026)**: oversample 3x + lanczos, smoothstep ease,
  `amount_for_duration()`, `pick_motion()`, x264 preset medium at crf 18. **A
  subset/`--only` render must never overwrite the master output.** (lesson: content/sop/lessons/video-crops-and-motion.md#ken-burns-goes-through-motionpy-measured-judder-fix-gm-feedback-1-sep-2026)

- **Captions** (`--captions`) - see below.
- **Two-pass loudnorm** to -14 LUFS, stereo 48k.

`--reuse` re-renders video from cached mp3s and alignments with no API calls -
use it for every iteration after the first.

### Demo walkthrough

```bash
.venv/bin/python scripts/record_demo.py --url <url> --steps <steps.json> \
  --out videos/demo.mp4 --warmup
.venv/bin/python scripts/voiceover.py --file script.txt --voice jay --out videos/vo.mp3
.venv/bin/python scripts/assemble.py --demo videos/demo.mp4 --voice videos/vo.mp3 \
  --brand <kit> --title "..." --cta "..." --out videos/<name>.mp4
```

**Always pass `--warmup`.** A fresh headless Chromium's first navigation of a
JS-heavy app sits on a blank white canvas for several real seconds before first
paint - Playwright's `load` event fires well before pixels render, so that blank
stretch gets recorded verbatim and ships as a white-screen defect. `--warmup`
does a throwaway unrecorded navigation first in the same context.

**NEVER record two clips in parallel - `record_demo.py` uses a SHARED `_rec_raw` dir and
the outputs cross-contaminate silently.** **Record clips SERIALLY**, `rm -rf <dir>/_rec_raw`
between runs, and verify each clip's CONTENT with frame-accurate seeking
(`ffmpeg -i clip -ss T`) before re-timing. (lesson: content/sop/lessons/imagery-and-captures.md#never-record-two-clips-in-parallel-shared-recraw-cross-contaminates-vr-root-cause-2-sep-2026)

**`scroll` is ABSOLUTE, not relative** - `y` is a destination. **Write scroll values as a
strictly increasing sequence of destinations**; a `goto` resets scroll to 0; verify with a
mean inter-frame delta over the clip. (lesson: content/sop/lessons/video-crops-and-motion.md#scroll-is-absolute-not-relative-sitefinity-8-aug-2026)

**Check what a deep scroll actually puts on screen** before choosing the maximum destination
(hard rule 8) - prove a hidden element is never painted via rendered size and computed
style, not `inner_text`. (lesson: content/sop/lessons/imagery-and-captures.md#check-what-a-deep-scroll-puts-on-screen-sitefinity-aug-2026)

**Type queries with `"delay"`, not `fill()`.** `record_demo.py`'s `type` action
sets the value in one frame unless the step carries `"delay": 55`, which types on
camera instead. A search demo's most persuasive second is watching the question
get asked; a query that teleports into the box reads as a mock-up.

**Audio tags are interpreted, not spoken - but verify it per build**: check the audio
shows a real silence gap at the tag, not an alignment-window RMS. (lesson: content/sop/lessons/voices-and-audio.md#audio-tags-are-interpreted-not-spoken-pug-tube-aug-2026)

**Probe candidate hero queries against the live API before recording** - seconds per
query, not a minute per take. (lesson: content/sop/lessons/imagery-and-captures.md#probe-candidate-hero-queries-against-the-live-api-pug-tube-aug-2026)

**Cursor is on by default** (`record_demo.py:CURSOR_JS`). Playwright's recorder
draws no pointer at all, so walkthroughs used to show UI reacting with nothing
visibly driving it. There is nothing in the footage to track afterwards - the
cursor must be real DOM injected via `context.add_init_script` so it renders
into the capture. `run_step`'s click also glides the mouse with `steps=20` so
the pointer travels on camera, then a ripple fires. Disable with `--no-cursor`.

---

## 3. Mechanisms worth knowing (so this doc does not rot)

### Captions - OFF by default, opt-in only

**NEVER put subtitles/captions on a video unless Jay explicitly asks for them
(binding, GM directive 4 Sep 2026).** Captions are OFF by default on every cut,
walkthrough and social alike; the `--captions` flag and everything in this
section are used ONLY when the brief or Jay explicitly requests captions. This
supersedes the old captions-on-by-default assumption (the "captioned social cut"
line, now removed). It also resolves the 1 Sep 2026 Cinema-group kickback
below: its `decision_note: "no subtitles"` was misread as a placement bug when it
literally meant remove them. The safe-zone/legibility rules below apply only
*when captions have been explicitly requested*.

### Captions mechanics (when explicitly requested) - Pillow, never drawtext

`scripts/captions.py`. **This machine's ffmpeg has no `drawtext`, `subtitles` or `ass`
filter** - cues are Pillow RGBA plates in Progress Sans Text, timed from `/with-timestamps`
character alignment, composited as one alpha strip. Traps and defaults: `burn()` and
`build_strip` pin `-t` from the source duration; offsets account for xfade (slide *i*
starts at `sum(durations[:i]) - i * xfade`); captions sit in the lower-third SAFE ZONE
(`MARGIN_BOTTOM = 132`, plate alpha 236, size 52, 3px stroke) - QA placement and legibility
over the lightest scene, not just presence; `words_from_alignment()` drops every character
inside a `[...]` span so an audio tag never burns on screen - print every built cue and
grep for stray `[`/`]`. (lesson: content/sop/lessons/voices-and-audio.md#caption-mechanics-burn-length-safe-zone-and-tag-leak-pug-tube-7-aug-vr-1-sep-2026)

### Captions AND music: OFF by default for a demo/showcase walkthrough (binding, GM directive 1 Sep 2026)

**For a product/demo/experience walkthrough the DEFAULT is narration-only: NO subtitles
and NO music bed.** A brief line-item is NOT authority; a kickback applies to every
not-yet-delivered cut from the same segments. (lesson: content/sop/lessons/voices-and-audio.md#captions-and-music-default-off-history-plant-demo-8-aug-vr-1-sep-music-absolute-2-sep-2026)

### Sync is a CRITICAL hard gate - verify EXHAUSTIVELY, never self-cert a partial fix (binding, GM directive 1 Sep 2026)

Voice-to-picture sync is the most-rejected defect on this factory's videos and the GM has
named it critical. **A spot-check is NOT verification**: sample frames densely (~every 0.5s)
across the WHOLE timeline and confirm the on-screen state matches the exact word being
spoken (from the char-alignment); `ffprobe` cannot see it. **The fix is an anchor per
beat:**

```json
{"anchor": {"phrase": "It opens the video AT that second", "lead": 1.0, "at": 19.8}}
```

`phrase` is looked up in the TTS character alignment; `lead` is seconds the event PRECEDES
the phrase (negative: the voice cues it; default 1.0); `at` declares a visually subtle
event - **text streaming into a mostly-white panel never wins a frame diff - declare it.**
Trim the dead head until they agree: `target = max(0.3, phrase_time - lead)`;
`trim = max(0.0, event_time - target)` (`event_times()` / `phrase_time()` / `anchor_trim()`
in `scripts/build_pugtube_video.py`). **Record generously so there is head to trim** -
spacing BETWEEN events is a `wait` step. A narration block that NAMES several things needs a
cut per name, timed off the beat's own char-alignment. **Verify after rendering, not from
the trim arithmetic**: screen leads voice by 0 to 3.5s, never trails by more than ~0.5s.
**Narration must not promise an interaction the footage never shows.** (lesson: content/sop/lessons/video-gates-and-currency.md#sync-is-the-most-rejected-defect-anchors-and-dense-verification-vr-and-pug-tube-aug-sep-2026)

### ElevenLabs returns an UNPREDICTABLE output level per render - always per-line normalise (Experience-co, 11 Sep 2026)

**Identical text, voice, model and settings come back anywhere from ~-18 to ~-32 dBFS.**
**Normalise every line to one speech-RMS target BEFORE assembly, then one loudnorm pass on
the assembled track**; verify per-line spread under ~1.5 LU. (lesson: content/sop/lessons/voices-and-audio.md#elevenlabs-output-level-is-unpredictable-per-render-experience-co-11-sep-2026)

### ffmpeg attenuates 3 dB when upmixing mono to stereo at the mux (Experience-co, 11 Sep 2026)

A mono narration track muxed into a stereo output silently loses 3 dB, quietly undoing any
level work upstream. Pan mono to stereo at unity explicitly (e.g. `pan=stereo|c0=c0|c1=c0`)
before encoding, and verify the DELIVERED file's speech level, not the pre-mux track's.

### A looped PNG overlay needs BOTH a -t bound and overlay shortest=1 (Experience-co, 11 Sep 2026)

An `ffmpeg -loop 1` overlay input is infinite: bound it with `-t` AND `shortest=1` on the
`overlay`, or the render never terminates - a stalled output size with hot CPU means a
non-terminating filter graph. (lesson: content/sop/lessons/instruments-and-controls.md#a-looped-png-overlay-needs-both-a--t-bound-and-overlay-shortest1-experience-co-11-sep-2026)

### Every segment must leave with audio and video the same length

Streams differing in length accumulate different chain totals, compounding per join.
(lesson: content/sop/lessons/instruments-and-controls.md#segment-audio-video-mismatch-compounds-per-join-pug-tube-aug-2026)

**`-t` does not fix this - it trims, it never pads.** `apad` the voice to the
video length in every segment builder. Verify per segment, not just on the final
render:

```bash
ffprobe -v error -select_streams v -show_entries stream=duration -of csv=p=0 seg.mp4
ffprobe -v error -select_streams a -show_entries stream=duration -of csv=p=0 seg.mp4
```

A container duration alone hides it - `probe_dur` returns the longer of the two.

### macOS case-insensitive paths silently collapse `s1.mp4` and `S1.mp4` into ONE file (Overbuilt, 18 Sep 2026)

`s1.mp4` and `S1.mp4` are THE SAME PATH on macOS. Never differentiate pipeline
filenames by case; per segment assert `nb_read_frames > 1` (`ffprobe -count_frames`) AND
that the stream lengths agree. (lesson: content/sop/lessons/instruments-and-controls.md#macos-case-insensitive-paths-collapse-s1-and-s1-into-one-file-overbuilt-18-sep-2026)

### Auto-detected anchors find the loudest pixel change, not the narrated event

Auto-detect picks the biggest pixel change - usually the viewer's own action, not the
narrated consequence - and is not deterministic. **Binding rule: anchor to the phrase that
makes the claim, not the phrase that cues it**, with a frame-verified `at` for any
load/settle payoff. **QA gate (binding): view the frame at BOTH the anchor's landing time
and the claim's spoken time.** (lesson: content/sop/lessons/video-gates-and-currency.md#auto-detected-anchors-find-the-loudest-pixel-change-pug-tube-rev-2-and-3-7-aug-2026)

### Re-recording a clip invalidates its anchor's `at` - re-measure, never carry it over

**Any re-record invalidates every measured constant tied to that clip** - re-measure
`at`, hero regions, start fractions. **Verify the gap in the finished render, not from the
trim arithmetic** (`scripts/plant-demo_verify_sync.py` pattern); record which KIND of event
each anchor points at. (lesson: content/sop/lessons/video-gates-and-currency.md#a-re-record-invalidates-every-measured-constant-plant-demo-7-aug-2026)

### Pick a detector that measures the narrated event, not generic motion

Prefer a semantic signal (an overlay dismissing, a mean-luminance jump) over generic
frame-differencing. (lesson: content/sop/lessons/instruments-and-controls.md#pick-a-detector-that-measures-the-narrated-event-plant-demo-aug-2026)

### Budget footage against narration length before you assemble

Check `clip_duration - trim >= audio_duration` per anchored beat -
`tpad=stop_mode=clone` ships a frozen frame, not an error; the tail needs the same
generosity as the head. (lesson: content/sop/lessons/video-gates-and-currency.md#budget-footage-against-narration-before-assembling-plant-demo-aug-2026)

### Hero punch-outs need a frame margin

Keep a margin (26px worked) and cap the punch scale:
`scale = min(scale, (W - 2*M)/w, (H - 2*M)/h)`, clamp position into `[M, W-sw-M]`, fix it in
the shared hero path, and check the region's height contains the content. (lesson: content/sop/lessons/video-crops-and-motion.md#hero-punch-outs-need-a-frame-margin-plant-demo-aug-2026)

### Pad the footage to the beat length BEFORE the hero punch, or the punch never fires

`tpad` the footage to the full beat length FIRST, then run the hero filter, or the
punch's `start` lands past the raw footage and never fires. Verify a frame at `start + 1s`.
(lesson: content/sop/lessons/video-crops-and-motion.md#pad-footage-to-beat-length-before-the-hero-punch-pay-co-pay-28-aug-2026)

### A visual defect in a SHARED UI component recurs on EVERY beat that renders it - sweep all of them

Scan EVERY beat that shows a reused component and re-record all of them off the fixed
app - not just the one flagged. (lesson: content/sop/lessons/video-gates-and-currency.md#a-shared-component-defect-recurs-on-every-beat-that-renders-it-pay-co-pay-28-aug-2026)

### Hero regions are measured on a frame, after the scroll settles

Regions are in source pixel space: extract a real frame at the reveal time, measure on
THAT, and set the start fraction past the beat's own scroll. `scrollTo(y)` silently CLAMPS
to the page maximum - probe in the SAME step order the recording uses, never carry a
destination across builds, assert `window.scrollY` landed within 2px, and take region
coordinates from the landed position. (lesson: content/sop/lessons/video-crops-and-motion.md#hero-regions-and-scroll-clamps-three-shipped-instances-sitefinity-openedge-21-24-aug-2026)

### Gate a post-answer scroll on the ANSWER's selector, never on a fixed wait

Nastier: the scroll fires before the page has GROWN. (lesson: content/sop/lessons/video-crops-and-motion.md#gate-a-post-answer-scroll-on-the-answers-selector-openedge-v2-22-aug-2026)

`record_demo.py` now has a **`waitfor`** action for exactly this:

```json
{"action": "click",   "selector": ".ge-chip", "wait": 1200},
{"action": "waitfor", "selector": "#answerWrap .ge-answer-panel",
                      "timeout": 150000, "wait": 2500},
{"action": "scroll",  "y": 300, "wait": 26000}
```

Binding: **any scroll whose destination only exists after an async answer must be
gated on that answer's own selector.** A fixed wait tuned to a probe's latency is
a race you will lose on the take that matters, and live retrieval varies by 2x
run to run.

**Post-record assertion (cheap, catches it every time):** a clip whose page-top
region is *static for the whole clip* never scrolled. Score the top strip against
the clip's final frame - if it settles at 0.0s, the scroll clamped:

```bash
.venv/bin/python scripts/settle_events.py clip.mp4 --region 344:100:1232:200
```

Run it across every scrolling beat before assembling, not just the one you suspect.

### A segment cache makes one-beat fixes affordable

Skip any segment newer than its own inputs and delete just the one to rebuild - so the
honest call and the cheap call stop competing. (lesson: content/sop/lessons/instruments-and-controls.md#a-segment-cache-makes-one-beat-fixes-affordable-aug-2026)

### Burned captions collide with a card's own bottom-anchored text

Give any card that will carry burned captions a raised footer (`H - 330` worked) and keep
the bottom ~200px clear. (lesson: content/sop/lessons/voices-and-audio.md#burned-captions-collide-with-a-cards-bottom-anchored-text-aug-2026)

### Brand cards - `scripts/assemble.py`

- **`load_logo()` rasterises SVG via CairoSVG**; a base64 `<image>` in an `<svg>` is a
  bitmap and needs a real vector file.
- **Progress Sans, not Arial.** `_find_face()` globs
  `/Library/Fonts/Managed/ProgressSans{Display,Text}-{weight}_*.ttf`; Display for headlines,
  Text for body and captions, never swapped; `brand_face_report()` prints what resolved.
- **`fit_lines()` autofits** the title from 104pt down. (lesson: content/sop/lessons/imagery-and-captures.md#brand-cards-svg-logos-and-progress-sans-resolution-revolution-aug-2026)

### Audio

- **Cards sit over a soft pad, not `anullsrc`.** Every assembled video used to
  open on ~3 seconds of literal digital silence, which reads as a broken file.
- **Two-pass `loudnorm`** to `I=-14:TP=-1.5:LRA=11`, forced stereo 48k. Output
  measured -18 LUFS with LRA ~2.6 before this - about 4 LU quieter than
  surrounding feed content - and the forced stereo also fixes the mono/stereo
  mismatch that made concat fragile.

### Auto-framing - `scripts/autoframe.py` (OpenCV)

Trims uniform bands inward from the edges only, snaps to 16:9. It correctly declines
on dashboard apps whose chrome touches all four edges - **do not loosen the threshold to
force a crop**; interior dead space is an editorial push-in. (lesson: content/sop/lessons/instruments-and-controls.md#auto-framing-declines-on-dashboard-apps-and-that-is-correct-autoframepy-aug-2026)

---

## 4. ElevenLabs v3 - measured API reality (2026-08-07)

Probed against the live API. **The endpoint docs do not flag any of this**, and
two of these were wrong in our own earlier recommendations:

| Parameter | On `eleven_v3` |
|---|---|
| `output_format` | Works. Use `mp3_44100_192`; the 128 kbps default cost a second lossy generation for nothing |
| `previous_text` / `next_text` | **HTTP 400 - "not yet supported"** |
| `previous_request_ids` / `next_request_ids` | **HTTP 400 - "not yet supported"** |
| `seed` | Accepted, but **NOT reproducible** - same seed twice returned different audio (identical byte length, different hash) |
| `style`, `use_speaker_boost` | Accepted, audibly change output |
| `speed` | Accepted but appears inert (byte-identical to baseline) |
| `apply_text_normalization` | Accepted and changes output, despite the model docs saying v3 has no normalisation |

**Consequence: cross-segment prosody continuity is unavailable on v3 today, and takes
cannot be pinned** - `_payload()` gates the continuity params off v3; when continuity or
reproducibility matters, run `eleven_multilingual_v2` and accept losing the audio tags.
(lesson: content/sop/lessons/voices-and-audio.md#v3-prosody-continuity-is-unavailable-multilingualv2-is-the-fallback-aug-2026)

**Audio tags** are v3's real advantage and should be used surgically:
`[serious]` on a refusal beat, `[curious]` on a question, ellipses for pauses,
CAPITALS for emphasis.

**AN ELLIPSIS IN v3 PRODUCES AN UNBOUNDED PAUSE, AND EVERY OTHER CHECK CALLS THE
TAKE CLEAN (9 Oct 2026).** "The same question... from two different people"
rendered a **5.33 second hole** of dead air at the ellipsis inside a 40.64s take,
against a 1.5s internal-gap ceiling. Level, words-per-minute and forced alignment
all passed: the words are all present, correctly spoken and correctly timed, so
nothing that measures the WORDS can see it. The defect lives entirely in the
silence between them, which is the one thing none of those instruments reads.
This line of the skill said "ellipses for pauses" and was silent on magnitude,
which is how it shipped.

So: **measure internal silence per take, fail the build over a ceiling, and plant
a deliberate hole to prove the measure fires** - a gap check that has never fired
is indistinguishable from one that cannot. `videos/sa-use-cases/make_vo.py` is the
reference implementation and carries a planted-3s selftest.

Two things it gets right that are easy to miss. It **backfills the measurement
for takes kept by `--only`**, so the population is the whole film rather than the
lines that happened to be re-recorded - a per-take check that only examines
today's takes silently excludes yesterday's. And the fix for an over-long pause is
to **write the pause**, not to tune the renderer: break the line, or use an
explicit short tag, rather than trusting an ellipsis to mean a particular
duration. It does not. v3 stability is a three-preset system (0.0 Creative /
0.5 Natural / 1.0 Robust), not a free dial; Natural keeps tags responsive.

**v3 has no text normalisation safety net for identifiers.** Spell numbers as
words in script (the Revolution script did this correctly - "eighteen vehicles",
"fourteen days"), and build a pronunciation dictionary for ARAG, Nuclia, REMi,
PDI, ADAS and part-number patterns (`pronunciation_dictionary_locators`, max 3).

**Speaker-note hygiene.** `clean_note()` strips only parentheticals built purely from
stage vocabulary and containing no digits - stripping every parenthetical deletes legitimate
spoken content. (lesson: content/sop/lessons/voices-and-audio.md#speaker-note-hygiene-cleannote-scope-aug-2026)

---

## 5. QA (binding)

- **A scan that cannot fail is not evidence** - ship every leak/claim scanner with a
  `selftest()` proving each pattern fires on a real positive, run as a precondition; never
  FP-suppress a zero-tolerance term family. (lesson: content/sop/lessons/video-gates-and-currency.md#a-scan-that-cannot-fail-is-not-evidence-selftest-discipline-aug-2026)
- **A cited source title can carry a hard-rule-2 breach** - scan the citation chips of every
  filmed answer; corpus document titles are part of the video's copy surface. (lesson: content/sop/lessons/video-gates-and-currency.md#a-cited-source-title-can-breach-hard-rule-2-erp-reel-22-sep-2026)
- **A compliance capture re-drives the app** - for any run-varying beat, read the chips and
  the answer off the RECORDED FRAME. (lesson: content/sop/lessons/video-gates-and-currency.md#a-compliance-capture-re-drives-the-app-erp-reel-22-sep-2026)
- **Choose a wait marker that cannot already be on the page** - wait on text GROWTH past the
  baseline, then on a marker only the answer can produce; fail loudly. (lesson: content/sop/lessons/video-gates-and-currency.md#choose-a-wait-marker-that-cannot-already-be-on-the-page-cartwright-sep-2026)

- **Clear generated frame directories before regenerating them.** A re-plan
  renumbers beats, so last run's `b012_app_*.png` sits beside this run's
  `b012_question_*.png` and a reviewer grades a mix of two cuts. The QA step
  deletes its own output first.

- **The in-frame capture needs prove-it-can-fail discipline** - wait on the answer's own
  MARKER and raise if it never appears; check the captured payload contains what you filmed.
  (lesson: content/sop/lessons/video-gates-and-currency.md#the-in-frame-capture-needs-prove-it-can-fail-discipline-erp-keynote-19-sep-2026)
- **Load a borrowed scanner under its own module name**
  (`importlib.util.spec_from_file_location`) and assert the provenance of what it scans.
  (lesson: content/sop/lessons/instruments-and-controls.md#load-a-borrowed-scanner-under-its-own-module-name-erp-keynote-19-sep-2026)

- **`ffprobe -show_entries stream=a,b,c` returns the entries in the STREAM's
  order, not the order you asked for.** A three-way unpack then mislabels them -
  a QA gate printed "audio aac 48000ch 2Hz" and FAILed a perfectly good stereo
  48k file. Query one entry per call.

- **Re-verify the app's own copy against the LIVE app** (fresh cache-busted context), OCR
  the finished video and compare; never crop a beat to hide on-screen text. (lesson: content/sop/lessons/video-gates-and-currency.md#re-verify-the-apps-copy-against-the-live-app-openedge-v3-24-aug-2026)
- **`--warmup` does not guarantee the white screen away** - sample first-frame mean
  luminance per clip (near-white ~250 is blank) and cut past it or re-record. (lesson: content/sop/lessons/imagery-and-captures.md#warmup-reduces-the-white-screen-check-per-clip-openedge-v3-24-aug-2026)

- Playback duration against script timing.
- **Per-beat sync gap, measured in the FINISHED FILE and printed** - run
  `scripts/plant-demo_verify_sync.py <final>.mp4` (or the equivalent for the build):
  it finds each anchored event inside that beat's own window of the rendered
  output and prints `claim_time - landing_time` per beat. Screen leads voice by
  0 to 3.5s. Matching stream durations is NOT this check and will pass while the
  video is badly out of sync; neither is the assemble-time trim table, which is
  arithmetic over declared constants and will print a clean row against a stale
  `at` (this shipped past a frame spot-check once - see the re-record section).
- **Re-derive every measured constant from the clips currently on disk** before
  trusting `narration.json` - a re-recorded clip silently invalidates its `at`.
- **VIEW** extracted frames at start, middle and end - "looks fine" is a FAIL
  per the DoP evidence rule. Include a frame at the moment the narration names
  each proof beat, and confirm the thing being named is actually on screen.
- `ffprobe` the output: confirm -14 LUFS +/- 0.5, stereo 48k.
- `silencedetect` the head: any silence at t=0 is a defect.
- Check captions are in sync at a mid-point frame, and that none end on a
  dangling separator.
- Crop or neutralise any residency string (hard rule 8).
- Australian English, no em dashes, no banned words.

**Check `shots/presentation-library/` before capturing anything new** (GM
directive, 5 Aug 2026) - an existing shot of the same capability is usually
already there and is canon.

**Deliver via PMK-1** - `dam_claim_work` / `dam_submit_work` once QA and the DoP
gate pass (hard rule 12). No chat approval gate on the script; the finished
video is judged at DAM review time.

---

## 6. Documented but deliberately NOT adopted

Manim, Blender/`bpy`, MoviePy, D2, VHS, stock footage and AI image generation/avatars
were each researched Aug 2026 and deferred - read the lesson before re-litigating.
**MoviePy pins `pillow<12.0` and would silently downgrade Pillow - do not install.** (lesson: content/sop/lessons/instruments-and-controls.md#video-tooling-researched-and-deliberately-not-adopted-aug-2026)

**Installed and in use:** `cairosvg`, `opencv-python-headless` (both verified not
to disturb Pillow 12.3.0). Do not add `moviepy`.

## Cut-4 viewer-gate lessons (22 Sep 2026, Molyneux Files) - binding additions to 0b/5

An instrumented QA PASS and a fresh-eyes viewer NO can land on the same cut. Digest; full
incidents and measurements are in the linked lessons.

1. Floor metrics the strict way: full-runtime zero-motion and silence maps, no card
   exemptions; end-card hold caps ~4s. (lesson: content/sop/lessons/video-gates-and-currency.md#instrumented-pass-versus-fresh-eyes-no-strict-floor-metrics-molyneux-cut-4-22-sep-2026)
2. Ship-blocking proper-noun check: ASR the final narration; verify by ASR AND ear. (lesson: content/sop/lessons/voices-and-audio.md#proper-noun-pronunciation-is-ship-blocking-molyneux-22-sep-2026)
3. Luminance floor: TRUE brightness on a phone; under ~10/255 mean fails. (lesson: content/sop/lessons/video-crops-and-motion.md#luminance-floor-for-feed-viewing-molyneux-22-sep-2026)
4. Thesis lines get the strongest image - the camera performs exactly them. (lesson: content/sop/lessons/video-gates-and-currency.md#thesis-lines-get-the-strongest-image-molyneux-22-sep-2026)
5. Transition audit: no superimposed layouts, OS cursor, banners, clipped-and-held text.
   (lesson: content/sop/lessons/video-crops-and-motion.md#transition-audit-molyneux-22-sep-2026)
6. Viewer gate outranks instruments; on conflict reconcile, never average. (lesson: content/sop/lessons/video-gates-and-currency.md#the-viewer-gate-outranks-instruments-reconcile-never-average-molyneux-22-sep-2026)
7. Hall-legibility floor: evidence cap-height ~2.8-3.3% of frame height; the floor map is a
   REQUIRED QA artifact. (lesson: content/sop/lessons/video-crops-and-motion.md#hall-legibility-floor-for-keynote-pieces-erp-reel-22-sep-2026)
8. A caption never lands before its evidence; reconcile card copy with the app. (lesson: content/sop/lessons/video-gates-and-currency.md#a-caption-never-lands-before-its-evidence-22-sep-2026)
9. Motion is measured at PHONE WIDTH (~390px tblend); only EVENTS count; gate on the
   longest frozen RUN. (lesson: content/sop/lessons/video-crops-and-motion.md#motion-is-measured-at-phone-width-and-only-events-count-molyneux-cut-7-22-sep-2026)
10. Loudness differs ~3 LU between stereo and mono measurement. (lesson: content/sop/lessons/instruments-and-controls.md#loudness-differs-about-3-lu-between-stereo-and-mono-measurement-22-sep-2026)
11. The text-slice guard works at the LINE level: whole-or-out (`framing_proof.py`). (lesson: content/sop/lessons/video-crops-and-motion.md#the-text-slice-guard-works-at-the-line-level-erp-reel-22-sep-2026)
12. Pause-capping trims true silence only (no >20dB step in ~50ms); a type resize re-runs
    fit proofs; punches start at column boundaries. (lesson: content/sop/lessons/video-crops-and-motion.md#two-edit-regression-traps-molyneux-cut-7-22-sep-2026)
13. The settled frame must BE the proven frame; proofs assert BOTH ends of a move; caches
    key on the renderer's mtime. (lesson: content/sop/lessons/video-crops-and-motion.md#the-settled-frame-must-be-the-proven-frame-erp-reel-22-sep-2026)
14. A gate measures the ARTIFACT, never an upstream proposal. (lesson: content/sop/lessons/video-gates-and-currency.md#a-gate-measures-the-artifact-never-a-proposal-erp-reel-b3p-22-sep-2026)
15. An unauditable shot does not ship; exclusion guards run per-frame across moves. (lesson: content/sop/lessons/video-gates-and-currency.md#an-unauditable-shot-does-not-ship-iwtv-graph-act-22-sep-2026)
16. Reviewers read a FROZEN, checksum-named artifact; dispatches carry the md5. (lesson: content/sop/lessons/video-gates-and-currency.md#a-reviewer-reads-a-frozen-checksum-named-artifact-sitefinity-enablement-22-sep-2026)
17. The talk track argues, the screen states: no narration line shares its key noun-verb
    content with visible text. (lesson: content/sop/lessons/voices-and-audio.md#the-talk-track-argues-the-screen-states-gm-kickback-22-sep-2026)
18. `speed` works on `eleven_multilingual_v2` (joins the TTS cache key; "inert" is
    v3-only); proper-noun checks run in the RENDER loop. (lesson: content/sop/lessons/voices-and-audio.md#two-tts-measurement-laws-keynote-rev2-23-sep-2026)
19. Pace and loudness are FULL-RENDER properties; two-pass loudnorm; positive-control any
    "text not visible" result. (lesson: content/sop/lessons/voices-and-audio.md#voice-pace-and-loudness-are-full-render-properties-23-sep-2026)
20. The motion floor is EVENTS WITH AREA: thin, slow or small elements never register;
    assert the scan's sample count. (lesson: content/sop/lessons/video-crops-and-motion.md#the-motion-floor-is-events-with-area-and-the-threshold-is-computable-tourism-film-29-sep-2026)
21. Take the 2x still INSIDE the recording session (`device_scale_factor=2`). (lesson: content/sop/lessons/imagery-and-captures.md#take-the-2x-still-inside-the-recording-session-29-sep-2026)
22. Reading shots get no camera push; padding must exceed half any kept push. (lesson: content/sop/lessons/video-crops-and-motion.md#a-camera-push-travels-past-the-framing-you-proved-29-sep-2026)
23. No statistical photograph detector - assert no `<img>` box overlaps the recorded
    viewport and REFUSE otherwise. (lesson: content/sop/lessons/instruments-and-controls.md#no-statistical-detector-for-a-photograph-in-frame-prove-the-geometry-29-sep-2026)
24. The end card composites `assets/logos/primary-horizontal-alternate.png`, never type;
    WIPE the mark in. (lesson: content/sop/lessons/imagery-and-captures.md#the-end-card-composites-the-supplied-lockup-never-type-29-sep-2026)
25. Size the app plate from whichever dimension binds; geometry RAISES if a caption falls
    off-frame. (lesson: content/sop/lessons/video-crops-and-motion.md#size-the-app-plate-to-fit-the-frame-and-assert-dependent-geometry-tourism-film-29-sep-2026)
26. A full build DELETES orphan segments; a cut REFUSES stale segment names. (lesson: content/sop/lessons/video-gates-and-currency.md#a-renamed-beat-leaves-orphan-segment-files-29-sep-2026)
27. Parameterise a gate's file when a second cut exists; inapplicable checks report NOT
    APPLICABLE. (lesson: content/sop/lessons/video-gates-and-currency.md#a-gate-hardcoded-to-one-file-leaves-the-other-cut-uncovered-29-sep-2026)
28. Freeze the artifact under review - verify the md5 before starting, refuse on mismatch.
    (lesson: content/sop/lessons/video-gates-and-currency.md#freeze-the-artifact-a-reviewer-is-reading-29-sep-2026)
29. Viewer-instrument conflicts: reproduce with the defined method; it can go EITHER way.
    (lesson: content/sop/lessons/video-gates-and-currency.md#viewer-instrument-conflicts-reconcile-either-way-29-sep-2026)
30. Design the first frame as a poster. (lesson: content/sop/lessons/imagery-and-captures.md#design-the-first-frame-as-a-poster-29-sep-2026)
31. Free render trees at the END of finish (`--keep-frames` opt-in); NEVER sweep clips,
    stills, TTS takes or cited evidence frames. (lesson: content/sop/lessons/instruments-and-controls.md#release-per-frame-render-trees-in-the-finish-step-29-sep-2026)
