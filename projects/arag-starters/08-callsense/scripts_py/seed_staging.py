"""
Seed the staging KB (apps/call-analysis/.env.staging) with the ElevenLabs
voice-cast corpus: 16 re-rendered media resources (from scripts_py/render_media.py
output) + 8 unchanged transcript resources, identical labelsets/DA-task
definitions to the live KB except the DA tasks are pinned to the cheap
chatgpt-azure-4o-mini tier (hard rule 15 fix - the live KB's three tasks ran
on the premium chatgpt-azure-4o, a disclosed gap from the 12 Sep 2026 harden
pass). Never touches the live KB (550da8b5-dbf2-4f45-9277-f75ae33ec738).
"""
import base64
import json
import subprocess
import sys
import time
from pathlib import Path

import requests

APP_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).parent))
from scenarios import SCENARIOS, icon_for, media_type_for, transcript_text  # noqa: E402

MEDIA_DIR = APP_ROOT / "scripts_py" / "media_output"


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
CHEAP_MODEL = {"model": "chatgpt-azure-4o-mini", "provider": "openai"}

KB_URL = f"{BASE}/kb/{KB_ID}"
AUTH = {"X-NUCLIA-SERVICEACCOUNT": f"Bearer {KEY}"}


def api(path, method="GET", body=None, raw=None, headers=None, query=None, repeat_query=None):
    url = KB_URL + path
    h = dict(AUTH)
    if headers:
        h.update(headers)
    kwargs = {"headers": h, "timeout": 60}
    if query:
        url += "?" + "&".join(f"{k}={v}" for k, v in query.items())
    if repeat_query:
        # e.g. show=basic&show=values (repeated key, not comma-joined)
        sep = "&" if "?" in url else "?"
        url += sep + "&".join(f"{k}={v}" for k, v in repeat_query)
    if raw is not None:
        r = requests.request(method, url, data=raw, headers=h, timeout=120)
    elif body is not None:
        h["Content-Type"] = "application/json"
        r = requests.request(method, url, json=body, headers=h, timeout=60)
    else:
        r = requests.request(method, url, headers=h, timeout=60)
    return r


# ---------------- Labelsets ----------------

RESOURCE_LABELSETS = [
    {"id": "call_reason", "title": "Call Reason", "color": "#2563eb", "multiple": False, "kind": "RESOURCES",
     "labels": ["Claims", "Billing & Payments", "Enrollment & Eligibility", "Benefits & Coverage",
                "Prior Authorization", "Provider Network", "Pharmacy & Rx", "Complaint",
                "Cancellation & Retention", "Portal & Tech Support"]},
    {"id": "call_outcome", "title": "Outcome", "color": "#16a34a", "multiple": False, "kind": "RESOURCES",
     "labels": ["Resolved", "Follow-up Required", "Escalated", "Transferred", "Unresolved"]},
    {"id": "sentiment", "title": "Sentiment", "color": "#db2777", "multiple": False, "kind": "RESOURCES",
     "labels": ["Positive", "Neutral", "Negative", "Mixed"]},
    {"id": "line_of_business", "title": "Line of Business", "color": "#9333ea", "multiple": False, "kind": "RESOURCES",
     "labels": ["Individual & Family", "Medicare Advantage", "Medicaid", "Employer Group", "Dental & Vision", "Supplemental"]},
    {"id": "disposition_flags", "title": "Disposition Flags", "color": "#ea580c", "multiple": True, "kind": "RESOURCES",
     "labels": ["Complaint Raised", "Cross-sell Offered", "Cross-sell Accepted", "Retention Save",
                "Compliance Risk", "Coverage Denied", "First-Call Resolution", "Vulnerable Member"]},
]
PARAGRAPH_LABELSET = {"id": "moment", "title": "Call Moment", "color": "#0891b2", "multiple": True, "kind": "PARAGRAPHS",
    "labels": ["Greeting & Verification", "Problem Statement", "Complaint", "Cross-sell Pitch", "Objection",
               "Resolution", "Compliance Disclosure", "Escalation", "Empathy Statement", "Next Steps", "Sensitive / PII"]}
ALL_LABELSETS = RESOURCE_LABELSETS + [PARAGRAPH_LABELSET]

