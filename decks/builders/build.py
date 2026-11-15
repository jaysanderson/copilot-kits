"""SemanticSite overview deck, built by populating the Progress corporate template."""
import sys, copy
from pathlib import Path
ROOT = Path("/Users/user/Claude/ARAG-PMK-1"); sys.path.insert(0, str(ROOT / "scripts"))
from build_from_template import (Presentation, drop_slides, DEFAULT_TEMPLATE, sanitise_package,
                                 audit_package, harvest_names)
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from lxml import etree
from PIL import Image

SH = Path("/private/tmp/claude-502/-Users-user-Claude-ARAG-PMK-1/4a5c5ea7-aa03-4d01-9f55-733d1c378caf/scratchpad/shots")
OUT = ROOT / "decks/semanticsite-arag-2026-10-12/semanticsite-arag-2026-10-12.pptx"
NAVY, GREEN, MUTED, DARK = RGBColor(0x00,0x21,0x6B), RGBColor(0x00,0x89,0x63), RGBColor(0x5A,0x62,0x75), RGBColor(0x1B,0x1F,0x2A)
DISC = "Demonstration site: Sitecrawl Coffee Roasters is a fictional site built to show SemanticSite. Live capture, 12 October 2026."
LM = 0.79  # left margin, matches the template title placeholders

prs = Presentation(str(DEFAULT_TEMPLATE)); drop_slides(prs)
L = [l for m in prs.slide_masters for l in m.slide_layouts]
def lay(name): return next(l for l in L if l.name == name)

def ph(slide, idx): return next(p for p in slide.placeholders if p.placeholder_format.idx == idx)
def drop_ph(slide, idx):
    p = ph(slide, idx); p._element.getparent().remove(p._element)
def set_lines(p, lines, size=None, color=None, bold=None):
    tf = p.text_frame; tf.text = lines[0]
    for l in lines[1:]: tf.add_paragraph().text = l
    for para in tf.paragraphs:
        for r in para.runs:
            if size: r.font.size = Pt(size)
            if color is not None: r.font.color.rgb = color
            if bold is not None: r.font.bold = bold
def title(slide, text, color=None, idx=0, size=None):
    p = ph(slide, idx); p.text_frame.text = text
    for r in p.text_frame.paragraphs[0].runs:
        if color is not None: r.font.color.rgb = color
        if size: r.font.size = Pt(size)
def body_at(slide, idx, x, y, w, h):
    p = ph(slide, idx); p.left, p.top, p.width, p.height = Inches(x), Inches(y), Inches(w), Inches(h)
def tbox(slide, x, y, w, h, lines, size=14, color=DARK, bold=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, space=6):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)); tf = tb.text_frame
    tf.word_wrap = True; tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for i, l in enumerate(lines):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.alignment = align; para.space_after = Pt(space)
        spec = l if isinstance(l, tuple) else (l, {})
        r = para.add_run(); r.text = spec[0]; r.font.size = Pt(spec[1].get("size", size))
        r.font.bold = spec[1].get("bold", bold); r.font.color.rgb = spec[1].get("color", color)
    return tb
def caption(slide, x, y, w, text=DISC, extra=None):
    t = (extra + " " if extra else "") + text
    return tbox(slide, x, y, w, 0.5, [t], size=11, color=MUTED)
def shot(slide, name, x, y, w=None, h=None):
    im = Image.open(SH / name); ar = im.width / im.height
    if w is None: w = h * ar
    if h is None: h = w / ar
    pic = slide.shapes.add_picture(str(SH / name), Inches(x), Inches(y), Inches(w), Inches(h))
    pic.line.color.rgb = RGBColor(0xC9, 0xCC, 0xD3); pic.line.width = Pt(0.75)
    spPr = pic._element.spPr
    eff = etree.SubElement(spPr, qn("a:effectLst"))
    sh = etree.SubElement(eff, qn("a:outerShdw"), blurRad="76200", dist="25400", dir="5400000", algn="t", rotWithShape="0")
    clr = etree.SubElement(sh, qn("a:srgbClr"), val="000000"); etree.SubElement(clr, qn("a:alpha"), val="22000")
    return pic, w, h
