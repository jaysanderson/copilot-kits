#!/usr/bin/env python3
"""Find elements that are brought ON screen and never taken off: the ghost class.

A motif phase is "cleared" by the author animating its elements to autoAlpha 0. Two ways
that fails silently:

  1. a legend's TEXT and its ARTWORK live in different parents, the author clears the
     parent they think of as "the legend", and the other orphans (m-jy: #jy-leg was
     faded, the SVG swatches #jy-lg0..3 and #jy-lgq never were);
  2. the author DIMS instead of clearing (autoAlpha 0.25), which leaves readable debris
     under the next phase.

Neither is visible to a lint that checks selectors resolve, nor to a motion check, nor
to an illustration-share metric. It is visible here.

Reports, per composition:
  ORPHAN  - raised above 0 and never returned to 0 before the composition ends
  DIMMED  - lowered to a nonzero value and left there (readable debris)

Exits non-zero if any orphan is found. Ships with controls.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# tl.to(target, {...}, pos) / gsap.set(target, {...})
CALL = re.compile(r"\b(?:tl\.(?:to|fromTo|set)|gsap\.set)\s*\(")
ID_IN_STR = re.compile(r'"#([A-Za-z0-9_-]+)"')
VARNAME = re.compile(r'"#([A-Za-z0-9_-]+)"\s*\+')
ALPHA = re.compile(r"autoAlpha\s*:\s*([\d.]+)")
DUR = re.compile(r'data-duration="([\d.]+)"')


def args_of(text, open_paren):
    depth, j = 0, open_paren
    while j < len(text):
        if text[j] in "([{":
            depth += 1
        elif text[j] in ")]}":
            depth -= 1
            if depth == 0:
                break
        j += 1
    inner = text[open_paren + 1:j]
    parts, d2, last = [], 0, 0
    for k, ch in enumerate(inner):
        if ch in "([{":
            d2 += 1
        elif ch in ")]}":
            d2 -= 1
        elif ch == "," and d2 == 0:
            parts.append(inner[last:k])
            last = k + 1
    parts.append(inner[last:])
    return parts, j


def scan(text):
    """Return {id: [(position_or_None, alpha), ...]} in source order."""
    events = {}
    order = 0
    for m in CALL.finditer(text):
        parts, _ = args_of(text, m.end() - 1)
        if len(parts) < 2:
            continue
        target, vars_blob = parts[0], " ".join(parts[1:-1]) if len(parts) > 2 else parts[1]
        a = ALPHA.search(vars_blob)
        if not a:
            continue
        alpha = float(a.group(1))
        # Ids addressed literally, MINUS the ones that are really family prefixes
        # ("#jy-pill" + i). The first version tested each id against a string it built
        # itself, which always matched, so every id was filtered out and the scanner
        # found nothing - including in its own controls, which is how it was caught.
        fams = set(VARNAME.findall(target))
        ids = [i for i in ID_IN_STR.findall(target) if i not in fams]
        # a family cleared as a family is not an orphan; track it as one entity
        ids += [f + "*" for f in fams]
        for i in set(ids):
            events.setdefault(i, []).append((order, alpha))
        order += 1
    return events


def check(path):
    text = path.read_text()
    ev = scan(text)
    orphans, dimmed = [], []
    for eid, seq in ev.items():
        seq.sort()
        raised = [a for _, a in seq if a > 0]
        if not raised:
            continue
        last = seq[-1][1]
        if last > 0:
            (orphans if last >= 0.9 else dimmed).append((eid, last))
    return sorted(orphans), sorted(dimmed)


CONTROL_ORPHAN = '''<div id="root" data-duration="10">
  <div id="a-lab"></div><svg><path id="a-swatch"/></svg>
  <script>
    gsap.set("#a-lab", { autoAlpha: 0 });
    gsap.set("#a-swatch", { autoAlpha: 0 });
    tl.to("#a-lab", { autoAlpha: 1 }, 1);
    tl.to("#a-swatch", { autoAlpha: 1 }, 1);
    tl.to("#a-lab", { autoAlpha: 0 }, 5);
  </script></div>'''      # a-swatch orphans: raised, never cleared

CONTROL_CLEAN = '''<div id="root" data-duration="10">
  <div id="a-lab"></div><svg><path id="a-swatch"/></svg>
  <script>
    gsap.set("#a-lab", { autoAlpha: 0 });
    gsap.set("#a-swatch", { autoAlpha: 0 });
    tl.to("#a-lab", { autoAlpha: 1 }, 1);
    tl.to("#a-swatch", { autoAlpha: 1 }, 1);
    tl.to("#a-lab", { autoAlpha: 0 }, 5);
    tl.to("#a-swatch", { autoAlpha: 0 }, 5);
  </script></div>'''

CONTROL_DIM = '''<div id="root" data-duration="10">
  <div id="a-lab"></div>
  <script>
    gsap.set("#a-lab", { autoAlpha: 0 });
    tl.to("#a-lab", { autoAlpha: 1 }, 1);
    tl.to("#a-lab", { autoAlpha: 0.25 }, 5);
  </script></div>'''


def selftest():
    import tempfile
    print("--- selftest: each case declares FIRE or QUIET up front ---")
    bad = []
    for name, src, want_orphan, want_dim in (
            ("orphaned swatch must FIRE", CONTROL_ORPHAN, True, False),
            ("fully cleared must stay QUIET", CONTROL_CLEAN, False, False),
            ("dimmed-not-cleared must FIRE as DIMMED", CONTROL_DIM, False, True)):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "c.html"
            p.write_text(src)
            o, d = check(p)
            ok = (bool(o) == want_orphan) and (bool(d) == want_dim)
            print(f"  {'PASS' if ok else 'FAIL'}  {name}: orphans={o} dimmed={d}")
            if not ok:
                bad.append(name)
    if bad:
        sys.exit(f"SCANNER DEFECT: {bad}")
    print()


def main():
    selftest()
    comps = sorted(ROOT.glob("*/composition.html"))
    if not comps:
        sys.exit("no compositions - zero of zero is not a pass")
    print(f"--- scanning {len(comps)} composition(s) for the ghost class ---")
    total_o = total_d = 0
    for c in comps:
        o, d = check(c)
        total_o += len(o)
        total_d += len(d)
        flag = "FAIL" if o else ("warn" if d else "PASS")
        print(f"  {flag:4}  {c.parent.name}")
        for eid, a in o:
            print(f"          ORPHAN  #{eid} left at autoAlpha {a}")
        for eid, a in d:
            print(f"          DIMMED  #{eid} left at autoAlpha {a} (readable debris)")
    print(f"\n{len(comps)} composition(s): {total_o} orphan(s), {total_d} dimmed")
    sys.exit(1 if total_o else 0)


if __name__ == "__main__":
    main()
