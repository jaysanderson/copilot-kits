"""SemanticSite API. Route names are our own, never the platform's. The platform key stays server-side."""
import json
import time
from pathlib import Path

import hmac
import threading

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from . import ask as askmod
from . import config, pipeline, store, vocab
from .schema import (AmbiguityDecision, ApproveRequest, ConflictAck, AskRequest, AskResponse, CreateSite, ExistingMarkup, Graph, Issue, PageDetail,
                     PageSummary, SiteStatus, Suggestion, Validation)

app = FastAPI(title="SemanticSite", docs_url=None, redoc_url=None, openapi_url=None)


@app.on_event("startup")
def _register_objects():
    if config.KB_URL:
        from . import arag
        arag.ensure_cheap_defaults()
        arag.ensure_search_config()
        arag.ensure_labelsets()


def require_key(x_semanticsite_key: str = Header(default="")):
    """Operator key for every route that starts work, spends a model call or changes review state. Reads stay public."""
    if not config.ACCESS_KEY:
        if config.ALLOW_OPEN:
            return
        raise HTTPException(503, "This instance has no operator key set, so actions that start work are switched off.")
    if not hmac.compare_digest(x_semanticsite_key.encode(), config.ACCESS_KEY.encode()):
        raise HTTPException(401, "An operator key is needed for this action. Browsing is open; starting a crawl, asking a question and approving records are not.")


def _site(sid):
    s = store.get("sites", sid)
    if not s:
        raise HTTPException(404, "Unknown site")
    return s


def _status(s):
    cov, cov_raw = None, None
    c = s.get("counts") or {}
    pool = c.get("discovered") or 0           # every page address seen, from the sitemap or by following links
    if s.get("state") == "ready" and pool:
        cov_raw = round(100 * (c.get("ingested") or 0) / pool, 1)
        # pages we were told not to take (robots, noindex, user patterns, links the user chose not to follow) or that are not web pages are correct outcomes,
        # not failures, so they leave the denominator; a 404 the site lists, or a page we could not reach, stays in it
        directive = {"blocked_by_robots", "noindex", "excluded_by_pattern", "not_html", "private_address", "off_host", "redirected"}
        told_no = {g["url"] for g in (s.get("gaps") or []) if not g["url"].endswith((".xml", ".xml.gz")) and (
            g["reason"] in directive or (g["reason"] == "link_only" and "following links is off" in g.get("detail", "")))}
        permitted = max(pool - len(told_no), 0)
        cov = round(100 * (c.get("ingested") or 0) / permitted, 1) if permitted else None
    return SiteStatus(id=s["id"], root_url=s["root_url"], state=s["state"], detail=s.get("detail", ""), error=s.get("error"),
                      started_at=s["started_at"], finished_at=s.get("finished_at"), counts=c, coverage_percent=cov_raw, permitted_coverage_percent=cov,
                      gaps=s.get("gaps") or [], scope=s.get("scope") or {}, robots=s.get("robots") or {}, cost=({**s["cost"], "notes": pipeline.cost_notes()} if s.get("cost") else {}),
                      structured_data=s.get("structured_data") or {}, entity_counts=s.get("entity_counts") or {},
                      relation_counts=s.get("relation_counts") or {}, conflicts=s.get("conflicts", 0),
                      ambiguities=s.get("ambiguities", 0), platform_graph=s.get("platform_graph") or {},
                      changes=s.get("changes"), seconds_to_first_insight=s.get("seconds_to_first_insight"),
                      dropped=s.get("dropped"), unsupported_dropped=s.get("unsupported_dropped", 0))


@app.get("/api/health")
def health():
    return {"ok": True, "configured": bool(config.KB_URL and config.KB_TOKEN), "commit": config.BUILD_COMMIT}


@app.get("/api/access")
def access(x_semanticsite_key: str = Header(default="")):
    """Lets the interface ask whether a key is needed and whether the one it holds works, without starting anything."""
    gated = bool(config.ACCESS_KEY) or not config.ALLOW_OPEN
    ok = (not gated) or (bool(config.ACCESS_KEY) and hmac.compare_digest(x_semanticsite_key.encode(), config.ACCESS_KEY.encode()))
    return {"gated": gated, "valid": ok}


