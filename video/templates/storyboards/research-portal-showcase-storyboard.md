# The Research Portal - showcase film - SCRIPT + SHOT STORYBOARD

- Work item: cd4262f4cb474f9ea78af65c3a210137 "Research Portal demo showcase film"
- Source (real product footage): https://your-app.fly.dev/t/frdc-2 - the FRDC Knowledge Hub, a research-discovery app built on Progress Agentic RAG over the Fisheries Research and Development Corporation corpus.
- Audience: field and technical buyers evaluating Agentic RAG. Tone: confident, credible, calm - a product, not a hype reel.
- Voice: David (Australian male, ElevenLabs CFN1FeTIoSu4xm6mDCkI) - single narrator throughout. GM call (30 Aug): FRDC is an Australian research corporation, so the Australian read is right. eleven_multilingual_v2 for long-form stability.
- Australian/British English, no em dashes (spaced hyphen), no banned words, no political content. Numbers spelled as words in the TTS script.
- Music: original CC0 synth chord bed (scripts/music_bed.py, I-vi-IV-V), built with a slow upward volume envelope so it lifts under the narration, sidechain-ducked well below the voice. No licence risk.
- Supers: tasteful lower-third key phrases that name the ARAG mechanism at each capability beat. Full film carries supers, no burned captions; the 90s social cut carries captions instead.
- App theme: LIGHT mode (clean, credible register) bracketed by dark-navy Progress brand cards.

Runtime: full film 2:34; 90s social cut ~1:20 (scenes 1,2,3,7).

---

## CORPUS-SAFE FRAMING (binding steers from the GM - corpus is mid-ingest)

Nothing on screen reveals or implies a small/incomplete corpus. Every surface filmed was scrubbed for: Library grid, stat counters (170 resources / 155 reports), un-merchandised report cards, raw filenames, Processing badges, 0-count topics, and the sparse/duplicate knowledge graph. NONE appear in a single frame. Surfaces that could not be shown safely were dropped (see the two dropped beats below).

---

## BEAT 00 - TITLE (dark-navy Progress card) - ~11s

VO: "Decades of fisheries research. Written down, filed away, and rarely read again. This is what it looks like when that knowledge answers back."
On screen: "PROGRESS AGENTIC RAG / The Research Portal / Decades of research. Finally answerable."

## BEAT 01a - HERO, THE GROUNDED CITED ANSWER (live) - route /assistant - ~19s [SCENE 1]

Query typed on camera: "What is known about southern rock lobster growth and mortality rates?"
| On screen | VO | Value |
|---|---|---|
| New session opens clean. The question is typed. "Retrieving sources..." then the answer streams in with inline citations [1][2][3]. | "A research portal, built on Progress Agentic RAG, over the published reports of Australia's Fisheries Research and Development Corporation. Ask it a real research question, and it retrieves from those reports and writes the answer, citing each claim as it goes." | The money shot: grounded, cited, live. |
Super: GROUNDED AND CITED / Progress Agentic RAG retrieval and grounding

## BEAT 01b - MULTI-SOURCE + CURRENCY (still, hero punch) - ~21s [SCENE 2]

| On screen | VO | Value |
|---|---|---|
| Push in on "Sources: 4" - four named projects (1975-022, 1976-020, 1977-021, 1972-014) - the date range 1972-1977, and the honest currency caveat. | "This single answer was drawn from four separate research projects, spanning years of work, and each one named, so you can open it for yourself. It even tells you how current the evidence is. Honestly, when the most recent report is already decades old." | Reaches across the estate; honest about currency. |
Super: FOUR SOURCES, ONE ANSWER / reaching across the whole estate

## BEAT 01c - THE QUALITY SIGNAL (still, hero punch) - ~15s

| On screen | VO | Value |
|---|---|---|
| Push in on ANSWER QUALITY: Relevance 5.0/5, Groundedness 5.0/5, Context 3.0/5 (REMi), with the honest per-source verdicts behind it. | "And Progress Agentic RAG scores its own work. A groundedness rating, measured against the sources it actually retrieved, and a candid verdict on every one. A real measurement, never a made up number." | Trust you can measure. |
Super: A QUALITY SIGNAL / Progress Agentic RAG scores its own groundedness