LABEL_DESCRIPTIONS = {
    "Claims": "Status, denial, payment, or submission of a medical/dental claim.",
    "Billing & Payments": "Premiums, invoices, autopay, refunds, payment failures.",
    "Enrollment & Eligibility": "Signing up, adding/removing dependents, plan changes, effective dates, eligibility checks.",
    "Benefits & Coverage": "What is covered, copays, deductibles, out-of-pocket maximums, in/out of network coverage questions.",
    "Prior Authorization": "Pre-approval for procedures, imaging, surgery, or specialist referrals.",
    "Provider Network": "Finding in-network doctors, hospitals, or specialists; provider directory issues.",
    "Pharmacy & Rx": "Prescription drug coverage, formulary, pharmacy benefits, medication cost.",
    "Complaint": "Member is primarily calling to complain about service, denial, billing error, or experience.",
    "Cancellation & Retention": "Member wants to cancel, downgrade, or is shopping competitors.",
    "Portal & Tech Support": "Login, app, ID card, website, or technical issues.",
    "Resolved": "Member's issue was fully resolved on this call.",
    "Follow-up Required": "Resolution pending a callback, document, or future action.",
    "Escalated": "Routed to a supervisor, specialist team, or grievance process.",
    "Transferred": "Handed to another department without resolution.",
    "Unresolved": "Call ended without resolving the member's issue.",
    "Positive": "Member was satisfied/grateful overall.",
    "Neutral": "Matter-of-fact, no strong emotion.",
    "Negative": "Member was frustrated, upset, or angry overall.",
    "Mixed": "Started negative but improved, or vice versa.",
    "Individual & Family": "Individual or family commercial plan.",
    "Medicare Advantage": "Medicare Advantage / senior plans.",
    "Medicaid": "Medicaid / state-sponsored plans.",
    "Employer Group": "Coverage through an employer group plan.",
    "Dental & Vision": "Standalone dental or vision plan.",
    "Supplemental": "Supplemental/ancillary products (accident, critical illness, hospital indemnity).",
    "Complaint Raised": "A complaint or grievance was expressed during the call.",
    "Cross-sell Offered": "The agent offered an additional product or plan.",
    "Cross-sell Accepted": "The member agreed to an additional product or plan.",
    "Retention Save": "A member who wanted to cancel was retained.",
    "Compliance Risk": "Possible compliance issue: missing disclosure, PHI mishandling, unverified identity.",
    "Coverage Denied": "A claim, service, or authorization was denied.",
    "First-Call Resolution": "Issue resolved on the first contact with no follow-up.",
    "Vulnerable Member": "Member appears elderly, distressed, or in a sensitive health situation.",
    "Greeting & Verification": "Opening, identity verification, HIPAA verification.",
    "Problem Statement": "The member explains why they are calling.",
    "Cross-sell Pitch": "The agent pitches an additional product, plan, or upgrade.",
    "Objection": "The member pushes back, hesitates, or declines an offer.",
    "Resolution": "The agent resolves the issue or states the resolution/next steps for the problem.",
    "Compliance Disclosure": "Required disclosure, recording notice, terms, or regulatory script.",
    "Escalation": "The call is escalated to a supervisor or specialist.",
    "Empathy Statement": "The agent acknowledges feelings or expresses empathy.",
    "Next Steps": "Wrap-up, summary of actions, and what happens next.",
    "Sensitive / PII": "Personal, health, or payment information is shared (SSN, DOB, diagnosis, card number).",
}


def create_labelsets():
    for ls in ALL_LABELSETS:
        body = {"title": ls["title"], "color": ls["color"], "multiple": ls["multiple"],
                "kind": [ls["kind"]], "labels": [{"title": t} for t in ls["labels"]]}
        r = requests.post(f"{KB_URL}/labelset/{ls['id']}", json=body, headers={**AUTH, "Content-Type": "application/json"}, timeout=30)
        print(f"  labelset {'OK' if r.status_code in (200, 201) else 'FAIL ' + str(r.status_code)}: {ls['id']} ({len(ls['labels'])} labels)")


# ---------------- Resources ----------------

def origin_and_extra(sc, duration_sec):
    media_type = media_type_for(sc["format"])
    return {
        "origin": {
            "created": sc["createdISO"], "modified": sc["createdISO"],
            "path": f"/{sc['queue']}", "tags": [media_type, sc["queue"]],
            "collaborators": [sc["agentName"]],
        },
        "extra": {"metadata": {
            "agent_name": sc["agentName"], "member_id": sc["memberId"], "queue": sc["queue"],
            "duration_sec": duration_sec, "media_type": media_type,
        }},
    }