@app.post("/api/sites", dependencies=[Depends(require_key)])
def create_site(body: CreateSite):
    try:                                    # the address is judged first: a hostile address is refused whether or not anything else is configured
        pipeline.check_address(body.url)
    except ValueError as e:
        raise HTTPException(422, str(e))
    if not config.KB_URL:
        raise HTTPException(503, "The knowledge service is not configured.")
    try:
        sid = pipeline.create_site(body.url, body.include, body.exclude, body.max_pages, body.follow_links)
    except ValueError as e:
        raise HTTPException(422, str(e))
    except RuntimeError as e:
        raise HTTPException(429, str(e))
    return {"id": sid}


@app.get("/api/sites", dependencies=[Depends(require_key)])
def list_sites():
    """The list of every crawl is operator-only: the sites a seller has pointed the crawler at are commercially sensitive. A single site
    is still readable by its (unguessable) id, so a demo link works for someone who was sent one."""
    with store._lock:
        raw = [json.loads(r["data"]) for r in store._db.execute("SELECT data FROM sites").fetchall()]
    return sorted([_status(s) for s in raw], key=lambda s: -s.started_at)


@app.get("/api/sites/{sid}", response_model=SiteStatus)
def site(sid: str):
    return _status(_site(sid))


@app.post("/api/sites/{sid}/recrawl", dependencies=[Depends(require_key)])
def recrawl(sid: str):
    _site(sid)
    try:
        pipeline.start(sid)
    except RuntimeError as e:
        raise HTTPException(409, str(e))
    return {"id": sid, "state": "queued"}


@app.delete("/api/sites/{sid}", dependencies=[Depends(require_key)])
def delete_site(sid: str):
    """Remove a site record, its stored review state and the page text it put in the knowledge base."""
    s = _site(sid)
    if pipeline._running.get(sid):
        raise HTTPException(409, "A run is in progress for this site. Try again when it finishes.")
    rids = [p.get("rid") for p in store.all_("pages", sid) if p.get("rid")]
    removed, failed = 0, 0
    if config.KB_URL:
        from . import arag
        meter = arag.Meter()
        for rid in rids:
            try:
                arag.delete_resource(meter, rid)
                removed += 1
            except arag.ArError as e:
                if e.status == 404:
                    removed += 1
                else:
                    failed += 1
    for t in store.TABLES:
        store.clear(t, sid)
    store.delete("sites", sid)
    return {"ok": True, "site": sid, "knowledge_resources_removed": removed, "knowledge_resources_failed": failed}


def _summary(p, sug):
    issues = []
    for ex in p.get("existing", []):
        issues += [Issue(**i) for i in ex["validation"]["issues"]]
    issues += [Issue(**i) for i in p.get("enrichment_issues", [])]
    return PageSummary(id=p["id"], url=p["url"], title=p.get("title"), status=p.get("status", "failed"), reason=p.get("reason"),
                       http_status=p.get("http_status"), resource_id=p.get("rid"), in_sitemap=p.get("in_sitemap", False),
                       structured_data=p.get("structured_data", "none"), existing_types=p.get("existing_types", []),
                       issues=issues, entity_count=p.get("entity_count", 0),
                       suggestion_status=sug["status"] if sug else None, suggestion_id=sug["id"] if sug else None)


@app.get("/api/sites/{sid}/pages", response_model=list[PageSummary])
def pages(sid: str):
    _site(sid)
    sugs = {s["page_id"]: s for s in store.all_("suggestions", sid)}
    return sorted([_summary(p, sugs.get(p["id"])) for p in store.all_("pages", sid)], key=lambda p: p.url)


@app.get("/api/sites/{sid}/entities", response_model=Graph)
def entities(sid: str):
    _site(sid)
    g = store.get("entities", sid) or {"nodes": [], "edges": [], "conflicts": [], "ambiguities": []}
    return Graph(**g, note="Relationships read from existing markup or navigation are 'extracted'. Those a model read from page text are 'suggested' and need review.")


