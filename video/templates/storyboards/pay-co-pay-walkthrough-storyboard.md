# Pay-co Pay - narrated walkthrough - SCRIPT + SHOT STORYBOARD

- Work item: 02f996f2 "Fintech RAG Demo for UK Market"
- Source (real product footage): https://your-app.fly.dev - genuine ARAG-powered app, QA-clean
- Audience: UK fintech - CIO (primary), Solutions Architect (secondary). Tone: confident.
- Voice: Daniel (British male, "Steady Broadcaster", ElevenLabs premade onwK4e9ZLuTAKqWW03F9) - single voice throughout.
- Length target: 5min+. Estimated ~5:10 of narration.
- British English, no em dashes, no banned words, no political content. AU-sandboxed synthetic KB serving a UK story.
- Numbers spelled as words in the TTS script (v3 has no normalisation); shown as digits here for readability.

Music: light, ducked, royalty-free / CC0 bed, documented in the DoP cert. Captions: OFF on the full walkthrough (clean CIO/SA piece); a 60-90s captioned social cut is the standard second deliverable - proposed, awaiting your call.

---

## BEAT A - COMPLIANCE CONSOLE (HERO, the hook) - route /compliance-console - ~85s

Query used: "What is the threshold for filing a Suspicious Activity Report, and who can approve it?"
Shown twice: as Support Agent (honest decline), then Compliance Officer (full cited answer).

| Sub | On screen / crop | VO line (exact) | Value |
|---|---|---|---|
| A1 hook | Console loads, role set to Support Agent. Type the SAR question on camera. | "Here is the same governance question, asked twice. A support agent asks it first." | Open on the money shot, no throat-clearing. |
| A2 | Support Agent answer returns: an honest decline. PUSH IN on the decline panel, hold. | "And Pay-co Pay's assistant declines. It will not show this agent something their role is not entitled to see." | The refusal is the proof, held. |
| A3 problem | Switch the role control to Compliance Officer. Re-ask the identical question. | "Now the very same question, asked by a compliance officer. For a bank, the difference between those two answers is everything." | The failure mode a CIO recognises. |
| A4 | Compliance Officer answer streams in: full, cited to the policy. PUSH IN on the cited answer + citation chip, hold. | "This time, the full answer, cited to the policy it came from. Two roles, one question, genuinely different content." | The differentiated result. |
| A5 capability | Pull back to the whole console. | "This is not a curtain drawn over one answer. The same question is sent to Progress Agentic RAG twice, each time scoped, inside the retrieval itself, to what that role may draw on. The restricted answer is never generated for the role that should not see it, and every citation is re-checked server side before it is shown." | How it actually works, honest to the mechanism. |

Anchor: A4 answer-stream landing -> phrase "the full answer, cited to the policy".

---

## BEAT B - INTERNAL SEARCH - route /internal-search - ~42s

Query: "What is the maximum working-from-abroad allowance in days per year?"

| Sub | On screen / crop | VO line | Value |
|---|---|---|---|
| B1 | Internal Search view. Type the question on camera. | "Away from governance, this is the question every operations handler asks a dozen times a day. What does the policy actually say." | Everyday grounded search. |
| B2 | Cited answer streams in. PUSH IN on the answer + citation. | "A grounded answer over Pay-co Pay's own internal policies and runbooks, with the exact clause cited. Not a half-remembered summary from a colleague, and not a confident guess at the handbook." | Cited to the real document. |

Anchor: B2 answer landing -> phrase "A grounded answer over".

---

## BEAT C - SUPPORT ASSISTANT (honesty beat) - route /support-assistant - ~52s

Query: "Why was my card payment declined?"

| Sub | On screen / crop | VO line | Value |
|---|---|---|---|
| C1 | Support Assistant view. The disclosed-fallback banner is on screen, visible, before any ask. Hold on the banner briefly. | "The support assistant answers a real customer question from Pay-co Pay's own published help centre. And it is honest about exactly how it does that today." | Sets up the disclosure plainly. |
| C2 | Push in on the banner text. | "In a live product this would run as Progress Agentic RAG's own retrieval agent. That live agent is currently blocked by a platform issue, so the app orchestrates the same underlying grounded call instead, and says so, here, on screen." | Names the gap, no overclaim. |
| C3 | Type the question. Cited answer streams in. Push in on answer + citation. | "The retrieval and the grounding are genuinely ARAG. The answer is drawn from the real help material, cited, and honest when the help centre does not cover it." | Real ARAG retrieval, disclosed. |

