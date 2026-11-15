"""Branded title cards for pages with no real image. Typographic, University palette, the page's own title and section.
No decorative imagery. Usage: compose_cards.py [--selftest]"""
import os, re, json, sys
from urllib.parse import urlparse
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
CRIMSON, TEAL, INK, PAPER = (0xE1, 0x27, 0x44), (0x00, 0x84, 0x81), (0x21, 0x25, 0x29), (0xF8, 0xF5, 0xF2)
W, H = 960, 540; PAD = 64
F = lambda w, s: ImageFont.truetype(os.path.join(HERE, "fonts", "Poppins-%s.ttf" % w), s)
SECTION = {"study": "Study", "explore": "Explore University", "research": "Research", "news": "News", "alumni": "Alumni",
           "collaborate": "Collaborate", "schools": "Schools", "events": "Events", "about": "About University", "international": "International"}

def clean_title(t):
    t = re.sub(r"\s*\|\s*The university\s*$", "", t or "").strip()
    return t or "The university"

def section(url):
    p = urlparse(url or "")
    if p.netloc.startswith("goto."): return "The university"
    seg = [s for s in p.path.split("/") if s]
    return SECTION.get(seg[0], seg[0].replace("-", " ").title()) if seg else "The university"

def wrap(d, text, font, maxw):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) <= maxw: cur = t
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines

def fit(d, text, maxw, maxh):
    for size in range(60, 27, -2):
        f = F("SemiBold", size); lines = wrap(d, text, f, maxw)
        if all(d.textlength(l, font=f) <= maxw for l in lines) and len(lines) * size * 1.22 <= maxh: return f, size, lines, False
    f = F("SemiBold", 28); lines = wrap(d, text, f, maxw); mx = int(maxh // (28 * 1.22))
    if len(lines) > mx:
        lines = lines[:mx]; lines[-1] = lines[-1].rstrip(" ,.-") + "..."
        while d.textlength(lines[-1], font=f) > maxw: lines[-1] = lines[-1][:-4].rstrip() + "..."
    return f, 28, lines, True

def card(title, url, out):
    im = Image.new("RGB", (W, H), PAPER); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 14], fill=CRIMSON); d.rectangle([0, 14, 260, 22], fill=TEAL)
    d.text((PAD, 66), section(url).upper(), font=F("Medium", 24), fill=TEAL)
    f, size, lines, trunc = fit(d, clean_title(title), W - 2 * PAD, 280)
    y = 120
    for l in lines: d.text((PAD, y), l, font=f, fill=INK); y += int(size * 1.22)
    logo = Image.open(os.path.join(HERE, "assets", "mu-logo.png")).convert("RGBA"); lw = 190
    logo = logo.resize((lw, round(logo.height * lw / logo.width)), Image.LANCZOS)
    im.paste(logo, (PAD, H - PAD - logo.height + 8), logo)
    im.quantize(64, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save(out, optimize=True); return size, len(lines), trunc

if __name__ == "__main__":
    raw = json.load(open(os.path.join(ROOT, "thumbs", "raw.json")))["thumbs"]
    if "--selftest" in sys.argv:
        longest = max(raw.values(), key=lambda r: len(clean_title(r["title"])))
        tests = [longest["title"], " ".join(["Interdisciplinary"] * 14), "Short"]  # last: ordinary; middle: forces truncation path (expect trunc=True)
        for i, t in enumerate(tests):
            print(i, card(t, longest["url"], "/tmp/_cardtest.png") if False else card(t, longest["url"], os.path.join(ROOT, "thumbs", "_selftest_%d.png" % i)), repr(t[:50]))
        sys.exit(0)
    n = 0
    for r in raw.values():
        if r["absent"]:
            out = os.path.join(ROOT, "static", "thumbs", "card-%s.png" % r["rid"])
            s, nl, tr = card(r["title"], r["url"], out); r["card_path"] = "static/thumbs/card-%s.png" % r["rid"]
            r["card_web_path"] = "/static/thumbs/card-%s.png" % r["rid"]; r["card_font_px"] = s; r["card_truncated"] = tr; n += 1
    real = [r for r in raw.values() if not r["absent"]]
    def dh(p):  # 64-bit difference hash: finds the same picture under different filenames and crops
        im = Image.open(os.path.join(ROOT, p)).convert("L").resize((9, 8), Image.LANCZOS); px = list(im.getdata())
        return sum(1 << (i * 8 + j) for i in range(8) for j in range(8) if px[i * 9 + j] > px[i * 9 + j + 1])
    hs = {r["rid"]: dh(r["image_path"]) for r in real}; reps, groups = [], {}
    for r in real:  # greedy clusters, Hamming distance <= 6 of 64
        for rep in reps:
            if bin(hs[r["rid"]] ^ hs[rep]).count("1") <= 6: groups[rep].append(r["rid"]); r["_g"] = rep; break
        else: reps.append(r["rid"]); groups[r["rid"]] = [r["rid"]]; r["_g"] = r["rid"]
    for r in real:
        g = groups[r.pop("_g")]; r["image_key"] = raw[g[0]]["image_url"].split("?")[0].rsplit("/", 1)[-1]; r["image_reuse_count"] = len(g)
        r["image_shared_with"] = [x for x in g if x != r["rid"]]
    meta = {"generated": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(), "denominator": sum(1 for r in raw.values() if not r["rid"].startswith("x-")), "extra_destinations": sum(1 for r in raw.values() if r["rid"].startswith("x-")), "real": len(real),
            "absent": n, "errored": sum(1 for r in raw.values() if r.get("error")),
            "real_by_source": {s: sum(1 for r in real if r["source"] == s) for s in {r["source"] for r in real}},
            "real_bytes": sum(r["bytes"] for r in real),
            "images_reused": sum(1 for r in real if r["image_reuse_count"] > 1), "distinct_images": len(groups), "cards_truncated": sum(1 for r in raw.values() if r.get("card_truncated"))}
    for dst in ("thumbs/manifest.json", "static/thumbs/manifest.json"):  # static/ copy rides the Docker image
        json.dump({"meta": meta, "thumbs": raw}, open(os.path.join(ROOT, dst), "w"), indent=1)
    print(meta)