@app.get("/api/pages/{pid}/schema", response_model=PageDetail)
def page_schema(pid: str):
    p = store.get("pages", pid)
    if not p:
        raise HTTPException(404, "Unknown page")
    sid = p["site_id"]
    sug = store.get("suggestions", f"s-{pid}")
    g = store.get("entities", sid) or {"nodes": [], "edges": []}
    ents = [n for n in g["nodes"] if any(x["page_id"] == pid for x in n["pages"]) and n["type"] != "WebPage"]
    ids = {n["id"] for n in ents}
    rels = [e for e in g["edges"] if e["source"] in ids and (e["provenance"]["source_url"] == p["url"] or any(c["source_url"] == p["url"] for c in e.get("corroboration", [])))]
    ex = [ExistingMarkup(raw=e["raw"], parsed=e["parsed"], validation=Validation(**e["validation"])) for e in p.get("existing", [])]
    return PageDetail(page=_summary(p, sug), source_text=p.get("text", ""), existing=ex,
                      proposed=Suggestion(**sug) if sug else None, open_findings=open_findings(sid, pid), entities=ents, relations=rels)


def _flat(doc):
    """Top-level properties of every node, keyed '<node @id>|<property>' (blank nodes as _:nK)."""
    nodes = [n for n in vocab._iter_nodes(doc) if isinstance(n, dict)]
    out = {}
    for i, n in enumerate(nodes):
        nid = n.get("@id") or f"_:n{i}"
        for k, v in n.items():
            if k != "@context":
                out[f"{nid}|{k}"] = json.dumps(v, sort_keys=True)
    return out


def edit_violations(before, after):
    """The validity gate for the human path. The engine refuses a property whose domain or range does not fit; a reviewer's
    hand edit goes through the same check, for exactly the properties the reviewer added or changed. Pre-existing warnings on
    untouched properties are not this gate's business (they remain warnings to acknowledge)."""
    changed = {c["key"] for c in _diff(before, after) if c["change"] in ("added", "changed")}
    if not changed:
        return []
    nodes = [n for n in vocab._iter_nodes(after) if isinstance(n, dict)]
    by_id = {n["@id"]: n for n in nodes if n.get("@id")}
    out = []
    for i, n in enumerate(nodes):
        nid = n.get("@id") or f"_:n{i}"
        ts = vocab.types_of(n)
        for k, v in n.items():
            if k.startswith("@") or f"{nid}|{k}" not in changed:
                continue
            p = vocab.PROPS.get(k)
            if p is None:
                continue                                  # unknown_property is already an error in validate_doc
            label = n.get("name") or nid
            if ts and not any(set(p["dom"]) & vocab.ancestors(t) for t in ts if t in vocab.TYPES):
                out.append({"node": nid, "property": k, "reason": f"'{k}' is not valid on {'/'.join(ts)} ({label}); it belongs on {', '.join(p['dom'][:3])}."})
                continue
            for item in (v if isinstance(v, list) else [v]):
                target = item if isinstance(item, dict) and set(item) != {"@id"} else by_id.get(item.get("@id")) if isinstance(item, dict) else None
                if target is None:
                    continue
                tts = [x for x in vocab.types_of(target) if x in vocab.TYPES]
                inner = target.get("itemOffered") if isinstance(target.get("itemOffered"), dict) else None
                if inner is not None and "Offer" in tts:
                    continue
                if tts and not any(vocab.edge_valid(k, ts[0] if ts else "Thing", x)[0] for x in tts):
                    out.append({"node": nid, "property": k, "reason": f"'{k}' on {'/'.join(ts)} ({label}) cannot point to a {'/'.join(tts)}."})
    return out


def _diff(before, after):
    b, a_ = _flat(before), _flat(after)
    return ([{"key": k, "change": "added"} for k in a_ if k not in b] + [{"key": k, "change": "changed"} for k in a_ if k in b and a_[k] != b[k]]
            + [{"key": k, "change": "removed"} for k in b if k not in a_])


def open_findings(sid, pid):
    """Unsettled findings that bear on THIS record: a conflict in which this page is one of the parties, and an ambiguous
    match involving an entity the record actually names. (A conflict about something merely mentioned here belongs to the
    pages that state it.)"""
    from .resolve import norm_name
    g = store.get("entities", sid) or {}
    sug = store.get("suggestions", f"s-{pid}") or {}
    named = {norm_name(str(n.get("name"))) for n in vocab._iter_nodes(sug.get("jsonld") or {}) if isinstance(n, dict) and n.get("name")}
    out = []
    for c in g.get("conflicts", []):
        if not c.get("acknowledged") and any(v["page_id"] == pid for v in c["values"]):
            out.append({"kind": "conflict", "id": c["id"], "text": f"{c['entity_label']}: '{c['property']}' is stated differently in more than one place."})
    for x in g.get("ambiguities", []):
        if x["status"] == "needs_review" and any(norm_name(lbl) in named for lbl in x["labels"]):
            out.append({"kind": "ambiguity", "id": x["id"], "text": x["reason"]})
    return out


