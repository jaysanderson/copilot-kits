"""Cartwright Freight Group - ARAG proxy layer (UC01 Contract Terms Desk).

Every call to ARAG is server-side only; the KB service-account token never
reaches the browser. Pattern lifted directly from working code in
reference-repos/plant-demo-erp/ai.py and reference-repos/rwa-intel-demo/app.py.

Mechanism used for UC01: query-time POST /kb/{kb}/ask with a saved KB
search_configuration ("contract-desk", kind=ask) that carries the honest,
on-brand system prompt - configured on the KB itself (visible in the ARAG
admin console), not hardcoded in this file. REMi (POST {kb}/predict/remi)
is scored against the FULL retrieved paragraph set, not just the cited
excerpts (CLAUDE.md's ResearchOS fix - thin context makes a good answer
score as ungrounded).

Known platform gap (found live provisioning this KB, 20 Aug 2026): when
retrieval genuinely finds nothing relevant, /ask returns status "no_context"
and a fixed platform string ("Not enough data to answer this.") regardless
of the search_configuration's own system prompt - the LLM path is
short-circuited before the prompt ever applies. This is disclosed, not
hidden: see NO_CONTEXT_MESSAGE below and the architecture reveal in the
frontend, which states plainly that ARAG's own retrieval made the honest
call to decline (never fabricating an answer) and only the wording shown
is supplied by this app, not by an ARAG-native message field.
"""
import asyncio
import json
import os
import re
import time
from collections import Counter
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent


def env():
    """Local dev reads .env; a deployed container has no .env file (it's
    gitignored, never baked into the image) and gets these instead as real
    Fly secrets / process env vars - which take precedence when both are
    present. Same pattern as reference-repos/plant-demo-erp/erp.py."""
    e = {}
    if (ROOT / ".env").exists():
        for line in (ROOT / ".env").read_text().splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, _, v = line.partition("=")
                e[k.strip()] = v.strip()
    e.update({k: v for k, v in os.environ.items()
              if k.startswith(("ARAG_", "KB_", "APP_"))})
    return e


ENV = env()
HOST = ENV.get("ARAG_HOST", "")
KB = ENV.get("KB_ID", "")
HDRS = {"X-NUCLIA-SERVICEACCOUNT": f"Bearer {ENV.get('KB_TOKEN', '')}"}
MODEL = os.environ.get("GEN_MODEL", "gemini-3.1-flash-lite")
# Was a bare "chatgpt-azure-4o-mini" constant with no env override. Fixed
# 29 Sep 2026: Azure-hosted generative models (chatgpt-azure-4o,
# chatgpt-azure-4o-mini) were returning HTTP 530 "Temporary error on
# information retrieval" estate-wide (confirmed live on this app's /api/ask -
# every call 502ing with that exact upstream error); gemini-3.1-flash-lite is
# confirmed working and is also the correct cheapest-capable tier (hard rule 15).
SEARCH_CONFIG = "contract-desk"

MANIFEST_PATH = ROOT / "data" / "kb-manifest.json"
MANIFEST = json.loads(MANIFEST_PATH.read_text()) if MANIFEST_PATH.exists() else {}
RID_TO_FILE = {rid: f for f, rid in MANIFEST.items()}
ALL_RIDS = list(MANIFEST.values())

NO_CONTEXT_MESSAGE = (
    "I can't find that in the contracts, rate schedules or policies I have "
    "access to for the Contract Terms Desk. It may not be covered by the "
    "current agreements, or it may sit outside this desk's scope - it's "
    "worth checking the source agreement directly or asking the account "
    "manager rather than guessing. (I never invent a rate, date or clause - "
    "if it isn't in the documents, I say so.)"
)

# --------------------------------------------------------------- UC05 - Client Handling SOPs
SOPS_MANIFEST_PATH = ROOT / "data" / "kb-manifest-sops.json"
SOPS_MANIFEST = json.loads(SOPS_MANIFEST_PATH.read_text()) if SOPS_MANIFEST_PATH.exists() else {}
SOPS_RID_TO_FILE = {rid: f for f, rid in SOPS_MANIFEST.items()}
SOPS_SEARCH_CONFIG = "client-sops-desk"

CLIENTS = {
    "harrow-retail": {"name": "Harrow Retail Group", "site": "Sydney DC"},
    "bluewater-foods": {"name": "Bluewater Foods Co-operative", "site": "Melbourne DC"},
    "anvil-construction": {"name": "Anvil Construction Supplies", "site": "Newcastle yard"},
    "coastal-pharma": {"name": "Coastal Pharma Manufacturing", "site": "Melbourne DC"},
    "ironbark-mining": {"name": "Ironbark Mining Co", "site": "Kalgoorlie site"},
}


def sops_rids_for_client(client: str) -> list[str]:
    """Hard-scope by an explicit resource-id subset (same proven pattern as
    UC01's ALL_RIDS), not by an ARAG label filter - the label filter path
    has its own documented quirks (CLAUDE.md: legacy `filters` array
    silently returns zero matches; `filter_expression`'s key name varies by
    endpoint) that aren't worth the risk on a live demo when a plain
    resource-id list already does the job reliably. A genuine Labeler DA
    task is still registered on the KB for admin-console credibility (see
    scripts/register_labeler.py) - this is a deliberate choice about which
    mechanism the APP's own retrieval calls lean on, not a workaround for a
    broken one."""
    prefix = f"sop-{client}-"
    return [rid for f, rid in SOPS_MANIFEST.items() if f.startswith(prefix)]


