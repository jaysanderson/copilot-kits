"""Orchestration: discover -> crawl -> extract (free) -> ingest -> infer (model) -> resolve -> suggest.

Stages that cost nothing run first and publish results immediately, so the first useful insight
arrives before any model call. Only prose-only knowledge goes to a model."""
import hashlib
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

from . import arag, config, extract, infer, knowledge, resolve, store, suggest, vocab
from .crawler import Crawler, matches, norm
from .resolve import norm_name
from .schema import Cost, CrawlGap

SKIP_EXT = (".pdf", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".zip", ".mp4", ".mp3", ".css", ".js", ".xml", ".ico", ".woff", ".woff2", ".docx", ".xlsx")
_running = {}


def pid_for(sid, url):
    """Page ids are scoped to the site. (Keyed on the URL alone, two sites that crawled the same address overwrote each
    other's page records and the older site silently lost its pages.)"""
    return hashlib.sha1(f"{sid}|{url}".encode()).hexdigest()[:12]


def sget(site_id):
    return store.get("sites", site_id)


def sset(site_id, **kw):
    d = sget(site_id)
    d.update(kw)
    store.put("sites", site_id, site_id, d)
    return d


_budget = {"window": 0.0, "pages": 0}
_budget_l = threading.Lock()


def check_address(url):
    """Raises ValueError (with a sentence for the reader) unless this is a public http(s) address."""
    p = urlparse(url if "://" in url else "https://" + url)
    if p.scheme not in ("http", "https") or not p.netloc or not p.hostname:
        raise ValueError("Enter a full web address, for example https://example.com or a sitemap URL.")
    if any(ch.isspace() for ch in url.strip()) or (not config.ALLOW_PRIVATE_HOSTS and "." not in p.hostname and ":" not in p.hostname):
        raise ValueError("Enter a full web address, for example https://example.com or a sitemap URL.")
    from .crawler import private_address
    if not config.ALLOW_PRIVATE_HOSTS and private_address(p.hostname):
        raise ValueError("That address is on a private network. SemanticSite only reads public websites.")
    return p


def create_site(url, include, exclude, max_pages, follow_links=False):
    p = check_address(url)
    if len(_running) >= config.MAX_CONCURRENT_RUNS:
        raise RuntimeError("Several sites are being read right now. Try again in a few minutes.")
    want = max(1, min(int(max_pages or config.DEFAULT_MAX_PAGES), config.MAX_PAGES_CAP))
    with _budget_l:                                  # cost safety: a public instance cannot be driven to unbounded spend
        if time.time() - _budget["window"] > 3600:
            _budget.update(window=time.time(), pages=0)
        if _budget["pages"] + want > config.HOURLY_PAGE_BUDGET:
            raise RuntimeError("This demo has reached its hourly page allowance. Try again later.")
        _budget["pages"] += want
    sid = store.new_id()
    doc = {"id": sid, "root_url": p.geturl(), "state": "queued", "detail": "Queued", "error": None, "started_at": time.time(),
           "finished_at": None, "include": include, "exclude": exclude, "follow_links": bool(follow_links),
           "max_pages": want,
           "counts": {}, "gaps": [], "robots": {}, "cost": {}, "runs": 0}
    store.put("sites", sid, sid, doc)
    start(sid)
    return sid


def start(sid):
    if _running.get(sid):
        raise RuntimeError("A run is already in progress for this site.")
    t = threading.Thread(target=_guard, args=(sid,), daemon=True)
    _running[sid] = t
    t.start()


def _refund(sid):
    """Return the unused part of the hourly page allowance: a 12-page site should not cost a 100-page reservation."""
    s = sget(sid) or {}
    used = (s.get("counts") or {}).get("fetched", 0)
    with _budget_l:
        _budget["pages"] = max(0, _budget["pages"] - max(0, s.get("max_pages", 0) - used))


def _guard(sid):
    try:
        run(sid)
    except Exception as e:  # noqa: BLE001 - surface any failure on the site, never a silent death
        traceback.print_exc()
        sset(sid, state="failed", error=f"{e.__class__.__name__}: {str(e)[:300]}", finished_at=time.time())
    finally:
        _refund(sid)
        _running.pop(sid, None)


