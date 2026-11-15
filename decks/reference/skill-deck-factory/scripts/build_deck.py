"""Build the Tangerine x Progress Agentic RAG sales deck (16:9).

Fully customer-branded from brand/brand.json. Slide copy on the "answer" slide
is limited to claims verified against the Progress Agentic RAG knowledge box.

Usage:
    python scripts/build_deck.py [output.pptx]
"""
import json
import sys
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

SHOTS = Path("shots")
BRAND = Path("brand")


def _rgb(hexstr, default):
    if not hexstr:
        return default
    h = hexstr.lstrip("#")
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _mix(rgb, target, t):
    return RGBColor(*[round(c + (tc - c) * t) for c, tc in zip(rgb, target)])


# ---- Brand palette: primary auto-loaded from a brand kit -------------------
# Kit selected by env DECK_BRAND (a brand/<name>.json path or kit name); the
# default "brand" matches create-mode live capture.
import os
_kit = os.environ.get("DECK_BRAND", "brand")
_bj = Path(_kit) if _kit.endswith(".json") else BRAND / f"{_kit}.json"
_brand = json.loads(_bj.read_text()) if _bj.exists() else {}
ORANGE = _rgb(_brand.get("primary"), RGBColor(0xFE, 0x74, 0x00))  # brand accent


def _lum(c):
    return (0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]) / 255


# A bright primary (e.g. a lime green) is illegible with white text, so full-bleed
# slides + headings use INK (kit "ink", or a darkened primary); the accent still
# drives the logo/watermark. A dark-enough primary (e.g. orange) is used directly.
INK = _rgb(_brand.get("ink"), _mix(ORANGE, (0, 0, 0), 0.72))
SOLID = ORANGE if _lum(ORANGE) < 0.58 else INK   # readable fills / bg / headings
HEADING = SOLID
GRAD_LIGHT = _mix(SOLID, (255, 255, 255), 0.10)  # gradient top for brand slides
GRAD_DEEP = _mix(SOLID, (0, 0, 0), 0.07)          # gradient bottom
BLACK = RGBColor(0x14, 0x14, 0x14)    # Tangerine ink (bold black)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
DARK = RGBColor(0x1A, 0x1A, 0x1A)     # headings / body on white
MUTED = RGBColor(0x5F, 0x5F, 0x5F)    # captions / sub text
CARD_FILL = RGBColor(0xFF, 0xFF, 0xFF)  # white cards + soft shadow (premium)
CARD_LINE = RGBColor(0xE6, 0xE6, 0xE6)
IMG_BORDER = RGBColor(0xC8, 0xC8, 0xC8)  # neutral from palette

HEAD_FONT = "Calibri"   # brand fonts (Barlow / HWTArtz) are not installed; do not fake
BODY_FONT = "Calibri"

EMU_IN = 914400
SW, SH = 13.333, 7.5


def set_bg(slide, color):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color


def _style_run(run, size, bold, color, font):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    run.font.name = font


def add_text(slide, l, t, w, h, paras, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    """paras: list of dicts {text,size,bold,color,font,space_after,line_spacing}."""
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
                   p.get("color", DARK), p.get("font", BODY_FONT))
    return tb


def add_title(slide, text, color=DARK, l=0.66, t=0.40, w=12.0):
    # Tangerine's brand voice is heavy uppercase display type.
    add_text(slide, l, t, w, 0.85,
             [{"text": text.upper(), "size": 27, "bold": True, "color": color,
               "font": HEAD_FONT}])


def add_shadow(shape, blur=50800, dist=25400, alpha=22000):
    """Attach a soft outer drop shadow to any shape/picture."""
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


def gradient_bg(slide, c1=GRAD_LIGHT, c2=GRAD_DEEP, angle=55):
    """Full-bleed diagonal gradient background."""
    rect = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0,
                                  Inches(SW), Inches(SH))
    rect.line.fill.background()
    rect.shadow.inherit = False
    rect.fill.gradient()
    stops = rect.fill.gradient_stops
    stops[0].position = 0.0
    stops[0].color.rgb = c1
    stops[1].position = 1.0
    stops[1].color.rgb = c2
    try:
        rect.fill.gradient_angle = angle
    except Exception:
        pass
    return rect


