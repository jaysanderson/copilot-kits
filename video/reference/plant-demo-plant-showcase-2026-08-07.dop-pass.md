# DoP certificate - Plant-demo Plant manufacturing showcase video

| | |
|---|---|
| **Artifact (long cut)** | `videos/plant-demo-plant-showcase-2026-08-07.mp4` |
| **Artifact (social cut)** | `videos/plant-demo-plant-showcase-social-2026-08-07.mp4` |
| **DAM work item** | `b571efa1ed1c4187b1010dc603a3950c` - "Progress Agentic RAG for Manufacturing Systems" |
| **DoP version** | v1, 31 Jul 2026 |
| **Certified** | 2026-08-07 |
| **Producer** | video-producer (this agent) - certification carried by the producer, not relayed |
| **Source app** | `https://your-app.fly.dev/` - routes `/quality?demo=1`, `/ap-invoices?demo=1`, `/ctp?demo=1` |
| **Build script** | `scripts/build_plant-demo_video.py`, narration `videos/plant-demo-work/narration.json` |
| **Voice** | `hope` (single narrator) |
| **Delivered** | DAM asset `0ea225d0c6594b1bb4e3bc709be59493`, status `in_review`, via the sanctioned `submit-file` route. Integrity verified after delivery, not assumed: `stored_size` 54,804,230 bytes and sha256 `3db1dbb6…c072d945` both match the local file exactly, and the DAM independently parsed the duration as 6:55 |

## Rev 2 (2026-08-08) - Jay's revision: "Remove subtitles"

Jay reviewed the delivered captioned cut and kicked the work item back with `decision_note: "Remove subtitles"` - a taste/format call, not a defect (the captions themselves were in sync, tag-clean and DoP-PASS per the table below; he simply doesn't want burned-in text on this piece). Rebuilt via `python scripts/build_plant-demo_video.py --assemble --out videos/plant-demo-plant-showcase-2026-08-08.mp4` (no `--captions` flag) from the same cached segments/audio, so nothing else about the cut changed - same 12 beats, same anchors, same hero treatment, same 415.0s (6:55) runtime, same -18.0 LUFS pre-normalisation input.

**Verification (not assumed from the flag alone):**
- `ffprobe` duration 415.000000s, audio 48000Hz stereo - matches the captioned version exactly.
- Two frames extracted and viewed directly (40s into b02-problem; mid-render at 200s during a hero punch-out) - no caption plate, no residual band artifact at the bottom margin where the plate used to sit.
- File size 53,006,232 bytes (vs 54,804,230 captioned - the ~1.8MB difference is consistent with dropping the caption alpha-strip overlay, nothing else).

**Table line updated:** "Captions burned, in sync, no dangling separators" changes from **PASS** to **N/A - removed per Jay's explicit 2026-08-08 direction**. This is a GM override of a prior PASS, not a re-grade of the captions themselves - the original caption implementation is not in question and the fix (`captions.py`'s bracket-tag stripping) stays in the pipeline for whenever captions are wanted again.

