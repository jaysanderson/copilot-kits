# Fin-demo showcase film - RESUME

**Status: PAUSED 16 Oct 2026 by Jay.** Not a quality decision. Jay reviewed every video
project and picked one to continue (the research portal films); everything else stopped,
this included. The work was mid-way through a ten-item fix pass. Nothing here is broken.

This file exists so someone with no context can pick it up cold. Read it before touching
anything in `fin-demo-showcase/` or `videos/fin-demo-*`.

---

## 1. Frozen state - do not overwrite

Three copies of the delivered film, all byte-identical, md5 `88cc37155ca64505b8c93252445df167`:

| path | mtime |
|---|---|
| `fin-demo-showcase/renders/fin-demo-showcase_2026-10-16_22-06-34.mp4` | 22:10:51 |
| `videos/fin-demo-showcase-progress-rebuild-2026-10-16.mp4` (delivery path) | 22:14:51 |
| `videos/fin-demo-showcase-progress-rebuild-2026-10-16__88cc3715.mp4` (content-identified) | 22:16:32 |

177.533s, 5326 frames, 1920x1080 at 30, AAC stereo 48k, -16.4 LUFS, -3.9 dBTP.

**The independent viewer's walk (`videos/fin-demo-viewer2-report.md`) is dated to that md5.**
Every finding below is a finding about that file. Re-render and the report stops describing
the artifact.

Pre-built and untouched, all matching that md5:
- `videos/fin-demo-showcase-progress-rebuild-2026-10-16.dop-pass.md` (3,785 bytes)
- `videos/fin-demo-showcase-thumb.jpg` (50,862 bytes)
- `videos/fin-demo-showcase-submission.json` (1,926 bytes)

Two smaller derived cuts exist. Neither is the film itself - the film is the `88cc3715`
master above - but one of them is what Jay was sent for review.

**`videos/fin-demo-showcase-progress-2026-10-16-SMALL.mp4` is the one delivered to Jay.**
13,087,141 bytes (12.48 MiB), video 454 kbps, audio re-encoded at 127 kbps, which lifted true
peak from -3.9 to -3.4 dBFS (2.9 dB inside the ceiling, not a defect).

**`videos/fin-demo-showcase-progress-rebuild-2026-10-16__sub15mb__5e575c32.mp4`** - md5
`5e575c32f0ccfb355189211b1455afca`, 14,477,525 bytes (13.81 MiB), video 451 kbps, audio
stream copied rather than re-encoded so it md5s identically to the source audio and the
-16.4 LUFS / -3.9 dBTP figures are the same bytes rather than re-derived ones. Verified by
eye at 1:1 against the source on the five densest text regions. **It was not the one
delivered because the two files carry near-identical video bitrate (451 against 454) and the
entire 1.4MB difference is audio, so bit-identical audio on a review copy buys nothing a
viewer can hear while spending margin against a size limit whose exact definition is
unknown.** Keep it as the strict-no-change alternative; do not re-derive the comparison.

---

## 2. If you rebuild, read this first - THE MTIME TRAP

**The twelve voice WAVs in `assets/voice-el/` carry mtimes NEWER than the render that
produced the delivered film, and their bytes did not change.**

Newest WAV `12.wav` is 22:13:52. The render in `renders/` is 22:10:51. The WAVs are about
three minutes newer than the film built from them, because `audio_stage.json` was re-staged
after the render for verification and the staging chain rewrites byte-identical files.

**A segment cache that compares mtime rather than content will decide the audio is stale and
re-encode twelve takes that did not change.** That costs a full audio pass and, worse, it
makes the rebuilt file differ from `88cc3715` for no reason anybody can see in a diff.

Note the asymmetry, because it is the thing that will mislead you: relative to the two copies
in `videos/` (22:14:51 and 22:16:32) the WAVs are OLDER, because copying reset those mtimes.
So "are the WAVs newer than the film" answers yes or no depending on which copy you ask, and
only the `renders/` copy is the one a build pipeline compares against.

**This cannot affect `88cc3715`.** That file is already made. The trap only bites a rebuild.
Compare content, not mtime.

---

## 3. The ten-item fix list and where each one stands

Source of truth for the verbatim findings is `videos/fin-demo-viewer2-report.md`. Verdict was
**NO - not in front of a customer as it stands.** Items are the viewer's own numbering and
order (most serious first). None of the fixes were applied; the film is as the viewer saw it.

### Blocking

**1. Green rings on EMPTY boxes (0:32-0:40). OUTSTANDING.**
Confirmed at 5x. At 0:40 three rings sit on Skin, Lung and Bone/Injury; only Bone carries a
handwritten X. The "handwritten X" pill attaches to the Bone ring, which teaches the viewer
that a ring means a found tick, so the picture asserts a detection the page does not contain
on the one beat the whole film is built around. Remedy: ring only the ticked box, or ring
every box in a neutral "examined" stroke with a legend. A reserved marker must not sit on an
empty box.

