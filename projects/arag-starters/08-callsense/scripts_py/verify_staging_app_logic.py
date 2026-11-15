"""
Verify the staging KB serves data in EXACTLY the shape the (unchanged) app
code expects - lib/arag.ts, lib/calls.ts, lib/parse.ts. This substitutes for
a live preview deploy, which is currently blocked by an expired flyctl
session auth in this environment (a genuine credential issue, not a code
issue - flagged to the lead separately). The app's own data-layer code is
NOT being changed by this reseed, only which KB it points to, so replicating
its exact read/query logic against the staging KB is a faithful proxy for
"would the cutover work" - not a substitute for the still-recommended
demo-tester/qa-reviewer pass once the cutover actually lands.

Run: .venv/bin/python apps/call-analysis/scripts_py/verify_staging_app_logic.py
"""
import json
import re
import sys
from pathlib import Path

import requests

APP_ROOT = Path(__file__).resolve().parents[1]


def read_env(path):
    e = {}
    for line in path.read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, _, v = line.partition("=")
            e[k.strip()] = v.split("#")[0].strip()
    return e


ENV = read_env(APP_ROOT / ".env.staging")
BASE = ENV["ARAG_BASE"]
KB_ID = ENV["ARAG_KB_ID"]
KEY = ENV["ARAG_API_KEY"]
GEN_MODEL = ENV["ARAG_GENERATIVE_MODEL"]
KB_URL = f"{BASE}/kb/{KB_ID}"
AUTH = {"X-NUCLIA-SERVICEACCOUNT": f"Bearer {KEY}"}

VALID_METRIC_VALUES = {
    "call_reason": {"Claims", "Billing & Payments", "Enrollment & Eligibility", "Benefits & Coverage",
                     "Prior Authorization", "Provider Network", "Pharmacy & Rx", "Complaint",
                     "Cancellation & Retention", "Portal & Tech Support"},
    "outcome": {"Resolved", "Follow-up Required", "Escalated", "Transferred", "Unresolved"},
    "sentiment": {"Positive", "Neutral", "Negative", "Mixed"},
    "line_of_business": {"Individual & Family", "Medicare Advantage", "Medicaid", "Employer Group",
                          "Dental & Vision", "Supplemental"},
}


def strip_code_fence(s):
    s = s.strip()
    m = re.match(r"^```(?:json)?\s*([\s\S]*?)\s*```$", s)
    return m.group(1) if m else s


def read_json_field(res, destination):
    for group in ("texts", "generics"):
        fields = res.get("data", {}).get(group, {})
        for fid, f in fields.items():
            if not fid.startswith("da-") or destination not in fid:
                continue
            body = (f.get("value") or {}).get("body") or f.get("body") or (f.get("extracted") or {}).get("text", {}).get("text")
            if isinstance(body, str):
                try:
                    return json.loads(strip_code_fence(body))
                except json.JSONDecodeError:
                    pass
    return None


def sanitize_metrics(raw):
    if not raw:
        return raw
    clean = dict(raw)
    dropped = []
    for key, allowed in VALID_METRIC_VALUES.items():
        v = clean.get(key)
        if isinstance(v, str) and v not in allowed:
            dropped.append((key, v))
            clean[key] = None
    return clean, dropped


