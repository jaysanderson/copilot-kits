"""Build data/resource_cache.json and data/all_resources.json for the app.

Joins corpus/*.json (the real scraped text + title + url) with ingest-manifest.json
(the resource id each page was ingested as), and assigns each page to a display
category from its URL path - the taxonomy the app's discovery/persona surfaces use.

Run once after ingest.py; re-run any time the corpus or exclusion list changes.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "corpus"
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)

CATEGORY_PATTERNS = [
    (re.compile(r"^study-in-perth/education-providers"), "Education Providers"),
    (re.compile(r"^study-in-perth/study-areas"), "Study Areas"),
    (re.compile(r"^study-in-perth/levels-of-study"), "Levels of Study"),
    (re.compile(r"^study-in-perth/international-student-scholarships"), "Scholarships"),
    (re.compile(r"^study-in-perth/(study-pathways|how-to-apply)"), "Applying & Pathways"),
    (re.compile(r"^study-in-perth/australian-universities"), "Universities"),
    (re.compile(r"^moving-to-perth/student-visas-and-migration"), "Visa & Migration"),
    (re.compile(r"^moving-to-perth/when-you-arrive"), "Arrival"),
    (re.compile(r"^moving-to-perth/before-you-depart"), "Before You Depart"),
    (re.compile(r"^living-in-perth/accommodation"), "Accommodation"),
    (re.compile(r"^living-in-perth/cost-of-living"), "Cost of Living"),
    (re.compile(r"^living-in-perth/safety-and-wellness"), "Safety & Wellness"),
    (re.compile(r"^living-in-perth/australian-culture-and-diversity"), "Culture & Diversity"),
    (re.compile(r"^living-in-perth/weather-and-climate"), "Weather & Climate"),
    (re.compile(r"^living-in-perth/convenience-and-transport"), "Transport"),
    (re.compile(r"^careers/career-support/career-mentoring-program/meet-the-mentees"), "Mentoring Program"),
    (re.compile(r"^careers/career-support"), "Career Support"),
    (re.compile(r"^careers/alumni-community/alumni-stories"), "Alumni Stories"),
    (re.compile(r"^careers/alumni-community"), "Alumni Community"),
    (re.compile(r"^careers/working-in-perth"), "Working Rights"),
    (re.compile(r"^careers/find-a-job"), "Find a Job"),
    (re.compile(r"^careers/for-employers"), "For Employers"),
    (re.compile(r"^about-studycity/international-student-ambassadors"), "Student Ambassadors"),
    (re.compile(r"^about-studycity/meet-the-board"), "Board"),
    (re.compile(r"^about-studycity/meet-the-team"), "Staff"),
    (re.compile(r"^about-studycity/become-a-member"), "Membership"),
    (re.compile(r"^student-support/student-engagement"), "Student Engagement"),
    (re.compile(r"^student-support/student-hub"), "Student Hub"),
    (re.compile(r"^student-support/emergency-contacts-and-assistance"), "Emergency Support"),
    (re.compile(r"^student-support/free-support-services"), "Free Support Services"),
    (re.compile(r"^student-support"), "Student Support"),
    (re.compile(r"^blogs-news"), "News"),
    (re.compile(r"^events"), "Events"),
]


def category_for(url):
    path = url.replace("https://www.studycity.com.au", "").strip("/")
    for pattern, label in CATEGORY_PATTERNS:
        if pattern.match(path):
            return label
    return "General"


PERSON_CATEGORY_PATTERNS = [
    (re.compile(r"^careers/career-support/career-mentoring-program/meet-the-mentees/[^/]+/?$"),
     "Career Mentoring Program Mentee"),
    (re.compile(r"^careers/alumni-community/alumni-stories/[^/]+/?$"), "Alumni Story"),
    (re.compile(r"^about-studycity/international-student-ambassadors/[^/]+/?$"),
     "International Student Ambassador"),
    (re.compile(r"^about-studycity/meet-the-board/[^/]+/?$"), "Studycity Board Member"),
    (re.compile(r"^about-studycity/meet-the-team/[^/]+/?$"), "Studycity Staff"),
]


def display_title(url, raw_title):
    path = url.replace("https://www.studycity.com.au", "").strip("/")
    for pattern, label in PERSON_CATEGORY_PATTERNS:
        if pattern.match(path):
            return f"{label}: {raw_title}"
    return raw_title


def main():
    excluded = set(json.loads((ROOT / "excluded-slugs.json").read_text()))
    ingest_manifest = json.loads((ROOT / "ingest-manifest.json").read_text())
    slug_to_rid = {r["slug"]: r["resource_id"] for r in ingest_manifest if r["ok"]}

    cache = {}
    kept = []
    for f in sorted(CORPUS.glob("*.json")):
        rec = json.loads(f.read_text())
        meta = rec["meta"]
        slug = meta["slug"]
        if slug in excluded:
            continue
        rid = slug_to_rid.get(slug)
        if not rid:
            continue
        title = display_title(meta["url"], meta["title"] or slug)
        category = category_for(meta["url"])
        # Must match ingest.py's body_text prefix EXACTLY - citation paragraph
        # offsets from /ask are computed against the ingested text (title +
        # "Source: <url>" line + blank line + real content), not the raw
        # scraped text alone. Storing this length lets the resource viewer
        # shift a citation's offset back onto the raw (displayed) text.
        index_prefix = f"{title}\n\nSource: {meta['url']}\n\n"
        cache[rid] = {
            "title": title,
            "raw_title": meta["title"],
            "uri": meta["url"],
            "text": rec["text"],
            "category": category,
            "headings": meta.get("headings", []),
            "index_prefix_len": len(index_prefix),
        }
        kept.append({"id": rid, "title": title, "uri": meta["url"], "category": category})

    (DATA / "resource_cache.json").write_text(json.dumps(cache, ensure_ascii=False, indent=1))
    (DATA / "all_resources.json").write_text(json.dumps({"kept": kept}, ensure_ascii=False, indent=1))

    from collections import Counter
    cat_counts = Counter(r["category"] for r in kept)
    print(f"{len(kept)} resources cached")
    for cat, n in cat_counts.most_common():
        print(f"  {n:4d}  {cat}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
