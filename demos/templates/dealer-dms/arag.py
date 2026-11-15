"""Server-side ARAG client for Ignition DMS.

Every call here runs server-side only - the KB service-account token never
reaches the browser (hard rule 6). Auth: X-NUCLIA-SERVICEACCOUNT (KB writes/
reads need the KB token, never the account NUA key - see the arag-kb skill).
Cost safety (hard rule 15): every generative call pins the cheap
gemini-3.1-flash-lite tier explicitly, never inherits a premium default.
"""
import os
import re
import time

import requests

KB_HOST = os.environ["KB_HOST"]
KB_ID = os.environ["KB_ID"]
KB_TOKEN = os.environ["KB_TOKEN"]
GEN_MODEL = os.environ.get("GEN_MODEL", "gemini-3.1-flash-lite")
SEARCH_CONFIG = "ignition-ops-assistant"

HEADERS = {
    "X-NUCLIA-SERVICEACCOUNT": f"Bearer {KB_TOKEN}",
    "X-Synchronous": "true",
    "Content-Type": "application/json",
}

FIXED_NO_CONTEXT_LEAD = "Not enough data to answer this."
WARM_NO_CONTEXT_LEAD = (
    "I can't find enough in the recon, compliance and supplier records to answer "
    "that directly."
)


def _url(path):
    return f"{KB_HOST}/kb/{KB_ID}{path}"


def ask(query, filter_expression=None, extra=None, use_search_config=True, timeout=40):
    payload = {"query": query, "citations": True, "reranker": "predict"}
    if use_search_config:
        payload["search_configuration"] = SEARCH_CONFIG
    else:
        payload["generative_model"] = GEN_MODEL
        payload["features"] = ["keyword", "semantic"]
    if filter_expression:
        payload["filter_expression"] = filter_expression
    if extra:
        payload.update(extra)
    r = requests.post(_url("/ask"), headers=HEADERS, json=payload, timeout=timeout)
    r.raise_for_status()
    return r.json()


def ask_schema(query, schema, filter_expression=None, timeout=40):
    """Query-time structured JSON answer (the WORKING mechanism - never the
    broken ingest-time DA Generator task). Never combine with citations:true
    (crashes the backend) - read retrieval_results.resources for provenance
    instead."""
    payload = {
        "query": query,
        "answer_json_schema": schema,
        "generative_model": GEN_MODEL,
        "features": ["keyword", "semantic"],
        "citations": False,
    }
    if filter_expression:
        payload["filter_expression"] = filter_expression
    r = requests.post(_url("/ask"), headers=HEADERS, json=payload, timeout=timeout)
    r.raise_for_status()
    return r.json()


def find(query, filter_expression=None, page_size=20, timeout=30):
    payload = {"query": query, "features": ["keyword", "semantic"], "reranker": "predict",
               "page_size": page_size}
    if filter_expression:
        payload["filter_expression"] = filter_expression
    r = requests.post(_url("/find"), headers=HEADERS, json=payload, timeout=timeout)
    r.raise_for_status()
    return r.json()


def remi(question, answer, contexts, timeout=30):
    ctxs = [c for c in (contexts or []) if c and c.strip()][:8]
    payload = {
        "user_id": "ignition-dms",
        "question": question,
        "answer": answer,
        "contexts": ["\n\n".join(ctxs)] if ctxs else [],
    }
    r = requests.post(_url("/predict/remi"), headers=HEADERS, json=payload, timeout=timeout)
    if r.status_code != 200:
        return None
    d = r.json()
    ctx = d.get("context_relevance") or []
    gnd = d.get("groundedness") or []
    return {
        "answer_relevance": (d.get("answer_relevance") or {}).get("score"),
        "context_relevance": max(ctx) if ctx else None,
        "groundedness": max(gnd) if gnd else None,
    }


def confidence_label(remi_result):
    """Groundedness-primary weighting (B34/B39) - a genuinely grounded answer
    never reads Low just because answer_relevance is a soft secondary signal."""
    if not remi_result or remi_result.get("groundedness") is None:
        return {"label": "Trust read unavailable", "cls": "moderate"}
    g = remi_result["groundedness"]
    if g >= 4:
        return {"label": "High confidence", "cls": "high"}
    if g >= 2.5:
        return {"label": "Moderate confidence", "cls": "moderate"}
    return {"label": "Low confidence", "cls": "low"}