NO_CONTEXT_MESSAGE_SOPS = (
    "I can't find that in this client's handling SOPs, damage procedures or "
    "shift-handover notes. It may not be covered for this client, or it may "
    "sit outside this desk's scope - it's worth checking with the site shift "
    "supervisor rather than guessing or borrowing another client's rule. "
    "(I never invent a timing threshold or a figure - if it isn't in the "
    "documents, I say so.)"
)

# --------------------------------------------------------------- UC04 - Dangerous Goods
DG_MANIFEST_PATH = ROOT / "data" / "kb-manifest-dg.json"
DG_MANIFEST = json.loads(DG_MANIFEST_PATH.read_text()) if DG_MANIFEST_PATH.exists() else {}
DG_RID_TO_FILE = {rid: f for f, rid in DG_MANIFEST.items()}
DG_ALL_RIDS = list(DG_MANIFEST.values())
DG_SEARCH_CONFIG = "dangerous-goods-desk"

NO_CONTEXT_MESSAGE_DG = (
    "I can't find that in the CFG DG Code, supplier SDSs, segregation matrix "
    "or acceptance policy I have access to. It may not be covered by the "
    "current code, or it may sit outside this desk's scope - check with the "
    "site DG coordinator rather than guessing. (I never invent a class, UN "
    "number or segregation distance - if it isn't in the documents, I say "
    "so.)"
)


async def ask_dg(query: str) -> dict:
    """UC04 Dangerous Goods - hard-scoped to the CFG DG Code corpus."""
    return await _ask(query, DG_SEARCH_CONFIG, DG_ALL_RIDS, NO_CONTEXT_MESSAGE_DG, top_k=12)


# --------------------------------------------------------------- UC02 - Rate Integrity
# App-orchestrated fusion, BY DESIGN (reframed 4 Sep 2026 - see the README's
# "Rate Integrity mechanism" note for why). This desk does not attempt, and
# does not depend on, an ARAG Retrieval Agent (RAO) session - arag_agent.py
# documents a real platform bug found exploring that path, but it is
# unused/unimported dead code now, not a fallback this desk falls back to.
# Every step below is a genuine ARAG /ask call - real retrieval + real
# generation on the platform - orchestrated by this app's own code, which
# is the intended, standing mechanism for this desk, not a workaround for
# anything broken.

RATE_RECONCILE_SCHEMA = {
    "name": "rate_reconciliation",
    "description": "Reconciles billed freight rates against the contracted rate schedule",
    "parameters": {
        "type": "object",
        "properties": {
            "findings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "invoice_no": {"type": "string"},
                        "lane": {"type": "string"},
                        "contracted_base_rate": {"type": "number",
                            "description": "The contracted base rate for this lane, in AUD, from the retrieved rate schedule."},
                        "billed_base_rate": {"type": "number"},
                        "variance_aud": {"type": "number",
                            "description": "billed_base_rate minus contracted_base_rate; negative means undercharge."},
                        "is_undercharge": {"type": "boolean"},
                    },
                    "required": ["invoice_no", "lane", "contracted_base_rate",
                                "billed_base_rate", "variance_aud", "is_undercharge"],
                },
            },
            "summary": {"type": "string",
                       "description": "One or two plain-English sentences summarising the findings."},
        },
        "required": ["findings", "summary"],
    },
}


def contract_rids_for_customer(customer: str) -> list[str]:
    prefix = f"contract-{customer}-"
    return [rid for f, rid in MANIFEST.items() if f.startswith(prefix)]


async def reconcile_customer(customer: str, customer_name: str, invoices: list[dict]) -> dict:
    """UC02's core step: given the customer's actually-billed invoices (app
    data), ask ARAG to retrieve the contracted rate schedule and produce a
    structured reconciliation - genuine retrieval + reasoning on the
    platform, via answer_json_schema. A second, parallel plain-text /ask
    call (citations, no schema - the two can never combine in one call)
    supplies the citation cards, so every number ison"t just structured
    output but traceable to the actual contract clause."""
    rids = contract_rids_for_customer(customer)
    if not rids or not invoices:
        return {"grounded": False, "findings": [], "summary": None, "citations": [], "contexts": []}

    lines = "; ".join(
        f"{i['invoice_no']} on lane {i['lane']} billed a base rate of ${i['base_rate_billed']:.2f}"
        for i in invoices)
    question_schema = (
        f"Here are the base rates actually billed to {customer_name} on recent invoices: "
        f"{lines}. For EACH invoice, find the CONTRACTED base rate for that exact lane from "
        f"the rate schedule, compute the variance (billed minus contracted), and state whether "
        f"it is an undercharge (billed is less than contracted).")

    payload_schema = {
        "query": question_schema[:1900],
        "search_configuration": SEARCH_CONFIG,
        "answer_json_schema": RATE_RECONCILE_SCHEMA,
        "citations": False,  # never combine with answer_json_schema - platform crash
        "top_k": 15,
        "resource_filters": rids,
        "generative_model": MODEL,
    }
    async with httpx.AsyncClient(timeout=90) as cx:
        r = await cx.post(f"{HOST}/api/v1/kb/{KB}/ask",
                          headers={**HDRS, "X-Synchronous": "true", "Content-Type": "application/json"},
                          json=payload_schema)
    if r.status_code != 200:
        raise RuntimeError(f"reconcile ask failed ({r.status_code}): {r.text[:300]}")
    d = r.json()
    answer_json = d.get("answer_json") or {}
    findings = answer_json.get("findings") or []
    summary = answer_json.get("summary")
    # gotcha 4 in the arag-kb skill: retrieval_results IS populated even
    # with citations:false - pull the schema call's OWN contexts for REMi,
    # not a separate call's, so groundedness is scored against the actual
    # paragraphs that produced this answer (a real B31 instability found
    # live: scoring against a different call's contexts swung groundedness
    # 4 then 2 on the same correct answer).
    _, schema_contexts = parse_citations(d.get("retrieval_results") or {})

    # Parallel citations-only call - same scope, plain-text question - for
    # the "cited to the contract clause" requirement (gotcha 4 again:
    # citations + schema can never share one call).
    cite_result = await _ask(
        f"What is the contracted base rate and fuel surcharge schedule for {customer_name}?",
        SEARCH_CONFIG, rids, NO_CONTEXT_MESSAGE, top_k=10)

    return {
        "grounded": bool(findings),
        "findings": findings,
        "summary": summary,
        "citations": cite_result["citations"],
        "contexts": schema_contexts or cite_result["contexts"],
        "remi_question": question_schema,  # score REMi against the question that actually
                                            # produced this answer, not the user's free-text
                                            # query - keeps question/answer/context aligned
                                            # (a REMi B31 stability fix, same lesson as the
                                            # full-context-not-thin-excerpts one).
    }


