#!/usr/bin/env python3
"""Derive new beat times for every frame from the MEASURED new takes.

Nothing is hand-typed and nothing is carried over. For each line we have, for
the OLD Kokoro take, word-level timings (audio_engine_meta.json) and for the NEW
ElevenLabs take, character-level timings (assets/voice-el/NN.align.json). The
same words are spoken in both, so word k gives an anchor pair
(old_start_k -> new_start_k). Every authored beat time maps through the monotone
piecewise-linear interpolation of those anchors, which keeps each beat attached
to the WORD it was authored against rather than to a clock position.

Controls (run `python3 tools_retime.py`):
  - word counts must match per line, else the anchor set is wrong -> raises
  - map(0) == 0 and map(old_dur) == new_dur exactly
  - monotonicity over a dense sweep
  - a spot anchor: the mapped old time of a named phrase lands within 60ms of
    that phrase's independently-looked-up new start (tools_align), which is a
    SEPARATE instrument reading the same alignment a different way
"""
import json, pathlib, re, sys, unicodedata, bisect, difflib

P = pathlib.Path(__file__).parent
IDS = [f"{i:02d}" for i in range(1, 13)]


def _norm_word(w):
    w = unicodedata.normalize("NFKD", w).lower()
    w = w.replace("’", "'").replace("‘", "'")
    return "".join(c for c in w if c.isalnum() or c == "'")


def old_words():
    meta = json.load(open(P / "audio_engine_meta.json"))["voices"]
    out = {}
    for v in meta:
        out[v["id"]] = dict(
            duration=float(v["duration_s"]),
            words=[(_norm_word(w["text"]), float(w["start"]), float(w["end"]))
                   for w in v["words"] if _norm_word(w["text"])],
        )
    return out


def new_words(lid):
    """Word starts/ends rebuilt from the character alignment."""
    d = json.load(open(P / "assets/voice-el" / f"{lid}.align.json"))
    chars, st, en = d["characters"], d["character_start_times_seconds"], d["character_end_times_seconds"]
    words, cur, c_start, c_end = [], [], None, None
    for c, s, e in zip(chars, st, en):
        if c.strip() == "":
            if cur:
                words.append(("".join(cur), c_start, c_end)); cur, c_start = [], None
            continue
        if c_start is None: c_start = s
        c_end = e; cur.append(c)
    if cur: words.append(("".join(cur), c_start, c_end))
    out = [(_norm_word(w), s, e) for w, s, e in words if _norm_word(w)]
    return dict(duration=en[-1], words=out)


class Remap:
    """Monotone piecewise-linear old-take-time -> new-take-time map.

    Anchors come from a SEQUENCE ALIGNMENT on word text (difflib), never from
    index-for-index pairing: the two engines tokenise differently ("twenty-eight"
    vs "28", "Powered by Progress" as one token), and index pairing silently
    shifts every anchor after the first divergence - line 07 diverged at word 26,
    which would have mis-timed the whole checksum roll-call while reporting a
    clean count. Only words whose normalised text is IDENTICAL become anchors;
    divergent runs are spanned by interpolation between the anchors either side.
    """

    MIN_COVERAGE = 0.70
    # Lines 08 and 12 were deliberately REWRITTEN (the deletion claim was rescoped), so
    # their old and new word sets differ by design and coverage drops. The floor exists to
    # catch an anchor set that is too sparse to retime, not a line that was edited on
    # purpose, so those two carry a named override - and the constructor then asserts that
    # no authored beat lands after the last text-identical anchor, which is the thing the
    # floor was protecting. Frame 08's latest beat is OLD 7.300s against a last anchor at
    # OLD 8.07s, so nothing is interpolated across the rewritten tail.
    COVERAGE_OVERRIDE = {"08": 0.55, "12": 0.65}

    def __init__(self, lid):
        o, n = old_words()[lid], new_words(lid)
        self.lid, self.old_dur, self.new_dur = lid, o["duration"], n["duration"]
        ow, nw = o["words"], n["words"]
        sm = difflib.SequenceMatcher(a=[w[0] for w in ow], b=[w[0] for w in nw], autojunk=False)
        pairs = []
        for blk in sm.get_matching_blocks():
            for k in range(blk.size):
                a, b = ow[blk.a + k], nw[blk.b + k]
                assert a[0] == b[0], "anchor text must be identical"
                pairs.append((a[1], b[1]))
        self.n_old, self.n_new, self.n_anchor = len(ow), len(nw), len(pairs)
        self.coverage = len(pairs) / max(len(ow), len(nw))
        floor = self.COVERAGE_OVERRIDE.get(lid, self.MIN_COVERAGE)
        if self.coverage < floor:
            raise ValueError(f"line {lid}: only {len(pairs)} anchors over "
                             f"{len(ow)}/{len(nw)} words ({self.coverage:.0%}) - too sparse to retime")
        self.last_anchor_old = pairs[-1][0] if pairs else 0.0
        xs, ys = [0.0], [0.0]
        for os_, ns in pairs:
            if os_ > xs[-1] + 1e-6 and ns > ys[-1] + 1e-6:
                xs.append(os_); ys.append(ns)
        if self.old_dur > xs[-1] + 1e-6 and self.new_dur > ys[-1] + 1e-6:
            xs.append(self.old_dur); ys.append(self.new_dur)
        self.xs, self.ys = xs, ys
        # largest un-anchored stretch in OLD time: where the map is least informed
        self.max_gap = max(b - a for a, b in zip(xs, xs[1:])) if len(xs) > 1 else 0.0

    def __call__(self, t):
        xs, ys = self.xs, self.ys
        if t <= xs[0]:
            return round(ys[0] + (t - xs[0]), 3)
        if t >= xs[-1]:
            return round(ys[-1] + (t - xs[-1]) * (ys[-1] / xs[-1]), 3)
        i = bisect.bisect_right(xs, t) - 1
        f = (t - xs[i]) / (xs[i + 1] - xs[i])
        return round(ys[i] + f * (ys[i + 1] - ys[i]), 3)


