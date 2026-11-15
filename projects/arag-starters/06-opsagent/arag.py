"""Server-side Progress Agentic RAG client.

The service-account token never leaves this process - the browser only ever
talks to this application's own API.
"""
from __future__ import annotations

import os
import re
from typing import Any

import httpx

HOST = os.environ["ARAG_HOST"].rstrip("/")
KB_ID = os.environ["KB_ID"]
TOKEN = os.environ["KB_TOKEN"]
# Hard rule 15 - cheapest capable tier, pinned explicitly on every call so a
# platform default can never silently promote us to a premium model.
MODEL = os.environ.get("ARAG_MODEL", "gemini-3.1-flash-lite")

KB = f"{HOST}/kb/{KB_ID}"
_H = {
    "X-NUCLIA-SERVICEACCOUNT": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
    # Nuclia streams NDJSON even when JSON is requested unless this is set.
    "X-Synchronous": "true",
}

_client = httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=20.0))


class UpstreamError(RuntimeError):
    """Raised when the retrieval service cannot be reached or fails."""


async def _post(path: str, payload: dict) -> dict:
    try:
        r = await _client.post(f"{KB}{path}", headers=_H, json=payload)
    except httpx.HTTPError as exc:  # network / timeout
        raise UpstreamError("The knowledge service did not respond in time.") from exc
    if r.status_code >= 400:
        raise UpstreamError(f"The knowledge service returned an error ({r.status_code}).")
    try:
        return r.json()
    except ValueError as exc:
        raise UpstreamError("The knowledge service returned an unreadable response.") from exc


def label_filter(pairs: list[tuple[str, str]]) -> dict | None:
    """Build a filter expression from (labelset, label) pairs.

    Always a filter_expression - the legacy `filters` array can fail open.
    """
    if not pairs:
        return None
    terms = [{"prop": "label", "labelset": ls, "label": lb} for ls, lb in pairs]
    if len(terms) == 1:
        return {"field": terms[0]}
    return {"field": {"or": terms}}


# ---------------------------------------------------------------- retrieval
async def find(query: str, filt: dict | None = None, top_k: int = 12) -> dict:
    """Semantic retrieval. Returns the real matching resources."""
    payload: dict[str, Any] = {"query": query, "features": ["keyword", "semantic"], "top_k": top_k}
    if filt:
        payload["filter_expression"] = filt
    return await _post("/find", payload)


def resources_from_find(data: dict) -> list[dict]:
    out = []
    for rid, res in (data.get("resources") or {}).items():
        best_score, best_text = 0.0, ""
        for field in (res.get("fields") or {}).values():
            for para in (field.get("paragraphs") or {}).values():
                sc = para.get("score") or 0
                if sc > best_score:
                    best_score, best_text = sc, para.get("text") or ""
        out.append({
            "rid": rid,
            "title": res.get("title") or "",
            "url": ((res.get("origin") or {}).get("url")) or "",
            "score": round(best_score, 3),
            "excerpt": clean_excerpt(best_text),
        })
    out.sort(key=lambda r: -r["score"])
    return out


# The site marks trademarks with <sup>TM</sup>; stripping tags leaves a stranded
# "TM". Restoring the glyph is a display fix for a scraping artefact, not a content
# change - it puts back exactly what the published page shows.
def tidy(text: str) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    text = re.sub(r"(?<=[A-Za-z0-9])\s+TM\b", "\u2122", text)
    text = re.sub(r"(?<=[A-Za-z0-9])\s+\u00ae", "\u00ae", text)
    return text


def clean_excerpt(text: str, limit: int = 340) -> str:
    text = tidy(text)
    if len(text) > limit:
        text = text[:limit].rsplit(" ", 1)[0] + "..."
    return text


# ------------------------------------------------------------ grounded answer
async def ask(query: str, filt: dict | None = None, prompt: str | None = None,
              top_k: int = 12) -> dict:
    payload: dict[str, Any] = {
        "query": query,
        "citations": True,
        "generative_model": MODEL,
        "top_k": top_k,
        "rag_strategies": [{"name": "neighbouring_paragraphs", "before": 1, "after": 1}],
    }
    if filt:
        payload["filter_expression"] = filt
    if prompt:
        payload["prompt"] = {"user": prompt + "\n\nQuestion: {question}\n\nContext:\n{context}"}
    return await _post("/ask", payload)