@app.post("/api/pages/{pid}/schema/approve", dependencies=[Depends(require_key)])
def approve(pid: str, body: ApproveRequest):
    sug = store.get("suggestions", f"s-{pid}")
    if not sug:
        raise HTTPException(404, "There is no proposal for this page.")
    if body.decision == "reject":
        sug = store.update("suggestions", sug["id"], status="rejected", decided_at=time.time())
        return Suggestion(**sug)
    doc = body.jsonld if body.jsonld is not None else sug["jsonld"]
    if isinstance(doc, str):
        parsed, val = vocab.parse(doc)
        doc = parsed
    else:
        val = vocab.validate_doc(doc)
    if doc is None or not val.valid:
        raise HTTPException(422, {"message": "This JSON-LD has errors and cannot be approved.", "validation": val.model_dump()})
    page = store.get("pages", pid) or {}
    # A review step must surface the product's own findings at the moment of decision: unsettled conflicts and ambiguous
    # matches touching this page's entities block approval until a reviewer has settled them; warnings need an explicit acknowledgement.
    findings = open_findings(page.get("site_id", ""), pid)
    if findings:
        raise HTTPException(409, {"message": "This page has open findings. Settle each one (merge or keep separate; acknowledge a conflict) before approving.",
                                  "findings": findings})
    warns = [i.model_dump() for i in val.issues if i.severity == "warning"]
    if warns and not body.acknowledge_warnings:
        raise HTTPException(409, {"message": "This record has validation warnings. Approve again with acknowledge_warnings once you have read them.", "warnings": warns})
    changes = _diff(sug.get("proposed_jsonld") or sug["jsonld"], doc)
    edited = bool(changes) and body.jsonld is not None
    if edited:
        bad = edit_violations(sug.get("proposed_jsonld") or sug["jsonld"], doc)
        if bad:
            raise HTTPException(422, {"message": "Your edit adds a property the Schema.org vocabulary does not allow there, so it cannot be approved. The product checks a hand edit exactly as it checks its own proposals.",
                                      "violations": bad, "validation": Validation(valid=False, issues=val.issues + [
                                          Issue(severity="error", code="property_not_valid_for_type", message=x["reason"], path=f"{x['node']}.{x['property']}") for x in bad]).model_dump()})
    sug = store.update("suggestions", sug["id"], jsonld=doc, validation=val.model_dump(), edited=sug.get("edited") or edited,
                       reviewer_changes=changes if edited else sug.get("reviewer_changes", []), warnings_acknowledged=bool(warns),
                       status="approved", decided_at=time.time())
    return Suggestion(**sug)


@app.post("/api/sites/{sid}/conflicts/{cid}/acknowledge", dependencies=[Depends(require_key)])
def acknowledge_conflict(sid: str, cid: str, body: ConflictAck):
    """A reviewer records that they have seen a disagreement between pages and decided how to proceed."""
    _site(sid)
    g = store.get("entities", sid) or {}
    if not any(c["id"] == cid for c in g.get("conflicts", [])):
        raise HTTPException(404, "Unknown conflict")
    store.put("decisions", f"{sid}:{cid}", sid, {"kind": "conflict", "cid": cid, "note": body.note[:500]})
    g = pipeline.republish(sid)
    return {"ok": True, "conflicts": g["conflicts"]}


@app.post("/api/sites/{sid}/ambiguities/{aid}/decision", dependencies=[Depends(require_key)])
def decide_ambiguity(sid: str, aid: str, body: AmbiguityDecision):
    """A reviewer settles an ambiguous entity match: merge the two into one entity, or keep them separate."""
    _site(sid)
    g = store.get("entities", sid) or {}
    amb = next((x for x in g.get("ambiguities", []) if x["id"] == aid), None)
    if not amb:
        raise HTTPException(404, "Unknown ambiguity")
    from .resolve import norm_name
    a, b = amb.get("keys") or [norm_name(x) for x in amb["labels"]]
    store.put("decisions", f"{sid}:{aid}", sid, {"a": a, "b": b, "decision": body.decision})
    g = pipeline.republish(sid)
    return {"ok": True, "decision": body.decision, "ambiguities": g["ambiguities"]}


