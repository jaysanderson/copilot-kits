"""Build a deck on the OFFICIAL Progress corporate template.

Unlike build_deck / build_imedia (which draw everything from scratch), this
builder opens the real Progress template, clears its sample slides, and adds new
slides ON its native layouts. That means every slide inherits the genuine
Progress chrome: the logo, the green/blue "ribbon" motif, the copyright footer,
and page numbers all come from the template master. Body content (stat numbers,
cards, diagrams) is drawn on the clean 'Title Only' canvas in the Progress
palette; hero moments use the native Statement / Segue / Section layouts.

    .venv/bin/python scripts/build_progress.py decks/<name>.pptx

Template lives at brand/templates/progress-corporate-fy26.pptx. To refresh it,
drop a newer Progress .pptx there under the same name and rebuild — layout
indices below (LAYOUTS) may need re-checking if Progress reorders the master.
"""
import sys
from pathlib import Path

sys.path.insert(0, "scripts")

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

import build_imedia  # this deck's content + John's voiced notes (edit per deck)
NOTES = getattr(build_imedia, "NOTES", [])

TEMPLATE = "brand/templates/progress-corporate-fy26.pptx"
BRAND = Path("brand")

# ---- Progress theme palette (from the template's theme1.xml) ----------------
NAVY = RGBColor(0x00, 0x20, 0x6B)     # dk2 — headings, dark cards
GREEN = RGBColor(0x00, 0x89, 0x63)    # accent1 — primary Progress green
GREEN2 = RGBColor(0x00, 0xB5, 0x63)   # accent2 — brighter green
BLUE = RGBColor(0x4B, 0x4B, 0xF7)     # accent4
YELLOW = RGBColor(0xFF, 0xD0, 0x00)   # accent6 — pop on blue
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
DARK = RGBColor(0x1A, 0x1A, 0x1A)
MUTED = RGBColor(0x5F, 0x5F, 0x5F)
LIGHTMUTE = RGBColor(0xC9, 0xD6, 0xDB)  # muted on dark
CARD_LINE = RGBColor(0xE6, 0xE6, 0xE6)

HEAD = "Arial Bold"      # template major font (installed)
BODY = "Arial"           # template minor font

SW, SH = 13.333, 7.5

# Layout indices in the Progress master (verified against FY26 template).
LAYOUTS = {
    "title_green": 2,      # Title Slide Green No Photo
    "title_blue": 3,       # Title Slide Blue No Photo
    "statement_blue": 14,  # Statement slide 1 (full-bleed blue)
    "statement_green": 15,  # Statement Slide 2 (full-bleed green)
    "title_only": 19,      # Title Only (clean white canvas + chrome)
    "section": 27,         # Section 1 (white + blue ribbon + body)
    "segue": 8,            # Segue 1 (full-bleed blue, centred title)
}


def add_shadow(shape, blur=90000, dist=28000, alpha=13000):
    spPr = shape._element.spPr
    old = spPr.find(qn("a:effectLst"))
    if old is not None:
        spPr.remove(old)
    eff = spPr.makeelement(qn("a:effectLst"), {})
    shdw = eff.makeelement(qn("a:outerShdw"),
                           {"blurRad": str(blur), "dist": str(dist),
                            "dir": "5400000", "rotWithShape": "0"})
    clr = shdw.makeelement(qn("a:srgbClr"), {"val": "000000"})
    a = clr.makeelement(qn("a:alpha"), {"val": str(alpha)})
    clr.append(a)
    shdw.append(clr)
    eff.append(shdw)
    spPr.append(eff)


def _style_run(run, size, bold, color, font):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    run.font.name = font


