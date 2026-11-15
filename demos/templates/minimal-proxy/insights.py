"""Visitor-question insights: a log of what people actually asked, and a surface over it.

Additive module. InsightsLogger is a pure ASGI middleware that wraps POST /api/answer and
POST /api/page-ask from OUTSIDE: it times the call and reads the JSON the app already returns
(`declined` is the server's own label). Nothing inside those handlers changes.

Stored per ask: timestamp, question text (<=600 chars), chosen language, outcome, number of
sources, cited titles/urls, milliseconds, scope (site or page) and a provenance flag. Never
read or stored: IP address, user agent, cookies, headers other than the driver key, session id.
"""
import json
import os
import sqlite3
import statistics
import time
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

HERE = Path(__file__).parent
DB_PATH = Path(os.environ.get("INSIGHTS_DB", HERE / "data" / "insights.db"))
# Rows from the team's own driver script carry this header; the value must match the env key,
# so a stray visitor cannot mislabel themselves. Unset key: nothing is ever flagged 'team'.
DRIVER_KEY = os.environ.get("INSIGHTS_DRIVER_KEY", "")
WATCHED = {"/api/answer": "site", "/api/page-ask": "page"}
LANG_NAMES = {"en": "English", "zh": "Chinese", "ar": "Arabic", "id": "Bahasa Indonesia"}

_SCHEMA = """CREATE TABLE IF NOT EXISTS asks(
 id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL NOT NULL, q TEXT NOT NULL, lang TEXT NOT NULL,
 outcome TEXT NOT NULL, n_sources INTEGER NOT NULL, sources TEXT NOT NULL, ms INTEGER NOT NULL,
 scope TEXT NOT NULL, page TEXT, source TEXT NOT NULL)"""


def _db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB_PATH, timeout=5)
    c.execute(_SCHEMA)
    return c


def record(**r) -> None:
    try:
        with _db() as c:
            c.execute("INSERT INTO asks(ts,q,lang,outcome,n_sources,sources,ms,scope,page,source) VALUES(?,?,?,?,?,?,?,?,?,?)",
                      (r["ts"], r["q"], r["lang"], r["outcome"], r["n_sources"], json.dumps(r["sources"]),
                       r["ms"], r["scope"], r.get("page"), r["source"]))
    except Exception:
        pass  # logging must never break an answer


class InsightsLogger:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        path = scope.get("path")
        if scope["type"] != "http" or scope.get("method") != "POST" or path not in WATCHED:
            return await self.app(scope, receive, send)
        chunks = []
        while True:
            m = await receive()
            chunks.append(m.get("body", b""))
            if not m.get("more_body"):
                break
        raw = b"".join(chunks)
        sent = False

        async def replay():
            nonlocal sent
            if not sent:
                sent = True
                return {"type": "http.request", "body": raw, "more_body": False}
            return await receive()

        driver = False
        for k, v in scope.get("headers", []):
            if k == b"x-insights-source" and DRIVER_KEY and v.decode("latin1") == DRIVER_KEY:
                driver = True
        t0 = time.time()
        status, body = 0, []

        async def tap(msg):
            nonlocal status
            if msg["type"] == "http.response.start":
                status = msg["status"]
            elif msg["type"] == "http.response.body":
                body.append(msg.get("body", b""))
            await send(msg)

        await self.app(scope, replay, tap)
        try:
            req = json.loads(raw or b"{}")
            q = str(req.get("q", "")).strip()[:600]
            if not q:
                return
            lang = req.get("lang", "en")
            if lang not in LANG_NAMES:
                lang = "en"
            resp = {}
            try:
                resp = json.loads(b"".join(body) or b"{}")
            except Exception:
                pass
            if status >= 400:
                if status == 400:
                    return  # malformed ask, not a visitor question
                outcome, sources = "error", []
            elif resp.get("declined"):
                outcome, sources = "declined", []
            else:
                outcome = "answered"
                sources = [{"title": s.get("title", ""), "url": s.get("url", "")} for s in resp.get("sources", [])]
                if WATCHED[path] == "page":
                    sources = [{"title": resp.get("page", ""), "url": ""}]
            record(ts=t0, q=q, lang=lang, outcome=outcome, n_sources=len(sources), sources=sources,
                   ms=int((time.time() - t0) * 1000), scope=WATCHED[path],
                   page=req.get("page") if WATCHED[path] == "page" else None,
                   source="team" if driver else "visitor")
        except Exception:
            pass


def _section(url: str) -> str:
    segs = [s for s in urlparse(url).path.split("/") if s]
    if not segs:
        return "Home"
    return " / ".join(segs[:2]).replace("-", " ").capitalize()


