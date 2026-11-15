# Partner landing page template - the prompt

**Status:** v2.0, 13 August 2026. Partner enablement asset.
**What this is:** a single, tool-agnostic prompt (paste into any AI site builder - v0,
Lovable, Cursor, Claude, or similar) that generates a complete, finished, genuinely
beautiful landing page for a partner offering built on the platform. It is a shareable
exemplar, not a fill-in-the-blanks kit: the prompt invents a fictitious studio ("Northlight
Studio") and writes the whole page for it, so a prospective partner sees a polished
end-to-end example they can adapt by swapping the studio name and their own lead use case.
**Vendor-neutral by design:** the page copy names no platform vendor, so it is safe to
share with any prospective partner, and official co-branding stays a separate Progress-side
decision.

## How a partner uses it

1. Paste the prompt into their AI site builder of choice.
2. Ship it as-is to see the finished exemplar, or swap "Northlight Studio" for their own
   brand, set the one accent-colour variable, and replace the lead use case.
3. Keep the five or six gallery cards that match their real strengths; delete the rest. No
   partner should claim all ten.

## Guardrails baked into the copy

- The offering is END TO END - unify systems of truth into one governed knowledge foundation,
  ground and retrieve over it, then the experience people use every day. The word "front-end"
  never appears; the framing is the whole journey, not a layer on top.
- Never say or imply the customer already has retrieval, a knowledge base, a vector index, or
  a working chatbot - they have raw, scattered knowledge, and the partner builds the rest.
- No platform or vendor name in any page copy - "your knowledge base" / "your AI knowledge
  platform" only.
- No accuracy percentage anywhere - claims are about mechanisms (cited, governed,
  measurable), never a number about correctness.
- A neutral independence line in the footer (this is the studio's own offering).
- "Northlight Studio" is a fictional exemplar - a partner replaces it with their own brand.

---

## The prompt

```
Build a complete, production-ready, single-page marketing website for a fictional digital
experience studio called "Northlight Studio" that designs and builds solutions on top of an
organisation's AI knowledge base. Write the whole page in full - real, finished copy for
Northlight, not placeholders. This is meant to be genuinely award-worthy: assume it will be
judged against the best agency sites on the web. Use any modern stack the tool prefers
(React/Next + Tailwind, or plain HTML/CSS/JS) - the result matters, not the framework.

STRICT COPY RULE: never use "Progress", "Agentic RAG", "ARAG", or any underlying vendor or
product name anywhere on the page. Refer only to "your knowledge base", "your AI knowledge
platform", and "grounded, cited answers". Never state an accuracy or correctness percentage -
every quality claim is about a mechanism (cited, governed, measurable), never a number.

SCOPE RULE (important): Northlight delivers the whole END-TO-END journey, not a single piece -
(1) connecting and unifying the customer's existing systems of truth (documents, drives,
sites, apps, databases) into one governed knowledge foundation the AI can reason over
(integration and ingestion); (2) grounded, cited retrieval over that foundation; and (3) the
on-brand experience people rely on day to day. Deliver it as one end-to-end outcome.
NEVER use the word "front-end" or "front end" anywhere on the page - talk about the end-to-end
experience, the whole journey, or the product people use. And NEVER say or imply the customer
already has AI retrieval, a knowledge base, a vector index, retrieval pipelines, or a working
chatbot - the whole point is that most organisations have the raw knowledge, scattered across
the systems they already run, and NOT the foundation, the grounding, or the trusted experience.
Northlight builds all of it.

=== DESIGN SYSTEM (this is the point - make it exceptional) ===

Art direction: editorial, confident, quietly luxurious - the restraint of a high-end design
studio, not a busy SaaS template. Big ideas, big type, generous negative space, and a few
moments of genuine delight. Every surface should feel intentional.

Colour: a deep near-black ink base (#0B0E14) for the hero and dark sections; a warm paper
tone (#F6F3EC) for light sections; one luminous accent used sparingly (electric teal #16E0C4)
for emphasis, links and interactive states; a soft secondary (warm amber #FFB86B) only for
data highlights. Add a subtle, slow-moving iridescent gradient mesh behind the hero headline
(teal to violet to ink), very low opacity, tasteful - never garish. A faint film-grain / noise
overlay across dark sections for depth.

Typography: a high-impact display face for headlines (use "Clash Display" or "Satoshi" from
Fontshare, or a comparable modern grotesque) at large sizes with tight tracking; a clean,
legible sans for body ("General Sans" or "Inter"); a monospace ("JetBrains Mono") reserved
for small technical labels and data. Establish a real type scale with a strong size jump
between display and body. Headlines can be oversized and set to break across lines
deliberately.

Layout: an asymmetric editorial grid, not centred boxes. Wide margins, confident whitespace,
content that steps and offsets rather than stacking in identical rows. A thin, minimal sticky
top nav that goes translucent on scroll.

Motion and interaction (keep it performant and never gratuitous): a kinetic hero headline
that settles on load (staggered word reveal); scroll-reveal fades and gentle parallax on
section entry; magnetic hover on primary buttons; the gallery cards lift with a soft shadow
and a subtle accent-edge glow on hover; an animated "draft -> review -> publish -> rollback"
flow in the governance section; a custom fine cursor accent on desktop (subtle, optional).
Respect prefers-reduced-motion.

Craft details that make it feel expensive: hairline dividers, precise 8px spacing rhythm,
soft large-radius cards on dark with 1px luminous borders, real focus states, buttery
easing (cubic-bezier, ~400-600ms), and pixel-clean alignment throughout. Fully responsive,
fast (lazy-load, no layout shift), and accessible (WCAG AA contrast, semantic HTML, keyboard
nav).

=== PAGE CONTENT (write all of it, in full, for Northlight Studio) ===

1. HERO. Oversized kinetic headline: "Your knowledge deserves an experience people trust."
Subhead: Northlight Studio takes you end to end - connecting the systems where your knowledge
already lives into one trusted, governed foundation, then into on-brand experiences your
people actually use. Cited, controlled, live in weeks. Primary CTA "Book a pilot", secondary
"See what's possible" (smooth-scrolls to the gallery). A small trust line beneath: "Every
answer cited. Every release reviewed."

2. THE GAP. A short, striking statement section. Write it as, in substance: your organisation
already has the knowledge - it lives scattered across the systems you already run. Turning
that into something people can actually trust and use, end to end, is the hard part: bringing
it into one governed foundation, grounding every answer in it, and delivering an experience
people rely on. That whole journey is what Northlight does. (Do NOT say the organisation
already has AI retrieval, a knowledge base, a vector index, or a working chatbot - they have
raw, scattered knowledge, nothing more. Do NOT use the word "front-end".)

3. END TO END - a clean three-part band making the scope explicit, one partner across the
whole journey:
   - Unify - connect your existing systems of truth (documents, drives, sites, apps,
     databases) into one governed knowledge foundation.
   - Ground - grounded, cited retrieval that reasons over that foundation and answers with
     sources.
   - Experience - the day-to-day experience your people rely on, on-brand and trustworthy.
   Tie it off: "One partner, end to end - from the systems where your knowledge lives to a
   product people trust."

4. LEAD USE CASE - a focused feature band above the gallery. Write a concrete Northlight
example: a member knowledge portal for a professional association, launched in two weeks -
Northlight connects the association's existing document stores and site content into one
foundation, then members ask questions in plain language and get answers cited to the
association's own standards and policies. Include a short outcome line. (This is the "lead
with one thing" moment.)

5. "WHAT YOU CAN BUILD" - the centrepiece gallery. A refined, interactive grid of ten
experience patterns, each a card with a crafted icon, a bold name, and one plain sentence.
Add an HTML comment telling the adapter to keep 5-6 that match their strengths and delete the
rest:
   - Cited answer portal - ask anything, every answer linked to its source.
   - Answer-quality desk - responses graded for how well they're grounded; weak answers held back.
   - Video and audio that answer - jump to the exact moment in a recording.
   - Photos into structured data - upload images, get clean structured detail back.
   - Operations console - incoming work classified, enriched and routed, human in control.
   - Explore by connections - navigate by people, topics and relationships, not just search.
   - Embedded assistant - a governed answer widget inside the site you already run.
   - Conversation analytics - mine calls and chats, click to jump to the moment.
   - Retrofit, don't rebuild - add intelligence to your existing CMS or store.
   - Multi-tenant workspaces - a separate branded workspace per client or team.

6. GOVERNANCE & TRUST - the differentiator, with the animated draft-to-publish flow. Copy:
drafts, review gates, releases and rollback; brand enforcement so nothing ships off-brand;
every claim cited to source. Headline: "AI you can put your name to."

7. HOW IT WORKS - four elegant steps: unify your systems of truth into one knowledge
foundation -> ground and retrieve with citations -> compose the governed experience ->
review and publish. Speed framed as a pilot outcome, not a guarantee: "a live, cited
experience in front of your stakeholders in weeks."

8. PROOF - a tasteful band with three short, clearly-illustrative outcome statements
attributed to fictional Northlight clients (make it obvious these are example outcomes, not
real testimonials).

9. PILOT CTA - a beautifully composed closing section with a contact form: name, work email,
team/role, and "what's your knowledge base?". Heading: "Start with one use case."

10. FOOTER - Northlight Studio wordmark, a "Built by Northlight Studio" line, tasteful nav,
and a neutral independence disclaimer (this is Northlight's own offering).

Deliver a single, complete, polished site. Prioritise visual excellence, typographic craft,
and smooth motion - it should make a viewer stop and say "who built this".
```

## The principle it enforces

Breadth on the page, focus in the sale. Section 3 leads with one use case; section 4 shows
the range; the keep-5-6-cards note stops a partner claiming ten things they cannot all do.
Range earns the meeting; focus closes it. The governance-and-trust section is the constant
differentiator that separates a real partner from a generic AI-page generator, and it stays
in for every partner.

## Provenance

The ten gallery patterns are the experience archetypes from the demo estate audit and
back-catalogue archaeology (August 2026) - each is a pattern the factory has a working demo
for, not a hypothetical. The "breadth on the page, focus in the sale" principle and the
one-feature-first doctrine come from the field persona interview
(`operating-inside-progress.md`).

## Change log
- **2026-08-13** - v2.2. GM correction (second pass): remove the word "front-end" entirely and
  frame the whole thing as the end-to-end experience; harden the no-retrieval rule so the
  downstream builder cannot amplify it into "vector indexes / retrieval pipelines / a chatbot
  that mostly works". Lesson: copy written into a generator prompt is rendered and often
  amplified verbatim - the literal claims in a prompt must be audited against the messaging
  house, especially implied-state claims about the customer.
- **2026-08-13** - v2.1. GM correction: the offering spans the full stack, not just
  front-ends. Added a SCOPE RULE and a "Full stack" band (Unify / Ground / Experience);
  rewrote THE GAP so it says organisations have the knowledge (scattered) but NOT that they
  already have AI retrieval or a unified foundation; broadened hero and How It Works to lead
  with connecting systems of truth into one foundation. Root cause of the original error: the
  v2 prompt's own GAP copy asserted the customer "already has the AI retrieval".
- **2026-08-13** - v2.0. Reworked per GM revision: tool-agnostic (not tied to any one builder), a
  finished page for a fictitious exemplar studio ("Northlight Studio") instead of
  placeholders, and a full premium design system specified in the prompt so the output is
  visually exceptional.
- **2026-08-13** - v1.0. First version (single-tool, placeholder-driven).
