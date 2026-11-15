"""Ignition DMS - FastAPI server-side proxy.

The KB service-account token never reaches the browser (hard rule 6). Every
ARAG call (arag.py) runs here, server-side, and only the derived JSON the
frontend needs is returned. Static frontend is plain HTML + vanilla JS.
"""
import json
import os
import time
from pathlib import Path

import requests
from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).parent


def read_env(path):
    e = {}
    if not path.exists():
        return e
    for line in path.read_text().splitlines():
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, _, v = line.partition("=")
            e[k.strip()] = v.split("#")[0].strip()
    return e


for k, v in read_env(ROOT / ".env").items():
    os.environ.setdefault(k, v)

import arag  # noqa: E402

app = FastAPI(title="Ignition DMS")


def load_json(name, default=None):
    p = ROOT / name
    if not p.exists():
        return default
    return json.loads(p.read_text())


MANIFEST = load_json("corpus_manifest.json", {"stock": [], "docs": []})
MEDIA = load_json("media_manifest.json", [])
INGEST = load_json("ingest_results.json", {})
COPY_CACHE = load_json("corpus_copy_cache.json", {})
INSIGHTS = load_json("insights_cache.json", {})

STOCK_BY_NO = {s["no"]: s for s in MANIFEST["stock"]}
DOC_BY_FILE = {d["file"]: d for d in MANIFEST["docs"]}
MEDIA_BY_FILE = {m["file"]: m for m in MEDIA}


def reload_caches():
    global MANIFEST, MEDIA, INGEST, COPY_CACHE, INSIGHTS, STOCK_BY_NO, DOC_BY_FILE, MEDIA_BY_FILE
    MANIFEST = load_json("corpus_manifest.json", {"stock": [], "docs": []})
    MEDIA = load_json("media_manifest.json", [])
    INGEST = load_json("ingest_results.json", {})
    COPY_CACHE = load_json("corpus_copy_cache.json", {})
    INSIGHTS = load_json("insights_cache.json", {})
    STOCK_BY_NO = {s["no"]: s for s in MANIFEST["stock"]}
    DOC_BY_FILE = {d["file"]: d for d in MANIFEST["docs"]}
    MEDIA_BY_FILE = {m["file"]: m for m in MEDIA}


# ---------------------------------------------------------------- catalog index
def build_catalog_item(doc, rid, kind):
    copy = COPY_CACHE.get(rid, {})
    item = {
        "id": rid,
        "kind": kind,
        "title": copy.get("title") or doc.get("title"),
        "summary": copy.get("summary") or "",
        "highlights": copy.get("highlights") or [],
        "doc_type": doc.get("doc_type"),
        "site": doc.get("site"),
        "make": doc.get("make"),
        "urgency": doc.get("urgency"),
        "stock_no": doc.get("stock_no"),
    }
    if kind == "media":
        item["body"] = doc.get("body")
        item["angle"] = doc.get("angle")
        item["thumb_url"] = f"/api/media/{rid}"
    return item


def all_catalog_items():
    items = []
    for fname, doc in DOC_BY_FILE.items():
        rid = INGEST.get(fname)
        if rid:
            items.append(build_catalog_item(doc, rid, "document"))
    for fname, m in MEDIA_BY_FILE.items():
        rid = INGEST.get(fname)
        if rid:
            items.append(build_catalog_item(m, rid, "media"))
    return items


# ---------------------------------------------------------------- static frontend
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")

PAGES = ["index", "service-assistant", "compliance", "media-library", "deal-desk", "insights", "resource"]


@app.get("/")
def home():
    return FileResponse(ROOT / "static" / "index.html")


for _page in PAGES[1:]:

    def _make_handler(page_name):
        def handler():
            return FileResponse(ROOT / "static" / f"{page_name}.html")
        return handler

    app.get(f"/{_page}")(_make_handler(_page))

app.get("/r/{resource_id}")(lambda resource_id: FileResponse(ROOT / "static" / "resource.html"))


