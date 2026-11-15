#!/usr/bin/env python3
"""Verify the retime against the REGISTERED timeline, by membership.

The first version of this paired old and new beats by index and reported eight
frames failing. It was wrong: GSAP returns children sorted by start time, and
holding the eyebrows past the transition REORDERS them, so index pairing
compared different beats. Compare the multiset of start times instead - the
same lesson as diffing lists by index rather than by membership.

Declared additions are the only beats allowed to exist that the old cut did not
have, and each is named here rather than tolerated as a count.
"""
import json, subprocess, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import tools_retime as R

FR = {"01-powered-by.html": "01", "02-sample-pack.html": "02", "03-the-hard-page.html": "03",
      "04-step-1-split.html": "04", "05-step-2-identify.html": "05", "06-step-3-ask.html": "06",
      "07-step-4-score.html": "07", "08-step-5-delete.html": "08", "09-the-output.html": "09",
      "10-measured.html": "10", "11-messy-ones.html": "11", "12-powered-by-close.html": "12"}
HOLD = 0.52
# beats deliberately added after the baseline was captured
ADDED = {
    "05-step-2-identify.html": [("eyebrow entrance (was static)", HOLD)],
    "07-step-4-score.html":    [("eyebrow entrance (was static)", HOLD)],
    "08-step-5-delete.html":   [("eyebrow entrance (was static)", HOLD)],
    "09-the-output.html":      [("eyebrow fade-out at the push-in", None)],  # P(ZOOM_AT)=P(3.0)
    "10-measured.html":        [("scope qualifier entrance", "P6.2")],
}
# beats deliberately REMOVED after the baseline was captured
REMOVED = {
    "10-measured.html": [("ghost backdrop entrance - the element was removed", 0.0)],
}
# Frames where beats were deliberately REMOVED in bulk. The check then asserts that every
# surviving beat is still at its expected position (a subset of the expected multiset),
# which proves nothing MOVED and only the declared removals happened - rather than
# loosening the comparison, which would stop it detecting a retime error.
# Beats deliberately MOVED, declared with their old and new offsets so a move cannot
# pass as a coincidence and a retime error cannot pass as a declared move.
MOVED = {
    "07-step-4-score.html": [
        ("row value entrance, +0.10 -> +0.45 after the cue so it lands after the mark "
         "is drawn", [9.7, 12.5, 15.2, 17.9], 0.10, 0.45),
    ],
}
BULK_REMOVED = {
    "07-step-4-score.html": (12, "the four per-row counting figures (0.94 / 0.95 / 0.95 / "
                                 "0.90) were invented - 3 tweens each: the value counter, "
                                 "its scale, and the seek-safe landing"),
}
TOL = 0.008


def main(before, after):
    B, A = json.load(open(before)), json.load(open(after))
    ok = True
    print(f"{'frame':26s} {'beats':>6s} {'total':>8s} {'take':>8s} {'held':>5s} {'added':>5s} {'unmatched':>9s}")
    for f, lid in FR.items():
        b, a = B[f], A[f]
        if "error" in a:
            print("FAIL", f, a["error"], a.get("page_errors")); ok = False; continue
        r = R.remap(lid)
        exp, held = [], 0
        for ob in b["beats"]:
            t = r(ob["start"])
            if any("eyebrow" in str(x) for x in ob["targets"]) and t < HOLD:
                t = HOLD; held += 1
            exp.append(round(t, 3))
        for label, fixed in ADDED.get(f, []):
            if fixed == "P6.2":
                exp.append(round(r(6.2), 3))
            else:
                exp.append(round(fixed if fixed is not None else r(3.0), 3))
        for label, cues, off_old, off_new in MOVED.get(f, []):
            for c in cues:
                # NB: not `a` - that name holds the after-table in the enclosing scope,
                # and reusing it turned a dict into a float two lines later.
                t_from, t_to = round(r(c + off_old), 3), round(r(c + off_new), 3)
                if t_from in exp:
                    exp.remove(t_from); exp.append(t_to)
                else:
                    print(f"      MOVED {label}: no beat at {t_from} to move")
        for label, at in REMOVED.get(f, []):
            if round(at, 3) in exp:
                exp.remove(round(at, 3))
            else:
                print(f"      REMOVAL {label}: no beat at {at} to remove - declaration is wrong")
        got = sorted(x["start"] for x in a["beats"])
        exp.sort()
        unmatched = []
        if f in BULK_REMOVED:
            n_rm, why = BULK_REMOVED[f]
            if len(exp) - len(got) != n_rm:
                unmatched.append(f"declared {n_rm} removed, actual drop {len(exp)-len(got)}")
            pool = list(exp)
            for g in got:
                hit = next((e for e in pool if abs(g - e) <= TOL), None)
                if hit is None:
                    unmatched.append(f"surviving beat {g} is not at any expected position")
                else:
                    pool.remove(hit)
        elif len(got) != len(exp):
            unmatched.append(f"count {len(got)} vs {len(exp)}")
        else:
            for g, e in zip(got, exp):
                if abs(g - e) > TOL:
                    unmatched.append(f"{g} vs {e}")
        print(f"{f:26s} {a['n']:6d} {a['total']:8.3f} {r.new_dur:8.3f} {held:5d} "
              f"{len(ADDED.get(f, [])) - len(REMOVED.get(f, [])) - (BULK_REMOVED.get(f, (0,))[0]):5d} {len(unmatched):9d}")
        for u in unmatched[:5]:
            print("     ", u)
        if unmatched: ok = False
        if abs(a["total"] - r.new_dur) > 0.02:
            print(f"      FAIL total {a['total']} != take {r.new_dur}"); ok = False

    # negative control: the same comparison against another line's map must fail
    b, a = B["01-powered-by.html"], A["01-powered-by.html"]
    rw = R.remap("07")
    exp = sorted(round(rw(x["start"]), 3) for x in b["beats"])
    got = sorted(x["start"] for x in a["beats"])
    worst = max(abs(g - e) for g, e in zip(got, exp))
    print(f"\nNEGATIVE CONTROL (frame 01 vs line 07's map): worst {worst:.3f} -> "
          f"{'DETECTED' if worst > TOL else 'NOT DETECTED - CHECK IS DECORATION'}")
    if worst <= TOL: ok = False
    print("\nVERIFY", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
