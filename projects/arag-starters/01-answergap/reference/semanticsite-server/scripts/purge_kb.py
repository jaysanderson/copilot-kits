"""30-second reset: delete every resource in the SemanticSite knowledge base and clear local review state.

    python server/scripts/purge_kb.py            # resources + local store
    python server/scripts/purge_kb.py --keep-db  # resources only
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
import httpx  # noqa: E402

from server import config  # noqa: E402

H = {"X-NUCLIA-SERVICEACCOUNT": f"Bearer {config.KB_TOKEN}", "X-Synchronous": "true"}
c = httpx.Client(timeout=60)
total = 0
while True:
    r = c.get(f"{config.KB_URL}/resources", headers=H, params={"page": 0, "size": 100})
    r.raise_for_status()
    rs = r.json().get("resources", [])
    if not rs:
        break
    for x in rs:
        d = c.delete(f"{config.KB_URL}/resource/{x['id']}", headers=H)
        total += d.status_code < 300
    print("deleted so far", total)
if "--keep-db" not in sys.argv:
    from server import store
    for t in store.TABLES:
        store._db.execute(f"DELETE FROM {t}")
    store._db.commit()
    print("local store cleared")
print("done:", total, "resources deleted")
