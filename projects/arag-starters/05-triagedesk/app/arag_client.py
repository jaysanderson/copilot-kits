"""Thin wrapper over the ARAG (Nuclia) Knowledge Box API used by the triage pipeline.

Auth: X-NUCLIA-SERVICEACCOUNT: Bearer <token>, server-side only - never reaches
the browser (proxy pattern, gate 6/9). Every /ask call is hard-scoped to a
single page-resource via resource_filters (arag-kb gotcha 2) and pins the
generative model explicitly (gotcha 3). Classification/extraction is done via
a plain-text /ask with a strict labelled-line output format, not the DA
Generator's json:true path - that path is a confirmed platform bug (see
CLAUDE.md "Known live platform fragility" / arag-kb gotcha 9), so we never
attempt it here.
"""
import os
import re
import time
import httpx

MODEL = os.environ.get("GEN_MODEL", "gemini-3.1-flash-lite")
# Was a bare "chatgpt-azure-4o-mini" constant with no env override. Fixed
# 29 Sep 2026: Azure-hosted generative models (chatgpt-azure-4o,
# chatgpt-azure-4o-mini) were returning HTTP 530 "Temporary error on
# information retrieval" estate-wide; gemini-3.1-flash-lite is confirmed
# working and is also the correct cheapest-capable tier under hard rule 15.


def _env():
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    env = dict(os.environ)
    if os.path.exists(path):
        for line in open(path):
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env.setdefault(k.strip(), v.split("#")[0].strip())
    return env


_ENV = _env()
KB_URL = _ENV.get("ARAG_KB_URL", "").rstrip("/")
TOKEN = _ENV.get("ARAG_SERVICEACCOUNT", "")
HDRS = {"X-NUCLIA-SERVICEACCOUNT": f"Bearer {TOKEN}"}


def configured() -> bool:
    return bool(KB_URL and TOKEN)


async def upload_page(client: httpx.AsyncClient, filename: str, content: bytes, mime: str) -> str:
    """Simple-upload one file as its own resource. Returns the resource uuid."""
    r = await client.post(
        f"{KB_URL}/upload",
        headers={**HDRS, "X-Filename": filename, "Content-Type": mime},
        content=content,
        timeout=60,
    )
    if r.status_code not in (200, 201):
        raise RuntimeError(f"upload failed ({r.status_code}): {r.text[:300]}")
    return r.json()["uuid"]


async def wait_processed(client: httpx.AsyncClient, rid: str, timeout: float = 90.0) -> str:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        r = await client.get(f"{KB_URL}/resource/{rid}", headers=HDRS, params={"show": "basic"}, timeout=30)
        if r.is_success:
            status = r.json().get("metadata", {}).get("status")
            if status in ("PROCESSED", 1):
                return "PROCESSED"
            if status in ("ERROR", 2):
                return "ERROR"
        await _sleep(1.5)
    return "TIMEOUT"


async def _sleep(seconds: float):
    import asyncio
    await asyncio.sleep(seconds)


async def resource_language(client: httpx.AsyncClient, rid: str) -> str:
    """Nuclia's own detected language for the resource (authoritative, not LLM-guessed)."""
    r = await client.get(f"{KB_URL}/resource/{rid}", headers=HDRS, params={"show": "basic"}, timeout=30)
    if not r.is_success:
        return ""
    return (r.json().get("metadata") or {}).get("language") or ""


async def delete_resource(client: httpx.AsyncClient, rid: str) -> bool:
    r = await client.delete(f"{KB_URL}/resource/{rid}", headers=HDRS, timeout=30)
    return r.status_code in (200, 204, 404)


async def labeler_classification(client: httpx.AsyncClient, rid: str) -> str | None:
    """Reads the REAL Labeler DA task's classification for this resource, if it has
    landed yet (computedmetadata.field_classifications, labelset "document_type").
    This is genuine ARAG configuration output, not app-side parsing - distinct from
    classify_page()'s /ask-based extraction, which the live per-request pipeline still
    needs for a bounded-latency synchronous response and for extracting fields the
    Labeler doesn't produce (name, stamps, dates). See app/pipeline.py for how the two
    are combined: the Labeler's label is preferred when it has already landed,
    /ask's parse is the always-available fallback.
    """
    r = await client.get(f"{KB_URL}/resource/{rid}", headers=HDRS, params={"show": "basic"}, timeout=30)
    if not r.is_success:
        return None
    classifications = (r.json().get("computedmetadata") or {}).get("field_classifications") or []
    for entry in classifications:
        for c in entry.get("classifications", []):
            if c.get("labelset") == "document_type" and c.get("label"):
                return c["label"]
    return None


