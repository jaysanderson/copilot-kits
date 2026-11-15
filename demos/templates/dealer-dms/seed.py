#!/usr/bin/env python3
"""Ignition DMS - 30-second reset.

Usage:
    .venv/bin/python seed.py --purge   # delete every resource in the KB, then reseed clean
    .venv/bin/python seed.py           # reseed without purging (fills gaps, does not dedupe)

Regenerates the synthetic corpus, re-ingests it, and recomputes the two
ARAG-backed caches (catalogue copy, dealer insights) that the app serves from.
Safe to run against a live demo between sessions.
"""
import argparse
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
PY = os.path.join(ROOT, ".venv", "bin", "python")


def read_env(path):
    e = {}
    for line in open(path):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, _, v = line.partition("=")
            e[k.strip()] = v.split("#")[0].strip()
    return e


def purge():
    import requests
    env = read_env(os.path.join(ROOT, ".env"))
    headers = {"X-NUCLIA-SERVICEACCOUNT": f"Bearer {env['KB_TOKEN']}"}
    base = env["KB_HOST"]
    kb = env["KB_ID"]
    print("Purging all resources from the Ignition KB...")
    page = 0
    total = 0
    while True:
        r = requests.get(f"{base}/kb/{kb}/resources", headers=headers,
                          params={"page_size": 200, "page": page}, timeout=30)
        d = r.json()
        res = d.get("resources", [])
        for x in res:
            requests.delete(f"{base}/kb/{kb}/resource/{x['id']}", headers=headers, timeout=30)
            total += 1
        if d.get("pagination", {}).get("last", True) or not res:
            break
        page += 1
    print(f"  deleted {total} resources.")


def run(script):
    print(f"\n=== {script} ===")
    subprocess.run([PY, os.path.join(ROOT, "scripts", script)], check=True, cwd=ROOT)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--purge", action="store_true", help="Delete every KB resource before reseeding")
    args = ap.parse_args()

    if args.purge:
        purge()

    run("gen_corpus.py")
    run("gen_media.py")
    run("enrich_manifest.py")
    run("ingest.py")
    run("generate_catalog_copy.py")
    run("compute_insights.py")

    print("\nDone. Restart the server (or POST /api/admin/reload-caches) to pick up the fresh caches.")


if __name__ == "__main__":
    main()
