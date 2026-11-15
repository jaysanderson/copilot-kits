#!/usr/bin/env python3
"""Convert initial-state `tl.set(target, {...}, 0)` calls to immediate `gsap.set(...)`.

HyperFrames' own lint: a zero-duration set at position 0 inside a PAUSED timeline does
not render while the playhead sits exactly at 0, so frame 0 shows the UN-hidden state.
Frame 0 is the poster frame, so this is not cosmetic.

Only calls whose position argument is exactly `0` are converted - a set at any other
position is a real timeline event and is left alone. Prints a per-file count, and exits
non-zero if it cannot parse a call it matched, so a silent partial conversion is not
possible.

Usage:  .venv/bin/python videos/_motifs/fix_initial_states.py <file> [<file> ...]
"""
import re
import sys
from pathlib import Path

# tl.set( ... , 0 )  - the target and vars may span lines; the position must be bare 0.
CALL = re.compile(r"\b(?P<tlvar>tl|tt)\.set\(", re.M)


def convert(text: str):
    """Return (new_text, converted, skipped). Scans for tl.set(/tt.set( and walks the
    parentheses so multi-line calls are handled correctly rather than by a line regex."""
    out = []
    i = 0
    converted = skipped = 0
    for m in CALL.finditer(text):
        if m.start() < i:
            continue
        open_paren = m.end() - 1
        depth = 0
        j = open_paren
        while j < len(text):
            ch = text[j]
            if ch in "([{":
                depth += 1
            elif ch in ")]}":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        if j >= len(text):
            sys.exit(f"unbalanced {m.group(0)} at offset {m.start()}")
        args = text[open_paren + 1:j]
        # split the top-level arguments
        parts, depth2, last = [], 0, 0
        for k, ch in enumerate(args):
            if ch in "([{":
                depth2 += 1
            elif ch in ")]}":
                depth2 -= 1
            elif ch == "," and depth2 == 0:
                parts.append(args[last:k])
                last = k + 1
        parts.append(args[last:])
        if len(parts) >= 3 and parts[-1].strip() == "0":
            new_args = ",".join(parts[:-1])
            out.append(text[i:m.start()])
            out.append(f"gsap.set({new_args})")
            i = j + 1
            converted += 1
        else:
            skipped += 1
    out.append(text[i:])
    return "".join(out), converted, skipped


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: fix_initial_states.py <file> [<file> ...]")
    total_c = total_s = 0
    for a in sys.argv[1:]:
        p = Path(a)
        t = p.read_text()
        new, c, s = convert(t)
        if c:
            p.write_text(new)
        print(f"  {p.name:34} converted {c:3d} initial set(s), left {s:3d} timed set(s)")
        total_c += c
        total_s += s
    print(f"\n{total_c} converted, {total_s} timed sets left in place")
    if total_c == 0:
        sys.exit("nothing converted - either already done, or the matcher is broken; "
                 "zero of zero is not a pass")


if __name__ == "__main__":
    main()
