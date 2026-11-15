#!/usr/bin/env python3
"""Precompute catalogue copy (title/summary/highlights) for every ingested
resource via a REAL Progress Agentic RAG call (query-time /ask +
answer_json_schema, seeded with the resource's own extracted text) - never
the confirmed-broken ingest-time DA Generator task. Cached to disk and served
by the app; re-run this after any reseed (folded into seed.py).

Cost note (hard rule 15): ~60 calls on gemini-3.1-flash-lite, well under a
dollar - the cheap tier, run once, not corpus-wide per query.
"""
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def read_env(path):
    e = {}
    for line in open(path):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, _, v = line.partition("=")
            e[k.strip()] = v.split("#")[0].strip()
    return e


env = read_env(os.path.join(ROOT, ".env"))
for k, v in env.items():
    os.environ.setdefault(k, v)

import arag  # noqa: E402

with open(os.path.join(ROOT, "corpus_manifest.json")) as f:
    manifest = json.load(f)
with open(os.path.join(ROOT, "media_manifest.json")) as f:
    media_manifest = json.load(f)
with open(os.path.join(ROOT, "ingest_results.json")) as f:
    ingest_results = json.load(f)

cache = {}

print("Generating catalogue copy for text documents...")
for doc in manifest["docs"]:
    rid = ingest_results.get(doc["file"])
    if not rid:
        continue
    text = arag.get_resource_text(rid) or doc["title"]
    try:
        copy = arag.generate_catalog_copy(text)
    except Exception as e:
        print(f"  warn: {doc['file']} failed: {e}")
        continue
    if copy:
        cache[rid] = copy
        print(f"  {doc['file']} -> {copy.get('title')}")
    time.sleep(0.15)

print("Generating catalogue copy for media items...")
for m in media_manifest:
    rid = ingest_results.get(m["file"])
    if not rid:
        continue
    seed = (
        f"Recon documentation photo. Stock {m['stock_no']}, a {m['make']} {m['model']} "
        f"({m['body']}) at the {m['site']} site. Angle: {m['angle']}. This is an "
        f"illustrative recon-documentation image for a dealer operations system, not a "
        f"real vehicle photograph."
    )
    try:
        copy = arag.generate_catalog_copy(seed)
    except Exception as e:
        print(f"  warn: {m['file']} failed: {e}")
        continue
    if copy:
        cache[rid] = copy
        print(f"  {m['file']} -> {copy.get('title')}")
    time.sleep(0.15)

with open(os.path.join(ROOT, "corpus_copy_cache.json"), "w") as f:
    json.dump(cache, f, indent=2)

print(f"\nDone. {len(cache)} items cached.")
