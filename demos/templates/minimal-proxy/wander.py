"""Wander: explore the University site by what pages share, not by where the menu puts them.

Add-only module. Every traversal is a real anchored query against the knowledge base's graph
(graphwalk.py); the browser never sees the knowledge base URL or token.
"""
import asyncio
import re

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse

import graphwalk as gw
from answers import STYLE, ask_numbers_ok, clean_prose

STARTS = [
    "study/international-students", "study/scholarships", "research/research-ethics-and-integrity",
    "study/courses/study-areas", "explore/support-services", "collaborate/business-and-industry",
]

def tree_path(pid: str) -> list:
    """Segments below the site root. The home page (/home, or a bare domain) is the root itself, zero steps down."""
    segs = [s for s in gw.PAGES[pid]["url"].split("/")[3:] if s]
    return [] if segs == ["home"] else segs

def tree_steps(a: str, b: str) -> int:
    """Steps between two pages along the site's own URL tree: up to the shared ancestor, then down.
    This is tree distance, not clicks: the real mega-menu and logo give shortcuts we cannot measure."""
    pa = tree_path(a)
    pb = tree_path(b)
    k = 0
    while k < min(len(pa), len(pb)) and pa[k] == pb[k]:
        k += 1
    return (len(pa) - k) + (len(pb) - k)

def build_router(kb, headers, model, templates, clean_title):
    router = APIRouter()
    pid_by_path = {p["url"].rstrip("/").split("university.edu.au/")[-1]: i for i, p in gw.PAGES.items() if not p.get("alias")}

    @router.get("/wander", response_class=HTMLResponse)
    async def wander(request: Request):
        starts = [gw.page_card(pid_by_path[s]) for s in STARTS if s in pid_by_path]
        return templates.TemplateResponse(request, "wander.html", {"starts": starts, "s": gw.SITE, "f": gw.FACTS})

    @router.get("/wander/reveal", response_class=HTMLResponse)
    async def reveal(request: Request):
        """The How this works fragment. Figures are counted from the graph file, never typed into the template."""
        return templates.TemplateResponse(request, "wander_reveal.html", {"f": gw.FACTS, "s": gw.SITE})

    @router.post("/api/wander/start")
    async def start(request: Request):
        """Where am I? A real search finds the visitor's starting page; the graph takes over from there."""
        q = str((await request.json()).get("q", "")).strip()[:300]
        if not q:
            return JSONResponse({"error": "empty"}, status_code=400)
        async with httpx.AsyncClient() as c:
            try:
                r = await c.post(f"{kb}/find", json={"query": q, "top_k": 12, "show": ["basic"], "features": ["semantic", "keyword"]}, headers=headers, timeout=20)
                r.raise_for_status()
            except httpx.HTTPError:
                return JSONResponse({"error": "upstream"}, status_code=502)
        d = r.json()
        # Retrieval never returns empty: gibberish still comes back with hits, all scored 0.0 by the reranker.
        # Nothing below this best-paragraph score is offered as a start (gibberish 0.0, real queries 0.3 to 0.9).
        best = max((p.get("score", 0) for r in (d.get("resources") or {}).values() for f in r.get("fields", {}).values()
                    for p in f.get("paragraphs", {}).values()), default=0)
        if best < 0.15:
            return {"pages": []}
        order = [b.split("/")[0] for b in (d.get("best_matches") or [])] or list((d.get("resources") or {}))
        out = [gw.page_card(i) for i in dict.fromkeys(order) if i in gw.PAGES and not gw.PAGES[i].get("alias")]
        return {"pages": out[:6]}

    @router.get("/api/wander/page")
    async def page(id: str, frm: str = ""):
        if id not in gw.PAGES or gw.PAGES[id].get("alias"):
            return JSONResponse({"error": "not_found"}, status_code=404)
        async with httpx.AsyncClient() as c:
            try:
                ex = await gw.expand_page(c, kb, headers, id)
            except httpx.TimeoutException:
                return JSONResponse({"error": "timeout"}, status_code=504)
            except httpx.HTTPError:
                return JSONResponse({"error": "upstream"}, status_code=502)
        for l in ex["links"]:
            for p in l["pages"]:
                p["tree_steps"] = tree_steps(id, p["id"])
        ex["capped"] = ex["relations_read"] >= 500
        ex["reach"] = gw.page_reach(id)   # derived from graph/graph_edges.json at load, never typed in
        ex["site"] = gw.SITE
        return ex

    @router.post("/api/wander/answer")
    async def answer(request: Request):
        """Ask across the walk: the graph walk scopes the retrieval and is passed as extra_context."""
        body = await request.json()
        q = str(body.get("q", "")).strip()[:500]
        ids = [i for i in (body.get("ids") or []) if i in gw.PAGES][:40]
        ctx = [str(x)[:400] for x in (body.get("context") or [])][:8]
        if not q or not ids:
            return JSONResponse({"error": "empty"}, status_code=400)
        payload = {"query": q, "generative_model": model, "citations": True, "resource_filters": ids, "prompt": {"system": STYLE}}
        if ctx:
            payload["extra_context"] = ctx
        async with httpx.AsyncClient() as c:
            try:
                r = await c.post(f"{kb}/ask", json=payload, headers=headers, timeout=55)
                if r.status_code < 400:
                    d = r.json()
                    if d.get("citations") and not ask_numbers_ok(d)[0]:
                        # A phone number the cited pages do not carry: one retry, never a repair. At most 2 ask calls per request.
                        r = await c.post(f"{kb}/ask", json=payload, headers=headers, timeout=55)
            except httpx.TimeoutException:
                return JSONResponse({"error": "timeout"}, status_code=504)
            except httpx.HTTPError:
                return JSONResponse({"error": "upstream"}, status_code=502)
        if r.status_code >= 400:
            return JSONResponse({"error": "upstream"}, status_code=502)
        d = r.json()
        cites = list(dict.fromkeys(k.split("/")[0] for k in (d.get("citations") or {})))
        text = (d.get("answer") or "").strip()
        text = clean_prose(text, "en")
        if d.get("status") != "success" or not cites or not text or (d.get("citations") and not ask_numbers_ok(d)[0]):
            return {"declined": True}
        return {"declined": False, "answer": text, "sources": [gw.page_card(i) for i in cites if i in gw.PAGES]}

    return router