def create_text_resource(sc):
    body = {"title": sc["title"], "slug": sc["slug"], "icon": "text/plain",
            **origin_and_extra(sc, None),
            "texts": {"transcript": {"body": transcript_text(sc), "format": "PLAIN"}}}
    r = requests.post(f"{KB_URL}/resources", json=body, headers={**AUTH, "Content-Type": "application/json"}, timeout=30)
    r.raise_for_status()
    return r.json()["uuid"]


def create_resource_shell(sc, duration_sec):
    body = {"title": sc["title"], "slug": sc["slug"], "icon": icon_for(sc["format"]),
            **origin_and_extra(sc, duration_sec)}
    r = requests.post(f"{KB_URL}/resources", json=body, headers={**AUTH, "Content-Type": "application/json"}, timeout=30)
    r.raise_for_status()
    return r.json()["uuid"]


def upload_file_field(rid, filepath: Path, content_type: str):
    data = filepath.read_bytes()
    filename_b64 = base64.b64encode(filepath.name.encode()).decode()
    r = requests.post(f"{KB_URL}/resource/{rid}/file/media/upload", data=data,
                       headers={**AUTH, "Content-Type": content_type, "X-FILENAME": filename_b64, "X-LANGUAGE": "en"},
                       timeout=180)
    r.raise_for_status()


def ffprobe_duration(path: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                           "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
                          check=True, capture_output=True, text=True).stdout.strip()
    return round(float(out), 2)


def ingest_all():
    rid_by_slug = {}
    for sc in SCENARIOS:
        if sc["format"] == "transcript":
            rid = create_text_resource(sc)
            print(f"  text     {sc['slug']} -> {rid}")
        else:
            ext = "mp3" if sc["format"] == "mp3" else "mp4"
            path = MEDIA_DIR / f"{sc['slug']}.{ext}"
            duration = ffprobe_duration(path)
            rid = create_resource_shell(sc, duration)
            upload_file_field(rid, path, icon_for(sc["format"]))
            print(f"  media    {sc['slug']} -> {rid} ({duration}s)")
        rid_by_slug[sc["slug"]] = rid
    return rid_by_slug


def wait_for_processed(rid_by_slug, timeout_s=900):
    pending = dict(rid_by_slug)
    start = time.time()
    while pending and time.time() - start < timeout_s:
        for slug, rid in list(pending.items()):
            r = requests.get(f"{KB_URL}/resource/{rid}", params={"show": "basic"}, headers=AUTH, timeout=30)
            if r.status_code == 200 and r.json().get("metadata", {}).get("status") == "PROCESSED":
                print(f"  processed OK {slug}")
                del pending[slug]
            elif r.status_code == 200 and r.json().get("metadata", {}).get("status") == "ERROR":
                print(f"  processed ERROR {slug}")
                del pending[slug]
        if pending:
            time.sleep(8)
    if pending:
        print(f"  still pending after {timeout_s}s: {list(pending.keys())}")
    return pending


def verify_transcript_paragraphs(rid_by_slug):
    """Count TRANSCRIPT-kind paragraphs per media resource in rid_by_slug (may
    be the full 24 or a retry subset). Returns dict slug -> count, and list
    of failures. Only iterates scenarios actually present in rid_by_slug."""
    failures = []
    counts = {}
    for sc in SCENARIOS:
        if sc["format"] == "transcript" or sc["slug"] not in rid_by_slug:
            continue
        rid = rid_by_slug[sc["slug"]]
        url = f"{KB_URL}/resource/{rid}"
        r = requests.get(url, headers=AUTH, timeout=30,
                          params=[("show", "basic"), ("show", "values"), ("show", "extracted"),
                                  ("extracted", "text"), ("extracted", "metadata")])
        r.raise_for_status()
        data = r.json()
        files = data.get("data", {}).get("files", {})
        kinds = set()
        n_transcript = 0
        for fname, fdata in files.items():
            paras = fdata.get("extracted", {}).get("metadata", {}).get("metadata", {}).get("paragraphs", [])
            for p in paras:
                kinds.add(p.get("kind"))
                if p.get("kind") == "TRANSCRIPT":
                    n_transcript += 1
        counts[sc["slug"]] = n_transcript
        status = "OK" if n_transcript > 0 else "MISSING"
        print(f"  {status:8s} {sc['slug']:45s} TRANSCRIPT paragraphs={n_transcript} kinds={kinds}")
        if n_transcript == 0:
            failures.append(sc["slug"])
    return counts, failures