# --------------------------------------------------------------- UC03 - Dispute Evidence Pack
DISPUTE_MANIFEST_PATH = ROOT / "data" / "kb-manifest-dispute.json"
DISPUTE_MANIFEST = json.loads(DISPUTE_MANIFEST_PATH.read_text()) if DISPUTE_MANIFEST_PATH.exists() else {}
DISPUTE_RID_TO_FILE = {rid: f for f, rid in DISPUTE_MANIFEST.items()}
DISPUTE_ALL_RIDS = list(DISPUTE_MANIFEST.values())
DISPUTE_SEARCH_CONFIG = "dispute-evidence-desk"

NO_CONTEXT_MESSAGE_DISPUTE = (
    "I can't find that in the evidence documents or contract clause I have "
    "access to for this dispute. It may not be covered by what's been "
    "gathered so far - check with the ops team investigating this case "
    "rather than guessing. (I never invent a delivery detail, date or "
    "figure - if it isn't in the documents, I say so.)"
)


async def ask_dispute(query: str, customer: str = "coastal-pharma") -> dict:
    """UC03 Dispute Evidence Pack - hard-scoped to the evidence documents
    (POD scan, docket, email thread, remittance advice, ops notes) PLUS
    that customer's own contract clauses, so the assembled answer can cite
    the contracted liability/chain-of-custody condition alongside the
    delivery evidence - three real sources in one genuine ARAG call."""
    rids = DISPUTE_ALL_RIDS + contract_rids_for_customer(customer)
    return await _ask(query, DISPUTE_SEARCH_CONFIG, rids, NO_CONTEXT_MESSAGE_DISPUTE, top_k=12)


async def dg_graph_sample(limit: int = 12) -> list[dict]:
    """A handful of real extracted UN number -> class -> segregation-group
    relations from the registered llm-graph DA task, for the 'watch the
    graph' panel - genuine extracted data, never hand-authored. Returns []
    on any failure (the graph task may still be running) rather than
    fabricating relations."""
    try:
        async with httpx.AsyncClient(timeout=30) as cx:
            r = await cx.post(f"{HOST}/api/v1/kb/{KB}/graph", headers=HDRS,
                              json={"query": {"prop": "path"}, "top_k": 200})
        if r.status_code != 200:
            return []
        d = r.json()
        out = []
        for path in d.get("paths") or []:
            src_node, dst_node = path.get("source") or {}, path.get("destination") or {}
            # keep entity-to-entity relations only - a resource-to-entity
            # relation (default NER on ingest) isn't the UN-number/class
            # graph the registered task is building, and its "source" is a
            # raw resource id, not a readable label.
            if src_node.get("type") != "entity" or dst_node.get("type") != "entity":
                continue
            # hard-scope to THIS demo's own DG resources (arag-kb gotcha 2 -
            # a shared KB can hold several demos' content, and the graph
            # endpoint has no resource_filters param the way /ask does) -
            # a graph path carries its source resource in metadata.field_id.
            field_id = (path.get("metadata") or {}).get("field_id") or ""
            if not any(field_id.startswith(rid) for rid in DG_ALL_RIDS):
                continue
            src, dst = src_node.get("value", ""), dst_node.get("value", "")
            rel = (path.get("relation") or {}).get("label", "")
            if src and dst:
                out.append({"source": src, "relation": rel, "destination": dst})
            if len(out) >= limit:
                break
        return out
    except Exception:
        return []


def clean(text: str) -> str:
    return re.sub(r"\s*—\s*", " - ", text or "")


# ------------------------------------------------------------ B33 - inline citation markers
# Deterministic, server-side [[n]] token placement at the sentence a
# citation's own retrieved text best overlaps - never asks the model to
# place markers (it invents positions, see the arag-demo-app skill's B33
# trap notes). n is the citation's 1-based position in the (already
# relevance-sorted) citations list, matching the numbered source panel the
# client renders below the answer. The client swaps [[n]] for a clickable
# <sup> AFTER markdown rendering, so the renderer's own escaping never eats
# the token (same proven pattern as the cinema-group elevation).