def stock_thumb_map():
    """First real recon-photo resource id per stock number, so the Overview
    stock cards can reuse the same per-vehicle imagery as the Media Library
    instead of a flat repeated icon (consistency bar - B10 applied estate-
    wide, not just on the Media Library route)."""
    out = {}
    for m in MEDIA:
        rid = INGEST.get(m["file"])
        if rid and m["stock_no"] not in out:
            out[m["stock_no"]] = rid
    return out


# ---------------------------------------------------------------- domain data (app's own system of record)
@app.get("/api/stock")
def api_stock():
    thumbs = stock_thumb_map()
    stock = []
    for s in MANIFEST["stock"]:
        s = dict(s)
        rid = thumbs.get(s["no"])
        if rid:
            s["thumb_url"] = f"/api/media/{rid}"
        stock.append(s)
    return {"stock": stock}


@app.get("/api/stock/{stock_no}")
def api_stock_detail(stock_no: str):
    s = STOCK_BY_NO.get(stock_no.upper())
    if not s:
        raise HTTPException(404, "Unknown stock number")
    return s


@app.get("/api/summary")
def api_summary():
    stock = MANIFEST["stock"]
    return {
        "total_stock": len(stock),
        "ready_for_delivery": sum(1 for s in stock if s["pdi_status"] == "Ready for delivery"),
        "pdi_hold": sum(1 for s in stock if s["pdi_status"] == "PDI hold"),
        "in_recon": sum(1 for s in stock if s["pdi_status"] == "In recon"),
        "sites": sorted({s["site"] for s in stock}),
        "documents_indexed": len(DOC_BY_FILE) + len(MEDIA_BY_FILE),
    }


# ---------------------------------------------------------------- media proxy (key never reaches browser)
@app.get("/api/media/{resource_id}")
def api_media(resource_id: str):
    """Streams the platform-native extracted thumbnail/preview for a resource
    (Nuclia's own resource.thumbnail field, read with show=basic - the combined
    show=basic,values form silently returns an empty payload, gotcha 14). The
    key never reaches the browser - this proxy holds it server-side."""
    r0 = requests.get(f"{arag.KB_HOST}/kb/{arag.KB_ID}/resource/{resource_id}",
                       headers=arag.HEADERS, params={"show": "basic"}, timeout=20)
    if r0.status_code != 200:
        raise HTTPException(404, "Not found")
    thumb_path = r0.json().get("thumbnail")
    if not thumb_path:
        raise HTTPException(404, "No thumbnail available")
    r = requests.get(f"{arag.KB_HOST}{thumb_path}", headers=arag.HEADERS, timeout=20)
    if r.status_code != 200:
        raise HTTPException(404, "Thumbnail fetch failed")
    ctype = r.headers.get("content-type", "")
    if not ctype or ctype == "application/octet-stream":
        ctype = "image/jpeg"
    return Response(content=r.content, media_type=ctype)


# ---------------------------------------------------------------- catalog / compliance / media library
@app.get("/api/catalog")
def api_catalog(kind: str = None, doc_type: str = None, site: str = None):
    items = all_catalog_items()
    if kind:
        items = [i for i in items if i["kind"] == kind]
    if doc_type:
        items = [i for i in items if i["doc_type"] == doc_type]
    if site:
        items = [i for i in items if i.get("site") == site]
    return {"items": items, "total": len(items)}


@app.get("/api/facets")
def api_facets(kind: str = None):
    items = all_catalog_items()
    if kind:
        items = [i for i in items if i["kind"] == kind]
    from collections import Counter
    return {
        "doc_type": dict(Counter(i["doc_type"] for i in items if i["doc_type"])),
        "site": dict(Counter(i["site"] for i in items if i.get("site"))),
        "urgency": dict(Counter(i["urgency"] for i in items if i.get("urgency"))),
    }


