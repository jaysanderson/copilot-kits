"""Programmatic knowledge graph over the University site: run-time traversal.

The relations were written once, deterministically, by seed/build_graph.py (no model call). Here
every hop is a real anchored graph query against the knowledge base, undirected, one per hop.
graph/graph_edges.json is the build-time evidence index (the sentence that justified each edge)
and the page directory; it is never used to invent an edge, only to explain one the graph returned.
"""
import asyncio
import json
from pathlib import Path

import httpx

HERE = Path(__file__).parent
_idx = json.loads((HERE / "graph" / "graph_edges.json").read_text())
PAGES: dict = _idx["pages"]
LABELS = {"parent-of", "covers-topic", "addresses", "located-at", "names"}
GROUP_LABEL = {"TOPIC": "Topic", "AUDIENCE": "Audience", "CAMPUS": "Campus", "NAMED": "Name"}
# NAMED edges stay in the knowledge base but are never shown: a shared surname-like phrase is not a shared subject.
SURFACED = {"TOPIC", "AUDIENCE", "CAMPUS"}
ORDER = {"TOPIC": 0, "AUDIENCE": 0, "CAMPUS": 1, "NAMED": 2}  # topics and audiences first: names are the colour, not the spine
WHY = {}      # (page id, group, value) -> evidence sentence
COUNT = {}    # (page id, group, value) -> mention count
for e in _idx["edges"]:
    if e.get("node"):
        k = (e["from"], e["node"]["group"], e["node"]["value"])
        WHY[k] = e["why"]
        COUNT[k] = e.get("count", 1)


def section(pid: str) -> str:
    segs = [s for s in PAGES.get(pid, {}).get("url", "").split("/")[3:] if s]
    return segs[0] if segs else "home"


def page_card(pid: str) -> dict:
    p = PAGES.get(pid, {})
    return {"id": pid, "title": p.get("title") or "The university page", "url": p.get("url", ""), "section": section(pid)}


async def graph_query(client: httpx.AsyncClient, kb: str, headers: dict, source: dict, top_k: int = 500) -> list:
    """One anchored hop. undirected=True is not optional: without it the query is source-only and
    silently drops most of the edges."""
    r = await client.post(f"{kb}/graph", json={"query": {"prop": "path", "source": source, "undirected": True}, "top_k": top_k}, headers=headers, timeout=20)
    r.raise_for_status()
    return [p for p in r.json().get("paths", []) if p["relation"]["label"] in LABELS]


def anchor_page(pid): return {"value": pid, "match": "exact", "type": "resource"}
def anchor_node(group, value): return {"value": value, "match": "exact", "type": "entity", "group": group}


async def expand_page(client, kb, headers, pid: str, max_concepts: int = 10) -> dict:
    """Hop 1: the page's own relations. Hop 2: one anchored query per concept it touches."""
    paths = await graph_query(client, kb, headers, anchor_page(pid))
    parent, children, concepts = None, [], {}
    for p in paths:
        a, b, lab = p["source"], p["destination"], p["relation"]["label"]
        if lab == "parent-of":
            if b["value"] == pid and a["type"] == "resource": parent = a["value"]
            elif a["value"] == pid and b["type"] == "resource": children.append(b["value"])
        elif b["type"] == "entity" and a["value"] == pid and b["group"] in SURFACED:
            concepts[(b["group"], b["value"])] = lab
    base = section(pid)

    async def hop(key):
        group, value = key
        ps = await graph_query(client, kb, headers, anchor_node(group, value))
        pids = sorted({p["source"]["value"] for p in ps if p["source"]["type"] == "resource" and p["source"]["value"] != pid})
        return key, pids
    # most specific concepts first (a concept on 40 pages says little), crossing sections is the point
    results = await asyncio.gather(*[hop(k) for k in concepts])
    links = []
    for (group, value), pids in results:
        if not pids: continue
        cross = [x for x in pids if section(x) != base]
        links.append({
            "group": group, "kind": GROUP_LABEL.get(group, group), "value": value, "label": concepts[(group, value)],
            "why": WHY.get((pid, group, value), ""), "total": len(pids) + 1,
            "sections": sorted({section(x) for x in pids} | {base}), "cross": len(cross),
            "pages": [dict(page_card(x), why=WHY.get((x, group, value), ""), n=COUNT.get((x, group, value), 1)) for x in
                      sorted(pids, key=lambda x: (section(x) == base, -COUNT.get((x, group, value), 1)))[:12]],
        })
    # rank: concepts that carry you across the menu first; broad ones after narrow ones
    links.sort(key=lambda l: (ORDER.get(l["group"], 9), -(len(l["sections"]) > 1), l["total"], l["value"]))
    return {"page": page_card(pid), "parent": page_card(parent) if parent else None,
            "children": [page_card(x) for x in sorted(children, key=lambda x: PAGES[x]["title"])][:24],
            "links": links[:max_concepts], "relations_read": len(paths)}