def add_watermark(slide, size=6.2, l=None, t=None):
    """Large faint citrus mark as a brand motif; defaults to bottom-right bleed."""
    if l is None:
        l = SW - size + 0.5
    if t is None:
        t = SH - size + 0.5
    slide.shapes.add_picture(str(BRAND / "citrus-watermark.png"),
                             Inches(l), Inches(t), Inches(size), Inches(size))


def add_pill(slide, l, t, text, size=12):
    """White rounded pill with orange bold label (Tangerine button motif)."""
    w = 0.42 + len(text) * 0.098
    h = 0.44
    pill = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                  Inches(l), Inches(t), Inches(w), Inches(h))
    pill.adjustments[0] = 0.5
    pill.fill.solid()
    pill.fill.fore_color.rgb = WHITE
    pill.line.fill.background()
    pill.shadow.inherit = False
    tf = pill.text_frame
    tf.word_wrap = False
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_top = Inches(0.02)
    tf.margin_bottom = Inches(0.02)
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = text.upper()
    _style_run(r, size, True, HEADING, HEAD_FONT)
    return pill


def add_badge(slide, l, t, d, label, fill=SOLID, txt=WHITE, size=24):
    """Orange circle badge with a centred bold label (icon-badge motif)."""
    o = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(l), Inches(t),
                               Inches(d), Inches(d))
    o.fill.solid()
    o.fill.fore_color.rgb = fill
    o.line.fill.background()
    o.shadow.inherit = False
    tf = o.text_frame
    tf.word_wrap = False
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_top = 0
    tf.margin_bottom = 0
    tf.margin_left = 0
    tf.margin_right = 0
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = label
    _style_run(r, size, True, txt, HEAD_FONT)
    return o


def add_tile(slide, l, t, d=0.6):
    """Small orange rounded tile carrying the white citrus mark (app-icon motif)."""
    tile = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                  Inches(l), Inches(t), Inches(d), Inches(d))
    tile.adjustments[0] = 0.28
    tile.fill.solid()
    tile.fill.fore_color.rgb = SOLID
    tile.line.fill.background()
    tile.shadow.inherit = False
    pad = d * 0.2
    slide.shapes.add_picture(str(BRAND / "citrus-white.png"),
                             Inches(l + pad), Inches(t + pad),
                             Inches(d - 2 * pad), Inches(d - 2 * pad))
    return tile


def add_footer(slide, page_no):
    """Small black wordmark + slide number on white content slides."""
    slide.shapes.add_picture(str(BRAND / "logo-black.png"),
                             Inches(0.66), Inches(7.02), height=Inches(0.24))
    add_text(slide, 11.8, 6.98, 0.9, 0.35,
             [{"text": str(page_no), "size": 10, "bold": False, "color": MUTED,
               "font": BODY_FONT, "align": PP_ALIGN.RIGHT}], align=PP_ALIGN.RIGHT)


def add_shot(slide, path, bx, by, bw, bh):
    """Fit image into box preserving aspect, centred, with border + shadow."""
    iw, ih = Image.open(path).size
    ar = iw / ih
    if ar > bw / bh:            # width-constrained
        w, h = bw, bw / ar
    else:                        # height-constrained
        h, w = bh, bh * ar
    l = bx + (bw - w) / 2
    t = by + (bh - h) / 2
    pic = slide.shapes.add_picture(str(path), Inches(l), Inches(t),
                                   Inches(w), Inches(h))
    pic.line.color.rgb = IMG_BORDER
    pic.line.width = Pt(0.75)
    add_shadow(pic)
    return l, t, w, h


def add_caption(slide, text, l, t, w):
    add_text(slide, l, t, w, 0.5,
             [{"text": text, "size": 11, "bold": False, "color": MUTED,
               "font": BODY_FONT, "align": PP_ALIGN.CENTER}],
             align=PP_ALIGN.CENTER)


def add_card(slide, l, t, w, h, fill=CARD_FILL, line=CARD_LINE, shadow=True):
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
        add_shadow(card, blur=90000, dist=28000, alpha=13000)
    card.text_frame.text = ""
    return card


def fill_card(card, paras, pad_top=0.22, anchor=MSO_ANCHOR.MIDDLE):
    tf = card.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = Inches(0.28)
    tf.margin_right = Inches(0.28)
    tf.margin_top = Inches(pad_top)
    tf.margin_bottom = Inches(0.2)
    for i, p in enumerate(paras):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.space_after = Pt(p.get("space_after", 6))
        para.space_before = Pt(p.get("space_before", 0))
        para.line_spacing = p.get("line_spacing", 1.0)
        run = para.add_run()
        run.text = p["text"]
        _style_run(run, p.get("size", 13), p.get("bold", False),
                   p.get("color", DARK), p.get("font", BODY_FONT))


