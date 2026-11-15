#!/usr/bin/env python3
"""Dealer Insights - genuine unstructured-to-structured extraction (Standard
B28: must showcase ARAG deriving insight from free text, never a GROUP BY on
fields that were already structured).

For every consultant field note (free-text prose, not a coded field), run a
real query-time /ask + answer_json_schema call that extracts an issue
category, severity and two risk flags from the NARRATIVE - values that do not
exist anywhere as a database column, only as something a person or an LLM has
to read and judge. Aggregate the results server-side into chart-ready counts.
Cached to disk; re-run via seed.py after any reseed.
"""
import json
import os
import sys
import time
from collections import Counter, defaultdict

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
with open(os.path.join(ROOT, "ingest_results.json")) as f:
    ingest_results = json.load(f)

STOCK_BY_NO = {s["no"]: s for s in manifest["stock"]}

CATEGORY_ENUM = [
    "brake-wear", "tyre-wear-or-alignment", "recall-remedy", "glass-or-adas",
    "software-or-electrical", "cosmetic", "compliance-disclosure", "other",
]

SCHEMA = {
    "name": "consultant_note_insight",
    "parameters": {
        "type": "object",
        "properties": {
            "issue_category": {"type": "string", "enum": CATEGORY_ENUM},
            "severity": {"type": "string", "enum": ["low", "medium", "high"]},
            "customer_facing_risk": {"type": "boolean",
                "description": "True if leaving this unaddressed could affect the customer after delivery"},
            "requires_parts_order": {"type": "boolean"},
            "one_line_rationale": {"type": "string"},
        },
        "required": ["issue_category", "severity", "customer_facing_risk",
                     "requires_parts_order", "one_line_rationale"],
    },
}

records = []
notes = [d for d in manifest["docs"] if d["doc_type"] == "consultant-note"]

print(f"Extracting structured insight from {len(notes)} consultant notes (unstructured -> structured, B28)...")
for doc in notes:
    rid = ingest_results.get(doc["file"])
    stock_no = doc.get("stock_no")
    stock = STOCK_BY_NO.get(stock_no, {})
    text = arag.get_resource_text(rid) if rid else None
    if not text:
        continue
    payload = {
        "query": (
            "Read this dealer recon consultant field note and extract the structured "
            "assessment. Note: " + text[:1400]
        ),
        "answer_json_schema": SCHEMA,
        "generative_model": os.environ.get("GEN_MODEL", "gemini-3.1-flash-lite"),
        "citations": False,
    }
    try:
        import requests
        r = requests.post(f"{env['KB_HOST']}/kb/{env['KB_ID']}/ask",
                           headers=arag.HEADERS, json=payload, timeout=40)
        r.raise_for_status()
        extracted = r.json().get("answer_json")
    except Exception as e:
        print(f"  warn: {doc['file']} failed: {e}")
        continue
    if not extracted:
        continue
    extracted["stock_no"] = stock_no
    extracted["site"] = stock.get("site")
    extracted["make"] = stock.get("make")
    records.append(extracted)
    print(f"  {stock_no}: {extracted['issue_category']} / {extracted['severity']}")
    time.sleep(0.15)

# aggregate server-side (deterministic maths, no further LLM calls)
by_category = Counter(r["issue_category"] for r in records)
by_severity = Counter(r["severity"] for r in records)
by_site = defaultdict(Counter)
for r in records:
    by_site[r["site"]][r["issue_category"]] += 1
customer_risk_count = sum(1 for r in records if r.get("customer_facing_risk"))
parts_needed_count = sum(1 for r in records if r.get("requires_parts_order"))

result = {
    "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "total_notes_analysed": len(records),
    "by_category": dict(by_category),
    "by_severity": dict(by_severity),
    "by_site": {site: dict(c) for site, c in by_site.items()},
    "customer_facing_risk_count": customer_risk_count,
    "requires_parts_order_count": parts_needed_count,
    "records": records,
}
with open(os.path.join(ROOT, "insights_cache.json"), "w") as f:
    json.dump(result, f, indent=2)

print(f"\nDone. {len(records)} notes analysed, cached to insights_cache.json.")