# -------------------------------------------------------------------------------------------------------
def run(sid):
    site = sget(sid)
    t0 = time.time()
    meter = arag.Meter()
    prev = {p["url"]: p for p in store.all_("pages", sid)}
    is_recrawl = bool(prev)
    sset(sid, state="discovering", detail="Reading robots.txt and sitemaps", error=None, finished_at=None,
         started_at=t0, runs=site.get("runs", 0) + 1)

    crawler = Crawler(site["root_url"])
    gaps, seen, queue = [], {}, []
    in_sitemap = set()

    def gap(url, reason, detail="", ins=False):
        if not any(g["url"] == url and g["reason"] == reason for g in gaps):
            gaps.append({"url": url, "reason": reason, "detail": detail, "in_sitemap": ins})

    # ---- discover ------------------------------------------------------------------------------------
    root = site["root_url"]
    cands = []
    if urlparse(root).path.lower().endswith((".xml", ".xml.gz")):
        smaps = [root]
    else:
        smaps = crawler.robots["sitemaps"] or [f"{crawler.base}/sitemap.xml"]
    sm_notes = []
    for sm in smaps:
        urls, notes = crawler.sitemap_urls(sm)
        cands += urls
        sm_notes += notes
    for n in sm_notes:
        reason = "not_found" if "404" in n["problem"] else "blocked_by_robots" if "robots" in n["problem"] else "fetch_failed"
        gap(n["url"], reason, f"Sitemap problem: {n['problem']}", ins=False)
    for u in cands:
        if not crawler.same_site(urlparse(u).netloc):
            gap(u, "off_host", "Listed in the sitemap but on a different host; not fetched.", True)
            continue
        in_sitemap.add(u)
        queue.append(u)
    if not urlparse(root).path.lower().endswith((".xml", ".xml.gz")):
        seed = norm(root)                                   # the address the user typed is always read first
        queue.insert(0, seed)
        in_sitemap.discard(seed) if seed not in cands else None
    queue = list(dict.fromkeys(queue))
    # Scope is an explicit choice: the sitemap's pages (plus the address typed), or also pages reached by following links.
    # A site with no usable sitemap has nothing else to go on, so links are followed and the scope says so.
    follow = bool(site.get("follow_links")) or not cands
    mode = "sitemap + links" if site.get("follow_links") else ("links (no sitemap found)" if not cands else "sitemap only")
    typed = norm(root)
    linked_only = set()
    sset(sid, scope={"mode": mode, "sitemap_urls": len(cands), "follows_links": follow,
                     "estimate": f"{len(queue)} addresses to read" + ("" if not follow else " plus pages reached by following links")},
         state="discovering", robots={**crawler.robots, "user_agent": config.USER_AGENT, "delay_seconds": crawler.delay},
         counts={"discovered": len(queue), "in_sitemap": len(in_sitemap)}, detail=f"{len(queue)} URLs discovered")

    # ---- crawl ---------------------------------------------------------------------------------------
    pages = {}
    cap = site["max_pages"]
    sset(sid, state="crawling")
    i = 0
    while i < len(queue):
        url = queue[i]
        i += 1
        if url in pages:
            continue                                            # already read (for example as the target of a redirect)
        ins = url in in_sitemap
        if site["include"] and not matches(url, site["include"]):
            gap(url, "excluded_by_pattern", "Does not match an include pattern.", ins)
            continue
        if site["exclude"] and matches(url, site["exclude"]):
            gap(url, "excluded_by_pattern", "Matches an exclude pattern.", ins)
            continue
        if sum(1 for p in pages.values() if p["status"] == "fetched") >= cap:
            gap(url, "over_page_cap", f"Page limit of {cap} reached.", ins)
            continue
        if not crawler.allowed(url):
            gap(url, "blocked_by_robots", "Disallowed by robots.txt; not fetched.", ins)
            continue
        r = crawler.fetch(url)
        pid = pid_for(sid, url)
        rec = {"id": pid, "site_id": sid, "url": url, "in_sitemap": ins, "http_status": r.status, "status": "failed", "reason": None}
        if r.error:
            gap(url, r.error if r.error in ("blocked_by_robots", "off_host", "private_address") else "fetch_failed", r.headers.get("_err", r.error), ins)
            rec["reason"] = r.error
            pages[url] = rec
            continue
        if r.status == 404 or r.status == 410:
            gap(url, "not_found", f"HTTP {r.status}", ins)
            rec["reason"] = "not_found"
            pages[url] = rec
            continue
        if r.status != 200:
            gap(url, "http_error", f"HTTP {r.status}", ins)
            rec["reason"] = "http_error"
            pages[url] = rec
            continue
        if "html" not in r.ctype.lower():
            gap(url, "not_html", r.ctype, ins)
            rec["reason"] = "not_html"
            pages[url] = rec
            continue
        fin = norm(r.final)
        if fin != norm(url):                                    # the address redirected: the page lives at its final address
            gap(url, "redirected", f"Redirects to {fin}; the page is read there, not twice.", ins)
            rec.update(status="excluded", reason="redirected")
            pages[url] = rec
            if fin in pages or not crawler.same_site(urlparse(fin).netloc):
                continue
            url = fin
            rec = {"id": pid_for(sid, url), "site_id": sid, "url": url, "in_sitemap": ins or fin in in_sitemap, "http_status": r.status,
                   "status": "failed", "reason": None}
            pid = rec["id"]
        html = r.body.decode("utf-8", "replace")
        info = extract.parse_page(html, url)
        xrt = (r.headers.get("x-robots-tag") or "").lower()
        if "noindex" in info["robots"] or "noindex" in xrt:
            gap(url, "noindex", "Page asks not to be indexed (robots meta or header); respected.", ins)
            rec["status"], rec["reason"] = "excluded", "noindex"
            pages[url] = rec
            continue
        truncated = len(info["text"]) > config.MAX_TEXT_CHARS
        if truncated:
            info["text"] = info["text"][:config.MAX_TEXT_CHARS]
        rec.update(status="fetched", truncated=truncated, title=info["title"], text=info["text"], canonical=info["canonical"],
                   content_hash=hashlib.sha1(info["text"].encode()).hexdigest()[:16],
                   jsonld_raw=info["jsonld_raw"], breadcrumb_html=info["breadcrumb_html"], nav_tree=info["nav_tree"],
                   microdata_present=info["microdata_present"])
        pages[url] = rec
        for link, _t in info["links"]:                                     # follow same-host links
            link = norm(link)
            if not crawler.same_site(urlparse(link).netloc) or link.lower().split("?")[0].endswith(SKIP_EXT):
                continue
            if link not in in_sitemap and link not in queue and link not in pages and link not in linked_only:
                if follow:
                    queue.append(link)
                elif len(linked_only) < 200:
                    linked_only.add(link)
                    gap(link, "link_only", "Linked from a page but not in the sitemap; not read because following links is off.", False)
        sset(sid, detail=f"Fetched {sum(1 for p in pages.values() if p['status'] == 'fetched')} pages",
             counts={"discovered": len(queue), "in_sitemap": len(in_sitemap),
                     "fetched": sum(1 for p in pages.values() if p["status"] == "fetched")})
    for u in queue:
        if u not in in_sitemap and u != typed and u in pages and pages[u]["status"] == "fetched":
            gap(u, "link_only", "Found by following links; not listed in the sitemap.", False)
    sset(sid, gaps=gaps)

    crawler.close()
    if not any(r["status"] == "fetched" for r in pages.values()):
        why = {"blocked_by_robots": "robots.txt does not allow SemanticSiteBot to fetch it",
               "fetch_failed": "the site could not be reached", "not_found": "the address returned not found",
               "http_error": "the site returned an error", "not_html": "the address is not a web page", "private_address": "the address is on a private network",
               "noindex": "the pages ask not to be indexed"}
        rs = [g["reason"] for g in gaps]
        top = next((r for r in ("blocked_by_robots", "private_address", "noindex", "http_error", "not_found", "not_html") if r in rs), "fetch_failed")
        sset(sid, state="failed", error=f"No pages could be read: {why.get(top, top)}.", gaps=gaps, finished_at=time.time(),
             counts=counts_of(pages, gaps, in_sitemap, queue), robots={**crawler.robots, "user_agent": config.USER_AGENT, "delay_seconds": crawler.delay})
        return

    # ---- deterministic extraction (zero model cost) -----------------------------------------------------
    sset(sid, state="extracting", detail="Reading existing structured data and page structure")
    fetched = [p for p in pages.values() if p["status"] == "fetched"]
    defined_ids, doc_refs = set(), {}
    mentions, rels = [], []
    key2name = {}
    for p in fetched:
        p["existing"] = []
        for raw in p["jsonld_raw"]:
            doc, val = vocab.parse(raw)
            p["existing"].append({"raw": raw.strip(), "parsed": doc, "validation": val.model_dump()})
    pending_refs = []
    for p in fetched:
        page_mentions = []
        for ex in p["existing"]:
            if ex["parsed"] is None:
                continue
            ms, es, refs = knowledge.mentions_from_jsonld(ex["parsed"], p["url"])
            d, r = vocab.defined_ids(ex["parsed"])
            defined_ids |= {knowledge.urljoin(p["url"], x) for x in d}
            doc_refs.setdefault(p["id"], set()).update(knowledge.urljoin(p["url"], x) for x in r)
            for m in ms:
                mid = f"{p['id']}:{m['key'].split('#')[-1]}:{len(mentions)}"
                key2name[m["key"]] = m["name"]
                mentions.append({"id": mid, "page_id": p["id"], "url": p["url"], "rid": None, "kind": "extracted", "method": "json-ld",
                                 "type": m["type"], "name": m["name"], "jsonld_id": m["jsonld_id"], "props": dict(m["props"]),
                                 "prop_kind": {k: "extracted" for k in m["props"]}, "prop_evidence": {}, "aliases": m["aliases"],
                                 "evidence": None, "evidence_verified": True, "_key": m["key"]})
                page_mentions.append(m)
            for e in es:
                pending_refs.append((p, e))
        # navigation facts
        doc0 = next((ex["parsed"] for ex in p["existing"] if ex["parsed"] is not None), None)
        for ed in knowledge.breadcrumb_edges(doc0 or [], p["breadcrumb_html"], p["nav_tree"], p["url"]):
            for side in ("child", "parent"):
                x = ed[side]
                x["url"] = norm(x["url"])
                if not any(m["jsonld_id"] == x["url"] and m["page_id"] == p["id"] for m in mentions):
                    mentions.append({"id": f"{p['id']}:nav:{len(mentions)}", "page_id": p["id"], "url": p["url"], "rid": None,
                                     "kind": "extracted", "method": ed["method"] if ed["method"] != "json-ld" else "breadcrumb", "type": "WebPage",
                                     "name": x["name"], "jsonld_id": x["url"], "props": {}, "prop_kind": {}, "prop_evidence": {},
                                     "aliases": [], "evidence": None, "evidence_verified": True})
            rels.append({"id": f"{p['id']}:nav:{len(rels)}", "page_id": p["id"], "url": p["url"], "rid": None, "kind": "extracted",
                         "method": ed["method"] if ed["method"] != "json-ld" else "breadcrumb", "support": "navigation",
                         "subject": ed["child"]["name"], "subject_url": ed["child"]["url"], "predicate": ed["predicate"],
                         "object": ed["parent"]["name"], "object_url": ed["parent"]["url"], "evidence": None, "evidence_verified": True})
    id2name, id_names, id_home = {}, {}, {}
    for m in mentions:
        if m["jsonld_id"] and m["type"] != "WebPage":
            id_names.setdefault(m["jsonld_id"], set()).add(resolve.norm_name(m["name"]))
            id2name[m["jsonld_id"]] = m["name"]
            # the claimant defined on the document the @id belongs to (https://site/#org belongs to https://site/) is the owner of that identifier
            if norm(m["jsonld_id"].split("#")[0]) == norm(m["url"]):
                id_home.setdefault(m["jsonld_id"], set()).add(m["name"])
    # an @id that two different names claim is followed to its owner when exactly one claimant sits on the identifier's own document;
    # with no clear owner a reference to it is left unresolved rather than guessed
    for k in list(id2name):
        if len(id_names[k]) > 1:
            home = id_home.get(k, set())
            if len({resolve.norm_name(n) for n in home}) == 1:
                id2name[k] = next(iter(home))
            else:
                del id2name[k]
    dangling = {}
    for p, e in pending_refs:
        subj = key2name.get(e["subject_key"])
        if "object_ref" in e:
            tgt = id2name.get(e["object_ref"])
            if not tgt:
                dangling.setdefault(p["id"], []).append(e["object_ref"])
                continue
        else:
            tgt = key2name.get(e["object_key"])
        if subj and tgt:
            rels.append({"id": f"{p['id']}:r:{len(rels)}", "page_id": p["id"], "url": p["url"], "rid": None, "kind": "extracted",
                         "method": "json-ld", "support": "markup", "subject": subj, "predicate": e["predicate"], "object": tgt,
                         "evidence": None, "evidence_verified": True})
    for p in fetched:                                                   # site-level @id check on top of per-page validation
        for d in dangling.get(p["id"], []):
            p["existing"] and p["existing"][0]["validation"]["issues"].append(
                {"severity": "error", "code": "dangling_id", "message": f"@id reference '{d}' points to nothing defined on this site.", "path": ""})
            p["existing"][0]["validation"]["valid"] = False
        p["structured_data"], p["existing_types"] = classify(p)
        p["entity_count"] = 0
    pages_by_id = {p["id"]: p for p in fetched}

    # ---- ingest (reuse unchanged pages on a recrawl) -------------------------------------------------------
    sset(sid, state="ingesting", detail="Indexing pages into the knowledge base")
    changes = {"new": [], "modified": [], "removed": [], "unchanged": []} if is_recrawl else None
    rel_by_page = {}
    for r_ in rels:
        if r_["support"] == "markup":
            rel_by_page.setdefault(r_["page_id"], []).append(r_)
    written_rel_count = 0
    to_wait = []
    for p in fetched:
        old = prev.get(p["url"])
        if old and old.get("rid") and old.get("content_hash") == p["content_hash"] and old.get("status") in ("fetched", "ingested"):
            p["rid"], p["inferred"] = old["rid"], old.get("inferred")
            changes and changes["unchanged"].append(p["url"])
            continue
        if old and old.get("rid"):
            try:
                arag.delete_resource(meter, old["rid"])
            except arag.ArError:
                pass
            changes and changes["modified"].append(p["url"])
        elif changes is not None:
            changes["new"].append(p["url"])
        body = (p["title"] or p["url"]) + "\n\n" + p["text"]
        reln = []
        for r_ in rel_by_page.get(p["id"], []):
            reln.append({"relation": "ENTITY", "label": r_["predicate"],
                         "from": {"value": r_["subject"], "type": "entity", "group": "ENTITY"},
                         "to": {"value": r_["object"], "type": "entity", "group": "ENTITY"}})
        try:
            p["rid"] = arag.create_resource(meter, p["title"] or p["url"], body, p["url"], reln, labels=[("markup-status", p.get("structured_data") or "none")])
            written_rel_count += len(reln)
            to_wait.append(p)
        except arag.ArError as e:
            p["status"], p["reason"] = "failed", f"ingest_error:{e.status}"
            gap(p["url"], "fetch_failed", f"Fetched but the knowledge base rejected it ({e.status}).", p["in_sitemap"])
        sset(sid, detail=f"Indexed {sum(1 for q in fetched if q.get('rid'))} of {len(fetched)} pages")
    if not any(p.get("rid") for p in fetched):
        sset(sid, state="failed", error="The knowledge service did not accept any page, so nothing was indexed. Nothing has been faked or skipped: check the service credential and try again.",
             gaps=gaps, finished_at=time.time(), counts=counts_of(pages, gaps, in_sitemap, queue), cost=build_cost(meter, 0, 0, crawler))
        return
    if changes is not None:
        changes["removed"] = [u for u, o in prev.items() if o.get("status") in ("fetched", "ingested") and u not in pages]
        for u in changes["removed"]:
            if prev[u].get("rid"):
                try:
                    arag.delete_resource(meter, prev[u]["rid"])
                except arag.ArError:
                    pass
    pend, errd = arag.wait_processed(meter, [p["rid"] for p in to_wait], timeout=180 + 3 * len(to_wait))
    for p in fetched:
        if p.get("rid") in pend | errd:
            gap(p["url"], "fetch_failed", "Indexed but the platform did not finish processing it in time." if p["rid"] in pend else "The platform reported a processing error.", p["in_sitemap"])
            p["status"], p["reason"] = "failed", "processing"
    for m in mentions:
        m["rid"] = pages_by_id[m["page_id"]].get("rid")
    for r_ in rels:
        r_["rid"] = pages_by_id[r_["page_id"]].get("rid")
    for p in fetched:
        store.put("pages", p["id"], sid, _slim(p))
    for u, rec in pages.items():
        if rec["status"] != "fetched":
            store.put("pages", rec["id"], sid, rec)

    first_insight = time.time() - t0
    publish(sid, pages_by_id, mentions, rels, dangling, crawler.base)       # markup-only view available now
    sset(sid, seconds_to_first_insight=round(first_insight, 1))

    # ---- infer from prose (the only model-cost stage) -------------------------------------------------------
    sset(sid, state="extracting", detail="Reading page prose for entities and relationships")
    todo = [p for p in fetched if p["status"] == "fetched" and p.get("rid") and not p.get("inferred")]
    dropped_total = {}

    def work(p):
        try:
            out, dropped = infer.run_page(meter, p["rid"], (p["title"] or p["url"]) + "\n\n" + p["text"], config.EXTRACT_PASSES)
            p["inferred"] = {"result": out, "dropped": dropped}
        except arag.ArError as e:
            p["inferred"] = {"error": f"{e.status}"}
    done = [0]
    with ThreadPoolExecutor(config.ASK_WORKERS) as ex:
        futs = [ex.submit(work, p) for p in todo]
        for f in futs:
            f.result()
            done[0] += 1
            sset(sid, detail=f"Extracted prose from {done[0]} of {len(todo)} pages")
    for p in fetched:
        store.put("pages", p["id"], sid, _slim(p))

    # ---- fold model proposals into mentions/relations -------------------------------------------------------
    unsupported = 0
    for p in fetched:
        inf = p.get("inferred") or {}
        for k, v in (inf.get("dropped") or {}).items():
            unsupported += v
            dropped_total[k] = dropped_total.get(k, 0) + v
        if inf.get("error"):
            dropped_total["extraction_failed"] = dropped_total.get("extraction_failed", 0) + 1
        res = inf.get("result")
        if not res:
            continue
        by_name = {}
        for e in res["entities"]:
            m = {"id": f"{p['id']}:model:{len(mentions)}", "page_id": p["id"], "url": p["url"], "rid": p["rid"], "kind": "suggested",
                 "method": "model", "type": e["type"], "name": e["name"], "jsonld_id": None, "props": {}, "prop_kind": {},
                 "prop_evidence": {}, "aliases": [], "evidence": e["evidence"], "evidence_verified": e["evidence_verified"]}
            mentions.append(m)
            by_name[norm_name(e["name"])] = m
        for f in res["facts"]:
            m = by_name.get(norm_name(f["entity"]))
            if m and f["property"] not in m["props"]:
                m["props"][f["property"]] = f["value"]
                m["prop_kind"][f["property"]] = "suggested"
                m["prop_evidence"][f["property"]] = f["evidence"]
        for r_ in res["relations"]:
            rels.append({"id": f"{p['id']}:prose:{len(rels)}", "page_id": p["id"], "url": p["url"], "rid": p["rid"], "kind": "suggested",
                         "method": "model", "support": "prose", "subject": r_["subject"], "predicate": r_["predicate"],
                         "object": r_["object"], "label": r_.get("label", ""), "evidence": r_["evidence"], "evidence_verified": r_["evidence_verified"]})

    sset(sid, state="resolving", detail="Resolving entities and checking for conflicts")
    graph = publish(sid, pages_by_id, mentions, rels, dangling, crawler.base, unsupported=unsupported)

    # ---- read back deterministic relations from the platform's own graph --------------------------------------
    pg = readback(meter, rels, written_rel_count)

    # ---- final status -------------------------------------------------------------------------------------------
    cost = build_cost(meter, sum(1 for p in fetched if p["status"] == "fetched"), len([p for p in fetched if (p.get("inferred") or {}).get("result") and p in todo]), crawler)
    sset(sid, state="ready", detail="Ready", finished_at=time.time(), cost=cost, platform_graph=pg, changes=changes,
         gaps=gaps, dropped=dropped_total,
         counts=counts_of(pages, gaps, in_sitemap, queue), robots={**crawler.robots, "user_agent": config.USER_AGENT, "delay_seconds": crawler.delay})
    _summarise(sid)