def notes(slide, text): slide.notes_slide.notes_text_frame.text = text

# 1 Cover - Title Slide Blue No speaker info (full blue: white text is correct here; verified by render)
s = prs.slides.add_slide(lay("Title Slide Blue No speaker info"))
title(s, "Your website already holds your knowledge")
set_lines(ph(s, 1), ["SemanticSite shows what a machine can read from it, and what it cannot"])
notes(s, "Open on the premise: the organisation's knowledge is already on its website. The question is what a machine gets from it. Built on Progress Agentic RAG.")

# 2 Problem - Statement slide
s = prs.slides.add_slide(lay("Statement slide 1"))
title(s, "A machine reading your site gets the layout, not the fact")
notes(s, "The meaning sits in the design. A person sees a founding date; a machine sees text in a box. Everything that follows is about closing that gap without guessing.")

# 3 The answer
s = prs.slides.add_slide(lay("Title Only"))
title(s, "SemanticSite reads your site and tells you what a machine cannot", size=36)
tbox(s, LM, 1.95, 11.75, 0.4, ["It crawls the pages, finds the Schema.org markup already there, and counts what is missing or invalid."], size=16, color=DARK)
pic, w, h = shot(s, "c_overview.png", LM, 2.55, h=3.95)
caption(s, LM, 2.55 + h + 0.1, w)
notes(s, "Point it at a URL or sitemap. The overview reports what was read, and what the site already says in structured data: complete, partial or invalid, and none. Pages with none are where proposals begin. The 91% and 95% figures are two different denominators; say 20 pages read of 22 addresses found.")

# 4 Explorer: one solid and one dashed link side by side, with the panel that names each
s = prs.slides.add_slide(lay("Title Only"))
title(s, "See which relationships the site states and which a model inferred", size=36)
pic, w, h = shot(s, "c_graph_sel2.png", LM, 2.4, h=3.9)
pic2, w2, h2 = shot(s, "c_conn.png", 12.54 - 5.2, 2.4, w=5.2)
tbox(s, 12.54 - 5.2, 2.4 + h2 + 0.25, 5.2, 1.0, [("Solid: stated in the site's markup.", {"size": 16}), ("Dashed: read from prose by a model.", {"size": 16})], space=4)
caption(s, LM, 2.4 + h + 0.12, 11.75, extra="Selected: Mill Street Caf\u00e9. Its link to Sitecrawl Coffee Roasters is solid and marked \"in markup\"; links read from prose are dashed.")
notes(s, "Select any entity and the explorer isolates its neighbours. The line style is the honesty mechanism: a solid line is stated by the site's own markup or navigation, a dashed line is a model reading prose. The panel names the source of each link. Proposals whose supporting quote is not on the page are discarded and the view says so.")

