"""The one place the application talks to Progress Agentic RAG.

Every call is counted and every generative call's token usage is read from the platform's own
response (`metadata.tokens`), so cost per page is a measurement and not an estimate. The meter is
attached to a `Run` so a crawl's cost is separable from a later question's cost.
"""
import threading
import time

import httpx

from . import config

H = {"X-NUCLIA-SERVICEACCOUNT": f"Bearer {config.KB_TOKEN}", "Content-Type": "application/json",
     "X-Synchronous": "true"}


class Meter:
    def __init__(self):
        self.calls = {}
        self.model_calls = 0
        self.input_tokens = 0
        self.output_tokens = 0
        self.errors = 0
        self._l = threading.Lock()

    def call(self, kind, tokens=None):
        with self._l:
            self.calls[kind] = self.calls.get(kind, 0) + 1
            if tokens:
                self.model_calls += 1
                self.input_tokens += int(tokens.get("input") or 0)
                self.output_tokens += int(tokens.get("output") or 0)

    def error(self):
        with self._l:
            self.errors += 1

    def snapshot(self):
        with self._l:
            return {"platform_calls": dict(self.calls), "model_calls": self.model_calls,
                    "input_tokens": self.input_tokens, "output_tokens": self.output_tokens,
                    "errors": self.errors}


class ArError(Exception):
    def __init__(self, status, text):
        super().__init__(f"{status}: {text[:300]}")
        self.status = status


_client = httpx.Client(timeout=httpx.Timeout(60.0, connect=10.0))


def _req(method, path, meter, kind, retries=1, **kw):
    """One platform call with a timeout and one honest retry on a stall or 5xx. 4xx are shown, not retried."""
    last = None
    for attempt in range(retries + 1):
        try:
            r = _client.request(method, f"{config.KB_URL}{path}", headers=H, **kw)
        except (httpx.TimeoutException, httpx.TransportError) as e:
            last = ArError(0, f"network: {e.__class__.__name__}")
            meter and meter.error()
            time.sleep(1.5)
            continue
        if r.status_code >= 500 and attempt < retries:
            meter and meter.error()
            last = ArError(r.status_code, r.text)
            time.sleep(1.5)
            continue
        if r.status_code >= 400:
            meter and meter.error()
            raise ArError(r.status_code, r.text)
        d = r.json() if r.content else {}
        tokens = (d.get("metadata") or {}).get("tokens") if isinstance(d, dict) else None
        meter and meter.call(kind, tokens)
        return d
    raise last


LABELSETS = {"markup-status": ("Structured data already on the page", ["complete", "partial_or_invalid", "none"])}


def ensure_labelsets():
    """Register the labelsets as real objects on the knowledge base (idempotent), so the console shows them. Labels are assigned
    deterministically at ingest from the crawl's own classification of the page's existing markup: no model, no cost, and never
    from a faceted count."""
    ok = True
    for lid, (title, labels) in LABELSETS.items():
        body = {"title": title, "kind": ["RESOURCES"], "multiple": False, "labels": [{"title": x} for x in labels]}
        try:
            r = _client.post(f"{config.KB_URL}/labelset/{lid}", headers=H, json=body)
            ok = ok and r.status_code < 300
        except httpx.HTTPError:
            ok = False
    return ok


def create_resource(meter, title, body, url, relations=None, slug=None, labels=None):
    payload = {"title": title, "origin": {"url": url},
               "texts": {"body": {"body": body, "format": "PLAIN"}}}
    if slug:
        payload["slug"] = slug
    um = {}
    if relations:
        um["relations"] = relations
    if labels:
        um["classifications"] = [{"labelset": ls, "label": lb} for ls, lb in labels]
    if um:
        payload["usermetadata"] = um
    return _req("POST", "/resources", meter, "ingest_resource", json=payload)["uuid"]


def delete_resource(meter, rid):
    return _req("DELETE", f"/resource/{rid}", meter, "delete_resource")


def resource_status(meter, rid):
    d = _req("GET", f"/resource/{rid}", meter, "status_poll", params={"show": "basic"})
    return (d.get("metadata") or {}).get("status")