**2. "28 pages, 8 applications" header against a voiced seven (0:18-0:28 vs 2:44-2:50). OUTSTANDING, cause settled.**
The film is CORRECT and the narration must not change. The batch holds seven applications
(start pages p1, p5, p9, p13, p17, p21, p25; 28 / 4 = 7). The "8" is the example number in
the filename `example-8-bulk-from-scanner.pdf` surfacing as an application count, which is a
product bug filed against the demo, not a film error. It stays a film problem only because a
viewer sees a contradiction whoever caused it. Remedy is cover, crop or re-capture, never a
narration change.

**3. The hero fails the product's own ID checksum and the voice never says so (1:20-2:00). OUTSTANDING.**
Red X on "South African ID checksum", 2 notes, 89% amber, "Needs review: 1 field". The IDs
are fabricated so a failing checksum is expected, but a South African buyer cannot know that
and reads it as a misread. One spoken sentence fixes it: the checksum caught a doubtful ID
and flagged it. Related: the voice says "anything under 70% goes on a review list" while the
hero sits at 89% with a field needing review; per-field and overall are different things and
nothing says so.

**4. Two unexplained confidence numbers for the same pages (2:00-2:30). OUTSTANDING.**
89% hero overall confidence against 99% model accuracy for `chatgpt-azure-5.5`, the same
model named in the capture header, on the same four pages. Different measures, neither frame
nor voice distinguishes them.

### Serious

**5. "Nine files. Seven kinds of trouble." SETTLED - see section 4.**

**6. Step 3 shows three TRUE results and only one is visible (1:12-1:20). OUTSTANDING.**
`bone_injury_conditions`, `sugar_diabetes` and `vehicle_accident` all true with authored
green ticks; the crop shows only the Bone X. The other two fields sit lower on the page and
the film never shows them, so the picture does not earn two of the three. Distinct from item
7: this one needs a FRAME showing the other two fields, not a claim check.

**7. Four pills asserted by text and voice with no result frame (2:40-2:46). EVIDENCED - see section 5.**

**8. Handovers leave bare or near-bare frames. OUTSTANDING.**
0:12-0:14 (headline on near-empty navy about 3s), 0:28-0:30 (title alone about 1.5s),
0:44-0:46 (dissolve while "Step 1" is spoken, stage not yet arrived). The close is populated
and there is no black tail.

**9. Captured app screenshots are soft and hard-cropped (2:00-2:20). OUTSTANDING.**
Upscaled low-resolution capture cut hard at about y=940 with a navy band replacing the page
bottom; the field table is cut mid-row at `main_member.paypoint 85%`.

**10. Callout pills occlude content (2:08-2:15). OUTSTANDING.**
"pages 4 / 4" and "Copy JSON / Download" sit over the second validation note and cut it at
"...misread or miswrit" - covering the very line item 3 says the film should be addressing.

### Minor, recorded and not actioned
Count-up transient through "66" and a "93" without its percent sign mid-animation (at rest it
reads correctly). Jacob Smith is both the hero and the first row of the batch, unexplained.

---

## 4. Item 5 SETTLED - what the nine is

Settled from the live app's own sample picker, not from reasoning.

**There are nine files. There is no Example 9.** The pack runs Examples 1 to 8 plus one more
variant; the count of files is nine and the count of distinct kinds is seven, because
**Examples 5, 6 and 7 are three Word variants of the same kind.** Both numbers in the
headline were right; nothing in the film established either, which is why it read as a
miscount.

**Sharpening, and it changes the copy: one of the seven is the clean scan, which is not
trouble.** So the line wants to be **"seven kinds"**, not "seven kinds of trouble". Calling a
clean scan trouble is a small inaccuracy pointed the wrong way, and it is the kind a careful
buyer notices.

The remaining choice is the picture-copy pair: either show the nine (two kinds repeated) or
say what is being counted. The settled facts support either; nobody has picked one.

---

## 5. Items 6 and 7 - what was proved, and what was not

Three bounded jobs were run against the live demo (11 pages, about 30 vision calls,
`claude-5-5-sonnet`). These were authorised at the time. Results:

| claim | state | evidence |
|---|---|---|
| Missing page FLAGGED | **TRUE** | run returned `3/4 missing: 2 undertaking` with a `page_missing` note |
| Shuffled scan REASSEMBLED | **TRUE** | tiles returned roles in order 1, 3, 2, 4 - out of sequence on input, correctly reassembled |
| Phone photos READ, DOUBTFUL FIELDS FLAGGED | **TRUE** | 73% confidence and 60 fields flagged, against the hero's 89% and 1 field |
| Word files CONVERTED | **UNVERIFIED** | files were captured but never read before the stop |

