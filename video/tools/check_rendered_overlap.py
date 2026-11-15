#!/usr/bin/env python3
"""Overlap and text-overflow check on RENDERED extents, not authored rectangles.

WHY THIS EXISTS. `videos/_motifs/check_overlap.py` says so in its own first line:
"Static geometric overlap check on authored rectangles". It regex-parses `style="..."`.
So it compares the boxes an author DECLARED, and it cannot see:

  - text that OVERFLOWS its box (a 268px div holding 288px of text),
  - text that WRAPS to a second line and collides with the row beneath,
  - anything positioned or sized at runtime,
  - a STROKE crossing a label, which is not a box overlap at all.

That blind class is not hypothetical. One film's authored-rect check passed all 17
compositions while a viewer found ten collisions in the rendered film, including a
legend printing "AVAILABLE TODAY" over "ISV BUILDS". Another had a curve run through a
label so the glyphs read "Ret/ieval Agent".

AND IT IS REACHABLE BY CONSTRUCTION WHENEVER TYPE IS RAISED. Raising a film to a
legibility floor widens every string in it. The two checks are complementary: the static
one finds declared collisions before anything renders, this one finds what layout
actually did.

Usage:
    check_rendered_overlap.py <composition.html> [more.html ...] [--times 2,6,10]
"""
import argparse
import re
import sys
from pathlib import Path

ROOT = Path("/Users/user/Claude/ARAG-PMK-1")

# Pairs that are MEANT to sit on top of each other are opted out by a comment in the
# composition, the same convention the static checker uses:
#     OVERLAP-BY-DESIGN <idA> + <idB>: <why>
OPTOUT = re.compile(r"OVERLAP-BY-DESIGN\s+([\w-]+)\s*\+\s*([\w-]+)\s*:")

JS_MEASURE = """() => {
  const vis = e => {
    const cs = getComputedStyle(e);
    if (cs.visibility === 'hidden' || parseFloat(cs.opacity) < 0.05) return false;
    for (let n = e.parentElement; n; n = n.parentElement) {
      const p = getComputedStyle(n);
      if (p.visibility === 'hidden' || parseFloat(p.opacity) < 0.05) return false;
    }
    return true;
  };
  const out = [];
  document.querySelectorAll('div,span,p').forEach(e => {
    if (!vis(e)) return;
    const r = e.getBoundingClientRect();
    if (r.width < 4 || r.height < 4) return;
    const cs = getComputedStyle(e);
    const txt = (e.textContent || '').trim();
    const leaf = e.children.length === 0;
    // OVERFLOW: the text is wider than the box that is supposed to hold it.
    // WRAP: the rendered height exceeds one line of its own line-height.
    const fs = parseFloat(cs.fontSize) || 0;
    const lh = parseFloat(cs.lineHeight) || (fs * 1.2);
    const overflow = leaf && txt ? Math.max(0, e.scrollWidth - e.clientWidth) : 0;
    const vclip = leaf && txt ? Math.max(0, e.scrollHeight - e.clientHeight) : 0;
    // COUNT VISUAL LINES FROM THE TEXT ITSELF, not from the box height. The first
    // version used Math.round(height / lineHeight), which counts a FIXED-HEIGHT box as
    // multi-line whenever the box is taller than one line - a 60px flex container
    // holding one 32px line reported 2, and that produced nine false WRAP findings on
    // the first run. A Range over the element's contents returns one client rect PER
    // RENDERED LINE, which is the quantity the check actually names.
    let lines = 1, ink = null;
    if (leaf && txt) {
      const rg = document.createRange();
      rg.selectNodeContents(e);
      const rects = [...rg.getClientRects()];
      lines = Math.max(1, rects.length);
      // THE INK EXTENT, not the line box. An element's box includes line-height
      // leading and padding, so two stacked rows can overlap as BOXES while their
      // glyphs are comfortably clear - which is how raising type produced six
      // "TEXT OVERLAP" findings on a frame that looks correct to the eye. Compare
      // what is actually drawn: the union of the Range's own client rects.
      if (rects.length) {
        const L = Math.min(...rects.map(r2 => r2.left));
        const R = Math.max(...rects.map(r2 => r2.right));
        const T = Math.min(...rects.map(r2 => r2.top));
        const B = Math.max(...rects.map(r2 => r2.bottom));
        ink = {x: L, y: T, w: R - L, h: B - T};
      }
    }
    out.push({id: e.id || '', cls: (typeof e.className === 'string' ? e.className : ''),
              x: r.left, y: r.top, w: r.width, h: r.height,
              text: txt.slice(0, 40), leaf: leaf, hasText: leaf && !!txt, ink: ink,
              overflow: overflow, vclip: vclip, lines: lines, nowrap: cs.whiteSpace.includes('nowrap')});
  });
  return out;
}"""


