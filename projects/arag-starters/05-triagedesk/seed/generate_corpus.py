#!/usr/bin/env python3
"""Build-time only: generates the synthetic degree-document corpus as PDFs
under seed/corpus/. Run ONCE locally (needs a Unicode TTF for Cyrillic/French
glyphs, not guaranteed present on the Fly deploy target) and commit the output
- seed.py just uploads these pre-built files at runtime, no font rendering on
the server. Re-run only if the corpus design changes.

Entirely synthetic: fictional people, fictional institutions. No real
applicant data (gate: synthetic-content-only for demo KBs).
"""
import io
import os
import random

from PIL import Image, ImageFilter, ImageEnhance
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from pdf2image import convert_from_path
import img2pdf

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "corpus")
os.makedirs(OUT, exist_ok=True)

FONT_CANDIDATES = [
    "/Library/Fonts/Arial Unicode.ttf",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
]
FONT_PATH = next((p for p in FONT_CANDIDATES if os.path.exists(p)), None)
if not FONT_PATH:
    raise SystemExit("No Unicode TTF found - install one or add a path to FONT_CANDIDATES.")
pdfmetrics.registerFont(TTFont("Unicode", FONT_PATH))

PAGE_W, PAGE_H = A4

random.seed(20260808)


def draw_seal(c, x, y, label, colour=(0.6, 0.1, 0.1)):
    c.saveState()
    c.setStrokeColorRGB(*colour)
    c.setLineWidth(1.4)
    c.circle(x, y, 32, stroke=1, fill=0)
    c.circle(x, y, 27, stroke=1, fill=0)
    c.setFont("Unicode", 6.5)
    c.setFillColorRGB(*colour)
    c.drawCentredString(x, y + 2, label[:18])
    c.drawCentredString(x, y - 8, label[18:36] if len(label) > 18 else "")
    c.restoreState()


def draw_signature(c, x, y, name):
    c.saveState()
    c.setStrokeColorRGB(0.15, 0.15, 0.4)
    c.setLineWidth(0.8)
    c.line(x, y, x + 140, y)
    c.setFont("Helvetica-Oblique", 8)
    c.setFillColorRGB(0.2, 0.2, 0.2)
    c.drawString(x, y - 12, name)
    c.restoreState()


def make_document_pdf(path, *, institution, title, body_lines, applicant_name,
                       date_line, apostille=False, notary=False, certified=False,
                       signature=False, lang_footer=""):
    c = canvas.Canvas(path, pagesize=A4)
    margin = 60

    c.setFillColorRGB(0.05, 0.15, 0.35)
    c.rect(0, PAGE_H - 90, PAGE_W, 90, fill=1, stroke=0)
    c.setFillColorRGB(1, 1, 1)
    header_size = 16
    while pdfmetrics.stringWidth(institution, "Unicode", header_size) > (PAGE_W - 2 * margin) and header_size > 9:
        header_size -= 1
    c.setFont("Unicode", header_size)
    c.drawString(margin, PAGE_H - 45, institution)
    c.setFont("Unicode", 9)
    c.drawString(margin, PAGE_H - 65, lang_footer)

    y = PAGE_H - 130
    c.setFillColorRGB(0.1, 0.1, 0.1)
    c.setFont("Unicode", 14)
    c.drawString(margin, y, title)
    y -= 30

    c.setFont("Unicode", 10.5)
    for line in body_lines:
        for wrapped in _wrap(line, 92):
            c.drawString(margin, y, wrapped)
            y -= 16
        y -= 4

    y -= 10
    c.setFont("Unicode", 10.5)
    c.drawString(margin, y, date_line)
    y -= 40

    if certified:
        c.setFont("Helvetica-BoldOblique", 9)
        c.setFillColorRGB(0.15, 0.4, 0.15)
        c.drawString(margin, y, "CERTIFIED TRUE COPY OF THE ORIGINAL")
        y -= 20

    if signature:
        draw_signature(c, margin, y, "Registrar / Authorised Signatory")

    if apostille:
        draw_seal(c, PAGE_W - 120, 160, "APOSTILLE  HAGUE CONVENTION 1961")
    if notary:
        draw_seal(c, PAGE_W - 220, 160, "NOTARY CERTIFIED", colour=(0.1, 0.1, 0.55))

    c.setFont("Unicode", 7)
    c.setFillColorRGB(0.5, 0.5, 0.5)
    c.drawString(margin, 40, f"Applicant: {applicant_name}  |  Synthetic demonstration document - not a real credential.")

    c.save()


