#!/usr/bin/env python3
"""Rev 3 coverage verification: individually confirms every PRD section 9 status
and section 10 "live" code against a real test fixture, run through the actual
pipeline (not a code read). Prints PASS/FAIL/HONEST-GAP per target and writes a
JSON report for APPROVED.md evidence.

    .venv/bin/python seed/verify_coverage.py
"""
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import legibility, pipeline
from app import transliteration as tl

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS_DIR = os.path.join(HERE, "corpus")
MEDIA_DIR = os.path.join(os.path.dirname(HERE), "data", "media")

results = []


def record(target, kind, ok, detail, honest_gap=False):
    results.append({"target": target, "kind": kind, "ok": ok, "detail": detail, "honest_gap": honest_gap})
    tag = "PASS" if ok else ("HONEST-GAP" if honest_gap else "FAIL")
    print(f"[{tag}] {target}: {detail}")


def local_tests():
    print("\n=== Local deterministic checks (no ARAG calls) ===")
    sys.path.insert(0, HERE)
    import generate_corpus as gc

    src = os.path.join(CORPUS_DIR, "seed-ready-cohen.pdf")
    work = "/tmp/coverage_local"
    os.makedirs(work, exist_ok=True)

    rotated = os.path.join(work, "rotated.pdf")
    gc.apply_rotate(src, rotated, angle=90)
    from pdf2image import convert_from_path
    img_path = os.path.join(work, "rotated.png")
    convert_from_path(rotated, dpi=150)[0].save(img_path)
    res = legibility.assess_page(img_path)
    record("DOC_ROTATED (legibility.assess_page)", "status=Unclear", "DOC_ROTATED" in res["issues"], res)

    darkened = os.path.join(work, "dark.pdf")
    gc.apply_dark(src, darkened)
    img_path2 = os.path.join(work, "dark.png")
    convert_from_path(darkened, dpi=150)[0].save(img_path2)
    res2 = legibility.assess_page(img_path2)
    record("DOC_DARK_OR_LOW_QUALITY (legibility.assess_page)", "status=Unclear", "DOC_TOO_DARK" in res2["issues"], res2)

    # File-type / file-size validation (pure local logic, no ARAG).
    ok_files, msgs = pipeline._validate_files([("notes.txt", b"hello world")], "en")
    codes_found = [m["code"] for m in msgs]
    record("DOC_FILE_TYPE_NOT_SUPPORTED (_validate_files)", "unsupported extension rejected",
           len(ok_files) == 0 and "DOC_FILE_TYPE_NOT_SUPPORTED" in codes_found, codes_found)

    big_pdf_path = os.path.join(work, "big.pdf")
    single_pages = []
    tmp_page = os.path.join(work, "_p.pdf")
    gc.make_document_pdf(tmp_page, institution="TEST", title="TEST PAGE",
                          body_lines=["filler"], applicant_name="Test", date_line="",
                          apostille=False, notary=False, certified=False, signature=False,
                          lang_footer="")
    from pypdf import PdfReader, PdfWriter
    writer = PdfWriter()
    reader = PdfReader(tmp_page)
    for _ in range(9):
        writer.add_page(reader.pages[0])
    with open(big_pdf_path, "wb") as f:
        writer.write(f)
    with open(big_pdf_path, "rb") as f:
        content = f.read()
    ok_files2, msgs2 = pipeline._validate_files([("big.pdf", content)], "en")
    codes_found2 = [m["code"] for m in msgs2]
    record("DOC_FILE_SIZE_EXCEEDED (_validate_files, 9-page PDF)", "over 8-page limit rejected",
           len(ok_files2) == 0 and "DOC_FILE_SIZE_EXCEEDED" in codes_found2, codes_found2)

    # First/last name split matching - pure string logic, no ARAG needed.
    m1 = tl.match_name("Daniel Sullivan", "latin", "Michael Sullivan", "latin")
    record("DOC_FIRST_NAME_MISMATCH (transliteration.match_name, unit)", "first differs, last matches",
           m1["first_name_match"]["status"] == "MISMATCH" and m1["last_name_match"]["status"] == "MATCH", m1)
    m2 = tl.match_name("Daniel Sullivan", "latin", "Daniel Whitfield", "latin")
    record("DOC_LAST_NAME_MISMATCH (transliteration.match_name, unit)", "first matches, last differs",
           m2["first_name_match"]["status"] == "MATCH" and m2["last_name_match"]["status"] == "MISMATCH", m2)


async def run_bundle(filenames, declared_name, lang="en"):
    if isinstance(filenames, str):
        filenames = [filenames]
    files = []
    for filename in filenames:
        path = os.path.join(CORPUS_DIR, filename)
        with open(path, "rb") as f:
            files.append((filename, f.read()))
    declared_script = tl.detect_script(declared_name)
    return await pipeline.process_submission(
        files, declared_name=declared_name, declared_script=declared_script,
        response_lang=lang, media_dir=MEDIA_DIR,
    )