_ABBR_WORDS = {"mr", "mrs", "ms", "dr", "st", "vs", "etc", "bros", "no",
               "approx", "jr", "sr", "inc", "ltd", "co"}


def split_sentences(text: str) -> list[str]:
    """Sentence-boundary split for marker placement. Skips a period
    preceded by a known abbreviation or a single capital initial (so
    "Bros. Movie World"-style names don't fracture mid-name), and matches
    CJK sentence enders bare since they carry no following whitespace."""
    if not text:
        return []
    out, start, i, n = [], 0, 0, len(text)
    while i < n:
        ch = text[i]
        is_cjk_end = ch in "。！？"
        is_latin_end = ch in ".!?" and (i + 1 == n or text[i + 1].isspace())
        if is_cjk_end or is_latin_end:
            if is_latin_end and ch == ".":
                j = i - 1
                while j >= start and text[j].isalnum():
                    j -= 1
                word = text[j + 1:i].lower()
                if word in _ABBR_WORDS or len(word) == 1:
                    i += 1
                    continue
            out.append(text[start:i + 1])
            i += 1
            while i < n and text[i].isspace():
                i += 1
            start = i
            continue
        i += 1
    if start < n:
        out.append(text[start:])
    return [s for s in out if s.strip()]


_WORD_RE = re.compile(r"[a-zA-Z]{5,}")


def _keywords(s: str) -> set[str]:
    return {w.lower() for w in _WORD_RE.findall(s)}


def inject_citation_markers(answer: str, citations: list[dict]) -> str:
    """Places one [[n]] token at the end of the sentence whose content best
    overlaps a citation's own title+snippet (keyword-overlap match, no LLM
    call, fully deterministic). A citation that overlaps no sentence keeps
    its numbered source card but gets no inline marker - honest, since
    forcing a marker onto an unrelated sentence would be worse than none."""
    sentences = split_sentences(answer)
    if not sentences or not citations:
        return answer
    sent_kw = [_keywords(s) for s in sentences]
    used = [0] * len(sentences)
    markers = [""] * len(sentences)
    for idx, c in enumerate(citations):
        n = idx + 1
        c_kw = _keywords(f"{c.get('title', '')} {c.get('snippet', '')}")
        if not c_kw:
            continue
        best_i, best_score = -1, 0
        for i, kw in enumerate(sent_kw):
            if used[i] >= 2:
                continue
            overlap = len(kw & c_kw)
            if overlap > best_score:
                best_score, best_i = overlap, i
        if best_i >= 0 and best_score > 0:
            used[best_i] += 1
            markers[best_i] += f"[[{n}]]"
    return " ".join((s.rstrip() + m) for s, m in zip(sentences, markers))


# ------------------------------------------------------------ B34/B39 - qualitative trust label
def remi_qualitative_label(remi: dict | None) -> str | None:
    """Derives the default-visible qualitative confidence label from the
    real REMi scores - never a raw numeral on the customer-facing surface
    (B34). The raw per-dimension scores still travel in the API response
    for the "how this works" reveal / console-minded reviewer; the badge is
    what a buyer sees by default."""
    if not remi:
        return None
    vals = [v for v in (remi.get("answer_relevance"), remi.get("context_relevance"),
                        remi.get("groundedness")) if isinstance(v, (int, float))]
    if not vals:
        return None
    avg = sum(vals) / len(vals)
    if avg >= 4.0:
        return "High confidence"
    if avg >= 2.75:
        return "Moderate confidence"
    return "Limited confidence"


def normalize_extracted(text: str) -> str:
    """Nuclia's extracted-text field flattens a markdown source document's
    real line breaks into whitespace runs (found live provisioning this KB,
    20 Aug 2026 - a genuinely new platform lesson, not in CLAUDE.md yet):
    a blank-line paragraph break in the uploaded .md source comes back as a
    run of ~4-5 spaces, a single line break (e.g. between adjacent table
    rows) as a run of ~2-3 spaces, real newlines mixed in unpredictably.
    Rendered as-is, headers (## ...) and table rows never land on their own
    line, so a naive line-based markdown-lite renderer silently shows raw
    '##'/'|' syntax on screen (table-stakes gate 8) and any downstream
    citation-highlight matching keyed on line position breaks too. Fix:
    fold any run of whitespace (real newlines included) back into either a
    paragraph break or a line break, keyed on run length - reliable against
    this platform's actual flattening behaviour, verified against live
    extracted text from this KB.

    The corpus's own synthetic-content disclosure footer names "the
    Progress Agentic RAG demo" directly - left as-is (3 Sep 2026 rebuild):
    this is now a GENERIC Progress Agentic RAG-branded demo (Standard B2
    case 2), not the account-specific "OpenEdge AI Extension" framing an
    earlier GM directive set for a since-superseded named-account read of
    this build - see the README for the supersession note. Nothing to
    rewrite here any more; kept as a no-op wrapper (not deleted) so the
    call sites below don't need touching."""
    if not text:
        return text
    text = re.sub(r"[ \t]*\n[ \t]*", "   ", text)
    text = re.sub(r" {4,}", "\n\n", text)
    text = re.sub(r" {2,3}", "\n", text)
    return text.strip()


