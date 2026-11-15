"""Orchestrates one submission end to end: validate -> split -> legibility -> ARAG
ingest+classify -> merge into logical documents -> name transliteration/match ->
completeness/duplicate checks -> closed-vocabulary PRD-shaped verdict.

CanSubmit is always True: this is an advisory pre-check, never a submission
blocker. The human process remains authoritative.

8 Aug 2026 revision: response shape now matches the target PRD's section 12.2
field names directly (RequestId, ProcessingStatus, DetectedDocuments, ...) -
this dict IS the wire contract, not translated by a caller. See README for
the field-by-field mapping notes and honest gaps.
"""
import asyncio
import os
import shutil
import tempfile
import uuid
from datetime import datetime, timezone

import httpx

from . import arag_client as ac
from . import codes
from . import legibility
from . import pdf_split
from . import transliteration as tl

ENGINE_VERSION = "govdoc-triage-2.1.0"

DOC_TYPES = (
    "DIPLOMA", "TRANSCRIPT", "NAME_CHANGE_CERTIFICATE",
    "INSTITUTION_NAME_CHANGE_CERTIFICATE", "EQUIVALENCY_CERTIFICATE", "UNRECOGNISED",
)

# Stamp/authenticity checks apply per document type (PRD section 7.4's exact table -
# Diploma/Transcript/Institution Name Change Certificate require them, Name Change
# Certificate and Equivalency Certificate do not).
STAMP_CHECK_REQUIRED = {
    "DIPLOMA": True,
    "TRANSCRIPT": True,
    "NAME_CHANGE_CERTIFICATE": False,
    "INSTITUTION_NAME_CHANGE_CERTIFICATE": True,
    "EQUIVALENCY_CERTIFICATE": False,
    "UNRECOGNISED": False,
}

# Which document types INSTITUTION / DEGREE_TYPE / DOCUMENT_DATE are meaningful for -
# checked for "not clear" only where relevant, never flagged on a type where the field
# doesn't apply.
INSTITUTION_RELEVANT = {"DIPLOMA", "TRANSCRIPT", "INSTITUTION_NAME_CHANGE_CERTIFICATE", "EQUIVALENCY_CERTIFICATE"}
DEGREE_RELEVANT = {"DIPLOMA", "EQUIVALENCY_CERTIFICATE"}
DATE_RELEVANT = {"DIPLOMA", "TRANSCRIPT", "NAME_CHANGE_CERTIFICATE", "INSTITUTION_NAME_CHANGE_CERTIFICATE", "EQUIVALENCY_CERTIFICATE"}

REQUIRED_DOC_TYPES = ("DIPLOMA", "TRANSCRIPT")
SUPPORTED_LANGUAGES = {"he", "en", "ru", "uk", "fr"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024
MAX_PAGES_PER_FILE = 8
SUPPORTED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}

# Document status enum - PRD section 9's exact labels.
STATUS_VALID = "Valid"
STATUS_PARTIALLY_VALID = "Partially Valid"
STATUS_MISSING = "Missing"
STATUS_UNCLEAR = "Unclear"
STATUS_UNIDENTIFIED = "Unidentified"
STATUS_MISSING_STAMP = "Missing Stamp"
STATUS_INVALID_STAMP = "Invalid/Unidentified Stamp"
STATUS_ADDITIONAL_DOCUMENT_REQUIRED = "Additional Document Required"
STATUS_DUPLICATE = "Duplicate"
STATUS_MANUAL_REVIEW_REQUIRED = "Manual Review Required"


def _tri_state(value: str) -> str:
    v = (value or "UNKNOWN").upper()
    if v == "PRESENT":
        return "PRESENT"
    if v == "UNCLEAR":
        return "UNCLEAR"
    return "ABSENT"


def _clean_field(value: str) -> str:
    v = (value or "").strip()
    return "" if v.upper() == "UNKNOWN" else v


