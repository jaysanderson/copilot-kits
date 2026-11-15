"""Offline controls for the phone-number guard wiring in wander.py (no platform call).
Each case declares FIRE (guard fails) or QUIET and the expected /ask call count; the stub proves it was exercised."""
import sys, re, os
from pathlib import Path
D = Path(__file__).resolve().parent.parent; sys.path.insert(0, str(D)); os.chdir(D)
import httpx, wander, graphwalk as gw
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi.templating import Jinja2Templates

pid = next(iter(i for i, p in gw.PAGES.items() if not p.get("alias")))
calls = {"n": 0}
RESP = {"status": "success", "answer": "Call 08 9360 6000 now.", "citations": {pid + "/a/b/0-1": [[0, 5]]}}
class R:
    status_code = 200
    def json(self): return RESP
async def fake_post(self, url, **kw):
    calls["n"] += 1; return R()
httpx.AsyncClient.post = fake_post
app = FastAPI(); app.include_router(wander.build_router(kb="http://x", headers={}, model="m", templates=Jinja2Templates(directory="templates"), clean_title=lambda t: t))
cl = TestClient(app)
fails = 0
def case(name, guard_results, want_declined, want_calls):
    global fails
    q = list(guard_results); seen = {"g": 0}
    def g(d): seen["g"] += 1; return (q.pop(0) if q else guard_results[-1], [])
    wander.ask_numbers_ok = g; calls["n"] = 0
    out = cl.post("/api/wander/answer", json={"q": "x", "ids": [pid]}).json()
    ok = out.get("declined") == want_declined and calls["n"] == want_calls and seen["g"] > 0
    print("PASS" if ok else "FAIL", name, "| declined", out.get("declined"), "| ask calls", calls["n"], "| guard consulted", seen["g"])
    fails += 0 if ok else 1
case("FIRE once then QUIET: retry succeeds, answer shown, 2 calls", [False, True, True], False, 2)
case("FIRE both times: declined, never more than 2 calls", [False, False, False], True, 2)
case("QUIET first time: no retry, 1 call", [True, True], False, 1)
print("FAILS", fails); sys.exit(1 if fails else 0)