def _wrap(text, width):
    words = text.split(" ")
    lines, cur = [], ""
    for w in words:
        if len(cur) + len(w) + 1 > width:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        lines.append(cur)
    return lines


def apply_blur(pdf_path, out_pdf_path):
    imgs = convert_from_path(pdf_path, dpi=150)
    img = imgs[0].filter(ImageFilter.GaussianBlur(radius=6))
    _image_to_pdf(img, out_pdf_path)


def apply_dark(pdf_path, out_pdf_path):
    imgs = convert_from_path(pdf_path, dpi=150)
    img = ImageEnhance.Brightness(imgs[0]).enhance(0.28)
    _image_to_pdf(img, out_pdf_path)


def apply_rotate(pdf_path, out_pdf_path, angle=90):
    """legibility.py's rotation check is an aspect-ratio-flip proxy (a slight
    skew doesn't change aspect ratio enough to trip it) - a ~90 degree turn is
    the input that actually exercises that specific heuristic."""
    imgs = convert_from_path(pdf_path, dpi=150)
    img = imgs[0].rotate(angle, expand=True, fillcolor=(255, 255, 255))
    _image_to_pdf(img, out_pdf_path)


def apply_crop(pdf_path, out_pdf_path):
    imgs = convert_from_path(pdf_path, dpi=150)
    img = imgs[0]
    w, h = img.size
    img = img.crop((int(w * 0.12), int(h * 0.10), w, h))
    _image_to_pdf(img, out_pdf_path)


def _image_to_pdf(img, out_pdf_path):
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    with open(out_pdf_path, "wb") as f:
        f.write(img2pdf.convert(buf.getvalue()))


def merge_pdfs(paths, out_path):
    from pypdf import PdfWriter
    writer = PdfWriter()
    for p in paths:
        writer.append(p)
    with open(out_path, "wb") as f:
        writer.write(f)


