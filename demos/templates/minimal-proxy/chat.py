"""Rich chat for the University front door: two stages, one conversation.

Stage 1  POST /api/chat/pages   real retrieval only (/find). Returns the pages found, with thumbnails.
Stage 2  POST /api/chat/reply   the grounded, cited answer (/ask) plus the destinations the ANSWER named.

CTA rule (binding): a destination is shown because the answer's PROSE named it, in the order the prose
named it. If the prose names none, destinations are re-derived from the pages the answer CITED (not
retrieval order) and labelled as such. If neither names one, there are none. A decline withholds the
WHOLE response, decided here on the server.

Thumbnails come from the harvested manifest (static/thumbs/manifest.json); a page without one gets no
image here and the client composes a branded title card for it. Nothing is generated or invented.
"""
import asyncio
import hashlib
import os
import json
import re
import time
from pathlib import Path
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse

HERE = Path(__file__).parent
MANIFEST_PATHS = [HERE / "static" / "thumbs" / "manifest.json", HERE / "thumbs" / "manifest.json"]
BASE = "https://www.university.edu.au"

# Real destinations, each checked 200 on 9 Oct 2026. Links OUT only; nothing is processed here.
DEST = {
    "apply": "/study/how-to-apply",
    "courses": "/study/courses",
    "scholarships": "/study/scholarships",
    "entry": "/study/how-to-apply/entry-requirements",
    "international": "/study/international-students",
    "fees": "/study/fees",
    "visit": "/study/open-day",
    "tours": "/explore/about-university/our-locations/maps-and-tours",
    "accommodation": "/study/international-students/life-in-perth/accommodation",
    "visa": "/study/international-students/before-moving-to-perth/apply-for-a-visa",
    "english": "/study/how-to-apply/entry-requirements/english-proficiency-tests",
    "contact": "/contact-us",
}
# Words the PROSE uses, in each supported language. Position in the prose decides the order.
KEYWORDS = {
    "apply": r"how to apply|\bapplications?\b|\bapplying\b|\bapply (?:for|to|online|directly|through|via)\b|申请|التقدم|تقديم|الطلب|mendaftar|pendaftaran|mengajukan",
    "scholarships": r"scholarships?|bursar(?:y|ies)|奖学金|منح(?:ة)?|المنح|beasiswa",
    "courses": r"\bcourses\b|\bdegrees\b|\bprogra(?:m|mme)s\b|find a course|课程|学位|专业|الدورات|دورات|الدرجات|البرامج|kursus|program studi|gelar",
    "entry": r"entry requirements?|admission requirements?|\bATAR\b|入学要求|录取要求|شروط القبول|متطلبات القبول|متطلبات الالتحاق|persyaratan masuk|syarat masuk",
    "international": r"international students?|国际学生|الطلاب الدوليين|الطلبة الدوليين|mahasiswa internasional",
    "fees": r"\bfees?\b|tuition|学费|费用|الرسوم|رسوم|biaya|uang kuliah",
    "visit": r"open day|开放日|يوم مفتوح|اليوم المفتوح|hari terbuka",
    "tours": r"campus tours?|maps and tours|校园参观|جولة|جولات|tur kampus|kunjungan kampus",
    "accommodation": r"accommodation|housing|住宿|السكن|akomodasi|tempat tinggal",
    "visa": r"\bvisas?\b|签证|التأشيرة|تأشيرة|visa",
    "english": r"english (?:language )?(?:proficiency|test)|IELTS|TOEFL|雅思|托福|اللغة الإنجليزية|bahasa inggris",
    "contact": r"contact (?:university|the university|us)|\benquir(?:y|ies)\b|联系|تواصل|اتصل|hubungi",
}
KW = {k: re.compile(v, re.I) for k, v in KEYWORDS.items()}
# A cited page's URL path maps to a destination (used only when the prose named none).
URL_RULES = [
    ("scholarships", "/study/scholarships"), ("entry", "/study/how-to-apply/entry-requirements"),
    ("english", "/english"), ("apply", "/study/how-to-apply"), ("courses", "/study/courses"),
    ("visa", "/apply-for-a-visa"), ("accommodation", "/accommodation"), ("fees", "/study/fees"),
    ("visit", "/study/open-day"), ("tours", "/our-locations"), ("international", "/study/international-students"),
]
# Harvested images known to be unfit. open-day carries a past date (28.3.26). Remove when re-harvested.
STALE = {"x-study-open-day"}
from answers import SYSTEM, ask_numbers_ok, clean_prose, mask_phone_runs  # noqa: E402  (shared by every surface that calls /ask)



