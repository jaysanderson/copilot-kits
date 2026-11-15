"""Print the reach figures shown on /wander, derived by the same code the route uses (graphwalk.py).
Offline: reads graph/graph_edges.json only, no platform call. Re-run after any rebuild of the graph.
DEFINITIONS (stated so the figure can be re-derived): tree neighbours = parent (nearest ancestor path present in the
graph), children, and pages sharing that parent; thread neighbours = every other page sharing at least one surfaced
thread; STRANDED = a page with one or no tree neighbour AND three or more thread-neighbour PAGES (not three threads).
Under the same tree, 25 pages have one or no tree neighbour and 21 of them have three or more thread-neighbour pages;
only 8 of the 25 belong to three or more distinct threads. A reading of "reached by three or more threads" as distinct
threads gives 8, as thread-neighbour pages gives 21: the surface uses the second and says so.
Scope: the graphed pages (www.university.edu.au, short-link and fragment duplicates excluded); threads are the
surfaced ones only (topic, audience, campus). The tree is parent, children and siblings by URL path."""
import hashlib, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import graphwalk as gw

src = Path(__file__).resolve().parent.parent / "graph" / "graph_edges.json"
print("source:", src.name, hashlib.md5(src.read_bytes()).hexdigest()[:12], "| pages in file:", len(gw.PAGES), "| graphed:", gw.SITE["pages"])
print(json.dumps(gw.SITE, indent=1))
# controls: a leaf with no thread must read 0 thread reach; a page's reach never exceeds the graphed pages
loners = [i for i in gw.THREAD if not gw.THREAD[i]]
assert loners and all(gw.page_reach(i)["thread_one"] == 0 for i in loners), "no-thread control failed"
assert all(gw.page_reach(i)["thread_two"] < gw.SITE["pages"] and gw.page_reach(i)["tree_two"] < gw.SITE["pages"] for i in gw.THREAD)
assert gw.SITE["pages"] > 0
print("controls ok:", len(loners), "no-thread pages read 0")
low = [i for i in gw.THREAD if len(gw.TREE[i]) <= 1]
print("tree-stranded (<=1 tree neighbour):", len(low), "| with >=3 thread-neighbour pages:", sum(1 for i in low if len(gw.THREAD[i]) >= 3))
worst = sorted(gw.THREAD, key=lambda i: len(gw.TREE[i]) - len(gw.THREAD[i]))[:5]
for i in worst: print(" tree %3d vs thread %3d  %s" % (len(gw.TREE[i]), len(gw.THREAD[i]), gw.PAGES[i]["title"]))
