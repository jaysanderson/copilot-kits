"""
REMi, scored properly (CLAUDE.md relational-sync finding #7 / feedback_remi_on_rao_surface_needs_grounding_context):
"REMi context on a short-record corpus must be built from cited record BODIES,
not scored paragraphs." verify_staging_app_logic.py's REMi call used a single
hardcoded placeholder sentence unrelated to the real answer - this script fixes
that by extracting the real cited resource id(s) from the /ask response's
`citations` keys, fetching each cited resource's FULL extracted text body, and
passing those bodies as the REMi context list.

Run: .venv/bin/python apps/call-analysis/scripts_py/verify_remi_proper_context.py
"""
import json
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
import seed_staging as s  # noqa: E402


def cited_resource_ids(citations: dict) -> list[str]:
    ids = []
    for key in citations:
        rid = key.split("/")[0]
        if rid not in ids:
            ids.append(rid)
    return ids


def resource_full_text(rid: str) -> str:
    r = requests.get(
        f"{s.KB_URL}/resource/{rid}", headers=s.AUTH, timeout=30,
        params=[("show", "basic"), ("show", "values"), ("show", "extracted"), ("extracted", "text")],
    )
    r.raise_for_status()
    data = r.json()
    files = data.get("data", {}).get("files", {})
    texts_field = data.get("data", {}).get("texts", {})
    parts = []
    for fdata in files.values():
        t = fdata.get("extracted", {}).get("text", {}).get("text", "")
        if t:
            parts.append(t)
    for fdata in texts_field.values():
        t = fdata.get("extracted", {}).get("text", {}).get("text", "")
        if t:
            parts.append(t)
    return "\n".join(parts)


def main():
    rid_map = json.loads((Path(__file__).parent / "rid_map.json").read_text())
    slug = "call-telehealth-benefit-0023"
    rid = rid_map[slug]

    question = "Summarize this call in two sentences."
    ask_body = {
        "query": question,
        "resource_filters": [rid],
        "features": ["keyword", "semantic"],
        "generative_model": s.ENV.get("ARAG_GENERATIVE_MODEL", "chatgpt-azure-4o-mini"),
        "citations": True,
        "top_k": 8,
    }
    r = requests.post(f"{s.KB_URL}/ask", json=ask_body,
                       headers={**s.AUTH, "Content-Type": "application/json", "X-Synchronous": "true"}, timeout=60)
    r.raise_for_status()
    data = r.json()
    answer = data.get("answer", "")
    citations = data.get("citations", {})
    print(f"Question: {question}")
    print(f"Answer: {answer}\n")

    cited_rids = cited_resource_ids(citations)
    print(f"Cited resource id(s): {cited_rids}")

    contexts = [resource_full_text(r) for r in cited_rids]
    contexts = [c for c in contexts if c.strip()]
    print(f"Context(s) passed to REMi: {len(contexts)} full cited-record bodies, "
          f"{sum(len(c) for c in contexts)} total chars\n")

    remi_body = {"user_id": "call-analysis", "question": question, "answer": answer, "contexts": contexts}
    rr = requests.post(f"{s.KB_URL}/predict/remi", json=remi_body,
                        headers={**s.AUTH, "Content-Type": "application/json"}, timeout=60)
    print(f"/predict/remi HTTP {rr.status_code}")
    print(json.dumps(rr.json(), indent=2))


if __name__ == "__main__":
    main()
