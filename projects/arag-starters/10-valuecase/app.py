"""ROI & Value Case tool - Progress Agentic RAG.

Rebuilt from a stateless client-side calculator (work item 0be7b846, GM
rejection: "this seems more like a demo page... needs to be better than
other products on the market for this task, such as Shark Finesse") into a
persistent, day-to-day value-engineering tool: cases survive past the
meeting they were built in, every input carries who-gave-it provenance,
scenarios and sensitivity are native, and real time-phased NPV/IRR/Payback
back the value case, alongside branded PowerPoint/Word exports.

Still makes zero ARAG API calls and holds no Knowledge Box or ARAG key -
the only secret this app has is its own access passphrase (a case holds a
real account name and a buyer's real numbers, so it cannot sit on an
unauthenticated public URL, team-lead directive 22 Sep 2026).

Run locally:  ../../.venv/bin/python -m uvicorn app:app --port 8098
"""
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")  # must run before auth/db read their env vars at import time

from fastapi import Cookie, Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import io

import auth
import db
from finance import evaluate_case, sensitivity_ranking
from levers import LEVERS, PRICING, case_scenario_totals, clamp_input_value
import exports

STAGES = ["discovery", "evaluation", "decision", "delivery", "renewal"]

app = FastAPI(title="ROI & Value Case Tool", docs_url=None, redoc_url=None, openapi_url=None)


@app.on_event("startup")
def _startup():
    db.init_db()


@app.middleware("http")
async def noindex(request: Request, call_next):
    resp = await call_next(request)
    resp.headers["X-Robots-Tag"] = "noindex, nofollow"
    return resp


def require_auth(roi_session: Optional[str] = Cookie(default=None)):
    if not auth.verify_session_cookie(roi_session):
        raise HTTPException(status_code=401, detail="Not authenticated")
    return True


def _shape_case(case: dict) -> dict:
    """The wire shape returned by every case-reading AND every case-mutating
    endpoint. Every save endpoint returns this (not {"ok": true}) so the
    client can apply the server's own post-write state to its local cache
    instead of trusting its own possibly-stale copy - see the "stale
    in-memory case" fix, demo-tester finding 1, 22 Sep 2026."""
    import json
    case = dict(case)
    case["discovery"] = json.loads(case.pop("discovery_json") or "{}")
    case["selected_levers"] = json.loads(case.pop("selected_levers") or "[]")
    return case


def _get_shaped_case_or_404(case_id: str) -> dict:
    case = db.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return _shape_case(case)


# ---------------------------------------------------------------- auth

class LoginBody(BaseModel):
    passphrase: str


@app.post("/api/login")
def login(body: LoginBody, response: Response):
    if not auth.check_passphrase(body.passphrase):
        raise HTTPException(status_code=403, detail="Incorrect passphrase")
    cookie_value = auth.make_session_cookie_value()
    response.set_cookie(
        auth.COOKIE_NAME, cookie_value, max_age=auth.COOKIE_MAX_AGE,
        httponly=True, secure=True, samesite="lax",
    )
    return {"ok": True}


@app.post("/api/logout")
def logout(response: Response):
    response.delete_cookie(auth.COOKIE_NAME)
    return {"ok": True}


@app.get("/api/session")
def session_status(roi_session: Optional[str] = Cookie(default=None)):
    return {"authenticated": auth.verify_session_cookie(roi_session)}


# ---------------------------------------------------------------- reference data

@app.get("/api/levers")
def get_levers(_: bool = Depends(require_auth)):
    return {"levers": LEVERS, "pricing": PRICING}


# ---------------------------------------------------------------- cases

class NewCaseBody(BaseModel):
    account_name: str
    seller_name: str


@app.get("/api/cases")
def api_list_cases(_: bool = Depends(require_auth)):
    return {"cases": db.list_cases()}