def boxes_overlap(a, b, pad=0):
    return (a["x"] < b["x"] + b["w"] - pad and a["x"] + a["w"] > b["x"] + pad
            and a["y"] < b["y"] + b["h"] - pad and a["y"] + a["h"] > b["y"] + pad)


def selftest():
    """FIRE on overflow, FIRE on wrap, FIRE on a real overlap, QUIET on neighbours.

    THE FIXTURE IS THE POINT. These four shapes are what the product actually emits
    when type is raised against a fixed box, so any future implementation of this class
    inherits the controls instead of the blind spot. Derived from observed output - a
    268px box holding 288px of text - never from what a failure is imagined to look like.
    """
    cases = [
        ("a box whose text OVERFLOWS it", True,
         '<div id="c-a" style="position:absolute;left:0;top:0;width:120px;'
         'font-size:32px;white-space:nowrap;">AVAILABLE TODAY AND MORE</div>'),
        ("a box whose text WRAPS to a second line", True,
         '<div id="c-b" style="position:absolute;left:0;top:200px;width:120px;'
         'font-size:32px;line-height:38px;">AVAILABLE TODAY AND MORE</div>'),
        ("two boxes genuinely overlapping", True,
         '<div id="c-c" style="position:absolute;left:400px;top:0;width:200px;height:60px;'
         'background:#333;"></div>'
         '<div id="c-d" style="position:absolute;left:450px;top:20px;width:200px;height:60px;'
         'background:#555;"></div>'),
        ("a FIXED-HEIGHT box holding ONE line", False,
         '<div id="c-g" style="position:absolute;left:1200px;top:400px;width:430px;'
         'height:60px;display:flex;align-items:center;justify-content:center;'
         'font-size:32px;">Source documents</div>'),
        ("two boxes merely adjacent", False,
         '<div id="c-e" style="position:absolute;left:800px;top:0;width:100px;height:60px;'
         'background:#333;"></div>'
         '<div id="c-f" style="position:absolute;left:910px;top:0;width:100px;height:60px;'
         'background:#555;"></div>'),
    ]
    from playwright.sync_api import sync_playwright
    bad = []
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": 1920, "height": 1080}, device_scale_factor=1)
        for name, expect_fire, markup in cases:
            pg.set_content(f'<body style="margin:0;width:1920px;height:1080px;">{markup}</body>')
            pg.wait_for_timeout(60)
            els = pg.evaluate(JS_MEASURE)
            ids = {e["id"] for e in els if e["id"]}
            if not ids:
                bad.append(f"{name}: INERT PLANT - the markup produced no measurable element")
                continue
            fired = (any(e["overflow"] > 1 for e in els)
                     or any(e["hasText"] and e["lines"] > 1 for e in els)
                     or any(boxes_overlap(a, c) for i, a in enumerate(els)
                            for c in els[i + 1:]))
            tag = "FIRE " if expect_fire else "QUIET"
            ok = fired == expect_fire
            print(f"  selftest {tag} {name:<42} {'ok' if ok else 'WRONG'}")
            if not ok:
                bad.append(f"{name}: expected {'FIRE' if expect_fire else 'QUIET'}")
        b.close()
    if bad:
        for x in bad:
            print("  SELFTEST FAIL:", x)
        sys.exit("rendered-overlap selftest failed - no verdict below is trustworthy")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("comps", nargs="+")
    ap.add_argument("--times", default="")
    a = ap.parse_args()
    selftest()

    sys.path.insert(0, str(ROOT / "videos" / "exec-use-cases"))
    import render_probe as rp
    from playwright.sync_api import sync_playwright

    findings, wraps, examined = [], [], 0
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": 1920, "height": 1080}, device_scale_factor=1)
        for cp in a.comps:
            comp = Path(cp)
            src = comp.read_text()
            optouts = {frozenset(m) for m in OPTOUT.findall(src)}
            host = ROOT / "videos" / "exec-use-cases" / ".probe" / f"ro_{comp.parent.name}.html"
            host.parent.mkdir(exist_ok=True)
            host.write_text(rp.host_html(comp))
            pg.goto(host.as_uri())
            pg.wait_for_timeout(600)
            cid = pg.evaluate("Object.keys(window.__timelines)[0] || null")
            if not cid:
                findings.append(f"{comp.parent.name}: NO TIMELINE - not measured")
                continue
            dur = pg.evaluate(f"window.__timelines['{cid}'].duration()")
            times = ([float(t) for t in a.times.split(",")] if a.times
                     else [round(dur * f, 2) for f in (0.05, 0.2, 0.4, 0.6, 0.8, 0.95)])
            for t in times:
                pg.evaluate(f"window.__timelines['{cid}'].time({t}); gsap.ticker.tick();")
                pg.wait_for_timeout(60)
                els = pg.evaluate(JS_MEASURE)
                examined += 1
                for e in els:
                    if e["overflow"] > 1:
                        findings.append(f"{comp.parent.name} t={t}: '{e['text']}' "
                                        f"({e['id'] or e['cls']}) OVERFLOWS its box by "
                                        f"{e['overflow']}px")
                    # A WRAP IS NOT A DEFECT ON ITS OWN. "Source documents" on two
                    # lines inside a card sized for two lines is correct, and flagging
                    # it reported three benign labels as failures. The defect the lead
                    # specified is text wrapping INTO THE NEXT ROW - so a wrap fails
                    # only when it also OVERFLOWS its own box vertically. A wrap that
                    # fits is reported as information and carries no verdict.
                    if e["hasText"] and e["lines"] > 1 and not e["nowrap"]:
                        if e.get("vclip", 0) > 1:
                            findings.append(
                                f"{comp.parent.name} t={t}: '{e['text']}' "
                                f"({e['id'] or e['cls']}) WRAPS to {e['lines']} lines and "
                                f"OVERFLOWS its box vertically by {e['vclip']}px - it is "
                                f"in the row beneath")
                        else:
                            wraps.append(f"{comp.parent.name} t={t}: '{e['text']}' "
                                         f"wraps to {e['lines']} lines, fits its box")
                texts = [e for e in els if e["hasText"]]
                for e in texts:
                    for o in els:
                        if o is e or not o["id"] or not e["id"]:
                            continue
                        if frozenset((e["id"], o["id"])) in optouts:
                            continue
                        # compare INK to INK where both have it
                        ea, ob = e.get("ink") or e, o.get("ink") or o
                        if o["hasText"] and boxes_overlap(ea, ob, pad=1):
                            findings.append(f"{comp.parent.name} t={t}: TEXT OVERLAP "
                                            f"'{e['text']}' + '{o['text']}'")
        b.close()

    uniq = sorted(set(findings))
    print(f"\n{examined} frame(s) measured across {len(a.comps)} composition(s), "
          f"RENDERED extents at device scale 1.")
    if uniq:
        for f in uniq[:40]:
            print("  FAIL ", f)
        if len(uniq) > 40:
            print(f"  ... and {len(uniq) - 40} more")
        sys.exit(f"{len(uniq)} rendered-layout finding(s)")
    print("  PASS  no overflow, no unexpected wrap, no text-on-text overlap")
    if wraps:
        print(f"  {len(wraps)} wrap(s) that FIT their box, reported not failed:")
        for w in sorted(set(wraps))[:6]:
            print("    -", w)
    print("  BLIND CLASS, declared: this compares BOXES. A stroke crossing a label is "
          "not a box overlap and is not covered here.")
    sys.exit(0)


if __name__ == "__main__":
    main()
