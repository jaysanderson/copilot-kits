#!/usr/bin/env python3
"""Read the REGISTERED timeline of a frame composition and report every beat.

Why this exists: a retime that edits source literals is verified by comparing
what the timeline REGISTERS before and after, not by reading the diff. An
un-wrapped literal keeps its old start time, which this sees and a diff does
not. Population is GSAP's own children, so anything the frame schedules is in
scope by construction.

Usage:  python3 tools_beats.py <frame.html> [...]   -> JSON per frame on stdout
"""
import json, sys, pathlib, re
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).parent

HARNESS = """<!DOCTYPE html><html><head><meta charset="utf-8">
<style>html,body{margin:0;width:1920px;height:1080px;overflow:hidden}</style>
<script>GSAP_SRC</script></head><body><div id="mount"></div></body></html>"""


def read(frame_path, pw_page):
    src = pathlib.Path(frame_path).read_text()
    m = re.search(r"<template[^>]*>(.*)</template>", src, re.S)
    body = m.group(1) if m else src
    # strip the composition's own gsap script tag - the harness already has it
    body = re.sub(r'<script src="[^"]*gsap[^"]*"></script>', "", body)
    cid = re.search(r'data-composition-id="([^"]+)"', body)
    cid = cid.group(1) if cid else pathlib.Path(frame_path).stem
    pw_page.evaluate(
        """({body}) => {
             window.__timelines = {};
             document.getElementById('mount').innerHTML = body;
             document.querySelectorAll('#mount script').forEach(s => {
               const n = document.createElement('script');
               n.textContent = s.textContent;
               document.body.appendChild(n);
             });
           }""",
        {"body": body},
    )
    data = pw_page.evaluate(
        """(cid) => {
             const tl = window.__timelines[cid];
             if (!tl) return {error: 'no timeline registered for ' + cid,
                              have: Object.keys(window.__timelines)};
             const kids = tl.getChildren(false, true, true).map((c, i) => ({
               i, start: Math.round(c.startTime()*1000)/1000,
               dur: Math.round(c.duration()*1000)/1000,
               targets: (c.targets ? c.targets() : []).map(t => t.id || t.tagName || '?').slice(0,3),
               vars: Object.keys(c.vars || {}).filter(k => !['duration','ease','onUpdate','onComplete'].includes(k)).slice(0,6)
             }));
             return {cid, total: Math.round(tl.duration()*1000)/1000, n: kids.length, beats: kids};
           }""",
        cid,
    )
    return data


def main():
    gsap = (ROOT / ".beats-gsap.js")
    if not gsap.exists():
        import urllib.request
        urllib.request.urlretrieve("https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js", gsap)
    out = {}
    with sync_playwright() as p:
        gsap_js = gsap.read_text()
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1920, "height": 1080})
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.set_content(HARNESS.replace("GSAP_SRC", gsap_js))
        for f in sys.argv[1:]:
            del errs[:]
            try:
                d = read(f, pg)
            except Exception as e:
                d = {"error": repr(e)}
            if errs:
                d["page_errors"] = errs[:4]
            out[pathlib.Path(f).name] = d
            pg.set_content(HARNESS.replace("GSAP_SRC", gsap_js))
        b.close()
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
