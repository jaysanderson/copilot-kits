#!/usr/bin/env python3
"""Ingest the synthetic veterinary corpus into the vet knowledge box.

WHY THIS SCRIPT EXISTS, AND THE DEFECT IT IS FIXING
---------------------------------------------------
The portal answered "No direct evidence found" to reasonable typed questions while the
right document sat in the corpus. Measured on 9 Oct 2026: retrieval ranked the correct
document FIRST for every failing question (RRF score 0.033 with the reranker switched
off, which is the score for rank one in both the keyword and semantic lists), and the
reranker then scored it 0.038, 0.034 and 0.074 out of 1. The one question that worked
scored 0.877. The reranker was right: the documents were topically adjacent to the
questions and never contained the answers. Ten documents averaging 374 words cannot
answer what a veterinarian types. The fix is corpus depth, not a threshold.

SHAPE, COPIED FROM AN EXISTING RESOURCE RATHER THAN INVENTED
------------------------------------------------------------
  slug                        = filename stem
  title                       = frontmatter title
  texts.body.body             = the markdown body
  usermetadata.classifications = [{labelset: "topic", label: <topic>}]

A resource whose shape differs from the ones already there is a resource the portal's
own filters cannot see, which is the silent-empty-portal failure mode recorded in
DESIGN.md section 5.

COST (hard rule 15, checked BEFORE the run, not after)
------------------------------------------------------
`GET /tasks` returns configs: [], running: [], done: [], and `GET /extract_strategies`
returns {}. There is no data-augmentation or graph task on this knowledge box, so ingest
is embeddings only - no LLM call per paragraph. This is the cheap path, and it is the
reason a corpus this size can be ingested without a cost estimate first.

TEXT GOES TO /resources, NEVER /upload. `/upload` is for genuine binaries and silently
corrupts self-supplied text by OCRing it while retrieval keeps working.

Usage:
  ingest_vet.py --dry-run        parse and report, write nothing
  ingest_vet.py                  ingest every seed file, replacing by slug
  ingest_vet.py --only <slug>    one file
"""
import argparse
import json
import re
import sys
import time
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
SEED = HERE / "vet"
ENV = HERE.parent / ".env.vet"

ALLOWED_TOPICS = {
    "animal-health-production", "biosecurity-emerging-disease", "clinical-practice",
    "companion-animal", "diagnostics-pathology", "equine",
    "teaching-clinical-training", "wildlife-conservation",
}
ALLOWED_TYPES = {"advisory", "case-review", "guideline", "policy", "protocol", "report"}


def env(key):
    """Read a secret file-to-file. Never echoed, never partially masked."""
    m = re.search(rf"^{key}=(\S+)", ENV.read_text(), re.M)
    if not m:
        sys.exit(f"{key} missing from {ENV}")
    return m.group(1).split("#")[0].strip()


