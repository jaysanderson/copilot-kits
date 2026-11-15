#!/usr/bin/env python3
"""Rendered-extent sweep: what did raising the type break?

Raising 45 type rules is moving geometry, and the defects it creates are not in
the rules that moved - they are in the containers around them. This reads the
RENDERED box of every text element after layout (an authored rectangle cannot
see wrapped or overflowing text) and reports three things: text overflowing its
own box, text outside the 1920x1080 frame, and text overlapping other text.
"""
import pathlib, re, sys, urllib.request
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).parent
H = """<!DOCTYPE html><html><head><meta charset="utf-8">
<style>html,body{margin:0;width:1920px;height:1080px;overflow:hidden;background:#00216B}</style>
<script>GSAP</script></head><body><div id="mount"></div></body></html>"""
JS = """() => {
  const vis = e => { const c = getComputedStyle(e);
    return c.visibility !== 'hidden' && c.display !== 'none' && parseFloat(c.opacity) > 0.05; };
  const txt = [...document.querySelectorAll('#mount *')]
    .filter(e => !e.children.length && (e.innerText || '').trim() && vis(e));
  const over = [], out = [], hit = [];
  for (const e of txt) {
    const r = e.getBoundingClientRect();
    // A box shorter than its own line spills glyphs, but that only HARMS where
    // something clips them. Every one of the 82 first-run hits was a 3px line-box
    // spill on an element with overflow:visible all the way up - the condition
    // without the consequence. Test the consequence.
    let clipper = null;
    for (let a = e; a && a.id !== 'mount'; a = a.parentElement) {
      const o = getComputedStyle(a);
      if (o.overflow !== 'visible' || o.overflowX !== 'visible' || o.overflowY !== 'visible') {
        clipper = a; break;
      }
    }
    // Two cases, and the first draft handled only one - so a planted clipped overflow
    // did not fire and the clean result was decoration. If the element clips ITSELF its
    // rect IS the clipped box, so the escape can only be seen in scroll vs client size;
    // if an ANCESTOR clips, compare the rects.
    if (clipper) {
      const spills = e.scrollWidth > e.clientWidth + 2 || e.scrollHeight > e.clientHeight + 2;
      let escapes = false;
      if (clipper === e) {
        escapes = spills;
      } else if (spills) {
        const cr = clipper.getBoundingClientRect();
        escapes = r.right > cr.right + 2 || r.bottom > cr.bottom + 2 || r.left < cr.left - 2;
      }
      if (escapes)
        over.push({id: e.id || e.className, sw: e.scrollWidth, cw: e.clientWidth,
                   sh: e.scrollHeight, ch: e.clientHeight,
                   clip: clipper === e ? 'self' : (clipper.id || clipper.className),
                   t: (e.innerText||'').trim().slice(0,26)});
    }
    if (r.width && (r.left < -2 || r.top < -2 || r.right > 1922 || r.bottom > 1082))
      out.push({id: e.id || e.className, box: [Math.round(r.left), Math.round(r.top),
                Math.round(r.right), Math.round(r.bottom)], t: (e.innerText||'').trim().slice(0,26)});
  }
  for (let i = 0; i < txt.length; i++) for (let j = i + 1; j < txt.length; j++) {
    const a = txt[i].getBoundingClientRect(), b = txt[j].getBoundingClientRect();
    if (!a.width || !b.width) continue;
    if (txt[i].contains(txt[j]) || txt[j].contains(txt[i])) continue;
    const ox = Math.min(a.right,b.right) - Math.max(a.left,b.left);
    const oy = Math.min(a.bottom,b.bottom) - Math.max(a.top,b.top);
    if (ox > 3 && oy > 3)
      hit.push({a: txt[i].id || txt[i].className, b: txt[j].id || txt[j].className,
                ox: Math.round(ox), oy: Math.round(oy),
                ta: (txt[i].innerText||'').trim().slice(0,18), tb: (txt[j].innerText||'').trim().slice(0,18)});
  }
  return {n: txt.length, over, out, hit};
}"""


def main():
    g = ROOT / ".beats-gsap.js"
    if not g.exists():
        urllib.request.urlretrieve("https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js", g)
    shell = ROOT / "_of_harness.html"; shell.write_text(H.replace("GSAP", g.read_text()))
    bad = 0
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1920, "height": 1080}, device_scale_factor=1)
        for f in sorted((ROOT / "compositions/frames").glob("*.html")):
            src = f.read_text()
            body = re.sub(r'<script src="[^"]*gsap[^"]*"></script>', "",
                          re.search(r"<template[^>]*>(.*)</template>", src, re.S).group(1))
            cid = re.search(r'data-composition-id="([^"]+)"', body).group(1)
            # sample several points, because a collision can exist only mid-build
            for frac in (0.25, 0.6, 0.98):
                pg.goto(shell.as_uri())
                pg.evaluate("""({body}) => { window.__timelines = {};
                    document.getElementById('mount').innerHTML = body;
                    document.querySelectorAll('#mount script').forEach(s => {
                      const n = document.createElement('script'); n.textContent = s.textContent;
                      document.body.appendChild(n); }); }""", {"body": body})
                pg.wait_for_timeout(800 if frac == 0.25 else 250)
                pg.evaluate("""({cid, frac}) => { const t = window.__timelines[cid];
                                if (t) t.seek(t.duration() * frac, false); }""",
                            {"cid": cid, "frac": frac})
                pg.wait_for_timeout(200)
                d = pg.evaluate(JS)
                issues = len(d["over"]) + len(d["out"]) + len(d["hit"])
                if issues:
                    bad += issues
                    print(f"{f.stem}  @{frac:.2f}  {d['n']} text els, {issues} issue(s)")
                    for o in d["over"][:4]:
                        print(f"    OVERFLOW {o['id']}  {o['sw']}x{o['sh']} in {o['cw']}x{o['ch']}  {o['t']!r}")
                    for o in d["out"][:4]:
                        print(f"    OFF-FRAME {o['id']}  {o['box']}  {o['t']!r}")
                    for o in d["hit"][:4]:
                        print(f"    OVERLAP  {o['a']} x {o['b']}  {o['ox']}x{o['oy']}px  "
                              f"{o['ta']!r} / {o['tb']!r}")
        b.close()
    shell.unlink(missing_ok=True)
    print(f"\n{bad} rendered-extent issue(s) across 12 frames at 3 sample points each")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
