#!/usr/bin/env python3
"""Static geometric overlap check on authored rectangles and their animated positions.

The defect this exists for: `#bd-idx` and `#bd-inf` were both authored at
`left:870 top:640`, 170x110, and animated to positions 30px apart - a 73% area overlap,
present in every render, invisible to the lint, the motion check, the contrast check and
the ink measure. It was found by a human cropping one frame.

It is arithmetic, so it does not need a render and it finds EVERY phase at once. That
matters more than the one defect: fixing a sibling instance by hand feels like closing
the class and is not, so the check has to enumerate rather than the author remember.

What it reads: `left/top/width/height` from inline styles, plus `x:`/`y:` offsets from
`tl.to` / `tl.fromTo` / `gsap.set` calls on that element. Elements that are never on
screen at the same time cannot collide, so pairs are only compared when their on-screen
windows overlap - derived from the autoAlpha timeline, not assumed.

Usage: .venv/bin/python videos/_motifs/check_overlap.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
AREA_CEIL = 0.35          # fraction of the smaller element that may be covered
SHIPPED = {"body-of-knowledge", "one-engine-every-door", "retrieval-narrowing",
           "threads-and-quality"}

STYLE_EL = re.compile(
    r'<div[^>]*id="([\w-]+)"[^>]*style="([^"]*)"', re.S)
NUM = lambda s, k: (float(m.group(1)) if (m := re.search(rf"{k}\s*:\s*(-?[\d.]+)px", s))
                    else None)
MOVE = re.compile(r'(?:tl\.(?:to|fromTo)|gsap\.set)\(\s*"#([\w-]+)"\s*,([^;]*?)\)\s*;', re.S)
XY = re.compile(r"\b([xy])\s*:\s*(-?[\d.]+)")
ALPHA = re.compile(r"autoAlpha\s*:\s*([\d.]+)")
OPTOUT = re.compile(r"OVERLAP-BY-DESIGN\s+([\w-]+)\s*\+\s*([\w-]+)")


CONST = re.compile(r"const\s+(AT_[A-Z0-9_]+)\s*=\s*([\d.]+)")
CALL_POS = re.compile(
    r'(?:tl\.(?:to|fromTo)|gsap\.set)\(\s*"#([\w-]+)"\s*,(.*?)\)\s*;', re.S)


def consts_of(text):
    return {k: float(v) for k, v in CONST.findall(text)}


def pos_of(tok, consts):
    tok = tok.strip().rstrip(")").strip()
    if re.fullmatch(r"[\d.]+", tok):
        return float(tok)
    m = re.fullmatch(r"(AT_[A-Z0-9_]+)\s*([-+])\s*([\d.]+)", tok)
    if m and m.group(1) in consts:
        return consts[m.group(1)] + (float(m.group(3)) if m.group(2) == "+"
                                     else -float(m.group(3)))
    return consts.get(tok)


def timeline(text):
    """Per element: the rectangles it occupies WHILE VISIBLE, and the intervals it is
    visible for. A base position counts only if the element is raised without being
    moved in the same call - otherwise it is never on screen there, which is what made
    the first version report six pairs that never share the frame."""
    consts = consts_of(text)
    base = {}
    for eid, style in STYLE_EL.findall(text):
        l, t = NUM(style, "left"), NUM(style, "top")
        w, h = NUM(style, "width"), NUM(style, "height")
        if None not in (l, t, w, h):
            base[eid] = (l, t, w, h)

    events = {}
    for m in CALL_POS.finditer(text):
        eid, body = m.group(1), m.group(2)
        parts = body.rsplit(",", 1)
        t = pos_of(parts[-1], consts) if len(parts) > 1 else 0.0
        a = ALPHA.findall(body)
        xy = dict(XY.findall(body))
        events.setdefault(eid, []).append(
            (0.0 if t is None else t,
             float(a[-1]) if a else None,
             float(xy.get("x", "nan")) if "x" in xy else None,
             float(xy.get("y", "nan")) if "y" in xy else None))

    vis, rect = {}, {}
    for eid, evs in events.items():
        evs.sort(key=lambda e: e[0])
        l, t0, w, h = base.get(eid, (0.0, 0.0, 0.0, 0.0))
        dx = dy = 0.0
        first_alpha = next((a for _, a, _, _ in evs if a is not None), None)
        on = 0.0 if first_alpha == 0 else None
        for when, alpha, x, y in evs:
            if x is not None:
                dx = x
            if y is not None:
                dy = y
            if alpha is not None:
                if alpha > 0 and on is None:
                    on = when
                elif alpha == 0 and on is not None:
                    vis.setdefault(eid, []).append((on, when))
                    on = None
            if on is not None and eid in base:
                rect.setdefault(eid, set()).add((l + dx, t0 + dy, w, h))
        if on is not None:
            vis.setdefault(eid, []).append((on, 1e6))
            if eid in base:
                rect.setdefault(eid, set()).add((l + dx, t0 + dy, w, h))
    return rect, vis


def ancestry(text):
    """id -> set of ancestor ids, by walking the markup. Containment is NOT collision:
    a boundary holding its own table is the design. And a PARENT's autoAlpha applies to
    its descendants, so a child whose parent was faded is not on screen either - which
    is what left three containment pairs reported after the time-awareness pass."""
    stack, anc = [], {}
    for m in re.finditer(r'<div\b([^>]*)>|</div>', text):
        if m.group(0) == "</div>":
            if stack:
                stack.pop()
            continue
        attrs = m.group(1) or ""
        if attrs.rstrip().endswith("/"):
            continue
        idm = re.search(r'id="([\w-]+)"', attrs)
        eid = idm.group(1) if idm else None
        if eid:
            anc[eid] = {x for x in stack if x}
        stack.append(eid)
    return anc


def co_present(vis, a, b):
    for s1, e1 in vis.get(a, []):
        for s2, e2 in vis.get(b, []):
            if min(e1, e2) - max(s1, s2) > 0.15:   # more than a crossfade
                return True
    return False


def overlap(r1, r2):
    ox = min(r1[0] + r1[2], r2[0] + r2[2]) - max(r1[0], r2[0])
    oy = min(r1[1] + r1[3], r2[1] + r2[3]) - max(r1[1], r2[1])
    if ox <= 0 or oy <= 0:
        return 0.0
    return (ox * oy) / min(r1[2] * r1[3], r2[2] * r2[3])


def scan(path):
    text = path.read_text()
    R, VIS = timeline(text)
    ANC = ancestry(text)
    # a parent's visibility window applies to its children
    for eid in list(VIS):
        for par in ANC.get(eid, ()):
            if par in VIS:
                VIS[eid] = [(max(s1, s2), min(e1, e2))
                            for s1, e1 in VIS[eid] for s2, e2 in VIS[par]
                            if min(e1, e2) > max(s1, s2)]
    opt = {tuple(sorted(p)) for p in OPTOUT.findall(text)}
    found = []
    ids = sorted(R)
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            if tuple(sorted((a, b))) in opt:
                continue
            if a in ANC.get(b, ()) or b in ANC.get(a, ()):
                continue        # containment is not collision
            if not co_present(VIS, a, b):
                continue
            worst = max((overlap(ra, rb) for ra in R[a] for rb in R[b]), default=0.0)
            if worst > AREA_CEIL:
                found.append((a, b, worst))
    return sorted(found, key=lambda f: -f[2])


CONTROL_HIT = '''<div id="root">
  <div id="c-a" style="left:100px; top:100px; width:170px; height:110px;"></div>
  <div id="c-b" style="left:100px; top:130px; width:170px; height:110px;"></div>
  <script>tl.to("#c-a",{autoAlpha:1},1);tl.to("#c-b",{autoAlpha:1},1);</script></div>'''
CONTROL_MOVE = '''<div id="root">
  <div id="c-a" style="left:100px; top:100px; width:170px; height:110px;"></div>
  <div id="c-b" style="left:100px; top:100px; width:170px; height:110px;"></div>
  <script>tl.to("#c-a",{x:320,y:-40,autoAlpha:1},1);
          tl.to("#c-b",{x:340,y:-40,autoAlpha:1},1);</script></div>'''
CONTROL_CLEAR = '''<div id="root">
  <div id="c-a" style="left:100px; top:100px; width:170px; height:110px;"></div>
  <div id="c-b" style="left:900px; top:100px; width:170px; height:110px;"></div>
  <script>tl.to("#c-a",{autoAlpha:1},1);tl.to("#c-b",{autoAlpha:1},1);</script></div>'''
CONTROL_OPT = '''<div id="root">
  <!-- OVERLAP-BY-DESIGN c-a + c-b: a badge deliberately sits on its token -->
  <div id="c-a" style="left:100px; top:100px; width:170px; height:110px;"></div>
  <div id="c-b" style="left:100px; top:130px; width:170px; height:110px;"></div>
  <script>tl.to("#c-a",{autoAlpha:1},1);tl.to("#c-b",{autoAlpha:1},1);</script></div>'''


def selftest():
    import tempfile
    print("--- selftest: each case declares FIRE or QUIET up front ---")
    bad = []
    for name, src, want in (("stacked rectangles must FIRE", CONTROL_HIT, True),
                            ("overlap created by a MOVE must FIRE", CONTROL_MOVE, True),
                            ("separated rectangles stay QUIET", CONTROL_CLEAR, False),
                            ("an opted-out pair stays QUIET", CONTROL_OPT, False)):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "c.html"
            p.write_text(src)
            got = scan(p)
            ok = bool(got) == want
            print(f"  {'PASS' if ok else 'FAIL'}  {name}: {[(a,b,round(o,2)) for a,b,o in got]}")
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
    print(f"--- overlap scan, {len(comps)} composition(s), ceiling {AREA_CEIL} ---")
    print(f"  DOMAIN: the 7 motifs this film owns. The shipped library motifs "
          f"({', '.join(sorted(SHIPPED))})\n          are reported but not gated - "
          f"they ship with a delivered film.")
    print("  declared blind class: co-presence is inferred from autoAlpha raises, not "
          "from a\n          timeline solve, so a pair that never shares the screen may "
          "still be reported.")
    total = 0
    for c in comps:
        f = scan(c)
        gated = c.parent.name not in SHIPPED
        if f:
            print(f"  {'FAIL' if gated else 'note'}  {c.parent.name}")
            for a, b, o in f:
                print(f"          #{a} + #{b} overlap {o * 100:.0f}% of the smaller "
                      f"element")
            if gated:
                total += len(f)
        else:
            print(f"  PASS  {c.parent.name}")
    print(f"\n{total} gated overlap(s). Opt out a deliberate one with the comment "
          f"'OVERLAP-BY-DESIGN <idA> + <idB>: <why>'.")
    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main()