CLASSIFY_SYSTEM = (
    "You are a document-triage assistant for a government academic-credential "
    "pre-check service. Read the OCR-extracted text of the single scanned page "
    "provided as context. Respond ONLY in the exact labelled-line format below, "
    "one field per line, no extra commentary, no markdown. If a field cannot be "
    "determined from the visible text, write UNKNOWN for that field.\n\n"
    "DOCUMENT_TYPE: one of DIPLOMA, TRANSCRIPT, NAME_CHANGE_CERTIFICATE, "
    "INSTITUTION_NAME_CHANGE_CERTIFICATE, EQUIVALENCY_CERTIFICATE, UNRECOGNISED\n"
    "LANGUAGE: ISO 639-1 code of the document's main language (e.g. ru, uk, en, fr, he)\n"
    "APPLICANT_NAME: the full name of the person the document is issued to, in its "
    "original script, or UNKNOWN\n"
    "INSTITUTION: the name of the issuing educational institution or authority, or UNKNOWN\n"
    "DEGREE_TYPE: the degree name or type (e.g. Bachelor of Science) if this document is a "
    "diploma or equivalency certificate, or UNKNOWN if not stated or not applicable\n"
    "DOCUMENT_DATE: the document's issue date or the study period's end date, or UNKNOWN\n"
    "APOSTILLE: PRESENT, ABSENT, or UNCLEAR - PRESENT only if the word apostille or an "
    "apostille certificate block is visibly present in the text; UNCLEAR if a stamp/seal is "
    "described but it cannot be determined whether it is specifically an apostille\n"
    "NOTARY: PRESENT, ABSENT, or UNCLEAR - as above, for notarisation wording\n"
    "CERTIFIED_COPY: PRESENT, ABSENT, or UNCLEAR - as above, for certified-true-copy wording\n"
    "SIGNATURE: PRESENT, ABSENT, or UNCLEAR - as above, for a signature or signature line\n"
    "SUMMARY: one short factual sentence describing the document\n"
)

CLASSIFY_USER = (
    "Document context (OCR text of this page):\n{context}\n\n"
    "Task: {question}\n\nRespond using only the labelled-line format from the system prompt."
)

_FIELD_RE = re.compile(
    r"^(DOCUMENT_TYPE|LANGUAGE|APPLICANT_NAME|INSTITUTION|DEGREE_TYPE|DOCUMENT_DATE|"
    r"APOSTILLE|NOTARY|CERTIFIED_COPY|SIGNATURE|SUMMARY)\s*:\s*(.*)$",
    re.IGNORECASE,
)


def _parse_labelled(text: str) -> dict:
    out = {}
    for line in text.splitlines():
        m = _FIELD_RE.match(line.strip())
        if m:
            out[m.group(1).upper()] = m.group(2).strip()
    return out