Note: never imply a live autonomous agent ran. VO says "the app orchestrates the same underlying grounded call" - matches the on-screen banner.
Anchor: C3 answer landing -> phrase "drawn from the real help material".

---

## BEAT D - AUDIT TRAIL (trust you can measure) - route /audit-trail - ~58s

Query: "What is the standard per-transaction limit for Instant Transfers on a personal account?"

| Sub | On screen / crop | VO line | Value |
|---|---|---|---|
| D1 | Audit Trail view. Ask the question. Cited answer returns. | "Audit Trail proves an answer is grounded, not guessed, and does it with two things an audit function actually needs." | Frames the two proofs. |
| D2 | REMi trust panel renders/scores. PUSH IN on the REMi chart, hold. | "First, a real trust score. This is REMi, Progress Agentic RAG's own quality signal, scoring the answer against the full context that was retrieved. A genuine measurement, never a made-up accuracy figure." | Measurable trust, real REMi. |
| D3 | Click a citation. The real source opens and the exact passage is highlighted. PUSH IN on the highlighted passage. | "Second, every citation opens the exact source passage it came from. Click it, and you land on the real document, with the grounding passage highlighted." | Citation click-through to source. |

Anchors: D2 REMi render -> phrase "a real trust score"; D3 citation highlight -> phrase "the grounding passage highlighted".

---

## BEAT E - FRAUD REVIEW (grounded-only discipline) - route /fraud-review - ~52s

Open CASE-0142 (flagged, quoted structuring pattern) then CASE-0143 (clean, no red flags).

| Sub | On screen / crop | VO line | Value |
|---|---|---|---|
| E1 | Fraud Review case list. Open CASE-0142. Grounded red-flag result renders. PUSH IN on the quoted red flag. | "Fraud Review shows the discipline that matters most on a fraud desk. Open a genuinely suspicious case, and the real evidence is surfaced and quoted, in the analyst's own words, from that case's own file." | Grounded, quoted evidence. |
| E2 | Open CASE-0143. Result reports clean, no red flags. PUSH IN on the clean result. | "Open a genuinely clean case, and it is reported clean. No invented red flag to look thorough. An AI reviewer that never manufactures a finding the file does not support." | The honest negative, the hard part. |

Anchor: E1 case answer landing -> phrase "surfaced and quoted".

---

## BEAT F - DEPLOYMENT / "run where your data lives" - branded capability card (NOT app footage) - ~20s

Brief must_show: "run where the data must live, flexible deployment options." Stated platform capability, KB-verified (nuclia.com/nuclia-deployment-options), decoupled from the AU sandbox footage - no faked on-prem screens.

| On screen | VO line | Value |
|---|---|---|
| Branded Progress Agentic RAG capability card listing the three deployment options (Cloud EU/US, Hybrid with local storage, On-premises / air-gapped). No app footage. | "One more thing a fintech team has to ask of any AI system. Where does our data actually live. Because this is Progress Agentic RAG, the answer is wherever it must. Run it in EU or US cloud, run it hybrid with the data held in your own storage, or run it fully on premises, even air gapped. The capability moves to the data. The data never has to move to it." | Data-residency / deployment flexibility, honest stated capability. |

KB facts: Cloud = Europe or USA; Hybrid = processing in Nuclia cloud, storage in your own local NucliaDB; On-premise = full pipeline + generative model in your own infrastructure, air-gapped supported.

---

## CTA - branded end card - ~20s

| On screen | VO line |
|---|---|
| Progress Agentic RAG branded end card. | "Every answer you just saw was either a genuine ARAG mechanism at work, or an honestly disclosed gap. Grounded, cited, and governed where it counts. Discover how Progress Agentic RAG can transform your fintech operations today." |

---

## Build notes
- Keep the app's on-screen "Demonstration data" synthetic-sandbox banner VISIBLE in all footage - never crop it (residency-sensitive fintech piece).
- record_demo.py with --warmup (no media playback in this app, screen capture is clean). Type steps with delay for on-camera typing. Scroll destinations strictly increasing; gate any post-answer scroll on the answer selector.
- Per-beat segments with anchors (build_pugtube_video.py pattern) for sync; re-measure every `at` from the recorded clips.
- QA: per-beat sync gap in the finished file, LUFS -14, stereo 48k, no white-screen head, view frames at each proof beat, leak scan with selftest.