@app.get("/api/sites/{sid}/export")
def export(sid: str):
    s = _site(sid)
    pgs = {p["id"]: p for p in store.all_("pages", sid)}
    recs, excluded = [], []
    for sug in store.all_("suggestions", sid):
        if sug["status"] != "approved":
            continue
        val = vocab.validate_doc(sug["jsonld"])          # re-validated at the moment of export
        if not val.valid:
            excluded.append({"page_url": pgs[sug["page_id"]]["url"], "reason": "failed validation at export"})
            continue
        recs.append({"page_url": pgs[sug["page_id"]]["url"], "jsonld": sug["jsonld"], "approved_at": sug.get("decided_at"),
                     "edited_by_reviewer": sug.get("edited", False), "reviewer_changes": sug.get("reviewer_changes", []),
                     "provenance_file": f"/api/sites/{sid}/export/provenance"})
    body = {"site": s["root_url"], "generated_at": time.time(), "approved_only": True, "record_count": len(recs),
            "records": sorted(recs, key=lambda r: r["page_url"]), "excluded": excluded,
            "note": "Each record is one page's JSON-LD. Records refer to each other by @id (for example an organisation's offers point at product records on other pages), "
                    "so a single record validated on its own shows those references as unresolved. They resolve once the pages are published together on the site."}
    return JSONResponse(body, headers={"Content-Disposition": f'attachment; filename="semanticsite-{sid}.json"'})


def _prov_rows(doc, url, pp, pe, changed):
    """One row per property occurrence in the record, at every depth. A nested property inherits the origin and the quotes
    of the nearest ancestor property that has a record; where there is none the row says 'not_recorded' in its own label."""
    rows = []

    def lookup(table, ids, dotted):
        parts = dotted.split(".")
        for cut in range(len(parts), 0, -1):                 # the property itself, then each ancestor
            for nid in ids:
                k = f"{nid}|{'.'.join(parts[:cut])}"
                if k in table:
                    return k, table[k], cut < len(parts)
        return None, None, False

    def walk(ids, node, path, prefix):
        for k, v in node.items():
            if k == "@context":
                continue
            dotted, shown = f"{prefix}{k}", f"{path}{k}"
            key, origin, inherited = lookup(pp, ids, dotted)
            top = dotted.split(".")[0]
            ch = next((changed.get(f"{nid}|{top}") for nid in ids if changed.get(f"{nid}|{top}")), None)
            kind = "reviewer" if ch in ("added", "changed") else (origin or "not_recorded")
            _, ev, _ = lookup(pe, ids, dotted)
            rows.append({"page_url": url, "node": ids[0], "property": shown, "provenance": kind, "inherited_from_parent": bool(inherited),
                         "change_by_reviewer": ch, "source_url": url,
                         "quotes": [{"quote": q["quote"], "source_url": q["source_url"], "verified_on_page": q["verified"]} for q in (ev or [])]})
            for n_, item in enumerate(v if isinstance(v, list) else [v]):
                if isinstance(item, dict) and set(item) != {"@id"}:
                    walk(ids, item, f"{shown}[{n_}]." if isinstance(v, list) else f"{shown}.", f"{dotted}.")

    for i, n in enumerate([x for x in vocab._iter_nodes(doc) if isinstance(x, dict)]):
        nid = n.get("@id") or f"_:n{i}"
        # the engine keys the breadcrumb it derives from page structure as _:breadcrumb, not by position
        ids = [nid, "_:breadcrumb"] if nid.startswith("_:") and "BreadcrumbList" in vocab.types_of(n) else [nid]
        walk(ids, n, "", "")
    return rows


