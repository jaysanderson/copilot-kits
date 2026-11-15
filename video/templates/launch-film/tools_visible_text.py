#!/usr/bin/env python3
"""Collect every string a VIEWER can read, by seeking each frame's timeline.

The first text sweep read the SOURCE and produced 42 findings, every one of them
a CSS property name ("color", "center") or an em dash inside a code comment -
nothing a viewer sees. Source is the wrong population for a copy rule. This
mounts each frame, steps its paused timeline across the whole take and unions
the rendered innerText at every step, so JS-injected copy that only exists at
t=9s is in scope and code is not.
"""
import json, re, sys, pathlib, urllib.request
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).parent
STEPS = 60
HARNESS = """<!DOCTYPE html><html><head><meta charset="utf-8">
<style>html,body{margin:0;width:1920px;height:1080px;overflow:hidden}</style>
<script>GSAP</script></head><body><div id="mount"></div></body></html>"""


def main():
    g = ROOT / ".beats-gsap.js"
    if not g.exists():
        urllib.request.urlretrieve("https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js", g)
    gsap = g.read_text()
    out = {}
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1920, "height": 1080})
        for f in sorted((ROOT / "compositions/frames").glob("*.html")):
            src = f.read_text()
            m = re.search(r"<template[^>]*>(.*)</template>", src, re.S)
            body = re.sub(r'<script src="[^"]*gsap[^"]*"></script>', "", m.group(1) if m else src)
            cid = re.search(r'data-composition-id="([^"]+)"', body).group(1)
            pg.set_content(HARNESS.replace("GSAP", gsap))
            pg.evaluate("""({body}) => {
                window.__timelines = {};
                document.getElementById('mount').innerHTML = body;
                document.querySelectorAll('#mount script').forEach(s => {
                  const n = document.createElement('script'); n.textContent = s.textContent;
                  document.body.appendChild(n);
                });
            }""", {"body": body})
            texts = pg.evaluate("""({cid, steps}) => {
                const tl = window.__timelines[cid];
                if (!tl) return {error: 'no timeline ' + cid};
                const D = tl.duration(), seen = new Set(), root = document.getElementById('mount');
                for (let i = 0; i <= steps; i++) {
                  tl.seek(D * i / steps, false);
                  root.querySelectorAll('*').forEach(el => {
                    if (el.children.length) return;
                    const t = (el.innerText || el.textContent || '').trim();
                    if (!t) return;
                    const cs = getComputedStyle(el);
                    if (cs.visibility === 'hidden' || cs.display === 'none') return;
                    seen.add(t);
                  });
                }
                return {n: seen.size, texts: [...seen]};
            }""", {"cid": cid, "steps": STEPS})
            out[f.name] = texts
            print(f"  {f.name:28s} {texts.get('n', 0):4d} distinct visible strings")
        b.close()
    json.dump(out, open(ROOT / "visible_text.json", "w"), indent=1, ensure_ascii=False)
    total = sum(v.get("n", 0) for v in out.values())
    print(f"\n{total} visible strings written to visible_text.json")
    if total == 0:
        sys.exit("collected nothing - a sweep over an empty population is not a pass")


if __name__ == "__main__":
    main()