async def classify_page(client: httpx.AsyncClient, rid: str) -> dict:
    """One /ask call, hard-scoped to this page's resource, plain-text labelled-line parse.

    Returns the parsed fields plus the raw citations so the UI can show a real
    grounded/cited answer (paragraph + score) pointing back at this page.
    """
    # Query is deliberately keyword-rich across every possible doc type/field so
    # retrieval scores well regardless of which type this page turns out to be -
    # a generic instructional query (no domain keywords) scores near zero and
    # /ask returns "no_retrieval_data" even with resource_filters pinning the
    # resource (tested live 8 Aug 2026). rag_strategies full_resource then pulls
    # the whole page text into context rather than just the top paragraph.
    payload = {
        "query": (
            "diploma transcript degree certificate name change institution "
            "equivalency applicant name date issued apostille notary certified copy signature"
        ),
        "features": ["keyword", "semantic"],
        "citations": True,
        "top_k": 10,
        "resource_filters": [rid],
        "rag_strategies": [{"name": "full_resource", "count": 1}],
        "prompt": {"system": CLASSIFY_SYSTEM, "user": CLASSIFY_USER},
        "generative_model": MODEL,
    }
    r = await client.post(
        f"{KB_URL}/ask",
        headers={**HDRS, "X-Synchronous": "true", "Content-Type": "application/json"},
        json=payload,
        timeout=90,
    )
    if r.status_code != 200:
        raise RuntimeError(f"ask failed ({r.status_code}): {r.text[:300]}")
    d = r.json()
    answer_text = d.get("answer", "")
    parsed = _parse_labelled(answer_text)
    citations = []
    full_context = []
    retrieval = d.get("retrieval_results") or d.get("citations") or {}
    for res_id, res in (retrieval.get("resources") or {}).items() if isinstance(retrieval, dict) else []:
        for fid, field in (res.get("fields") or {}).items():
            for pid, para in (field.get("paragraphs") or {}).items():
                text = para.get("text") or ""
                citations.append({
                    "rid": res_id,
                    "snippet": text[:300],
                    "score": para.get("score"),
                })
                # UNTRUNCATED text, for REMi scoring - never slice the context
                # fed to a groundedness check the way the display snippet is.
                if text.strip():
                    full_context.append(text)
    return {
        "raw_answer": answer_text, "fields": parsed, "citations": citations,
        "full_context": full_context, "status": d.get("status"),
    }


REMI_QUESTION = (
    "What is this document's type, and what applicant name, institution, degree, "
    "date and authenticity indicators (apostille, notarisation, certified copy, "
    "signature) does it show?"
)


async def score_remi(client: httpx.AsyncClient, answer: str, contexts: list[str]) -> dict | None:
    """Scores one classify/extract answer for groundedness against the FULL
    retrieved page context (never just the truncated display citations - a
    thin context starves a genuinely grounded answer of the material that
    grounds it, per CLAUDE.md's REMi full-context lesson). Call shape and the
    single-concatenated-context pattern are taken from the one working REMi
    implementation in the estate (reference-repos/rwa-intel-demo/app.py):
    per-paragraph scoring punishes an answer grounded ACROSS paragraphs, one
    concatenated block does not. Returns None (never a fabricated score) if
    the call fails or there's nothing to score - callers must treat that as
    "unavailable", not "zero"."""
    ctxs = [c for c in contexts if c and c.strip()][:8]
    if not answer.strip() or not ctxs:
        return None
    payload = {
        "user_id": "akademdocs-precheck",
        "question": REMI_QUESTION,
        "answer": answer,
        "contexts": ["\n\n".join(ctxs)],
    }
    try:
        r = await client.post(
            f"{KB_URL}/predict/remi",
            headers={**HDRS, "Content-Type": "application/json"},
            json=payload,
            timeout=60,
        )
        if r.status_code != 200:
            return None
        d = r.json()
    except Exception:
        return None
    ctx_scores = d.get("context_relevance") or []
    gnd_scores = d.get("groundedness") or []
    return {
        "answer_relevance": (d.get("answer_relevance") or {}).get("score"),
        "context_relevance": max(ctx_scores) if ctx_scores else None,
        "groundedness": max(gnd_scores) if gnd_scores else None,
    }


async def classify_page_with_retry(client: httpx.AsyncClient, rid: str, attempts: int = 7, delay: float = 4.0) -> dict:
    """Retry wrapper: a resource reported PROCESSED can still lag a few seconds
    before it's actually reachable via /ask's retrieval-scored search (indexing
    propagation, observed live 8 Aug 2026 - metadata.status flips to PROCESSED
    before the resource is consistently findable). Retries on
    status == "no_retrieval_data" or a totally unparsed answer.
    """
    last = {"raw_answer": "", "fields": {}, "citations": [], "full_context": [], "status": None}
    for i in range(attempts):
        last = await classify_page(client, rid)
        if last["status"] == "success" and last["fields"].get("DOCUMENT_TYPE"):
            return last
        if i < attempts - 1:
            await _sleep(delay)
    return last