@app.post("/api/cases")
def api_create_case(body: NewCaseBody, _: bool = Depends(require_auth)):
    if not body.account_name.strip() or not body.seller_name.strip():
        raise HTTPException(status_code=400, detail="Account name and seller name are both required")
    case_id = db.create_case(body.account_name.strip(), body.seller_name.strip())
    return {"id": case_id}


@app.get("/api/cases/{case_id}")
def api_get_case(case_id: str, _: bool = Depends(require_auth)):
    return _get_shaped_case_or_404(case_id)


class UpdateCaseBody(BaseModel):
    account_name: Optional[str] = None
    seller_name: Optional[str] = None
    stage: Optional[str] = None
    discount_rate: Optional[float] = None
    horizon_months: Optional[int] = None
    pricing_tier: Optional[str] = None
    custom_monthly_cost: Optional[float] = None
    one_time_cost: Optional[float] = None
    discovery: Optional[dict] = None
    selected_levers: Optional[list] = None


@app.put("/api/cases/{case_id}")
def api_update_case(case_id: str, body: UpdateCaseBody, _: bool = Depends(require_auth)):
    if not db.get_case(case_id):
        raise HTTPException(status_code=404, detail="Case not found")
    if body.stage is not None and body.stage not in STAGES:
        raise HTTPException(status_code=400, detail=f"stage must be one of {STAGES}")
    import json
    fields = body.dict(exclude_unset=True)
    if "discovery" in fields:
        fields["discovery_json"] = json.dumps(fields.pop("discovery"))
    if "selected_levers" in fields:
        fields["selected_levers"] = json.dumps(fields["selected_levers"])
    db.update_case_fields(case_id, fields)
    return _get_shaped_case_or_404(case_id)


@app.delete("/api/cases/{case_id}")
def api_delete_case(case_id: str, _: bool = Depends(require_auth)):
    if not db.get_case(case_id):
        raise HTTPException(status_code=404, detail="Case not found")
    db.delete_case(case_id)
    return {"ok": True}


# ---------------------------------------------------------------- lever inputs

VALUE_SCENARIO_KEYS = ("conservative", "expected", "aggressive")
META_KEYS = ("measure_in_pov", "provided_by_name", "provided_by_role", "provided_at", "source_type")


@app.put("/api/cases/{case_id}/levers/{lever_id}/inputs/{input_key}")
async def api_put_input(case_id: str, lever_id: str, input_key: str, request: Request, _: bool = Depends(require_auth)):
    """PARTIAL update, by design (demo-tester finding 1, 22 Sep 2026): the
    request body carries ONLY the field(s) the user actually just changed -
    e.g. `{"expected": 400}` from one scenario field's blur, or
    `{"provided_by_name": "Dana Ho"}` from the provenance name field's blur.
    Any key genuinely omitted is left exactly as stored - never nulled.
    This is what makes a stale client-side snapshot harmless: even if the
    browser's local copy of this input's OTHER columns is out of date, this
    call cannot touch them because it never sends them."""
    if not db.get_case(case_id):
        raise HTTPException(status_code=404, detail="Case not found")
    body = await request.json()
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="Body must be a JSON object")
    # Server-side clamp (roi-case-tester finding, 22 Sep 2026): the client
    # clamps on blur, but a raw API PUT bypasses the UI entirely - verified
    # a 150% fraction and a negative count were both accepted and stored
    # verbatim. Every write funnels through clamp_input_value so the
    # database can never hold a value the UI itself would refuse, no
    # matter how the write arrived.
    values = {k: clamp_input_value(lever_id, input_key, body[k]) for k in VALUE_SCENARIO_KEYS if k in body}
    meta = {k: body[k] for k in META_KEYS if k in body}
    db.upsert_input_partial(case_id, lever_id, input_key, values, meta)
    return _get_shaped_case_or_404(case_id)


class OwnerBody(BaseModel):
    owner_name: Optional[str] = None
    owner_role: Optional[str] = None