def reprocess(rid):
    r = requests.post(f"{KB_URL}/resource/{rid}/reprocess", headers=AUTH, timeout=30)
    return r.status_code


# ---------------- DA tasks ----------------

def label_ops(sets):
    return [{"label": {"ident": ls["id"],
                        "description": f"Classify the call by {ls['title']}. " + ("Apply all that genuinely apply." if ls["multiple"] else "Choose the single best label."),
                        "multiple": ls["multiple"],
                        "labels": [{"label": t, "description": LABEL_DESCRIPTIONS[t], "examples": []} for t in ls["labels"]]}}
            for ls in sets]


ANALYSIS_PROMPT = """You are a call-analysis engine for a US health-insurance contact center. Analyze the call transcript and return ONLY a JSON object with exactly these keys:
{
  "executive_summary": string (2-3 sentence summary of the whole call),
  "member_intent": string (why the member called, one sentence),
  "key_topics": string[] (3-6 short topic tags),
  "agent_scorecard": { "empathy": number (0-100), "compliance": number (0-100), "resolution_effectiveness": number (0-100) },
  "complaint": { "present": boolean, "category": string|null, "severity": "low"|"medium"|"high"|null, "quote": string|null },
  "cross_sell": { "offered": boolean, "product": string|null, "accepted": boolean, "objection": string|null },
  "action_items": string[] (concrete follow-ups, empty if none),
  "risk_flags": string[] (compliance/retention/clinical risks, empty if none),
  "notable_quotes": [ { "speaker": "Agent"|"Member", "quote": string } ]
}
Base every field strictly on the transcript. Do not invent facts."""

METRICS_PROMPT = """You are a call-analytics engine for a US health-insurance contact center. Analyze the call transcript and return ONLY a FLAT JSON object of metrics suitable for dashboard aggregation, with exactly these keys (use the allowed values):
{
  "call_reason": one of ["Claims","Billing & Payments","Enrollment & Eligibility","Benefits & Coverage","Prior Authorization","Provider Network","Pharmacy & Rx","Complaint","Cancellation & Retention","Portal & Tech Support"],
  "outcome": one of ["Resolved","Follow-up Required","Escalated","Transferred","Unresolved"],
  "sentiment": one of ["Positive","Neutral","Negative","Mixed"],
  "line_of_business": one of ["Individual & Family","Medicare Advantage","Medicaid","Employer Group","Dental & Vision","Supplemental"],
  "complaint": boolean,
  "complaint_category": string|null,
  "cross_sell_offered": boolean,
  "cross_sell_accepted": boolean,
  "csat_estimate": integer 1-5,
  "compliance_score": integer 0-100,
  "first_call_resolution": boolean,
  "escalated": boolean,
  "product_mentioned": string|null
}
Base every field strictly on the transcript. Do not invent facts."""

AGENTS = [
    {"key": "resource-labeler", "type": "labeler",
     "parameters": {"name": "resource-labeler", "on": 1, "operations": label_ops(RESOURCE_LABELSETS), "llm": CHEAP_MODEL}},
    {"key": "paragraph-labeler", "type": "labeler",
     "parameters": {"name": "paragraph-labeler", "on": 0, "operations": label_ops([PARAGRAPH_LABELSET]), "llm": CHEAP_MODEL}},
    {"key": "call-insights", "type": "ask",
     "parameters": {"name": "call-insights", "on": 1, "operations": [
         {"ask": {"question": ANALYSIS_PROMPT, "destination": "call_analysis", "json": False}},
         {"ask": {"question": METRICS_PROMPT, "destination": "call_metrics", "json": False}},
     ], "llm": CHEAP_MODEL}},
]


def list_tasks():
    r = requests.get(f"{KB_URL}/tasks", headers=AUTH, timeout=30)
    r.raise_for_status()
    return r.json()


def start_agent(agent):
    r = requests.post(f"{KB_URL}/task/start", json={"name": agent["type"], "parameters": agent["parameters"]},
                       headers={**AUTH, "Content-Type": "application/json"}, timeout=30)
    r.raise_for_status()
    return r.json()["id"]


