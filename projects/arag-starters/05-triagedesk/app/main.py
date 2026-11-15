"""FastAPI orchestration layer for the gov degree-equivalency document-triage
demo ("AkademDocs Pre-Check"). Holds the ARAG service-account token server-side
only (never reaches the browser) - the browser calls this API, this API calls
ARAG. See README.md for the seeded demo narrative and the 30-second reset.
"""
import os

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import arag_client as ac
from . import codes as codes_module
from . import pipeline
from . import store
from . import transliteration as tl

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(APP_DIR, "static")
MEDIA_DIR = os.path.join(APP_DIR, "data", "media")

app = FastAPI(title="AkademDocs Pre-Check API")


# ---------------------------------------------------------------- API routes
@app.get("/api/healthz")
def healthz():
    return {"ok": True, "arag_configured": ac.configured(), "engine_version": pipeline.ENGINE_VERSION}


@app.get("/api/codes")
def get_codes():
    return {
        "engine_version": pipeline.ENGINE_VERSION,
        "full_coverage_languages": list(codes_module.FULL_LANGS),
        "partial_coverage_languages": list(codes_module.PARTIAL_LANGS),
        "catalogue": codes_module.CATALOGUE,
    }


@app.get("/api/submissions")
def list_submissions():
    items = store.load_all()
    summaries = []
    for v in items:
        summaries.append({
            "request_id": v["RequestId"],
            "processing_date_time": v["ProcessingDateTime"],
            "applicant": v["applicant"],
            "overall_status": v["overall_status"],
            "document_count": len(v["DetectedDocuments"]),
            "document_types": [d["document_type"] for d in v["DetectedDocuments"]],
            "can_submit": v["CanSubmit"],
        })
    return {"submissions": summaries}


@app.get("/api/submissions/{request_id}")
def get_submission(request_id: str):
    v = store.get(request_id)
    if not v:
        raise HTTPException(404, "submission not found")
    return v


@app.get("/api/analytics")
def analytics():
    """Aggregates real per-document extraction output across every processed
    case - document types, legibility issues, authenticity flags, language
    mix and which classification path produced each result. Every dimension
    here is something Agentic RAG derived by reading an unstructured page
    image (or this app's deterministic local checks over that same image),
    never a pre-structured record field - see the Insights page's "How this
    works" reveal."""
    items = store.load_all()

    def counter_list(counts: dict) -> list[dict]:
        return sorted(
            [{"key": k, "count": v} for k, v in counts.items() if k],
            key=lambda x: -x["count"],
        )

    doc_types, statuses, legibility, languages = {}, {}, {}, {}
    classified_by = {"labeler_da_task": 0, "ask_grounded_query": 0}
    name_match = {"MATCH": 0, "MISMATCH": 0, "NOT_FOUND": 0}
    confidence = {"High": 0, "Moderate": 0, "Low": 0}
    remi_scored_docs = 0
    codes = {}
    by_day = {}
    total_docs = 0

    for v in items:
        day = (v.get("ProcessingDateTime") or "")[:10]
        by_day[day] = by_day.get(day, 0) + 1
        statuses[v["overall_status"]] = statuses.get(v["overall_status"], 0) + 1
        for d in v["DetectedDocuments"]:
            total_docs += 1
            doc_types[d["document_type"]] = doc_types.get(d["document_type"], 0) + 1
            for issue in d.get("legibility_issues") or []:
                legibility[issue] = legibility.get(issue, 0) + 1
            if d.get("detected_language"):
                languages[d["detected_language"]] = languages.get(d["detected_language"], 0) + 1
            conf = d.get("extraction_confidence")
            if conf in confidence:
                confidence[conf] += 1
            if d.get("remi") and isinstance(d["remi"].get("groundedness"), (int, float)):
                remi_scored_docs += 1
            for p in d.get("pages") or []:
                cb = p.get("classified_by")
                if cb in classified_by:
                    classified_by[cb] += 1
            if d.get("name_match"):
                st = d["name_match"].get("status")
                if st in name_match:
                    name_match[st] += 1
        for m in v.get("CandidateMessages") or []:
            codes[m["code"]] = codes.get(m["code"], 0) + 1

    top_codes = sorted(codes.items(), key=lambda x: -x[1])[:8]
    top_codes_out = [
        {"code": c, "count": n, "severity": codes_module.CATALOGUE.get(c, {}).get("severity", "INFO")}
        for c, n in top_codes
    ]

    return {
        "totals": {
            "submissions": len(items),
            "documents": total_docs,
            "ready": statuses.get("READY", 0),
            "needs_attention": statuses.get("NEEDS_ATTENTION", 0),
            "needs_human_review": statuses.get("NEEDS_HUMAN_REVIEW", 0),
        },
        "doc_type_distribution": counter_list(doc_types),
        "status_distribution": counter_list(statuses),
        "legibility_issues": counter_list(legibility),
        "language_distribution": counter_list(languages),
        "classified_by": classified_by,
        "name_match": name_match,
        "confidence_distribution": confidence,
        "remi_scored_documents": remi_scored_docs,
        "top_codes": top_codes_out,
        "by_day": sorted(by_day.items()),
    }