def get_resource(rid, show, extracted):
    params = [("show", s) for s in show] + [("extracted", e) for e in extracted]
    r = requests.get(f"{KB_URL}/resource/{rid}", headers=AUTH, params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def main():
    rid_map = json.loads((Path(__file__).parent / "rid_map.json").read_text())
    print(f"Verifying {len(rid_map)} resources against app's exact read logic...\n")

    print("=== 1. Dashboard replication: read call_metrics, sanitize, tally by_lob ===")
    by_lob = {}
    total_dropped = []
    with_metrics = 0
    for slug, rid in rid_map.items():
        res = get_resource(rid, ["basic", "values", "extracted", "extra"], ["metadata"])
        raw_metrics = read_json_field(res, "call_metrics")
        if raw_metrics is None:
            continue
        with_metrics += 1
        clean, dropped = sanitize_metrics(raw_metrics)
        total_dropped.extend([(slug, k, v) for k, v in dropped])
        lob = clean.get("line_of_business")
        if lob:
            by_lob[lob] = by_lob.get(lob, 0) + 1

    print(f"  {with_metrics}/{len(rid_map)} resources carry a parsed call_metrics field")
    print(f"  Line of Business chart values: {by_lob}")
    refusal_leak = any("not enough" in str(k).lower() or "not enough" in str(v).lower() for _, k, v in total_dropped) or \
                   any("not enough" in lob.lower() for lob in by_lob)
    print(f"  Values dropped by sanitizeMetrics (never reach the chart): {total_dropped}")
    print(f"  Refusal-string leak into a chart: {'YES - FAIL' if refusal_leak else 'no'}")

    print("\n=== 2. Agent labels present + roled (B14) ===")
    sample_rid = list(rid_map.values())[0]
    res = get_resource(sample_rid, ["basic", "extra"], ["metadata"])
    agent_name = res.get("extra", {}).get("metadata", {}).get("agent_name")
    print(f"  Sample resource agent_name: {agent_name!r} (app renders 'Agent: {agent_name}')")

    print("\n=== 3. Live /ask round-trip, scoped to one call (exact app call shape) ===")
    media_slug = next(s for s, r in rid_map.items() if s.startswith("call-telehealth"))
    rid = rid_map[media_slug]
    ask_body = {
        "query": "Summarize this call in two sentences.",
        "resource_filters": [rid],
        "features": ["keyword", "semantic"],
        "generative_model": GEN_MODEL,
        "citations": True,
        "top_k": 8,
    }
    r = requests.post(f"{KB_URL}/ask", json=ask_body, headers={**AUTH, "Content-Type": "application/json", "X-Synchronous": "true"}, timeout=60)
    print(f"  /ask HTTP {r.status_code}")
    if r.status_code == 200:
        try:
            data = r.json()
        except json.JSONDecodeError:
            # NDJSON despite X-Synchronous in some cases - take the last line
            lines = [l for l in r.text.strip().split("\n") if l.strip()]
            data = json.loads(lines[-1])
        answer = data.get("answer", "")
        citations = data.get("citations", {})
        print(f"  answer: {answer[:200]}")
        print(f"  citations: {len(citations)} resolved key(s)")
    else:
        print(f"  BODY: {r.text[:500]}")

    print("\n=== 4. REMi call (exact app shape) ===")
    remi_body = {"user_id": "call-analysis", "question": "test", "answer": answer if r.status_code == 200 else "test answer",
                 "contexts": ["Yes, Marcus. Your employer plan covers telehealth visits with in-network providers."]}
    rr = requests.post(f"{KB_URL}/predict/remi", json=remi_body, headers={**AUTH, "Content-Type": "application/json"}, timeout=60)
    print(f"  /predict/remi HTTP {rr.status_code}: {rr.text[:300]}")

    print("\n=== 5. TRANSCRIPT-driven citation timestamp resolution spot-check ===")
    detail = get_resource(rid, ["basic", "values", "extracted", "origin", "extra"], ["text", "metadata"])
    files = detail.get("data", {}).get("files", {})
    for fname, fdata in files.items():
        paras = fdata.get("extracted", {}).get("metadata", {}).get("metadata", {}).get("paragraphs", [])
        transcript_paras = [p for p in paras if p.get("kind") == "TRANSCRIPT"]
        print(f"  field={fname}: {len(transcript_paras)} TRANSCRIPT paragraphs with start_seconds/end_seconds")
        if transcript_paras:
            p0 = transcript_paras[0]
            print(f"    sample: start={p0.get('start_seconds')} end={p0.get('end_seconds')}")

    print("\n=== DONE ===")


if __name__ == "__main__":
    main()
