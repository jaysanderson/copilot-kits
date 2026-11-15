# HyperFrames Agent Playbook (binding methodology)

Handed down by the GM, 4 Sep 2026, to make our videos even better. This is the CREATIVE
methodology layer for every HyperFrames build; `SKILL.md` in this folder is the factory-
environment mechanics (install, fonts, render path, traps). Follow both. The mechanics get a
clip to render; this playbook makes it *good*.

## The core reframe

Do NOT treat HyperFrames as `prompt -> video`. Treat it as a programmable production SYSTEM:

  knowledge -> narrative -> creative system -> storyboard -> compositions -> reusable
  components -> controlled iteration -> render -> variants

The goal is never "one impressive MP4". It is: good narrative + strong visual direction +
editable source + reusable components + repeatable templates + reliable renders. The source
PROJECT is the core asset; the rendered video is an output.

## 1. Start from source material (warm start, never invent)

Ground every important video in authoritative source: website, product page, brief, messaging
doc, screenshots, demo recording, transcript, PDF, repo, customer story, research, CSV, brand
guidelines. Before building, establish: source of truth / audience / what they should
understand / believe / do next / which claims are actually supported. NEVER invent unsupported
product capabilities, statistics, UI, terminology or customer results. (This IS the no-fake /
authenticity gate - hard rule 3 / B47 - applied to video.)

## 2. Artifacts before build (for anything multi-beat)

Simple/very-short pieces may be built directly. Anything with several narrative beats gets the
creative artifacts FIRST, as durable production files (do not bury creative decisions only in
implementation code):
- **DESIGN.md** - the visual system (§3)
- **STORYBOARD.md** - the beats (§5)
- **narration.txt** - for narrated pieces (§18)
Sequence: Capture -> Design -> Script -> Storyboard -> Voiceover -> Build -> Validate.

## 3. DESIGN.md first - define the visual system before any scene

Cover: visual direction, colour palette, typography, spacing, composition rules, background
treatment, UI presentation, motion language, transition language, caption treatment, chart
treatment, image treatment, brand constraints, things to avoid. Translate subjective direction
into OBSERVABLE rules. Not "make it premium/futuristic" but e.g.: near-black bg, off-white
type, brand colour only for emphasis/active states, large grotesk sans headlines, small mono
secondary labels, large negative space, product UI occupies ~65-75% of frame when shown, avoid
decorative particles/neon/generic-AI imagery/excess gradients.

## 4. Define the motion system (once, not per scene)

Establish a consistent motion language and reuse it: consistent easing, duration, stagger,
camera movement, transition motifs. Example: primary entrances = opacity + 20-30px rise;
product UI = slow scale ~0.96->1; secondary elements = 80-150ms stagger; scene transitions =
masked camera push; stats = count-up with restrained overshoot; CTA = slow scale settle; bg =
subtle continuous movement where apt. Motion reinforces hierarchy and narrative - never animate
just because an element *can* move.

## 5. STORYBOARD.md - explicit beats

Break the video into beats, each specifying (where relevant): duration, purpose, visual,
on-screen copy, voiceover, assets, animation, camera behaviour, transition, proof point, CTA.
Describe what the VIEWER EXPERIENCES, not implementation. Example beat: "BEAT 1 - Problem /
0-5s / Purpose: establish the audience problem / Visual: minimal headline over abstract
product-context bg / Copy: 'Enterprise AI has a context problem.' / Motion: slow camera / Exit:
headline rises as product interface enters."

## 6. Make the first seconds earn attention

No slow logo reveals, generic setup, introductions or corporate filler. The opening
immediately establishes ONE of: problem / tension / surprising claim / capability / result /
visual transformation. Useful product-marketing arc: Problem -> Shift -> Product -> Mechanism
-> Proof -> Outcome -> CTA (not every video needs all seven, but every scene must ADVANCE the
story).

## 7. Control text density

Video is not a deck. One idea per frame; short headlines/labels; large type; strong hierarchy.
Keep important on-screen copy under ~8 words where possible. Push supporting explanation into
voiceover / animation / visual evidence / later beats. Never make the viewer read long text AND
inspect detailed UI at once.

