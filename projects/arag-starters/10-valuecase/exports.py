"""Stakeholder-ready branded exports - MUST #7 from the market teardown.
Replaces the old build's flat, unbranded, uneditable print-to-PDF with a
genuine editable PowerPoint and Word document a champion can adapt and
carry into their own board deck.
"""
import io
from datetime import datetime

from docx import Document
from docx.shared import Pt, Inches, RGBColor as DocxRGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from pptx import Presentation
from pptx.util import Inches as PptxInches, Pt as PptxPt
from pptx.dml.color import RGBColor as PptxRGBColor
from pptx.enum.text import PP_ALIGN

from levers import LEVERS, LEVERS_BY_ID, PRICING, compute_lever
from finance import evaluate_case

BLUE_P1 = (0x00, 0x21, 0x6B)
BLUE_P2 = (0x2B, 0x2B, 0xB2)
GREEN_P3 = (0x00, 0xD3, 0x64)
GREY_TEXT = (0x3D, 0x3D, 0x42)
import os as _os

# NOTE: brand/logo-black.png and brand/logo-white.png in the shared brand/
# folder are MISLABELLED - they contain a different, unrelated customer's
# logo (Tangerine Telecom), not a Progress mark. Flagged to the lead
# separately; this export uses the app's own verified Progress Agentic RAG
# lockup instead (rasterised from static/assets/logo-primary-horizontal.svg,
# since python-pptx/python-docx cannot embed SVG directly).
LOGO_PATH = _os.path.join(_os.path.dirname(__file__), "static", "assets", "logo-primary-horizontal.png")
if not _os.path.exists(LOGO_PATH):
    LOGO_PATH = None


def fmt_usd(n):
    if n is None:
        return "-"
    return "US${:,.0f}".format(n)


def fmt_pct(n):
    if n is None:
        return "n/a"
    return "{:.1f}%".format(n * 100)


def _case_expected_totals(case):
    selected = case["selected_levers"]
    values_by = {}
    pov_by = {}
    for row in case["values"]:
        values_by.setdefault((row["lever_id"], row["input_key"]), {})[row["scenario"]] = row["value"]
    for row in case["meta"]:
        pov_by[(row["lever_id"], row["input_key"])] = bool(row["measure_in_pov"])
    from levers import case_scenario_totals
    return case_scenario_totals(selected, values_by, pov_by, "expected"), values_by, pov_by


def _monthly_cost(case):
    tier = case.get("pricing_tier") or "starter"
    if tier == "custom":
        return case.get("custom_monthly_cost") or 0.0
    return PRICING.get(tier, PRICING["starter"])


