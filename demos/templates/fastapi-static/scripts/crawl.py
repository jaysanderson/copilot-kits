"""Crawl clinic.com published pages + news posts into a local corpus.

Published content only. No inference, no invention - each document carries the
page's own visible text, its real title and its real URL.
"""
import json, re, html, time, sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import requests

OUT = Path(__file__).resolve().parent.parent / "corpus"
OUT.mkdir(exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36"}

SKIP = re.compile(r"(privacy-policy|right-to-receive-documents|thank-you|-old/|/remplir-2/|cookie|sitemap)", re.I)

# Boilerplate chrome present on every page - stripped so it never grounds an answer.
BOILER = [
    "Skip to content", "We detected you're visiting from",
    "You've already unlocked access", "Re-register", "Continue with existing access",
]


def sitemap_urls():
    urls = []
    for sm in ["page-sitemap", "post-sitemap1", "post-sitemap2"]:
        r = requests.get(f"https://clinic.com/{sm}.xml", headers=UA, timeout=30)
        for m in re.finditer(r"<loc>([^<]+)</loc>", r.text):
            u = m.group(1)
            if not SKIP.search(u):
                urls.append(u)
    # de-dup, keep order
    seen, out = set(), []
    for u in urls:
        if u not in seen:
            seen.add(u); out.append(u)
    return out


def clean(t):
    t = re.sub(r"<script.*?</script>", " ", t, flags=re.S | re.I)
    t = re.sub(r"<style.*?</style>", " ", t, flags=re.S | re.I)
    t = re.sub(r"<noscript.*?</noscript>", " ", t, flags=re.S | re.I)
    return t


def extract(url):
    try:
        r = requests.get(url, headers=UA, timeout=30)
        if r.status_code != 200:
            return None
        h = r.text
    except Exception:
        return None

    title = ""
    m = re.search(r"<title[^>]*>(.*?)</title>", h, flags=re.S | re.I)
    if m:
        title = html.unescape(re.sub(r"\s+", " ", m.group(1))).strip()
    title = re.sub(r"\s*[-|]\s*Clinic\s*$", "", title).strip() or url

    # main content region if present, else body
    body = h
    mm = re.search(r"<main\b.*?</main>", h, flags=re.S | re.I)
    if mm:
        body = mm.group(0)
    body = clean(body)

    # keep block structure as newlines
    body = re.sub(r"<(br|/p|/h[1-6]|/li|/div|/tr|/td)[^>]*>", "\n", body, flags=re.I)
    body = re.sub(r"<[^>]+>", " ", body)
    body = html.unescape(body)
    lines = []
    for ln in body.split("\n"):
        ln = re.sub(r"[ \t\xa0]+", " ", ln).strip()
        if not ln or len(ln) < 3:
            continue
        if any(b.lower() in ln.lower() for b in BOILER):
            continue
        lines.append(ln)

    # drop repeated nav lines (appear many times identically)
    out, seen = [], set()
    for ln in lines:
        k = ln.lower()
        if k in seen and len(ln) < 60:
            continue
        seen.add(k)
        out.append(ln)

    text = "\n".join(out)
    # trim the global footer tail
    for marker in ["Clinic Headquarters", "ABN: 57 118 897 135", "Sign up to our newsletter"]:
        i = text.find(marker)
        if i > 400:
            text = text[:i]
    text = text.strip()
    if len(text) < 200:
        return None
    return {"url": url, "title": title, "text": text}


def main():
    urls = sitemap_urls()
    print(f"{len(urls)} candidate urls", flush=True)
    docs = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        for i, d in enumerate(ex.map(extract, urls)):
            if d:
                docs.append(d)
            if i % 25 == 0:
                print(f"  {i}/{len(urls)} -> {len(docs)} kept", flush=True)
    (OUT / "docs.json").write_text(json.dumps(docs, indent=1))
    print(f"kept {len(docs)} documents -> {OUT/'docs.json'}")
    tot = sum(len(d["text"]) for d in docs)
    print(f"total chars {tot:,}")


if __name__ == "__main__":
    main()