def usable(d):
    return bool(d and d.get("status") == "success" and d.get("citations") and (d.get("answer") or "").strip())


def needs_retry(d, lang):
    """One retry in total, never two stacked. Reasons: an answer whose phone numbers are not in its cited sources
    (any language), or an uncited answer on a non-English question (cross-lingual retrieval, measured)."""
    if usable(d):
        return not ask_numbers_ok(d)[0]
    return lang != "en"


MAX_CTAS = 3
MAX_MARKERS = 3

_manifest = {"mtime": None, "data": {}}
_rid_url: dict[str, str] = {}


def norm(url: str) -> str:
    p = urlparse(url or "")
    return f"{p.netloc.lower().removeprefix('www.')}{p.path.rstrip('/')}"


def _entry(v):
    """Harvester shape: {web_path, absent, source}. A page flagged absent has no real image."""
    if isinstance(v, str):
        return {"image": v, "kind": "og"}
    # STALE entries are skipped (open-day carries a past date, 28.3.26).
    if isinstance(v, dict) and not v.get("absent") and v.get("rid") not in STALE:
        img = v.get("web_path") or v.get("image") or v.get("image_url")
        if img:
            # Same photograph under different rids is common; a content hash lets the client show it once per response.
            key = v.get("image_key")  # perceptual group from the harvester, catches crops; md5 is the fallback
            try:
                key = key or hashlib.md5((HERE / img.lstrip("/")).read_bytes()).hexdigest()[:12]
            except OSError:
                key = img
            return {"image": img, "kind": v.get("source") or "og", "key": key}
    return None


def manifest() -> dict:
    """Reloaded when the file changes, so a fresh harvest lands without a restart."""
    for path in MANIFEST_PATHS:
        if path.exists():
            m = path.stat().st_mtime
            if _manifest["mtime"] != (path, m):
                try:
                    raw = json.loads(path.read_text())
                except Exception:
                    raw = {}
                if isinstance(raw, dict) and isinstance(raw.get("thumbs"), (dict, list)):
                    raw = raw["thumbs"]
                items = raw.items() if isinstance(raw, dict) else [(e.get("url"), e) for e in raw if isinstance(e, dict)]
                data = {}
                for u, v in items:
                    e = _entry(v)
                    u = (v.get("url") if isinstance(v, dict) else None) or u
                    if u and e:
                        data[norm(u)] = e
                _manifest.update(mtime=(path, m), data=data)
            return _manifest["data"]
    return {}


def thumb(url: str):
    e = manifest().get(norm(url))
    return {"image": e["image"], "kind": e["kind"], "key": e.get("key")} if e else None


def derive_ctas(prose: str, cited_urls: list[str]):
    """Destinations keyed off what the ANSWER named. Returns (keys, mode)."""
    hits = sorted((m.start(), k) for k, rx in KW.items() for m in [rx.search(prose)] if m)
    keys = [k for _, k in hits]
    if keys:
        return keys[:MAX_CTAS], "prose"
    cited = []
    for u in cited_urls:
        path = urlparse(u).path
        for k, frag in URL_RULES:
            if frag in path:
                if k not in cited:
                    cited.append(k)
                break
    return cited[:MAX_CTAS], ("cited" if cited else "none")


