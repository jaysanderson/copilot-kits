"""Thirty-second reset for the Clinic Knowledge Desk.

    python scripts/reset.py            # re-crawl clinic.com and re-ingest
    python scripts/reset.py --purge    # delete every resource first, then re-ingest

Nothing about a demo run mutates the knowledge base, so a reset is only needed
after the published site changes. Credentials come from apps/clinic/.env.
"""
import subprocess
import sys
from pathlib import Path

import requests

APP = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(APP / "scripts"))
from provision import read_env  # noqa: E402

PY = sys.executable


def purge(cfg):
    kb = f"{cfg['ARAG_HOST']}/kb/{cfg['KB_ID']}"
    h = {"X-NUCLIA-SERVICEACCOUNT": f"Bearer {cfg['KB_TOKEN']}"}
    removed = 0
    while True:
        # /resources paginates on pagination.last, never on .more
        r = requests.get(f"{kb}/resources", headers=h, params={"size": 50}, timeout=60)
        items = r.json().get("resources", [])
        if not items:
            break
        for res in items:
            requests.delete(f"{kb}/resource/{res['id']}", headers=h, timeout=60)
            removed += 1
        print(f"  deleted {removed}", flush=True)
    print(f"purged {removed} resources")


def main():
    cfg = read_env(APP / ".env")
    if "--purge" in sys.argv:
        purge(cfg)
        (APP / "corpus" / "index.json").write_text("[]")
    subprocess.run([PY, str(APP / "scripts" / "crawl.py")], check=True)
    subprocess.run([PY, str(APP / "scripts" / "provision.py")], check=True)
    print("\nReset complete. Redeploy so the container picks up the new record:")
    print("  flyctl deploy --ha=false --app clinic-knowledge-desk")


if __name__ == "__main__":
    main()