@app.get("/api/resource/{resource_id}")
def api_resource(resource_id: str, highlight_start: int = None, highlight_end: int = None):
    text = arag.get_resource_text(resource_id)
    res = arag.get_resource(resource_id)
    title = (res or {}).get("title", "Document")
    copy = COPY_CACHE.get(resource_id, {})
    return {
        "id": resource_id,
        "title": title,
        "text": text or "",
        "copy": copy,
        "highlight_start": highlight_start,
        "highlight_end": highlight_end,
    }


# ---------------------------------------------------------------- ask (Service Assistant, general grounded Q&A)
@app.post("/api/assistant")
def api_ask(body: dict):
    question = (body or {}).get("question", "").strip()
    if not question:
        raise HTTPException(400, "question is required")
    filter_expression = (body or {}).get("filter_expression")

    d = arag.ask(question, filter_expression=filter_expression)
    answer = d.get("answer", "")
    status = d.get("status")
    citations = d.get("citations") or {}
    resources = (d.get("retrieval_results") or {}).get("resources") or {}

    marked_answer, sources = arag.build_sources_and_markers(answer, citations, resources)

    # Treat "no genuine citation" as a decline regardless of the raw `status`
    # field - a query can come back status:"success" with zero citations
    # (the model declines in-voice per the search-configuration system
    # prompt, without the platform's own no_context/no_retrieval_data flag
    # firing). Scoring REMi on a decline is misleading either way: a decline
    # that happens to reference real context can score groundedness=5 and
    # render a false "High confidence" badge on an answer that isn't an
    # answer at all - found live. Skip the confidence/REMi badge whenever
    # there is nothing to cite.
    if status in ("no_context", "no_retrieval_data") or not sources:
        answer = arag.strip_fixed_no_context_lead(answer)
        return {
            "answer": answer,
            "status": status,
            "sources": [],
            "confidence": {"label": "No grounded answer", "cls": "moderate"},
            "remi": None,
        }

    # REMi scored against the FULL retrieved paragraph set (B31), not the thin
    # cites - and the paragraphs dict is NOT ordered by relevance, so we must
    # sort by score ourselves before taking the top 8, or REMi gets scored
    # against whatever happened to iterate first (found live: a brake-pad
    # question got scored against a tyre-alignment paragraph and returned a
    # false "Low confidence" on a genuinely well-grounded answer).
    scored_paras = []
    for res in resources.values():
        for field in (res.get("fields") or {}).values():
            for para in (field.get("paragraphs") or {}).values():
                if para.get("text"):
                    scored_paras.append((para.get("score", 0), para["text"]))
    scored_paras.sort(key=lambda x: x[0], reverse=True)
    contexts = [t for _, t in scored_paras[:8]]
    remi_result = arag.remi(question, answer, contexts)
    confidence = arag.confidence_label(remi_result)

    enrich_sources_with_highlights(sources)

    return {
        # scrubbed AFTER marker injection, never before - a pre-injection
        # dash scrub is length-changing and would shift every citation
        # marker position computed against ARAG's original answer string
        "answer": arag.scrub_dashes(marked_answer),
        "status": status,
        "sources": sources,
        "confidence": confidence,
        "remi": remi_result,
    }


def enrich_sources_with_highlights(sources):
    """Resolve each source's excerpt into an exact character range on its own
    resource (Standard B23) so the client can deep-link straight to
    /r/{id}?hl=start-end instead of a fuzzy client-side text search."""
    for s in sources:
        hl = arag.resolve_highlight(s["resource_id"], s.get("excerpt", ""))
        if hl:
            s["hl_start"], s["hl_end"] = hl


# ---------------------------------------------------------------- deal desk (structured diagnosis + citations)
DEAL_SCHEMA = {
    "name": "deal_diagnosis",
    "parameters": {
        "type": "object",
        "properties": {
            "blocker_summary": {"type": "string"},
            "required_actions": {"type": "array", "items": {"type": "string"}},
            "compliance_note": {"type": "string"},
        },
        "required": ["blocker_summary", "required_actions", "compliance_note"],
    },
}


