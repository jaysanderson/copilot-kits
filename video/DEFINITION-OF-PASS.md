# Definition of Pass (video kit)

Trimmed from `reference/DEFINITION-OF-PASS.full.md` to the lines a video can fail. Every delivered file is walked
line by line; each numbered line gets PASS, FAIL or N/A with evidence beside it. One FAIL on any numbered line
means not done. A PASS without evidence is a FAIL: attach the frames viewed, the scan output, the figure with its
md5 and duration, the source that confirmed a claim.

## A. Truth
1. Every product claim spoken or shown traces to a source you hold (product documentation, the live app, the
   brief's locked facts). Nothing from memory. A claim no source confirms is flagged, never kept quietly.
2. No fabricated numbers: no invented accuracy, adoption, ROI or benchmark. Quality is shown (cited answers, a
   quality signal), never asserted as a figure. Demo figures are labelled as demo figures.
3. No silent substitute: if a capability the film shows was not delivered by the product's own mechanism, the film
   says so on screen or in narration; it never ships dressed as a feature.
4. Certifications are named only when verified outside the product documentation.
5. Locked facts hold everywhere: the same numbers appear identically in script, screen and certificate.
6. Statistics come from named independent sources, cited on screen or in the notes; nothing older than about five
   years without a date; never a vendor number presented as independent.
7. All pricing in USD; no legible localised price anywhere, even inside a crop.
8. Every figure on screen was read off live footage or a source you hold, and the frame it appears in was viewed.
9. Reused screenshots are checked against the live product before use; a stale number in a frame is a FAIL.
10. A line that promises an action shows it; an "every" claim shows the whole set.

## B. Safety and hygiene
11. No secret, API key, token or voice id in any file, frame, script or repository.
12. No hosting-region or infrastructure string visible in any frame (`aws-`, `ap-southeast`, `us-east-`, `eu-west`,
    `nuclia.cloud`, `fly.dev` and the like); crop or neutralise before recording.
13. Other customers' names and account identifiers never appear; fictional entities and neutral demo logins only.
14. No real third-party brand used as if owned; no real personal identifiers.
15. Synthetic-data disclosure is present but discreet (a footer, never the headline).
16. Outbound use of the film is a draft until Jay signs off.
17. No stock footage and no AI-generated imagery; every frame is real product footage or authored brand motion.

## C. Language and voice
18. Australian English unless the brief names another variant for spelling (accent is a separate choice).
19. No em dashes anywhere, on screen or in narration; a spaced hyphen instead.
20. Banned words absent: delve, leverage, unlock, seamless, game-changing.
21. De-AI pass done: no hedging, filler, symmetrical triads or corporate fluff.
22. Room test: a CIO, CMO or solutions architect would not wince at any line.
23. "Progress Agentic RAG" in full on first prominent use in anything customer-facing; "ARAG" internal only.
24. Narration argues, the screen states: no narration line repeats the key noun and verb of visible text.

## D. Video
25. Film type (demo, concept, hybrid) is written in the brief before anything was built and the film honours it; a
    concept film that is typeset statements on a background FAILS whatever else it passes.
26. Script, storyboard and narration existed before footage; the arc is hook, problem, capability, proof, CTA; no
    route tour; the hook is in the first five seconds.
27. One narrator voice per piece, chosen from `brand/voices.json` by audience and register, reason recorded.
28. No captions unless the brief says so in writing. No music, ever.
29. Loudness: integrated -14 LUFS within 0.5 LU, true peak under -1.5 dBTP, stereo 48 kHz, two-pass loudnorm.
30. No digital silence at t=0; no silence gap over 2.0 s outside a declared hold; the music-free check runs on
    decoded PCM, not on a `-v error` silencedetect.
31. Audio and video streams end together in every segment and in the master.
32. Sync measured in the finished file at every anchor: the named thing is on screen 0 to 3.5 s before the word,
    and never trails it by more than 0.5 s.
33. Narration never promises an interaction the footage does not show; a product function is never a static end state.
34. Motion: frozen share under 25% of runtime; longest still run under 2.5 s; at least one cut above 12.0 (0 to 255
    grey levels at 480x270) per 15 s; a concept film is at least 60% illustration-led with no type-only run over 3 s.
35. Footage sits in a device frame on one branded stage, never full-bleed; mobile captures sit in a phone bezel.
36. Progress livery around the footage: tokens from `brand/progress-hyperframes-brand.md`, real Progress Sans via
    local `@font-face` (proven by metric), one graphic device, lockup untouched and at least 75 px high.
37. Captured product frames are untouched; only the authored stage is rebranded.
38. Legibility: evidence-class text is never the smallest type in the frame; text inside captured plates is in the
    population; the first frame reads as a poster.
39. Every must-not-appear string from the brief is OCR-absent from frames sampled across the whole film, with the
    OCR control proven to fire on a planted string.
40. Frames viewed at start, middle and end, and at each timestamp where narration names a proof, and the frames
    are kept with the certificate.
41. Every reported figure names the md5 and duration of the file it was measured on and states its unit.
42. Gates ran with their controls: `video_gate.py` exit 0 with every HOLE named and read by a human; a gate that
    skipped itself, examined zero items or had a control fail is a FAIL for this line.
43. Render once: a low-quality preview was read before the single master render; variants were cut from the master
    or recomposed, not re-rendered.
44. Two cuts where the brief asks for a feed: the full piece and a 60 to 90 s social cut from the same segments.
45. A meaningful thumbnail per delivered cut: a real frame or a designed card with the film's own title and the
    Progress mark; never a blank card or generic icon.
46. The certificate (`<name>.dop-pass.md`) is written by the producer who built the film, lists every line above
    with evidence, and the delivered file's md5, duration, voice and source; a relayed verdict is not evidence.