async def _process_one_page(client: httpx.AsyncClient, page, source_file: str) -> dict:
    legibility_result = legibility.assess_page(page.image_path)

    rid = await ac.upload_page(client, page.upload_filename, page.upload_bytes, page.upload_mime)
    status = await ac.wait_processed(client, rid, timeout=90)

    classify = {"fields": {}, "citations": [], "full_context": [], "raw_answer": ""}
    lang = ""
    labeler_label = None
    remi = None
    if status == "PROCESSED":
        # Indexing can lag a few seconds behind metadata.status flipping to PROCESSED
        # (observed live 8 Aug 2026) - a short buffer cuts down wasted first attempts.
        await asyncio.sleep(2.0)
        classify = await ac.classify_page_with_retry(client, rid)
        lang = await ac.resource_language(client, rid)
        # Best-effort peek at the REAL Labeler DA task's output (registered on this KB
        # 8 Aug 2026) - preferred when it has already landed. It's an async background
        # worker, so a brand-new page in a live demo often won't have it yet within a
        # couple of seconds; that's expected and falls back to the /ask-based parse
        # below, not a bug. Pre-seeded/backfilled resources will have it immediately.
        for _ in range(2):
            labeler_label = await ac.labeler_classification(client, rid)
            if labeler_label:
                break
            await asyncio.sleep(1.5)
        # Real REMi groundedness read (B39, binding) - scores the classify/extract
        # answer against the FULL retrieved page context, never the truncated
        # display citations. One call per page, same cardinality as the classify
        # call itself, so cost is negligible - not a corpus-wide task (hard rule 15
        # does not apply the way it does to graph/DA-task extraction).
        remi = await ac.score_remi(client, classify.get("raw_answer", ""), classify.get("full_context", []))

    fields = classify["fields"]
    ask_doc_type = fields.get("DOCUMENT_TYPE", "UNRECOGNISED").upper()
    if ask_doc_type not in DOC_TYPES:
        ask_doc_type = "UNRECOGNISED"
    doc_type = labeler_label if (labeler_label and labeler_label in DOC_TYPES) else ask_doc_type
    classified_by = "labeler_da_task" if doc_type == labeler_label and labeler_label else "ask_grounded_query"

    return {
        "page_number": page.page_number,
        "source_file": source_file,
        "resource_id": rid,
        "processing_status": status,
        "document_type": doc_type,
        "classified_by": classified_by,
        "remi": remi,
        "detected_language": (lang or fields.get("LANGUAGE", "").lower() or ""),
        "extracted_name": _clean_field(fields.get("APPLICANT_NAME", "")),
        "extracted_institution": _clean_field(fields.get("INSTITUTION", "")),
        "extracted_degree_type": _clean_field(fields.get("DEGREE_TYPE", "")),
        "extracted_date": _clean_field(fields.get("DOCUMENT_DATE", "")),
        "summary": fields.get("SUMMARY", ""),
        "authenticity": {
            "apostille": _tri_state(fields.get("APOSTILLE")),
            "notarisation": _tri_state(fields.get("NOTARY")),
            "certified_copy": _tri_state(fields.get("CERTIFIED_COPY")),
            "signature": _tri_state(fields.get("SIGNATURE")),
        },
        "legibility": legibility_result,
        "citations": classify["citations"][:2],
        "image_path": page.image_path,
    }


def _group_pages_into_documents(pages: list[dict]) -> list[dict]:
    """Merge consecutive same-file, same-type pages into one logical document with a page range."""
    docs = []
    current = None
    for p in pages:
        if (current and current["source_file"] == p["source_file"]
                and current["document_type"] == p["document_type"]):
            current["pages"].append(p)
        else:
            if current:
                docs.append(current)
            current = {"source_file": p["source_file"], "document_type": p["document_type"], "pages": [p]}
    if current:
        docs.append(current)
    return docs


