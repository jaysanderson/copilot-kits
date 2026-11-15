"""The single door to Progress Agentic RAG. Server-side only; the key never leaves this process.

Discipline applied to every call:
  * X-Synchronous: true on every NON-streaming call (otherwise the platform answers in NDJSON).
  * An explicit timeout pair. A STALL (timeout / connect failure) is retried exactly once on the
    longer timeout; a real 4xx/5xx is never retried and surfaces at once.
  * Latency is measured with perf_counter around the awaited call and written to the trace; nothing
    in a trace is a literal.
"""
import json
import time

import httpx

from . import config

# Visitor-safe names for the mechanisms. The real paths never reach a client (leak regex).
MECH = {
    "find": "hybrid retrieval (keyword + semantic, reranked)",
    "find_fast": "hybrid retrieval (keyword + semantic, rank-fused)",
    "ask": "grounded answer (generative)",
    "remi": "answer quality scoring (generative-class)",
    "graph": "knowledge graph traversal",
    "list": "catalogue listing",
    "resource": "resource read",
}


VERB = {"find": "retrieved", "find_fast": "retrieved", "ask": "generated", "remi": "quality scored",
        "graph": "traversed", "list": "listed", "resource": "read", "arithmetic": "calculated"}


class PlatformError(Exception):
    def __init__(self, kind, status=None, detail=""):
        super().__init__(f"{kind} {status or ''} {detail}".strip())
        self.kind, self.status, self.detail = kind, status, detail   # kind: stall | http | bad_payload


class Trace:
    """Per-request record of every platform call, in the contract shape plus a stamp."""
    def __init__(self):
        self.rows = []

    def add(self, call, mech, generative, model, cache, ms, **extra):
        row = {"call": call, "verb": VERB.get(mech, "ran"), "endpoint": MECH.get(mech, mech), "generative": bool(generative),
               "model": model, "cache": cache, "ms": int(round(ms))}
        row.update({k: v for k, v in extra.items() if v is not None})
        # Per-CALL truth for the reveal (CONTRACT-FIELDS-05): where THIS call was served from. A page-load call answered from the
        # resident catalogue never left this process; a retrieval/answer replay came from an earlier call's stored result; only
        # "miss" means a real call was made to the knowledge box on this request.
        row["served_from"] = {"warm": "memory", "hit": "cache-replay"}.get(cache, "knowledge-box")
        self.rows.append(row)
        return row

    def as_list(self):
        return list(self.rows)