def classify(p):
    types, worst = [], "complete"
    if not p["existing"]:
        return "none", []
    for ex in p["existing"]:
        if ex["parsed"] is not None:
            for n in vocab._iter_nodes(ex["parsed"]):
                if isinstance(n, dict):
                    types += vocab.types_of(n)
        v = ex["validation"]
        if not v["valid"] or any(i["severity"] == "warning" for i in v["issues"]):
            worst = "partial_or_invalid"
    return worst, sorted(set(types))


def _slim(p):
    d = {k: v for k, v in p.items()}
    d["status"] = "ingested" if p["status"] == "fetched" and p.get("rid") else p["status"]
    d["jsonld_raw"] = []
    return d


def counts_of(pages, gaps, in_sitemap, queue=()):
    ing = sum(1 for p in pages.values() if p["status"] == "fetched" and p.get("rid"))
    pattern_excluded = {g["url"] for g in gaps if g["reason"] == "excluded_by_pattern"}
    seen_urls = set(pages) | set(queue) | {g["url"] for g in gaps if g["reason"] in ("blocked_by_robots", "over_page_cap", "link_only") and not g["url"].endswith(("sitemap.xml", ".xml.gz"))}
    return {"discovered": len(seen_urls - pattern_excluded),
            "in_sitemap": len(in_sitemap), "fetched": sum(1 for p in pages.values() if p["status"] == "fetched"),
            "ingested": ing, "failed": sum(1 for p in pages.values() if p["status"] == "failed") + sum(1 for g in gaps if g["reason"] in ("fetch_failed",) and not any(p["url"] == g["url"] for p in pages.values())),
            "excluded": sum(1 for g in gaps if g["reason"] in ("blocked_by_robots", "noindex", "excluded_by_pattern", "over_page_cap", "off_host", "redirected")),
            "link_only": sum(1 for g in gaps if g["reason"] == "link_only")}


