"""ARAG starter chassis - one FastAPI process, one static page, every ARAG call server-side.

Routes the starter ships with:
  GET  /               the product page (static/index.html)
  GET  /api/config     product name, promise line, suggested questions (from PRODUCT below)
  POST /api/ask        grounded answer: prose, inline citation placement, sources, confidence badge
  POST /api/find       retrieval only: scored resources, no generation
  GET  /healthz

Everything ARAG-specific lives in arag.py (copied from a finished app, do not rewrite it).
Add your product's own route(s) under "# --- product routes" and leave the rest alone.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

import arag  # noqa: E402  (needs env loaded first)
from fastapi import FastAPI  # noqa: E402
from fastapi.responses import HTMLResponse, JSONResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

ROOT = Path(__file__).parent
PRODUCT = json.loads((ROOT / "product.json").read_text(encoding="utf-8"))

app = FastAPI(title=PRODUCT["name"], docs_url=None, redoc_url=None)

# Starter-grade guard rails: a per-IP budget on the generating route and a one-line access log
# that never records the question text (status and latency only).
import logging  # noqa: E402
import time  # noqa: E402
from collections import defaultdict, deque  # noqa: E402

from fastapi import Request  # noqa: E402

log = logging.getLogger("starter")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
RATE_LIMIT = int(os.environ.get("RATE_LIMIT_PER_MIN", "20"))  # asks per IP per minute; 0 disables
_hits: dict[str, deque] = defaultdict(deque)


@app.middleware("http")
async def guard(request: Request, call_next):
    t0 = time.perf_counter()
    if RATE_LIMIT and request.method == "POST" and request.url.path.startswith("/api/"):
        ip = request.client.host if request.client else "?"
        q = _hits[ip]
        now = time.monotonic()
        while q and now - q[0] > 60:
            q.popleft()
        if len(q) >= RATE_LIMIT:
            return JSONResponse(status_code=429, content={"error": "Too many questions in a minute. Please wait a moment and try again."})
        q.append(now)
    response = await call_next(request)
    log.info("%s %s %s %dms", request.method, request.url.path, response.status_code, int((time.perf_counter() - t0) * 1000))
    return response
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")

# The decline contract: the model says this exact phrase when the sources do not hold the
# answer, and the app turns it into a withheld answer with nothing attached.
NOT_FOUND = "NOT IN SOURCES"
SYSTEM = (
    f"Answer only from the supplied context. If the context does not contain the answer, reply with "
    f"exactly: {NOT_FOUND} - followed by one sentence naming what would be needed. Do not infer or "
    f"generalise. Australian English, no em dashes."
)


class AskIn(BaseModel):
    question: str = Field(min_length=3, max_length=500)
    lang: str | None = Field(default=None, max_length=12)  # BCP-47 like "ja" or "ar"; None = source language


class FindIn(BaseModel):
    query: str = Field(min_length=2, max_length=300)
    top_k: int = Field(default=12, ge=1, le=50)


def declined(answer: str) -> dict:
    """The one way a withheld answer leaves this app: no sources, no badge, no sentences."""
    return {"answer": answer, "withheld": True, "sentences": [], "sources": [],
            "confidence": {"label": "Answer withheld", "tone": "unknown", "detail": ""}}


def sources_payload(items: list[dict]) -> list[dict]:
    top = max((s.get("score") or 0) for s in items) if items else 0
    out = []
    for s in items:
        title = s.get("title") or "Source document"
        if re.match(r"^[0-9a-f]{16,}", title):  # never show a raw internal key
            title = "Source document"
        out.append({"rid": s.get("rid"), "title": title, "url": s.get("url") or "",
                    "excerpt": s.get("excerpt", ""),
                    "relevance": round((s.get("score") or 0) / top, 3) if top else None})
    return out


async def grounded_answer(question: str, lang: str | None = None, filt: dict | None = None) -> dict:
    prompt = SYSTEM + (f" Answer in the language with code '{lang}', whatever language the sources are in." if lang else "")
    data = await arag.ask(question, filt=filt, prompt=prompt)
    answer = arag.tidy(data.get("answer") or "")
    if not answer or answer.upper().startswith(NOT_FOUND):
        return declined(answer or f"{NOT_FOUND} - the sources do not cover this.")
    sources = arag.resources_from_find(data.get("retrieval_results") or {})
    contexts = arag.contexts_from_ask(data)
    score = await arag.groundedness(question, answer, contexts)  # None on a non-enterprise KB
    payload = sources_payload(sources[:8])
    sentences = arag.place_citations(answer, payload)
    return {"answer": answer, "withheld": False, "sentences": sentences, "sources": payload,
            "confidence": arag.confidence_badge(score), "retrieved": len(sources)}


# --- chassis routes
@app.get("/api/config")
async def config():
    return {k: PRODUCT[k] for k in ("name", "promise", "suggested", "how_it_works")}


@app.post("/api/ask")
async def ask(body: AskIn):
    return await grounded_answer(body.question, lang=body.lang)


@app.post("/api/find")
async def find(body: FindIn):
    data = await arag.find(body.query, top_k=body.top_k)
    return {"results": sources_payload(arag.resources_from_find(data))}


@app.get("/healthz")
async def healthz():
    return {"ok": True}


# --- product routes (add yours here; copy the shape of /api/ask)


@app.exception_handler(arag.UpstreamError)
async def upstream_handler(_request, exc):
    return JSONResponse(status_code=502, content={"error": str(exc)})


@app.get("/", include_in_schema=False)
@app.get("/{full_path:path}", include_in_schema=False)
async def page(full_path: str = ""):
    return HTMLResponse((ROOT / "static" / "index.html").read_text(encoding="utf-8"))
