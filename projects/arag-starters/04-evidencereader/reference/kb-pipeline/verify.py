"""Verify the Studycity KB after ingest: resource count reconciliation, extracted-text
readback, then eight real /ask probes covering the site's actual range plus one
deliberate out-of-corpus negative control.

Pagination gotchas (arag-kb skill): /resources keys on pagination.last, not .more;
/catalog uses fulltext.next_page. Both silently truncate at 50 otherwise.

Retrieval never returns a genuinely empty result - a deliberately irrelevant query
still returns low-scoring hits trailing toward zero (CLAUDE.md's citation-
distribution lesson). The negative control is judged by NO_CONTEXT / a declined
answer, not by an empty citations list.
"""
import json
import os
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT / ".env"


def read_env(path):
    e = {}
    for line in path.read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, _, v = line.partition("=")
            e[k.strip()] = v.split("#")[0].strip()
    return e


def list_all_resources(kb_url, headers):
    out = []
    page = 0
    while True:
        r = requests.get(f"{kb_url}/resources", headers=headers,
                          params={"page": page, "size": 50}, timeout=30)
        r.raise_for_status()
        j = r.json()
        out.extend(j.get("resources", []))
        if j.get("pagination", {}).get("last", True):
            break
        page += 1
    return out


def readback_check(kb_url, headers, resources, n=3):
    import random
    sample = random.sample(resources, min(n, len(resources)))
    out = []
    for res in sample:
        rid = res["id"]
        r = requests.get(f"{kb_url}/resource/{rid}", headers=headers,
                          params=[("show", "basic"), ("show", "extracted"), ("extracted", "text")], timeout=30)
        d = r.json()
        text = ""
        for field in d.get("data", {}).get("texts", {}).values():
            text = field.get("extracted", {}).get("text", {}).get("text", "")
            if text:
                break
        out.append({"resource_id": rid, "title": d.get("title"), "extracted_chars": len(text)})
    return out


def ask(kb_url, headers, query, model=None):
    model = model or os.environ.get("GEN_MODEL", "gemini-3.1-flash-lite")
    r = requests.post(f"{kb_url}/ask", headers={**headers, "Content-Type": "application/json", "X-Synchronous": "true"},
                       data=json.dumps({"query": query, "citations": True, "show": ["basic"], "generative_model": model}),
                       timeout=60)
    if r.status_code != 200:
        return {"answer": "", "error": f"status {r.status_code}: {r.text[:200]}"}
    return r.json()


def main():
    env = read_env(ENV_FILE)
    kb_url = env["KB_URL"]
    token = env["KB_TOKEN"]
    headers = {"X-NUCLIA-SERVICEACCOUNT": f"Bearer {token}"}

    resources = list_all_resources(kb_url, headers)
    print(f"{len(resources)} resources in KB")
    manifest = json.loads((ROOT / "ingest-manifest.json").read_text())
    ok_ingested = [r for r in manifest if r["ok"]]
    print(f"ingest-manifest.json recorded {len(ok_ingested)} successful ingests")
    print("RECONCILES OK" if len(resources) == len(ok_ingested) else "** MISMATCH **")

    print("\n--- extracted-text readback (proves real content, not just a file pointer) ---")
    for rb in readback_check(kb_url, headers, resources):
        print(f"  {rb['resource_id'][:8]} | title={rb['title']!r} | extracted_chars={rb['extracted_chars']}")
        if rb["extracted_chars"] == 0:
            print("  ** WARNING: zero extracted characters - this resource has no real text **")

    probes = [
        ("courses", "What courses can I study in the IT and computer science field in Perth?"),
        ("visa", "What visa do I need to study in Perth as an international student?"),
        ("accommodation", "What accommodation options are available for international students in Perth?"),
        ("working rights", "How many hours can I work as an international student in Perth?"),
        ("cost of living", "What does it cost to live in Perth as an international student, roughly?"),
        ("transport", "How do I get around Perth using public transport as a student?"),
        ("support services", "What support services are available if I have an emergency as an international student?"),
        ("NEGATIVE CONTROL (expected decline)", "What is the Wi-Fi password at the Studycity office?"),
    ]
    results = {}
    for label, q in probes:
        print(f"\n--- probe: {label} ---\nQ: {q}")
        j = ask(kb_url, headers, q)
        answer = j.get("answer", "")
        citations = j.get("citations") or {}
        print(f"A: {answer[:500]}")
        print(f"citations: {len(citations)}")
        results[label] = {"question": q, "answer": answer, "citation_count": len(citations)}

    (ROOT / "verify-results.json").write_text(json.dumps({
        "resource_count": len(resources), "probes": results,
    }, indent=1))
    print("\nwritten to verify-results.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