def build_docx(case: dict) -> bytes:
    (recurring, one_time, incomplete, pov_levers), values_by, pov_by = _case_expected_totals(case)
    monthly_cost = _monthly_cost(case)
    fin = evaluate_case(
        recurring_monthly_benefit=recurring, one_time_benefit=one_time, monthly_cost=monthly_cost,
        one_time_cost=case.get("one_time_cost") or 0.0, discount_rate_annual=case.get("discount_rate"),
        horizon_months=case.get("horizon_months") or 24,
    )

    doc = Document()
    style = doc.styles["Normal"]
    style.font.size = Pt(10.5)

    if LOGO_PATH:
        doc.add_picture(LOGO_PATH, height=Inches(0.35))

    title = doc.add_heading("Progress Agentic RAG - business case", level=1)
    title.runs[0].font.color.rgb = DocxRGBColor(*BLUE_P1)

    meta_p = doc.add_paragraph()
    meta_p.add_run(f"Prepared for: {case['account_name']}    ").bold = True
    meta_p.add_run(f"Prepared by: {case['seller_name']}    ")
    meta_p.add_run(f"Date: {datetime.now().strftime('%d %B %Y')}")

    honesty = doc.add_paragraph()
    honesty_run = honesty.add_run(
        "Every number in this document was supplied by the parties named above. Nothing is a vendor benchmark "
        "unless explicitly labelled as one; no accuracy percentage appears anywhere in this model."
    )
    honesty_run.italic = True
    honesty_run.font.size = Pt(9)
    honesty_run.font.color.rgb = DocxRGBColor(*GREY_TEXT)

    doc.add_heading("Value levers", level=2)
    for lever_id in case["selected_levers"]:
        lever = LEVERS_BY_ID.get(lever_id)
        if not lever:
            continue
        doc.add_heading(f"{lever['number']} - {lever['title']}", level=3)
        owner = next((o for o in case["owners"] if o["lever_id"] == lever_id), None)
        if owner and (owner.get("owner_name") or owner.get("owner_role")):
            doc.add_paragraph(f"Owner: {owner.get('owner_name') or '-'} ({owner.get('owner_role') or '-'})")

        table = doc.add_table(rows=1, cols=4)
        table.style = "Light Grid Accent 1"
        hdr = table.rows[0].cells
        hdr[0].text, hdr[1].text, hdr[2].text, hdr[3].text = "Input", "Value", "Source", "Provided by"
        for inp in lever["inputs"]:
            meta_row = next(
                (m for m in case["meta"] if m["lever_id"] == lever_id and m["input_key"] == inp["key"]), None
            )
            is_pov = bool(meta_row and meta_row["measure_in_pov"])
            cell = values_by.get((lever_id, inp["key"]), {})
            row = table.add_row().cells
            row[0].text = inp["label"]
            row[1].text = "Measure in POV" if is_pov else (f"{cell.get('expected')} {inp['unit']}" if cell.get("expected") is not None else "-")
            row[2].text = (meta_row["source_type"] if meta_row and meta_row.get("source_type") else ("measured-in-pov" if is_pov else "-"))
            provider = ""
            if meta_row and (meta_row.get("provided_by_name") or meta_row.get("provided_by_role")):
                provider = f"{meta_row.get('provided_by_name') or '-'} ({meta_row.get('provided_by_role') or '-'}, {meta_row.get('provided_at') or '-'})"
            row[3].text = provider or "-"

        period, amount = compute_lever(lever_id, {k: values_by.get((lever_id, k), {}).get("expected") for k in [i["key"] for i in lever["inputs"]]}) if lever_id not in pov_levers else (None, None)
        if period:
            p = doc.add_paragraph()
            p.add_run(f"Value: {fmt_usd(amount)}{' one-time' if period == 'one-time' else '/month'}").bold = True

    doc.add_heading("Combined value", level=2)
    doc.add_paragraph(f"Recurring monthly value: {fmt_usd(recurring) if recurring else '-'}")
    doc.add_paragraph(f"One-time value: {fmt_usd(one_time) if one_time else '-'}")

    doc.add_heading("Scenario comparison", level=2)
    scen_table = doc.add_table(rows=1, cols=4)
    scen_table.style = "Light Grid Accent 1"
    hdr = scen_table.rows[0].cells
    hdr[0].text, hdr[1].text, hdr[2].text, hdr[3].text = "Scenario", "Recurring/mo", "One-time", "NPV"
    for scenario in ("conservative", "expected", "aggressive"):
        from levers import case_scenario_totals
        r, o, _, _ = case_scenario_totals(case["selected_levers"], values_by, pov_by, scenario)
        f = evaluate_case(r, o, monthly_cost, case.get("one_time_cost") or 0.0, case.get("discount_rate"), case.get("horizon_months") or 24)
        row = scen_table.add_row().cells
        row[0].text = scenario.capitalize()
        row[1].text = fmt_usd(r)
        row[2].text = fmt_usd(o)
        row[3].text = fmt_usd(f.npv) if f.npv is not None else "n/a (no discount rate entered)"

    doc.add_heading("Financial view", level=2)
    doc.add_paragraph(f"Horizon: {case.get('horizon_months') or 24} months")
    doc.add_paragraph(f"Discount rate (annual): {fmt_pct(case.get('discount_rate')) if case.get('discount_rate') else 'not entered'}")
    doc.add_paragraph(f"NPV: {fmt_usd(fin.npv) if fin.npv is not None else 'enter a discount rate to calculate'}")
    if fin.irr_annual is not None:
        doc.add_paragraph(f"IRR (annualised): {fmt_pct(fin.irr_annual)}")
    else:
        doc.add_paragraph(f"IRR: not meaningful for this case - {fin.irr_undefined_reason}")
    doc.add_paragraph(f"Payback: {'{:.1f} months'.format(fin.payback_months) if fin.payback_months is not None else 'beyond the modelled horizon'}")
    for flag in fin.credibility_flags:
        fp = doc.add_paragraph()
        fp.add_run(f"Note: {flag}").italic = True

    doc.add_heading("Cost reference", level=2)
    doc.add_paragraph("Starter: US$700/month  |  Pro: US$1,925/month  |  Enterprise: custom. Usage-based consumption, not per-seat. 14-day free trial. Re-verify live before quoting.")

    footer = doc.add_paragraph()
    footer_run = footer.add_run(
        "Based on the Progress Agentic RAG ROI value model, v2.0 (5 September 2026). "
        "Discounted cash-flow figures use standard monthly-compounding convention; this is general "
        "finance methodology, not a Progress Agentic RAG product claim."
    )
    footer_run.font.size = Pt(8)
    footer_run.font.color.rgb = DocxRGBColor(*GREY_TEXT)

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def build_pptx(case: dict) -> bytes:
    (recurring, one_time, incomplete, pov_levers), values_by, pov_by = _case_expected_totals(case)
    monthly_cost = _monthly_cost(case)
    fin = evaluate_case(
        recurring_monthly_benefit=recurring, one_time_benefit=one_time, monthly_cost=monthly_cost,
        one_time_cost=case.get("one_time_cost") or 0.0, discount_rate_annual=case.get("discount_rate"),
        horizon_months=case.get("horizon_months") or 24,
    )

    prs = Presentation()
    prs.slide_width = PptxInches(13.333)
    prs.slide_height = PptxInches(7.5)
    blank = prs.slide_layouts[6]

    def new_slide():
        return prs.slides.add_slide(blank)

    def add_title(slide, text, top=0.35):
        box = slide.shapes.add_textbox(PptxInches(0.6), PptxInches(top), PptxInches(12.1), PptxInches(0.9))
        tf = box.text_frame
        tf.text = text
        run = tf.paragraphs[0].runs[0]
        run.font.size = PptxPt(28)
        run.font.bold = True
        run.font.color.rgb = PptxRGBColor(*BLUE_P1)
        return box

    def add_body(slide, text, top=1.3, size=16, bold=False, color=None):
        box = slide.shapes.add_textbox(PptxInches(0.6), PptxInches(top), PptxInches(12.1), PptxInches(0.6))
        tf = box.text_frame
        tf.word_wrap = True
        tf.text = text
        run = tf.paragraphs[0].runs[0]
        run.font.size = PptxPt(size)
        run.font.bold = bold
        run.font.color.rgb = PptxRGBColor(*(color or GREY_TEXT))
        return box

    # Slide 1 - cover
    s1 = new_slide()
    if LOGO_PATH:
        s1.shapes.add_picture(LOGO_PATH, PptxInches(0.6), PptxInches(0.45), height=PptxInches(0.45))
    add_title(s1, "Progress Agentic RAG - business case", top=1.25)
    add_body(s1, f"Prepared for {case['account_name']}", top=2.35, size=20, bold=True, color=BLUE_P2)
    add_body(s1, f"Prepared by {case['seller_name']}  -  {datetime.now().strftime('%d %B %Y')}", top=2.85, size=14)
    add_body(
        s1,
        "Every number in this deck was supplied by the parties above. Nothing is a vendor benchmark unless "
        "explicitly labelled as one; no accuracy percentage appears anywhere in this model.",
        top=6.4, size=11,
    )

    # Slide 2 - combined value
    s2 = new_slide()
    add_title(s2, "The value case")
    add_body(s2, f"Estimated recurring value: {fmt_usd(recurring) if recurring else '-'} / month", top=1.5, size=22, bold=True, color=GREEN_P3 if recurring else GREY_TEXT)
    add_body(s2, f"One-time value: {fmt_usd(one_time) if one_time else '-'}", top=2.2, size=18)
    y = 3.0
    for lever_id in case["selected_levers"]:
        lever = LEVERS_BY_ID.get(lever_id)
        if not lever:
            continue
        tag = " (measure in POV)" if lever_id in pov_levers else ""
        add_body(s2, f"{lever['number']} - {lever['title']}{tag}", top=y, size=13)
        y += 0.45

    # Slide 3 - scenario comparison
    s3 = new_slide()
    add_title(s3, "Scenario comparison")
    rows, cols = 4, 4
    table_shape = s3.shapes.add_table(rows, cols, PptxInches(0.6), PptxInches(1.5), PptxInches(12.1), PptxInches(2.2))
    table = table_shape.table
    headers = ["Scenario", "Recurring/mo", "One-time", "NPV"]
    for c, h in enumerate(headers):
        table.cell(0, c).text = h
    from levers import case_scenario_totals
    for i, scenario in enumerate(("conservative", "expected", "aggressive"), start=1):
        r, o, _, _ = case_scenario_totals(case["selected_levers"], values_by, pov_by, scenario)
        f = evaluate_case(r, o, monthly_cost, case.get("one_time_cost") or 0.0, case.get("discount_rate"), case.get("horizon_months") or 24)
        table.cell(i, 0).text = scenario.capitalize()
        table.cell(i, 1).text = fmt_usd(r)
        table.cell(i, 2).text = fmt_usd(o)
        table.cell(i, 3).text = fmt_usd(f.npv) if f.npv is not None else "n/a"

    # Slide 4 - financial view
    s4 = new_slide()
    add_title(s4, "Financial view")
    add_body(s4, f"NPV: {fmt_usd(fin.npv) if fin.npv is not None else 'enter a discount rate to calculate'}", top=1.6, size=20, bold=True)
    if fin.irr_annual is not None:
        add_body(s4, f"IRR (annualised): {fmt_pct(fin.irr_annual)}", top=2.3, size=20, bold=True)
    else:
        add_body(s4, "IRR: not meaningful for this case", top=2.3, size=18, bold=True)
        add_body(s4, fin.irr_undefined_reason or "", top=2.85, size=12)
    add_body(s4, f"Payback: {'{:.1f} months'.format(fin.payback_months) if fin.payback_months is not None else 'beyond the modelled horizon'}", top=3.6, size=20, bold=True)
    y = 4.4
    for flag in fin.credibility_flags:
        add_body(s4, f"Note: {flag}", top=y, size=11)
        y += 0.6

    # Slide 5 - cost reference
    s5 = new_slide()
    add_title(s5, "Cost reference")
    add_body(s5, "Starter: US$700/month", top=1.6, size=18)
    add_body(s5, "Pro: US$1,925/month", top=2.2, size=18)
    add_body(s5, "Enterprise: custom", top=2.8, size=18)
    add_body(s5, "Usage-based consumption, not per-seat. 14-day free trial. Re-verify live before quoting.", top=3.6, size=13)

    buf = io.BytesIO()
    prs.save(buf)
    return buf.getvalue()