def wait_processed(meter, rids, timeout=240):
    """Poll until every resource is PROCESSED; returns the set still pending/errored."""
    pending, deadline = set(rids), time.time() + timeout
    errored = set()
    while pending and time.time() < deadline:
        for rid in list(pending):
            try:
                st = resource_status(meter, rid)
            except ArError:
                continue
            if st == "PROCESSED":
                pending.discard(rid)
            elif st == "ERROR":
                pending.discard(rid)
                errored.add(rid)
        if pending:
            time.sleep(3)
    return pending, errored


def extract(meter, rid, query, schema, kind="structured_extraction"):
    """Structured per-page extraction: /ask with answer_json_schema, scoped to ONE resource, whole
    resource in context. No citations flag on the same call (the platform 500s on that combination)."""
    body = {"query": query, "resource_filters": [rid], "answer_json_schema": schema,
            "generative_model": config.MODEL, "rag_strategies": [{"name": "full_resource"}]}
    d = _req("POST", "/ask", meter, kind, json=body)
    return d.get("answer_json"), d


SEARCH_CONFIG = "site-question-answering"
GROUNDING_PROMPT = (
    "You answer questions about one website using only the retrieved page text and any extra context supplied with the "
    "question. If the pages only partly cover the question, say plainly what is covered and what is not. If the retrieved "
    "text lists several relevant facts under the question's topic, include all of them. Never state a price, date, hour or "
    "name that is not in the retrieved text. Say that pages disagree only where the supplied context states a conflict for that item; two figures about different things (a part and a whole, one screen and the whole venue) do not disagree. If the context says no disagreement was computed, do not describe one. If the pages do not answer the "
    "question, say that the site does not say. Refer to 'the site' or 'the pages', and never to 'the provided text', 'the context' or 'metadata'. Use Australian English. Never use an em dash; use a spaced hyphen instead.")


def ensure_cheap_defaults():
    """The knowledge base ships with a premium default generative model. Any call that forgot to pin a model would
    silently inherit it, so the defaults are moved to the cheapest capable tier (hard rule 15)."""
    try:
        r = _client.patch(f"{config.KB_URL}/configuration", headers=H,
                          json={"generative_model": config.MODEL, "summary_model": config.MODEL})
        return r.status_code < 300
    except httpx.HTTPError:
        return False


def ensure_search_config():
    """Register the answer configuration as a real object on the knowledge base (idempotent). Model, prompt and
    top_k live there, so the call below sends only the name, not its own copies of those settings."""
    payload = {"kind": "ask", "config": {"prompt": {"system": GROUNDING_PROMPT}, "generative_model": config.MODEL, "top_k": 12}}
    try:
        r = _client.post(f"{config.KB_URL}/search_configurations/{SEARCH_CONFIG}", headers=H, json=payload)
        if r.status_code == 409:
            r = _client.patch(f"{config.KB_URL}/search_configurations/{SEARCH_CONFIG}", headers=H, json=payload)
        return r.status_code < 300
    except httpx.HTTPError:
        return False


def ask(meter, question, rids, extra_context=None, kind="grounded_answer"):
    body = {"query": question, "citations": True, "search_configuration": SEARCH_CONFIG,
            "resource_filters": list(rids)}
    if extra_context:
        body["extra_context"] = extra_context
    return _req("POST", "/ask", meter, kind, json=body)


def graph_neighbours(meter, entity):
    """One hop from an entity in the platform's own graph. undirected:true is mandatory: a directed
    anchored query silently returns only edges where the anchor is the source."""
    d = _req("POST", "/graph", meter, "graph_readback",
             json={"query": {"prop": "path", "source": {"value": entity}, "undirected": True}, "top_k": 200})
    return d.get("paths", [])


def remi(meter, question, answer, contexts):
    """Answer-quality scores from the platform's evaluation model. It has no model field and reports no consumption."""
    d = _req("POST", "/predict/remi", meter, "answer_quality",
             json={"user_id": "semanticsite", "question": question, "answer": answer, "contexts": contexts}, retries=0)

    def mx(v):
        if isinstance(v, list):
            v = max(v) if v else None
        try:
            return round(float(v), 1)
        except (TypeError, ValueError):
            return None
    return {"groundedness": mx(d.get("groundedness")), "context_relevance": mx(d.get("context_relevance"))}