def publish(sid, pages_by_id, mentions, rels, dangling, root_url, unsupported=0):
    pages_map = {pid: {"url": p["url"], "id": pid, "text": p.get("text", ""), "title": p.get("title") or ""} for pid, p in pages_by_id.items()}
    res = resolve.resolve(mentions, rels, pages_map, store.all_("decisions", sid))
    mbp = {}
    for m in mentions:
        mbp.setdefault(m["page_id"], []).append(m)
    # suggestions
    old = {s["page_id"]: s for s in store.all_("suggestions", sid)}
    enrich = {}
    store.clear("suggestions", sid)
    for pid, p in pages_by_id.items():
        if not p.get("rid"):
            continue
        b = suggest.build(p, res, mbp, res["edges"], dangling, root_url)
        if not b:
            continue
        import json
        prev = old.get(pid)
        status, edited, decided = "pending", False, None
        jd = b["jsonld"]
        if prev and prev["status"] in ("approved", "rejected"):
            if json.dumps(prev["jsonld"], sort_keys=True) == json.dumps(jd, sort_keys=True) or prev.get("edited"):
                status, decided = prev["status"], prev.get("decided_at")
                if prev.get("edited"):
                    jd, edited = prev["jsonld"], True
        enrich[pid] = b["enriched"]
        sg = {"id": f"s-{pid}", "page_id": pid, "jsonld": jd, "property_provenance": b["property_provenance"],
              "evidence": [e.model_dump() for e in b["evidence"]], "validation": vocab.validate_doc(jd).model_dump() if edited else b["validation"].model_dump(),
              "confidence": b["confidence"].model_dump(), "status": status, "edited": edited, "decided_at": decided,
              "needs_review": b["needs_review"], "property_evidence": b["property_evidence"], "proposed_jsonld": b["jsonld"]}
        store.put("suggestions", sg["id"], sid, sg)
    ent_pages = {}
    for n in res["nodes"]:
        if n.type != "WebPage":
            for pg in n.pages:
                ent_pages[pg["page_id"]] = ent_pages.get(pg["page_id"], 0) + 1
    for pid, p in pages_by_id.items():
        p["entity_count"] = ent_pages.get(pid, 0)
        trunc = [{"severity": "warning", "code": "truncated", "message": f"This page is very long; only the first {config.MAX_TEXT_CHARS:,} characters were read.", "path": ""}] if p.get("truncated") else []
        p["enrichment_issues"] = trunc + [{"severity": "warning" if core else "info", "code": "stated_in_text_not_in_markup", "message": m_, "path": ""}
                                  for core, m_ in enrich.get(pid, [])]
        if any(core for core, _ in enrich.get(pid, [])) and p.get("structured_data") == "complete":
            p["structured_data"] = "partial_or_invalid"
        if p.get("rid"):
            store.put("pages", pid, sid, _slim(p))
    # Site structure (breadcrumbs, menus) describes how PAGES relate; pages are not entities, so it is reported separately
    page_url = {eid: next((m["jsonld_id"] for m in e["mentions"] if m.get("jsonld_id")), None) for eid, e in res["entities"].items() if e["group"] == "page"}
    label_of = {n.id: n.label for n in res["nodes"]}
    navigation = [{"id": e.id, "child": {"name": label_of.get(e.source), "url": page_url.get(e.source)},
                   "parent": {"name": label_of.get(e.target), "url": page_url.get(e.target)},
                   "method": e.provenance.method, "found_on": e.provenance.source_url}
                  for e in res["edges"] if e.support == "navigation"]
    g = {"nodes": [n.model_dump() for n in res["nodes"] if n.type != "WebPage"],
         "edges": [e.model_dump() for e in res["edges"] if e.support != "navigation" and e.source != e.target
                   and e.source in {n.id for n in res["nodes"] if n.type != "WebPage"} and e.target in {n.id for n in res["nodes"] if n.type != "WebPage"}],
         "navigation": navigation,
         "conflicts": [c.model_dump() for c in res["conflicts"]], "ambiguities": [a.model_dump() for a in res["ambiguities"]],
         "unsupported_dropped": unsupported + res.get("dropped_edges", 0), "edges_without_object_in_quote": res.get("dropped_edges", 0), "dropped_edges": res.get("dropped_detail", []), "dropped_by_guard": dict(__import__("collections").Counter(x.get("guard", "other") for x in res.get("dropped_detail", []))),
         "edges_object_from_page": sum(1 for e in res["edges"] if not e.object_in_quote and e.support == "prose")}
    store.put("entities", sid, sid, g)
    store.clear("mentions", sid)
    store.put("mentions", sid, sid, {"mentions": mentions, "relations": rels})
    _summarise(sid, g)
    return g


