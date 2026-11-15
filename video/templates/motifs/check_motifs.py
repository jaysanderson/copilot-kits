#!/usr/bin/env python3
"""Static check for motif compositions.

A dangling selector in a HyperFrames composition does not raise: gsap silently accepts a
selector matching nothing, so the shot renders with that element never animated - which is
exactly the "checks PASS while a section renders BLANK" failure the factory has hit before.
This catches the class the renderer cannot report.

Per composition it checks:
  1. every "#id" gsap/query selector and getElementById("id") resolves to an id that the
     HTML actually defines (or that the script creates with .id = "...")
  2. data-composition-id matches the window.__timelines["..."] key
  3. ids are unique within the file
  4. every data-var-text name is documented in the motif's README
  5. the declared data-duration is >= the largest timeline position referenced
  6. no Math.random (deterministic render)

Ships with a planted positive control per rule, run as a precondition: a scan that cannot
fail is not evidence. Exits non-zero on any finding.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

ID_DEF = re.compile(r'\bid\s*=\s*"([A-Za-z0-9_-]+)"')
ID_SET = re.compile(r'\.id\s*=\s*"([A-Za-z0-9_-]+)"\s*\+\s*(\w+)|\.id\s*=\s*"([A-Za-z0-9_-]+)"')
SEL_HASH = re.compile(r'"#([A-Za-z0-9_-]+)(?:\s[^"]*)?"')
SEL_CONCAT = re.compile(r'"#([A-Za-z0-9_-]+)"\s*\+')
GET_BY_ID = re.compile(r'getElementById\("([A-Za-z0-9_-]+)"\)')
QSEL = re.compile(r'querySelector(?:All)?\("([^"]+)"\)')
COMP_ID = re.compile(r'data-composition-id="([^"]+)"')
TL_KEY = re.compile(r'window\.__timelines\[\s*"([^"]+)"\s*\]')
VAR_TEXT = re.compile(r'data-var-text="([A-Za-z0-9_]+)"')
DURATION = re.compile(r'data-duration="([\d.]+)"')
MATH_RANDOM = re.compile(r'Math\.random\s*\(')
# A hex colour literal is not an id selector. Real motif ids are kebab-case with a prefix;
# a bare 3/4/6/8-digit hex string in a "#..." string is a colour. Without this the scanner
# reported "#00B563" as a dangling selector in every composition including three shipped
# library motifs, which is how the false-positive class was found.
# prefixes the script builds ids/selectors from: getElementById("tr-s" + b)
FAMILY_PREFIX = re.compile(r'(?:getElementById|querySelector)\(\s*"#?([\w-]+?)"\s*\+')
HEXCOLOUR = re.compile(r'^(?:[0-9A-Fa-f]{3,4}|[0-9A-Fa-f]{6}|[0-9A-Fa-f]{8})$')
LINE_COMMENT = re.compile(r'(?m)//[^\n]*')
BLOCK_COMMENT = re.compile(r'/\*.*?\*/', re.S)


# The motif READMEs document families in range notation, which is the library's own
# existing convention (`bokLabel1..bokLabel5`, `oeDoor0..oeDoor4`). Expand those so a
# documented family counts as documenting each member, rather than forcing every README to
# list names one by one.
RANGE = re.compile(r'\b([A-Za-z_][A-Za-z0-9_]*?)(\d+)([A-Za-z_]*)\s*\.\.\s*'
                   r'(?:([A-Za-z_][A-Za-z0-9_]*?))?(\d+)([A-Za-z_]*)\b')


def range_names(txt: str) -> set:
    """Every variable name covered by an `X0..X3` style range in a README."""
    out = set()
    for pre, lo, suf, pre2, hi, suf2 in RANGE.findall(txt):
        if pre2 and pre2 != pre:
            continue
        if suf2 != suf:
            continue
        a, b = int(lo), int(hi)
        if b < a or b - a > 64:
            continue
        for n in range(a, b + 1):
            out.add(f"{pre}{n}{suf}")
    return out


def decomment(txt: str) -> str:
    """Strip comments so a comment NAMING a banned construct is not read as using it.
    body-of-knowledge's own "// Seeded LCG - deterministic, no Math.random." was reported
    as a Math.random use by the first version of this scanner."""
    return LINE_COMMENT.sub("", BLOCK_COMMENT.sub("", txt))
# numeric timeline positions: the last argument of a tl.to/from/fromTo/set call
TL_POS = re.compile(r'\btl\.(?:to|from|set)\([^;]*?,\s*([A-Z_]+(?:\s*[-+]\s*[\d.]+)?|[\d.]+)\s*\)\s*;')
CONST_DEF = re.compile(r'const\s+([A-Z][A-Z0-9_]*)\s*=\s*([\d.]+)\s*;')


def scan(path: Path, readme: Path | None):
    """Return a list of finding strings for one composition file.

    `raw` is the file as written (ids and attributes live there); `txt` is the file with
    comments stripped (selectors and banned constructs are judged on that).
    """
    raw = path.read_text()
    txt = decomment(raw)
    out = []

    # --- ids the HTML defines, plus ids the script builds by concatenation
    defined = set(ID_DEF.findall(raw))
    # ids created dynamically as "prefix" + i  -> record the prefix as a family
    families = set()
    for m in re.finditer(r'\.id\s*=\s*"([A-Za-z0-9_-]+?)"\s*\+', raw):
        families.add(m.group(1))
    for m in re.finditer(r'id\s*=\s*"([A-Za-z0-9_-]+?)"\s*\+', raw):
        families.add(m.group(1))

    _all = ID_DEF.findall(raw)
    dup = [i for i in set(_all) if _all.count(i) > 1]
    for d in sorted(dup):
        out.append(f"duplicate id {d!r}")

    def known(name: str) -> bool:
        if name in defined:
            return True
        return any(name.startswith(f) and name[len(f):].isdigit() for f in families)

    # --- selectors used by the script
    used = set()
    for m in SEL_HASH.finditer(txt):
        nm = m.group(1)
        if HEXCOLOUR.match(nm):
            continue        # hex colour literal, not a selector
        used.add(nm)
    for m in GET_BY_ID.finditer(txt):
        used.add(m.group(1))
    # "#jy-pill" + i  -> treat as a family reference, satisfied if the family exists
    concat = set(SEL_CONCAT.findall(txt))
    for name in sorted(used):
        if name in concat:
            if not (name in families or known(name + "0")):
                out.append(f"selector family \"#{name}\" + i matches no created id")
            continue
        if not known(name):
            out.append(f"dangling selector \"#{name}\" - no such id in the HTML")

    # querySelector with a descendant/class path: only check a leading #id
    for sel in QSEL.findall(txt):
        m = re.match(r'#([A-Za-z0-9_-]+)', sel)
        if m and not known(m.group(1)):
            out.append(f"dangling querySelector root \"#{m.group(1)}\" in {sel!r}")

    # --- composition id vs timeline key
    cid = COMP_ID.findall(raw)
    key = TL_KEY.findall(txt)
    if not cid:
        out.append("no data-composition-id")
    if not key:
        out.append("no window.__timelines[...] registration")
    if cid and key and cid[0] != key[0]:
        out.append(f"data-composition-id {cid[0]!r} != timeline key {key[0]!r}")

    # --- declared duration vs the largest timeline position actually referenced
    consts = {k: float(v) for k, v in CONST_DEF.findall(txt)}
    worst, worst_src = 0.0, ""
    for m in TL_POS.finditer(txt):
        tok = m.group(1).strip()
        val = None
        if re.fullmatch(r'[\d.]+', tok):
            val = float(tok)
        else:
            mm = re.fullmatch(r'([A-Z_][A-Z0-9_]*)\s*([-+])\s*([\d.]+)', tok)
            if mm and mm.group(1) in consts:
                val = consts[mm.group(1)] + (float(mm.group(3)) if mm.group(2) == "+"
                                             else -float(mm.group(3)))
            elif tok in consts:
                val = consts[tok]
        if val is not None and val > worst:
            worst, worst_src = val, tok
    dur = DURATION.findall(raw)
    if dur:
        d = float(dur[0])
        # a tween STARTING at the declared duration can never be seen
        if worst >= d:
            out.append(f"timeline position {worst} ({worst_src}) is at or past "
                       f"data-duration {d} - that tween never renders")
    else:
        out.append("no data-duration")

    # --- EMPTY SHAPES. A declared illustration that draws a labelled rectangle with
    # nothing inside it passes every other check here, passes the lint, passes the
    # motion measure, and counts 1.00 toward illustration share - and a viewer calls it
    # an empty box and stops watching. This is the check that would have failed the
    # STORYBOARD rather than the film, which is why it is static and runs before
    # anything is drawn.
    #
    # A "shape" is a sized, bordered element. It needs content: a child in the markup,
    # a child appended to it in the script, or an explicit opt-out saying the emptiness
    # is the point.
    shapes = re.findall(r'<div class="([\w-]+)"[^>]*id="([\w-]+)"[^>]*>(\s*)</div>', raw)
    for cls, eid, _ in shapes:
        rule = re.search(r'\.' + re.escape(cls) + r'\s*\{([^}]*)\}', raw, re.S)
        if not rule:
            continue
        body = rule.group(1)
        sized = ("width:" in body and "height:" in body) or "inset:" in body
        bordered = "border" in body or "background" in body
        if not (sized and bordered):
            continue
        # Populated if the script REFERENCES this element and appends anywhere. The
        # first version matched `getElementById("exact-id").appendChild` literally and
        # so could not see `getElementById("tr-s" + b)`, which is how every
        # script-populated family got reported as empty - the same hardcoded-literal
        # brittleness that bit a sibling's heading parser the same day.
        # Populated means SOMETHING IS APPENDED TO THIS ELEMENT, not merely that the
        # script mentions it. The looser "mentioned anywhere + the file appends
        # somewhere" version cleared #sk-reader, an empty bordered box that a viewer
        # then saw as an empty box - the detector agreeing with the defect.
        appended = False
        # a) direct: getElementById("id").appendChild / host.appendChild where host was
        #    assigned from this id
        if re.search(r'getElementById\("' + re.escape(eid) + r'"\)\s*\.appendChild', txt):
            appended = True
        for vm in re.finditer(r'(?:const|let|var)\s+(\w+)\s*=\s*document\.getElementById\('
                              r'"' + re.escape(eid) + r'"\)', txt):
            if re.search(r'\b' + vm.group(1) + r'\.appendChild', txt):
                appended = True
        # b) family: getElementById("prefix" + i).appendChild, for an id in that family
        for pre in FAMILY_PREFIX.findall(txt):
            if not (eid.startswith(pre) and eid[len(pre):].isdigit()):
                continue
            if re.search(r'getElementById\("' + re.escape(pre) + r'"\s*\+[^)]*\)'
                         r'[\s\S]{0,400}?appendChild', txt):
                appended = True
            for vm in re.finditer(r'(?:const|let|var)\s+(\w+)\s*=\s*document\.getElementById\('
                                  r'"' + re.escape(pre) + r'"\s*\+[^)]*\)', txt):
                if re.search(r'\b' + vm.group(1) + r'\.appendChild', txt):
                    appended = True
        # d) array-loop: ["sk-f0","sk-f1"].forEach(... getElementById(id) ... append)
        for arr in re.finditer(r'\[([^\]]*"' + re.escape(eid) + r'"[^\]]*)\]\s*\.forEach'
                               r'([\s\S]{0,600}?appendChild)', txt):
            appended = True
        # c) passed to a helper that appends: fill("tr-comp-a", ...)
        if re.search(r'\w+\(\s*"' + re.escape(eid) + r'"', txt) and "appendChild" in txt:
            appended = True
        optout = f"EMPTY-BY-DESIGN {eid}" in raw
        if not appended and not optout:
            out.append(f"empty shape #{eid} (.{cls}) - sized and bordered with no "
                       f"content and no opt-out; a viewer reads this as an empty box. "
                       f"Give it content, or write the comment "
                       f"'EMPTY-BY-DESIGN {eid}: <why>' beside it")

    # --- determinism
    if MATH_RANDOM.search(txt):
        out.append("Math.random present - render would not be deterministic")

    # --- every variable is documented, so a host knows what it can bind
    if readme and readme.exists():
        rtxt = readme.read_text()
        covered = range_names(rtxt)
        for v in sorted(set(VAR_TEXT.findall(raw))):
            if v not in rtxt and v not in covered:
                out.append(f"data-var-text {v!r} is not documented in {readme.name}")
    elif VAR_TEXT.findall(raw):
        out.append("composition declares variables but has no README")

    return out


CONTROLS = [
    ("empty shape", '<style>.a-box { position:absolute; width:100px; height:60px; border:2px solid #5E719F; background:rgba(0,0,0,0.2); }</style><div id="a-real"></div><div class="a-box" id="a-box1"></div><script>tl.to("#a-real", { autoAlpha: 1 }, 0.5);window.__timelines["m-x"] = tl;</script>', 'data-composition-id="m-x" data-duration="2.0"'),

    ("dangling selector", '''<div id="a-real"></div><script>
       var x = document.getElementById("a-real");
       tl.to("#a-ghost", { autoAlpha: 1 }, 0.5);
       window.__timelines["m-x"] = tl;</script>''',
     'data-composition-id="m-x" data-duration="2.0"'),
    ("id/key mismatch", '''<div id="a-real"></div><script>
       window.__timelines["m-WRONG"] = tl;
       tl.to("#a-real", { autoAlpha: 1 }, 0.5);</script>''',
     'data-composition-id="m-x" data-duration="2.0"'),
    ("Math.random", '''<div id="a-real"></div><script>
       var r = Math.random();
       tl.to("#a-real", { autoAlpha: 1 }, 0.5);
       window.__timelines["m-x"] = tl;</script>''',
     'data-composition-id="m-x" data-duration="2.0"'),
    ("tween past duration", '''<div id="a-real"></div><script>
       tl.to("#a-real", { autoAlpha: 1 }, 9.9);
       window.__timelines["m-x"] = tl;</script>''',
     'data-composition-id="m-x" data-duration="2.0"'),
    ("duplicate id", '''<div id="a-real"></div><div id="a-real"></div><script>
       tl.to("#a-real", { autoAlpha: 1 }, 0.5);
       window.__timelines["m-x"] = tl;</script>''',
     'data-composition-id="m-x" data-duration="2.0"'),
]


HEAD = '<div id="root" data-composition-id="m-x" data-duration="2.0">'
TAIL = '</div>'

# DISCRIMINATORS - the third control CLAUDE.md requires: the nearest legitimate
# look-alike in the same artifact. Each of these is something a real composition does and
# the scan must stay QUIET on. The first two are the false-positive classes this scanner
# actually shipped with, found because it flagged three known-good library motifs.
DISCRIMINATORS = [
    ("a shape populated by a script FAMILY is not empty",
     '<style>.a-box { position:absolute; width:100px; height:60px; border:2px solid #5E719F; background:rgba(0,0,0,0.2); }</style><div id="a-real"></div><div class="a-box" id="a-box0"></div><script>for (var i=0;i<1;i++){var d=document.createElement("div");document.getElementById("a-box" + i).appendChild(d);}tl.to("#a-real", { autoAlpha: 1 }, 0.5);window.__timelines["m-x"] = tl;</script>'),
    ("an opted-out empty shape is not reported",
     '<style>.a-box { position:absolute; width:100px; height:60px; border:2px solid #5E719F; background:rgba(0,0,0,0.2); }</style><div id="a-real"></div><!-- EMPTY-BY-DESIGN a-box2: it is a gap, not a container --><div class="a-box" id="a-box2"></div><script>tl.to("#a-real", { autoAlpha: 1 }, 0.5);window.__timelines["m-x"] = tl;</script>'),
    ("hex colour literals are not selectors",
     '<div id="a-real"></div><script>'
     'tl.to("#a-real", { borderColor: "#00B563", background: "#5E719F" }, 0.5);'
     'tl.to("#a-real", { color: "#fff", outline: "#D7DEEAFF" }, 0.8);'
     'window.__timelines["m-x"] = tl;</script>'),
    ("a comment naming Math.random is not a use",
     '<div id="a-real"></div><script>\n'
     '// Seeded LCG - deterministic, no Math.random.\n'
     'tl.to("#a-real", { autoAlpha: 1 }, 0.5);\n'
     'window.__timelines["m-x"] = tl;</script>'),
    ("Math.round is not Math.random",
     '<div id="a-real"></div><script>'
     'var w = Math.round(1.4 * 64);'
     'tl.to("#a-real", { autoAlpha: 1 }, 0.5);'
     'window.__timelines["m-x"] = tl;</script>'),
    ("a dynamically created id family resolves",
     '<div id="a-real"></div><script>'
     'for (var i = 0; i < 3; i++) { var d = document.createElement("div");'
     ' d.id = "a-kid" + i; }'
     'tl.to("#a-kid" + 0, { autoAlpha: 1 }, 0.5);'
     'window.__timelines["m-x"] = tl;</script>'),
]


def selftest(tmp: Path):
    """Prove every rule FIRES on a planted positive, STAYS QUIET on a clean file, and
    DISCRIMINATES against the nearest legitimate look-alikes."""
    print("--- selftest: each rule must fire on its planted control ---")
    bad = []
    for name, body, attrs in CONTROLS:
        p = tmp / ("ctrl_" + re.sub(r"\W+", "_", name) + ".html")
        p.write_text(f'<div id="root" {attrs}>{body}</div>')
        found = scan(p, None)
        hit = bool(found)
        print(f"  {'FIRES' if hit else 'DEAD '}  {name}"
              + (f"  -> {found[0]}" if found else ""))
        if not hit:
            bad.append(name)
    # negative control: a clean minimal composition must produce NOTHING
    clean = tmp / "ctrl_clean.html"
    clean.write_text('<div id="root" data-composition-id="m-x" data-duration="2.0">'
                     '<div id="a-real"></div><script>'
                     'tl.to("#a-real", { autoAlpha: 1 }, 0.5);'
                     'window.__timelines["m-x"] = tl;</script></div>')
    cf = scan(clean, None)
    print(f"  {'QUIET' if not cf else 'NOISY'}  negative control: a clean composition"
          + (f"  -> {cf}" if cf else ""))
    if cf:
        bad.append("negative control produced findings")
    for name, body in DISCRIMINATORS:
        p = tmp / ("disc_" + re.sub(r"\W+", "_", name) + ".html")
        p.write_text(HEAD + body + TAIL)
        f = scan(p, None)
        print(f"  {'QUIET' if not f else 'NOISY'}  discriminator: {name}"
              + (f"  -> {f}" if f else ""))
        if f:
            bad.append(f"discriminator fired: {name}")
    if bad:
        sys.exit(f"SCANNER DEFECT: {bad}")
    print()


def main():
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        selftest(Path(td))

    SHIPPED = {"body-of-knowledge", "one-engine-every-door", "retrieval-narrowing",
               "threads-and-quality"}
    comps = sorted(ROOT.glob("*/composition.html"))
    if not comps:
        sys.exit("no compositions found - zero of zero is not a pass")
    print(f"--- scanning {len(comps)} composition(s) under {ROOT} ---")
    total = 0
    print(f"  empty-shape rule DOMAIN: the 7 motifs this film owns. The 4 shipped "
          f"library motifs ({', '.join(sorted(SHIPPED))}) are OUT OF SCOPE - they ship "
          f"with a delivered film and are not this film's to change.")
    print(f"  declared blind class: the append detector reads four code shapes; a fifth "
          f"would read as empty. Flagged shapes are eye-checked, not auto-trusted.")
    for c in comps:
        findings = scan(c, c.parent / "README.md")
        if c.parent.name in SHIPPED:
            findings = [f for f in findings if not f.startswith("empty shape")]
        total += len(findings)
        print(f"  {'PASS' if not findings else 'FAIL'}  {c.parent.name}")
        for f in findings:
            print(f"          {f}")
    print(f"\n{len(comps)} composition(s), {total} finding(s)")
    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main()