# 5 Seals
s = prs.slides.add_slide(lay("Image Slide Left"))
title(s, "Every claim says how it is known", size=36)
set_lines(ph(s, 13), ["Extracted: read from the page's own markup.", "Derived: built from page structure, no model.", "Suggested: a model's proposal, with a verbatim quote."], size=16)
drop_ph(s, 10); body_at(s, 13, 6.77, 2.75, 5.77, 3.0)
pic, w, h = shot(s, "c_claims2.png", LM, 0.55, h=6.15)
caption(s, 6.77, 5.95, 5.77)
# This layout has no footer mark (it assumes a full-bleed picture); copy the template's own logo picture, at its own position.
lg = next(sh for sh in lay("Image Slide").shapes if sh.shape_type == 13)
_el = copy.deepcopy(lg._element)
for _sv in _el.iter("{http://schemas.microsoft.com/office/drawing/2016/SVG/main}svgBlip"):
    _old = _sv.get(qn("r:embed")); _part = lay("Image Slide").part.related_part(_old)
    _sv.set(qn("r:embed"), s.part.relate_to(_part, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"))
s.shapes._spTree.append(_el)
notes(s, "Each record carries one of three marks, and all three are in this frame: EXTRACTED and SUGGESTED on the Station Yard Cafe record, SUGGESTED on the Place and Product records, and DERIVED on the breadcrumb record. Suggested records carry the sentence they came from and the source page.")

# 6 Blocked approval
s = prs.slides.add_slide(lay("Image Slide"))
title(s, "Approval is blocked while the site contradicts itself", size=36)
set_lines(ph(s, 13), ["Settle the disagreement first.", "Then a person approves the record, one page at a time."], size=16)
drop_ph(s, 10); body_at(s, 13, LM, 2.75, 5.77, 3.0)
pic, w, h = shot(s, "c_blocked.png", 7.95, 0.8, w=5.0)
caption(s, 7.95, 0.8 + h + 0.12, 5.0)
notes(s, "The Approve control is disabled until the finding is decided. Here the page states a founding date differently in more than one place. Review is per page; there is no bulk approval, by design.")

# 7 Publish
s = prs.slides.add_slide(lay("Title Only"))
title(s, "A person approves every record. You publish what was approved.", size=36)
pic, w, h = shot(s, "c_banner.png", LM, 2.25, w=11.75)
caption(s, LM, 2.25 + h + 0.1, 11.75)
cols = [("Approved records only", "Anything not approved stays out of the export."),
        ("A provenance file", "One row per property, showing where it came from."),
        ("Publishing is your step", "Cross-page references resolve once the site is published.")]
for i, (hd, tx) in enumerate(cols):
    x = LM + i * 4.0
    tbox(s, x, 5.2, 3.7, 1.4, [(hd, {"bold": True, "size": 20, "color": NAVY}), (tx, {"size": 17})], space=6)
notes(s, "The export contains approved records only and ships with a provenance file. Each page exports on its own and refers to records on other pages by @id; those resolve once the site is published, so a single file checked alone shows them as unresolved. Publishing is the customer's step.")

# 8 Ask
s = prs.slides.add_slide(lay("Title Only"))
title(s, "Ask the site a question and see the pages behind the answer", size=36)
pic, w, h = shot(s, "c_answer.png", LM, 2.2, w=8.6)
caption(s, LM, 2.2 + h + 0.1, 8.6, extra="A live answer: numbered citations on each statement, with the first two of its seven sources shown.")
tbox(s, 9.7, 2.2, 2.85, 3.9, [("Answers are written from the pages retrieved, with the page quote shown beside each.", {"size": 18}),
                              ("If the pages do not say, the assistant says so.", {"size": 18}),
                              ("Retrieval by Progress Agentic RAG.", {"size": 18, "bold": True, "color": GREEN})], space=16)
notes(s, "The conversational layer answers questions about the site's own content and lists the pages it used. Each answer is a fresh generation and wording varies between runs. The citation band confirms a sentence was matched to a cited page; it does not detect a sentence that contradicts the page it cites, which is why the limits slide says so.")

# 9 Economics
s = prs.slides.add_slide(lay("3 items list"))
title(s, "Priced in model calls, and the cost is measured", size=36)
heads = {10: "2", 23: "about 5,288", 25: "about 1,000"}; bodies = {13: "model calls per page", 28: "tokens per page", 29: "calls for a 500-page site"}
for idx, txt in heads.items():
    # the third figure is arithmetic, not a measurement: it must not wear the measured figures' colour
    set_lines(ph(s, idx), [txt], size=32, color=(MUTED if idx == 25 else GREEN), bold=True)
for idx, txt in bodies.items(): set_lines(ph(s, idx), [txt], size=16, color=DARK)
p29 = ph(s, 29); pp = p29.text_frame.add_paragraph(); pp.text = "Extrapolated, not measured: 20 pages scaled to 500. We have not crawled a 500-page site."
for r in pp.runs: r.font.size = Pt(13); r.font.color.rgb = MUTED; r.font.italic = True
tbox(s, LM, 2.45, 5.77, 0.7, ["Progress Agentic RAG starts self-serve, on published pricing."], size=14, color=DARK)
tbox(s, LM, 5.75, 8.2, 0.8, ["The first two figures are measured on our own build: a 20-page crawl, read from the platform's responses, 9 October 2026. Not a product performance claim. No per-paragraph agents run at ingest."], size=12, color=MUTED)
notes(s, "Source: the app's README and design record. 40 calls, 66,937 input and 38,816 output tokens for a 20-page crawl, read from the platform's own responses on 9 October 2026. A 500-page site is therefore about 1,000 calls: arithmetic from the 20-page measurement, not a crawl we have run, which is why that figure is set in grey. It is possible because no ingest-time per-paragraph tasks are registered. Measure on the target site before any large crawl. The self-serve pricing line was checked against the published pricing page on 12 October 2026 (entry tier with a 14-day trial; no figure is quoted on the slide).")

# 10 Limits
s = prs.slides.add_slide(lay("6 items list"))
title(s, "What it does not do, stated up front", size=36)
items = [(10, 13, "Traceability, not truth", "The band confirms a sentence matched a cited page. It does not detect a sentence contradicting it."),
         (17, 26, "Cross-page references", "@id references resolve only once the site is published."),
         (21, 27, "Capped rates", "Crawl and question rates are capped."),
         (15, 28, "Operator key", "The site list needs one, because it records which sites were analysed."),
         (19, 29, "No bulk approval", "Review is per page."),
         (23, 30, "A moment in time", "An approval reflects the crawl, not later changes to the page.")]
col_x = {10: 1.7, 17: 5.67, 21: 9.67, 15: 1.7, 19: 5.67, 23: 9.67}
row_y = {10: 2.45, 17: 2.45, 21: 2.45, 15: 4.7, 19: 4.7, 23: 4.7}
for hi, bi, hd, bd in items:
    set_lines(ph(s, hi), [hd], size=18, color=NAVY, bold=True); set_lines(ph(s, bi), [bd], size=16, color=DARK)
    body_at(s, hi, col_x[hi], row_y[hi], 2.87, 0.5); body_at(s, bi, col_x[hi], row_y[hi] + 0.6, 2.87, 1.5)
notes(s, "These are the product's own stated limits, and the credibility of the rest depends on saying them. The citation band is a traceability check, not a correctness check.")

# 11 Close
s = prs.slides.add_slide(lay("1_Closing Slide"))
tbox(s, (13.333 - 9) / 2, 4.75, 9, 0.6, ["Name one site. We will show you what a machine cannot read from it."], size=24, color=NAVY, bold=True, align=PP_ALIGN.CENTER)
tbox(s, (13.333 - 9) / 2, 5.95, 9, 0.5, ["For agencies packaging AI-readiness audits, and SEO and content teams."], size=14, color=MUTED, align=PP_ALIGN.CENTER)
notes(s, "One ask: pick a site. Built for agencies packaging structured-content audits and AI-readiness work, and for SEO and content teams who need to see what a site contains.")

OUT.parent.mkdir(parents=True, exist_ok=True); prs.save(str(OUT))
rep = sanitise_package(OUT, slide_count=len(prs.slides._sldIdLst), title="SemanticSite overview")
tpl = DEFAULT_TEMPLATE
pos = audit_package(tpl, deny_names=harvest_names(tpl))
print("POSITIVE CONTROL (template): findings", len(pos[0]), "parts", pos[1], "text parts", pos[2])
fnd, parts, tparts = audit_package(OUT, deny_names=harvest_names(tpl))
print("DECK audit: findings", len(fnd), "parts", parts, "text parts", tparts); print(fnd[:10]); print(rep)

# Binary-part redaction now lives in the shared builder (sanitise_package), and audit_package is strict.
import zipfile
fnd, parts, tparts = audit_package(OUT, deny_names=harvest_names(tpl), strict=True)
print("strict audit passed:", len(fnd), "findings over", parts, "parts; embedded names redacted:", len(rep["embedded_names_redacted"]), "binary parts")
assert zipfile.ZipFile(OUT).testzip() is None
Presentation(str(OUT))
