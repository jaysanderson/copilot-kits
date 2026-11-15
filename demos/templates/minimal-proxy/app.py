"""The university prospective-student front door.

FastAPI proxy: the browser never sees the knowledge base URL or token. One route,
/api/answer, calls the ARAG ask endpoint server-side with the generative model pinned.
"""
import asyncio
import os
import re
from pathlib import Path

import httpx
import uvicorn
from dotenv import load_dotenv
from answers import STYLE, ask_numbers_ok, clean_prose
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

HERE = Path(__file__).parent
load_dotenv(HERE / ".env")

KB_URL = os.environ.get("KB_URL", "").rstrip("/")
KB_TOKEN = os.environ.get("KB_TOKEN", "")
MODEL = os.environ.get("ARAG_GENERATIVE_MODEL", "gemini-3.1-flash-lite")
HEADERS = {
    "X-NUCLIA-SERVICEACCOUNT": f"Bearer {KB_TOKEN}",
    "Content-Type": "application/json",
    "X-Synchronous": "true",
}
LANGS = {
    "en": "English",
    "zh": "Simplified Chinese (Mandarin)",
    "ar": "Arabic",
    "id": "Bahasa Indonesia",
}
MAX_MARKERS = 3
# RESEED TRAP: scope filters on each resource's origin.path (the URL path), which was PATCHED onto
# the 343 resources by seed/set_origin_path.py. A reseed or re-crawl loses it, and every scoped ask then
# returns nothing (the server-side cited-source check will withhold, so it fails visibly, not open).
# Re-run `python seed/set_origin_path.py` after ANY reseed.
# Section scopes for embedders. Keys are allow-listed and mapped to a filter_expression HERE;
# an unrecognised key is rejected, never answered unscoped (a malformed expression fails open).
SCOPES = {
    "study": "/study",
    "scholarships": "/study/scholarships",
    "how-to-apply": "/study/how-to-apply",
    "international": "/study/international-students",
    "explore": "/explore",
    "research": "/research",
    "news": "/news",
}
CORS_ORIGINS = [o.strip() for o in os.environ.get("CORS_ORIGINS", "*").split(",") if o.strip()]

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, allow_methods=["POST", "OPTIONS"],
                   allow_headers=["Content-Type"], allow_credentials=False)
app.mount("/static", StaticFiles(directory=HERE / "static"), name="static")
templates = Jinja2Templates(directory=HERE / "templates")
_url_cache: dict[str, str] = {}

# Real university.edu.au destinations, each checked 200 on 9 Oct 2026. The demo links OUT to
# these; it never processes an application.
CTAS = {
    "apply": ("Start your application", "https://www.university.edu.au/study/how-to-apply"),
    "courses": ("Search courses", "https://www.university.edu.au/study/courses"),
    "scholarships": ("See scholarships", "https://www.university.edu.au/study/scholarships"),
    "international": ("International students", "https://www.university.edu.au/study/international-students"),
    "visit": ("Open day and campus visits", "https://www.university.edu.au/study/open-day"),
}
CTA_RULES = [
    ("apply", r"appl(y|ication)"),
    ("scholarships", r"scholarship|bursar"),
    ("courses", r"/courses?/|/units?/|/study/undergraduate|/study/postgraduate|/study-areas"),
    ("international", r"international"),
    ("visit", r"open-day|campus|tour|visit"),
]

ID_WORDS = {"yang", "dan", "untuk", "dengan", "anda", "dapat", "atau", "di", "ke", "dari", "pada"}


def script_ok(lang: str, text: str) -> bool:
    """Did the answer actually come back in the picked language? Compared, not eyeballed."""
    if lang == "en":
        return True
    ar = len(re.findall(r"[؀-ۿ]", text))
    cjk = len(re.findall(r"[一-鿿]", text))
    lat = len(re.findall(r"[A-Za-z]", text))
    if lang == "ar":
        return ar > 60 and ar > lat * 0.3
    if lang == "zh":
        return cjk > 60
    words = re.findall(r"[a-z]+", text.lower())
    return sum(w in ID_WORDS for w in words) >= 8