# ---- reach: how much of the site a visitor can get to from a page, by the site's tree and by shared threads ----
SURFACED_LABELS = {"covers-topic", "addresses", "located-at"}
_graphed = {i for i, p in PAGES.items() if not p.get("alias")}
_parent: dict = {}
_threads: dict = {}   # (group, value) -> set of page ids
for _e in _idx["edges"]:
    if _e["label"] == "parent-of":
        _parent[_e["to"]] = _e["from"]
    elif _e["label"] in SURFACED_LABELS:
        _threads.setdefault((_e["node"]["group"], _e["node"]["value"]), set()).add(_e["from"])
_children: dict = {}
for _c, _p in _parent.items():
    _children.setdefault(_p, set()).add(_c)
TREE: dict = {}      # page -> parent, children and siblings: the neighbours the site's own tree gives you
THREAD: dict = {}    # page -> every page sharing at least one surfaced thread
for _i in _graphed:
    _n = set(_children.get(_i, ()))
    if _i in _parent:
        _n.add(_parent[_i]); _n |= _children.get(_parent[_i], set())
    TREE[_i] = _n - {_i}
    THREAD[_i] = set()
for _members in _threads.values():
    for _i in _members:
        THREAD[_i] |= _members
for _i in THREAD:
    THREAD[_i] -= {_i}


def _two(adj: dict, i: str) -> set:
    one = adj[i]
    out = set(one)
    for j in one:
        out |= adj.get(j, set())
    return out - {i}


def _median(xs):
    xs = sorted(xs)
    return xs[len(xs) // 2] if xs else 0


def site_reach() -> dict:
    """Site-wide reach, derived from the graph data on load (never typed in). Denominator is the graphed pages."""
    n = len(_graphed)
    one_t = [len(TREE[i]) for i in _graphed]; one_h = [len(THREAD[i]) for i in _graphed]
    two_t = [len(_two(TREE, i)) for i in _graphed]; two_h = [len(_two(THREAD, i)) for i in _graphed]
    return {
        "pages": n,
        "one_step": {"tree_median": _median(one_t), "thread_median": _median(one_h)},
        "two_steps": {"tree_median": _median(two_t), "thread_median": _median(two_h),
                      "tree_share": round(100 * _median(two_t) / n, 1), "thread_share": round(100 * _median(two_h) / n, 1)},
        "no_thread_pages": sum(1 for i in _graphed if not THREAD[i]),
        "stranded": sum(1 for i in _graphed if len(TREE[i]) <= 1 and len(THREAD[i]) >= 3),
    }


SITE = site_reach()


def page_reach(pid: str) -> dict:
    if pid not in _graphed:
        return {}
    return {"tree_one": len(TREE[pid]), "thread_one": len(THREAD[pid]),
            "tree_two": len(_two(TREE, pid)), "thread_two": len(_two(THREAD, pid)), "pages": len(_graphed)}


def graph_facts() -> dict:
    """Figures quoted in the reveal, counted from the same file the route reads."""
    surfaced = [e for e in _idx["edges"] if e["label"] in SURFACED_LABELS]
    groups = {}
    for key in _threads:
        groups[key[0]] = groups.get(key[0], 0) + 1
    return {"pages": len(_graphed), "tree_links": sum(1 for e in _idx["edges"] if e["label"] == "parent-of"),
            "thread_links": len(surfaced), "threads": len(_threads), "topics": groups.get("TOPIC", 0),
            "audiences": groups.get("AUDIENCE", 0), "campuses": groups.get("CAMPUS", 0),
            "title_only": sum(1 for e in surfaced if e["why"].startswith("In the page title")),
            "hidden_names": sum(1 for e in _idx["edges"] if e["label"] == "names")}


FACTS = graph_facts()
