#!/usr/bin/env python3
"""Delete the old media resources and re-ingest the regenerated, genuinely
distinct-per-unit recon photos (B10 fix). Updates ingest_results.json and
regenerates the catalogue copy cache for just those 14 items."""
import json
import os
import sys
import time

import requests

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

with open(os.path.join(ROOT, "media_manifest.json")) as f:
    media_manifest = json.load(f)
with open(os.path.join(ROOT, "ingest_results.json")) as f:
    ingest_results = json.load(f)
with open(os.path.join(ROOT, "corpus_copy_cache.json")) as f:
    copy_cache = json.load(f)

media_dir = os.path.join(ROOT, "corpus_media")

# delete old media resources (by filename -> old resource id)
for m in media_manifest:
    old_rid = ingest_results.get(m["file"])
    if old_rid:
        r = requests.delete(f"{arag.KB_HOST}/kb/{arag.KB_ID}/resource/{old_rid}",
                             headers=arag.HEADERS, timeout=30)
        print(f"deleted {m['file']} ({old_rid}): {r.status_code}")
        copy_cache.pop(old_rid, None)

# re-ingest
for m in media_manifest:
    fpath = os.path.join(media_dir, m["file"])
    with open(fpath, "rb") as f:
        content = f.read()
    headers = dict(arag.HEADERS)
    import base64
    headers["Content-Type"] = "image/png"
    headers["X-Filename"] = base64.b64encode(m["file"].encode()).decode()
    headers["X-Title"] = base64.b64encode(m["title"].encode()).decode()
    r = requests.post(f"{arag.KB_HOST}/kb/{arag.KB_ID}/upload", headers=headers, data=content, timeout=60)
    if r.status_code not in (200, 201):
        print(f"  upload FAILED for {m['file']}: {r.status_code} {r.text[:200]}")
        continue
    rid = r.json().get("uuid") or r.json().get("id")
    ingest_results[m["file"]] = rid

    classifications = [
        ("doc_type", "recon-photo"),
        ("site", m["site"]),
        ("make", m["make"]),
        ("body_type", m["body"]),
        ("angle", m["angle"]),
        ("stock", m["stock_no"]),
    ]
    patch = {"usermetadata": {"classifications": [{"labelset": ls, "label": lb} for ls, lb in classifications]}}
    requests.patch(f"{arag.KB_HOST}/kb/{arag.KB_ID}/resource/{rid}", headers=arag.HEADERS, json=patch, timeout=30)
    print(f"  {m['file']} -> {rid}")

    # regenerate catalogue copy from the real per-unit focus/annotation now baked into this image
    seed = (
        f"Recon documentation photo. Stock {m['stock_no']}, a {m['make']} {m['model']} "
        f"({m['body']}) at the {m['site']} site, colour as recorded on file. Angle: "
        f"{m['angle']}. Annotated finding area: {m.get('focus', 'general condition')}. "
        f"This is an illustrative recon-documentation image for a dealer operations "
        f"system, not a real vehicle photograph."
    )
    try:
        copy = arag.generate_catalog_copy(seed)
        if copy:
            copy_cache[rid] = copy
    except Exception as e:
        print(f"    warn: copy gen failed: {e}")
    time.sleep(0.15)

with open(os.path.join(ROOT, "ingest_results.json"), "w") as f:
    json.dump(ingest_results, f, indent=2)
with open(os.path.join(ROOT, "corpus_copy_cache.json"), "w") as f:
    json.dump(copy_cache, f, indent=2)

print("\nDone.")