**Word files stays UNVERIFIED.** Do not promote it to true because the other three held. It
is the only honest state for it and the next person should either run it or cut the pill.

**The phone-photo contrast is the strongest thing found in this whole pass, and it should not
be thrown away.** 73% with 60 fields flagged against the hero's 89% with 1 field is the
product doing exactly what the film claims, measured rather than asserted - a bad input
produces lower confidence and a much longer review list, and the system says so instead of
guessing. That is a frame the film does not currently have and the one most worth capturing:
it converts item 7 from a label into evidence. Everything else in the fix list removes an
overclaim; this one adds a proof.

---

## 6. Scratch inventory - none of it is wired in

Four directories, all untracked scratch. Nothing here is referenced by the build, the
timeline or any composition. Safe to delete; worth keeping while the pass is paused.

**`.recap/`** - the live-app runs behind section 5 (16 Oct 22:28-22:36):
`00_home.png`, `01_fin-demo.png`, `02_fin-demo.png`, `03_runs.png` (navigation),
`run_hero_example1.png`, `run_blueink_example4.png`, `run_bulk_example8.png`,
`run_phone_example10.png` (the 73% / 60-field result), `run_missing_page.png`,
`run_out_of_sequence.png`, `run_word_sized.png` (**captured, never read - this is the
UNVERIFIED item**).

**`.vfy/`** - two 1:1 verification crops from the ring investigation, item 1 (22:26):
`rings.png`, `t40.png`.

**`.eyeread/`** - six JPG frames pulled for the eye-read gate (22:12-22:13): t4.0, t103.5,
t112.0, t150.0, t158.0, t174.0.

**`.rx/`** - two full-resolution PNG frames (22:16): t100.0, t142.0.

The lead's recollection named only `.recap/` and `.vfy/`; `.eyeread/` and `.rx/` are also
present and are listed here so the inventory is complete.

---

## 7. Tool changes - instruments only, no artifact touched

Three files changed after the render. All three are measuring instruments. None of them can
have affected `88cc3715`, which was already made.

- **`tools_delivery_gate.py`** (22:12)
- **`tools_certificate.py`** (22:23) - read-only certificate generator. Prints every figure
  from the thing it describes, with its instrument and population, and now prints the
  measurement LAYER beside each figure (roughly half the gate figures are authoring-layer,
  not measured on the delivered file - do not let a certificate imply otherwise). Its
  `guard()` refuses to emit a certificate containing "not found" or "see output", proven to
  fire with exit 1.
- **`tools_blankruns.py`** (22:23) - **bug fix worth knowing.** Its timeline path was
  `Path(film).parent.parent / "timeline.json"`, which resolved correctly only when the film
  was read from `renders/` and broke silently when read from `videos/`. Now anchored to
  `Path(__file__).parent`. Any blank-run result produced against a film in `videos/` before
  this fix was measured without a timeline and should not be trusted.

`CERTIFICATE.md` was specified but never written to disk; the generator exists and the
equivalent content currently lives in
`videos/fin-demo-showcase-progress-rebuild-2026-10-16.dop-pass.md`.

---

## 8. Open decision, waiting on a human

**UI vintage. Unresolved.** The demo app has moved on since the film's captures were taken.
Any re-capture (items 2, 6, 7 and 9 all want one) risks putting a newer vintage of the app on
screen beside older captures the film keeps.

**A film mixing two ages of an app is a defect no gate can see** - every frame is real, every
frame is current with something, and nothing in the file disagrees with anything else.

The team lead's stated position, offered as what the answer would have been had the work
continued: **re-capture only the Fin-demo surfaces the film already shows.** Not a ruling, and
not acted on. Treat it as a strong default and confirm before capturing.

---

## 9. Standing limits

- **No second build was made, by ruling.** Reproducibility is therefore stated and not
  proven: no `Math.random`, `Date.now` or clock reads exist in any composition, the audio
  re-stages byte-identical and the encoder is deterministic on identical input, but the
  browser render step is untested for determinism.
- **Word files CONVERTED is unverified** (section 5).
- **Pronunciation of "Fin-demo" is unjudged.** The viewer had no audio perception and Whisper
  transcribed the brand name as "Un vousa". A human must listen to it. No instrument in this
  project closes that.
- **Orphan `chrome-headless-shell` processes** make a full render take about three and a half
  hours instead of minutes. 31 of them, about 691MB, up to nine days old, none belonging to
  this work. **This is with Jay. Do not touch them.**