def parse_citations(retrieval: dict) -> tuple[list[dict], list[str]]:
    """Returns (citation cards for the UI, full paragraph texts for REMi).

    Excludes any field id prefixed "/t/da-" - a real, user-visible defect
    found registering the Portfolio DA task (21 Aug 2026): once a resource
    carries DA-generated text fields (contract-plain-summary,
    portfolio-structured-fields), ARAG's own retrieval indexes and can
    return THEM as citation hits too, including the raw JSON blob showing
    up as a "contract clause" citation card - a genuine credibility defect
    (gate 8), not a hypothetical one; caught live testing the fusion hero.
    A DA-generated derived field is never the authoritative source text -
    the original uploaded file (/f/...) always is - so it's excluded from
    what's ever shown to a user as "the source", even though it's a real,
    intentional, still-searchable part of the KB."""
    out = []
    for rid, res in (retrieval or {}).get("resources", {}).items():
        title = res.get("title") or rid
        for fid, field in (res.get("fields") or {}).items():
            if fid.startswith("/t/da-"):
                continue
            for pid, para in (field.get("paragraphs") or {}).items():
                raw = para.get("text") or ""
                if not raw.strip():
                    continue
                # Same flattened-whitespace fix as normalize_extracted, but
                # collapsed back to a single readable line for the compact
                # source-card snippet (never raw '##'/'|' on screen - gate 8).
                # Strip markdown/table syntax throughout, not just at the
                # start - a snippet can span a heading or a table row
                # anywhere in its 400 chars, not only at position 0.
                text = re.sub(r"\s*\n\s*", " ", normalize_extracted(raw)).strip()
                text = re.sub(r"#{1,6}\s*", "", text)
                text = re.sub(r"\s*\|\s*", " - ", text).strip(" -")
                text = re.sub(r"(-\s*){3,}", "", text)  # a bare |---|---| separator row
                text = re.sub(r"\s{2,}", " ", text).strip()
                out.append({
                    "rid": rid,
                    "file": RID_TO_FILE.get(rid, title),
                    "title": title,
                    "score": para.get("score"),
                    "snippet": text[:400],
                    "_text": raw.strip(),
                })
    out.sort(key=lambda c: -(c["score"] or 0))
    out = out[:10]
    texts = [c.pop("_text") for c in out]
    seen, dedup = set(), []
    for c in out:
        key = (c["rid"], c["snippet"][:60])
        if key not in seen:
            seen.add(key)
            dedup.append(c)
    return dedup[:8], [t for t in texts if t.strip()][:8]


async def _ask(query: str, search_config: str, resource_filters: list[str],
               no_context_message: str, top_k: int = 15) -> dict:
    """Shared query-time /ask call - every use case hard-scopes to its own
    resource-id subset and references its own saved search configuration
    (honest-decline system prompt lives there, not here). Never send
    citations + answer_json_schema together (platform crash) - this call
    only ever uses citations, no schema."""
    payload = {
        "query": query[:1900],
        "search_configuration": search_config,
        "citations": True,
        "citation_threshold": 0.3,
        "top_k": top_k,
        "resource_filters": resource_filters,
        "generative_model": MODEL,
    }
    t0 = time.monotonic()
    async with httpx.AsyncClient(timeout=90) as cx:
        r = await cx.post(f"{HOST}/api/v1/kb/{KB}/ask",
                          headers={**HDRS, "X-Synchronous": "true",
                                   "Content-Type": "application/json"},
                          json=payload)
    if r.status_code != 200:
        raise RuntimeError(f"ask failed ({r.status_code}): {r.text[:300]}")
    d = r.json()
    latency_ms = int((time.monotonic() - t0) * 1000)

    status = d.get("status")
    retrieval = d.get("retrieval_results") or {}
    citations, contexts = parse_citations(retrieval)
    no_context = status == "no_context" or (not citations and not (d.get("answer") or "").strip())

    answer_text = no_context_message if no_context else clean(d.get("answer") or "")
    if not no_context and citations:
        for i, c in enumerate(citations):
            c["n"] = i + 1
        answer_text = inject_citation_markers(answer_text, citations)

    return {
        "answer": answer_text,
        "grounded": not no_context,
        "no_context_is_app_worded": no_context,  # disclosed workaround flag - see docstring
        "citations": [] if no_context else citations,
        "contexts": contexts,  # full retrieved paragraph set, for REMi scoring
        "status": status,
        "latency_ms": latency_ms,
    }


async def ask(query: str) -> dict:
    """UC01 Contract Terms Desk - hard-scoped to this KB's own contract
    resources."""
    return await _ask(query, SEARCH_CONFIG, ALL_RIDS, NO_CONTEXT_MESSAGE, top_k=15)


async def ask_sops(client: str, query: str) -> dict:
    """UC05 Client Handling SOPs - hard-scoped to ONE client's own SOP
    documents, never another client's, regardless of how similar a
    question sounds across clients."""
    rids = sops_rids_for_client(client)
    if not rids:
        return {"answer": NO_CONTEXT_MESSAGE_SOPS, "grounded": False,
                "no_context_is_app_worded": True, "citations": [], "contexts": [],
                "status": "unknown_client", "latency_ms": 0}
    return await _ask(query, SOPS_SEARCH_CONFIG, rids, NO_CONTEXT_MESSAGE_SOPS, top_k=10)


