#!/usr/bin/env python3
"""Inventory every AUTHORED type size, rendered, and report it at delivery scale.

Authored pixels are not the unit the verdict is made in. A 1920-wide frame shown
at 390 CSS px scales by 0.2031, so the floor is derived from the smallest thing
that must be READ on a phone and converted back, rather than set just under
whatever currently passes.

STATED LIMIT, and it is the important half: this reads the DOM, so it sees only
authored type. Every word inside a captured screenshot is invisible to it, and
that is exactly where this film's evidence lives. Treat a clean result here as
"the authored layer is sized", never as "the film is legible".
"""
import json, pathlib, re, sys, urllib.request
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).parent
PHONE = 390 / 1920            # 0.2031
READ_FLOOR_PHONE = 11.0       # smallest glyph a person reads on a phone held at arm's length
H = """<!DOCTYPE html><html><head><meta charset="utf-8">
<style>html,body{margin:0;width:1920px;height:1080px;overflow:hidden;background:#00216B}</style>
<script>GSAP</script></head><body><div id="mount"></div></body></html>"""


def main():
    g = ROOT / ".beats-gsap.js"
    if not g.exists():
        urllib.request.urlretrieve("https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js", g)
    shell = ROOT / "_type_harness.html"
    shell.write_text(H.replace("GSAP", g.read_text()))
    rows = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1920, "height": 1080}, device_scale_factor=1)
        for f in sorted((ROOT / "compositions/frames").glob("*.html")):
            src = f.read_text()
            body = re.sub(r'<script src="[^"]*gsap[^"]*"></script>', "",
                          re.search(r"<template[^>]*>(.*)</template>", src, re.S).group(1))
            cid = re.search(r'data-composition-id="([^"]+)"', body).group(1)
            pg.goto(shell.as_uri())
            pg.evaluate("""({body}) => {
                window.__timelines = {};
                document.getElementById('mount').innerHTML = body;
                document.querySelectorAll('#mount script').forEach(s => {
                  const n = document.createElement('script'); n.textContent = s.textContent;
                  document.body.appendChild(n);
                });
            }""", {"body": body})
            pg.wait_for_timeout(900)
            pg.evaluate("""(cid) => { const t = window.__timelines[cid];
                            if (t) t.seek(t.duration() - 0.3, false); }""", cid)
            pg.wait_for_timeout(300)
            got = pg.evaluate("""() => [...document.querySelectorAll('#mount *')]
                .filter(e => !e.children.length && (e.innerText || '').trim()
                             && getComputedStyle(e).visibility !== 'hidden'
                             && parseFloat(getComputedStyle(e).opacity) > 0.05)
                .map(e => ({sel: e.id || e.className || e.tagName,
                            fs: parseFloat(getComputedStyle(e).fontSize),
                            op: parseFloat(getComputedStyle(e).opacity),
                            t: (e.innerText || '').trim().slice(0, 34)}))""")
            for r in got:
                rows.append({"frame": f.stem, **r})
        b.close()
    shell.unlink(missing_ok=True)
    if not rows:
        sys.exit("no type found - a scale audit over nothing is not a pass")

    need = READ_FLOOR_PHONE / PHONE
    print(f"authored floor to clear {READ_FLOOR_PHONE:.0f}px on a 390px phone: "
          f"{need:.0f}px authored (scale {PHONE:.4f})")
    print(f"{len(rows)} visible authored text elements across 12 frames\n")
    bands = [(">= 54 (phone-legible)", lambda v: v >= 54),
             ("32 to 53", lambda v: 32 <= v < 54),
             ("26 to 31", lambda v: 26 <= v < 32),
             ("20 to 25", lambda v: 20 <= v < 26),
             ("< 20 (worst)", lambda v: v < 20)]
    for name, f_ in bands:
        g_ = [r for r in rows if f_(r["fs"])]
        print(f"  {name:24s} {len(g_):4d} elements")
    worst = sorted(rows, key=lambda r: r["fs"])[:18]
    print(f"\n  smallest 18, authored px -> phone px:")
    for r in worst:
        print(f"    {r['fs']:5.1f} -> {r['fs']*PHONE:4.1f}  {r['frame'][:18]:18s} "
              f"{str(r['sel'])[:24]:24s} {r['t']!r}")
    json.dump(rows, open(ROOT / "typescale.json", "w"), indent=1)
    print(f"\n  written to typescale.json")
    print("  BLIND CLASS: text inside captured screenshots is not in this population.")


if __name__ == "__main__":
    main()
