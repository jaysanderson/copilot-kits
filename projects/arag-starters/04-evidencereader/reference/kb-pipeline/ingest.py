"""Ingest the audited Studycity corpus into the provisioned KB.

CORRECTED (found live in build QA, 29 Sep 2026): the arag-kb skill's documented
single-call `POST /kb/{id}/upload` is for BINARY FILE uploads, not a structured
text-body resource create. Sending a JSON resource-creation payload to /upload
on this deployment does NOT 4xx - it silently accepts it as a generic file
upload of content-type application/json, OCRs/extracts the raw JSON text
itself (so the resource's real title comes back as a random hash, and the
"extracted text" is polluted with literal JSON structure like
"title : X\n\ntexts body body : Y" wrapping the real content). Retrieval still
worked in testing (the real content is present somewhere inside that garbled
extraction), but the resource's own title metadata was wrong - which would
show as broken/garbled titles in the real ARAG admin console - and the exact
indexed character offsets no longer matched what the app's citation-highlight
logic assumed.

The correct call for a structured text-body resource, verified live: a single
`POST /kb/{id}/resources` with `title` + `texts.body.body` + `origin.url` -
confirmed to set the resource's real title cleanly and store the extracted
text as EXACTLY the body string sent, no wrapping. Use this, not /upload.

The page title is written into the body text as well as the resource title
field - a name living only in a title never grounds (CLAUDE.md "Known live
platform fragility" / arag-kb skill).

Reads credentials from apps/studycity/.env, never prints the token.
"""
import json
import re
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "corpus"
ENV_FILE = ROOT / ".env"
INGEST_MANIFEST = ROOT / "ingest-manifest.json"

# The corpus skews heavily toward person-shaped pages (ambassadors, board, team, alumni
# stories, mentees) whose page title is just a bare name - e.g. "Anh Thu Nguyen" gives no
# signal it's an ambassador profile rather than a board bio. That flattens them all into
# one shape for similarity search. Prefix a category label onto the title at ingest time
# (the raw scraped title is untouched in corpus/ - this is an ingest-time enrichment, not
# a rewrite of the source capture). Ordered longest-prefix-first so a more specific path
# wins.
PERSON_CATEGORY_PATTERNS = [
    (re.compile(r"^careers/career-support/career-mentoring-program/meet-the-mentees/[^/]+/?$"),
     "Career Mentoring Program Mentee"),
    (re.compile(r"^careers/alumni-community/alumni-stories/[^/]+/?$"), "Alumni Story"),
    (re.compile(r"^about-studycity/international-student-ambassadors/[^/]+/?$"),
     "International Student Ambassador"),
    (re.compile(r"^about-studycity/meet-the-board/[^/]+/?$"), "Studycity Board Member"),
    (re.compile(r"^about-studycity/meet-the-team/[^/]+/?$"), "Studycity Staff"),
]


def category_prefixed_title(url, title):
    path = url.replace("https://www.studycity.com.au", "").strip("/")
    for pattern, label in PERSON_CATEGORY_PATTERNS:
        if pattern.match(path):
            return f"{label}: {title}"
    return title


def read_env(path):
    e = {}
    for line in path.read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, _, v = line.partition("=")
            e[k.strip()] = v.split("#")[0].strip()
    return e


def main():
    env = read_env(ENV_FILE)
    kb_url = env["KB_URL"]
    token = env["KB_TOKEN"]
    headers = {
        "X-NUCLIA-SERVICEACCOUNT": f"Bearer {token}",
        "X-Synchronous": "true",
    }

    # Load the excluded-list decision from the audit step (written by audit_corpus.py)
    excluded_file = ROOT / "excluded-slugs.json"
    excluded = set(json.loads(excluded_file.read_text())) if excluded_file.exists() else set()

    files = sorted(CORPUS.glob("*.json"))
    print(f"{len(files)} corpus files found, {len(excluded)} excluded by audit")

    results = []
    for i, f in enumerate(files, 1):
        rec = json.loads(f.read_text())
        meta = rec["meta"]
        slug = meta["slug"]
        if slug in excluded:
            continue
        raw_title = meta["title"] or slug.replace("-", " ").title()
        url = meta["url"]
        title = category_prefixed_title(url, raw_title)
        # Title written into the body too, per the arag-kb / gotcha rule that a title-only
        # name never grounds.
        body_text = f"{title}\n\nSource: {url}\n\n{rec['text']}"

        payload = {
            "title": title,
            "texts": {
                "body": {
                    "body": body_text,
                    "format": "PLAIN",
                }
            },
            "origin": {"url": url},
            "usermetadata": {
                "classifications": []
            },
        }
        try:
            r = requests.post(f"{kb_url}/resources", headers={**headers, "Content-Type": "application/json"},
                               data=json.dumps(payload), timeout=60)
        except requests.RequestException as e:
            results.append({"slug": slug, "url": url, "ok": False, "error": str(e)})
            continue

        if r.status_code not in (200, 201):
            results.append({"slug": slug, "url": url, "ok": False,
                             "status": r.status_code, "body": r.text[:300]})
            continue

        rid = None
        try:
            rj = r.json()
            rid = rj.get("uuid") or rj.get("id")
        except Exception:
            pass
        results.append({"slug": slug, "url": url, "ok": True, "resource_id": rid, "title": title})
        if i % 20 == 0:
            print(f"  {i}/{len(files)} ingested...")
        time.sleep(0.15)

    ok = [r for r in results if r["ok"]]
    fail = [r for r in results if not r["ok"]]
    INGEST_MANIFEST.write_text(json.dumps(results, indent=1))
    print(f"\ningested {len(ok)} resources, {len(fail)} failed")
    if fail:
        print("failures:")
        for r in fail[:10]:
            print("  ", r["slug"], r.get("status"), r.get("body", "")[:150])
    return 0 if not fail else 1


if __name__ == "__main__":
    sys.exit(main())
