#!/usr/bin/env python3
"""30-second reset / seed script for the gov degree-triage demo.

  .venv/bin/python seed/seed.py            # seed (skips bundles already in the store)
  .venv/bin/python seed/seed.py --purge    # wipe KB resources + local submission
                                            # history, then reseed fresh

Runs each pre-built corpus bundle (seed/corpus/*.pdf) through the exact same
pipeline a live upload uses - the seeded queue is real triage output, not
mocked data.
"""
import argparse
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx

from app import arag_client as ac
from app import pipeline
from app import store

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS_DIR = os.path.join(HERE, "corpus")
MEDIA_DIR = os.path.join(os.path.dirname(HERE), "data", "media")

# (corpus filename, declared applicant name, response language)
BUNDLES = [
    ("flagship-bundle-sidorov.pdf", "איוואן איוואנוב", "he"),
    ("seed-ready-cohen.pdf", "David Cohen", "en"),
    ("seed-attention-lefevre.pdf", "Marie Lefèvre", "fr"),
    ("seed-review-ryan.pdf", "Amelia Ryan", "en"),
    ("seed-missing-docs-melnyk.pdf", "Мельник Олена Василівна", "uk"),
]


async def purge_kb():
    print("Purging KB resources...")
    async with httpx.AsyncClient() as client:
        page = 0
        deleted = 0
        while True:
            r = await client.get(f"{ac.KB_URL}/resources", headers=ac.HDRS,
                                  params={"size": 100, "page": page}, timeout=30)
            if not r.is_success:
                break
            resources = r.json().get("resources", [])
            if not resources:
                break
            for res in resources:
                await ac.delete_resource(client, res["id"])
                deleted += 1
            page += 1
    print(f"  deleted {deleted} resources")


def purge_local():
    store.purge()
    if os.path.isdir(MEDIA_DIR):
        for f in os.listdir(MEDIA_DIR):
            os.remove(os.path.join(MEDIA_DIR, f))
    print("  cleared local submission history + media")


async def seed():
    if not ac.configured():
        print("ARAG_KB_URL / ARAG_SERVICEACCOUNT not set in apps/gov-degree-triage/.env", file=sys.stderr)
        sys.exit(1)

    existing_ids = {v["applicant"]["declared_name"] for v in store.load_all()}
    for filename, declared_name, lang in BUNDLES:
        if declared_name in existing_ids:
            print(f"skip (already seeded): {filename}")
            continue
        path = os.path.join(CORPUS_DIR, filename)
        if not os.path.exists(path):
            print(f"  ! missing corpus file {path} - run generate_corpus.py first", file=sys.stderr)
            continue
        print(f"seeding {filename} ...")
        with open(path, "rb") as f:
            content = f.read()
        declared_script = pipeline.tl.detect_script(declared_name)
        verdict = await pipeline.process_submission(
            [(filename, content)], declared_name=declared_name,
            declared_script=declared_script, response_lang=lang, media_dir=MEDIA_DIR,
        )
        store.save(verdict)
        print(f"  -> {verdict['RequestId']}  overall_status={verdict['overall_status']}")


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--purge", action="store_true", help="wipe KB + local state before seeding")
    args = parser.parse_args()

    if args.purge:
        await purge_kb()
        purge_local()

    await seed()
    print("\nDone. Live demo bundle for the upload flow: seed/corpus/flagship-bundle-sidorov.pdf")


if __name__ == "__main__":
    asyncio.run(main())