@app.put("/api/cases/{case_id}/levers/{lever_id}/owner")
def api_put_owner(case_id: str, lever_id: str, body: OwnerBody, _: bool = Depends(require_auth)):
    if not db.get_case(case_id):
        raise HTTPException(status_code=404, detail="Case not found")
    db.upsert_owner(case_id, lever_id, body.owner_name, body.owner_role)
    return _get_shaped_case_or_404(case_id)


# ---------------------------------------------------------------- compute

def _values_pov_maps(case):
    values_by = {}
    pov_by = {}
    for row in case["values"]:
        values_by.setdefault((row["lever_id"], row["input_key"]), {})[row["scenario"]] = row["value"]
    for row in case["meta"]:
        pov_by[(row["lever_id"], row["input_key"])] = bool(row["measure_in_pov"])
    return values_by, pov_by


def _monthly_cost(case):
    tier = case.get("pricing_tier") or "starter"
    if tier == "custom":
        return case.get("custom_monthly_cost") or 0.0
    return PRICING.get(tier, PRICING["starter"])


@app.post("/api/cases/{case_id}/compute")
def api_compute(case_id: str, _: bool = Depends(require_auth)):
    case = db.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    import json
    selected = json.loads(case["selected_levers"] or "[]")
    values_by, pov_by = _values_pov_maps(case)
    monthly_cost = _monthly_cost(case)

    scenarios = {}
    for scenario in ("conservative", "expected", "aggressive"):
        recurring, one_time, incomplete, pov_levers = case_scenario_totals(selected, values_by, pov_by, scenario)
        fin = evaluate_case(
            recurring_monthly_benefit=recurring, one_time_benefit=one_time, monthly_cost=monthly_cost,
            one_time_cost=case.get("one_time_cost") or 0.0, discount_rate_annual=case.get("discount_rate"),
            horizon_months=case.get("horizon_months") or 24,
        )
        scenarios[scenario] = {
            "recurring_monthly": recurring, "one_time": one_time,
            "incomplete_levers": incomplete, "pov_levers": pov_levers,
            "npv": fin.npv, "irr_annual": fin.irr_annual, "irr_undefined_reason": fin.irr_undefined_reason,
            "payback_months": fin.payback_months, "credibility_flags": fin.credibility_flags,
            "cashflows": fin.cashflows,
        }

    sensitivity = sensitivity_ranking(selected, values_by, pov_by, scenario="expected")

    return {
        "scenarios": scenarios,
        "sensitivity": sensitivity,
        "monthly_cost": monthly_cost,
    }


# ---------------------------------------------------------------- exports

@app.get("/api/cases/{case_id}/export/docx")
def api_export_docx(case_id: str, _: bool = Depends(require_auth)):
    case = db.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    import json
    case["selected_levers"] = json.loads(case["selected_levers"] or "[]")
    data = exports.build_docx(case)
    filename = f"{case['account_name'].replace(' ', '-')}-arag-business-case.docx".lower()
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/api/cases/{case_id}/export/pptx")
def api_export_pptx(case_id: str, _: bool = Depends(require_auth)):
    case = db.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    import json
    case["selected_levers"] = json.loads(case["selected_levers"] or "[]")
    data = exports.build_pptx(case)
    filename = f"{case['account_name'].replace(' ', '-')}-arag-business-case.pptx".lower()
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---------------------------------------------------------------- admin / reset

class PurgeBody(BaseModel):
    passphrase: str


@app.post("/api/admin/purge")
def api_purge(body: PurgeBody):
    """The 30-second reset. Requires the passphrase again (not just the
    session cookie) as a deliberate extra guard against an idle-browser
    misclick wiping every seller's live cases."""
    if not auth.check_passphrase(body.passphrase):
        raise HTTPException(status_code=403, detail="Incorrect passphrase")
    db.purge_all()
    return {"ok": True}


# Catch API 401s cleanly as JSON rather than an HTML error page, so the
# frontend can reliably detect "show the passphrase screen" vs a real error.
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


app.mount("/", StaticFiles(directory=str(ROOT / "static"), html=True), name="static")
