"""Set origin.path (the URL path) on every resource so a section scope can use the native
origin_path prefix filter. Metadata only: no reprocessing, no LLM call. Idempotent."""
import sys, httpx
from urllib.parse import urlparse
from pathlib import Path
env = dict(l.strip().split('=', 1) for l in open(Path(__file__).parent.parent / '.env') if '=' in l and not l.startswith('#'))
k = env['KB_URL'].split('#')[0].strip().rstrip('/'); t = env['KB_TOKEN'].split('#')[0].strip()
h = {"X-NUCLIA-SERVICEACCOUNT": "Bearer " + t, "X-Synchronous": "true", "Content-Type": "application/json"}
limit = int(sys.argv[1]) if len(sys.argv) > 1 else 10**6
ids, page = [], 0
while True:
    r = httpx.get(k + "/resources", params={"page": page, "size": 100}, headers=h, timeout=30).json()
    if not r.get("resources"): break
    ids += [x["id"] for x in r["resources"]]; page += 1
done = skipped = 0
for rid in ids[:limit]:
    d = httpx.get(f"{k}/resource/{rid}", params={"show": "origin"}, headers=h, timeout=30).json()
    o = d.get("origin") or {}
    path = urlparse(o.get("url") or "").path
    if not path or o.get("path") == path: skipped += 1; continue
    p = httpx.patch(f"{k}/resource/{rid}", json={"origin": {**o, "path": path}}, headers=h, timeout=30)
    p.raise_for_status(); done += 1
print("resources", len(ids), "patched", done, "skipped", skipped)