@app.post("/api/submit")
async def submit(
    # PRD section 12.1 request field names - this endpoint's request body IS the
    # target agent's own contract, not a demo-only shape. ApplicantName is the
    # single-field name this app's own UI collects; ApplicantFirstNameHebrew /
    # ApplicantLastNameHebrew are accepted too (an integrator sending the PRD's
    # split-name shape directly), concatenated when ApplicantName isn't given.
    # InstitutionCountry / DegreeType / DocumentSourceLanguage / DocLanguage are
    # accepted and echoed but not yet consumed by any check - see README "Known
    # gaps" rather than pretending they drive logic they don't.
    files: list[UploadFile] = File(...),
    RequestId: str = Form(None),
    ApplicantId: str = Form(""),
    ApplicantName: str = Form(""),
    ApplicantFirstNameHebrew: str = Form(""),
    ApplicantLastNameHebrew: str = Form(""),
    ResponseLanguage: str = Form("en"),
    DocumentSourceLanguage: str = Form(""),
    InstitutionCountry: str = Form(""),
    DegreeType: str = Form(""),
    DocLanguage: str = Form(""),
):
    if not ac.configured():
        raise HTTPException(503, "ARAG credentials not configured on the server")
    if not files:
        raise HTTPException(400, "at least one file is required")

    declared_name = ApplicantName.strip()
    if not declared_name:
        declared_name = f"{ApplicantFirstNameHebrew} {ApplicantLastNameHebrew}".strip()
    if not declared_name:
        raise HTTPException(400, "ApplicantName (or ApplicantFirstNameHebrew/ApplicantLastNameHebrew) is required")
    declared_script = tl.detect_script(declared_name)

    contents = []
    for f in files:
        data = await f.read()
        if not data:
            continue
        contents.append((f.filename, data))
    if not contents:
        raise HTTPException(400, "uploaded files were empty")

    verdict = await pipeline.process_submission(
        contents, declared_name=declared_name, declared_script=declared_script,
        response_lang=ResponseLanguage, media_dir=MEDIA_DIR,
        request_id=RequestId, applicant_id=ApplicantId,
    )
    store.save(verdict)
    return verdict


@app.get("/api/sample-bundle")
def sample_bundle():
    """Serves the seeded flagship demo bundle so the New Submission screen can
    offer a one-click 'load the demo bundle' for a fast, repeatable live demo."""
    path = os.path.join(APP_DIR, "seed", "corpus", "flagship-bundle-sidorov.pdf")
    if not os.path.isfile(path):
        raise HTTPException(404, "sample bundle not found")
    return FileResponse(path, media_type="application/pdf", filename="applicant-submission-bundle.pdf")


@app.get("/api/media/{filename}")
def get_media(filename: str):
    path = os.path.join(MEDIA_DIR, filename)
    if not os.path.isfile(path) or ".." in filename:
        raise HTTPException(404, "not found")
    return FileResponse(path, media_type="image/png")


@app.post("/api/admin/purge")
def admin_purge():
    """30-second reset: clears local submission history. Does not touch KB
    resources ingested from prior demo runs (see seed/seed.py --purge for the
    full KB + local-store reset used between live demos)."""
    store.purge()
    return {"ok": True}


# ------------------------------------------------------------ static routes
@app.get("/")
def route_dashboard():
    return FileResponse(os.path.join(STATIC_DIR, "dashboard.html"))


@app.get("/submit")
def route_submit():
    return FileResponse(os.path.join(STATIC_DIR, "submit.html"))


@app.get("/submission/{submission_id}")
def route_submission_detail(submission_id: str):
    return FileResponse(os.path.join(STATIC_DIR, "detail.html"))


@app.get("/codes")
def route_codes():
    return FileResponse(os.path.join(STATIC_DIR, "codes.html"))


@app.get("/insights")
def route_insights():
    return FileResponse(os.path.join(STATIC_DIR, "insights.html"))


app.mount("/assets", StaticFiles(directory=os.path.join(STATIC_DIR, "assets")), name="assets")