def add_text(slide, l, t, w, h, paras, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    tb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    for i, p in enumerate(paras):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.alignment = p.get("align", align)
        if p.get("space_after") is not None:
            para.space_after = Pt(p["space_after"])
        para.space_before = Pt(p.get("space_before", 0))
        if p.get("line_spacing"):
            para.line_spacing = p["line_spacing"]
        run = para.add_run()
        run.text = p["text"]
        _style_run(run, p.get("size", 14), p.get("bold", False),
                   p.get("color", DARK), p.get("font", BODY))
    return tb


def set_ph(ph, paras):
    """Overwrite a placeholder's text with styled paragraphs (keeps its box)."""
    tf = ph.text_frame
    tf.clear()
    for i, p in enumerate(paras):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        if p.get("space_after") is not None:
            para.space_after = Pt(p["space_after"])
        if p.get("line_spacing"):
            para.line_spacing = p["line_spacing"]
        run = para.add_run()
        run.text = p["text"]
        # keep placeholder's inherited font unless overridden
        if p.get("size"):
            run.font.size = Pt(p["size"])
        if p.get("bold") is not None:
            run.font.bold = p["bold"]
        if p.get("color"):
            run.font.color.rgb = p["color"]
        if p.get("font"):
            run.font.name = p["font"]


def add_card(slide, l, t, w, h, fill=WHITE, line=CARD_LINE, shadow=True):
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                  Inches(l), Inches(t), Inches(w), Inches(h))
    card.adjustments[0] = 0.06
    card.fill.solid()
    card.fill.fore_color.rgb = fill
    if line is None:
        card.line.fill.background()
    else:
        card.line.color.rgb = line
        card.line.width = Pt(0.75)
    card.shadow.inherit = False
    if shadow:
        add_shadow(card)
    card.text_frame.text = ""
    return card


def fill_card(card, paras, pad_top=0.24, anchor=MSO_ANCHOR.TOP):
    tf = card.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = Inches(0.28)
    tf.margin_right = Inches(0.28)
    tf.margin_top = Inches(pad_top)
    tf.margin_bottom = Inches(0.2)
    for i, p in enumerate(paras):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.alignment = p.get("align", PP_ALIGN.LEFT)
        para.space_after = Pt(p.get("space_after", 6))
        para.line_spacing = p.get("line_spacing", 1.0)
        run = para.add_run()
        run.text = p["text"]
        _style_run(run, p.get("size", 13), p.get("bold", False),
                   p.get("color", DARK), p.get("font", BODY))


def add_badge(slide, l, t, d, label, fill=GREEN, txt=WHITE, size=22):
    o = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(l), Inches(t),
                               Inches(d), Inches(d))
    o.fill.solid()
    o.fill.fore_color.rgb = fill
    o.line.fill.background()
    o.shadow.inherit = False
    tf = o.text_frame
    tf.word_wrap = False
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    for m in ("left", "right", "top", "bottom"):
        setattr(tf, f"margin_{m}", 0)
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = label
    _style_run(r, size, True, txt, HEAD)
    return o


# ---- slide constructors -----------------------------------------------------
def clear_slides(prs):
    lst = prs.slides._sldIdLst
    for sldId in list(lst):
        prs.part.drop_rel(sldId.get(qn("r:id")))
        lst.remove(sldId)


def L(prs, key):
    return prs.slide_masters[0].slide_layouts[LAYOUTS[key]]


def title_only(prs, title):
    s = prs.slides.add_slide(L(prs, "title_only"))
    set_ph(s.placeholders[0], [{"text": title, "color": NAVY}])
    return s


def stat_slide(prs, title, fig, claim, source):
    s = title_only(prs, title)
    add_text(s, 0.79, 2.05, 12.0, 2.2,
             [{"text": fig, "size": 150, "bold": True, "color": GREEN,
               "font": HEAD}])
    add_text(s, 0.82, 4.35, 10.8, 1.6,
             [{"text": claim, "size": 23, "bold": True, "color": NAVY,
               "font": BODY, "line_spacing": 1.12}])
    add_text(s, 0.82, 6.35, 11.4, 0.4,
             [{"text": "Source: " + source, "size": 11, "color": MUTED,
               "font": BODY}])
    return s


def source_line(s, text, t=6.55):
    add_text(s, 0.79, t, 11.7, 0.4,
             [{"text": "Source: " + text, "size": 11, "color": MUTED,
               "font": BODY}])


