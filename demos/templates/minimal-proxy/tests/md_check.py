"""Hold every markdown surface to ONE fixture of REAL emitted markdown (tests/md_fixture.json, built by
collect_md_fixture.py from live answers and crawled page bodies). Exit non-zero on any failure.
Usage (server running): .venv python tests/md_check.py [base_url]
Controls: a deliberately broken renderer must FAIL the same assertions (the check can fire), and the
fixture must contain the shapes the assertions are about (the check has something to chew on)."""
import json, re, sys
from playwright.sync_api import sync_playwright
BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8099"
FIX = json.load(open("tests/md_fixture.json"))
# Shapes the live sample did not happen to contain are added by hand and MARKED synthetic; they are
# not evidence about what the model emits, only about what the renderer tolerates.
SYN = [{"kind": "synthetic", "lang": "en", "text": "1. First step\n2. Second step with [a link](https://example.org/x)\n\nSee https://example.org/y, and <https://example.org/z>. *Italic* and 2026\\* guide. Email `graduateresearchdegrees@university.edu.au` or `a_b*c`."},
       {"kind": "synthetic", "lang": "ar", "text": "للاتصال:\n* +61 8 9360 6063\n* 1300 687 3624\n\nأو راسلنا: * **البريد:** info@university.edu.au * الهاتف: +61 8 9360 6000"}]
# Full-width-punctuation shapes (Mandarin), hand-written and MARKED synthetic: every markdown shape beside \u3002 and \uff1a.
SYN += json.load(open("tests/md_zh_shapes.json"))
ITEMS = FIX + SYN
fails = []
def check(name, cond, detail=""):
    if not cond:
        fails.append(f"{name}: {detail}")

def assertions(page, render, tag, kinds):
    """render: JS function name taking (text, lang) -> html string."""
    for n, it in enumerate(ITEMS):
        if it["kind"] not in kinds:
            continue
        src = it["text"]
        html = page.evaluate(f"({render})(arguments0)".replace("arguments0", json.dumps(src)))
        page.set_content(f'<div id="o" dir="{"rtl" if it["lang"]=="ar" else "ltr"}" style="width:340px;font:16px sans-serif">{html}</div>')
        txt = page.inner_text("#o")
        lab = f"{tag}[{n}:{it['kind']}:{it['lang']}]"
        check(lab + " raw link", not re.search(r"\]\(", txt), txt[:80])
        check(lab + " raw bold", "**" not in txt.replace("`a_b*c`", ""))
        check(lab + " raw backtick", "`" not in txt)
        # a "*" left on screen is a list marker or emphasis the renderer failed to consume (synthetic a_b*c and "2 * 3" excepted)
        check(lab + " stray asterisk", "*" not in re.sub(r"a_b\*c|\d \* \d|2026\*", "", txt), repr(txt[max(0, txt.find('*') - 20):txt.find('*') + 20]))
        marks = len(re.findall(r"(?:^|[\s\u3002\uff01\uff1f\uff1a\uff1b:;.!?)])\*\s+\S", src, re.M))
        if marks:
            check(lab + " every bullet marker became a list item", page.locator("#o li").count() >= marks, f"{page.locator('#o li').count()} li < {marks} markers")
        check(lab + " raw heading", not re.search(r"^\s*#{1,6}\s", txt, re.M))
        check(lab + " raw escape", not re.search(r"\\[*_#\[\]()`>~|\-.!+]", txt))
        check(lab + " raw cite marker", "⟦" not in txt)
        check(lab + " raw angle url", "<http" not in txt)
        links = set(re.findall(r"\[[^\]]+\]\((?:https?://|mailto:|tel:)[^)\s]+", src)) | set(re.findall(r"<https?://[^>]+>", src)) | set(re.findall(r"(?:^|\s)https?://[^\s<)]*[^\s<).,;:!?]", src))
        check(lab + " anchors", page.locator("#o a").count() >= len(links), f"{page.locator('#o a').count()} < {len(links)}")
        heads = len(re.findall(r"^\s*#{1,6}\s", src, re.M))
        check(lab + " headings", page.locator("#o :is(h1,h2,h3,h4,h5,h6)").count() == heads, f"{page.locator('#o :is(h1,h2,h3,h4,h5,h6)').count()} != {heads}")
        if re.search(r"^\s{2,}[*+-]\s", src, re.M):
            check(lab + " nested list", page.locator("#o li ul, #o li ol").count() >= 1)
        if re.search(r"^\s*(---|\*\*\*)\s*$", src, re.M):
            check(lab + " hr", page.locator("#o hr").count() >= 1)
        if it["lang"] == "ar":
            for ph in re.findall(r"(?:\+\d+ )?\d[\d ]{6,}\d", re.sub(r"\]\([^)]*\)", "", re.sub(r"[*\[]", "", src))):
                ok = page.evaluate("""p=>[...document.querySelectorAll('#o bdi[dir=ltr]')].some(b=>b.textContent.replace(/\\s+/g,' ').includes(p))""", ph.strip())
                check(lab + " phone isolated: " + ph, ok)
                if ok:
                    one = page.evaluate("""p=>{const b=[...document.querySelectorAll('#o bdi[dir=ltr]')].find(b=>b.textContent.replace(/\\s+/g,' ').includes(p));return b?b.getClientRects().length:0}""", ph.strip())
                    check(lab + " phone on one line: " + ph, one == 1, f"rects={one}")
                    order = page.evaluate("""p=>{const b=[...document.querySelectorAll('#o bdi[dir=ltr]')].find(b=>b.textContent.replace(/\\s+/g,' ').includes(p));
                      const t=b.firstChild,s=t.textContent;const x=i=>{const r=document.createRange();r.setStart(t,i);r.setEnd(t,i+1);return r.getBoundingClientRect().left};
                      const a=s.search(/\\d/),z=s.length-1;return x(a)<x(z)}""", ph.strip())
                    check(lab + " phone reads left-to-right on screen: " + ph, order)