def _summarise(sid, g=None):
    g = g or store.get("entities", sid) or {}
    ec, rc = {}, {}
    for n in g.get("nodes", []):
        if n["type"] != "WebPage":
            ec[n["type"]] = ec.get(n["type"], 0) + 1
    for e in g.get("edges", []):
        rc[e["support"]] = rc.get(e["support"], 0) + 1
    if g.get("navigation"):
        rc["navigation"] = len(g["navigation"])
    sd = {"complete": 0, "partial_or_invalid": 0, "none": 0}
    for p in store.all_("pages", sid):
        if p.get("status") == "ingested":
            sd[p.get("structured_data", "none")] = sd.get(p.get("structured_data", "none"), 0) + 1
    # resolution-stage guards are counted beside the extraction-stage ones, and every guard is always present, so a zero means
    # "the guard ran and dropped nothing", never "the guard does not record"
    by_guard = {k: 0 for k in ("separation", "sentence_object", "competing_object", "object_not_on_page")}
    by_guard.update(g.get("dropped_by_guard") or {})
    sset(sid, entity_counts=ec, relation_counts=rc, structured_data=sd, conflicts=len(g.get("conflicts", [])),
         ambiguities=len(g.get("ambiguities", [])), unsupported_dropped=g.get("unsupported_dropped", 0),
         dropped={**(sget(sid).get("dropped") or {}), **by_guard})