## BEAT 02 - THE HONEST REFUSAL (still, hero punch) - route /assistant - ~26s [SCENE 3, the differentiator climax]

Query: "What is the best recipe for cooking southern rock lobster?" (clearly out of scope)
| On screen | VO | Value |
|---|---|---|
| Push in and hold on the "No direct evidence found" decline: "This portal's content does not hold enough relevant material to answer this confidently..." | "The most important answer a research tool can give is the one it refuses to invent. Ask it something the reports do not cover, and it does not improvise. It says, plainly, that the portal's content does not hold enough relevant material to answer with confidence, and points you back to what it does cover. Progress Agentic RAG is built to know the edge of its own knowledge." | Almost no competitor demos a refusal. The climax. |
Super: HONEST BY DESIGN / Progress Agentic RAG grounded refusal

## BEAT 03 - REAL RESEARCH MADE USABLE (live) - route /generate - ~26s

| On screen | VO | Value |
|---|---|---|
| Briefing tab, "Brief me on Carp Control" chip, Generate. A structured briefing renders and scrolls: overview, KEY TAKEAWAYS, sections, GROUNDED IN 1 SOURCE (Project 1981-077), currency note, Export to Word / PDF. | "And the raw research becomes something you can use. Ask for a briefing, and Progress Agentic RAG synthesises one, grounded in the reports themselves. An overview, the key takeaways, and the detail beneath. Every line drawn from the source, with the source named, and ready to export to a document you can carry into the room." | Raw reports become an answerable, exportable artifact. |
Super: GENERATIVE SYNTHESIS / Progress Agentic RAG grounded generation

## BEAT 04 - THE ENGINE (dark-navy Progress card) - ~21s

VO: "None of this is bolted on afterwards. The retrieval and grounding, the citations, the quality signal, the knowledge graph, and the honest refusal. They are all Progress Agentic RAG, working over your own content, and every one of them is configurable to what your organisation needs."
On screen: "Built on Progress Agentic RAG / One engine, underneath" + the five mechanisms. (The one card that carries heavier ARAG branding, per the brief.)

## BEAT 05 - CTA (dark-navy Progress card) - ~10s [SCENE 7]

VO: "Decades of research. Fast, credible, and finally usable. The Research Portal, built on Progress Agentic RAG."
On screen: "Fast, credible, and finally usable. / The Research Portal. Built on Progress Agentic RAG."

---

## 90-SECOND SOCIAL CUT (captioned)

Scenes 1,2,3,7 = beats 01a + 01b + 01c + 02 (refusal) + a standalone CTA card. Burned captions (Progress Sans Text), same ducked music bed.

---

## DROPPED FROM THIS DRAFT (with reasons - both are re-shoot candidates once the corpus completes)

1. **Knowledge graph "explore" beat.** The /graph knowledge map is re-extracting live while the corpus ingests - its entities and dominant cluster changed on every load (coralline algae -> ciguatera/CTX -> prawns/mussels within one session), each load carrying fresh singular/plural duplicates (sand crab / sand crabs, prawns / prawn). Not reproducible or duplicate-free enough to film to a broadcast standard right now, and the GM's steer forbids showing the sparse/duplicate graph. The knowledge graph is still credited on the engine card and in the VO. Natural beat to add on the recut.
2. **A dedicated carp multi-source Q&A beat.** The modern carp questions ("National Carp Control Plan", "CyHV-3 biocontrol") REFUSE against this historical corpus. Carp is still present via the Generate briefing (Beat 03, grounded in the 1981 study). The rock-lobster hero already demonstrates multi-source (four named sources).

## HONESTY NOTE ON "FAST" (message 2)

The live app currently takes ~15-30s per answer, so no on-screen or spoken "~2 second" speed claim is made. The real streaming is shown (Beat 01a) and "fast" appears only in the client's chosen CTA tagline. Flagged to the lead.