## 8. Preserve real product UI

Use ACTUAL screenshots/recordings/captures/logos/interface assets. Don't recreate real software
UI unnecessarily. Enhance real UI via HyperFrames: browser framing, zoom, camera movement,
masking, highlighting, cursor movement, callouts, annotations, crop transitions, depth,
parallax, bg treatment. The product must stay recognisable and credible. (For our demo videos:
capture off the live demo, then FRAME it - do not redraw the demo.)

## 9. Composition, not decoration

Every frame has deliberate hierarchy: what the eye sees first, second, what can disappear, what
needs breathing room. One dominant visual idea per shot. Use negative space intentionally;
don't fill space just because it's there.

## 10-12. Reusable compositions, variables, existing blocks

- **Reusable compositions**: build once for recurring elements (brand intro, logo treatment,
  browser frame, product-UI scene, metric reveal, customer quote, chart, lower third, code
  animation, CTA, caption system, scene transition, bg treatment). If a sequence appears twice,
  make it reusable; across multiple videos, it almost certainly should be. Prefer nested
  compositions.
- **Variables aggressively**: expose title, subtitle, customerName, customerLogo, industry,
  metric, quote, speaker, productScreenshot, CTA, URL, colour, region, releaseName, featureName.
  Think: fixed creative system + variable content, not independent videos from scratch.
- **Existing HyperFrames blocks**: before hand-rolling a common effect (charts, transitions,
  overlays, data-viz, effects), check for an existing block/component; adapt it to THIS design
  system rather than letting it import inconsistent styling.

## 13. Build the first complete version quickly

After DESIGN.md + STORYBOARD.md are coherent, build the full first pass. Don't perfect an
isolated opening before the rest exists. Establish full narrative, overall timing, scene
relationships, visual consistency, asset completeness - THEN refine. A complete rough beats a
perfect 5s fragment for information.

## 14. Review like an editor

Inspect the WHOLE video: does the story make sense without explanation? Does the first 5s work?
Any scene too long? Anything visually confusing? Motion consistent? Every line readable
comfortably? Transitions aiding continuity? Product visible enough? Proof points clear? CTA
earned? Check pacing WITHOUT audio, then WITH. A visually strong video must not depend entirely
on narration to make sense.

## 15-17. Iterate surgically; fix the right layer

- **Surgical edits** once a complete version exists - never broad "make it more exciting"
  regeneration. Instead: "Scene 2 feels slow, remove 1.2s from the hold"; "increase title size
  in scene 3 by 15%"; "reduce the camera push in scene 4 by half"; "move the annotation above
  the product panel so it stops obscuring the UI"; "hold the final product shot 800ms longer -
  keep all other scenes unchanged." Smallest change that fixes the problem; PROTECT what works.
- **Conceptual problem -> STORYBOARD.md**: if a scene fails because the idea is weak, the story
  order is wrong, proof appears too early, message is unclear, or the scene has no purpose -
  fix the storyboard, then rebuild only the affected beat(s).
- **Systemic problem -> DESIGN.md**: if multiple scenes share an issue (headlines too small,
  animations too fast, UI frames too cramped, brand colour overused, transitions too
  aggressive, alignment inconsistent) - fix the design system rule, then apply across scenes.
  Fix the system over patching ten scenes. Keep creative intent, storyboard and implementation
  aligned - implementation is never the only source of truth.

## 18. Audio deliberately

Write narration BEFORE finalising timings (story -> script -> narration -> timing -> animation
refinement). Never force VO into durations designed without it. Keep narration concise. Do NOT
have VO read the on-screen text verbatim - use the two channels differently: SCREEN = high-level
message; VOICEOVER = context, explanation, nuance. (And per our own rule: when the query/answer
IS the payload - a funny ruling, a striking answer - voice it out loud.) Music supports pacing
without competing with narration; SFX reinforce meaningful events, not every animation. (Our
default remains music-free unless it genuinely serves.)

## 19. Transitions = continuity tools

A transition CONNECTS scenes, it doesn't announce itself. Prefer shared movement, camera
continuation, masking, element handoff, scale continuation, colour continuation, matching
geometry. Avoid a random catalogue of different effects - a video feels more expensive when
one or two transition motifs are repeated elegantly.

