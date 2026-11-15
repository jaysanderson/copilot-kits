"""Scrape Studycity's own published pages into a local corpus, from their real sitemap.

Their site sits behind Cloudflare and refuses a plain HTTP fetch (403 on the ferries-style
pages, a bot-verification interstitial on others), so this drives a real browser. That is
the documented path for this situation - persist with a real browser rather than fall back
to something approximate.

WHAT IS EXCLUDED, and why it matters to say so: utility pages (privacy, terms, sitemap,
search, the member portal) carry no visitor value and would pollute retrieval with
boilerplate - the same discipline as the Holidayisle build, where 189 ingested pages became
166 after hygiene. Everything else, including the ambassador and board profiles, is real
Studycity content a student might genuinely be answered from.

Output: one JSON per page in corpus/, plus a manifest. Nothing is invented here - this is
their published text, captured, with the URL kept so every future answer can cite back to
the real page.
"""
import json
import re
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "corpus"
SITEMAP = Path("/tmp/sp_sitemap.txt")

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/140.0 Safari/537.36")

EXCLUDE = re.compile(
    r"/(privacy-policy|terms|sitemap|search|portal|contact)(/|$)", re.I)

# Nav and footer text repeats on all 243 pages. Left in, it would dominate retrieval and
# make every page look similar - the boilerplate lesson from the graph-extraction work.
BOILER_START = re.compile(r"^(Skip to main content|Explore the Island Map)", re.I)


def slug(url):
    s = url.replace("https://www.studycity.com.au", "").strip("/")
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "home"


def main():
    if not SITEMAP.exists():
        raise SystemExit(f"no sitemap at {SITEMAP} - run the sitemap read first")
    urls = [u.strip() for u in SITEMAP.read_text().splitlines() if u.strip()]
    urls = [u for u in urls if not EXCLUDE.search(u)]
    CORPUS.mkdir(exist_ok=True)
    print(f"{len(urls)} pages to capture (utility pages excluded)")

    manifest, failures = [], []
    with sync_playwright() as p:
        br = p.chromium.launch()
        ctx = br.new_context(user_agent=UA, locale="en-AU",
                             viewport={"width": 1440, "height": 1100})
        pg = ctx.new_page()
        for i, url in enumerate(urls, 1):
            out = CORPUS / f"{slug(url)}.json"
            if out.exists():
                manifest.append(json.loads(out.read_text())["meta"])
                continue
            try:
                r = pg.goto(url, wait_until="domcontentloaded", timeout=45000)
                pg.wait_for_timeout(1200)
                if not r or r.status >= 400:
                    failures.append((url, r.status if r else "no response"))
                    continue
                title = (pg.title() or "").replace(" | Studycity", "").strip()
                # The main content region if the site marks one, else body minus chrome.
                body = None
                for sel in ("main", "#main-content", "[role=main]", "article"):
                    if pg.locator(sel).count():
                        body = pg.inner_text(sel)
                        break
                if not body:
                    body = pg.inner_text("body")
                lines = [ln.strip() for ln in body.split("\n")]
                lines = [ln for ln in lines if ln and not BOILER_START.match(ln)]
                text = "\n".join(lines)
                heads = pg.eval_on_selector_all(
                    "h1,h2,h3", "els=>els.map(e=>e.innerText.trim()).filter(Boolean)")
                rec = {
                    "meta": {"url": url, "slug": slug(url), "title": title,
                             "chars": len(text), "headings": heads[:20]},
                    "text": text,
                }
                out.write_text(json.dumps(rec, ensure_ascii=False, indent=1))
                manifest.append(rec["meta"])
                if i % 20 == 0:
                    print(f"  {i}/{len(urls)} ... {title[:50]}")
            except Exception as e:
                failures.append((url, f"{type(e).__name__}: {str(e)[:70]}"))
            time.sleep(0.25)
        br.close()

    (ROOT / "corpus-manifest.json").write_text(
        json.dumps({"pages": manifest, "failures": failures}, indent=1))
    total = sum(m["chars"] for m in manifest)
    print(f"\ncaptured {len(manifest)} pages, {total:,} characters")
    if failures:
        print(f"{len(failures)} failed:")
        for u, why in failures[:12]:
            print("   ", why, u)
    thin = [m for m in manifest if m["chars"] < 400]
    print(f"{len(thin)} page(s) under 400 chars - check these are genuinely thin, "
          f"not a capture that landed on an interstitial")
    return 0


if __name__ == "__main__":
    sys.exit(main())
