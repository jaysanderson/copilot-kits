#!/usr/bin/env python3
"""Ingest the Coppermill Motor Group corpus into the Ignition DMS Knowledge Box.

Uses the single-call POST /kb/{id}/upload pattern (the two-step create+PUT
pattern 500s on this deployment - see the arag-kb skill gotcha 1), then PATCHes
metadata (title, summary, usermetadata classifications) onto the created
resource. Classification axes here are DETERMINISTIC (doc_type, site, make,
urgency) - known at generation time, never inferred by an LLM labeler, per the
"format/provenance axes are deterministic, never Labeler-inferred" rule.
"""
import base64
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
KB_HOST = env["KB_HOST"]
KB_ID = env["KB_ID"]
TOKEN = env["KB_TOKEN"]
HEADERS_BASE = {"X-NUCLIA-SERVICEACCOUNT": f"Bearer {TOKEN}", "X-Synchronous": "true"}

with open(os.path.join(ROOT, "corpus_manifest.json")) as f:
    manifest = json.load(f)
with open(os.path.join(ROOT, "media_manifest.json")) as f:
    media_manifest = json.load(f)

STOCK_BY_NO = {s["no"]: s for s in manifest["stock"]}


def upload_file(filename, content_bytes, content_type, title):
    url = f"{KB_HOST}/kb/{KB_ID}/upload"
    headers = dict(HEADERS_BASE)
    headers["Content-Type"] = content_type
    headers["X-Filename"] = base64.b64encode(filename.encode()).decode()
    if title:
        headers["X-Title"] = base64.b64encode(title.encode()).decode()
    r = requests.post(url, headers=headers, data=content_bytes, timeout=60)
    if r.status_code not in (200, 201):
        raise SystemExit(f"upload failed for {filename}: {r.status_code} {r.text[:300]}")
    body = r.json()
    return body.get("uuid") or body.get("id")


def patch_resource(rid, title=None, summary=None, classifications=None):
    url = f"{KB_HOST}/kb/{KB_ID}/resource/{rid}"
    payload = {}
    if title:
        payload["title"] = title
    if summary:
        payload["summary"] = summary
    if classifications:
        payload["usermetadata"] = {
            "classifications": [
                {"labelset": ls, "label": lb} for ls, lb in classifications
            ]
        }
    if not payload:
        return
    r = requests.patch(url, headers=HEADERS_BASE, json=payload, timeout=30)
    if r.status_code not in (200, 204):
        print(f"  warn: patch failed for {rid}: {r.status_code} {r.text[:200]}")


def main():
    corpus_dir = os.path.join(ROOT, "corpus")
    media_dir = os.path.join(ROOT, "corpus_media")
    results = {}

    print("Ingesting text corpus...")
    for doc in manifest["docs"]:
        fpath = os.path.join(corpus_dir, doc["file"])
        with open(fpath, "rb") as f:
            content = f.read()
        rid = upload_file(doc["file"], content, "text/markdown", doc["title"])
        classifications = [("doc_type", doc["doc_type"])]
        if doc.get("site"):
            classifications.append(("site", doc["site"]))
        if doc.get("make"):
            classifications.append(("make", doc["make"]))
        if doc.get("urgency"):
            classifications.append(("urgency", doc["urgency"]))
        if doc.get("stock_no"):
            classifications.append(("stock", doc["stock_no"]))
        patch_resource(rid, classifications=classifications)
        results[doc["file"]] = rid
        print(f"  {doc['file']} -> {rid}")

    print("Ingesting media library images...")
    for m in media_manifest:
        fpath = os.path.join(media_dir, m["file"])
        with open(fpath, "rb") as f:
            content = f.read()
        rid = upload_file(m["file"], content, "image/png", m["title"])
        classifications = [
            ("doc_type", "recon-photo"),
            ("site", m["site"]),
            ("make", m["make"]),
            ("body_type", m["body"]),
            ("angle", m["angle"]),
            ("stock", m["stock_no"]),
        ]
        patch_resource(rid, classifications=classifications)
        results[m["file"]] = rid
        print(f"  {m['file']} -> {rid}")

    with open(os.path.join(ROOT, "ingest_results.json"), "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nDone. {len(results)} resources ingested.")


if __name__ == "__main__":
    main()