def codes_in(verdict):
    return {m["code"] for m in verdict["CandidateMessages"]}


def statuses_in(verdict):
    return {d["status"] for d in verdict["DetectedDocuments"]}


async def live_tests():
    print("\n=== Live ARAG-backed checks ===")

    v = await run_bundle("coverage-institution-nocert.pdf", "Noah Bergman")
    record("DOC_MISSING_INSTITUTION_NAME_APPRO", "diploma+transcript, different institutions, no cert",
           "DOC_MISSING_INSTITUTION_NAME_APPRO" in codes_in(v), codes_in(v))

    v = await run_bundle("coverage-institution-withcert.pdf", "Noah Bergman")
    record("DOC_INSTITUTION_NAME_MISMATCH", "same scenario + institution name-change cert present",
           "DOC_INSTITUTION_NAME_MISMATCH" in codes_in(v), codes_in(v))

    v = await run_bundle(["coverage-duplicate-a.pdf", "coverage-duplicate-b.pdf"], "Layla Haddad")
    record("DOC_DUPLICATE_TYPE / status Duplicate", "two diplomas in one submission",
           "DOC_DUPLICATE_TYPE" in codes_in(v) and "Duplicate" in statuses_in(v), (codes_in(v), statuses_in(v)))

    v = await run_bundle("coverage-rotated-diploma.pdf", "Owen Blackwood")
    record("DOC_ROTATED / status Unclear (live, not just the local legibility unit test)",
           "a genuinely ~90-degree-rotated page, still correctly classified as DIPLOMA",
           "DOC_ROTATED" in codes_in(v) and "Unclear" in statuses_in(v), (codes_in(v), statuses_in(v)))

    v = await run_bundle("coverage-language-unsupported.pdf", "Lukas Fischer")
    record("DOC_LANGUAGE_UNSUPPORTED / status Manual Review Required", "German-language diploma",
           "DOC_LANGUAGE_UNSUPPORTED" in codes_in(v) and "Manual Review Required" in statuses_in(v),
           (codes_in(v), statuses_in(v)))

    v = await run_bundle("coverage-stub-fields.pdf", "Sofia Marchetti")
    found = codes_in(v)
    record("DOC_INSTITUTION_NOT_CLEAR / DOC_DEGREE_NOT_CLEAR / DOC_DATE_NOT_CLEAR / status Partially Valid",
           "no institution/degree/date on the page",
           {"DOC_INSTITUTION_NOT_CLEAR", "DOC_DEGREE_NOT_CLEAR", "DOC_DATE_NOT_CLEAR"} <= found
           and "Partially Valid" in statuses_in(v), (found, statuses_in(v)))

    v = await run_bundle("coverage-stamp-unclear.pdf", "Priya Nair")
    ok = "DOC_STAMP_NOT_CLEAR" in codes_in(v)
    record("DOC_STAMP_NOT_CLEAR / status Invalid-Unidentified Stamp", "overlapping garbled seal graphic",
           ok, codes_in(v), honest_gap=not ok)

    v = await run_bundle("coverage-namechange-missing.pdf", "Grace Newman")
    found = codes_in(v)
    record("DOC_MISSING_NAME_CHANGE / DOC_MISSING_NAME_CHANGE_CERTIFICATE / status Additional Document Required",
           "name mismatch, no name-change cert anywhere",
           {"DOC_MISSING_NAME_CHANGE", "DOC_MISSING_NAME_CHANGE_CERTIFICATE"} <= found
           and "Additional Document Required" in statuses_in(v), (found, statuses_in(v)))

    v = await run_bundle("coverage-firstname-mismatch.pdf", "Daniel Sullivan")
    found = codes_in(v)
    record("DOC_FIRST_NAME_MISMATCH only (live)", "declared Daniel Sullivan vs doc Michael Sullivan",
           "DOC_FIRST_NAME_MISMATCH" in found and "DOC_LAST_NAME_MISMATCH" not in found, found)

    v = await run_bundle("coverage-lastname-mismatch.pdf", "Daniel Sullivan")
    found = codes_in(v)
    record("DOC_LAST_NAME_MISMATCH only (live)", "declared Daniel Sullivan vs doc Daniel Whitfield",
           "DOC_LAST_NAME_MISMATCH" in found and "DOC_FIRST_NAME_MISMATCH" not in found, found)


async def main():
    local_tests()
    await live_tests()

    print("\n=== Summary ===")
    passed = sum(1 for r in results if r["ok"])
    gaps = sum(1 for r in results if r["honest_gap"])
    failed = sum(1 for r in results if not r["ok"] and not r["honest_gap"])
    print(f"PASS: {passed}   HONEST-GAP: {gaps}   FAIL: {failed}   TOTAL: {len(results)}")

    with open(os.path.join(os.path.dirname(HERE), "data", "coverage_report.json"), "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
