"""Harvest real page thumbnails for every resource in the KB. Output: thumbs/manifest.json, static/thumbs/."""
import html as html_mod, os, re, io, json, sys, hashlib, concurrent.futures as cf
import requests
from PIL import Image
from urllib.parse import urljoin, urlparse
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env = {}
for l in open(os.path.join(ROOT, ".env")):
    if "=" in l and not l.startswith("#"):
        k, v = l.split("=", 1); env[k.strip()] = v.split(" #")[0].strip()
KB = env["KB_URL"].rstrip("/"); TOK = env["KB_TOKEN"]
H = {"X-NUCLIA-SERVICEACCOUNT": "Bearer " + TOK.replace("Bearer ", ""), "X-Synchronous": "true"}
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124 Safari/537.36"}
OUT = os.path.join(ROOT, "static", "thumbs"); os.makedirs(OUT, exist_ok=True)
MAXW = 640
EXTRA = ['/study/open-day', '/study/international-students/before-moving-to-perth/entry-requirements/english-proficiency-tests', '/contact-us']

def enumerate_pages():
    pages, page = [], 0
    while True:
        r = requests.get(KB + "/resources", headers=H, params={"page": page, "size": 100}, timeout=60)
        r.raise_for_status(); j = r.json()
        for x in j.get("resources", []):
            pages.append({"rid": x["id"], "title": x.get("title"), "url": None})
        if j.get("pagination", {}).get("last", True): break
        page += 1
    def og(p):
        for _ in range(3):
            try:
                d = requests.get(KB + "/resource/" + p["rid"], headers=H, params={"show": ["basic", "origin"]}, timeout=60).json()
                p["url"] = (d.get("origin") or {}).get("url") or None; return
            except Exception: pass
    with cf.ThreadPoolExecutor(8) as ex: list(ex.map(og, pages))
    return pages

META = re.compile(r'<meta\b[^>]*>', re.I)
def attr(tag, name):
    m = re.search(name + r'\s*=\s*(?:"([^"]*)"|\'([^\']*)\')', tag, re.I)
    return (m.group(1) or m.group(2)) if m else None
BAD = re.compile(r'logo|sprite|spacer|pixel|tracking|icon|favicon|cookie|placeholder|blank|\.svg|\.gif', re.I)
def candidates(html, base):
    og, tw = [], []
    for t in META.findall(html):
        k = (attr(t, "property") or attr(t, "name") or "").lower(); c = attr(t, "content")
        if not c: continue
        if k in ("og:image", "og:image:url", "og:image:secure_url"): og.append(c)
        elif k in ("twitter:image", "twitter:image:src"): tw.append(c)
    out = [("og:image", urljoin(base, html_mod.unescape(u))) for u in og] + [("twitter:image", urljoin(base, html_mod.unescape(u))) for u in tw]
    # hero: the page's own lead image. Strict: University pages are card grids, so card, blockquote portrait, tile,
    # icon and furniture images are NOT the page's image (a card shows ANOTHER page's picture).
    body = html.split("title banner end", 1)[-1].split("<footer", 1)[0]
    for m in re.finditer(r'<img\b[^>]*>', body, re.I):
        t = m.group(0); s = attr(t, "src") or attr(t, "data-src"); cls = attr(t, "class") or ""
        if not s or s.startswith("data:") or BAD.search(s): continue
        if re.search(r'card|blockquote|tile|icon|nav-|logo', cls): continue
        if re.fullmatch(r'\s*ratio ratio-16x9\s*', cls) or "d-block" in cls or "/banner/" in s:
            out.append(("hero", urljoin(base, html_mod.unescape(s))))
        if sum(1 for o in out if o[0] == "hero") >= 2: break
    return out

def norm(u):
    p = urlparse(u); return (p.netloc.lower().replace("www.", "") + p.path.rstrip("/")).lower()

def cards(html, base):
    """(target page url, image url) pairs from card images: University's own chosen picture for the linked page.
    Only when exactly one distinct internal link sits beside the image; ambiguous cards are skipped."""
    out = []
    body = html.split("title banner end", 1)[-1].split("<footer", 1)[0]
    for m in re.finditer(r'<img\b[^>]*>', body, re.I):
        t = m.group(0); cls = attr(t, "class") or ""; src = attr(t, "src")
        if not src or "card" not in cls or BAD.search(src): continue
        win = body[max(0, m.start() - 1200): m.end() + 1500]
        hs = {urljoin(base, html_mod.unescape(h)) for h in re.findall(r'<a\b[^>]*?href="([^"#]+)"', win)}
        hs = {h for h in hs if h.startswith("http") and norm(h) != norm(base) and "university.edu.au" in h}
        if len(hs) == 1: out.append((hs.pop(), urljoin(base, html_mod.unescape(src))))
    return out

# Eye-verified exclusions (9 Oct 2026): bush-court-banner shows a legible Liverpool FC / Standard Chartered shirt
# (third-party brand); the permit image is a scanned government document, not marketing imagery.
EXCLUDE = re.compile(r"bush-court-banner|bush-courta|permit", re.I)