def frontmatter(text, path):
    """Parse the YAML-ish frontmatter without a yaml dependency.

    Deliberately strict: a file whose topic is not in the allow-list RAISES rather than
    being ingested with a bad label, because an unregistered label renders an empty
    portal section with no error anywhere.
    """
    if not text.startswith("---"):
        raise ValueError(f"{path.name}: no frontmatter")
    _, fm, body = text.split("---", 2)
    out, key, buf = {}, None, []
    for line in fm.splitlines():
        if not line.strip():
            continue
        if re.match(r"^\s*- ", line):
            buf.append(line.strip()[2:].strip().strip('"\''))
            continue
        m = re.match(r"^(\w+):\s*(.*)$", line)
        if m:
            if key and buf:
                out[key] = buf[:] if key == "keyFacts" else " ".join(buf)
            key, val, buf = m.group(1), m.group(2).strip(), []
            if val and val not in (">-", ">", "|", "|-"):
                out[key] = val.strip('"\'')
                key = None
        elif key:
            buf.append(line.strip())
    if key and buf:
        out[key] = buf[:] if key == "keyFacts" else " ".join(buf)

    for req in ("title", "topic", "type"):
        if req not in out:
            raise ValueError(f"{path.name}: frontmatter missing {req}")
    if out["topic"] not in ALLOWED_TOPICS:
        raise ValueError(f"{path.name}: topic {out['topic']!r} is not a registered label - "
                         f"ingesting it renders an empty portal section silently")
    if out["type"] not in ALLOWED_TYPES:
        raise ValueError(f"{path.name}: type {out['type']!r} outside {sorted(ALLOWED_TYPES)}")
    return out, body.lstrip("\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only")
    a = ap.parse_args()

    base, tok = env("VET_KB_URL"), env("VET_KB_TOKEN")
    H = {"X-NUCLIA-SERVICEACCOUNT": f"Bearer {tok}",
         "Content-Type": "application/json", "X-Synchronous": "true"}

    files = sorted(p for p in SEED.glob("*.md"))
    if a.only:
        files = [p for p in files if p.stem == a.only] or sys.exit(f"no seed file {a.only}")
    if not files:
        sys.exit("ZERO SEED FILES - zero of zero is not a pass")

    docs, bad = [], []
    for p in files:
        try:
            fm, body = frontmatter(p.read_text(encoding="utf-8"), p)
            words = len([w for w in body.split() if any(c.isalnum() for c in w)])
            if "Synthetic teaching content" not in body:
                bad.append(f"{p.name}: NO SYNTHETIC DISCLOSURE in the body")
                continue
            docs.append((p.stem, fm, body, words))
        except ValueError as e:
            bad.append(str(e))

    print(f"parsed {len(docs)} of {len(files)} seed files")
    thin = [(s, w) for s, _, _, w in docs if w < 600]
    if thin:
        print(f"\nTHIN - under 600 words, which is the depth that caused the original defect:")
        for s, w in sorted(thin, key=lambda x: x[1]):
            print(f"   {w:5}  {s}")
    if bad:
        print("\nREJECTED:")
        for b in bad:
            print(f"   {b}")

    total = sum(w for *_, w in docs)
    print(f"\ntotal {total:,} words across {len(docs)} documents "
          f"(mean {total // max(len(docs), 1)})")

    if a.dry_run:
        sys.exit(1 if bad else 0)
    if bad:
        sys.exit("refusing to ingest with rejected files - fix them or pass --only")

    ok, fail = [], []
    for slug, fm, body, words in docs:
        payload = {
            "slug": slug,
            "title": fm["title"],
            "texts": {"body": {"body": body, "format": "MARKDOWN"}},
            # TWO labelsets, and the second one is load-bearing for a surface you cannot see
            # from here. The vet portal's Knowledge map draws its links from documents that
            # SHARE a label, and every document carries exactly one topic - so with topic
            # alone the map renders 8 unlinked bubbles and reads "0 overlaps". `kind` is the
            # second axis that makes it a map at all (14 categories, 21 overlaps live).
            # DROP THE kind ENTRY AND THE MAP SILENTLY GOES BLANK ON THE NEXT RE-INGEST.
            # Both are deterministic reads of the document's own frontmatter - no LLM, no
            # task, no inference. Intrinsic axes are set at ingest, never guessed.
            "usermetadata": {"classifications": [
                {"labelset": "topic", "label": fm["topic"]},
                {"labelset": "kind", "label": fm["type"]},
            ]},
        }
        # Replace by slug rather than accumulate duplicates: a second copy of a document
        # splits retrieval across two near-identical resources.
        requests.delete(f"{base}/slug/{slug}", headers=H, timeout=90)
        r = requests.post(f"{base}/resources", headers=H, json=payload, timeout=180)
        if r.status_code in (200, 201):
            ok.append((slug, words))
        else:
            fail.append((slug, r.status_code, r.text[:160]))
        print(f"   {'ok ' if r.status_code in (200,201) else 'FAIL'} {r.status_code}  {words:5}w  {slug}")
        time.sleep(0.2)

    print(f"\ningested {len(ok)}, failed {len(fail)}")
    for s, c, t in fail:
        print(f"   FAIL {s} {c} {t}")

    # READ TITLES BACK. After any ingest, read titles back - a resource can accept and store
    # something other than what was sent.
    print("\nreading titles back from the knowledge box")
    time.sleep(3)
    seen, page = {}, 0
    while True:
        r = requests.get(f"{base}/resources?page={page}&size=50", headers=H, timeout=90).json()
        for res in r.get("resources") or []:
            seen[res.get("slug")] = res.get("title")
        if (r.get("pagination") or {}).get("last", True):
            break
        page += 1
    print(f"   {len(seen)} resources in the box")
    missing = [s for s, _ in ok if s not in seen]
    wrong = [(s, seen[s], fm["title"]) for s, fm, _, _ in docs
             if s in seen and seen[s] != fm["title"]]
    if missing:
        print(f"   NOT READ BACK: {missing}")
    if wrong:
        print(f"   TITLE MISMATCH: {wrong}")
    sys.exit(1 if (fail or missing or wrong) else 0)


if __name__ == "__main__":
    main()