def _assemble_document(doc: dict, declared_name: str, declared_script: str, lang: str,
                        has_name_change_cert: bool) -> dict:
    pages = doc["pages"]
    doc_type = doc["document_type"]
    page_numbers = [p["page_number"] for p in pages]
    page_range = [min(page_numbers), max(page_numbers)]

    legibility_issues = sorted({issue for p in pages for issue in p["legibility"]["issues"]})
    is_legible = not legibility_issues

    stamp_check_applies = STAMP_CHECK_REQUIRED.get(doc_type, False)
    auth = {"apostille": "ABSENT", "notarisation": "ABSENT", "certified_copy": "ABSENT", "signature": "ABSENT"}
    for k in auth:
        states = [p["authenticity"][k] for p in pages]
        if "PRESENT" in states:
            auth[k] = "PRESENT"
        elif "UNCLEAR" in states:
            auth[k] = "UNCLEAR"

    extracted_name = next((p["extracted_name"] for p in pages if p["extracted_name"]), "")
    extracted_institution = next((p["extracted_institution"] for p in pages if p["extracted_institution"]), "")
    extracted_degree = next((p["extracted_degree_type"] for p in pages if p["extracted_degree_type"]), "")
    extracted_date = next((p["extracted_date"] for p in pages if p["extracted_date"]), "")
    extracted_lang = next((p["detected_language"] for p in pages if p["detected_language"]), "")
    extracted_script = tl.detect_script(extracted_name)

    name_match = None
    if doc_type in ("DIPLOMA", "TRANSCRIPT") and extracted_name:
        name_match = tl.match_name(declared_name, declared_script, extracted_name, extracted_script)

    # Real REMi groundedness read (B39, binding) - one live call per page,
    # scored against the FULL retrieved page context (app/arag_client.py::
    # score_remi), never the truncated display citations. Aggregated to this
    # document's own WORST-scoring page (min, not average/max) - a multi-page
    # document's overall trust is bounded by its weakest-grounded page, not
    # flattered by its best one. `remi_agg` is kept on the document for the
    # Insights aggregate and the solution-architecture reveal; only the
    # qualitative badge below is default-visible, per B34 - never a raw
    # numeral in the customer-facing view.
    def _agg_remi(key):
        vals = [p["remi"][key] for p in pages if p.get("remi") and isinstance(p["remi"].get(key), (int, float))]
        return min(vals) if vals else None

    remi_agg = {
        "groundedness": _agg_remi("groundedness"),
        "context_relevance": _agg_remi("context_relevance"),
        "answer_relevance": _agg_remi("answer_relevance"),
    }
    remi_groundedness = remi_agg["groundedness"]

    # Secondary signals - used only when REMi is genuinely unavailable for this
    # document (a disclosed fallback, never a fabricated REMi score), and to
    # gate the degenerate cases no groundedness read should flatter: whether
    # the independent background Labeler DA task confirmed the same document
    # type as the live synchronous read, and whether every field relevant to
    # this document type was actually extracted (not UNKNOWN).
    labeler_confirmed = any(p.get("classified_by") == "labeler_da_task" for p in pages)
    relevant_fields_total = sum([
        doc_type in INSTITUTION_RELEVANT, doc_type in DEGREE_RELEVANT, doc_type in DATE_RELEVANT,
    ])
    relevant_fields_present = sum([
        doc_type in INSTITUTION_RELEVANT and bool(extracted_institution),
        doc_type in DEGREE_RELEVANT and bool(extracted_degree),
        doc_type in DATE_RELEVANT and bool(extracted_date),
    ])
    fields_complete = relevant_fields_total == 0 or relevant_fields_present == relevant_fields_total

    # Qualitative confidence badge (B34/B39) - REMi's own 0-5 scale drives the
    # label directly when a score is available; never a raw numeral shown.
    if doc_type == "UNRECOGNISED" or not is_legible:
        extraction_confidence = "Low"
    elif remi_groundedness is not None:
        if remi_groundedness >= 4.0:
            extraction_confidence = "High"
        elif remi_groundedness >= 2.5:
            extraction_confidence = "Moderate"
        else:
            extraction_confidence = "Low"
    elif labeler_confirmed and fields_complete:
        extraction_confidence = "High"
    elif relevant_fields_total == 0 or relevant_fields_present > 0:
        extraction_confidence = "Moderate"
    else:
        extraction_confidence = "Low"

    messages = []

    def add(code_name):
        messages.append(codes.message_for(code_name, lang))

    # --- messages: every applicable issue is reported, independently ------------
    if doc_type == "UNRECOGNISED":
        add("DOC_UNKNOWN_TYPE")
    if not is_legible:
        if "DOC_ROTATED" in legibility_issues:
            add("DOC_ROTATED")
        if "DOC_TOO_DARK" in legibility_issues:
            add("DOC_DARK_OR_LOW_QUALITY")
        if "DOC_BLURRED" in legibility_issues or "DOC_CROPPED" in legibility_issues:
            add("DOC_UNREADABLE")
    if extracted_lang and extracted_lang not in SUPPORTED_LANGUAGES:
        add("DOC_LANGUAGE_UNSUPPORTED")
    if stamp_check_applies and "ABSENT" in auth.values():
        add("DOC_STAMP_MISSING")
    if stamp_check_applies and "UNCLEAR" in auth.values():
        add("DOC_STAMP_NOT_CLEAR")
    name_mismatch = bool(name_match and name_match["status"] == "MISMATCH")
    if name_mismatch:
        add("DOC_NAME_TRANSLATION_MISMATCH")
        if not has_name_change_cert:
            add("DOC_MISSING_NAME_CHANGE")
    # First/last positional token comparison - independent of the whole-name check
    # above (a long shared surname can pull the whole-name score above threshold
    # even when the first name genuinely differs, and vice versa).
    first_name_mismatch = bool(name_match and name_match.get("first_name_match")
                                and name_match["first_name_match"]["status"] == "MISMATCH")
    last_name_mismatch = bool(name_match and name_match.get("last_name_match")
                               and name_match["last_name_match"]["status"] == "MISMATCH")
    if first_name_mismatch:
        add("DOC_FIRST_NAME_MISMATCH")
    if last_name_mismatch:
        add("DOC_LAST_NAME_MISMATCH")
    # Secondary, lower-severity clarity checks - only where the field is relevant to
    # this document type, so a name-change certificate is never dinged for a missing
    # degree type it was never expected to carry.
    if doc_type in INSTITUTION_RELEVANT and not extracted_institution:
        add("DOC_INSTITUTION_NOT_CLEAR")
    if doc_type in DEGREE_RELEVANT and not extracted_degree:
        add("DOC_DEGREE_NOT_CLEAR")
    if doc_type in DATE_RELEVANT and not extracted_date:
        add("DOC_DATE_NOT_CLEAR")

    # --- status: exactly one, in priority order (PRD section 9) -----------------
    if doc_type == "UNRECOGNISED":
        status = STATUS_UNIDENTIFIED
    elif not is_legible:
        status = STATUS_UNCLEAR
    elif extracted_lang and extracted_lang not in SUPPORTED_LANGUAGES:
        status = STATUS_MANUAL_REVIEW_REQUIRED
    elif stamp_check_applies and "ABSENT" in auth.values():
        status = STATUS_MISSING_STAMP
    elif stamp_check_applies and "UNCLEAR" in auth.values():
        status = STATUS_INVALID_STAMP
    elif name_mismatch or first_name_mismatch or last_name_mismatch:
        status = STATUS_ADDITIONAL_DOCUMENT_REQUIRED if not has_name_change_cert else STATUS_PARTIALLY_VALID
    elif (doc_type in INSTITUTION_RELEVANT and not extracted_institution) \
            or (doc_type in DEGREE_RELEVANT and not extracted_degree) \
            or (doc_type in DATE_RELEVANT and not extracted_date):
        status = STATUS_PARTIALLY_VALID
    else:
        status = STATUS_VALID

    return {
        "document_id": f"doc_{uuid.uuid4().hex[:8]}",
        "document_type": doc_type,
        "status": status,
        "source_file": doc["source_file"],
        "page_range": page_range,
        "detected_language": extracted_lang,
        "extracted_name": extracted_name or None,
        "extracted_institution": extracted_institution or None,
        "extracted_degree_type": extracted_degree or None,
        "extracted_date": extracted_date or None,
        "legibility_issues": legibility_issues,
        "stamp_check_applies": stamp_check_applies,
        "authenticity_indicators": (
            {k: {"state": v, "confidence": "indicative"} for k, v in auth.items()}
            if stamp_check_applies else None
        ),
        "name_match": name_match,
        "extraction_confidence": extraction_confidence,
        "remi": remi_agg,
        "citations": [
            {"page_number": p["page_number"], "snippet": c["snippet"], "score": c["score"], "thumbnail": p.get("thumbnail")}
            for p in pages for c in p["citations"]
        ],
        "pages": [
            {"page_number": p["page_number"], "resource_id": p["resource_id"],
             "thumbnail": p.get("thumbnail"), "classified_by": p.get("classified_by")}
            for p in pages
        ],
        "messages": messages,
    }


