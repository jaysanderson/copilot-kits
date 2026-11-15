"""Seed the demo: start a REAL crawl of a website through the product's own API and wait until it is ready.

    python server/scripts/seed.py --api http://localhost:8811 --url https://your-app.fly.dev/
    python server/scripts/seed.py --purge ...      # 30-second reset first: delete every resource and local record

Nothing is pre-canned: the crawl, indexing, extraction and proposals are produced fresh by the live platform.
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path

import httpx

ap = argparse.ArgumentParser()
ap.add_argument("--api", default="http://localhost:8811")
ap.add_argument("--url", default="https://your-app.fly.dev/")
ap.add_argument("--purge", action="store_true")
ap.add_argument("--max-pages", type=int, default=60)
a = ap.parse_args()
if a.purge:
    subprocess.run([sys.executable, str(Path(__file__).resolve().parent / "purge_kb.py")], check=True)
import os
c = httpx.Client(timeout=30, headers={"X-SemanticSite-Key": os.environ.get("SS_ACCESS_KEY", "")})   # key for a gated instance; empty against a local open one
sid = c.post(f"{a.api}/api/sites", json={"url": a.url, "max_pages": a.max_pages}).json()["id"]
print("site", sid)
last = ""
while True:
    d = c.get(f"{a.api}/api/sites/{sid}").json()
    line = f"{d['state']}: {d['detail']}"
    if line != last:
        print(line)
        last = line
    if d["state"] in ("ready", "failed"):
        break
    time.sleep(4)
print(d["error"] or f"ready: {d['counts']}  coverage {d['coverage_percent']}%  model tokens/page {d['cost'].get('tokens_per_page')}")
sys.exit(0 if d["state"] == "ready" else 1)