@app.get("/api/sites/{sid}/export/provenance")
def export_provenance(sid: str):
    """Companion to the export: for every property occurrence in every approved record, at every depth, where it came from.
    An agency hands a client a file, not a login, so the evidence travels with the markup."""
    s = _site(sid)
    pgs = {p["id"]: p for p in store.all_("pages", sid)}
    rows = []
    for sug in store.all_("suggestions", sid):
        if sug["status"] != "approved" or not vocab.validate_doc(sug["jsonld"]).valid:
            continue
        url = pgs[sug["page_id"]]["url"]
        changed = {c["key"]: c["change"] for c in sug.get("reviewer_changes", [])}
        rows += _prov_rows(sug["jsonld"], url, sug.get("property_provenance", {}), sug.get("property_evidence", {}), changed)
        for key, ch in changed.items():
            if ch == "removed":
                nid, prop = key.split("|", 1)
                rows.append({"page_url": url, "node": nid, "property": prop, "provenance": "removed by reviewer", "inherited_from_parent": False,
                             "change_by_reviewer": "removed", "quotes": [], "source_url": url})
    body = {"site": s["root_url"], "generated_at": time.time(), "row_count": len(rows),
            "kinds": {"extracted": "read from markup already on the page", "suggested": "proposed by a model from page text; the quote is on the page",
                      "derived": "built by the product from the shape of the page (for example a breadcrumb trail from the visible HTML); the page carried no markup for it, and a model did not propose it",
                      "reviewer": "added or changed by the person who approved the record",
                      "not_recorded": "the product holds no record of where this came from; it is NOT claimed to be extracted",
                      "removed by reviewer": "taken out by the person who approved the record"},
            "note": "One row per property occurrence at every depth. A nested property (for example offers[0].price) carries inherited_from_parent: true when its origin is taken from the property that contains it.",
            "rows": rows}
    return JSONResponse(body, headers={"Content-Disposition": f'attachment; filename="semanticsite-{sid}-provenance.json"'})


_q_lock = threading.Lock()
_q_visitors = {}          # visitor -> timestamps of questions in the last hour
_q_all = []               # timestamps of every question in the last hour


def _key_ok(k):
    return bool(config.ACCESS_KEY) and hmac.compare_digest((k or "").encode(), config.ACCESS_KEY.encode())


def question_allowance(visitor, has_key, now=None):
    """Questions are open to a visitor with the link, within a per-visitor limit and a global hourly ceiling. A visitor holding the
    operator key passes the per-visitor limit; the ceiling still applies to everyone. Raises 429 with a plain sentence."""
    now = now or time.time()
    with _q_lock:
        cut = now - 3600
        _q_all[:] = [x for x in _q_all if x > cut]
        mine = [x for x in _q_visitors.get(visitor, []) if x > cut]
        _q_visitors[visitor] = mine
        if len(_q_all) >= config.QUESTION_HOURLY_CEILING:
            raise HTTPException(429, "This demo has reached its hourly question allowance. Try again later.")
        if not has_key and len(mine) >= config.QUESTIONS_PER_VISITOR_HOUR:
            wait = max(1, int((mine[0] + 3600 - now) / 60) + 1)
            raise HTTPException(429, f"This demo allows {config.QUESTIONS_PER_VISITOR_HOUR} questions an hour per visitor. You can ask again in about {wait} minute{'s' if wait != 1 else ''}.")
        mine.append(now)
        _q_all.append(now)


@app.post("/api/question", response_model=AskResponse)
def ask(body: AskRequest, request: Request, x_semanticsite_key: str = Header(default="")):
    _site(body.site_id)
    visitor = (request.headers.get("fly-client-ip") or (request.headers.get("x-forwarded-for") or "").split(",")[0].strip()
               or (request.client.host if request.client else "unknown"))
    q = body.question.strip()
    if not 3 <= len(q) <= 500:
        raise HTTPException(422, "Ask a question of 3 to 500 characters.")
    question_allowance(visitor, _key_ok(x_semanticsite_key))
    return askmod.answer(body.site_id, q)


# The interface (web/) is owned by another module and mounted here. Its routes are named for user tasks.
import sys  # noqa: E402

sys.path.insert(0, str(config.ROOT))
try:
    from web import router as _web  # noqa: E402
    app.include_router(_web.router)
    app.mount("/static", _web.static_app, name="static")
except ImportError:                      # API-only run (no interface present)
    _web = None


@app.get("/{path:path}", include_in_schema=False)
def unknown(path: str):
    if path.startswith("api/"):
        return JSONResponse({"error": "not found"}, status_code=404)
    if _web is None:
        return JSONResponse({"service": "SemanticSite API", "interface": "not present"})
    from fastapi.responses import RedirectResponse
    return RedirectResponse("/?notice=notfound", status_code=302)