def _validate_files(files: list[tuple[str, bytes]], lang: str) -> tuple[list[tuple[str, bytes]], list[dict]]:
    """File-level gates from PRD section 4.1 (10MB / 8 pages / pdf|jpg|png only).
    Invalid files are skipped, not fatal - CanSubmit stays true regardless."""
    ok_files = []
    top_messages = []
    for filename, content in files:
        ext = os.path.splitext(filename)[1].lower()
        if ext not in SUPPORTED_EXTENSIONS:
            top_messages.append(codes.message_for("DOC_FILE_TYPE_NOT_SUPPORTED", lang))
            continue
        if len(content) > MAX_FILE_SIZE_BYTES:
            top_messages.append(codes.message_for("DOC_FILE_SIZE_EXCEEDED", lang))
            continue
        if ext == ".pdf":
            try:
                from pypdf import PdfReader
                import io
                n_pages = len(PdfReader(io.BytesIO(content)).pages)
            except Exception:
                n_pages = 0
            if n_pages > MAX_PAGES_PER_FILE:
                top_messages.append(codes.message_for("DOC_FILE_SIZE_EXCEEDED", lang))
                continue
        ok_files.append((filename, content))
    return ok_files, top_messages


async def process_submission(files: list[tuple[str, bytes]], declared_name: str,
                              declared_script: str, response_lang: str,
                              media_dir: str, request_id: str | None = None,
                              applicant_id: str = "") -> dict:
    """files: list of (filename, content_bytes). Returns the PRD-shaped verdict."""
    submission_id = request_id or f"sub_{uuid.uuid4().hex[:10]}"
    work_dir = tempfile.mkdtemp(prefix="triage-")
    all_pages = []
    top_messages: list[dict] = []

    try:
        valid_files, file_messages = _validate_files(files, response_lang)
        top_messages.extend(file_messages)

        for filename, content in valid_files:
            file_work_dir = os.path.join(work_dir, os.path.splitext(filename)[0])
            pages = pdf_split.split_file(filename, content, file_work_dir)
            async with httpx.AsyncClient() as client:
                results = await asyncio.gather(*[
                    _process_one_page(client, p, filename) for p in pages
                ])
            all_pages.extend(sorted(results, key=lambda r: r["page_number"]))

        os.makedirs(media_dir, exist_ok=True)
        for p in all_pages:
            dest = os.path.join(media_dir, f"{submission_id}_{p['source_file']}_{p['page_number']}.png")
            if os.path.exists(p["image_path"]):
                shutil.copy(p["image_path"], dest)
            p["thumbnail"] = os.path.basename(dest)

        grouped = _group_pages_into_documents(all_pages)
        found_types_raw = [g["document_type"] for g in grouped]
        has_name_change_cert = "NAME_CHANGE_CERTIFICATE" in found_types_raw

        documents = [
            _assemble_document(g, declared_name, declared_script, response_lang, has_name_change_cert)
            for g in grouped
        ]

        # Duplicate-type detection (cross-document, PRD DOC_DUPLICATE_TYPE) - only
        # among real, identified types, never UNRECOGNISED.
        from collections import Counter
        type_counts = Counter(d["document_type"] for d in documents if d["document_type"] != "UNRECOGNISED")
        for d in documents:
            if type_counts.get(d["document_type"], 0) > 1:
                d["status"] = STATUS_DUPLICATE
                d["messages"].append(codes.message_for("DOC_DUPLICATE_TYPE", response_lang))

        missing_documents = []

        # Institution-name consistency (cross-document, PRD DOC_MISSING_INSTITUTION_NAME_APPRO /
        # DOC_INSTITUTION_NAME_MISMATCH) - compare extracted institution names pairwise across
        # every document type where the field is meaningful. A genuine mismatch with no
        # institution name-change certificate present is a completeness gap (the applicant
        # needs to explain the discrepancy); a mismatch WITH a certificate present is a
        # narrower "please confirm this reconciles" flag rather than a missing-document one.
        has_institution_change_cert = "INSTITUTION_NAME_CHANGE_CERTIFICATE" in found_types_raw
        institution_docs = [d for d in documents
                             if d["document_type"] in INSTITUTION_RELEVANT and d["extracted_institution"]]
        institution_mismatch_found = False
        for i in range(len(institution_docs)):
            for j in range(i + 1, len(institution_docs)):
                if tl.similarity(institution_docs[i]["extracted_institution"],
                                  institution_docs[j]["extracted_institution"]) < 0.72:
                    institution_mismatch_found = True
        if institution_mismatch_found:
            code_name = "DOC_INSTITUTION_NAME_MISMATCH" if has_institution_change_cert else "DOC_MISSING_INSTITUTION_NAME_APPRO"
            for d in institution_docs:
                d["messages"].append(codes.message_for(code_name, response_lang))
                if d["status"] == STATUS_VALID:
                    d["status"] = STATUS_PARTIALLY_VALID if has_institution_change_cert else STATUS_ADDITIONAL_DOCUMENT_REQUIRED
            if not has_institution_change_cert:
                missing_documents.append({"document_type": "INSTITUTION_NAME_CHANGE_CERTIFICATE", "status": STATUS_MISSING})

        # Completeness: a required type that never appears anywhere in the submission.
        found_types = {d["document_type"] for d in documents}
        for required_type in REQUIRED_DOC_TYPES:
            if required_type not in found_types:
                code_name = f"DOC_MISSING_{required_type}"
                top_messages.append(codes.message_for(code_name, response_lang))
                missing_documents.append({"document_type": required_type, "status": STATUS_MISSING})
        if any(d["status"] == STATUS_ADDITIONAL_DOCUMENT_REQUIRED for d in documents) and not has_name_change_cert:
            top_messages.append(codes.message_for("DOC_MISSING_NAME_CHANGE_CERTIFICATE", response_lang))
            missing_documents.append({"document_type": "NAME_CHANGE_CERTIFICATE", "status": STATUS_MISSING})

        # Overall rollup.
        severities = set(m["severity"] for m in top_messages)
        for d in documents:
            for m in d["messages"]:
                severities.add(m["severity"])
        if codes.SEVERITY_REVIEW in severities:
            overall = "NEEDS_HUMAN_REVIEW"
        elif codes.SEVERITY_ATTENTION in severities:
            overall = "NEEDS_ATTENTION"
        else:
            overall = "READY"

        if any(d["status"] in (STATUS_UNCLEAR, STATUS_UNIDENTIFIED) for d in documents):
            recommended_action = "Recommended to upload again"
        elif overall != "READY":
            recommended_action = "Recommended to complete documents"
        else:
            recommended_action = "Continue submission"

        rollup_code = "DOC_ALL_VALID" if overall == "READY" else "DOC_CAN_SUBMIT_WITH_WARNINGS"
        candidate_messages = [{**codes.message_for(rollup_code, response_lang), "document_id": None}]
        candidate_messages += [{**m, "document_id": None} for m in top_messages]
        for d in documents:
            candidate_messages += [{**m, "document_id": d["document_id"]} for m in d["messages"]]

        processing_status = "Completed" if valid_files else "Failed"
        if len(valid_files) < len(files):
            processing_status = "Partial" if valid_files else "Failed"

        verdict = {
            "RequestId": submission_id,
            "ApplicantId": applicant_id or None,
            "ProcessingStatus": processing_status,
            "ProcessingDateTime": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "EngineVersion": ENGINE_VERSION,
            "ResponseLanguage": response_lang,
            "CanSubmit": True,
            "RecommendedAction": recommended_action,
            "DetectedDocuments": documents,
            "SplitDocuments": [
                {"source_file": d["source_file"], "page_range": d["page_range"], "document_type": d["document_type"]}
                for d in documents
            ],
            "MissingDocuments": missing_documents,
            "DocumentValidationResults": [
                {"document_id": d["document_id"], "document_type": d["document_type"],
                 "page_range": d["page_range"], "status": d["status"]}
                for d in documents
            ],
            "StampsValidationResults": [
                {"document_id": d["document_id"], "document_type": d["document_type"],
                 "page_range": d["page_range"], "applicable": d["stamp_check_applies"],
                 "indicators": d["authenticity_indicators"]}
                for d in documents
            ],
            "NameMatchingResults": [
                {"document_id": d["document_id"], "document_type": d["document_type"],
                 "page_range": d["page_range"], **d["name_match"]}
                for d in documents if d["name_match"]
            ],
            "CandidateMessages": candidate_messages,
            "SplitDocumentFiles": [
                {"document_id": d["document_id"], "page_number": p["page_number"],
                 "resource_id": p["resource_id"], "thumbnail": p["thumbnail"],
                 "classified_by": p["classified_by"]}
                for d in documents for p in d["pages"]
            ],
            # Supplementary, not in the PRD's field list - the applicant's own
            # declared identity, kept for the officer console's display only.
            "applicant": {"declared_name": declared_name, "declared_name_script": declared_script},
            "overall_status": overall,
        }
        return verdict
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)