## 20. Data tells a story

Decide the CONCLUSION first, then build the viz around that argument. Weak: "show a 5-bar
chart." Better: "reveal four categories quietly, then emphasise the fifth because it proves the
claim." Use progressive disclosure, highlighting, comparison, count-up, annotation, camera
focus so the intended interpretation is obvious. The viewer must know WHY the number matters.

## 21. Avoid generic AI aesthetics

Unless the brief requires it, avoid: brains, robots, glowing neural networks, floating
particles, blue-purple neon, random circuitry, generic holograms, unnecessary glassmorphism,
fake futuristic dashboards. For an AI product, show the workflow / product / information /
result / evidence - the tech needs no AI-cliche representation.

## 22. Validate before final render

Run project health checks + lint; inspect the full preview; check every scene boundary, fonts,
media, variable values, narration timing, final duration, clipping, text overflow, layout at
target resolution. Produce a LOWER-QUALITY REVIEW RENDER before the highest-quality master;
final production render only once the composition is approved. Where reproducibility matters,
use the controlled render environment, not just local browser state.

## 23. Variants are re-composed, not cropped

16:9 / 9:16 / 1:1 are NOT simple crops. A vertical version may need a different UI crop,
headline wrapping, larger text, different hierarchy, fewer simultaneous elements, repositioned
captions. Reuse the design language + source, optimise the actual layout per format. Likewise
produce 60s master / 30s cut / 15s teaser / customer / industry / partner / regional variants
FROM the underlying system, not rebuilt independently.

## 24. Optimise for a production system, not isolated videos

When a project works, extract what's reusable: which composition -> template; which values ->
variables; which transitions -> standards; which type rules -> house style; which UI treatment
-> reusable; which prompt instructions -> permanent. Over time build a library: design system,
motion system, scene templates, brand components, customer-story/product-demo/data/release/CTA
templates, format variants. The long-term aim: a future request reads like "Create a 30s
product announcement, use the standard launch system, use this release brief as source of
truth, standard browser composition + feature reveal + metric card + CTA, produce 16:9 and
9:16" - not describing every visual decision from scratch. (Our `template/` folder in this
skill is where those live.)

## 25. Product-marketing workflows (quick reference)

- **Product launch**: input = brief/website/screens/messaging/proof -> master + 30s + 15s
  teaser + vertical social. Arc: problem -> change -> product -> how it works -> proof ->
  outcome -> CTA.
- **Product demo**: input = recording/screens/talk-track/messaging. Do NOT replay the
  recording - reframe/zoom/crop/highlight/annotate/focus/transition/narrate into a story.
- **Customer proof**: input = customer/problem/quote/metric/logo/screens/outcome -> a TEMPLATE
  with variables, repeatable across customers.
- **Feature/release**: input = release notes/screens/explanation/context. Focus on what
  changed / why it matters / how it works / what users can now do. Never read release notes
  verbatim.
- **Data story**: input = CSV/survey/research/benchmark/metrics. Identify the ARGUMENT first,
  then build the viz around it. Don't merely animate charts.

## 26. Operating rules (the checklist)

1. Ground important videos in supplied source. 2. Multi-scene -> DESIGN.md + STORYBOARD.md
before implementation. 3. No unsupported claims or UI. 4. Prefer actual product assets. 5.
Motion system before many animations. 6. Concise on-screen copy. 7. Strong hierarchy. 8.
Reusable compositions over duplication. 9. Expose content via variables. 10. Full first pass
before over-polishing. 11. Review the full narrative before cosmetic changes. 12. Precise,
localised edits. 13. STORYBOARD.md when the narrative is wrong. 14. DESIGN.md when the visual
system is wrong. 15. Protect what already works. 16. Validate before production render. 17.
Review renders before masters. 18. Turn successful work into templates. 19. Optimise variants,
don't blindly crop. 20. Source project = core asset, render = output.

## Final principle

The strongest outcome is not one impressive AI-generated video. It is a repeatable production
SYSTEM that turns new product info, customer stories, launches, data and demos into
consistently high-quality video with progressively less effort.