def build():
    # ---- 1. Flagship bundle: RU diploma (no apostille) + RU transcript (page
    #      blurred) + UK name-change certificate (apostille present, different
    #      applicant) - one messy multi-doc PDF for the live "upload it" demo.
    d1 = os.path.join(OUT, "_tmp_ru_diploma.pdf")
    make_document_pdf(
        d1,
        institution="ВОСТОКГОРСКИЙ ГОСУДАРСТВЕННЫЙ ТЕХНИЧЕСКИЙ УНИВЕРСИТЕТ",
        title="ДИПЛОМ О ВЫСШЕМ ОБРАЗОВАНИИ",
        body_lines=[
            "Настоящим удостоверяется, что Сидоров Пётр Николаевич в 2016 году",
            "полностью освоил программу высшего образования по направлению",
            "«Инженерия и технологии» и решением государственной аттестационной",
            "комиссии ему присвоена квалификация бакалавра техники и технологии.",
        ],
        applicant_name="Сидоров Пётр Николаевич",
        date_line="Дата выдачи: 28 июня 2016 г.  Регистрационный номер: 77-ВГТУ-04821",
        apostille=False, notary=False, certified=True, signature=True,
        lang_footer="Диплом бакалавра · Российская Федерация",
    )

    t1 = os.path.join(OUT, "_tmp_ru_transcript_raw.pdf")
    make_document_pdf(
        t1,
        institution="ВОСТОКГОРСКИЙ ГОСУДАРСТВЕННЫЙ ТЕХНИЧЕСКИЙ УНИВЕРСИТЕТ",
        title="ПРИЛОЖЕНИЕ К ДИПЛОМУ (ВЫПИСКА ОЦЕНОК)",
        body_lines=[
            "Сидоров Пётр Николаевич, зачётная книжка № 041-2012, за период",
            "обучения с 2012 по 2016 год прослушал курсы: Высшая математика (5),",
            "Физика (5), Теория механизмов и машин (4), Электротехника (5),",
            "Программирование (5), Материаловедение (4), Метрология (5).",
            "Средний балл диплома: 4.71.",
        ],
        applicant_name="Сидоров Пётр Николаевич",
        date_line="Дата выдачи: 28 июня 2016 г.",
        apostille=False, notary=False, certified=True, signature=True,
        lang_footer="Приложение к диплому · Российская Федерация",
    )
    t1_blur = os.path.join(OUT, "_tmp_ru_transcript.pdf")
    apply_blur(t1, t1_blur)

    n1 = os.path.join(OUT, "_tmp_uk_namechange.pdf")
    make_document_pdf(
        n1,
        institution="РЕЄСТРАЦІЙНИЙ ВІДДІЛ М. СОНЯЧНОГРАД",
        title="СВІДОЦТВО ПРО ЗМІНУ ІМЕНІ",
        body_lines=[
            "Цим засвідчується, що громадянка Петренко Ганна Олексіївна змінила",
            "своє прізвище з дошлюбного «Ковальчук» на «Петренко» відповідно до",
            "актового запису № 2019-114 від 03 квітня 2019 року.",
        ],
        applicant_name="Петренко Ганна Олексіївна",
        date_line="Дата видачі: 03 квітня 2019 р.",
        apostille=True, notary=False, certified=True, signature=True,
        lang_footer="Свідоцтво про зміну імені · Україна",
    )

    merge_pdfs([d1, t1_blur, n1], os.path.join(OUT, "flagship-bundle-sidorov.pdf"))

    # ---- 2. Clean READY case: EN diploma + EN transcript, all indicators present.
    e1 = os.path.join(OUT, "_tmp_en_diploma.pdf")
    make_document_pdf(
        e1,
        institution="RIVERSTONE STATE UNIVERSITY",
        title="DIPLOMA - BACHELOR OF SCIENCE",
        body_lines=[
            "This is to certify that David Cohen has satisfactorily completed the",
            "prescribed course of study and is hereby awarded the degree of",
            "Bachelor of Science in Computer Science, with all the rights,",
            "honours and privileges thereunto appertaining.",
        ],
        applicant_name="David Cohen",
        date_line="Conferred: 14 May 2018   Registrar reference: RSU-2018-30291",
        apostille=True, notary=True, certified=True, signature=True,
        lang_footer="Bachelor of Science Diploma - United States",
    )
    e2 = os.path.join(OUT, "_tmp_en_transcript.pdf")
    make_document_pdf(
        e2,
        institution="RIVERSTONE STATE UNIVERSITY",
        title="OFFICIAL ACADEMIC TRANSCRIPT",
        body_lines=[
            "Student: David Cohen. Record ID 2014-88213. Degree: BSc Computer",
            "Science. Courses: Data Structures (A), Algorithms (A-), Operating",
            "Systems (B+), Databases (A), Software Engineering (A), Linear",
            "Algebra (A-). Cumulative GPA: 3.78 / 4.00.",
        ],
        applicant_name="David Cohen",
        date_line="Issued: 14 May 2018",
        apostille=True, notary=True, certified=True, signature=True,
        lang_footer="Official Transcript - United States",
    )
    merge_pdfs([e1, e2], os.path.join(OUT, "seed-ready-cohen.pdf"))

    # ---- 3. NEEDS_ATTENTION case: FR diploma + transcript (both baseline documents
    #      present, so the completeness check passes clean) plus an FR equivalency
    #      certificate and FR institution name-change certificate, one page cropped.
    f0a = os.path.join(OUT, "_tmp_fr_diploma.pdf")
    make_document_pdf(
        f0a,
        institution="UNIVERSITÉ DE VALLONCHAMP",
        title="DIPLÔME - MASTER EN SCIENCES DE GESTION",
        body_lines=[
            "Il est certifié que Marie Lefèvre a satisfait aux exigences du programme",
            "et se voit décerner le grade de Master en sciences de gestion, avec toutes",
            "les prérogatives qui y sont attachées.",
        ],
        applicant_name="Marie Lefèvre",
        date_line="Délivré le : 28 juin 2019   Référence : UV-2019-77410",
        apostille=True, notary=False, certified=True, signature=True,
        lang_footer="Diplôme de Master - France",
    )
    f0b = os.path.join(OUT, "_tmp_fr_transcript.pdf")
    make_document_pdf(
        f0b,
        institution="UNIVERSITÉ DE VALLONCHAMP",
        title="RELEVÉ DE NOTES OFFICIEL",
        body_lines=[
            "Marie Lefèvre, dossier n° 2016-30294. Master en sciences de gestion.",
            "Matières : Finance d'entreprise (A), Stratégie (A-), Marketing (B+),",
            "Droit des affaires (A), Comptabilité de gestion (A-). Moyenne générale : 15.8/20.",
        ],
        applicant_name="Marie Lefèvre",
        date_line="Délivré le : 28 juin 2019",
        apostille=True, notary=False, certified=True, signature=True,
        lang_footer="Relevé de notes officiel - France",
    )

    f1 = os.path.join(OUT, "_tmp_fr_equivalency_raw.pdf")
    make_document_pdf(
        f1,
        institution="COMMISSION RÉGIONALE D'ÉQUIVALENCE ACADÉMIQUE - VALLONCHAMP",
        title="ATTESTATION D'ÉQUIVALENCE DE DIPLÔME",
        body_lines=[
            "Il est certifié que le diplôme délivré à Marie Lefèvre par l'Université",
            "de Vallonchamp est reconnu équivalent au grade de Master en sciences de",
            "gestion, conformément à la procédure d'équivalence académique.",
        ],
        applicant_name="Marie Lefèvre",
        date_line="Délivré le : 09 septembre 2020",
        apostille=True, notary=False, certified=True, signature=True,
        lang_footer="Attestation d'équivalence - France",
    )
    f1_crop = os.path.join(OUT, "_tmp_fr_equivalency.pdf")
    apply_crop(f1, f1_crop)

    f2 = os.path.join(OUT, "_tmp_fr_institution_namechange.pdf")
    make_document_pdf(
        f2,
        institution="RECTORAT DE L'ACADÉMIE DE VALLONCHAMP",
        title="ATTESTATION DE CHANGEMENT DE DÉNOMINATION D'ÉTABLISSEMENT",
        body_lines=[
            "Il est attesté que l'établissement anciennement dénommé « Institut",
            "Universitaire de Vallonchamp-Sud » porte, depuis le 01 janvier 2015, la",
            "dénomination officielle « Université de Vallonchamp ».",
        ],
        applicant_name="N/A - institutional record",
        date_line="Délivré le : 12 janvier 2015",
        apostille=False, notary=True, certified=True, signature=True,
        lang_footer="Changement de dénomination - France",
    )
    merge_pdfs([f0a, f0b, f1_crop, f2], os.path.join(OUT, "seed-attention-lefevre.pdf"))

    # ---- 4. NEEDS_HUMAN_REVIEW case: an unrecognised document type mixed in.
    u1 = os.path.join(OUT, "_tmp_unrecognised.pdf")
    make_document_pdf(
        u1,
        institution="RIVERBEND LOGISTICS PTY LTD",
        title="EMPLOYMENT REFERENCE LETTER",
        body_lines=[
            "This letter confirms that the bearer was employed with our company",
            "in a warehouse operations role from 2019 to 2021 and performed",
            "their duties satisfactorily throughout that period.",
        ],
        applicant_name="Unknown",
        date_line="Issued: 02 March 2021",
        apostille=False, notary=False, certified=False, signature=True,
        lang_footer="Not an academic credential document",
    )
    e3 = os.path.join(OUT, "_tmp_en_diploma_2.pdf")
    make_document_pdf(
        e3,
        institution="HARBOURVIEW INSTITUTE OF TECHNOLOGY",
        title="DIPLOMA - BACHELOR OF ENGINEERING",
        body_lines=[
            "This is to certify that Amelia Ryan has completed the requirements",
            "for the degree of Bachelor of Engineering (Honours) and is admitted",
            "to that degree with all rights and privileges thereto belonging.",
        ],
        applicant_name="Amelia Ryan",
        date_line="Conferred: 20 November 2019",
        apostille=True, notary=False, certified=True, signature=True,
        lang_footer="Bachelor of Engineering Diploma",
    )
    merge_pdfs([e3, u1], os.path.join(OUT, "seed-review-ryan.pdf"))

    # ---- 5. Absent-document case: only a name-change certificate submitted, no diploma or
    #      transcript anywhere - exercises the completeness check (a required document type
    #      that never appears at all, not a misclassification or legibility issue).
    m1 = os.path.join(OUT, "_tmp_uk_namechange_only.pdf")
    make_document_pdf(
        m1,
        institution="РЕЄСТРАЦІЙНИЙ ВІДДІЛ М. СОНЯЧНОГРАД",
        title="СВІДОЦТВО ПРО ЗМІНУ ІМЕНІ",
        body_lines=[
            "Цим засвідчується, що громадянка Мельник Олена Василівна змінила",
            "своє прізвище з дошлюбного «Бондаренко» на «Мельник» відповідно до",
            "актового запису № 2021-058 від 11 травня 2021 року.",
        ],
        applicant_name="Мельник Олена Василівна",
        date_line="Дата видачі: 11 травня 2021 р.",
        apostille=True, notary=False, certified=True, signature=True,
        lang_footer="Свідоцтво про зміну імені · Україна",
    )
    os.replace(m1, os.path.join(OUT, "seed-missing-docs-melnyk.pdf"))

    # Clean up temp singles, keep only the merged bundles + any standalone image samples.
    for f in os.listdir(OUT):
        if f.startswith("_tmp_"):
            os.remove(os.path.join(OUT, f))

    print("Corpus built:")
    for f in sorted(os.listdir(OUT)):
        print(" -", f)