async def remi(question: str, answer: str, contexts: list[str]) -> dict | None:
    """Score REMi against the FULL retrieved context block (not thin cited
    excerpts) via the KB service-account token, per the working rwa-intel-demo
    pattern. Returns None (never a fabricated score) if the call fails or
    there's no grounded answer to score."""
    # Cap raised from 8 -> 12 (21 Aug 2026, fusion-hero trust-score fix): the
    # Rate Integrity fusion answer now adds live-billing context items on
    # top of the KB-retrieved paragraphs (see app.py's api_ask_rate_integrity),
    # and a customer with several invoices plus a full contract set could
    # exceed 8 real, relevant context items - truncating at 8 risked
    # silently dropping the billing context that makes the fused claim
    # score correctly, which would have reintroduced the exact bug this
    # fix exists for.
    ctxs = [c for c in (contexts or []) if c and c.strip()][:12]
    if not ctxs or not answer.strip():
        return None
    payload = {
        "user_id": "cartwright-freight-demo",
        "question": question,
        "answer": answer,
        "contexts": ["\n\n".join(ctxs)],
    }
    try:
        async with httpx.AsyncClient(timeout=60) as cx:
            r = await cx.post(f"{HOST}/api/v1/kb/{KB}/predict/remi",
                              headers=HDRS, json=payload)
        if r.status_code != 200:
            return None
        d = r.json()
    except Exception:
        return None
    ar = (d.get("answer_relevance") or {})
    ctx_scores = d.get("context_relevance") or []
    gnd_scores = d.get("groundedness") or []
    return {
        "answer_relevance": ar.get("score"),
        "context_relevance": max(ctx_scores) if ctx_scores else None,
        "groundedness": max(gnd_scores) if gnd_scores else None,
    }


async def resource_detail(rid: str) -> dict | None:
    """Full extracted text of one contract document, for the source viewer
    (citations navigate here and highlight the cited passage)."""
    async with httpx.AsyncClient(timeout=30) as cx:
        r = await cx.get(f"{HOST}/api/v1/kb/{KB}/resource/{rid}",
                         params={"show": ["basic", "extracted"], "extracted": ["text"]},
                         headers=HDRS)
    if r.status_code != 200:
        return None
    d = r.json()
    file_ = (RID_TO_FILE.get(rid) or SOPS_RID_TO_FILE.get(rid)
             or DG_RID_TO_FILE.get(rid) or DISPUTE_RID_TO_FILE.get(rid, rid))
    title = d.get("title") or file_
    # The primary uploaded document body always lives under data.files (the
    # source .md/.png). DA-generated output (contract-plain-summary,
    # portfolio-structured-fields) lands as ADDITIONAL data.texts fields
    # keyed "da-<destination>-f-<fieldId>" (arag-kb skill gotcha 8) - once
    # those exist on a resource, an unqualified scan of data.texts picks
    # one of them up instead of the real document (found live registering
    # the Portfolio DA task, 21 Aug 2026 - a citation would have opened
    # showing a summary/JSON blob instead of the actual contract). Always
    # prefer data.files; only fall back to a NON-"da-"-prefixed texts field
    # (a resource with no file upload at all) if files has nothing.
    text = ""
    for field in (d.get("data", {}).get("files") or {}).values():
        extracted = (field.get("extracted") or {}).get("text") or {}
        text = extracted.get("text") or text
    if not text:
        for key, field in (d.get("data", {}).get("texts") or {}).items():
            if key.startswith("da-"):
                continue
            extracted = (field.get("extracted") or {}).get("text") or {}
            text = extracted.get("text") or text
    return {"rid": rid, "title": title, "file": file_,
            "text": normalize_extracted(text)}


# --------------------------------------------------------------- Portfolio dashboard
# Reads the "portfolio-structured-fields" DA task's genuine output (a
# constrained plain-text ask, not the confirmed-broken json:true Generator
# path - see scripts/register_portfolio_da.py's docstring) off each MTSA
# contract resource, and fuses it with the app's own real synthetic billing
# data. Two distinct genuine sources, shown as two distinct things - never
# blended into one number that looks like it all came from one place.

_PORTFOLIO_INT_FIELDS = {"term_months", "liability_cap_aud", "lane_count"}
_PORTFOLIO_KEYS = {"customer", "term_months", "liability_cap_aud", "fsc_basis",
                   "renewal_date", "lane_count"}


def _parse_portfolio_json(raw: str) -> dict | None:
    """The ask-type DA task is prompted for a bare JSON object, but its
    plain-text output pipeline strips literal double-quote characters
    (verified live, 21 Aug 2026 - the stored text comes back as
    `customer : Anvil Construction Supplies Pty Ltd ,` with the colons and
    commas intact but every `"` gone, since the field is stored as
    `format: PLAIN`) - so json.loads() always fails on it, not a model
    formatting slip. Rather than fight the pipeline for real JSON on a
    plain-text-only mechanism, this parses the ACTUAL consistent line-based
    shape the platform produces: one `key : value` pair per line, matched
    against the fixed field list this prompt asks for (never an open-ended
    key set - a genuinely unrecognised key is dropped, not guessed at).
    Returns None if the field is missing or nothing recognisable parses."""
    if not raw:
        return None
    t = raw.strip().strip("{}")
    out = {}
    for line in t.splitlines():
        line = line.strip().rstrip(",").strip()
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key, value = key.strip(), value.strip().rstrip(",").strip()
        if key not in _PORTFOLIO_KEYS:
            continue
        if value.lower() == "null" or not value:
            out[key] = None
        elif key in _PORTFOLIO_INT_FIELDS:
            m = re.match(r"-?\d+", value)
            out[key] = int(m.group()) if m else None
        else:
            out[key] = value
    return out or None