def within_scope(sources: list, prefix: str) -> bool:
    """/ask honours filters less reliably than /find, so every cited page is checked against the scope."""
    from urllib.parse import urlparse
    return bool(sources) and all(urlparse(x.get("url") or "").path.startswith(prefix) for x in sources)


def has_arabic(text: str) -> bool:
    return len(re.findall(r"[؀-ۿ]", text)) > len(re.findall(r"[A-Za-z]", text))


async def resource_url(client: httpx.AsyncClient, rid: str) -> str:
    if rid in _url_cache:
        return _url_cache[rid]
    try:
        r = await client.get(f"{KB_URL}/resource/{rid}", params={"show": "origin"}, headers=HEADERS, timeout=15)
        url = ((r.json().get("origin") or {}).get("url")) or ""
    except Exception:
        url = ""
    if url:
        _url_cache[rid] = url
    return url


def clean_title(t: str) -> str:
    return re.sub(r"\s*\|\s*The university\s*$", "", t or "").strip() or "The university"


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request, "index.html", {"ctas": CTAS})


FACULTY_URL = os.environ.get("FACULTY_URL", "https://your-app.fly.dev/t/universityvet")


@app.get("/faculty")
async def faculty():
    return RedirectResponse(FACULTY_URL, status_code=307)


@app.get("/healthz")
async def healthz():
    return {"ok": True}


@app.post("/api/pages")
async def pages(request: Request):
    """Real retrieval only: the pages the search finds, returned as soon as it lands."""
    body = await request.json()
    q = str(body.get("q", "")).strip()[:600]
    if not q:
        return JSONResponse({"error": "empty"}, status_code=400)
    payload = {"query": q, "top_k": 8, "show": ["basic", "origin"], "features": ["semantic", "keyword"]}
    async with httpx.AsyncClient() as client:
        try:
            r = await client.post(f"{KB_URL}/find", json=payload, headers=HEADERS, timeout=20)
            r.raise_for_status()
        except httpx.HTTPError:
            return JSONResponse({"error": "upstream"}, status_code=502)
    d = r.json()
    best = d.get("best_matches") or []
    res = d.get("resources") or {}
    out = []
    for rid in list(dict.fromkeys([b.split("/")[0] for b in best])) or list(res):
        v = res.get(rid)
        if not v:
            continue
        url = (v.get("origin") or {}).get("url") or ""
        if url:
            _url_cache[rid] = url
        out.append({"title": clean_title(v.get("title", "")), "url": url})
    return {"pages": out[:6]}