def blank(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])


def build(out_path):
    prs = Presentation()
    prs.slide_width = Inches(SW)
    prs.slide_height = Inches(SH)

    # ---- Slide 1: Title (orange gradient) ----------------------------------
    s = blank(prs)
    gradient_bg(s)
    add_watermark(s, size=6.6)
    s.shapes.add_picture(str(BRAND / "logo-white.png"), Inches(0.9), Inches(0.8),
                         height=Inches(0.72))
    add_pill(s, 0.92, 1.95, "Powered by Progress Agentic RAG")
    add_text(s, 0.88, 2.72, 11.6, 2.2, [
        {"text": "YOUR KNOWLEDGE, ANSWERING", "size": 50, "bold": True,
         "color": WHITE, "font": HEAD_FONT, "space_after": 12},
        {"text": "An AI customer-experience platform for Tangerine Telecom.",
         "size": 20, "bold": False, "color": WHITE, "font": BODY_FONT,
         "line_spacing": 1.1},
    ])
    add_text(s, 0.9, 6.5, 11.5, 0.5, [
        {"text": "Prepared for Tangerine Telecom  |  3 July 2026",
         "size": 13, "bold": False, "color": WHITE, "font": BODY_FONT}])

    # ---- Slide 2: The problem (white) --------------------------------------
    s = blank(prs)
    set_bg(s, WHITE)
    add_title(s, "The support challenge")
    add_text(s, 0.66, 1.25, 12.0, 0.6, [
        {"text": "Customers want fast, accurate answers. Today that knowledge "
                 "is locked in documents and static pages.",
         "size": 15, "color": MUTED, "font": BODY_FONT, "line_spacing": 1.1}])
    problems = [
        ("1", "Rising support load",
         "Customers phone and message for answers that already live in your "
         "own documents."),
        ("2", "Plan complexity",
         "NBN, mobile and fixed wireless plans, plus SFOA policies, are hard "
         "for customers to navigate."),
        ("3", "Self-service gaps",
         "Static FAQs and PDFs cannot answer a customer's question in their "
         "own words."),
    ]
    cw, gap = 3.8, 0.35
    left0 = (SW - (3 * cw + 2 * gap)) / 2
    for i, (num, head, body) in enumerate(problems):
        l = left0 + i * (cw + gap)
        card = add_card(s, l, 2.5, cw, 3.5)
        add_badge(s, l + 0.32, 2.5 + 0.34, 0.74, num)
        fill_card(card, [
            {"text": head, "size": 17, "bold": True, "color": DARK,
             "space_after": 8},
            {"text": body, "size": 13.5, "color": MUTED, "line_spacing": 1.14},
        ], pad_top=1.28, anchor=MSO_ANCHOR.TOP)
    add_footer(s, 2)

    # ---- Slide 3: The answer (white, KB-verified) --------------------------
    s = blank(prs)
    set_bg(s, WHITE)
    add_title(s, "What Progress Agentic RAG delivers")
    add_text(s, 0.66, 1.25, 12.0, 0.6, [
        {"text": "Turn Tangerine's own documents into answers your customers "
                 "and agents can trust.",
         "size": 15, "color": MUTED, "font": BODY_FONT, "line_spacing": 1.1}])
    answers = [
        ("Grounded answers with citations",
         "Answers are generated from your documents and cite the source text "
         "blocks they draw on."),
        ("Knowledge that stays current",
         "Data Augmentation Agents label and summarise content automatically, "
         "one-shot or continuously as new documents arrive."),
        ("Quality you can measure",
         "Built-in REMi evaluation scores Answer Relevance, Context Relevance "
         "and Groundedness."),
        ("Deploy on your terms",
         "Cloud, hybrid or on-premise, with data-residency options and "
         "encryption in transit and at rest."),
    ]
    cw2, ch2, gx, gy = 5.75, 2.15, 0.45, 0.32
    lx0 = (SW - (2 * cw2 + gx)) / 2
    ty0 = 2.02
    for i, (head, body) in enumerate(answers):
        r, c = divmod(i, 2)
        l = lx0 + c * (cw2 + gx)
        t = ty0 + r * (ch2 + gy)
        card = add_card(s, l, t, cw2, ch2)
        add_tile(s, l + 0.32, t + 0.3, 0.56)
        fill_card(card, [
            {"text": head, "size": 16, "bold": True, "color": HEADING,
             "space_after": 6},
            {"text": body, "size": 13, "color": DARK, "line_spacing": 1.14},
        ], pad_top=1.05, anchor=MSO_ANCHOR.TOP)
    add_footer(s, 3)

    # ---- Slides 4-9: shot slides -------------------------------------------
    shot_slides = [
        ("The customer experience", "demo-03.png",
         "A Tangerine-branded assistant that answers customer questions "
         "instantly, around the clock."),
        ("Answers you can trust", "demo-04.png",
         "Every answer is grounded in Tangerine's own documents, with "
         "citations back to the source."),
        ("Guided self-service", "demo-05.png",
         "Guided journeys: the Plan Finder walks customers to the right plan "
         "in four questions."),
        ("Grounded in your real content", "backend-02.png",
         "Built on Tangerine's real corpus: 390 documents from live CIS, "
         "SFOA, NBN and KFS sources."),
        ("Knowledge that maintains itself", "backend-03.png",
         "Data Augmentation Agents label and summarise content automatically, "
         "one-shot or continuously."),
        ("Quality you can measure", "backend-06.png",
         "Built-in REMi evaluation measures Answer Relevance, Context "
         "Relevance and Groundedness."),
    ]
    for idx, (title, fname, caption) in enumerate(shot_slides):
        s = blank(prs)
        set_bg(s, WHITE)
        add_title(s, title)
        l, t, w, h = add_shot(s, SHOTS / fname, 0.66, 1.12, 12.0, 5.06)
        add_caption(s, caption, l, t + h + 0.1, w)
        add_footer(s, 4 + idx)

    # ---- Slide 10: Next steps (orange gradient) ----------------------------
    s = blank(prs)
    gradient_bg(s)
    add_watermark(s, size=5.2, l=9.1, t=-1.6)
    s.shapes.add_picture(str(BRAND / "logo-white.png"), Inches(0.9), Inches(0.7),
                         height=Inches(0.6))
    add_text(s, 0.9, 1.65, 11.5, 0.9, [
        {"text": "NEXT STEPS", "size": 36, "bold": True, "color": WHITE,
         "font": HEAD_FONT}])
    # Pilot scope card
    pc = add_card(s, 0.9, 2.75, 5.75, 3.9, fill=WHITE, line=None, shadow=True)
    fill_card(pc, [
        {"text": "A focused pilot", "size": 18, "bold": True, "color": HEADING,
         "space_after": 10},
        {"text": "Point Progress Agentic RAG at a defined slice of Tangerine's "
                 "knowledge: NBN, mobile CIS and SFOA.",
         "size": 13.5, "color": DARK, "line_spacing": 1.14, "space_after": 8},
        {"text": "Stand up the customer support chat and the Plan Finder.",
         "size": 13.5, "color": DARK, "line_spacing": 1.14, "space_after": 8},
        {"text": "Measure Answer Relevance, Context Relevance and Groundedness "
                 "with REMi.",
         "size": 13.5, "color": DARK, "line_spacing": 1.14, "space_after": 8},
        {"text": "Review deflection and answer quality together.",
         "size": 13.5, "color": DARK, "line_spacing": 1.14},
    ], pad_top=0.35, anchor=MSO_ANCHOR.TOP)
    # Contact card
    cc = add_card(s, 6.95, 2.75, 5.45, 3.9, fill=WHITE, line=None, shadow=True)
    fill_card(cc, [
        {"text": "Let's talk", "size": 18, "bold": True, "color": HEADING,
         "space_after": 12},
        {"text": "Jay Sanderson", "size": 15, "bold": True, "color": DARK,
         "space_after": 3},
        {"text": "Progress Software", "size": 13.5, "color": MUTED,
         "space_after": 14},
        {"text": "Platform: Progress Agentic RAG", "size": 13.5, "color": MUTED},
    ], pad_top=0.35, anchor=MSO_ANCHOR.TOP)

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(out_path))
    print(f"Saved {out_path} ({len(prs.slides)} slides)")


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "decks/tangerine-arag-2026-07-03.pptx"
    build(out)