def build_router(kb, headers, model, langs, script_ok, has_arabic, clean_title):
    router = APIRouter()

    async def resource_url(client, rid):
        if rid in _rid_url:
            return _rid_url[rid]
        try:
            r = await client.get(f"{kb}/resource/{rid}", params={"show": "origin"}, headers=headers, timeout=15)
            url = ((r.json().get("origin") or {}).get("url")) or ""
        except Exception:
            url = ""
        if url:
            _rid_url[rid] = url
        return url

    def card(title, url):
        return {"title": clean_title(title), "url": url, "thumb": thumb(url), "path": urlparse(url).path}

    @router.get("/answers")
    async def answers_page():
        """The conversation page. State (question, language) lives in the URL: /answers?q=...&lang=en."""
        return FileResponse(HERE / "templates" / "answers.html", headers={"Cache-Control": "no-cache"})

    @router.post("/api/chat/pages")
    async def pages(request: Request):
        body = await request.json()
        q = str(body.get("q", "")).strip()[:600]
        if not q:
            return JSONResponse({"error": "empty"}, status_code=400)
        t0 = time.perf_counter()
        payload = {"query": q, "top_k": 8, "show": ["basic", "origin"], "features": ["semantic", "keyword"]}
        async with httpx.AsyncClient() as client:
            try:
                r = await client.post(f"{kb}/find", json=payload, headers=headers, timeout=20)
                r.raise_for_status()
            except httpx.TimeoutException:
                return JSONResponse({"error": "timeout"}, status_code=504)
            except httpx.HTTPError:
                return JSONResponse({"error": "upstream"}, status_code=502)
        d = r.json()
        res = d.get("resources") or {}
        order = list(dict.fromkeys(b.split("/")[0] for b in (d.get("best_matches") or []))) or list(res)
        out, seen = [], set()
        for rid in order:
            v = res.get(rid)
            url = ((v or {}).get("origin") or {}).get("url") or ""
            if not v or not url or url in seen:
                continue
            seen.add(url)
            _rid_url[rid] = url
            out.append(card(v.get("title", ""), url))
        return {"pages": out[:4], "ms": round((time.perf_counter() - t0) * 1000)}

    async def finalize(client, d, lang, t0):
        text = d.get("answer") or ""
        cites = d.get("citations") or {}
        ms = round((time.perf_counter() - t0) * 1000)
        # Server labels the event: a decline is "no sourced answer". The WHOLE response is withheld.
        if d.get("status") != "success" or not cites or not text.strip():
            return {"declined": True, "dir": "ltr", "lang": lang, "ms": ms}
        if not ask_numbers_ok(d)[0]:
            # A phone number the cited sources do not contain, after the one retry: withhold the whole response.
            return {"declined": True, "dir": "ltr", "lang": lang, "ms": ms, "withheld": "unverified_number"}
        resources = (d.get("retrieval_results") or {}).get("resources") or {}
        by_end: dict[int, list[str]] = {}
        for key, spans in cites.items():
            rid = key.split("/")[0]
            for _s, e in spans:
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
        text = clean_prose(text, lang)
        sources = []
        for (rid, n), url in zip(order.items(), urls):
            c = card((resources.get(rid) or {}).get("title", ""), url)
            c["n"] = n
            sources.append(c)
        plain = re.sub("⟦[\\d,]+⟧", "", text)
        keys, mode = derive_ctas(plain, [s["url"] for s in sources])
        dests = [{"key": k, "url": BASE + DEST[k], "thumb": thumb(BASE + DEST[k])} for k in keys]
        return {
            "declined": False, "answer": text, "sources": sources,
            "dests": dests, "dest_mode": mode,
            "contact": {"url": BASE + DEST["contact"]},
            "dir": "rtl" if (lang == "ar" or has_arabic(plain)) else "ltr",
            "lang": lang, "lang_ok": script_ok(lang, plain), "ms": ms,
        }

    def make_payload(body):
        q = str(body.get("q", "")).strip()[:600]
        lang = body.get("lang", "en")
        if lang not in langs:
            lang = "en"
        payload = {"query": q, "generative_model": model, "citations": True}
        hist = []
        for h in (body.get("history") or [])[-6:]:
            if isinstance(h, dict) and h.get("role") in ("user", "assistant") and isinstance(h.get("text"), str):
                text = re.sub("⟦[\\d,]+⟧", "", h["text"])[:1500]
                hist.append({"author": "USER" if h["role"] == "user" else "NUCLIA", "text": text})
        if hist:
            payload["chat_history"] = hist
        payload["prompt"] = {"system": SYSTEM + (f" Answer in {langs[lang]}, whatever language the sources are in." if lang != "en" else "")}
        return q, lang, payload

    @router.post("/api/chat/reply")
    async def reply(request: Request):
        body = await request.json()
        q, lang, payload = make_payload(body)
        if not q:
            return JSONResponse({"error": "empty"}, status_code=400)
        t0 = time.perf_counter()
        async with httpx.AsyncClient() as client:
            # Non-English questions retrieve against English pages and intermittently come back with an answer
            # and NO citations (measured: a compound Arabic scholarships question cited on roughly half the
            # runs). One bounded retry, on the failing path only, with query rephrasing. A second uncited
            # result is still a decline: nothing is shown without a source.
            for attempt in range(2):
                if attempt and not usable(d):
                    payload = {**payload, "rephrase": True}
                try:
                    r = await client.post(f"{kb}/ask", json=payload, headers=headers, timeout=55)
                except httpx.TimeoutException:
                    return JSONResponse({"error": "timeout"}, status_code=504)
                except httpx.HTTPError:
                    return JSONResponse({"error": "upstream"}, status_code=502)
                if r.status_code >= 400:
                    return JSONResponse({"error": "upstream", "code": r.status_code}, status_code=502)
                d = r.json()
                if not needs_retry(d, lang):
                    break
            return await finalize(client, d, lang, t0)


    # ---- streaming -------------------------------------------------------------------------------------
    # The ask endpoint streams NDJSON when X-Synchronous is NOT sent. Prose arrives from the first token, but
    # citations and the status arrive ONLY at the end, so whether an answer is sourced or declined is not known
    # until then. DRAFT mode (default) streams the prose under a "sources are checked when it finishes" label and
    # REPLACES it wholesale at the end (a decline withdraws the entire draft). CHAT_STREAM_DRAFT=0 holds the prose
    # back and sends only the final event (the strict, non-streaming-looking mode) - one switch, no code change.
    stream_headers = {k: v for k, v in headers.items() if k.lower() != "x-synchronous"}
    draft_on = os.environ.get("CHAT_STREAM_DRAFT", "1") != "0"
    # Measured 9 Oct (40 asks, 4 languages): uncited-but-success declines ran 44 to 444 characters (n=8; platform no_context declines are a fixed 31). 500 clears all 8. Env override for re-measuring.
    HOLD = int(os.environ.get("CHAT_STREAM_HOLD", "500"))

    def ndjson(o):
        return (json.dumps(o, ensure_ascii=False) + "\n").encode()

    async def ask_stream(client, payload, lang):
        """Yields ('text', cleaned_prefix) while streaming, then ('done', d) shaped like the synchronous reply."""
        acc, final = [], {"answer": "", "status": None, "citations": {}, "retrieval_results": {}}
        async with client.stream("POST", f"{kb}/ask", json=payload, headers=stream_headers,
                                 timeout=httpx.Timeout(55, read=55)) as r:
            if r.status_code >= 400:
                raise httpx.HTTPError(f"status {r.status_code}")
            buf = b""
            async for chunk in r.aiter_bytes():
                buf += chunk
                *lines, buf = buf.split(b"\n")  # NOT iter_lines: it also splits on U+2028 and truncates items
                for ln in lines:
                    if not ln.strip():
                        continue
                    it = json.loads(ln).get("item") or {}
                    ty = it.get("type")
                    if ty == "answer":
                        acc.append(it.get("text", ""))
                        raw = "".join(acc)
                        if draft_on and len(raw) >= HOLD:
                            cut = raw.rfind(" ")  # whole words only, so a half word is never respelled
                            if cut > 0:
                                yield "text", mask_phone_runs(clean_prose(raw[:cut], lang))
                    elif ty == "status":
                        final["status"] = it.get("status")
                    elif ty == "citations":
                        final["citations"] = it.get("citations") or {}
                    elif ty == "retrieval":
                        final["retrieval_results"] = it.get("results") or {}
        final["answer"] = "".join(acc)
        yield "done", final

    @router.post("/api/chat/stream")
    async def stream(request: Request):
        body = await request.json()
        q, lang, payload = make_payload(body)
        if not q:
            return JSONResponse({"error": "empty"}, status_code=400)
        t0 = time.perf_counter()

        async def gen():
            async with httpx.AsyncClient() as client:
                d = None
                for attempt in range(2):
                    pl = payload if not attempt or usable(d) else {**payload, "rephrase": True}
                    if attempt:
                        yield ndjson({"t": "reset"})
                    try:
                        async for kind, val in ask_stream(client, pl, lang):
                            if kind == "text":
                                yield ndjson({"t": "text", "text": val})
                            else:
                                d = val
                    except (httpx.HTTPError, ValueError):
                        yield ndjson({"t": "error", "error": "upstream"})
                        return
                    if not needs_retry(d, lang):
                        break
                out = await finalize(client, d, lang, t0)
                yield ndjson({"t": "final", **out})

        return StreamingResponse(gen(), media_type="application/x-ndjson", headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"})

    return router
