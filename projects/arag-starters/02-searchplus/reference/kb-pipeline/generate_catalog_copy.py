"""Generate per-institution catalogue copy (hook + highlights + chips) for the
"Find Your Path" discovery surface.

COST SAFETY (hard rule 15): this is NOT a corpus-wide ingest-time DA task - it is
one individual query-time /ask + answer_json_schema call PER resource in the
Find Your Path discovery scope (Education Providers, Study Areas, Levels of
Study, Universities, Scholarships, Applying & Pathways - ~76 resources total),
each reading only that resource's own already-cached text (no retrieval
fan-out, no per-paragraph cost). Model pinned to a cheap tier via GEN_MODEL
(default gemini-3.1-flash-lite - chatgpt-azure-4o-mini was the original pin,
verified live during this build, until it went dead on the account).
Estimated cost: ~76 short calls on a mini-tier model, a few cents total - not
worth a pre-flight estimate to Jay under the "obviously trivial" threshold,
but noted here and in the build report per hard rule 15's "state the model,
tier and rough cost" requirement.

Extended from Education-Providers-only (49 cards) to the full discovery scope
after a real defect found in build QA: Find Your Path re-ranks across all six
categories, so a card from Study Areas/Levels of Study/Universities with no
generated copy rendered as a visibly broken, mostly-empty card next to fully
populated Education Provider cards in the same grid.
"""
import json
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
ENV_FILE = ROOT / ".env"
import os
# chatgpt-azure-4o-mini (the original pin, verified live during this build) later
# went dead on the account - app.py was patched to gemini-3.1-flash-lite with a
# GEN_MODEL env override so a future dead pin doesn't need a code change; this
# script uses the same pattern.
MODEL = os.environ.get("GEN_MODEL", "gemini-3.1-flash-lite")


def read_env(path):
    e = {}
    for line in path.read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, _, v = line.partition("=")
            e[k.strip()] = v.split("#")[0].strip()
    return e


PATHWAY_CATEGORIES = {
    "Education Providers", "Study Areas", "Levels of Study",
    "Universities", "Scholarships", "Applying & Pathways",
}

SCHEMA = {
    "name": "discovery_card",
    "description": "A short, honest catalogue card summarising this page's own real content, for a prospective international student browsing.",
    "parameters": {
        "type": "object",
        "properties": {
            "hook": {"type": "string", "description": "One enticing sentence, max ~18 words, capturing what makes this page distinctive - drawn only from its own text."},
            "highlights": {
                "type": "array", "items": {"type": "string"}, "minItems": 2, "maxItems": 4,
                "description": "2-4 short factual highlights (a strength, a real number if stated, a key detail) - each under 8 words.",
            },
            "chips": {
                "type": "array", "items": {"type": "string"}, "minItems": 2, "maxItems": 5,
                "description": "2-5 short topic tags this page is about, e.g. 'Psychology', 'Vocational', 'Postgraduate', 'Scholarship'.",
            },
        },
        "required": ["hook", "highlights", "chips"],
    },
}


def main():
    env = read_env(ENV_FILE)
    kb_url = env["KB_URL"]
    token = env["KB_TOKEN"]
    headers = {
        "X-NUCLIA-SERVICEACCOUNT": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Synchronous": "true",
    }

    cache = json.loads((DATA / "resource_cache.json").read_text())
    providers = {rid: r for rid, r in cache.items() if r["category"] in PATHWAY_CATEGORIES}
    print(f"{len(providers)} discovery-scope pages to generate copy for, model={MODEL}")

    copy = {}
    if (DATA / "catalog_copy.json").exists():
        copy = json.loads((DATA / "catalog_copy.json").read_text())

    for i, (rid, r) in enumerate(providers.items(), 1):
        if rid in copy:
            continue
        query = (
            "Read the following real page text from Studycity's website, and summarise "
            "it as a catalogue card for a prospective international student. Use ONLY "
            "facts genuinely stated in this text - never invent a fee, ranking, campus "
            "count or any number not present. If the page states more than one figure for "
            "something (e.g. separate undergraduate and postgraduate fee ranges), report "
            "each one with its own real qualifier exactly as stated (e.g. \"Undergrad: "
            "AUD 25k-45k/yr\") - NEVER merge, average, or blend two separate stated "
            "figures into a single new range that does not appear verbatim in the text "
            "(a real defect found in build QA: \"AUD 25,000 to AUD 45,000\" undergrad and "
            "\"AUD 30,000 to AUD 50,000\" postgrad were merged into a fabricated "
            "\"AUD 25,000-50,000\" that never appears on the page). If reporting both "
            "figures cleanly isn't possible in a short highlight, omit the number "
            "entirely rather than approximate it.\n\n"
            f"PAGE TEXT:\n{r['text'][:3000]}"
        )
        payload = {
            "query": query, "answer_json_schema": SCHEMA, "citations": False,
            "show": ["basic"], "generative_model": MODEL,
            "resource_filters": [rid],
        }
        try:
            resp = requests.post(f"{kb_url}/ask", headers=headers, data=json.dumps(payload), timeout=60)
            resp.raise_for_status()
            obj = resp.json().get("answer_json") or {}
        except Exception as e:
            print(f"  [{i}/{len(providers)}] FAILED {r['title']}: {e}")
            continue
        copy[rid] = {
            "category": r["category"],
            "hook": obj.get("hook", ""),
            "highlights": obj.get("highlights", []),
            "chips": obj.get("chips", []),
        }
        if i % 10 == 0:
            print(f"  [{i}/{len(providers)}] {r['title']}")
            (DATA / "catalog_copy.json").write_text(json.dumps(copy, ensure_ascii=False, indent=1))
        time.sleep(0.1)

    (DATA / "catalog_copy.json").write_text(json.dumps(copy, ensure_ascii=False, indent=1))
    print(f"done - {len(copy)} cards generated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