class Arag:
    def __init__(self):
        self.client = httpx.AsyncClient(
            base_url=config.KB_URL, headers=config.KB_HEADERS,
            limits=httpx.Limits(max_connections=40, max_keepalive_connections=20, keepalive_expiry=60),
            timeout=httpx.Timeout(30.0))

    async def aclose(self):
        await self.client.aclose()

    async def _json(self, trace, call, mech, method, path, *, body=None, params=None, timeouts,
                    generative=False, model=None, cache="miss"):
        """One non-streaming call with stall-retry-once. Returns parsed JSON."""
        headers = {"X-Synchronous": "true"}
        last = None
        t_all = time.perf_counter()
        for attempt, tmo in enumerate(timeouts, 1):
            try:
                r = await self.client.request(method, path, json=body, params=params, headers=headers,
                                              timeout=httpx.Timeout(tmo, connect=min(tmo, 5.0)))
            except (httpx.TimeoutException, httpx.ConnectError, httpx.RemoteProtocolError, httpx.ReadError) as e:
                last = PlatformError("stall", detail=type(e).__name__)
                continue                                   # stall: one retry on the longer timeout
            ms = (time.perf_counter() - t_all) * 1000
            if r.status_code >= 400:                       # real error: surface, never retry
                trace.add(call, mech, generative, model, "error", ms, status=r.status_code, attempts=attempt)
                raise PlatformError("http", r.status_code, r.text[:200])
            try:
                data = r.json()
            except ValueError:
                trace.add(call, mech, generative, model, "error", ms, attempts=attempt)
                raise PlatformError("bad_payload", r.status_code)
            trace.add(call, mech, generative, model, cache, ms, attempts=attempt if attempt > 1 else None)
            return data
        trace.add(call, mech, generative, model, "error", (time.perf_counter() - t_all) * 1000,
                  attempts=len(timeouts), stalled=True)
        raise last

    # ---- retrieval ---------------------------------------------------------------------------
    async def find(self, trace, call, query, filter_expression, *, top_k=20, rerank=True):
        body = {"query": query, "features": ["keyword", "semantic"], "top_k": top_k,
                "show": ["basic"], "filter_expression": filter_expression,
                "autofilter": False}
        if not rerank:
            body["reranker"] = "noop"
        return await self._json(trace, call, "find" if rerank else "find_fast", "POST", "/find",
                                body=body, timeouts=config.TIMEOUTS["find"])

    async def graph(self, trace, call, entity, top_k=40):
        body = {"query": {"prop": "path", "source": {"value": entity}, "undirected": True}, "top_k": top_k}
        return await self._json(trace, call, "graph", "POST", "/graph", body=body,
                                timeouts=config.TIMEOUTS["graph"])

    async def list_resources(self, trace, call="catalogue.list"):
        out, page = [], 0
        while True:
            d = await self._json(trace, f"{call}[{page}]", "list", "GET", "/resources",
                                 params={"page": page, "size": 100}, timeouts=config.TIMEOUTS["catalogue"])
            out += d.get("resources", [])
            if d.get("pagination", {}).get("last", True) or not d.get("resources"):
                return out
            page += 1

    async def resource_text(self, trace, call, rid):
        d = await self._json(trace, call, "resource", "GET", f"/resource/{rid}",
                             params=[("show", "extracted"), ("extracted", "text"), ("extracted", "metadata")],
                             timeouts=config.TIMEOUTS["catalogue"])
        return d

    # ---- generation --------------------------------------------------------------------------
    async def ask_events(self, trace, call, question, filter_expression, *, top_k=config.ASK_TOP_K, retry_of=None, history=None):
        """Run the grounded answer and return the list of NDJSON items once complete.

        Pinned model on every call. NOT citations+answer_json_schema (backend 500s): plain text
        answer with citations:true. The stream is consumed fully server-side; release to the visitor
        happens only after the scope cross-check (see answer.py).
        """
        body = {"query": question, "generative_model": config.ASK_MODEL, "citations": True,
                "features": ["keyword", "semantic"], "top_k": top_k, "filter_expression": filter_expression,
                "autofilter": False,
                "rag_strategies": [{"name": "neighbouring_paragraphs", "before": 1, "after": 1}],
                "prompt": {"system": config.ANSWER_SYSTEM_PROMPT}}
        if history:
            # Prior turns travel for GENERATION only (so "that plan" can resolve in the prose). The floor, the scope and every guard are
            # decided on the CURRENT question alone, before this call is made (measured: concatenating a prior question onto a thin
            # follow-up takes "Tell me a joke" from a top score of 0.006 to 0.932).
            body["context"] = [{"author": "USER" if i % 2 == 0 else "NUCLIA", "text": t} for i, t in enumerate(history)]
        t0 = time.perf_counter()
        first = None
        items = []
        last = None
        for attempt, tmo in enumerate(config.TIMEOUTS["ask_first_byte"], 1):
            try:
                async with self.client.stream("POST", "/ask", json=body,
                                              timeout=httpx.Timeout(tmo, connect=5.0)) as r:
                    if r.status_code >= 400:
                        await r.aread()
                        trace.add(call, "ask", True, config.ASK_MODEL, "error",
                                  (time.perf_counter() - t0) * 1000, status=r.status_code, attempts=attempt)
                        raise PlatformError("http", r.status_code, r.text[:200])
                    async for line in r.aiter_lines():
                        if not line.strip():
                            continue
                        if first is None:
                            first = (time.perf_counter() - t0) * 1000
                        try:
                            items.append(json.loads(line).get("item", {}))
                        except ValueError:
                            continue
                break
            except (httpx.TimeoutException, httpx.ConnectError, httpx.RemoteProtocolError, httpx.ReadError) as e:
                last = PlatformError("stall", detail=type(e).__name__)
                if first is not None:        # stalled mid-stream: cannot retry cleanly, surface it
                    break
                items = []
                continue
        else:
            trace.add(call, "ask", True, config.ASK_MODEL, "error", (time.perf_counter() - t0) * 1000,
                      attempts=len(config.TIMEOUTS["ask_first_byte"]), stalled=True)
            raise last
        total = (time.perf_counter() - t0) * 1000
        meta = next((i for i in items if i.get("type") == "metadata"), {})
        gen_timings = meta.get("timings", {})
        trace.add(call, "ask", True, config.ASK_MODEL, "miss", total,
                  first_byte_ms=int(first) if first is not None else None,
                  generative_first_chunk_ms=int(gen_timings["generative_first_chunk"] * 1000)
                  if "generative_first_chunk" in gen_timings else None,
                  attempts=attempt if attempt > 1 else None, retry_of=retry_of)
        return items

    async def remi(self, trace, call, question, answer, contexts):
        body = {"user_id": "experience-site", "question": question, "answer": answer, "contexts": contexts}
        return await self._json(trace, call, "remi", "POST", "/predict/remi", body=body,
                                timeouts=config.TIMEOUTS["remi"], generative=True, model=config.REMI_MODEL_NOTE,
                                cache="miss")