**Not yet touched:** the social cut (`plant-demo-plant-showcase-social-2026-08-07.mp4`) still carries burned captions and was never delivered (Jay's routing call - new work item vs. existing - is still pending). If/when the social cut ships, it should go out without captions too unless Jay says otherwise for that piece specifically, since his direction reads as a preference for this video's presentation, not a one-off edit request.

**Generalizable lesson (hard rule 11):** burned-in captions were previously a fixed default of every long-form showcase build (`--captions` was habitually passed). Jay's kickback shows that's a per-video creative call, not a blanket standard - the pipeline supports both (`assemble(captions=False)` already existed, wasn't a new capability), but the *convention* of always burning them by default wasn't. Encoded in `.claude/skills/video-production/SKILL.md` this session: ask/default toward no-captions-by-default is not right either - the right fix is treating captions as a per-brief choice to confirm rather than an unstated default baked into the build command.

**Verdict: PASS.** No FAIL on any blocking line.

---

## 1. Truth gates

| Line | Verdict | Evidence |
|---|---|---|
| Every ARAG product claim traces to the `nuclia-mcp` KB | **PASS** | Four claims, four queries, run this session - see "KB verification" below |
| No fabricated numbers | **PASS** | Every figure spoken in narration was read off live app footage captured 2026-08-07, not from memory or estimate. Full list under "Figures" below; each was verified twice - once in the live Playwright capture, once in an extracted frame of the finished render |
| Demo figures labelled as demo figures | **PASS** | The app's own footer, visible in frames throughout, reads "Demonstration environment - all companies, people, parts, lots and figures are synthetic." Narration never presents any figure as measured product performance |
| No invented accuracy %, adoption %, ROI or benchmark | **PASS** | None present. No accuracy claim of any kind is made about ARAG; answer quality is shown, not asserted - the cited ranking, the evidence panel and the tool-call trace are the proof |
| Certifications named only if verified outside the KB | **PASS** | No certification (SOC 2 / ISO / PIPEDA) is named anywhere |
| Locked facts hold everywhere | **PASS (scoped)** | This work item is a product showcase over an existing demo build, not an account kit, so there is no `account-brief.md` to bind to. The binding source is the live app; the social cut is cut from the same rendered segments as the long cut, so its figures are identical by construction, not by re-entry |
| Statistics: authoritative independent sources, cited | **PASS (N/A)** | No third-party statistic, market size or analyst figure appears in either cut |
| All pricing in USD | **PASS (judgement, flagged)** | No product, licence or competitor pricing appears anywhere. The only dollar figures on screen are synthetic AP invoice amounts inside the demo dataset ($50,692.35 stuck, $23,782.80 batch, $2,140.50 invoice, $5,000.00 policy limit). These are transactional amounts in a fictional plant's ledger, not pricing of anything being sold, and carry no geo-localised currency marker. Flagged here rather than silently passed |
| Cross-artifact consistency | **PASS** | Both cuts share segments `b01-hook` and `b07-ctp` byte-for-byte; the social CTA introduces no figures |
| Screenshot-currency check | **PASS** | Nothing reused. Every frame in both cuts is from recordings made 2026-08-07 against the live app; no shot was taken from `shots/presentation-library/` (checked first per the 5 Aug directive - the library holds no Plant-demo quality/AP/CTP agent-trace shots, and this piece needs moving footage of the live agent regardless) |

### KB verification (hard rule 3)

Four product-level claims are made. Each was checked against `nuclia-mcp` this session:

1. **"Semantic search for meaning, keyword search for precision, and a knowledge graph over the entities pulled out of the content"** - query: *knowledge graph entity relation extraction hybrid semantic and keyword search structured unstructured data ingestion*. KB returned: "NucliaDB unifies semantic search, keyword search, metadata search, knowledge graph traversal, and multi-modal understanding" (`nuclia.com/rag-database/`), and "Nuclia's Graph Extraction Agent... ingests unstructured content and automatically extracts entities and their relationships, forming custom knowledge graphs".
2. **"The Retrieval Agent... plans its own sequence of lookups, calls tools against the plant's live systems over MCP"** - queries: *Retrieval Agent MCP driver Smart Agent planning reactive mode tool calls* and *MCP Model Context Protocol server tools agent Nuclia retrieval agent*. KB returned the Retrieval Agent context API (`POST /kb/{kbid}/agent/context`) whose `module` enum literally includes `mcp` alongside `sql`, `sparql`, `cypher`, `ask` etc., plus "Task-Specific Agents like Ingestion and Retrieval agents, and Multi-Step Agents".
3. **"Every answer has to show its work - which systems were consulted, which tool calls were made, which record each number came from"** - same first query. KB returned the reasoning-transparency passage: "which tool decided to call, what query it used, what result came back... before it produced the final answer. This transparency is critical for debugging agents and building trust with end users... All these steps are auditable."
4. **"One retrieval layer over structured records and unstructured content in the same index"** - covered by query 1: "knowledge graphs provide a structured foundation... This allows for deep data exploration and discovery of complex relationships within both structured and unstructured data."

No claim is made that the KB could not confirm. Nothing was asserted from memory.

### Figures spoken in narration (all read off live footage)

Quality: RUN-1111; FPY 84.3% against a 96.5% target; 66 affected units; lot KP-7742 with 3 defect records accounting for 47 of 66 units; asset INJ-01 service overdue with 1 open work order and 19 units; 1 operator rostered, ranked LOW.
Dashboard: 11 open production runs, 10 open defects, 5 quality holds, 4 supplier delays.
AP: 23 invoices failed to post, $50,692.35 stuck; 9 share cause GL-4102 totalling $23,782.80; 1 needs escalation beyond the AP clerk.
CTP: 250 units requested; commit date 2026-08-12; short 170 units; incoming PO 2,600 units due 2026-08-10; warehouse physical count agrees with book; other orders need 3,000; headroom minus 570, CONFLICT.

---

## 2. Safety and hygiene gates

| Line | Verdict | Evidence |
|---|---|---|
| No secrets, keys or tokens in the artifact | **PASS** | No credential appears in any frame. The Playwright storage state used for recording is `brand/plant-demo.auth.json`, which matches the gitignored `*.auth.json` pattern (confirmed against `.gitignore` line 7) and is never rendered |
| Outputs not committed to git | **PASS** | The factory root is not a git repository; `videos/` is a working directory and delivery is via the DAM (hard rule 12) |
| No hosting-region / infra string visible | **PASS** | `scripts/`-driven scan of the rendered visible text of all four routes while signed in returned **zero** hits against `aws-*`, `ap-southeast`, `us-east-`, `eu-west`, `sydney`, `frankfurt`, `ireland`, `nuclia.cloud`, `rag.progress.cloud`, `europe-west`. Independently confirmed by eye on every extracted frame viewed below - the only infra-adjacent strings on screen are the app's own relative endpoints (`/api/runs/`, `/mcp/cmms`, `/mcp/workforce`), which carry no host or region |
| Other customers' names and identifiers anonymised | **PASS** | Every company on screen is synthetic and part of the demo seed (Ellandra Motors, Southbank Truck Group, Marran Automotive, Korrawin Assemblies, Torrens Trade Parts, Coalcliff Steel, Meander Castings, Halcyon Chemicals, Ridgway Packaging, Warrigal Fasteners, Operator Polymers, Torren Bearings, Larkspur Electronics, Bellbrook Gauge & Rig). No real customer appears |
| No real personal identifiers | **PASS** | The signed-in user is the demo account "Avery Chen / admin"; the only person referenced in narration is employee code TC1027, a synthetic roster entry. Narration deliberately does not name the operator, and the beat is about the system declining to blame them |
| Discreet synthetic disclosure | **PASS** | App footer states the environment is synthetic; visible in frames at 5.9s, 259.3s, 329.7s and 361.5s among others. It is a footer, never the headline |
| Outbound requires GM sign-off | **PASS (N/A)** | Delivery is DAM submission for review, not publication. Nothing is posted outbound by this job |

---

## 3. Language and voice gates

| Line | Verdict | Evidence |
|---|---|---|
| Australian English | **PASS** | Programmatic scan of the full narration (1,050 words) found zero US spellings across `optimize/analyze/center/organiz/color/labeled`. "optimise", "centre", "moulding", "per cent" used throughout |
| No em dashes | **PASS** | Scan counted 0 em dashes (U+2014) and 0 en dashes (U+2013) in narration; card copy scan clean. Spaced hyphens used |
| Banned words absent | **PASS** | Scan for delve / leverage / unlock / seamless / game-changing across narration and card copy: 0 occurrences of each |
| De-AI pass | **PASS** | Opens on a claim, not a hedge ("Overnight, line A two fell below its first pass yield target"), with no "in today's fast-paced" framing anywhere. No symmetrical triads used as filler; the one list of three ("Quality, accounts payable, and a delivery promise") is the literal set of use cases shown. Concessions are concrete, not hedges |
| The room test | **PASS** | The technical spine is verifiable on screen by a Solutions Architect: named tool functions, HTTP verbs, real endpoints, an elapsed clock, and a cited evidence panel. The narrative spine is legible to a plant manager: three jobs, three answers, one of which declines to blame a person |

---

## 4. Per-type gates - Video (Workflow 3)

| Line | Verdict | Evidence |
|---|---|---|
| Script shown to Jay and approved before recording | **N/A - SUPERSEDED** | Superseded by the GM directive of 31 Jul 2026 ("Don't gate on chat approval"), which names this exact Workflow 3 hard stop: script quality is judged at DAM review time. Recorded here rather than passed silently |
| Narration timed to the walkthrough | **PASS** | Not just timed - anchored. Every demo beat declares the narration phrase that must land on a named on-screen event, with an explicitly measured event time; see the sync table below |
| Claims KB-verified | **PASS** | Section 1 |
| Playback duration against script timing | **PASS** | Long cut 415.0s (6:55) against a brief target of "5 min+". Sum of the twelve narration tracks is 408.4s; the 11 crossfades reclaim 5.5s and the render is 415.0s, consistent to within a frame |
| Frames viewed at start, middle and end | **PASS** | Viewed, not sampled blind - see the frame log below |
| Frame viewed at the moment narration names each proof beat | **PASS** | All five anchored claims checked individually - see the frame log |
| Residency string cropped or neutralised | **PASS** | Section 2 - none present, so nothing needed cropping |

### Per-beat sync (screen must lead voice by 0 to 3.5s)

Measured, not assumed. Event times come from `scripts/plant-demo_events.py`, a luminance-jump detector written for this build: the live-agent modal dims the page behind it, so the answer landing is an unambiguous brightening. Auto-detection was **not** used - the largest frame delta in these clips is the modal's own scrolling tool-call list, not the landing the narration claims. Each anchor is pinned to the phrase that **proves** the claim, never one that merely cues it.

| Beat | Anchor phrase (the claim) | Event in clip | Trim | Lands at | Voice says | Gap |
|---|---|---|---|---|---|---|
| b01-hook | "Here is the ranked root cause" | 34.5s | 29.6s | 4.9s | 5.9s | **+1.0s** |
| b04-agent | "Then the answer lands" | 29.2s | 2.0s | 27.2s | 28.2s | **+1.0s** |
| b05-media | "Supporting media, pulled from the same Knowledge Box" | 53.5s | 50.2s | 3.3s | 4.3s | **+1.0s** |
| b06-ap | "It traces the failure back along the chain" | 29.2s | 16.5s | 12.7s | 13.7s | **+1.0s** |
| b07-ctp | "Commit date, the twelfth of August" | 27.2s | 10.1s | 17.1s | 18.1s | **+1.0s** |

Note on b05-media: its anchored event is deliberately a **scroll settle**, not an answer landing. The claim is that the Knowledge Box media strip is on screen, and that only becomes true after the page scrolls to it (the answer itself lands at 35.25s in that clip). Recorded in the beat so a landing-detector guard does not read it as a mismatch.

All five inside the 0 to 3.5s window. Verified two ways, independently: by viewing the actual frame at each claim's spoken time in the finished render (below), **and** by `scripts/plant-demo_verify_sync.py`, which re-measures each landing inside its own window of the rendered file and prints the gap - not inferred from the trim arithmetic, which is exactly what failed to catch defect 5.

### Frame log (all viewed, not sampled blind)

Claim moments in the final render: 5.9s (ranked root cause on screen - Material TOP SUSPECT, Equipment HIGH, Shift LOW all visible), 163.0s (answer landed, RUN-1111 / 84.3% / 66 units on screen), 204.5s ("SUPPORTING MEDIA FROM THE KNOWLEDGE BOX" with all four thumbnails and the manual link on screen), 259.3s (failure chain INVOICE to VENDOR MASTER CC-410 closed to GL VALIDATION GL-4102 to POSTING blocked on screen), 329.7s (COMMIT DATE 2026-08-12 on screen).

Hero reveals, each viewed after its 0.6s fade completes: 15.7s shift card, 175.5s material card, 222.8s Knowledge Box media strip, 261.8s AP failure chain, 295.8s AP metrics row, 361.5s order-priority conflict panel showing "Headroom -570 CONFLICT". A first pass sampled three of these mid-fade and had to be re-extracted after the fade - a partially faded punch-out reads as a ghosted double image and would have been mis-reported as a defect.

Also viewed on the final render: 315.0s, confirming the corrected CTP beat now opens on the live agent modal ("Checking capable-to-promise... all in parallel", 7.8s on the clock) while the narration sets up the question - the state that defect 5 had replaced with an already-settled answer. Start (1.5s), end (414.0s, CTA card), a capability card (80s), and social cut start / middle / end all viewed. Frames retained at `videos/plant-demo-work/final-frames/`.

### Additional video gates from the `video-production` skill

| Line | Verdict | Evidence |
|---|---|---|
| Narrative arc, not a route tour | **PASS** | Hook (the agent declining to blame the night shift) / problem / three capability cards / four proof beats / integration / CTA. The three briefed routes are not walked in brief order or given equal treatment; the hook is the sharpest line in the piece, not the safest |
| Hero-beat treatment on proof moments | **PASS** | Six punch-outs with dim, blur and a Progress-green cutout, each region measured on a real extracted frame **after that beat's own scroll had settled**, each reveal timed past the end of any scroll inside the beat |
| Every segment leaves with audio and video the same length | **PASS** | `apad` in both segment builders; verified per segment with separate `-select_streams v` / `-select_streams a` probes. Twelve segments, maximum divergence 0.033s (one frame at 30fps) |
| Recorded with `--warmup` | **PASS** | All seven recordings used `--warmup`; no white-screen head in any clip (frame at 1.5s viewed) |
| Cursor visible | **PASS** | `record_demo.py` default DOM cursor present; visible in frames at 5.9s, 163.0s, 259.3s |
| Captions burned, in sync, no dangling separators | **PASS** | 172 cues. Programmatic scan across all twelve beats: 0 tag leaks, 0 cues ending on a dangling separator, 0 empty cues. Caption offsets account for xfade (beat *i* starts at `sum(durs[:i]) - i * 0.5`), confirmed by the caption reading exactly the expected sentence at each of the five sampled claim times |
| ElevenLabs v3 bracket tags not spoken or burned | **PASS** | All twelve beats carry v3 audio tags. `silencedetect` on the head shows a real 1.84s gap at 3.96s where the first `[pause]` sits - the tag is interpreted, not read aloud. Caption scan (above) confirms no `[` or `]` reached the plate |
| Two-cut rule | **PASS** | Long cut 415.0s (6:55) plus a captioned social cut at **67.8s**, inside the 60-90s window. Built from the same rendered segments, not a re-record: the hook in full, then the CTP beat sliced at a sentence boundary ("But look at the last panel", 35.3s in) so the conflict payoff and its hero reveal survive without the set-up the hook has already done, then a CTA written to stand alone. Caption alignments are shifted by the same offset so they stay on the words. Social cut also measures **-14.0 LUFS**, stereo 48k, 26 cues, no silence at t=0 |
| No stock footage, no AI-generated imagery | **PASS** | Every moving frame is Playwright recording of the live app. The five cards are Pillow-rendered from Progress brand tokens in `build_plant-demo_video.py`. Nothing sourced, nothing generated |
| Loudness and format | **PASS** | Integrated **-14.0 LUFS** (target -14 +/- 0.5), LRA 3.9 LU, 1920x1080, 30fps, AAC stereo 48 kHz |
| No silence at t=0 | **PASS** | `silencedetect -50dB` over the first 12s: first silence starts at 3.96s. Head is clean |

### Brand compliance

| Line | Verdict | Evidence |
|---|---|---|
| Progress palette | **PASS** | Cards use Blue P1 `#00216B` ground, Progress Green `#5CE500` rules/bullets/hero cutout, Light Green S4 `#CDFFCA` eyebrow - the documented AA-verified pairing on the blue hero background |
| Progress Sans, Display for headlines and Text for body/captions | **PASS** | Font resolution checked directly, no silent Arial fallback: Display Bd/Rg and Text Bd/Rg all resolve to `/Library/Fonts/Managed/ProgressSans*`. Confirmed visually on the rendered cards |

---

## 5. Defects found and fixed during this build

1. **CTP beat would have shipped with 9.5s of frozen padding.** After anchor trim the first CTP take left 47.2s of footage against 56.7s of narration, so `demo_segment_hero` would have `tpad`-cloned a still frame for the last 9.5s. Caught by budgeting footage against audio **before** assembling rather than after. Fixed by re-recording the clip with a longer tail hold (the skill's "record generously so there is head to trim", applied to the tail). The re-take also landed 13.8s faster than the first (27.2s vs 41.0s), which is exactly the run-to-run variance the anchor mechanism exists to absorb - `at` was re-measured on the new take rather than carried over.
2. **Two hero punch-outs were clipped flush against the frame edge.** The AP failure-chain and AP metrics regions both centre to a negative x at their punch scale, and the original clamp pinned them to `x=0`, cutting the border off the first card in each. Fixed by adding `HERO_MARGIN = 26` and capping the punch scale so the enlarged panel always fits inside the margin. This is a general fix in the shared hero code path, not a per-region nudge, so it cannot recur silently on a future region.
3. **The Knowledge Box media hero cropped the operation-manual link.** Region height 195px cut the descenders off `om-inj-01-operation-manual.md` at the bottom border. Extended to 208px and re-verified on the rebuilt render.
4. **The CTP beat's anchor still held the previous take's event time - the most serious defect in this build, and it survived a frame spot-check.** After re-recording the CTP clip (defect 1), its `at` was left at the first take's landing of 41.0s while the new take lands at 27.2s. Nothing complained: the trim table printed a plausible row, the segment built, and the claim frame at 329.7s **passed** its check, because once an answer lands it stays on screen, so "is the thing being named actually visible" was still true. What was wrong was the gap - the answer appeared **14.8s before** the narration named it, so a quarter of the beat narrated the question being asked over a screen that already showed the answer. Caught by writing a guard that re-derives every anchor event from the clips currently on disk and diffs it against what `narration.json` declares. Fixed by re-measuring (`at` 41.0 to 27.2) and rebuilding, and permanently by `scripts/plant-demo_verify_sync.py`, which measures the gap in the finished file rather than trusting declared constants. Both the trap and the two rules that fall out of it (a re-record invalidates every measured constant tied to that clip; verify sync in the render, not the arithmetic) are now written into the `video-production` skill.
5. **Anchor auto-detection would have picked the wrong event on every beat.** Not a defect that shipped - a trap avoided by design. The largest frame delta in these clips is the live-agent modal's own scrolling tool-call list, not the answer landing. Rather than trust it, `scripts/plant-demo_events.py` measures the landing as a luminance jump (the modal dims the page, so its dismissal is a ~99-unit brightening), which is deterministic and directly measures the narrated event. Every anchor carries an explicit `at`.

## 6. Known limitations (disclosed, not defects)

- **The settled quality answer appears in two beats.** The hook opens on it and the proof beat replays it with the live agent trace leading in. This is a deliberate cold-open-then-payoff structure, with ~110s and a different hero region between the two.
- **All plant data is synthetic.** Disclosed in the app's own footer, which is on screen throughout. No claim in either cut depends on the data being real; the claims are about how the answer was reached.
- **Agent run times vary between takes** (21.5s to 35.4s observed across six recordings of the same three flows). The anchors normalise this per take, but any re-record needs `at` re-measured with `scripts/plant-demo_events.py` - the values in `narration.json` are specific to the clips in `videos/plant-demo-work/`.
- **The integration card describes only what the footage proves.** It states that the app publishes MCP tools and holds the Knowledge Box credential server side, and that ARAG's Retrieval Agent is the client. It deliberately does **not** claim JWT-forwarded RBAC scoping for this specific app, because that was not observable in the recorded session - the `rao-workflow` pattern documents it, but an unobserved specific was not worth asserting.
- **The brief's CTA is rendered in Australian English** ("optimise" rather than the brief's "optimize"), per hard rule 2. Wording is otherwise the brief's own.
