# Motion system, transitions and the craft bar

`PLAYBOOK.md` says "define the motion system once, not per scene" and "transitions are
continuity tools". This file is the concrete vocabulary for doing that in this engine.
Distilled from the engine's own `hyperframes-animation` skill, which is the authority -
open `reference-repos/reference-repos/hyperframes/skills/hyperframes-animation/` for the
full recipes.

---

## 1. Define the motion system in one place

Put the whole motion language on the timeline's `defaults`, then deviate deliberately:

```js
const tl = gsap.timeline({
  paused: true,
  defaults: { duration: 0.6, ease: "power3.out" },   // the house settle
});
```

`power3.out` is the workhorse. The doctrine, verbatim from the engine skill: **smooth
beats bouncy.** Vary energy *within* the smooth families - `sine`/`power1` for calm,
`power3` standard, `power4`/`expo` for punch. Overshoot (`back`, `elastic`, `bounce`) is a
**register**, not a spice: reach for it only when the piece is explicitly playful, which
for a CIO/CMO/SA room it almost never is. One ease everywhere reads flat; bounce
everywhere reads cheap, and the second failure is much worse.

| Ease | Use |
| --- | --- |
| `power3.out` | Entrances, title cards, hero reveals. The default. |
| `power2.out`, `power1.out` | Secondary motion - a caption fade, a small shift. |
| `sine.inOut` | Long calm motion, crossfades, ambient drift, anything yoyo. |
| `power4.out`, `expo.out` | Dramatic snaps, premium reveals. |
| `none` | Camera moves with timed counterpoint, bars filling, mechanical motion. |
| `steps(N)` | Typing, counter ticks, cursor blink. |
| `back.out(1.7)`, `elastic.out` | Rare. Explicitly playful only. |

**Stagger, not N delayed tweens.** `stagger: 0.08` stays correct when the item count
changes. Cap a group arrival so it reads as one beat: `items x stagger <= ~0.5s`.

```js
tl.fromTo(".card", { y: 24, autoAlpha: 0 },
  { y: 0, autoAlpha: 1, duration: 0.5, stagger: 0.08 }, "cards");
```

### The seek-safe spring

The "iOS feel" is a damped spring's velocity curve, not a bounce. A real-time spring
solver is a stateful integrator and cannot be seeked, so it is banned. The engine skill
ships a closed-form spring as a pure function of progress - seek-safe by construction.
Full implementation in `hyperframes-animation/adapters/gsap-easing-and-stagger.md`
(`springEase({response, dampingFraction})`). Take **both** the ease and the duration it
returns; the settle time is the physics. `dampingFraction: 1` is the house setting - no
overshoot, the exact curve `power3.out` approximates, with a longer premium tail. Use it
when the settle *is* the shot: a wordmark landing, a final lockup.

---

## 2. Transitions - and the rule that corrects how this factory has been building

From the engine's `transitions/overview.md`, non-negotiable for any multi-scene piece:

1. **Every composition uses transitions.** No exceptions - scenes without them read as
   jump cuts.
2. **Every scene animates in.** Nothing pops fully formed onto screen. Use
   `gsap.fromTo()`, never `gsap.from()` (a `from()` against CSS `opacity: 0` is a 0-to-0
   noop and the element never appears).
3. **Exit animations are BANNED except on the final scene.** Do not fade the outgoing
   scene out before the next one enters. **The transition IS the exit.** The outgoing
   content must be fully visible when the transition starts.
4. The last scene may fade out. Only the last.

> This supersedes the old instruction in this skill's section 3 ("entrances with
> `.from(...autoAlpha:0...)`, exits with `.to(...autoAlpha:0...)`"). Fading A out and then
> animating B in is a jump cut with a dip in it, which is why factory pieces have read as
> assembled rather than produced. Both halves must move at the same timeline position.

```js
// WRONG - a dip, not a transition
tl.to("#s1", { autoAlpha: 0, duration: 0.4 }, 4.0);
tl.fromTo("#s2 .headline", { y: 40, autoAlpha: 0 }, { y: 0, autoAlpha: 1 }, 4.4);

// RIGHT - one handoff at one time T
const T = 4.0;
tl.to("#s1",   { yPercent: -100, filter: "blur(8px)", duration: 0.5, ease: "power3.in" }, T);
tl.fromTo("#s2", { yPercent: 100 }, { yPercent: 0,    duration: 0.5, ease: "power3.out" }, T);
```

### Choosing one

Pick ONE primary transition carrying 60-70% of the scene changes, plus one or two accents.
Never a different transition per scene.

| Energy | Primary | Duration | Easing |
| --- | --- | --- | --- |
| Calm (brand story, trust, premium) | Blur crossfade, focus pull | 0.5-0.8s | `sine.inOut`, `power1` |
| Medium (corporate, SaaS, explainer) - **the factory default** | Push slide, staggered blocks | 0.3-0.5s | `power2`, `power3` |
| High (launch, promo) | Zoom through, overexposure | 0.15-0.3s | `power4`, `expo` |

By narrative position: the **opening** gets your most distinctive transition (0.4-0.6s, it
sets the language); **between related points** the primary, consistent, 0.3s; a **topic
change** gets something different so the viewer's brain resets; the **climax** gets your
boldest accent; the **outro** the slowest and simplest, 0.6-1.0s, introducing no new
energy.

Blur intensity tracks energy: calm 20-30px over 0.8-1.2s, medium 8-15px over 0.4-0.6s,
high 3-6px over 0.2-0.3s.

---

## 3. Search the catalogue before hand-authoring a move

386 registry items and ~45 atomic rules already exist. Hand-authoring a beat that is
already built is the slow path and produces worse motion.

```bash
$HF catalog --query "<describe the beat in plain English, in English>"
```