def readback(meter, rels, written):
    """Ask the platform's graph for the deterministic relations we wrote, to show they persisted."""
    mk = [r for r in rels if r["support"] == "markup"]
    if not mk:
        return {"written": 0, "note": "No relationships were found in existing markup, so none were written to the graph."}
    subjects = list(dict.fromkeys(r["subject"] for r in mk))[:8]
    found = 0
    want = {(r["subject"], r["predicate"], r["object"]) for r in mk if r["subject"] in subjects}
    got = set()
    for s in subjects:
        try:
            for path in arag.graph_neighbours(meter, s):
                lab = (path.get("relation") or {}).get("label")
                a, b = (path.get("source") or {}).get("value"), (path.get("destination") or {}).get("value")
                if a and b and lab:
                    got.add((a, lab, b))
        except arag.ArError:
            continue
    found = len(want & got)
    return {"written": written, "sampled_entities": len(subjects), "sampled_relations": len(want), "read_back": found,
            "note": "Relationships from existing markup were written to the knowledge base at ingest, at no model cost, and read back from its graph."}


def build_cost(meter, pages, model_pages, crawler):
    s = meter.snapshot()
    c = Cost(platform_calls=s["platform_calls"], model_calls=s["model_calls"], input_tokens=s["input_tokens"],
             output_tokens=s["output_tokens"], pages=pages)
    if model_pages:
        tot = s["input_tokens"] + s["output_tokens"]
        c.tokens_per_page = round(tot / model_pages, 1)
        c.model_calls_per_page = round(s["model_calls"] / model_pages, 2)
        c.extrapolation_500_pages = {"model_calls": round(c.model_calls_per_page * 500), "input_tokens": round(s["input_tokens"] / model_pages * 500),
                                     "output_tokens": round(s["output_tokens"] / model_pages * 500),
                                     "minimum_polite_crawl_seconds": round(500 * crawler.delay)}
        if config.PRICE_IN_PER_M or config.PRICE_OUT_PER_M:
            usd = (s["input_tokens"] * config.PRICE_IN_PER_M + s["output_tokens"] * config.PRICE_OUT_PER_M) / 1e6
            c.estimated_usd_per_page = round(usd / model_pages, 6)
            c.price_assumption = f"Operator-supplied: ${config.PRICE_IN_PER_M}/M model input tokens, ${config.PRICE_OUT_PER_M}/M model output tokens"
    c.notes = cost_notes()
    return c.model_dump()


