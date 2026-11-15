"""Audit the scraped Studycity corpus before ingestion.

Reports: page count, total characters, thin pages (<400 chars, likely a bot-interstitial
capture rather than genuinely thin content), pages that are mostly repeated nav
boilerplate, and duplicates (by normalised text hash). Writes the exclusion decision to
excluded-slugs.json for ingest.py to consume, and prints a summary for the build report.
"""
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "corpus"

THIN_CHARS = 400
# Pages that are structurally utility/navigation rather than visitor-facing content,
# even though they passed the scraper's URL-pattern exclusion (that filter only caught
# obvious utility URL patterns like /privacy-policy/).
BOILERPLATE_TITLE_HINTS = ("404", "not found", "error")


def norm_hash(text):
    # Normalise whitespace/case so near-identical captures (e.g. a page fetched twice
    # with only timestamp differences) still collide.
    norm = " ".join(text.lower().split())
    return hashlib.sha1(norm.encode()).hexdigest()


def main():
    files = sorted(CORPUS.glob("*.json"))
    recs = [json.loads(f.read_text()) for f in files]
    print(f"{len(recs)} pages captured in corpus/")

    total_chars = sum(r["meta"]["chars"] for r in recs)
    print(f"{total_chars:,} total characters")

    thin = [r for r in recs if r["meta"]["chars"] < THIN_CHARS]
    print(f"\n{len(thin)} page(s) under {THIN_CHARS} chars:")
    for r in thin:
        print(f"   {r['meta']['chars']:4d} chars  {r['meta']['slug']}  ({r['meta']['url']})")

    # Duplicate detection by normalised full-text hash
    hashes = Counter()
    by_hash = {}
    for r in recs:
        h = norm_hash(r["text"])
        hashes[h] += 1
        by_hash.setdefault(h, []).append(r["meta"]["slug"])
    dupes = {h: slugs for h, slugs in by_hash.items() if len(slugs) > 1}
    print(f"\n{len(dupes)} duplicate group(s) (identical normalised text):")
    for h, slugs in dupes.items():
        print("   ", slugs)

    # Boilerplate-title check (error/interstitial pages that slipped past the scraper's
    # status-code check because the site returns 200 for a client-rendered 404)
    boiler_title = [r for r in recs if any(h in (r["meta"]["title"] or "").lower()
                                            for h in BOILERPLATE_TITLE_HINTS)]
    print(f"\n{len(boiler_title)} page(s) with an error/not-found title despite a 200:")
    for r in boiler_title:
        print("   ", r["meta"]["slug"], "-", r["meta"]["title"])

    excluded = set()
    for r in thin:
        excluded.add(r["meta"]["slug"])
    for r in boiler_title:
        excluded.add(r["meta"]["slug"])
    for h, slugs in dupes.items():
        # keep the first, exclude the rest
        for s in slugs[1:]:
            excluded.add(s)

    (ROOT / "excluded-slugs.json").write_text(json.dumps(sorted(excluded), indent=1))
    print(f"\n{len(excluded)} page(s) excluded -> {len(recs) - len(excluded)} will be ingested")
    print("excluded list written to excluded-slugs.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