The atomic rules live in `hyperframes-animation/rules-index.md`, indexed by trigger and
tag. The ones that map onto work this factory actually does:

| Beat the factory keeps building | Rule |
| --- | --- |
| Punchy tagline, phrases landing on a rhythm | `kinetic-beat-slam` |
| A metric with a bar, ring or rating beside it | `stat-bars-and-fills` |
| Counting a number up with escalating emphasis | `counting-dynamic-scale` |
| A headline arriving word by word | `waterfall-entry` |
| A card or logo arriving | `spring-pop-entrance` |
| Highlight sweeping through a headline | `gradient-text-sweep` |
| Pushing into a detail of a screenshot | `coordinate-target-zoom`, `multi-phase-camera` |
| Blurring everything except the focal panel | `depth-of-field-blur` |
| An outline or architecture diagram drawing itself | `svg-path-draw` |
| A cursor driving a UI | `cursor-click-ripple`, `cursor-drag` |
| Reading a value off a chart | `chart-scrub-readout` |
| Swapping one line of copy for another on a beat | `line-swap` (registry) |

Every rule assumes the same contract: one paused timeline, `fromTo` with explicit
from-states, absolute values (never relative `+=`), no `Math.random`/`Date.now`, finite
repeats, transforms and paint-only properties, no CSS `transition` on an animated element.

When nothing fits, say so - `$HF feedback --search-miss "<query>" --wanted "<the move>"
--tier words`. `catalog --query` prints that line pre-filled.

---

## 4. Property discipline

**Animate:** `x`, `y`, `xPercent`, `yPercent`, `scale`, `scaleX/Y`, `rotation`,
`rotationX/Y/Z`, `skew`, `transformOrigin`, `opacity`, `autoAlpha`, `filter`, `clipPath`,
`strokeDashoffset`, CSS custom properties.

**Never animate for layout:** `width`, `height`, `top`, `left`, `margin`, `padding`.
The engine forbids them. Where a box genuinely must grow, use a scale proxy with an
inverse counter-scale on the child, or a mask - see `anchored-layout-expand`.

**Never animate on a clip element:** `display`, raw `visibility`. The framework owns clip
visibility and lint rejects it. Use `autoAlpha`, or a zero-duration `tl.set()` at an
explicit beat boundary.

Two more, both silent failures the automated gates can miss:

- **A transformed element must be block-level and sized.** `scaleX` on an inline `<span>`
  is a no-op, and scaling an auto-width element shows nothing - the classic invisible
  progress bar. Give it `display: block` and a real width.
- **Pulsing absolute decoratives need clearance at their peak**, not their resting size,
  and must not straddle an `overflow: hidden` edge.

---

## 5. Pacing - and how to gate it

The factory's most persistent defect is not a broken render, it is a section that settles
early and then holds a static frame while the narration keeps talking. Measured example: a
well-formed 8-second section whose content all landed by t=2.2s produced **bit-identical
frames from 2.2s to 8s** and `hyperframes check` passed it with zero findings, because
`sweep_static` only fires when the *whole* composition never moves.

A `*.motion.json` sidecar catches it. It is the single highest-value thing in this engine
the factory was not using. Drop it next to the composition, matching the HTML basename -
`check` discovers it with no flag:

```json
{
  "duration": 8,
  "assertions": [
    { "kind": "appearsBy", "selector": "#c1", "bySec": 2.5 },
    { "kind": "before", "a": "#kicker", "b": "#headline" },
    { "kind": "staysInFrame", "selector": "#headline" },
    { "kind": "keepsMoving", "withinSelector": "#s1", "maxStaticSec": 2 }
  ]
}
```

Verified output on the dead-air section above:

```
Motion
  x motion_frozen: nothing moves within #s1 between 2.2s and 8s (5.8s static)
```

It names the section, the window and the duration, and it runs **before** the render.
Assertion kinds, all proven to fire:

| Kind | Fails when |
| --- | --- |
| `appearsBy(selector, bySec)` | not visible (opacity >= 0.5) by `bySec` - `motion_appears_late` |
| `before(a, b)` | `a` does not first appear strictly before `b` - `motion_out_of_order` |
| `staysInFrame(selector)` | once visible, its box leaves the canvas - `motion_off_frame` |
| `keepsMoving(withinSelector?, maxStaticSec?)` | a static window exceeds `maxStaticSec` (default 2s) - `motion_frozen` |

A selector matching nothing fails loudly as `motion_selector_missing` rather than passing
silently - so a typo cannot quietly disable an assertion.

**Write one `keepsMoving` assertion per scene, with `maxStaticSec: 2`, on every
multi-beat build.** That is the rule. And prove the sidecar fires at least once per
project by planting a deliberately wrong assertion and watching it fail, then removing it -
a gate you have never seen fail is not a gate.

---

## 6. Escape hatches for intentional layout

`check`'s layout audit measures `getBoundingClientRect`, not painted pixels, so
`overflow: hidden` does not silence a finding. Mark intent in the HTML instead:

| Attribute | Silences |
| --- | --- |
| `data-layout-allow-overflow` | Overflow, for deliberate entrance/exit travel. Inherited by descendants, so scope it to the narrowest wrapper. |
| `data-layout-allow-overlap` | Deliberate text layering. Not inherited - mark the participant, never a scene wrapper. |
| `data-layout-allow-occlusion` | An element meant to cover text. |
| `data-layout-ignore` | A purely decorative element. |

`data-layout-allow-overflow` has real blast radius: it also suppresses `text-clipping`,
`content-cramped-container` and `foreground-over-panel` for the whole subtree. Two checks
deliberately survive it - `primary-offscreen` and `foreground-over-panel` at the canvas
edge - so it cannot hide a wordmark sliced by the frame.
