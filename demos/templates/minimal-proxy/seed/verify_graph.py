"""Read the graph back through the KB's own graph endpoint and compare with what build_graph wrote.
Exits non-zero on any missing or unexpected edge. Reads only (search-class calls, no generation)."""
import collections, json, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from gk import KB_URL, c
from build_graph import LABELS
g = json.load(open(Path(__file__).parent.parent / "graph" / "graph_edges.json"))
pages = {i for i, p in g["pages"].items() if not p["alias"]}
want = set()
for e in g["edges"]:
    want.add((e["label"], e["from"], e["to"] or ("N", e["node"]["group"], e["node"]["value"])))
def read(pid):
    with c() as s:
        r = s.post(f"{KB_URL}/graph", json={"query": {"prop": "path", "source": {"value": pid, "match": "exact", "type": "resource"}, "undirected": True}, "top_k": 500}).json()["paths"]
    return pid, len(r), r
got, truncated = set(), []
with ThreadPoolExecutor(8) as ex:
    for pid, n, paths in ex.map(read, sorted(pages)):
        if n >= 500: truncated.append(pid)
        for p in paths:
            lab = p["relation"]["label"]
            if lab not in LABELS: continue
            a, b = p["source"], p["destination"]
            frm = a["value"]; to = b["value"] if b["type"] == "resource" else ("N", b["group"], b["value"])
            got.add((lab, frm, to))
missing, extra = want - got, got - want
print("written", len(want), "read back", len(got), "missing", len(missing), "unexpected", len(extra), "truncated queries", len(truncated))
print(dict(collections.Counter(l for l, _, _ in got)))
# A page whose anchored query hits the 500-path cap cannot be read back in full (platform limit,
# dominated by auto-extracted ENTITY edges). Those pages are NAMED HOLES, not passes: missing edges
# are tolerated only when they belong to a truncated page, and every other mismatch fails.
unexplained = {m for m in missing if m[1] not in truncated and m[2] not in truncated}
print("named holes (read capped at 500 paths):", [g["pages"][t]["url"] for t in truncated])
print("missing edges explained by those holes:", len(missing) - len(unexplained), "| unexplained:", len(unexplained))
sys.exit(1 if unexplained or extra else 0)