def diagram(s, y=3.35):
    boxes = [("YOUR CONTENT", "Docs, web, policies, product info", False),
             ("GROUNDED AI", "Retrieve the right passages, then generate", True),
             ("ON-BRAND, CITED ANSWERS", "Every answer traceable to its source", False)]
    bw, bh, gap = 3.55, 1.95, 0.85
    x0 = (SW - (3 * bw + 2 * gap)) / 2
    for i, (h, d, mid) in enumerate(boxes):
        x = x0 + i * (bw + gap)
        card = add_card(s, x, y, bw, bh, fill=(NAVY if mid else WHITE),
                        line=(None if mid else CARD_LINE))
        fill_card(card, [
            {"text": h, "size": 14, "bold": True,
             "color": (WHITE if mid else GREEN), "space_after": 5},
            {"text": d, "size": 11.5, "color": (WHITE if mid else MUTED),
             "line_spacing": 1.12},
        ], pad_top=0.28, anchor=MSO_ANCHOR.MIDDLE)
        if i < 2:
            ax = x + bw + 0.1
            ar = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(ax),
                                    Inches(y + bh / 2 - 0.16),
                                    Inches(gap - 0.2), Inches(0.32))
            ar.fill.solid()
            ar.fill.fore_color.rgb = GREEN
            ar.line.fill.background()
            ar.shadow.inherit = False


