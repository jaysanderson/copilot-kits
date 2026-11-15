"""Talk to one page, in your own language, with the cited passage highlighted in the page.

A separate router mounted at /page: it adds routes and touches none of the home-page ones.
Every capability is a real call per request: the page body is read from the knowledge base,
the answer comes from a scoped ask (resource_filters + full_resource) that also returns the passages
it relied on, copied word for word. Application code then checks each quote against the page's own
text: a block is highlighted only if the quote and the block contain one another. A quote that is
not found verbatim highlights nothing, and the page says so.
"""
import asyncio
import html
import json
import re
from pathlib import Path

import httpx
from answers import STYLE, clean_prose, phone_guard
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse

# Real university.edu.au pages in the knowledge base. Label, resource id, live URL.
PAGES = {
    "apply": ("How to apply", "fa75bb439de8477fab6d39dc573f4e0a", "https://www.university.edu.au/study/how-to-apply"),
    "international": ("International students", "eddfd3817e274ed08320eb4dea320d71", "https://www.university.edu.au/study/international-students"),
    "scholarships": ("Scholarships", "25d02cfd92074bf5a982d5e2c5b74ae1", "https://www.university.edu.au/study/scholarships"),
    "perth": ("Perth campus", "06480bbb296b42d29a4d5ae9b79a8fb9", "https://www.university.edu.au/explore/about-university/our-locations/perth-campus"),
}
_cache: dict[str, dict] = {}


def _inline(s: str) -> str:
    s = html.escape(s, quote=False)
    s = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]*)\)", lambda m: _anchor(m.group(1), m.group(2)), s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    return s


def _anchor(text: str, target: str) -> str:
    t = html.unescape(target).strip()
    t = re.sub(r'\s+"[^"]*"$', "", t)  # optional link title
    if re.match(r"(mailto|tel):", t, re.I):
        href = html.escape(t.replace(" ", "%20"), quote=True)
        return f'<a href="{href}">{text}</a>'
    href = _abs(t.replace(" ", "%20"))
    if href == "#":
        return text  # not a destination we can stand behind
    return f'<a href="{href}" target="_blank" rel="noopener">{text}</a>'


def _abs(u: str) -> str:
    u = html.unescape(u)
    if u.startswith("/"):
        u = "https://www.university.edu.au" + u
    if not re.match(r"https?://", u):
        return "#"
    return html.escape(u, quote=True)


def _unesc(t: str) -> str:
    """The crawl backslash-escapes markdown punctuation (2026\\*); show the character, not the escape."""
    return re.sub(r"\\([\\`*_{}\[\]()#+\-.!>~|])", r"\1", t)


def _plain(raw: str) -> str:
    raw = _join_links(raw)
    t = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", raw)
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)
    t = re.sub(r"^\s*#{1,6}\s*", "", _unesc(t), flags=re.M)
    return re.sub(r"[*_`]", "", t)


def _join_links(raw: str) -> str:
    """The crawl breaks a link's text across lines ("[View\nApply]"): keep it one link."""
    return re.sub(r"\[([^\]\n]*)\n\s*([^\]]*)\]\(", r"[\1 \2](", raw)


def _block_html(raw: str) -> str:
    raw = _join_links(raw)
    lines = [_unesc(l) for l in raw.split("\n") if l.strip()]
    if not lines:
        return ""
    if len(lines) == 1 and re.match(r"Image\b", lines[0]):
        return ""  # crawler alt-text line, not page copy
    out, para, items = [], [], []

    def flush():
        nonlocal para, items
        if para:
            out.append("<p>" + "<br>".join(para) + "</p>")
        if items:
            out.append("<ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>")
        para, items = [], []

    for l in lines:
        m = re.match(r"\s*(#{1,6})\s+(.*)", l)
        b = re.match(r"\s*[*+-]\s+(.*)", l)
        if m:
            flush()
            n = min(len(m.group(1)) + 1, 6)
            out.append(f"<h{n}>{_inline(m.group(2).strip())}</h{n}>")
        elif b:
            if para:
                flush()
            items.append(_inline(b.group(1)))
        else:
            if items:
                flush()
            para.append(_inline(l.strip()))
    flush()
    return "".join(out)


def _norm(t: str) -> str:
    """Words only, lower-cased: so a quote still matches when the page has bullets, pipes or curly quotes."""
    t = _plain(t).lower().replace("\u2019", "'").replace("\u2018", "'")
    return " ".join(re.findall(r"\w+", t))


def _is_nav(raw: str) -> bool:
    """A block that is only a list of links is navigation, not a passage to point at."""
    lines = [l for l in raw.split("\n") if l.strip()]
    return bool(lines) and all(re.match(r"\s*[*+-]\s+\[[^\]]+\]\([^)]*\)\s*$", l) for l in lines)


