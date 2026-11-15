"""Smoke test for the chassis - runs without a Knowledge Box.

    python smoke_test.py

Proves the process boots, the page and static files serve, the config route reflects product.json,
input validation rejects junk, the rate limit answers 429, and an unreachable ARAG host becomes a
clean 502 with a human message (never a stack trace). STANDARD.md line C5.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("ARAG_HOST", "https://example.invalid")
os.environ.setdefault("KB_ID", "smoke")
os.environ.setdefault("KB_TOKEN", "smoke")
os.environ["RATE_LIMIT_PER_MIN"] = "3"
sys.path.insert(0, str(Path(__file__).parent))

import app as starter  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

c = TestClient(starter.app, raise_server_exceptions=False)
fails: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(("PASS " if ok else "FAIL ") + name + (f"  ({detail})" if detail else ""))
    if not ok:
        fails.append(name)


r = c.get("/api/config")
check("config 200", r.status_code == 200, str(r.status_code))
check("config carries name, promise, suggested, how_it_works", all(k in r.json() for k in ("name", "promise", "suggested", "how_it_works")))
check("config has at least one suggested question", bool(r.json().get("suggested")))
check("page 200 html", c.get("/").status_code == 200 and "<title>" in c.get("/").text)
check("static css/js served", c.get("/static/app.css").status_code == 200 and c.get("/static/app.js").status_code == 200)
check("healthz", c.get("/healthz").json().get("ok") is True)
check("short question rejected 422", c.post("/api/ask", json={"question": "hi"}).status_code == 422)
r = c.post("/api/ask", json={"question": "What does the policy say about refunds?"})
check("unreachable ARAG becomes 502 with a message", r.status_code == 502 and "error" in r.json(), f"{r.status_code} {r.text[:80]}")
check("502 body is not a stack trace", "Traceback" not in r.text)
codes = [c.post("/api/ask", json={"question": "What does the policy say about refunds?"}).status_code for _ in range(3)]
check("rate limit answers 429 after the budget", 429 in codes, str(codes))
html = c.get("/").text
check("no mechanics in the page shell", not any(s in html for s in ("/ask", "/find", "Knowledge Box", "nuclia")))

print(f"\n{len(fails)} failing" if fails else "\nALL PASS")
sys.exit(1 if fails else 0)