def build_coverage():
    """Rev 3: dedicated, isolated test fixtures for the PRD section 9 statuses and
    section 10 codes not exercised by the main narrative corpus (build()). Not part
    of the seeded dashboard queue - run through the pipeline directly by
    seed/verify_coverage.py and captured as evidence, not shown to a live prospect.
    """
    # ---- A legible-content page that is genuinely rotated ~90 degrees but still
    #      correctly classified - status Unclear (distinct from Unidentified, which
    #      is reserved for pages that can't be classified at all). Confirmed live
    #      8 Aug 2026: lighter crops/rotations (up to ~45 degrees) don't reliably
    #      trip the aspect-ratio-based rotation heuristic on this corpus's generous
    #      page margins - only a genuine ~90 degree turn does, which also happens
    #      to be realistic (a page scanned sideways).
    clean_diploma = os.path.join(OUT, "_tmp_rot_diploma.pdf")
    make_document_pdf(
        clean_diploma, institution="RIVERSTONE STATE UNIVERSITY", title="DIPLOMA - BACHELOR OF SCIENCE",
        body_lines=["This is to certify that Owen Blackwood has satisfactorily completed",
                    "the prescribed course of study for a Bachelor of Science."],
        applicant_name="Owen Blackwood", date_line="Conferred: 08 August 2019",
        apostille=True, notary=True, certified=True, signature=True,
        lang_footer="Bachelor of Science Diploma",
    )
    apply_rotate(clean_diploma, os.path.join(OUT, "coverage-rotated-diploma.pdf"), angle=90)

    # ---- Institution mismatch WITHOUT an institution name-change certificate.
    ic1 = os.path.join(OUT, "_tmp_ic_diploma.pdf")
    make_document_pdf(
        ic1, institution="HARBOURVIEW INSTITUTE OF TECHNOLOGY",
        title="DIPLOMA - BACHELOR OF ARTS",
        body_lines=["This is to certify that Noah Bergman has completed the",
                    "requirements for the degree of Bachelor of Arts in History."],
        applicant_name="Noah Bergman", date_line="Conferred: 12 June 2017",
        apostille=True, notary=True, certified=True, signature=True,
        lang_footer="Bachelor of Arts Diploma",
    )
    ic2 = os.path.join(OUT, "_tmp_ic_transcript.pdf")
    make_document_pdf(
        ic2, institution="FAIRBRIDGE COLLEGE OF ARTS",
        title="OFFICIAL ACADEMIC TRANSCRIPT",
        body_lines=["Student: Noah Bergman. Degree: BA History. Courses: Ancient",
                    "History (A), Historiography (A-), Modern Europe (B+)."],
        applicant_name="Noah Bergman", date_line="Issued: 12 June 2017",
        apostille=True, notary=True, certified=True, signature=True,
        lang_footer="Official Transcript",
    )
    merge_pdfs([ic1, ic2], os.path.join(OUT, "coverage-institution-nocert.pdf"))

    # ---- Institution mismatch WITH an institution name-change certificate present.
    icc = os.path.join(OUT, "_tmp_icc_cert.pdf")
    make_document_pdf(
        icc, institution="FAIRBRIDGE COLLEGE OF ARTS",
        title="CERTIFICATE OF INSTITUTIONAL RENAMING",
        body_lines=["It is certified that Harbourview Institute of Technology was",
                    "renamed Fairbridge College of Arts effective 01 January 2016."],
        applicant_name="N/A - institutional record", date_line="Issued: 01 January 2016",
        apostille=False, notary=True, certified=True, signature=True,
        lang_footer="Institution name-change certificate",
    )
    merge_pdfs([ic1, ic2, icc], os.path.join(OUT, "coverage-institution-withcert.pdf"))

    # ---- Two diplomas of the same type, as two SEPARATE uploaded files (not two
    #      pages of one PDF - consecutive same-type pages of the SAME file are
    #      deliberately merged into one logical multi-page document by
    #      _group_pages_into_documents, which is correct behaviour for a real
    #      multi-page diploma; two distinct files is what "an applicant uploaded
    #      the same diploma twice" actually looks like) - DOC_DUPLICATE_TYPE / Duplicate.
    make_document_pdf(
        os.path.join(OUT, "coverage-duplicate-a.pdf"),
        institution="RIVERSTONE STATE UNIVERSITY", title="DIPLOMA - BACHELOR OF SCIENCE",
        body_lines=["This is to certify that Layla Haddad has satisfactorily completed",
                    "the prescribed course of study for a Bachelor of Science."],
        applicant_name="Layla Haddad", date_line="Conferred: 10 May 2015",
        apostille=True, notary=True, certified=True, signature=True,
        lang_footer="Bachelor of Science Diploma",
    )
    make_document_pdf(
        os.path.join(OUT, "coverage-duplicate-b.pdf"),
        institution="RIVERSTONE STATE UNIVERSITY", title="DIPLOMA - BACHELOR OF SCIENCE (DUPLICATE)",
        body_lines=["This is to certify that Layla Haddad has satisfactorily completed",
                    "the prescribed course of study for a Bachelor of Science."],
        applicant_name="Layla Haddad", date_line="Conferred: 10 May 2015",
        apostille=True, notary=True, certified=True, signature=True,
        lang_footer="Bachelor of Science Diploma (second copy)",
    )

    # ---- Unsupported document language - DOC_LANGUAGE_UNSUPPORTED / Manual Review Required.
    lang1 = os.path.join(OUT, "_tmp_lang_diploma.pdf")
    make_document_pdf(
        lang1, institution="TECHNISCHE HOCHSCHULE BERGSTADT",
        title="DIPLOM - BACHELOR OF INGENIEURWISSENSCHAFTEN",
        body_lines=["Hiermit wird bestätigt, dass Lukas Fischer das Studium der",
                    "Ingenieurwissenschaften erfolgreich abgeschlossen hat und den",
                    "akademischen Grad Bachelor of Engineering erhält."],
        applicant_name="Lukas Fischer", date_line="Ausgestellt: 09 Juli 2018",
        apostille=True, notary=False, certified=True, signature=True,
        lang_footer="Bachelor-Diplom - Deutschland",
    )
    os.replace(lang1, os.path.join(OUT, "coverage-language-unsupported.pdf"))

    # ---- A diploma missing institution/degree/date fields entirely - title and body
    #      say "DIPLOMA" unambiguously (so classification lands on DIPLOMA, the only
    #      type this ambiguous a stub could otherwise drift to being read as a
    #      transcript, which doesn't carry a degree-type field at all) but never
    #      name an institution, a specific degree, or a date. All four stamp
    #      indicators are present so the ONLY issues raised are the three "not
    #      clear" checks - DOC_INSTITUTION_NOT_CLEAR + DOC_DEGREE_NOT_CLEAR +
    #      DOC_DATE_NOT_CLEAR / status Partially Valid, with nothing else competing
    #      for priority in the status computation.
    stub = os.path.join(OUT, "_tmp_stub.pdf")
    make_document_pdf(
        stub, institution=" ", title="DIPLOMA",
        body_lines=["This diploma certifies that the named individual completed",
                    "a program of study and met all requirements for the award",
                    "of this diploma, granted with all rights and privileges."],
        applicant_name="Sofia Marchetti", date_line="",
        apostille=True, notary=True, certified=True, signature=True,
        lang_footer="",
    )
    os.replace(stub, os.path.join(OUT, "coverage-stub-fields.pdf"))

    # ---- An ambiguous/garbled stamp graphic - best-effort DOC_STAMP_NOT_CLEAR /
    #      Invalid/Unidentified Stamp (model-dependent, not guaranteed deterministic).
    unclear = os.path.join(OUT, "_tmp_unclear_stamp.pdf")
    make_document_pdf(
        unclear, institution="HARBOURVIEW INSTITUTE OF TECHNOLOGY",
        title="DIPLOMA - BACHELOR OF COMMERCE",
        body_lines=["This is to certify that Priya Nair has completed the",
                    "requirements for the degree of Bachelor of Commerce."],
        applicant_name="Priya Nair", date_line="Conferred: 03 March 2016",
        apostille=True, notary=False, certified=True, signature=True,
        lang_footer="Bachelor of Commerce Diploma",
    )
    # Overlay a second, illegibly-labelled seal near the apostille one so the page
    # shows two overlapping stamp-like marks with garbled text between them.
    c = canvas.Canvas(unclear.replace(".pdf", "_overlay.pdf"), pagesize=A4)
    c.saveState()
    c.setStrokeColorRGB(0.3, 0.3, 0.3)
    c.setLineWidth(1.2)
    x, y = PAGE_W - 150, 165
    c.circle(x, y, 30, stroke=1, fill=0)
    c.setFont("Unicode", 5.5)
    c.drawCentredString(x, y + 2, "XZQP##%%&&VVWW")
    c.drawCentredString(x, y - 8, "@@##$$ZZ??!!**")
    c.restoreState()
    c.save()
    from pypdf import PdfReader, PdfWriter
    base = PdfReader(unclear)
    overlay = PdfReader(unclear.replace(".pdf", "_overlay.pdf"))
    page = base.pages[0]
    page.merge_page(overlay.pages[0])
    writer = PdfWriter()
    writer.add_page(page)
    with open(os.path.join(OUT, "coverage-stamp-unclear.pdf"), "wb") as f:
        writer.write(f)

    # ---- Name mismatch with NO name-change certificate anywhere (distinct from the
    #      flagship bundle, which DOES include one) - DOC_MISSING_NAME_CHANGE +
    #      DOC_MISSING_NAME_CHANGE_CERTIFICATE / Additional Document Required.
    nm1 = os.path.join(OUT, "_tmp_nm_diploma.pdf")
    make_document_pdf(
        nm1, institution="RIVERSTONE STATE UNIVERSITY", title="DIPLOMA - BACHELOR OF SCIENCE",
        body_lines=["This is to certify that Grace Whitfield has satisfactorily",
                    "completed the prescribed course of study for a Bachelor of Science."],
        applicant_name="Grace Whitfield", date_line="Conferred: 21 April 2014",
        apostille=True, notary=True, certified=True, signature=True,
        lang_footer="Bachelor of Science Diploma",
    )
    nm2 = os.path.join(OUT, "_tmp_nm_transcript.pdf")
    make_document_pdf(
        nm2, institution="RIVERSTONE STATE UNIVERSITY", title="OFFICIAL ACADEMIC TRANSCRIPT",
        body_lines=["Student: Grace Whitfield. Degree: BSc. Courses: Chemistry (A),",
                    "Physics (A-), Biology (B+). Cumulative GPA: 3.7/4.0."],
        applicant_name="Grace Whitfield", date_line="Issued: 21 April 2014",
        apostille=True, notary=True, certified=True, signature=True,
        lang_footer="Official Transcript",
    )
    merge_pdfs([nm1, nm2], os.path.join(OUT, "coverage-namechange-missing.pdf"))
    # Declared applicant name for this bundle (used by verify_coverage.py): "Grace Newman"
    # - shares nothing distinctive with "Grace Whitfield" on the diploma/transcript above.

    # ---- First-name-only mismatch (last name matches) - DOC_FIRST_NAME_MISMATCH only.
    fn1 = os.path.join(OUT, "_tmp_fn_diploma.pdf")
    make_document_pdf(
        fn1, institution="RIVERSTONE STATE UNIVERSITY", title="DIPLOMA - BACHELOR OF SCIENCE",
        body_lines=["This is to certify that Michael Sullivan has satisfactorily",
                    "completed the prescribed course of study for a Bachelor of Science."],
        applicant_name="Michael Sullivan", date_line="Conferred: 15 June 2013",
        apostille=True, notary=True, certified=True, signature=True,
        lang_footer="Bachelor of Science Diploma",
    )
    os.replace(fn1, os.path.join(OUT, "coverage-firstname-mismatch.pdf"))
    # Declared applicant name for this bundle: "Daniel Sullivan" - Sullivan matches,
    # Michael/Daniel does not.

    # ---- Last-name-only mismatch (first name matches) - DOC_LAST_NAME_MISMATCH only.
    ln1 = os.path.join(OUT, "_tmp_ln_diploma.pdf")
    make_document_pdf(
        ln1, institution="RIVERSTONE STATE UNIVERSITY", title="DIPLOMA - BACHELOR OF SCIENCE",
        body_lines=["This is to certify that Daniel Whitfield has satisfactorily",
                    "completed the prescribed course of study for a Bachelor of Science."],
        applicant_name="Daniel Whitfield", date_line="Conferred: 15 June 2013",
        apostille=True, notary=True, certified=True, signature=True,
        lang_footer="Bachelor of Science Diploma",
    )
    os.replace(ln1, os.path.join(OUT, "coverage-lastname-mismatch.pdf"))
    # Declared applicant name for this bundle: "Daniel Sullivan" - Daniel matches,
    # Whitfield/Sullivan does not.

    for f in os.listdir(OUT):
        if f.startswith("_tmp_"):
            os.remove(os.path.join(OUT, f))

    print("Coverage corpus built:")
    for f in sorted(os.listdir(OUT)):
        if f.startswith("coverage-"):
            print(" -", f)


if __name__ == "__main__":
    build()
    build_coverage()
