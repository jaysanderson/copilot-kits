#!/usr/bin/env python3
"""Assert that a beat whose MEANING IS A CHANGE IN WORDING actually happens on screen.

WHY THIS EXISTS, and read this before deciding you do not need it.

Every other instrument in this suite reads geometry, motion, colour, level or duration.
NONE OF THEM READS TEXT. So any beat that means something because the words change - a
figure updating, a status flipping, a label being replaced - passes the entire gate suite
cleanly while being completely broken, and nothing anywhere will tell you.

That is not hypothetical. On the RAG explainer (1 Oct 2026) a policy card was supposed to
change from "fourteen days" to "twenty-one days" under the narration line "update the
material, and the answer updates". The text cross-fade was scheduled at 108.6s and the
cards did not resolve until 111.5s, so the card was never legible while it read fourteen:
the picture was static under a line promising a change. `lint` rc 0, `check` rc 0, the
motion sidecar clean, and three `verify_render` runs green at 11, 18 and 27 checks - on
that master. The composition held the right string, which is why reading the source
confirmed it and reading the frames refuted it.

THIS READS THE DELIVERED FILE, NEVER THE COMPOSITION, and stamps the md5 it measured.

Three assertions, not one:
  1. the BEFORE string is legible across a real hold, long enough to be read;
  2. the AFTER string is legible after the change;
  3. NEITHER appears in the other's window - a scanner that finds both everywhere would
     pass a one-sided presence check while proving nothing. Same reason any scanner needs
     a negative control.

Run --selftest FIRST. A check nobody has seen fail is not a check.

USAGE
  check_text_beat.py --master FILE --crop W:H:X:Y \
      --before "fourteen" --after "twenty-one" \
      --before-at 104.0 105.0 106.5 108.0 109.5 \
      --after-at  110.8 111.5 113.0 118.0
  check_text_beat.py --master FILE --crop ... --before ... --after ... --selftest

Do NOT sample inside the cross-fade itself: both strings are legitimately co-present
there. Leave that window unasserted and say so, rather than widening the match.

Requires ffmpeg and tesseract.
"""
import argparse, hashlib, pathlib, re, subprocess, sys, tempfile


def ocr(master: str, t: float, crop: str) -> str:
    """Crop one frame out of the DELIVERED file and read it. 2x upscale - small type does
    not survive OCR at native scale, the same reason a visual scan runs where the feature
    survives."""
    with tempfile.TemporaryDirectory() as d:
        png = pathlib.Path(d) / "f.png"
        subprocess.run(
            ["ffmpeg", "-loglevel", "error", "-ss", str(t), "-i", master,
             "-frames:v", "1", "-vf", f"crop={crop},scale=iw*2:ih*2", "-y", str(png)],
            check=True)
        out = subprocess.run(["tesseract", str(png), "stdout", "--psm", "6"],
                             capture_output=True, text=True).stdout
    # hyphens and punctuation render inconsistently; normalise both sides the same way
    return re.sub(r"\s+", " ", re.sub(r"[^a-z ]", " ", out.lower().replace("-", "")))


def norm(s: str) -> str:
    return re.sub(r"[^a-z ]", "", s.lower().replace("-", ""))


def check(master, crop, before, after, before_at, after_at, invert=False):
    """Returns (passes, fails, lines). invert=True flips every expectation - that is the
    selftest arm, and every case must FAIL for the check to be worth anything."""
    md5 = hashlib.md5(pathlib.Path(master).read_bytes()).hexdigest()
    b, a = norm(before), norm(after)
    passes, fails, lines = 0, 0, [f"master md5 {md5}"]
    for t, want, other in ([(t, b, a) for t in before_at] + [(t, a, b) for t in after_at]):
        txt = ocr(master, t, crop)
        want_seen, other_seen = want in txt, other in txt
        if invert:
            want_seen, other_seen = not want_seen, not other_seen
        ok = want_seen and not other_seen
        passes, fails = passes + ok, fails + (not ok)
        lines.append(f"  t={t:<8.2f} expected={want!r} seen={want_seen} "
                     f"other={other!r} present={other_seen} {'PASS' if ok else 'FAIL'}")
    return passes, fails, lines


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--master", required=True)
    p.add_argument("--crop", required=True, help="ffmpeg crop W:H:X:Y containing the text")
    p.add_argument("--before", required=True)
    p.add_argument("--after", required=True)
    p.add_argument("--before-at", nargs="+", type=float, default=[])
    p.add_argument("--after-at", nargs="+", type=float, default=[])
    p.add_argument("--negative-at", type=float, default=None,
                   help="a timestamp where NEITHER string should appear, e.g. before the "
                        "element exists. Proves the reader is not hallucinating matches.")
    p.add_argument("--selftest", action="store_true")
    a = p.parse_args()

    if a.selftest:
        # ARM 1: every expectation inverted. All must fail, or the check cannot fail.
        _, fails, lines = check(a.master, a.crop, a.before, a.after,
                                a.before_at, a.after_at, invert=True)
        n = len(a.before_at) + len(a.after_at)
        print("\n".join(lines))
        print(f"SELFTEST arm 1 (inverted): {fails} of {n} failed as required")
        if fails != n:
            print("SELFTEST FAILED - the check cannot detect a wrong value. Do not trust "
                  "a clean run from it.")
            return 2
        # ARM 2: negative control, where neither string should be readable.
        if a.negative_at is not None:
            txt = ocr(a.master, a.negative_at, a.crop)
            found = [s for s in (norm(a.before), norm(a.after)) if s in txt]
            print(f"SELFTEST arm 2 (negative control t={a.negative_at}): "
                  f"{'found ' + str(found) if found else 'neither string, as required'}")
            if found:
                print("SELFTEST FAILED - the reader finds strings that are not there.")
                return 2
        else:
            print("SELFTEST arm 2 SKIPPED - no --negative-at given. The reader has not "
                  "been shown to stay quiet; this is a declared hole, not a clean result.")
        print("SELFTEST PASS")
        return 0

    passes, fails, lines = check(a.master, a.crop, a.before, a.after,
                                 a.before_at, a.after_at)
    print("\n".join(lines))
    print(f"{passes} passed, {fails} failed")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