# --------------------------------------------------------------- Resource catalog + source connections
# ALL_FILE_MAP spans every manifest (contracts, SOPs, DG, dispute) - one
# lookup for the catalog page, which browses the whole KB, not one desk's
# scoped slice.
ALL_FILE_MAP = {**RID_TO_FILE, **SOPS_RID_TO_FILE, **DG_RID_TO_FILE, **DISPUTE_RID_TO_FILE}


def _filename_document_type(fname: str) -> str | None:
    """Deterministic document-type from the filename, in the SAME category
    taxonomy the real 'document-type' Labeler task's labelset defines.

    Why not read the Labeler task's own paragraph classifications here (the
    way client/site labels are read below)? Checked live, 21 Aug 2026:
    document-type came back genuinely wrong at the RESOURCE level - only
    1 of 5 real MTSA contracts landed on 'mtsa' after majority-voting each
    resource's own paragraph classifications, because an MTSA's later
    clauses (fuel surcharge, liability) legitimately discuss rate/policy
    topics and can out-vote the document's own overall type. That's an
    honest, expected limitation of PARAGRAPH-level classification applied
    to a RESOURCE-level fact (see arag.py's contract_lifecycle_labels
    docstring for the same noise pattern, there tolerated because a
    2-vote MTSA rarely ties) - not something to silently paper over on a
    page a reviewer will visually audit. The filename encodes the exact
    same real fact deterministically (this demo's own corpus generator
    names files by genuine content type), so it's used for the catalog
    display instead; the registered Labeler task itself is unchanged and
    still real, running, and visible in the admin console - only THIS
    page's badge source differs, and its reveal says so precisely."""
    if fname.endswith("-mtsa.md"):
        return "mtsa"
    if fname.endswith("-rate-schedule.md"):
        return "rate-schedule"
    if fname.endswith("-accessorials.md"):
        return "accessorials"
    if "-side-letter-" in fname:
        return "side-letter"
    if fname.startswith("policy-"):
        return "policy"
    if fname.endswith("-handling.md"):
        return "sop-handling"
    if fname.endswith("-damage-handover.md"):
        return "sop-damage-handover"
    if fname.startswith("dg-code-"):
        return "dg-code"
    if fname.startswith("dg-acceptance-policy"):
        return "dg-policy"
    if fname.startswith("sds-"):
        return "sds"
    if fname.startswith("segregation-matrix"):
        return "segregation-matrix"
    if any(fname.startswith(p) for p in ("docket-", "email-thread-", "ops-notes-",
                                          "remittance-advice-", "pod-")):
        return "dispute-evidence"
    return None


async def _resource_client_label(cx: httpx.AsyncClient, rid: str) -> str | None:
    """Majority-vote 'client' label for one resource - the real paragraph-
    classification read (same pattern as contract_lifecycle_labels()).
    Verified live, 21 Aug 2026: client labels check out 100% against
    ground truth (every resource's real customer, by filename) across all
    44 resources - unlike document-type (see _filename_document_type),
    this one is reliable to surface directly from the Labeler task."""
    r = await cx.get(f"{HOST}/api/v1/kb/{KB}/resource/{rid}",
                     params={"show": ["basic", "extracted"], "extracted": ["metadata"]},
                     headers=HDRS)
    if r.status_code != 200:
        return None
    files = (r.json().get("data", {}) or {}).get("files") or {}
    votes: Counter = Counter()
    for fdata in files.values():
        meta = ((fdata.get("extracted") or {}).get("metadata") or {}).get("metadata") or {}
        for para in meta.get("paragraphs") or []:
            for c in para.get("classifications") or []:
                if c.get("labelset") == "client" and c.get("label"):
                    votes[c["label"]] += 1
    return votes.most_common(1)[0][0] if votes else None


async def catalog_resources() -> list[dict]:
    """The real ARAG /catalog listing for the whole KB (44 resources, one
    page - confirmed live it fits in a single page_size=60 call, no
    pagination needed today), fused with per-resource labels: 'client' from
    the real Labeler task (verified accurate, see _resource_client_label),
    'document_type' from the filename (verified MORE accurate than the
    Labeler task's own paragraph-level vote for this resource-level fact,
    see _filename_document_type). This is the actual admin-console catalog
    listing, not a client-side re-derivation of it - a seller can open the
    real console afterward and see the identical resource set."""
    async with httpx.AsyncClient(timeout=30) as cx:
        r = await cx.get(f"{HOST}/api/v1/kb/{KB}/catalog",
                         params={"query": "", "page_size": 60, "show": ["basic"]}, headers=HDRS)
        if r.status_code != 200:
            return []
        resources = (r.json() or {}).get("resources") or {}

        rids = list(resources.keys())
        clients = await asyncio.gather(*(_resource_client_label(cx, rid) for rid in rids))

    out = []
    for rid, client in zip(rids, clients):
        res = resources[rid]
        fname = ALL_FILE_MAP.get(rid, res.get("title", rid))
        out.append({
            "rid": rid,
            "file": fname,
            "title": res.get("title", rid),
            "icon": res.get("icon", ""),
            "status": (res.get("metadata") or {}).get("status", ""),
            "document_type": _filename_document_type(fname),
            "client": client,
        })
    out.sort(key=lambda r: (r["document_type"] or "zzz", r["file"]))
    return out


