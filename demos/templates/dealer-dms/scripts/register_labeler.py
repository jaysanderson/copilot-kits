#!/usr/bin/env python3
"""Register a REAL Progress Agentic RAG Labeler DA task on a genuinely
SEMANTIC axis (issue category + severity, read from free-text consultant
notes and bulletins) - never a format/doc_type axis, which is deterministic
at ingest and must never be inferred by a Labeler (the arag-kb "an LLM
Labeler types media by what it depicts" lesson).

Cost safety (hard rule 15): scoped via `rids` to exactly the 20 resources
this axis is meaningful for (14 consultant notes + 6 recall/service
bulletins), pinned to gemini-3.1-flash-lite. Estimate: 20 resources x 2
label operations x 1 LLM call each (field-level, `on: 1`) = ~40 calls on the
cheapest tier - a few cents, not corpus-wide.
"""
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

with open(os.path.join(ROOT, "corpus_manifest.json")) as f:
    manifest = json.load(f)
with open(os.path.join(ROOT, "ingest_results.json")) as f:
    ingest = json.load(f)

target_files = [
    d["file"] for d in manifest["docs"]
    if d["doc_type"] in ("consultant-note", "recall", "service-bulletin")
]
rids = [ingest[f] for f in target_files if f in ingest]
print(f"Scoping Labeler to {len(rids)} resources (consultant notes + recall/service bulletins).")
print(f"Cost estimate: {len(rids)} resources x 2 label operations, gemini-3.1-flash-lite (cheapest tier) - well under $0.10.")

CATEGORY_LABELS = [
    {"label": "brake-wear", "description": "Brake pad, rotor or braking-system condition"},
    {"label": "tyre-wear-or-alignment", "description": "Tyre tread, wear pattern or wheel alignment"},
    {"label": "recall-remedy", "description": "An open manufacturer safety recall and its remedy status"},
    {"label": "glass-or-adas", "description": "Windscreen, glass or ADAS camera calibration"},
    {"label": "software-or-electrical", "description": "Infotainment, firmware, electrical or software issue"},
    {"label": "cosmetic", "description": "Paint, panel, trim or cosmetic condition"},
    {"label": "compliance-disclosure", "description": "A disclosure or compliance-policy matter"},
    {"label": "other", "description": "Does not clearly fit another category"},
]
SEVERITY_LABELS = [
    {"label": "low", "description": "Minor, cosmetic, or no action required"},
    {"label": "medium", "description": "Should be addressed before delivery but not a safety issue"},
    {"label": "high", "description": "Safety-relevant or a hard compliance/PDI blocker"},
]

task_params = {
    "name": "ignition-issue-classification",
    "on": 1,  # whole fields
    "filter": {"rids": rids},
    "llm": {"model": arag.GEN_MODEL},
    "operations": [
        {
            "label": {
                "ident": "issue_category",
                "description": (
                    "Classify what KIND of issue or topic this document's free text is "
                    "primarily about, from the consultant's own narrative - not a coded field."
                ),
                "multiple": False,
                "labels": CATEGORY_LABELS,
            }
        },
        {
            "label": {
                "ident": "issue_severity",
                "description": (
                    "Classify how severe or urgent the issue described in this document's "
                    "free text is."
                ),
                "multiple": False,
                "labels": SEVERITY_LABELS,
            }
        },
    ],
}

# The top-level `name` is the TASK TYPE enum ('labeler', 'llm-graph', ...),
# not a custom instance name - that custom name lives inside `parameters`.
payload = {"name": "labeler", "parameters": task_params}

r = requests.post(f"{arag.KB_HOST}/kb/{arag.KB_ID}/task/start", headers=arag.HEADERS, json=payload, timeout=30)
print("task/start:", r.status_code, r.text[:500])

if r.status_code == 422 and "extra_forbidden" in r.text and "parameters" not in r.text:
    print("Retrying unwrapped (this KB's task/start wants fields at top level)...")
    flat = {"name": "labeler", **task_params}
    r = requests.post(f"{arag.KB_HOST}/kb/{arag.KB_ID}/task/start", headers=arag.HEADERS,
                       json=flat, timeout=30)
    print("task/start (flat):", r.status_code, r.text[:500])

if r.status_code not in (200, 201):
    raise SystemExit("Task registration failed - see response above.")

task_id = r.json().get("id") if isinstance(r.json(), dict) else None
print(f"\nRegistered task id: {task_id}")
print("Poll GET /kb/{id}/tasks for completion, then verify coverage via computedmetadata.field_classifications.")