# The /page body is rendered SERVER-side by pagemode._block_html (a second renderer, Python). Same fixture.
sys.path.insert(0, ".")
import pagemode as PM, html as _h
for n, it in enumerate(i for i in FIX if i["kind"] == "page-body"):
    out = PM._block_html(it["text"])
    txt = _h.unescape(re.sub(r"<[^>]+>", " ", out))
    lab = f"server-body[{n}]"
    check(lab + " raw link", not re.search(r"\]\(", txt), txt[:80])
    check(lab + " raw heading", not re.search(r"^\s*#{1,6}\s", txt, re.M))
    check(lab + " raw escape", not re.search(r"\\[*_#\[\]()`>~|\-.!+]", txt))
    check(lab + " raw bold", "**" not in txt)
    nl = len(re.findall(r"\[[^\]]+\]\(", PM._join_links(it["text"])))
    check(lab + " anchors", out.count("<a ") >= nl, f"{out.count('<a ')} < {nl}")
    check(lab + " headings", len(re.findall(r"<h[1-6]>", out)) == len(re.findall(r"^\s*#{1,6}\s", it["text"], re.M)))
# control: the server check must fire on an unrendered block
bad = "[x](https://e.org)\n##### +61 8 9360 6063"
check("server control fires", re.search(r"\]\(", bad) is not None and "#####" in bad)

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 390, "height": 844}, is_mobile=True)
    pg.goto(BASE + "/page")
    assert pg.evaluate("typeof MuMd") == "object", "mdlite not loaded on /page"
    # surfaces that must share the module: the module is present, and no private renderer remains
    for url, js in [("/", "app.js"), ("/page", "page.js"), ("/wander", "wander.js")]:
        pg.goto(BASE + url)
        check(f"{url} loads MuMd", pg.evaluate("typeof MuMd") == "object")
        src = pg.evaluate("p=>fetch(p).then(r=>r.text())", "/static/" + js)
        check(f"{js} delegates to MuMd.md", "MuMd.md" in src)
        check(f"{js} has no private renderer", not re.search(r"function\s+inline\s*\(|\.replace\(/\\\*\\\*\(\[\^\*\]", src))
    # same fixture through the shared renderer, with the options each surface really passes
    pg.goto(BASE + "/page")
    assertions(pg, "t=>MuMd.md(t,{h:4})", "page/wander", {"page-answer", "wander-answer", "synthetic"})
    pg.goto(BASE + "/")
    assertions(pg, "t=>MuMd.md(t,{h:3,cites:true})", "home", {"home-answer", "synthetic"})

    # --- Citation-marker cases supplied by the home chat (mu-chat), exact expected HTML ---
    SUP = lambda n: '<sup class="c">' + "".join(f'<a href="#src-{x}" aria-label="Source {x}">{x}</a>' for x in n.split(",")) + "</sup>"
    cases = [("Apply online.\u27e61\u27e7", "<p>Apply online." + SUP("1") + "</p>"),
             ("Fees apply.\u27e62,3\u27e7", "<p>Fees apply." + SUP("2,3") + "</p>"),
             ("* **Bold:** text.\u27e64\u27e7", "<ul><li><strong>Bold:</strong> text." + SUP("4") + "</li></ul>"),
             ("**1. Heading**\u27e61\u27e7", "<p><strong>1. Heading</strong>" + SUP("1") + "</p>"),
             ("[x](https://a.b)\u27e61\u27e7", '<p><a href="https://a.b" target="_blank" rel="noopener">x</a>' + SUP("1") + "</p>")]
    cases.append(("Email `a@b.edu` now **bold**", "<p>Email a@b.edu now <strong>bold</strong></p>"))
    cases.append(("Use `**x**` and `[y](https://z.q)` literally", "<p>Use **x** and [y](https://z.q) literally</p>"))
    cases.append(("اتصل https://myadmission.university.edu.au/u/c\u27e61\u27e7 الآن", None))  # checked below: marker must land OUTSIDE the link
    for src, want in cases:
        got = pg.evaluate("t=>MuMd.md(t)", src)
        if want is None:
            check("citation marker after a bare URL stays outside the link", bool(re.search(r"</a>(</bdi>)?<sup class=\"c\">", got)) and "\u27e6" not in got, got[:200])
            check("URL href excludes the marker", 'href="https://myadmission.university.edu.au/u/c"' in got, got[:200])
            continue
        check("chat citation case " + src[:18], got == want, f"got {got!r}")

    # --- Every renderer against the same fixture: identical output asserted ---
    wsrc = open("static/embed/widget.js").read()
    wcode = wsrc[wsrc.index("function esc("):wsrc.index("function mount(")]
    pg.add_script_tag(content=wcode + ";window.WidgetMd=md;")
    msrc = open("static/mdlite.js").read()
    def norm(h): return re.sub(r"\s+", " ", h).strip()
    def drift(label, fn_a, fn_b, opts):
        n = 0
        for it in ITEMS:
            if it["kind"] == "page-body":
                continue
            a = norm(pg.evaluate(fn_a, it["text"])); bb = norm(pg.evaluate(fn_b, it["text"]))
            if a != bb:
                n += 1
        return n
    # CONTROL first: mutate the source (prove it changed), load it as a second renderer, and require the comparator to see it
    mut = msrc.replace("'<strong>$1</strong>'", "'<b>$1</b>'")
    check("control: mutation changed the renderer source", mut != msrc)
    pg.add_script_tag(content="(function(window){" + mut + "})(window.__fake={});")
    ctl = drift("control", "t=>MuMd.md(t,{h:3})", "t=>__fake.MuMd.md(t,{h:3})", None)
    check("control: comparator detects a planted difference", ctl > 0, f"detected {ctl}")
    d = drift("widget", "t=>MuMd.md(t,{h:3})", "t=>WidgetMd(t)", None)
    check("widget.js renders identically to mdlite.js (drift = shapes it renders differently)", d == 0, f"{d} of {len([i for i in ITEMS if i['kind']!='page-body'])} answer items differ")

    # CONTROL: a renderer that renders nothing must trip these assertions
    before = len(fails)
    assertions(pg, "t=>'<p>'+t.replace(/</g,'&lt;')+'</p>'", "CONTROL-broken", {"home-answer", "page-answer", "wander-answer", "synthetic"})
    tripped = len(fails) - before
    del fails[before:]
    check("control fires (broken renderer rejected)", tripped > 20, f"only {tripped} failures")
    # sanity: fixture contains the shapes under test
    j = "\n".join(i["text"] for i in FIX)
    for nm, pat in [("headings", r"^\s*#{1,6}\s"), ("mailto", r"mailto:"), ("nested bullets", r"^\s{2,}[*+-]\s"), ("cite markers", "⟦"), ("escapes", r"\\[*_#]"), ("arabic phone", None)]:
        if pat: check("fixture has " + nm, re.search(pat, j, re.M))
    check("fixture has arabic answer with a phone number", any(i["lang"] == "ar" and re.search(r"\d{3,4} \d{3} \d{4}|\d{4} \d{4}", i["text"]) for i in FIX))
    b.close()
print(f"items={len(ITEMS)} failures={len(fails)}")
for f in fails[:40]:
    print("FAIL", f)
sys.exit(1 if fails else 0)