def deal_desk_allowed_resource_ids(stock):
    """Scope the RETRIEVAL itself to this vehicle's own genuinely relevant
    documents - not just the display (the "scope the content, not just
    citations" lesson). Marketing spec sheets and off-make bulletins are
    deliberately excluded: a RAV4 diagnosis has no business citing a Kia
    Sportage spec sheet. Allow-list: this stock's own consultant note, every
    recon manual (procedure standards apply fleet-wide), any recall/service
    bulletin naming this vehicle's make, and compliance policy."""
    make = stock["make"].lower()
    allowed = []
    for doc in MANIFEST["docs"]:
        rid = INGEST.get(doc["file"])
        if not rid:
            continue
        if doc["doc_type"] == "consultant-note" and doc.get("stock_no") == stock["no"]:
            allowed.append(rid)
        elif doc["doc_type"] == "recon-manual":
            allowed.append(rid)
        elif doc["doc_type"] in ("recall", "service-bulletin") and make in doc["file"].lower():
            allowed.append(rid)
        elif doc["doc_type"] == "compliance":
            allowed.append(rid)
    return allowed


@app.get("/api/deal/{stock_no}")
def api_deal(stock_no: str):
    stock_no = stock_no.upper()
    stock = STOCK_BY_NO.get(stock_no)
    if not stock:
        raise HTTPException(404, "Unknown stock number")

    allow_ids = deal_desk_allowed_resource_ids(stock)

    query = (
        f"Stock {stock_no} is a {stock['year']} {stock['make']} {stock['model']} at the "
        f"{stock['site']} site. Based on its consultant field note and any relevant recon "
        f"manual, recall bulletin, or compliance standard, what is currently blocking or "
        f"required before this vehicle can be cleared for delivery?"
    )
    schema_payload = {
        "query": query,
        "answer_json_schema": DEAL_SCHEMA,
        "generative_model": arag.GEN_MODEL,
        "citations": False,
        "resource_filters": allow_ids,
    }
    r = requests.post(f"{arag.KB_HOST}/kb/{arag.KB_ID}/ask", headers=arag.HEADERS,
                       json=schema_payload, timeout=40)
    r.raise_for_status()
    schema_d = r.json()
    diagnosis = arag.scrub_dashes(schema_d.get("answer_json") or {})
    schema_resources = (schema_d.get("retrieval_results") or {}).get("resources") or {}

    # second, parallel citations-only call (gotcha 4: never combine schema + citations),
    # SAME allow-list so a citation can never point outside this vehicle's own scope
    cite_d = arag.ask(query, filter_expression=None, use_search_config=False,
                       extra={"resource_filters": allow_ids})
    cite_answer = cite_d.get("answer", "")
    citations = cite_d.get("citations") or {}
    cite_resources = (cite_d.get("retrieval_results") or {}).get("resources") or {}
    _, sources = arag.build_sources_and_markers(cite_answer, citations, cite_resources)
    if not sources:
        sources = [{"num": i + 1, "resource_id": rid, "title": res.get("title", "Source"), "excerpt": ""}
                   for i, (rid, res) in enumerate(list(schema_resources.items())[:5])]

    # cross-check: every source must genuinely be in the allow-list (belt and
    # braces on top of resource_filters actually restricting retrieval)
    sources = [s for s in sources if s["resource_id"] in allow_ids]
    for i, s in enumerate(sources, start=1):
        s["num"] = i
    enrich_sources_with_highlights(sources)

    return {
        "stock": stock,
        "diagnosis": diagnosis,
        "sources": sources,
    }


# ---------------------------------------------------------------- insights
@app.get("/api/insights")
def api_insights():
    return INSIGHTS


# ---------------------------------------------------------------- reset / reload
@app.post("/api/admin/reload-caches")
def api_reload_caches():
    reload_caches()
    return {"reloaded": True}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8420)), reload=False)