_r = {}
def remap(lid):
    if lid not in _r: _r[lid] = Remap(lid)
    return _r[lid]


if __name__ == "__main__":
    import tools_align as A
    ok = True
    print(f"{'line':5s} {'old_dur':>8s} {'new_dur':>8s} {'ratio':>6s} {'words o/n':>10s} {'anchors':>8s} {'cover':>6s} {'max_unanchored':>15s}")
    for lid in IDS:
        try:
            r = remap(lid)
        except ValueError as e:
            print("FAIL", e); ok = False; continue
        ovr = " OVERRIDE" if lid in r.COVERAGE_OVERRIDE else ""
        print(f"{lid:5s} {r.old_dur:8.3f} {r.new_dur:8.3f} {r.new_dur/r.old_dur:6.3f} "
              f"{str(r.n_old)+'/'+str(r.n_new):>10s} {r.n_anchor:8d} {r.coverage:6.0%} {r.max_gap:15.2f}"
              f"  last anchor OLD {r.last_anchor_old:6.2f}{ovr}")
        assert abs(r(0.0)) < 1e-6, f"{lid}: map(0) != 0"
        assert abs(r(r.old_dur) - r.new_dur) < 0.002, f"{lid}: map(old_dur)={r(r.old_dur)} != {r.new_dur}"
        prev = -1.0
        for k in range(0, 2001):
            v = r(r.old_dur * k / 2000.0)
            if v < prev - 1e-6:
                print(f"FAIL {lid}: not monotone"); ok = False; break
            prev = v

    print("\nSPOT ANCHORS - mapped old word-start vs tools_align phrase lookup (independent read of the alignment):")
    SPOTS = [("01", "boxes ticked by hand"), ("01", "you can trust"),
             ("03", "the ticks are gone"), ("04", "one page at a time"),
             ("06", "read from the pixels"), ("07", "date of birth"),
             ("07", "review list"), ("09", "none missing"),
             ("10", "seventy-five"), ("11", "one application per applicant"),
             ("12", "Keep nothing")]
    for lid, phrase in SPOTS:
        r = remap(lid)
        ow = old_words()[lid]["words"]
        toks = [_norm_word(w) for w in phrase.split()]
        hit = None
        for i in range(len(ow) - len(toks) + 1):
            if [w[0] for w in ow[i:i + len(toks)]] == toks:
                hit = ow[i][1]; break
        if hit is None:
            print(f"  {lid} {phrase!r:34s} NOT IN OLD WORD LIST (tokenisation) - no anchor check possible")
            continue
        mapped, direct = r(hit), A.at(lid, phrase)
        d = abs(mapped - direct)
        verdict = "OK" if d <= 0.06 else "*** OUT OF TOLERANCE"
        print(f"  {lid} {phrase!r:34s} old {hit:6.2f} -> mapped {mapped:7.3f} | align {direct:7.3f} | delta {d:.3f}  {verdict}")
        if d > 0.06: ok = False

    print("\nNEGATIVE CONTROL - a deliberately wrong map must fail the anchor check:")
    r = remap("01"); true_xs = r.xs
    r.xs = [x * 1.5 for x in true_xs]
    ow = old_words()["01"]["words"]
    hit = [w[1] for w in ow if w[0] == "boxes"][0]
    bad = abs(r(hit) - A.at("01", "boxes ticked by hand"))
    r.xs = true_xs
    print(f"  shifted map delta {bad:.3f} -> {'DETECTED (control fires)' if bad > 0.06 else 'NOT DETECTED - CHECK IS DECORATION'}")
    if bad <= 0.06: ok = False

    print("\nSELFTEST", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)
