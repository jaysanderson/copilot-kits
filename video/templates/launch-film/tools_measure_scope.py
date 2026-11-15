#!/usr/bin/env python3
"""Measure the frame-10 scope qualifier against the table it qualifies.

The brief's fence: the caveat clears the SAME legibility floor as the figures it
qualifies, measured rather than eyeballed. So this reads both off the rendered
DOM after layout at device scale 1 - where a CSS pixel is a rendered pixel - and
compares them, rather than comparing authored stylesheet values.

It also asserts the block does not overflow its own box, because the text is left
to wrap and a box shorter than its content spills glyphs rather than wrapping,
which no wrap detector reports.
"""
import json, pathlib, re, sys, urllib.request
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).parent
FRAME = ROOT / "compositions/frames/10-measured.html"
H = """<!DOCTYPE html><html><head><meta charset="utf-8">
<style>html,body{margin:0;width:1920px;height:1080px;overflow:hidden;background:#00216B}</style>
<script>GSAP</script></head><body><div id="mount"></div></body></html>"""


def main():
    g = ROOT / ".beats-gsap.js"
    if not g.exists():
        urllib.request.urlretrieve("https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js", g)
    src = FRAME.read_text()
    body = re.sub(r'<script src="[^"]*gsap[^"]*"></script>', "",
                  re.search(r"<template[^>]*>(.*)</template>", src, re.S).group(1))
    shell = ROOT / "_measure_harness.html"
    shell.write_text(H.replace("GSAP", g.read_text()))
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1920, "height": 1080}, device_scale_factor=1)
        failed = []
        pg.on("requestfailed", lambda r: failed.append(r.url.rsplit("/", 1)[-1]))
        pg.goto(shell.as_uri())
        pg.evaluate("""({body}) => {
            window.__timelines = {};
            document.getElementById('mount').innerHTML = body;
            document.querySelectorAll('#mount script').forEach(s => {
              const n = document.createElement('script'); n.textContent = s.textContent;
              document.body.appendChild(n);
            });
        }""", {"body": body})
        pg.wait_for_timeout(1200)
        tl_ok = pg.evaluate("""() => {
            const tl = window.__timelines['10-measured'];
            if (!tl) return false;
            tl.seek(tl.duration() - 0.5, false);   // settled, past every entrance
            return true;
        }""")
        if not tl_ok:
            sys.exit("no timeline registered for 10-measured")
        pg.wait_for_timeout(400)
        d = pg.evaluate("""() => {
            const px = s => parseFloat(s);
            const read = el => {
              const cs = getComputedStyle(el), r = el.getBoundingClientRect();
              return {fs: px(cs.fontSize), lh: cs.lineHeight, color: cs.color,
                      op: px(cs.opacity), w: Math.round(r.width), h: Math.round(r.height),
                      top: Math.round(r.top), left: Math.round(r.left),
                      scrollW: el.scrollWidth, scrollH: el.scrollHeight,
                      clientW: el.clientWidth, clientH: el.clientHeight,
                      text: (el.innerText || '').trim().slice(0, 60)};
            };
            const out = {};
            const sc = document.getElementById('f10-scope');
            out.scope = sc ? read(sc) : null;
            out.table_body = [...document.querySelectorAll('.f10-c-model, .f10-c-time, .f10-f1')]
              .slice(0, 6).map(read);
            out.table_header = [...document.querySelectorAll('.f10-th')].slice(0, 2).map(read);
            out.figures = [...document.querySelectorAll('.f10-num')].slice(0, 2).map(read);
            // anything overlapping the scope block
            const r = sc.getBoundingClientRect();
            out.overlaps = [...document.querySelectorAll('#mount *')].filter(e => {
              if (e === sc || sc.contains(e) || e.contains(sc)) return false;
              const t = (e.innerText || '').trim();
              if (!t || e.children.length) return false;
              const q = e.getBoundingClientRect();
              if (!q.width || !q.height) return false;
              if (getComputedStyle(e).opacity === '0') return false;
              return !(q.right < r.left || q.left > r.right || q.bottom < r.top || q.top > r.bottom);
            }).map(e => ({id: e.id || e.className, text: (e.innerText || '').trim().slice(0, 30)}));
            return out;
        }""")
        b.close()
    shell.unlink(missing_ok=True)
    if failed:
        print(f"*** assets failed to load: {sorted(set(failed))[:6]} - measuring the wrong frame")
        sys.exit(2)

    sc = d["scope"]
    if not sc:
        sys.exit("#f10-scope not found in the rendered frame")
    body_min = min(x["fs"] for x in d["table_body"])
    hdr_min = min(x["fs"] for x in d["table_header"])
    fig_min = min(x["fs"] for x in d["figures"])
    print("RENDERED, device scale 1, timeline settled:")
    print(f"  scope qualifier   {sc['fs']:.1f}px  colour {sc['color']}  opacity {sc['op']:.2f}")
    print(f"                    box {sc['w']}x{sc['h']} at ({sc['left']},{sc['top']})")
    print(f"                    {sc['text']!r}...")
    print(f"  table body cells  {body_min:.1f}px  (model / time / F1, {len(d['table_body'])} read)")
    print(f"  table figures     {fig_min:.1f}px  (the percentages)")
    print(f"  table headers     {hdr_min:.1f}px  (column labels - NOT the floor used)")

    checks = []
    checks.append(("caveat >= table body type", sc["fs"] >= body_min,
                   f"{sc['fs']:.1f} vs {body_min:.1f}"))
    checks.append(("caveat visible at settle", sc["op"] > 0.99, f"opacity {sc['op']:.2f}"))
    checks.append(("no horizontal overflow", sc["scrollW"] <= sc["clientW"] + 1,
                   f"scrollW {sc['scrollW']} vs clientW {sc['clientW']}"))
    checks.append(("no vertical overflow", sc["scrollH"] <= sc["clientH"] + 1,
                   f"scrollH {sc['scrollH']} vs clientH {sc['clientH']}"))
    checks.append(("inside the frame", sc["top"] >= 0 and sc["top"] + sc["h"] <= 1080,
                   f"{sc['top']}..{sc['top']+sc['h']}"))
    checks.append(("overlaps nothing with text", not d["overlaps"], str(d["overlaps"])))
    print()
    ok = True
    for name, good, detail in checks:
        print(f"  [{'PASS' if good else 'FAIL'}] {name:28s} {detail}")
        ok &= good

    # control: the measure must be able to FAIL on the asymmetry it exists to catch
    print(f"\n  CONTROL: at the header size ({hdr_min:.1f}px) the caveat would read "
          f"{'FAIL' if hdr_min < body_min else 'PASS'} against the body floor "
          f"({body_min:.1f}px) -> "
          f"{'the check can detect fine print' if hdr_min < body_min else 'CHECK IS DECORATION'}")
    ok &= hdr_min < body_min
    print("\nSCOPE QUALIFIER", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