def locate_quotes(blocks: list, quotes: list, cap: int = 4):
    """Verbatim check. A block is highlighted only if the model's quote and the block's own text
    contain one another once markup is stripped. A quote found nowhere highlights nothing.
    Quotes arrive in the order the model relied on them, so the first found quote is the focus (the one
    scrolled to) and the highlight is capped, so a click on "Show them" does not light up half the page."""
    picked: list = []
    found = 0
    for q in quotes[:6]:
        nq = _norm(str(q))
        if len(nq.split()) < 3:
            continue
        got = False
        for i, b in enumerate(blocks):
            if not b["html"] or b["nav"]:
                continue
            nb = b["norm"]
            if len(nb.split()) >= 3 and (nq in nb or nb in nq):
                got = True
                if i not in picked and len(picked) < cap:
                    picked.append(i)
        found += got
    focus = picked[0] if picked else None
    return sorted(picked), found, focus


async def load_page(client: httpx.AsyncClient, kb: str, headers: dict, key: str) -> dict:
    if key in _cache:
        return _cache[key]
    label, rid, url = PAGES[key]
    r = await client.get(f"{kb}/resource/{rid}", params=[("show", "extracted"), ("extracted", "text")], headers=headers, timeout=20)
    r.raise_for_status()
    data = r.json().get("data") or {}
    full = ""
    field = ""
    for ftype, fields in data.items():
        for fid, f in fields.items():
            t = (((f.get("extracted") or {}).get("text") or {}).get("text")) or ""
            if ftype in ("links", "texts", "files") and len(t) > len(full):
                full, field = t, f"{ftype[0]}/{fid}"
    h1 = re.search(r"^# .+$", full, re.M)
    ack = re.search(r"^## Acknowledgement of Country", full, re.M)
    if not h1 or not ack or ack.start() < h1.start():
        raise ValueError("page structure not recognised")
    start, end = h1.start(), ack.start()
    blocks = []
    for m in re.finditer(r"(?:(?!\n\s*\n).)+", full[start:end], re.S):
        raw = m.group(0)
        if not raw.strip():
            continue
        blocks.append({"s": start + m.start(), "e": start + m.end(), "html": _block_html(raw), "nav": _is_nav(raw), "norm": _norm(raw)})
    page = {"key": key, "label": label, "url": url, "rid": rid, "field": field, "blocks": blocks, "full": full}
    _cache[key] = page
    return page



# ---- Suggested questions: generated once per (page, language) by a real ask over that page ----------
_CHIPS: dict[str, list] = {}
_CHIP_LOCKS: dict[str, asyncio.Lock] = {}
_CHIP_FILE = Path(__file__).parent / "data" / "page_chips.json"
_SCRIPT = {"zh": r"[\u4e00-\u9fff]{2,}", "ar": r"[\u0600-\u06ff]{3,}"}


def _chips_load():
    try:
        _CHIPS.update(json.loads(_CHIP_FILE.read_text()))
    except Exception:
        pass


def _chips_save():
    try:
        _CHIP_FILE.parent.mkdir(exist_ok=True)
        _CHIP_FILE.write_text(json.dumps(_CHIPS, ensure_ascii=False))
    except Exception:
        pass  # read-only disk: memory cache only


def clean_chips(raw: list, lang: str) -> list:
    out = []
    for q in raw:
        if not isinstance(q, str):
            continue
        q = re.sub(r"^[\s*\-\d.)]+", "", q.strip()).strip(" *")
        if not (6 <= len(q) <= 110) or q in out:
            continue
        if lang in _SCRIPT and not re.search(_SCRIPT[lang], q):
            continue  # asked for this language, got another: do not show it
        out.append(q)
    return out[:3] if len(out) >= 3 else []  # fewer than three usable: show none, never pad