def build(out):
    prs = Presentation(TEMPLATE)
    clear_slides(prs)

    # 1 — Title (native green title layout) ------------------------------
    s = prs.slides.add_slide(L(prs, "title_green"))
    phs = {p.placeholder_format.idx: p for p in s.placeholders}
    set_ph(phs[0], [{"text": "AI That Delivers", "color": NAVY, "size": 40}])
    set_ph(phs[16], [{"text": "Moving marketing from experimentation to execution",
                      "color": DARK}])
    set_ph(phs[12], [{"text": "John Menagh", "color": DARK}])
    set_ph(phs[14], [{"text": "Progress", "color": MUTED}])
    set_ph(phs[15], [{"text": "Future of Marketing Summit  ·  Gold Coast 2026",
                      "color": MUTED}])

    # 2 — The moment (native blue statement) -----------------------------
    s = prs.slides.add_slide(L(prs, "statement_blue"))
    set_ph(s.placeholders[0], [
        {"text": "Every team is experimenting with AI.", "color": WHITE,
         "line_spacing": 1.06, "space_after": 4},
        {"text": "Few have moved to execution.", "color": YELLOW,
         "line_spacing": 1.06},
    ])
    # (71% adoption stat lives in the speaker notes; statement slide stays clean)

    # 3 — The gap (95%) --------------------------------------------------
    g = build_imedia.STAT_GAP
    stat_slide(prs, "The gap", g[0], g[1], g[2])

    # 4 — Why pilots stall (3 cards) -------------------------------------
    s = title_only(prs, "Why most AI pilots stall")
    reasons = [("1", "No goal or measure",
                "“Do something with AI” with no definition of good."),
               ("2", "Ungoverned knowledge",
                "Answers pulled from scattered, unmanaged content."),
               ("3", "No grounding",
                "Generic models guess instead of using your facts.")]
    cw, gap = 3.8, 0.35
    x0 = (SW - (3 * cw + 2 * gap)) / 2
    for i, (num, h, d) in enumerate(reasons):
        x = x0 + i * (cw + gap)
        c = add_card(s, x, 2.35, cw, 3.15)
        add_badge(s, x + 0.32, 2.35 + 0.32, 0.72, num)
        fill_card(c, [{"text": h, "size": 17, "bold": True, "color": NAVY,
                       "space_after": 8},
                      {"text": d, "size": 13.5, "color": MUTED,
                       "line_spacing": 1.14}], pad_top=1.24)
    st = build_imedia.STAT_STALL
    source_line(s, st[0] + ": " + st[1])

    # 5 — Cost of staying in the lab (50%+) ------------------------------
    c5 = build_imedia.STAT_COST
    stat_slide(prs, "The cost of staying in the lab", c5[0], c5[1], c5[2])

    # 6 — Execution starts with your own content (diagram) ---------------
    s = title_only(prs, "Execution starts with your own content")
    add_text(s, 0.79, 1.7, 12.0, 0.6,
             [{"text": "Ground AI in what you already own, so every answer is "
               "on-brand and cited, not guessed.",
               "size": 15, "color": MUTED, "font": BODY, "line_spacing": 1.12}])
    diagram(s, y=3.35)

    # 7 — The trust problem (66%) ----------------------------------------
    s = title_only(prs, "The trust problem")
    add_text(s, 0.79, 1.7, 12.0, 0.6,
             [{"text": "Ungrounded models sound confident and still get it wrong. "
               "Citations are how you tell the difference.",
               "size": 15, "color": MUTED, "font": BODY, "line_spacing": 1.12}])
    h7 = build_imedia.STAT_HALLUC
    lc = add_card(s, 0.79, 2.5, 5.55, 3.5, fill=NAVY, line=None)
    fill_card(lc, [
        {"text": h7[0], "size": 60, "bold": True, "color": WHITE, "font": HEAD,
         "space_after": 4},
        {"text": h7[1], "size": 14.5, "color": WHITE, "line_spacing": 1.16}],
        pad_top=0.7, anchor=MSO_ANCHOR.MIDDLE)
    rc = add_card(s, 6.68, 2.5, 5.86, 3.5, fill=WHITE)
    fill_card(rc, [
        {"text": "Grounding changes the contract", "size": 17, "bold": True,
         "color": GREEN, "space_after": 12},
        {"text": "•  Answers come from your approved content, not the model's "
         "memory.", "size": 14, "color": DARK, "line_spacing": 1.2, "space_after": 8},
        {"text": "•  Every claim links back to a source your team can check.",
         "size": 14, "color": DARK, "line_spacing": 1.2, "space_after": 8},
        {"text": "•  “I don't know” beats a confident wrong answer in front of a "
         "customer.", "size": 14, "color": DARK, "line_spacing": 1.2}],
        pad_top=0.4)
    source_line(s, h7[2])

    # 8 — What good looks like (5 tests) ---------------------------------
    s = title_only(prs, "What ‘good’ looks like")
    add_text(s, 0.79, 1.7, 12.0, 0.6,
             [{"text": "Five tests for AI you can put in front of customers.",
               "size": 15, "color": MUTED, "font": BODY}])
    words = [("Grounded", "in your content"), ("Cited", "back to source"),
             ("On-brand", "your voice, always"), ("Measured", "quality you can see"),
             ("Governed", "secure and controlled")]
    cw, gap = 2.15, 0.28
    x0 = (SW - (5 * cw + 4 * gap)) / 2
    for i, (w, d) in enumerate(words):
        x = x0 + i * (cw + gap)
        c = add_card(s, x, 3.0, cw, 2.4)
        fill_card(c, [{"text": w, "size": 17, "bold": True, "color": GREEN,
                       "align": PP_ALIGN.CENTER, "space_after": 4},
                      {"text": d, "size": 11.5, "color": MUTED,
                       "align": PP_ALIGN.CENTER, "line_spacing": 1.1}],
                  pad_top=0.55, anchor=MSO_ANCHOR.MIDDLE)

    # 9 — Same question, two answers -------------------------------------
    s = title_only(prs, "Same question, two answers")
    add_text(s, 0.79, 1.7, 12.0, 0.6,
             [{"text": "A customer asks: “Does my plan include international "
               "roaming?”", "size": 15, "color": MUTED, "font": BODY}])
    lc = add_card(s, 0.79, 2.55, 5.85, 3.4, fill=WHITE)
    fill_card(lc, [
        {"text": "GENERIC AI", "size": 13, "bold": True, "color": MUTED,
         "space_after": 8},
        {"text": "“Yes, most plans include international roaming in over 100 "
         "countries.”", "size": 15, "color": DARK, "line_spacing": 1.22,
         "space_after": 12},
        {"text": "Confident. Plausible. Not from your product catalogue, and no "
         "way to check it.", "size": 13, "color": MUTED, "line_spacing": 1.18}],
        pad_top=0.4)
    rc = add_card(s, 6.68, 2.55, 5.85, 3.4, fill=NAVY, line=None)
    fill_card(rc, [
        {"text": "GROUNDED AI", "size": 13, "bold": True, "color": GREEN2,
         "space_after": 8},
        {"text": "“Your Essential plan does not include roaming. The Traveller "
         "add-on covers 30 countries for $5/day.”", "size": 15, "color": WHITE,
         "line_spacing": 1.22, "space_after": 12},
        {"text": "Grounded in your plan documents. Cited to the source. On-brand, "
         "every time.", "size": 13, "color": LIGHTMUTE, "line_spacing": 1.18}],
        pad_top=0.4)

    # 10 — Where it pays off (3 cards) -----------------------------------
    s = title_only(prs, "Where it pays off for marketing")
    add_text(s, 0.79, 1.7, 12.0, 0.6,
             [{"text": "Grounded AI turns your content into everyday marketing "
               "leverage.", "size": 15, "color": MUTED, "font": BODY}])
    outs = [("Findability", "Customers and teams reach the right answer in seconds, "
             "not searches."),
            ("On-brand answers", "One consistent, accurate voice across every "
             "channel and touchpoint."),
            ("Self-service", "Deflect repetitive questions and free your team for "
             "higher-value work.")]
    cw, gap = 3.85, 0.32
    x0 = (SW - (3 * cw + 2 * gap)) / 2
    for i, (h, d) in enumerate(outs):
        x = x0 + i * (cw + gap)
        c = add_card(s, x, 2.5, cw, 2.9)
        fill_card(c, [{"text": h, "size": 16, "bold": True, "color": GREEN,
                       "space_after": 8},
                      {"text": d, "size": 13, "color": DARK, "line_spacing": 1.14}],
                  pad_top=0.4)
    p10 = build_imedia.STAT_PAYOFF
    source_line(s, p10[0] + ": " + p10[1])

    # 11 — The prize ($463B) ---------------------------------------------
    v = build_imedia.STAT_VALUE
    stat_slide(prs, "The prize", v[0], v[1], v[2])

    # 12 — Your turn (native blue segue) ---------------------------------
    s = prs.slides.add_slide(L(prs, "segue"))
    set_ph(s.placeholders[0],
           [{"text": "What is the one question your customers ask every day?",
             "color": WHITE}])
    add_text(s, 1.6, 5.0, 10.1, 1.0,
             [{"text": "That question, grounded in your own content, is your first "
               "AI use case.", "size": 18, "color": YELLOW, "font": BODY,
               "align": PP_ALIGN.CENTER, "line_spacing": 1.12}],
             align=PP_ALIGN.CENTER)

    # 13 — How to start (3 numbered cards) -------------------------------
    s = title_only(prs, "How to start")
    add_text(s, 0.79, 1.7, 12.0, 0.6,
             [{"text": "One high-value use case beats a hundred experiments.",
               "size": 15, "color": MUTED, "font": BODY}])
    steps = [("1", "Pick your most-asked question",
              "The one customers or staff raise every day."),
             ("2", "Ground it in your content",
              "Point AI at the source of truth and require citations."),
             ("3", "Measure, then scale",
              "Prove answer quality, then expand use case by use case.")]
    cw, gap = 3.8, 0.35
    x0 = (SW - (3 * cw + 2 * gap)) / 2
    for i, (num, h, d) in enumerate(steps):
        x = x0 + i * (cw + gap)
        c = add_card(s, x, 2.5, cw, 3.15)
        add_badge(s, x + 0.32, 2.5 + 0.32, 0.72, num)
        fill_card(c, [{"text": h, "size": 16, "bold": True, "color": NAVY,
                       "space_after": 8},
                      {"text": d, "size": 13.5, "color": MUTED,
                       "line_spacing": 1.14}], pad_top=1.24)

    # 14 — Define good before you scale (4 cards, 2x2) -------------------
    s = title_only(prs, "Define ‘good’ before you scale")
    add_text(s, 0.79, 1.7, 12.0, 0.6,
             [{"text": "If you cannot measure the answer, you cannot trust it in "
               "front of a customer.", "size": 15, "color": MUTED, "font": BODY}])
    metrics = [("Is it grounded?",
                "Does the answer come from your content, with a citation?"),
               ("Is it right?",
                "Sample and score answers for accuracy and relevance."),
               ("Is it deflecting?",
                "Track questions resolved without a human handoff."),
               ("Is it on-brand?",
                "Review tone and voice across channels, not just facts.")]
    cw, ch, gx, gy = 5.85, 1.62, 0.4, 0.26
    x0 = (SW - (2 * cw + gx)) / 2
    ty0 = 2.5
    for i, (h, d) in enumerate(metrics):
        r, cix = divmod(i, 2)
        x = x0 + cix * (cw + gx)
        y = ty0 + r * (ch + gy)
        c = add_card(s, x, y, cw, ch)
        fill_card(c, [{"text": h, "size": 15.5, "bold": True, "color": GREEN,
                       "space_after": 4},
                      {"text": d, "size": 12.5, "color": DARK, "line_spacing": 1.12}],
                  pad_top=0.24)

    # 15 — Two paths (fork) ----------------------------------------------
    s = title_only(prs, "Two paths from here")
    add_text(s, 0.79, 1.7, 12.0, 0.6,
             [{"text": "The tools are the same. The discipline is the difference.",
               "size": 15, "color": MUTED, "font": BODY}])
    lc = add_card(s, 0.79, 2.55, 5.85, 3.4, fill=WHITE)
    fill_card(lc, [
        {"text": "KEEP EXPERIMENTING", "size": 15, "bold": True, "color": MUTED,
         "space_after": 10},
        {"text": "More pilots. More demos. More “we’re looking at AI.”",
         "size": 14.5, "color": DARK, "line_spacing": 1.2, "space_after": 8},
        {"text": "Budget spent, nothing in production, no measurable outcome.",
         "size": 13, "color": MUTED, "line_spacing": 1.18}], pad_top=0.45)
    rc = add_card(s, 6.68, 2.55, 5.85, 3.4, fill=NAVY, line=None)
    fill_card(rc, [
        {"text": "MOVE TO EXECUTION", "size": 15, "bold": True, "color": GREEN2,
         "space_after": 10},
        {"text": "One grounded use case, cited and measured, in front of "
         "customers.", "size": 14.5, "color": WHITE, "line_spacing": 1.2,
         "space_after": 8},
        {"text": "Proven quality you can scale, and defend to the board.",
         "size": 13, "color": LIGHTMUTE, "line_spacing": 1.18}], pad_top=0.45)

    # 16 — CTA: Book a discovery call (native blue statement) ------------
    # The statement title placeholder is bottom-anchored; pin it to the top so
    # the ask reads top-to-bottom (title -> body -> URL).
    s = prs.slides.add_slide(L(prs, "statement_blue"))
    tph = s.placeholders[0]
    tph.left, tph.top = Inches(0.82), Inches(1.15)
    tph.width, tph.height = Inches(8.0), Inches(1.3)
    tph.text_frame.vertical_anchor = MSO_ANCHOR.TOP
    set_ph(tph, [{"text": "Book a discovery call", "color": WHITE, "size": 40}])
    add_text(s, 0.82, 2.75, 7.9, 1.9, [
        {"text": "Bring your most-asked question. In 30 minutes we’ll map your "
         "first grounded AI use case.", "size": 18, "color": WHITE, "font": BODY,
         "line_spacing": 1.15, "space_after": 16},
        {"text": "progress.com/ai-that-delivers", "size": 20, "bold": True,
         "color": YELLOW, "font": HEAD}])
    add_text(s, 0.82, 6.35, 7.5, 0.4,
             [{"text": "Presented by John Menagh, Progress", "size": 12,
               "bold": True, "color": WHITE, "font": BODY}])
    qcard = add_card(s, 9.55, 2.35, 2.8, 2.8, fill=WHITE, line=None, shadow=True)
    if (BRAND / "imedia-qr.png").exists():
        s.shapes.add_picture(str(BRAND / "imedia-qr.png"), Inches(9.9),
                             Inches(2.7), Inches(2.1), Inches(2.1))
    add_text(s, 9.55, 5.2, 2.8, 0.4,
             [{"text": "Scan to book", "size": 12, "bold": True, "color": WHITE,
               "font": BODY, "align": PP_ALIGN.CENTER}], align=PP_ALIGN.CENTER)

    # ---- Speaker notes (John's voice, shared with build_imedia) ---------
    if NOTES:
        for slide, note in zip(prs.slides, NOTES):
            slide.notes_slide.notes_text_frame.text = note

    Path(out).parent.mkdir(parents=True, exist_ok=True)
    prs.save(out)
    print(f"Saved {out} ({len(prs.slides)} slides, {len(NOTES)} notes)")


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1
          else "decks/imedia-fomau-progress-v2-2026-07-03.pptx")