def republish(sid):
    """Re-run resolution and proposals from the stored mentions, with no crawl and no model call. Used after a reviewer
    decides an ambiguity."""
    site = sget(sid)
    m = store.get("mentions", sid)
    pages_by_id = {p["id"]: p for p in store.all_("pages", sid) if p.get("status") == "ingested"}
    root = urlparse(site["root_url"])
    dangling = {}
    for p in pages_by_id.values():
        for ex in p.get("existing", []):
            for i in ex["validation"]["issues"]:
                if i["code"] == "dangling_id":
                    dangling.setdefault(p["id"], []).append(i["message"].split("'")[1] if "'" in i["message"] else i["message"])
    return publish(sid, pages_by_id, m["mentions"], m["relations"], dangling, f"{root.scheme}://{root.netloc}",
                   unsupported=((store.get("entities", sid) or {}).get("unsupported_dropped", 0) - (store.get("entities", sid) or {}).get("edges_without_object_in_quote", 0)))


def cost_notes():
    """Single source for the cost explanation; also applied when an older stored run is read."""
    return [
        "Model tokens are read from each generative response the platform returns; they are measured, not estimated, and they are not Progress Agentic RAG consumption tokens, which are a different unit.",
        "Page indexing (embeddings and text processing) happens inside the platform and is not metered per call in its API responses, so it is counted as calls, not model tokens.",
        "Markup extraction, navigation, entity resolution, conflict detection and JSON-LD assembly cost no model calls or model tokens.",
        "Two counted model calls per page: the structured extraction and a recall pass that re-reads the same page for relationships the first missed (the second is skipped when the first finds fewer than two entities). Both send the whole page, so cost grows with page length. Ingest-time extraction tasks that run per paragraph were deliberately not used.",
        f"Model pinned to {config.MODEL}.",
    ]