def build_router(*, kb, headers, model, langs, script_ok, has_arabic, templates, clean_title) -> APIRouter:
    router = APIRouter()

    @router.get("/page", response_class=HTMLResponse)
    async def page_view(request: Request):
        return templates.TemplateResponse(request, "page.html", {"pages": [(k, v[0]) for k, v in PAGES.items()]})

    @router.get("/api/page/{key}")
    async def page_body(key: str):
        if key not in PAGES:
            return JSONResponse({"error": "not_found"}, status_code=404)
        async with httpx.AsyncClient() as client:
            try:
                p = await load_page(client, kb, headers, key)
            except Exception:
                return JSONResponse({"error": "upstream"}, status_code=502)
        return {"key": key, "label": p["label"], "url": p["url"],
                "blocks": [{"i": i, "html": b["html"]} for i, b in enumerate(p["blocks"]) if b["html"]]}

    @router.get("/api/page-chips")
    async def page_chips(page: str, lang: str = "en"):
        if page not in PAGES:
            return JSONResponse({"error": "not_found"}, status_code=404)
        if lang not in langs:
            lang = "en"
        ck = f"{page}:{lang}"
        if not _CHIPS:
            _chips_load()
        if ck in _CHIPS:
            return {"chips": _CHIPS[ck]}
        lock = _CHIP_LOCKS.setdefault(ck, asyncio.Lock())
        async with lock:
            if ck in _CHIPS:
                return {"chips": _CHIPS[ck]}
            lname = langs[lang]
            schema = {"name": "page_questions", "description": "Short questions a student would ask about this page", "parameters": {
                "type": "object",
                "properties": {"questions": {"type": "array", "items": {"type": "string"},
                                             "description": f"Exactly three short questions (under 12 words each) a prospective student would ask about THIS page, written in {lname}. Each must be answerable from the page."}},
                "required": ["questions"]}}
            p = {"query": "Propose three short questions a student would ask about this page.", "generative_model": model,
                 "resource_filters": [PAGES[page][1]], "rag_strategies": [{"name": "full_resource"}], "answer_json_schema": schema,
                 "prompt": {"system": f"Write the questions in {lname}."}}
            try:
                async with httpx.AsyncClient() as client:
                    r = await client.post(f"{kb}/ask", json=p, headers=headers, timeout=40)
                aj = r.json().get("answer_json") if r.status_code < 400 else None
                chips = clean_chips((aj or {}).get("questions") or [], lang)
            except Exception:
                return {"chips": []}  # a failure is not cached, so the next view tries again
            if chips:
                _CHIPS[ck] = chips
                _chips_save()
            return {"chips": chips}

    @router.post("/api/page-ask")
    async def page_ask(request: Request):
        body = await request.json()
        key = body.get("page")
        q = str(body.get("q", "")).strip()[:600]
        lang = body.get("lang", "en")
        if key not in PAGES or not q:
            return JSONResponse({"error": "bad_request"}, status_code=400)
        if lang not in langs:
            lang = "en"
        rid = PAGES[key][1]
        lname = langs[lang]
        schema = {"name": "page_answer", "description": "An answer from one page, with the passages it relied on", "parameters": {
            "type": "object",
            "properties": {
                "answer": {"type": "string", "description": f"The answer, written in {lname}, whatever language the page is in. Plain markdown only (bullets with '* '), never HTML. Answer only from the page."},
                "quotes": {"type": "array", "items": {"type": "string"}, "description": "Up to 4 passages copied EXACTLY, word for word, from the page in the page's own language (never translated, never paraphrased), that the answer relies on. Empty if the page does not say."},
            },
            "required": ["answer", "quotes"]}}
        ask_p = {"query": q, "generative_model": model, "resource_filters": [rid],
                 "rag_strategies": [{"name": "full_resource"}], "answer_json_schema": schema,
                 "prompt": {"system": f"Write the answer in {lname}. Copy the quotes exactly from the page, untranslated. " + STYLE}}
        async with httpx.AsyncClient() as client:
            try:
                page, ra = await asyncio.gather(
                    load_page(client, kb, headers, key),
                    client.post(f"{kb}/ask", json=ask_p, headers=headers, timeout=55),
                )
            except httpx.TimeoutException:
                return JSONResponse({"error": "timeout"}, status_code=504)
            except Exception:
                return JSONResponse({"error": "upstream"}, status_code=502)
        if ra.status_code >= 400:
            return JSONResponse({"error": "upstream", "code": ra.status_code}, status_code=502)
        def parse(resp):
            d = resp.json()
            aj = d.get("answer_json") if isinstance(d.get("answer_json"), dict) else {}
            t = str(aj.get("answer") or "").strip()
            t = re.sub(r"</?(ul|ol)>", "\n", t)
            t = re.sub(r"<li>", "\n* ", t)
            t = re.sub(r"<[^>]+>", "", t).strip()
            t = clean_prose(t, lang)
            return d, t, [x for x in (aj.get("quotes") or []) if isinstance(x, str)]

        d, text, quotes = parse(ra)
        # A phone number the page never printed is withheld: one retry, then the whole response is declined.
        if d.get("status") == "success" and text and not phone_guard(text, [page["full"]])[0]:
            try:
                async with httpx.AsyncClient() as client:
                    ra2 = await client.post(f"{kb}/ask", json=ask_p, headers=headers, timeout=55)
                d, text, quotes = parse(ra2) if ra2.status_code < 400 else (d, "", [])
            except Exception:
                text = ""
            if not text or not phone_guard(text, [page["full"]])[0]:
                return {"declined": True, "dir": "ltr", "lang": lang}
        if d.get("status") != "success" or not text:
            return {"declined": True, "dir": "ltr", "lang": lang}
        highlight, found, focus = locate_quotes(page["blocks"], quotes)
        located = bool(highlight)
        plain = re.sub(r"[*_#`]", "", text)
        return {
            "declined": False,
            "answer": text,
            "highlight": highlight,
            "focus": focus,
            "located": located,
            "quotes_offered": len(quotes),
            "quotes_found": found,
            "cite": "found" if located else ("unverified" if quotes else "none"),
            "dir": "rtl" if (lang == "ar" or has_arabic(plain)) else "ltr",
            "lang": lang,
            "lang_ok": script_ok(lang, plain),
            "page": PAGES[key][0],
        }

    return router