@app.post("/api/answer")
async def answer(request: Request):
    body = await request.json()
    q = str(body.get("q", "")).strip()[:600]
    lang = body.get("lang", "en")
    if lang not in LANGS:
        lang = "en"
    if not q:
        return JSONResponse({"error": "empty"}, status_code=400)
    payload = {"query": q, "generative_model": MODEL, "citations": True}
    scope = body.get("scope")
    if scope:
        if scope not in SCOPES:
            return JSONResponse({"error": "unknown_scope"}, status_code=400)
        payload["filter_expression"] = {"field": {"prop": "origin_path", "prefix": SCOPES[scope]}}
    payload["prompt"] = {"system": STYLE + (f" Answer the question in {LANGS[lang]}, whatever language the sources are in." if lang != "en" else "")}
    async with httpx.AsyncClient() as client:
        try:
            r = await client.post(f"{KB_URL}/ask", json=payload, headers=HEADERS, timeout=55)
        except httpx.TimeoutException:
            return JSONResponse({"error": "timeout"}, status_code=504)
        except httpx.HTTPError:
            return JSONResponse({"error": "upstream"}, status_code=502)
        if r.status_code >= 400:
            return JSONResponse({"error": "upstream", "code": r.status_code}, status_code=502)
        d = r.json()
        # Phone-number guard: at most ONE retry (2 /ask calls per request), then withhold. No repair.
        if d.get("citations") and not ask_numbers_ok(d)[0]:
            try:
                r = await client.post(f"{KB_URL}/ask", json=payload, headers=HEADERS, timeout=55)
            except httpx.HTTPError:
                return JSONResponse({"error": "upstream"}, status_code=502)
            if r.status_code >= 400:
                return JSONResponse({"error": "upstream", "code": r.status_code}, status_code=502)
            d = r.json()
            if d.get("citations") and not ask_numbers_ok(d)[0]:
                return {"declined": True, "dir": "ltr", "lang": lang}
        text = d.get("answer") or ""
        cites = d.get("citations") or {}
        # Server labels the event: a decline is "no sourced answer", decided here, not by
        # string-matching in the client. The WHOLE response is withheld.
        if d.get("status") != "success" or not cites or not text.strip():
            return {"declined": True, "dir": "ltr", "lang": lang}

        resources = (d.get("retrieval_results") or {}).get("resources") or {}
        # span end offset -> ordered resource ids
        by_end: dict[int, list[str]] = {}
        for key, spans in cites.items():
            rid = key.split("/")[0]
            for s, e in spans:
                lst = by_end.setdefault(e, [])
                if rid not in lst:
                    lst.append(rid)
        order: dict[str, int] = {}
        inserts = []
        for e in sorted(by_end):
            pos = min(e, len(text))
            while pos < len(text) and text[pos] not in " \n.,;:!?。，；：！？)":
                pos += 1
            nums = []
            for rid in by_end[e][:MAX_MARKERS]:
                if rid not in order:
                    order[rid] = len(order) + 1
                if order[rid] not in nums:
                    nums.append(order[rid])
            inserts.append((pos, nums))
        for pos, nums in sorted(inserts, reverse=True):
            text = text[:pos] + "⟦" + ",".join(map(str, nums)) + "⟧" + text[pos:]
        urls = await asyncio.gather(*[resource_url(client, rid) for rid in order])
    sources = []
    for (rid, n), url in zip(order.items(), urls):
        title = clean_title((resources.get(rid) or {}).get("title", ""))
        sources.append({"n": n, "title": title, "url": url})
    if scope and not within_scope(sources, SCOPES[scope]):
        # Withhold the WHOLE response: a cited page outside the requested scope.
        return {"declined": True, "dir": "ltr", "lang": lang}
    keys = []
    blob = " ".join(s["url"].lower() + " " + s["title"].lower() for s in sources)
    for k, pat in CTA_RULES:
        if re.search(pat, blob):
            keys.append(k)
    # Runs AFTER the markers are inserted: stripping a preamble shifts character offsets.
    text = clean_prose(text, lang)
    plain = re.sub("⟦[\\d,]+⟧", "", text)
    return {
        "declined": False,
        "answer": text,
        "sources": sources,
        "ctas": [{"label": CTAS[k][0], "url": CTAS[k][1]} for k in keys[:3]],
        "dir": "rtl" if (lang == "ar" or has_arabic(plain)) else "ltr",
        "lang": lang,
        "lang_ok": script_ok(lang, plain),
    }



# Route modules handed over by their builders; each exposes a router and is registered here only.
from pagemode import build_router  # noqa: E402
app.include_router(build_router(kb=KB_URL, headers=HEADERS, model=MODEL, langs=LANGS, script_ok=script_ok,
                                has_arabic=has_arabic, templates=templates, clean_title=clean_title))
from embed import router as embed_router  # noqa: E402
app.include_router(embed_router)
from sections import router as sections_router  # noqa: E402
app.include_router(sections_router)
from runsheet import router as run_router  # noqa: E402
app.include_router(run_router)


from wander import build_router as wander_router  # noqa: E402
app.include_router(wander_router(kb=KB_URL, headers=HEADERS, model=MODEL, templates=templates, clean_title=clean_title))
from chat import build_router as chat_router  # noqa: E402
app.include_router(chat_router(kb=KB_URL, headers=HEADERS, model=MODEL, langs=LANGS, script_ok=script_ok,
                               has_arabic=has_arabic, clean_title=clean_title))
import insights  # noqa: E402
app.add_middleware(insights.InsightsLogger)
app.include_router(insights.build_router(templates=templates))


@app.exception_handler(404)
async def not_found(request: Request, exc):
    if request.url.path.startswith("/api/"):
        return JSONResponse({"error": "not_found"}, status_code=404)
    return RedirectResponse("/", status_code=307)


if __name__ == "__main__":
    uvicorn.run(app, host=os.environ.get("HOST", "127.0.0.1"), port=int(os.environ.get("PORT", "8080")))

