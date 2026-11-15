# Storyboard schema: claim, frame, data

**Read this first.** This file has two halves and a machine reads only one of them.
The fenced blocks tagged `filmkit-claims` further down are the MACHINE half: JSON, parsed
whole by `checks/claims.py`. Everything else is prose for people and is never parsed. A
parser that stops a list at the first line of explanation reads zero items and reports a
serene pass, which has happened twice in one day here; JSON either parses entire or
raises, so keep explanation outside the fences and never convert a block to a bullet list.

## The rule

Every beat that asserts an outcome, in the narration or on a pill, declares three things:

- **CLAIM** - the outcome, quoted as the film says it (`quote`), with `truth` recorded from
  the evidence you actually hold: `true`, `unverified` or `false`. Truth and proof are
  separate axes. A claim can be true of the product and still have no frame in the film;
  that is the fin-demo case, and it is a FAIL.
- **FRAME** - the picture that proves it: an image on screen (`image` in a composition at
  time `t`, or a `capture` file with its `display_height` in a Remotion film). A frame with
  no image is a restatement of the claim, not a result, and fails.
- **DATA** - the `fields` the claim rests on, each a region `[x0, y0, x1, y1]` in the
  SOURCE image's pixels, plus an optional `crop` (the window of that image the film
  actually shows; default is the whole image). Every field must sit inside the crop.

A beat that genuinely asserts nothing says so with `declared_none` and a reason. A beat
with no entry at all is reported UNDECLARED by name: an unmeasured beat never reads clean.

```json
{"film": "<key in checks/claims.py FILMS>",
 "beats": {"<composition stem or scene id>": {
   "claims": [{"id": "...", "kind": "pill|voice|result", "quote": "...", "truth": "true|unverified|false",
               "frame": {"composition": "<stem>", "t": 0.0, "image": "<file>", "crop": [0,0,0,0],
                         "fields": {"<name>": [0,0,0,0]}} }]}}}
```

(That skeleton is a plain `json` fence, not a `filmkit-claims` one, so it is not counted.)

## What the check does with it

Both directions. A declared claim with no frame, a frame whose image is not on screen at
`t`, or a field outside its crop fails. A rendered pill or narrated outcome sentence that no
declared claim covers also fails. The assertion population is discovered from the rendered
timeline and the script, never typed here. It prints the population count (claims found,
frames declared, beats undeclared) because zero of zero is not a pass.

It cannot judge whether a frame is PERSUASIVE, only whether it exists and contains the
declared regions. Field boxes and crops are declared, not read off pixels. The full blind
list (B1 to B7) is in the docstring of `checks/claims.py`.

## Worked example: fin-demo-showcase, the real defects

Two beats. In `11-messy-ones` four outcome pills have no result frame at all (viewer report
item 7); `word-files-converted` is `unverified` per `fin-demo-showcase/RESUME.md` section 5 and
stays so however the other three read. In `06-step-3-ask` three fields are TRUE and the
declared regions are in the source page (viewer report item 6): the check confirms they sit
inside the crop and prints each tick's rendered size, which is the reason the picture does
not earn the claim even when the fields are technically present.

```filmkit-claims
{"film": "fin-demo-showcase",
 "beats": {
  "11-messy-ones": {"claims": [
    {"id": "missing-page-flagged", "kind": "pill", "quote": "Missing page FLAGGED", "truth": "true", "frame": null,
     "note": "RESUME.md s5: run returned 3/4 missing, page_missing note. Not in the film."},
    {"id": "shuffled-reassembled", "kind": "pill", "quote": "Shuffled scan REASSEMBLED", "truth": "true", "frame": null,
     "note": "RESUME.md s5: roles returned 1,3,2,4 and reassembled. Not in the film."},
    {"id": "word-files-converted", "kind": "pill", "quote": "Word files CONVERTED", "truth": "unverified", "frame": null,
     "note": "RESUME.md s5: captured, never read. Stays UNVERIFIED."},
    {"id": "phone-photos-flagged", "kind": "pill", "quote": "Phone photos READ DOUBTFUL FIELDS FLAGGED", "truth": "true", "frame": null,
     "note": "RESUME.md s5: 73% and 60 fields flagged against the hero's 89% and 1. Not in the film."}
  ]},
  "06-step-3-ask": {"claims": [
    {"id": "three-fields-true", "kind": "result",
     "quote": "bone_injury_conditions true sugar_diabetes true vehicle_accident true", "truth": "true",
     "frame": {"composition": "06-step-3-ask", "t": 13.0, "image": "ex1-page3.png",
               "fields": {"bone_injury_conditions": [160, 306, 170, 320],
                          "sugar_diabetes": [106, 474, 122, 487],
                          "vehicle_accident": [71, 547, 85, 561]}}}
  ]}
 }}
```

## Worked example: the control, a claim the film does earn

`videos/kuraray-portal/en`, scene `answer` (46.8 to 54.6 s): the English answer names the
machining origin and sets the Japanese term beside it, and the capture on screen shows
both inside one sentence. The check must stay quiet on it, otherwise it fires on everything.
Remotion film, so the frame is a capture plus a `display_height` (700 in the storyboard).

```filmkit-claims
{"film": "kuraray-portal-en",
 "beats": {
  "answer": {"claims": [
    {"id": "japanese-term-quoted", "kind": "voice",
     "quote": "It names the machining origin, and quotes the Japanese term its source uses for it.", "truth": "true",
     "frame": {"capture": "captures/en2-ans.png", "display_height": 700,
               "fields": {"english_term": [680, 515, 1195, 575], "japanese_term": [1198, 515, 1430, 575]}}},
    {"id": "answer-in-english", "kind": "voice", "quote": "The answer comes back in English.", "truth": "true",
     "frame": {"capture": "captures/en2-ans.png", "display_height": 700,
               "fields": {"english_answer": [30, 350, 1850, 1060]}}}
  ]}
 }}
```

## Running it

```
.venv/bin/python scripts/filmkit/checks/claims.py --film fin-demo-showcase
.venv/bin/python scripts/filmkit/checks/claims.py --film kuraray-portal-en
.venv/bin/python scripts/filmkit/checks/claims.py --selftest
```

Add a new film by adding its key to `FILMS` in `claims.py` and a block here (or point
`--declarations` at the film's own storyboard). Exit code is the verdict.