def get_resource(rid, timeout=20):
    """`show` must be passed as REPEATED query params, not a comma-joined
    string - `show=basic,values` 422s outright (a distinct trap from gotcha
    14's silent-empty combined form)."""
    r = requests.get(_url(f"/resource/{rid}"),
                      headers=HEADERS,
                      params=[("show", "basic"), ("show", "values")],
                      timeout=timeout)
    if r.status_code != 200:
        return None
    return r.json()


def _normalise_extracted_text(text):
    """Nuclia's plain-text extraction collapses a real markdown line/paragraph
    break into a run of 2+ spaces rather than preserving it as a newline
    (confirmed on this corpus: a heading followed immediately by its own body
    text on the same physical line, e.g. "## Inspection standard   Every
    vehicle..."). Left as spaces, a line-based markdown renderer never
    recognises the heading - raw "##" visible on screen, a B46 FAIL. Applied
    HERE, once, at the source, so every consumer (catalogue-copy generation,
    insights extraction, and B23 highlight-offset resolution) sees the SAME
    normalised text - normalising only at render time would compute highlight
    offsets against different text than what gets displayed and desync them."""
    return re.sub(r"[ \t]{2,}", "\n", text or "")


def get_resource_text(rid, timeout=20):
    """Fetch a resource's extracted text (needs show=extracted&extracted=text
    TOGETHER - show=values alone only returns the file pointer). Real shape on
    this deployment: data.files.{fieldId}.extracted.text.text."""
    r = requests.get(_url(f"/resource/{rid}"),
                      headers=HEADERS,
                      params={"show": "extracted", "extracted": "text"},
                      timeout=timeout)
    if r.status_code != 200:
        return None
    d = r.json()
    data = d.get("data", {})
    for field in (data.get("files") or {}).values():
        text = (field.get("extracted") or {}).get("text", {}).get("text")
        if text:
            return _normalise_extracted_text(text)
    for field in (data.get("texts") or {}).values():
        body = (field.get("value") or {}).get("body")
        if body:
            return _normalise_extracted_text(body)
    return None


def resolve_highlight(resource_id, excerpt):
    """Resolve a citation's excerpt into an exact (start, end) character range
    on the resource's own RAW extracted text (Standard B23) - a whitespace-
    tolerant regex search against the raw text, never a normalise-then-map-
    back scheme (which drifts once markdown/whitespace differs between the
    citation excerpt and the rendered body - see the arag-demo-app skill's
    B23 traps on FILE/markdown corpora)."""
    text = get_resource_text(resource_id) or ""
    if not excerpt or not text:
        return None
    snippet = excerpt.strip()[:200]
    words = [w for w in re.split(r"\s+", snippet) if w]
    if not words:
        return None
    pattern = r"\s+".join(re.escape(w) for w in words)
    m = re.search(pattern, text, re.IGNORECASE)
    if m:
        # NOTE: some paragraphs Nuclia chunks are just a section heading with
        # no body text of its own, so the highlight can be a short heading
        # label rather than a full sentence (found live, flagged non-
        # blocking). An attempted fix that extended the range into the next
        # paragraph was reverted: the highlight marker-splice approach can't
        # safely span a block-element boundary (heading -> paragraph) without
        # producing invalid nested <mark> HTML that renders worse than the
        # short-but-correct highlight - a real span, honestly reflecting what
        # was actually cited, beats a broken-looking longer one.
        return (m.start(), m.end())
    short = snippet[:60]
    idx = text.find(short)
    if idx >= 0:
        return (idx, idx + len(short))
    return None


DASH_RE = re.compile(r"\s*[—–]\s*")  # em dash, en dash - explicit codepoints only


def scrub_dashes(value):
    """Hard rule 2 (no em dashes) applies to MODEL OUTPUT too, not just
    hand-written copy - the generative model routinely emits them even when
    the seed prompt is clean. Scrub recursively at generation/cache-write
    time (the revolution-dms lesson: em-dash scrub ALL rendered metadata, not
    just body copy), so a 30-second reset that regenerates catalogue copy
    from a live LLM call can never reintroduce one."""
    if isinstance(value, str):
        return DASH_RE.sub(" - ", value)
    if isinstance(value, list):
        return [scrub_dashes(v) for v in value]
    if isinstance(value, dict):
        return {k: scrub_dashes(v) for k, v in value.items()}
    return value