def wait_tasks_idle(timeout_s=600):
    time.sleep(8)
    start = time.time()
    while time.time() - start < timeout_s:
        d = list_tasks()
        running = [t for t in d.get("running", []) if not t.get("stopped")]
        if not running:
            time.sleep(6)
            return True
        time.sleep(6)
    return False


def run_agents_sequentially():
    ids = {}
    for a in AGENTS:
        tid = start_agent(a)
        ids[a["key"]] = tid
        print(f"  agent -> {a['key']} ({a['type']}) id={tid} ... waiting")
        ok = wait_tasks_idle()
        print(f"  agent settled: {a['key']} (idle={ok})")
    return ids


# ---------------- Search configurations ----------------

SEARCH_CONFIGS = {
    "Demo - Compliance & QA": {
        "kind": "ask", "config": {
            "highlight": False,
            "prompt": {"system": "You are a call-quality and compliance reviewer for a health insurer. For each theme, assess whether required disclosures were made and whether the agent followed process, and note how the issue was resolved or escalated. Flag any compliance risks or missed disclosures explicitly, rate handling as good, adequate or needs review, and keep it brief and audit-focused. Ground every point in the cited calls."},
            "citations": True, "show_hidden": False,
            "rag_strategies": [{"name": "neighbouring_paragraphs", "before": 2, "after": 2}],
            "rag_images_strategies": [], "rephrase": True, "prefer_markdown": False,
        },
    },
    "Demo - Deep analysis": {
        "kind": "ask", "config": {
            "highlight": False,
            "prompt": {"system": "You are a senior call-centre analyst. Give a thorough, structured analysis of the member calls. Group the drivers into clear themes, quantify each where the data allows, describe sentiment and how calls are resolved, and call out compliance risks and coaching opportunities. Use short headed sections and ground every point in the cited calls."},
            "citations": True, "show_hidden": False,
            "rag_strategies": [{"name": "neighbouring_paragraphs", "before": 2, "after": 2}],
            "rag_images_strategies": [], "rephrase": True, "prefer_markdown": False,
        },
    },
    "Demo - Quick answer": {
        "kind": "ask", "config": {
            "highlight": False, "citations": True, "show_hidden": False,
            "rag_strategies": [{"name": "neighbouring_paragraphs", "before": 2, "after": 2}],
            "rag_images_strategies": [], "rephrase": True, "prefer_markdown": False,
        },
    },
}


def create_search_configs():
    for name, cfg in SEARCH_CONFIGS.items():
        r = requests.post(f"{KB_URL}/search_configurations/{name}", json=cfg,
                           headers={**AUTH, "Content-Type": "application/json"}, timeout=30)
        print(f"  search_config {'OK' if r.status_code in (200, 201) else 'FAIL ' + str(r.status_code) + ' ' + r.text[:200]}: {name}")


# ---------------- Coverage verification (facet-aggregation is BANNED - CLAUDE.md) ----------------

def verify_label_coverage(rid_by_slug):
    """Never use faceted aggregation (POST or GET) - re-derive each label's
    presence by reading each resource's own computedmetadata directly."""
    total = len(rid_by_slug)
    labelset_hit_counts = {ls["id"]: 0 for ls in RESOURCE_LABELSETS}
    moment_hit_count = 0
    for slug, rid in rid_by_slug.items():
        r = requests.get(f"{KB_URL}/resource/{rid}", headers=AUTH, timeout=30, params={"show": "basic"})
        r.raise_for_status()
        data = r.json()
        fcls = data.get("computedmetadata", {}).get("field_classifications", [])
        seen_sets = set()
        seen_moment = False
        for fc in fcls:
            for c in fc.get("classifications", []):
                ls = c.get("labelset")
                if ls in labelset_hit_counts:
                    seen_sets.add(ls)
                if ls == "moment":
                    seen_moment = True
        for ls in seen_sets:
            labelset_hit_counts[ls] += 1
        if seen_moment:
            moment_hit_count += 1
    print(f"\n  Resource-level labelset coverage (of {total} resources):")
    for ls_id, count in labelset_hit_counts.items():
        print(f"    {ls_id:20s} {count}/{total}")
    print(f"    {'moment (paragraph)':20s} {moment_hit_count}/{total} resources carry >=1 moment label")
    return labelset_hit_counts, moment_hit_count


if __name__ == "__main__":
    print("This module is imported by run_staging_seed.py - run that instead.")