async def contract_lifecycle_labels() -> dict[str, str]:
    """Reads the REAL "lifecycle" Labeler DA task output (paragraph-level
    classifications under data.files.{fieldId}.extracted.metadata.metadata.
    paragraphs[].classifications - a different storage location again from
    the plain-text ask output above) for each MTSA resource, and returns a
    {rid: label} map using the MAJORITY label across that resource's
    classified paragraphs. Majority vote, not "first paragraph", because
    paragraph-level classification is genuinely noisy in practice - e.g. a
    paragraph inside an MTSA that happens to discuss rate mechanics can get
    classified "rate-schedule" for the unrelated "document-type" labelset,
    even though the whole file is an MTSA (observed live on this KB, 21 Aug
    2026). A single stray paragraph should not flip the whole contract's
    displayed status; the majority is a fair, still-genuine read of what
    the DA task actually produced. Returns {} entries only for resources
    where the classification is genuinely absent, never a guessed default."""
    out = {}
    async with httpx.AsyncClient(timeout=30) as cx:
        for fname, rid in MANIFEST.items():
            if not fname.endswith("-mtsa.md"):
                continue
            r = await cx.get(f"{HOST}/api/v1/kb/{KB}/resource/{rid}",
                             params={"show": ["basic", "extracted"], "extracted": ["metadata"]},
                             headers=HDRS)
            if r.status_code != 200:
                continue
            files = (r.json().get("data", {}) or {}).get("files") or {}
            votes = Counter()
            for fdata in files.values():
                meta = ((fdata.get("extracted") or {}).get("metadata") or {}).get("metadata") or {}
                for para in meta.get("paragraphs") or []:
                    for c in para.get("classifications") or []:
                        if c.get("labelset") == "lifecycle" and c.get("label"):
                            votes[c["label"]] += 1
            if votes:
                out[rid] = votes.most_common(1)[0][0]
    return out


def _count_lane_rows(rate_schedule_text: str) -> int | None:
    """Counts real lane rows in a rate-schedule's own markdown table
    (header + separator rows excluded) - deterministic and 100% grounded,
    used in place of the DA task's own attempt at this field. Returns None
    if no table is found, never a guessed number."""
    if not rate_schedule_text:
        return None
    rows = [ln for ln in rate_schedule_text.splitlines() if ln.strip().startswith("|")]
    rows = [r for r in rows if not re.match(r"^\s*\|?[\s:|-]+\|?\s*$", r)]  # drop separator rows
    return max(0, len(rows) - 1) if rows else None  # -1 for the header row


async def contract_portfolio_fields() -> list[dict]:
    """One real ARAG Data Augmentation task (portfolio-structured-fields)
    extracted per-contract fields at ingest time - this function reads what's
    already stored on each MTSA resource (data.texts, keyed
    "da-portfolio_fields-f-<fieldId>"), it makes no live /ask call for those
    fields. A contract whose DA output is missing or unparsed is skipped,
    not padded with an invented row.

    lane_count is the one exception: the DA task is scoped to a single
    resource, so it genuinely cannot see the rate-schedule document (a
    SEPARATE resource from the MTSA it runs on) and correctly returned null
    for every contract rather than guessing (verified live, 21 Aug 2026) -
    a real, honest limitation of per-resource DA tasks, not a bug to route
    around with a bigger prompt. Rather than claim a DA extraction that
    isn't actually happening, lane_count is counted deterministically from
    the real rate-schedule table (_count_lane_rows) - still 100% grounded,
    just via table counting instead of LLM inference, and arguably more
    reliable for a bare count than an LLM guess would have been."""
    out = []
    async with httpx.AsyncClient(timeout=30) as cx:
        for fname, rid in MANIFEST.items():
            if not fname.endswith("-mtsa.md"):
                continue
            r = await cx.get(f"{HOST}/api/v1/kb/{KB}/resource/{rid}",
                             params={"show": ["basic", "values", "extracted"], "extracted": ["text"]},
                             headers=HDRS)
            if r.status_code != 200:
                continue
            texts = (r.json().get("data", {}) or {}).get("texts") or {}
            raw = None
            for key, field in texts.items():
                if key.startswith("da-portfolio_fields-"):
                    raw = ((field.get("extracted") or {}).get("text") or {}).get("text")
                    break
            fields = _parse_portfolio_json(raw)
            if not fields:
                continue
            fields["rid"] = rid
            fields["file"] = fname

            rs_fname = fname.replace("-mtsa.md", "-rate-schedule.md")
            rs_rid = MANIFEST.get(rs_fname)
            if rs_rid:
                rs = await cx.get(f"{HOST}/api/v1/kb/{KB}/resource/{rs_rid}",
                                  params={"show": ["basic", "extracted"], "extracted": ["text"]},
                                  headers=HDRS)
                if rs.status_code == 200:
                    rs_text = ""
                    for field in (rs.json().get("data", {}) or {}).get("files", {}).values():
                        rs_text = ((field.get("extracted") or {}).get("text") or {}).get("text") or rs_text
                    fields["lane_count"] = _count_lane_rows(normalize_extracted(rs_text))
            out.append(fields)
    return out