def generate_catalog_copy(seed_text, schema_hint="document"):
    """Real ARAG call: query-time /ask + answer_json_schema, seeded with the
    item's own extracted text (or metadata for media), NEVER the broken
    ingest-time DA Generator task (gotcha 9). This is what actually powers
    every catalogue card's title/summary/highlights (Standard B10)."""
    schema = {
        "name": "catalog_copy",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "A short, specific, human-readable title"},
                "summary": {"type": "string", "description": "One or two sentence summary"},
                "highlights": {"type": "array", "items": {"type": "string"}, "description": "2-4 scannable highlight bullets"},
            },
            "required": ["title", "summary", "highlights"],
        },
    }
    payload = {
        "query": seed_text[:1200],
        "answer_json_schema": schema,
        "generative_model": GEN_MODEL,
        "citations": False,
    }
    r = requests.post(_url("/ask"), headers=HEADERS, json=payload, timeout=40)
    r.raise_for_status()
    d = r.json()
    return scrub_dashes(d.get("answer_json"))


def strip_fixed_no_context_lead(answer):
    if answer and answer.startswith(FIXED_NO_CONTEXT_LEAD):
        rest = answer[len(FIXED_NO_CONTEXT_LEAD):].strip()
        return f"{WARM_NO_CONTEXT_LEAD} {rest}".strip()
    return answer


WORD_CHAR = re.compile(r"\S")


def _snap_to_boundary(text, pos):
    """Advance pos to the next whitespace/string-end if it falls inside a word
    (B33 Trap 3 - a raw char offset can land mid-word)."""
    n = len(text)
    if pos >= n:
        return n
    if pos == 0 or text[pos - 1].isspace() or text[pos].isspace():
        return pos
    while pos < n and not text[pos].isspace():
        pos += 1
    return pos


def build_sources_and_markers(answer_text, citations, retrieval_resources):
    """Groups ARAG's raw citation char-offsets (keyed by resource) into
    numbered sources (order of first appearance) and injects [[n]] markers at
    each citation's end offset, snapped to a word boundary and grouped when
    multiple markers land at the same position (B33 traps 3/4)."""
    if not citations:
        return answer_text, []

    order = []
    order_seen = set()
    marker_positions = {}  # snapped_pos -> set(source_number)

    # sort paragraph ids by their first range start so numbering follows the
    # answer's natural reading order
    items = []
    for pid, ranges in citations.items():
        resource_id = pid.split("/f/")[0]
        for rng in ranges:
            if len(rng) == 2:
                items.append((rng[0], rng[1], resource_id))
    items.sort(key=lambda x: x[0])

    for start, end, resource_id in items:
        if resource_id not in order_seen:
            order_seen.add(resource_id)
            order.append(resource_id)
        num = order.index(resource_id) + 1
        snapped = _snap_to_boundary(answer_text, min(end, len(answer_text)))
        marker_positions.setdefault(snapped, set()).add(num)

    # build sources list, with a representative excerpt for click-through highlighting (B23)
    excerpt_by_resource = {}
    for pid in citations.keys():
        resource_id = pid.split("/f/")[0]
        if resource_id in excerpt_by_resource:
            continue
        res = (retrieval_resources or {}).get(resource_id, {})
        for field in (res.get("fields") or {}).values():
            para = (field.get("paragraphs") or {}).get(pid)
            if para and para.get("text"):
                excerpt_by_resource[resource_id] = para["text"].strip()
                break

    sources = []
    for i, rid in enumerate(order, start=1):
        res = (retrieval_resources or {}).get(rid, {})
        title = res.get("title") or "Source document"
        sources.append({
            "num": i, "resource_id": rid, "title": title,
            "excerpt": excerpt_by_resource.get(rid, ""),
        })

    # insert markers from rightmost position to leftmost so offsets don't shift
    out = answer_text
    for pos in sorted(marker_positions.keys(), reverse=True):
        nums = sorted(marker_positions[pos])
        token = "".join(f"[[{n}]]" for n in nums)
        # separate token from following word if any, single shared space (Trap 3)
        prefix = out[:pos]
        suffix = out[pos:]
        needs_lead_space = bool(prefix) and not prefix.endswith((" ", "\n"))
        needs_trail_space = bool(suffix) and not suffix.startswith((" ", "\n", ".", ",", ")"))
        ins = (" " if needs_lead_space else "") + token + (" " if needs_trail_space else "")
        out = prefix + ins + suffix

    return out, sources