def fetch_img(u):
    if EXCLUDE.search(u): return None
    r = requests.get(u, headers=UA, timeout=25)
    if r.status_code != 200: return None
    if len(r.content) < 4000: return None
    im = Image.open(io.BytesIO(r.content)); im.load()
    if im.width < 300 or im.height < 150: return None
    return im

def process(p):
    rec = {"rid": p["rid"], "url": p["url"], "title": p["title"], "absent": True, "image_path": None, "web_path": None,
           "source": None, "width": None, "height": None, "bytes": None, "card_path": None, "card_web_path": None, "error": None}
    if not p["url"]: rec["error"] = "no origin.url"; return rec
    try:
        r = requests.get(p["url"], headers=UA, timeout=25); r.raise_for_status()
        html = r.text; base = r.url
    except Exception as e:
        rec["error"] = "page fetch: %s" % type(e).__name__; return rec
    rec["_cards"] = cards(html, base)
    for src, u in candidates(html, base):
        try: im = fetch_img(u)
        except Exception: im = None
        if im is None: continue
        im = im.convert("RGB")
        if im.width > MAXW: im = im.resize((MAXW, round(im.height * MAXW / im.width)), Image.LANCZOS)
        path = os.path.join(OUT, p["rid"] + ".jpg"); im.save(path, "JPEG", quality=78, optimize=True, progressive=True)
        rec.update(absent=False, image_path="static/thumbs/%s.jpg" % p["rid"], web_path="/static/thumbs/%s.jpg" % p["rid"],
                   source=src, width=im.width, height=im.height, bytes=os.path.getsize(path), image_url=u)
        break
    return rec

if __name__ == "__main__":
    pages = enumerate_pages(); print("enumerated", len(pages), "with url", sum(1 for p in pages if p["url"]))
    # Chat destination pages that are not in the KB: harvested the same way, keyed "x-<slug>" (not KB resources).
    for d in EXTRA:
        pages.append({"rid": "x-" + re.sub(r"\W+", "-", d.strip("/")), "title": None, "url": "https://www.university.edu.au" + d, "extra": True})
    json.dump(pages, open(os.path.join(ROOT, "thumbs", "pages.json"), "w"), indent=1)
    with cf.ThreadPoolExecutor(8) as ex: recs = list(ex.map(process, pages))
    cmap = {}
    for r in recs:
        for tgt, img in r.pop("_cards", []): cmap.setdefault(norm(tgt), []).append(img)
    for r in recs:
        if not r["absent"] or r["error"]: continue
        imgs = cmap.get(norm(r["url"]))
        if not imgs: continue
        u = max(set(imgs), key=imgs.count)
        try: im = fetch_img(u)
        except Exception: im = None
        if im is None: continue
        im = im.convert("RGB")
        if im.width > MAXW: im = im.resize((MAXW, round(im.height * MAXW / im.width)), Image.LANCZOS)
        path = os.path.join(OUT, r["rid"] + ".jpg"); im.save(path, "JPEG", quality=78, optimize=True, progressive=True)
        r.update(absent=False, image_path="static/thumbs/%s.jpg" % r["rid"], web_path="/static/thumbs/%s.jpg" % r["rid"],
                 source="linked-card", width=im.width, height=im.height, bytes=os.path.getsize(path), image_url=u)
    # Hand-picked destination images (eye-verified 9 Oct 2026): pages with no image of their own whose own card
    # for a child route depicts the destination honestly. Labelled "hand-picked-card"; never overrides a real source.
    ovp = os.path.join(ROOT, "seed", "dest_overrides.json")
    for path, o in json.load(open(ovp)).items():
        for r in recs:
            if not r["absent"] or norm(r["url"] or "") != norm("https://www.university.edu.au" + path): continue
            im = fetch_img(o["image_url"]); assert im is not None, path
            im = im.convert("RGB")
            if im.width > MAXW: im = im.resize((MAXW, round(im.height * MAXW / im.width)), Image.LANCZOS)
            pth = os.path.join(OUT, r["rid"] + ".jpg"); im.save(pth, "JPEG", quality=78, optimize=True, progressive=True)
            r.update(absent=False, image_path="static/thumbs/%s.jpg" % r["rid"], web_path="/static/thumbs/%s.jpg" % r["rid"],
                     source="hand-picked-card", width=im.width, height=im.height, bytes=os.path.getsize(pth), image_url=o["image_url"], pick_note=o["why"])
    json.dump({"meta": {"denominator": len(pages)}, "thumbs": {r["rid"]: r for r in recs}}, open(os.path.join(ROOT, "thumbs", "raw.json"), "w"), indent=1)
    print("real", sum(1 for r in recs if not r["absent"]), "absent", sum(1 for r in recs if r["absent"] and not r["error"]), "errored", sum(1 for r in recs if r["error"]))
