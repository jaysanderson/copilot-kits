#!/usr/bin/env python3
"""Screenshot one frame composition at a given point on its own timeline.

Lets a fix be judged in seconds instead of waiting out a 40-minute render.
Mounts the composition, seeks the paused timeline, captures 1920x1080.
Usage: tools_shot.py <frame.html> <t> <out.png>
"""
import re, sys, pathlib, urllib.request
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).parent
H = """<!DOCTYPE html><html><head><meta charset="utf-8">
<style>html,body{margin:0;width:1920px;height:1080px;overflow:hidden;background:#00216B}</style>
<script>GSAP</script></head><body><div id="mount"></div></body></html>"""


def main(frame, t, out):
    g = ROOT / ".beats-gsap.js"
    if not g.exists():
        urllib.request.urlretrieve("https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js", g)
    src = pathlib.Path(frame).read_text()
    m = re.search(r"<template[^>]*>(.*)</template>", src, re.S)
    body = re.sub(r'<script src="[^"]*gsap[^"]*"></script>', "", m.group(1) if m else src)
    cid = re.search(r'data-composition-id="([^"]+)"', body).group(1)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1920, "height": 1080}, device_scale_factor=1)
        shell = ROOT / "_shot_harness.html"
        shell.write_text(H.replace("GSAP", g.read_text()))
        missing = []
        pg.on("requestfailed", lambda r: missing.append(r.url.rsplit("/", 1)[-1]))
        pg.goto(shell.as_uri())
        pg.evaluate("""({body, base}) => {
            window.__timelines = {};
            const el = document.createElement('base'); el.href = base;
            document.head.appendChild(el);
            document.getElementById('mount').innerHTML = body;
            document.querySelectorAll('#mount script').forEach(s => {
              const n = document.createElement('script'); n.textContent = s.textContent;
              document.body.appendChild(n);
            });
        }""", {"body": body, "base": (ROOT).as_uri() + "/"})
        pg.wait_for_timeout(1200)
        ok = pg.evaluate("""({cid, t}) => {
            const tl = window.__timelines[cid];
            if (!tl) return false;
            tl.seek(t, false); return true;
        }""", {"cid": cid, "t": float(t)})
        if not ok:
            sys.exit(f"no timeline registered for {cid}")
        pg.wait_for_timeout(500)
        pg.screenshot(path=out)
        b.close()
    shell.unlink(missing_ok=True)
    if missing:
        print(f"  *** {len(missing)} asset(s) failed to load: {sorted(set(missing))[:6]}")
        print("      a frame missing its images is not the frame that ships")
        sys.exit(2)
    print(f"{out}  ({frame} at t={t}s)")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