async def ask_structured(query: str, schema: dict, filt: dict | None = None,
                         prompt: str | None = None, top_k: int = 14) -> dict:
    """Structured answer call.

    Never sends citations alongside a response schema - that combination crashes
    the backend. Provenance is handled by constraining the schema's source field
    to an enum of genuinely retrieved titles.
    """
    payload: dict[str, Any] = {
        "query": query,
        "citations": False,
        "generative_model": MODEL,
        "top_k": top_k,
        "answer_json_schema": schema,
    }
    if filt:
        payload["filter_expression"] = filt
    if prompt:
        payload["prompt"] = {"user": prompt + "\n\nQuestion: {question}\n\nContext:\n{context}"}
    return await _post("/ask", payload)


def contexts_from_ask(data: dict, limit: int = 8) -> list[str]:
    """The full retrieved paragraph set the answer was actually grounded on."""
    scored: list[tuple[float, str]] = []
    for res in ((data.get("retrieval_results") or {}).get("resources") or {}).values():
        for field in (res.get("fields") or {}).values():
            for para in (field.get("paragraphs") or {}).values():
                scored.append((para.get("score") or 0, para.get("text") or ""))
    scored.sort(key=lambda x: -x[0])
    return [t for _, t in scored[:limit] if t]


# ------------------------------------------------------------------- scoring
async def groundedness(question: str, answer: str, contexts: list[str]) -> int | None:
    """REMi groundedness, scored against the FULL retrieved context set."""
    if not answer or not contexts:
        return None
    try:
        data = await _post("/predict/remi", {
            "user_id": "arag-starter",
            "question": question,
            "answer": answer,
            "contexts": contexts,
        })
    except UpstreamError:
        return None
    g = data.get("groundedness")
    if isinstance(g, dict):
        g = g.get("score")
    if isinstance(g, list) and g:
        g = g[0]
    try:
        return int(round(float(g)))
    except (TypeError, ValueError):
        return None


# What the support check actually measures is whether the answer's WORDING is
# carried by the retrieved passages. Measured on this corpus: a single-claim
# explanatory answer scores 4-5, a genuinely fabricated answer scores 0, and a
# list or a multi-document summary also scores low because it restates rather
# than echoes. So the reading is shown alongside the per-statement source
# matching and the sources themselves, never as a verdict on correctness.
CONFIDENCE = [
    (5, "Closely tracks the sources", "high",
     "Every part of this answer stays close to the wording of the retrieved passages."),
    (4, "Tracks the sources", "high",
     "The answer stays close to the wording of the retrieved passages."),
    (3, "Partly tracks the sources", "medium",
     "Parts of this answer move away from the wording of the retrieved passages. Read the sources."),
    (0, "Reworded from the sources", "low",
     "The wording of this answer sits well away from the retrieved passages. That is expected for a list or a summary, and it is also what a wrong answer looks like - so read the sources below before relying on it."),
]


def confidence_badge(score: int | None) -> dict:
    """Qualitative only - a raw score is never shown to the reader."""
    if score is None:
        return {"label": "Support not scored", "tone": "unknown",
                "detail": "The support check did not return a reading for this answer. Read the sources below."}
    for threshold, label, tone, detail in CONFIDENCE:
        if score >= threshold:
            return {"label": label, "tone": tone, "detail": detail}
    return {"label": "Reworded from the sources", "tone": "low", "detail": ""}


# --------------------------------------------------- inline citation placement
_STOP = set("""a an the and or of to in for on with is are was were be been being that this these those it its as at by from
their there they we our you your not no which who what when where how can could may might will would should must more most
than then also into over under about between each other such same own only very some any all both few many much""".split())


def _terms(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9+]{3,}", (text or "").lower()) if w not in _STOP}


def place_citations(answer: str, sources: list[dict]) -> list[dict]:
    """Split the answer into sentences and attach the best-matching source to each.

    The sources themselves come from the grounded answer call; this alignment
    only decides WHERE each marker sits in the prose.
    """
    if not answer:
        return []
    src_terms = [(i, _terms(s.get("excerpt", "") + " " + s.get("title", ""))) for i, s in enumerate(sources)]
    # split on lines first so a markdown list survives as separate units, then on
    # sentence boundaries within each line
    parts: list[str] = []
    for line in answer.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        parts.extend(p for p in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'])", line) if p.strip())
    out = []
    for sent in parts:
        if not sent.strip():
            continue
        st = _terms(sent)
        best, best_overlap = None, 0.0
        for i, terms in src_terms:
            if not terms or not st:
                continue
            overlap = len(st & terms) / max(4, len(st) ** 0.5 * 2)
            if overlap > best_overlap:
                best, best_overlap = i, overlap
        out.append({"text": sent.strip(), "source": best if best_overlap >= 0.35 else None})
    return out