def _group(rows: list[dict]) -> list[dict]:
    """One entry per distinct question (same text and language, ignoring case, spacing and
    trailing punctuation), newest first. Display only: the log keeps every row."""
    import re
    out: dict[tuple, dict] = {}
    for r in rows:  # rows arrive newest first
        key = (re.sub(r"[\s?.!\u3002\uff1f\uff01\u061f]+$", "", " ".join(r["q"].casefold().split())), r["lang"])
        g = out.get(key)
        if g is None:
            out[key] = {**r, "count": 1, "sources_set": {r["source"]}}
        else:
            g["count"] += 1
            g["sources_set"].add(r["source"])
    for g in out.values():
        # a group is 'team' only if every row in it is; otherwise a mixed group shows as direct
        g["source"] = "team" if g["sources_set"] == {"team"} else "visitor"
    return list(out.values())


def summarise() -> dict:
    with _db() as c:
        c.row_factory = sqlite3.Row
        rows = [dict(r) for r in c.execute("SELECT * FROM asks ORDER BY ts DESC")]
    for r in rows:
        r["sources"] = json.loads(r["sources"])
    n = len(rows)
    ok = [r for r in rows if r["outcome"] != "error"]
    declined = [r for r in ok if r["outcome"] == "declined"]
    answered = [r for r in ok if r["outcome"] == "answered"]
    errors = [r for r in rows if r["outcome"] == "error"]
    langs = Counter(r["lang"] for r in rows)
    lang_decl = Counter(r["lang"] for r in declined)
    pages = Counter()
    sections: dict[str, list] = {}
    for r in answered:
        if r["scope"] != "site":
            continue
        seen = set()
        for s in r["sources"]:
            if s["url"] and s["url"] not in seen:
                seen.add(s["url"])
                pages[(s["title"], s["url"])] += 1
        top = next((s for s in r["sources"] if s["url"]), None)
        if top:
            sections.setdefault(_section(top["url"]), []).append(r)
    sections = {k: _group(v) for k, v in sections.items()}
    ms = sorted(r["ms"] for r in ok)
    timing = None
    if ms:
        timing = {"n": len(ms), "median": int(statistics.median(ms)), "max": ms[-1],
                  "p90": ms[min(len(ms) - 1, int(len(ms) * 0.9))] if len(ms) >= 10 else None}
    return {
        "declined_groups": _group(declined),
        "answered_distinct": len(_group(answered)),
        "n": n, "n_team": sum(r["source"] == "team" for r in rows), "n_visitor": sum(r["source"] == "visitor" for r in rows),
        "answered": answered, "declined": declined, "errors": errors, "n_page": sum(r["scope"] == "page" for r in rows),
        "first": min((r["ts"] for r in rows), default=None), "last": max((r["ts"] for r in rows), default=None),
        "langs": [(LANG_NAMES[k], v, lang_decl.get(k, 0)) for k, v in langs.most_common()],
        "pages": pages.most_common(10),
        "sections": sorted(sections.items(), key=lambda kv: -len(kv[1])),
        "timing": timing,
    }


def build_router(*, templates) -> APIRouter:
    router = APIRouter()

    @router.get("/insights", response_class=HTMLResponse)
    async def insights_view(request: Request):
        return templates.TemplateResponse(request, "insights.html", {"s": summarise(), "ts_fmt": _fmt, "now": time.time()})

    return router


def _fmt(ts: float) -> str:
    import datetime as dt
    return dt.datetime.fromtimestamp(ts, dt.timezone(dt.timedelta(hours=8))).strftime("%-d %b %Y, %-I:%M %p AWST")


if __name__ == "__main__":
    # Reset tool. Run on the host that owns the log, e.g.
    #   fly ssh console -a university-demo -C "python insights.py --all"
    # Clears ROWS of the asks table only (the file, schema and volume stay). Prints counts.
    import argparse
    ap = argparse.ArgumentParser(description="Clear rows from the insights log.")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--all", action="store_true", help="delete every row")
    g.add_argument("--source", choices=["team", "visitor"], help="delete rows with this provenance flag")
    g.add_argument("--like", metavar="TEXT", help="delete rows whose question contains TEXT (case-insensitive)")
    g.add_argument("--count", action="store_true", help="delete nothing, print counts")
    a = ap.parse_args()
    with _db() as c:
        before = c.execute("SELECT source, COUNT(*) FROM asks GROUP BY source").fetchall()
        if a.all:
            c.execute("DELETE FROM asks")
        elif a.source:
            c.execute("DELETE FROM asks WHERE source=?", (a.source,))
        elif a.like:
            c.execute("DELETE FROM asks WHERE q LIKE ?", (f"%{a.like}%",))
        after = c.execute("SELECT source, COUNT(*) FROM asks GROUP BY source").fetchall()
    print(f"db={DB_PATH}\nbefore={dict(before)}\nafter={dict(after)}")
