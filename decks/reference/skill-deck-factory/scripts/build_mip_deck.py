"""Build the ISVCO x Progress Agentic RAG partner deck (16:9).

ISVCO-branded (navy ink + olive-green accent + teal, real ISVCO logo). ISVCO is a
Progress partner; the platform is Progress Agentic RAG. Covers three prototyped
use cases: document processing, real-time customer support (customer self-service
voice/chat + live agent assist), and call summary & analysis. All capability copy
is limited to claims verified against the Progress Agentic RAG / Nuclia KB.

Run: DECK_BRAND=isvco .venv/bin/python scripts/build_mip_deck.py decks/<name>.pptx
"""
import json
import os
import sys
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

BRAND = Path("brand")
SHOTS = Path("shots")


def _rgb(hexstr, default):
    if not hexstr:
        return default
    h = hexstr.lstrip("#")
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _mix(rgb, target, t):
    return RGBColor(*[round(c + (tc - c) * t) for c, tc in zip(rgb, target)])


_kit = os.environ.get("DECK_BRAND", "isvco")
_bj = Path(_kit) if _kit.endswith(".json") else BRAND / f"{_kit}.json"
_brand = json.loads(_bj.read_text()) if _bj.exists() else {}

GREEN = _rgb(_brand.get("primary"), RGBColor(0x93, 0xA8, 0x3C))   # ISVCO accent
NAVY = _rgb(_brand.get("ink"), RGBColor(0x1E, 0x2F, 0x5E))         # ISVCO ink
TEAL = _rgb(_brand.get("teal"), RGBColor(0x23, 0x6C, 0x98))        # ISVCO secondary
LIME = RGBColor(0xC0, 0xD8, 0x80)                                  # light circle

# Progress Software (secondary co-brand): its own logo, colours and font.
PROGRESS_GREEN = RGBColor(0x5C, 0xE5, 0x00)
PROGRESS_NAVY = RGBColor(0x15, 0x19, 0x50)
PLOGO_WHITE = "logo-white.png"   # Progress wordmark, white (for dark backgrounds)
PLOGO_NAVY = "logo-black.png"    # Progress wordmark, navy (for light backgrounds)
PMARK_GREEN = "mark-green.png"   # Progress mark, green
ARIAL = "Arial"                  # Progress (and ISVCO) brand font; installed, not faked

# Progress Agentic RAG PRODUCT brand (from progress.com/agentic-rag): a cobalt
# blue with a hexagon "knowledge-layer" node + sparkle mark, distinct from the
# corporate green. Used for product callouts; the corporate logo stays for the
# company partnership lockups.
PARAG_BLUE = RGBColor(0x0B, 0x4F, 0xE0)   # product cobalt (page CTA ~#0048fc)
PARAG_INK = RGBColor(0x0A, 0x16, 0x4A)    # product deep navy

WHITE = RGBColor(0xFF, 0xFF, 0xFF)
DARK = RGBColor(0x1A, 0x1A, 0x1A)
MUTED = RGBColor(0x5F, 0x5F, 0x5F)
CARD_FILL = RGBColor(0xFF, 0xFF, 0xFF)
CARD_LINE = RGBColor(0xE6, 0xE6, 0xE6)
IMG_BORDER = RGBColor(0xC8, 0xC8, 0xC8)

HEADING = NAVY
GRAD_LIGHT = _mix(TEAL, (255, 255, 255), 0.04)   # teal top
GRAD_DEEP = _mix(NAVY, (0, 0, 0), 0.16)           # navy bottom

HEAD_FONT = "Calibri"   # ISVCO font (Arial) not faked; Calibri used for the deck
BODY_FONT = "Calibri"

LOGO = "sample-logo-full.png"
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


def add_title(slide, text, color=NAVY, l=0.66, t=0.40, w=12.0):
    add_text(slide, l, t, w, 0.85,
             [{"text": text.upper(), "size": 25, "bold": True, "color": color,
               "font": HEAD_FONT}])
    bar = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                 Inches(l + 0.02), Inches(t + 0.74), Inches(0.62),
                                 Inches(0.07))
    bar.adjustments[0] = 0.5
    bar.fill.solid()
    bar.fill.fore_color.rgb = GREEN
    bar.line.fill.background()
    bar.shadow.inherit = False


def add_shadow(shape, blur=50800, dist=25400, alpha=22000):
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


def _oval(slide, l, t, d, color):
    o = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(l), Inches(t),
                               Inches(d), Inches(d))
    o.fill.solid()
    o.fill.fore_color.rgb = color
    o.line.fill.background()
    o.shadow.inherit = False
    return o


def circle_motif(slide, cx, cy, scale=1.0):
    """ISVCO's overlapping-circle mark, drawn in the brand palette."""
    _oval(slide, cx, cy, 0.42 * scale, GREEN)
    _oval(slide, cx + 0.34 * scale, cy + 0.10 * scale, 0.30 * scale, LIME)
    _oval(slide, cx + 0.16 * scale, cy + 0.34 * scale, 0.24 * scale, TEAL)


def add_pill(slide, l, t, text, size=12, fill=None, txt=None):
    fill = GREEN if fill is None else fill
    txt = NAVY if txt is None else txt
    w = 0.5 + len(text) * 0.096
    h = 0.44
    pill = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                  Inches(l), Inches(t), Inches(w), Inches(h))
    pill.adjustments[0] = 0.5
    pill.fill.solid()
    pill.fill.fore_color.rgb = fill
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
    _style_run(r, size, True, txt, HEAD_FONT)
    return pill


def progress_lockup(slide, right_x, top, label, on_dark=True):
    """Secondary co-brand mark: a small label + the real Progress logo,
    right-aligned to right_x. Progress's own logo, colour and font."""
    logo = PLOGO_WHITE if on_dark else PLOGO_NAVY
    lbl = WHITE if on_dark else PROGRESS_NAVY
    lh = 0.34
    lw = lh * (3200 / 750)
    add_text(slide, right_x - 3.4, top, 3.4, 0.24,
             [{"text": label, "size": 9.5, "bold": True, "color": lbl,
               "font": ARIAL, "align": PP_ALIGN.RIGHT}], align=PP_ALIGN.RIGHT)
    slide.shapes.add_picture(str(BRAND / logo), Inches(right_x - lw),
                             Inches(top + 0.26), height=Inches(lh))


def parag_mark(slide, l, t, d):
    """Progress Agentic RAG product mark: a cobalt hexagon 'knowledge-layer'
    node with a white sparkle, echoing progress.com/agentic-rag."""
    hexg = slide.shapes.add_shape(MSO_SHAPE.HEXAGON, Inches(l), Inches(t),
                                  Inches(d), Inches(d))
    hexg.fill.solid()
    hexg.fill.fore_color.rgb = PARAG_BLUE
    hexg.line.fill.background()
    hexg.shadow.inherit = False
    sp = 0.5 * d
    star = slide.shapes.add_shape(MSO_SHAPE.STAR_4_POINT,
                                  Inches(l + (d - sp) / 2), Inches(t + (d - sp) / 2),
                                  Inches(sp), Inches(sp))
    star.fill.solid()
    star.fill.fore_color.rgb = WHITE
    star.line.fill.background()
    star.shadow.inherit = False
    try:
        star.adjustments[0] = 0.12   # slim, sparkle-like points
    except Exception:
        pass


def _parag_runs(paragraph, size):
    """Two-tone 'Progress Agentic RAG' wordmark: navy 'Progress ' + blue rest."""
    r1 = paragraph.add_run()
    r1.text = "Progress "
    _style_run(r1, size, True, PARAG_INK, ARIAL)
    r2 = paragraph.add_run()
    r2.text = "Agentic RAG"
    _style_run(r2, size, True, PARAG_BLUE, ARIAL)


def powered_by_progress(slide, l, t):
    """White pill: product hexagon-sparkle mark + 'Powered by | Progress Agentic
    RAG' wordmark, in the Agentic RAG product colours."""
    h = 0.5
    ms = 0.3
    w = 3.95
    pill = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                  Inches(l), Inches(t), Inches(w), Inches(h))
    pill.adjustments[0] = 0.5
    pill.fill.solid()
    pill.fill.fore_color.rgb = WHITE
    pill.line.fill.background()
    pill.shadow.inherit = False
    parag_mark(slide, l + 0.18, t + (h - ms) / 2, ms)
    tb = slide.shapes.add_textbox(Inches(l + 0.18 + ms + 0.14), Inches(t),
                                  Inches(w - (0.18 + ms + 0.14) - 0.1), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = False
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_top = 0
    tf.margin_bottom = 0
    tf.margin_left = 0
    tf.margin_right = 0
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    lead = p.add_run()
    lead.text = "POWERED BY  "
    _style_run(lead, 9.5, True, MUTED, ARIAL)
    _parag_runs(p, 13)


def parag_lockup(slide, right_x, top):
    """Right-aligned product lockup for light slides: small 'POWERED BY' label
    over [hexagon-sparkle mark] + 'Progress Agentic RAG' wordmark."""
    add_text(slide, right_x - 3.6, top, 3.6, 0.22,
             [{"text": "POWERED BY", "size": 9.5, "bold": True, "color": MUTED,
               "font": ARIAL, "align": PP_ALIGN.RIGHT}], align=PP_ALIGN.RIGHT)
    d = 0.36
    gap = 0.14
    text_w = 2.35
    row_t = top + 0.26
    start_x = right_x - (d + gap + text_w)
    parag_mark(slide, start_x, row_t, d)
    tb = slide.shapes.add_textbox(Inches(start_x + d + gap), Inches(row_t - 0.05),
                                  Inches(text_w), Inches(d + 0.1))
    tf = tb.text_frame
    tf.word_wrap = False
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_top = 0
    tf.margin_bottom = 0
    tf.margin_left = 0
    tf.margin_right = 0
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    _parag_runs(p, 16)


def add_badge(slide, l, t, d, label, fill=NAVY, txt=WHITE, size=24):
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
    """Navy rounded tile carrying ISVCO's green circle-cluster motif."""
    tile = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                  Inches(l), Inches(t), Inches(d), Inches(d))
    tile.adjustments[0] = 0.28
    tile.fill.solid()
    tile.fill.fore_color.rgb = NAVY
    tile.line.fill.background()
    tile.shadow.inherit = False
    s = d / 0.6
    circle_motif(slide, l + 0.12 * s, t + 0.11 * s, scale=0.62 * s)
    return tile


def add_footer(slide, page_no):
    slide.shapes.add_picture(str(BRAND / LOGO),
                             Inches(0.66), Inches(6.98), height=Inches(0.3))
    add_text(slide, 11.5, 6.98, 1.2, 0.35,
             [{"text": f"ISVCO  ·  {page_no}", "size": 10, "bold": False,
               "color": MUTED, "font": BODY_FONT, "align": PP_ALIGN.RIGHT}],
             align=PP_ALIGN.RIGHT)


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
    tf.margin_left = Inches(0.26)
    tf.margin_right = Inches(0.26)
    tf.margin_top = Inches(pad_top)
    tf.margin_bottom = Inches(0.2)
    for i, p in enumerate(paras):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.space_after = Pt(p.get("space_after", 6))
        para.space_before = Pt(p.get("space_before", 0))
        para.line_spacing = p.get("line_spacing", 1.0)
        para.alignment = p.get("align", PP_ALIGN.LEFT)
        run = para.add_run()
        run.text = p["text"]
        _style_run(run, p.get("size", 13), p.get("bold", False),
                   p.get("color", DARK), p.get("font", BODY_FONT))


def add_flow(slide, steps, top, left=0.66, total_w=12.0, height=1.9):
    n = len(steps)
    gap = 0.42
    cw = (total_w - (n - 1) * gap) / n
    for i, (head, body) in enumerate(steps):
        l = left + i * (cw + gap)
        card = add_card(slide, l, top, cw, height, fill=WHITE, line=CARD_LINE)
        add_badge(slide, l + 0.24, top + 0.24, 0.4, str(i + 1), fill=GREEN,
                  txt=NAVY, size=15)
        fill_card(card, [
            {"text": head, "size": 13.5, "bold": True, "color": NAVY,
             "space_after": 5},
            {"text": body, "size": 11, "color": MUTED, "line_spacing": 1.08},
        ], pad_top=0.82, anchor=MSO_ANCHOR.TOP)
        if i < n - 1:
            ch = slide.shapes.add_shape(MSO_SHAPE.CHEVRON,
                                        Inches(l + cw + 0.06), Inches(top + height / 2 - 0.14),
                                        Inches(0.3), Inches(0.28))
            ch.fill.solid()
            ch.fill.fore_color.rgb = GREEN
            ch.line.fill.background()
            ch.shadow.inherit = False


def add_shot(slide, path, bx, by, bw, bh):
    iw, ih = Image.open(path).size
    ar = iw / ih
    if ar > bw / bh:
        w, h = bw, bw / ar
    else:
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
             [{"text": text, "size": 11.5, "bold": False, "color": MUTED,
               "font": BODY_FONT, "align": PP_ALIGN.CENTER}],
             align=PP_ALIGN.CENTER)


def shot_slide(prs, kicker, title, fname, caption, page_no, box=None):
    s = blank(prs)
    set_bg(s, WHITE)
    add_text(s, 0.66, 0.42, 12.0, 0.35, [
        {"text": kicker.upper(), "size": 12, "bold": True, "color": GREEN,
         "font": HEAD_FONT}])
    add_text(s, 0.66, 0.72, 12.0, 0.55, [
        {"text": title, "size": 22, "bold": True, "color": NAVY,
         "font": HEAD_FONT}])
    bx, by, bw, bh = box or (0.66, 1.5, 12.0, 4.7)
    l, t, w, h = add_shot(s, SHOTS / fname, bx, by, bw, bh)
    add_caption(s, caption, 0.66, min(by + bh + 0.06, t + h + 0.08), 12.0)
    add_footer(s, page_no)
    return s


def blank(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])


def build(out_path):
    prs = Presentation()
    prs.slide_width = Inches(SW)
    prs.slide_height = Inches(SH)

    # ---- Slide 1: Title (teal -> navy gradient) ----------------------------
    s = blank(prs)
    gradient_bg(s)
    circle_motif(s, 11.15, 5.35, scale=3.6)   # large brand motif, bottom-right
    # ISVCO logo on a white panel (colour logo reads on white)
    panel = add_card(s, 0.9, 0.72, 3.05, 1.12, fill=WHITE, line=None, shadow=True)
    s.shapes.add_picture(str(BRAND / LOGO), Inches(1.16), Inches(0.98),
                         width=Inches(2.5))
    progress_lockup(s, 12.43, 0.92, "IN PARTNERSHIP WITH", on_dark=True)
    powered_by_progress(s, 0.92, 2.08)
    add_text(s, 0.88, 2.86, 11.8, 2.4, [
        {"text": "THREE PROTOTYPES,", "size": 44, "bold": True, "color": WHITE,
         "font": HEAD_FONT, "space_after": 0, "line_spacing": 1.0},
        {"text": "BUILT ON YOUR KNOWLEDGE", "size": 44, "bold": True,
         "color": LIME, "font": HEAD_FONT, "space_after": 14, "line_spacing": 1.0},
        {"text": "AI use cases prototyped for ISVCO and its clients.",
         "size": 19, "bold": False, "color": WHITE, "font": BODY_FONT,
         "line_spacing": 1.1},
    ])
    add_text(s, 0.9, 6.5, 11.6, 0.7, [
        {"text": "Prepared for Kelly O'Donnell & the ISVCO team  ·  July 2026",
         "size": 13, "bold": False, "color": WHITE, "font": BODY_FONT,
         "space_after": 2},
        {"text": "Built on Progress Agentic RAG",
         "size": 12, "bold": False, "color": LIME, "font": BODY_FONT}])

    # ---- Slide 2: Recap (white) --------------------------------------------
    s = blank(prs)
    set_bg(s, WHITE)
    add_title(s, "From our conversation to working prototypes")
    add_text(s, 0.66, 1.32, 12.0, 0.9, [
        {"text": "When we spoke on 17 June we scoped three use cases across "
                 "three of your clients. As a Progress partner, ISVCO can deliver "
                 "each on Progress Agentic RAG, the AI layer over the knowledge "
                 "your systems already hold. All three are now working "
                 "prototypes.",
         "size": 14.5, "color": MUTED, "font": BODY_FONT, "line_spacing": 1.14}])
    cases = [
        ("1", "Document processing",
         "Turn unstructured documents into structured, searchable, cited "
         "knowledge."),
        ("2", "Real-time customer support",
         "Grounded, cited answers for customers by voice and chat, plus live "
         "assist for your agents."),
        ("3", "Call summary & analysis",
         "Transcribe call recordings, then summarise and extract the entities "
         "and topics that matter."),
    ]
    cw, gap = 3.85, 0.35
    left0 = (SW - (3 * cw + 2 * gap)) / 2
    for i, (num, head, body) in enumerate(cases):
        l = left0 + i * (cw + gap)
        card = add_card(s, l, 2.75, cw, 3.25)
        add_badge(s, l + 0.32, 2.75 + 0.34, 0.74, num)
        fill_card(card, [
            {"text": head, "size": 17, "bold": True, "color": NAVY,
             "space_after": 8},
            {"text": body, "size": 13.5, "color": MUTED, "line_spacing": 1.16},
        ], pad_top=1.28, anchor=MSO_ANCHOR.TOP)
    add_footer(s, 2)

    # ---- Slide 3: One platform (white, KB-verified) ------------------------
    s = blank(prs)
    set_bg(s, WHITE)
    add_title(s, "One platform behind all three")
    parag_lockup(s, 12.66, 0.5)
    add_text(s, 0.66, 1.32, 12.0, 0.7, [
        {"text": "You already build on Progress. Progress Agentic RAG (Nuclia) "
                 "turns your own content into trusted, cited answers, in any "
                 "language.",
         "size": 15, "color": MUTED, "font": BODY_FONT, "line_spacing": 1.12}])
    answers = [
        ("Grounded answers with citations",
         "Answers are generated only from your own content and cite the source "
         "passages they draw on."),
        ("Understands any content",
         "Ingests 100+ file formats, documents, images, audio and video, with "
         "OCR and speech-to-text."),
        ("Enriches as it ingests",
         "Data Augmentation Agents automatically label, summarise and extract "
         "entities and relationships."),
        ("Quality you can measure",
         "Built-in REMi evaluation scores Answer Relevance, Context Relevance "
         "and Groundedness."),
    ]
    cw2, ch2, gx, gy = 5.75, 2.02, 0.45, 0.3
    lx0 = (SW - (2 * cw2 + gx)) / 2
    ty0 = 2.28
    for i, (head, body) in enumerate(answers):
        r, c = divmod(i, 2)
        l = lx0 + c * (cw2 + gx)
        t = ty0 + r * (ch2 + gy)
        card = add_card(s, l, t, cw2, ch2)
        add_tile(s, l + 0.32, t + 0.32, 0.56)
        fill_card(card, [
            {"text": head, "size": 15.5, "bold": True, "color": NAVY,
             "space_after": 6},
            {"text": body, "size": 12.5, "color": DARK, "line_spacing": 1.14},
        ], pad_top=1.02, anchor=MSO_ANCHOR.TOP)
    add_footer(s, 3)

    # ---- Slide 4: Use case 1 - Document processing (flow) ------------------
    s = blank(prs)
    set_bg(s, WHITE)
    add_title(s, "Use case 1 · Document processing")
    add_text(s, 0.66, 1.32, 12.0, 0.6, [
        {"text": "Turn unstructured documents into structured, searchable, "
                 "cited knowledge.",
         "size": 15, "color": MUTED, "font": BODY_FONT, "line_spacing": 1.1}])
    add_flow(s, [
        ("Ingest", "100+ file formats, with OCR and speech-to-text applied when "
                   "needed."),
        ("Understand", "Smart semantic chunking, embeddings and an automatic "
                       "knowledge graph."),
        ("Enrich", "Labeler, Generator and Graph Extraction agents add labels, "
                   "summaries and entities."),
        ("Retrieve", "Granular passages returned with citations back to the "
                     "source."),
    ], top=2.28)
    card = add_card(s, 0.66, 4.68, 12.0, 1.5, fill=NAVY, line=None)
    fill_card(card, [
        {"text": "The prototype", "size": 12, "bold": True, "color": GREEN,
         "space_after": 4},
        {"text": "Point the platform at a client's document set and it returns "
                 "grounded answers with a citation back to the exact source "
                 "paragraph, ready to embed in a search or Q&A experience.",
         "size": 14, "color": WHITE, "line_spacing": 1.16}],
        pad_top=0.24, anchor=MSO_ANCHOR.MIDDLE)
    add_footer(s, 4)
    shot_slide(prs, "Use case 1 · in the prototype",
               "From raw document to structured, cited fields",
               "demo-doc.png",
               "Document Intelligence Studio on Progress Agentic RAG: a sample "
               "invoice classified, read by a visual LLM, then enriched and "
               "standardised into typed fields and JSON, XML or CSV.",
               5)

    # ---- Slide 6: Use case 2 - Real-time customer support (flow) -----------
    s = blank(prs)
    set_bg(s, WHITE)
    add_title(s, "Use case 2 · Real-time customer support")
    add_text(s, 0.66, 1.32, 12.0, 0.6, [
        {"text": "Grounded, cited answers from your Knowledge Box, for your "
                 "customers and for the agents who serve them.",
         "size": 15, "color": MUTED, "font": BODY_FONT, "line_spacing": 1.1}])
    add_flow(s, [
        ("Customer or agent", "A customer asks by voice or chat, or an agent "
                              "works a live call."),
        ("Retrieve", "The Knowledge Box finds the relevant passages from your "
                     "trusted content."),
        ("Answer or brief", "A cited answer for the customer, or a live brief "
                            "for the agent."),
        ("Escalate & learn", "Low-confidence queries route to a human, and the "
                             "answer is learned."),
    ], top=2.28)
    lc = add_card(s, 0.66, 4.68, 5.83, 1.62, fill=WHITE, line=CARD_LINE)
    fill_card(lc, [
        {"text": "Self-service, in their words", "size": 13.5, "bold": True,
         "color": NAVY, "space_after": 5},
        {"text": "A no-code, embeddable voice and chat widget answers customers "
                 "directly, with citations, in any language.",
         "size": 12, "color": MUTED, "line_spacing": 1.14}],
        pad_top=0.22, anchor=MSO_ANCHOR.TOP)
    rc = add_card(s, 6.83, 4.68, 5.83, 1.62, fill=NAVY, line=None)
    fill_card(rc, [
        {"text": "Live assist for your agents", "size": 13.5, "bold": True,
         "color": GREEN, "space_after": 5},
        {"text": "Listens silently to a live call and keeps a real-time brief "
                 "updated: who they are speaking to, what they want and what to "
                 "say next, with sources.",
         "size": 12, "color": WHITE, "line_spacing": 1.14}],
        pad_top=0.22, anchor=MSO_ANCHOR.TOP)
    add_footer(s, 6)
    shot_slide(prs, "Use case 2 · in the prototype",
               "Grounded voice for customers",
               "demo-voice.png",
               "ARAG Voice: a voice front-end over Progress Agentic RAG, with "
               "live quality telemetry, citation coverage, handoff rate and "
               "response latency, and the retrieval bridge online.",
               7, box=(0.66, 2.15, 12.0, 2.7))
    shot_slide(prs, "Use case 2 · in the prototype",
               "Live assist that briefs the agent in real time",
               "demo-voice-listen.png",
               "The same engine listens to a live conversation and keeps a "
               "grounded brief evolving for the human agent, who they are "
               "speaking to, what they want and what to say next, and stays "
               "silent.",
               8, box=(0.66, 2.15, 12.0, 2.7))

    # ---- Slide 9: Use case 3 - Call summary & analysis (flow) --------------
    s = blank(prs)
    set_bg(s, WHITE)
    add_title(s, "Use case 3 · Call summary & analysis")
    add_text(s, 0.66, 1.32, 12.0, 0.6, [
        {"text": "Make call recordings searchable, then summarise and extract "
                 "what matters.",
         "size": 15, "color": MUTED, "font": BODY_FONT, "line_spacing": 1.1}])
    add_flow(s, [
        ("Transcribe", "Speech-to-text turns the recording into searchable "
                       "text."),
        ("Summarise", "Concise or extended summaries, with your own custom "
                      "prompt if needed."),
        ("Extract", "Named entities, topics and relationships surfaced "
                    "automatically."),
        ("Ask", "Generated Q&A lets the team query the call in plain "
                "language."),
    ], top=2.28)
    card = add_card(s, 0.66, 4.68, 12.0, 1.5, fill=NAVY, line=None)
    fill_card(card, [
        {"text": "The prototype", "size": 12, "bold": True, "color": GREEN,
         "space_after": 4},
        {"text": "A call recording becomes a concise summary, a list of key "
                 "entities and a set of answerable questions, every point "
                 "grounded in the transcript.",
         "size": 14, "color": WHITE, "line_spacing": 1.16}],
        pad_top=0.24, anchor=MSO_ANCHOR.MIDDLE)
    add_footer(s, 9)
    shot_slide(prs, "Use case 3 · in the prototype",
               "Every call summarised, scored and searchable",
               "demo-call-detail.png",
               "One analysed call: an AI summary, extracted entities, an agent "
               "scorecard, action items and notable quotes, with grounded "
               "“Ask this call” Q&A over the transcript.",
               10)
    shot_slide(prs, "Use case 3 · in the prototype",
               "Patterns across every conversation",
               "demo-call-dashboard.png",
               "The analytics view aggregates calls by reason, outcome, "
               "sentiment and line of business, with first-call resolution, "
               "complaint rate and compliance at a glance.",
               11)

    # ---- Slide 12: Trust / REMi (white) ------------------------------------
    s = blank(prs)
    set_bg(s, WHITE)
    add_title(s, "Answers you can trust, and measure")
    add_text(s, 0.66, 1.32, 12.0, 0.6, [
        {"text": "Every answer is generated only from your content and cited, "
                 "then scored by REMi, Nuclia's open RAG-evaluation model.",
         "size": 15, "color": MUTED, "font": BODY_FONT, "line_spacing": 1.12}])
    metrics = [
        ("Answer Relevance", "Does the answer actually address the question "
                             "that was asked?"),
        ("Context Relevance", "Was the retrieved content relevant to the "
                              "question in the first place?"),
        ("Groundedness", "Is the answer genuinely supported by the retrieved "
                         "source content?"),
    ]
    cw3, gap3 = 3.85, 0.35
    l0 = (SW - (3 * cw3 + 2 * gap3)) / 2
    for i, (head, body) in enumerate(metrics):
        l = l0 + i * (cw3 + gap3)
        card = add_card(s, l, 2.6, cw3, 3.05)
        add_tile(s, l + 0.32, 2.6 + 0.34, 0.62)
        fill_card(card, [
            {"text": head, "size": 16, "bold": True, "color": NAVY,
             "space_after": 8},
            {"text": body, "size": 13, "color": MUTED, "line_spacing": 1.18},
        ], pad_top=1.28, anchor=MSO_ANCHOR.TOP)
    add_footer(s, 12)

    # ---- Slide 13: Deployment & data residency (white) ---------------------
    s = blank(prs)
    set_bg(s, WHITE)
    add_title(s, "Deploy on your terms, including in-country")
    add_text(s, 0.66, 1.32, 12.0, 0.6, [
        {"text": "Cloud, hybrid or fully on-premise, with ISO 27001 and SOC 2 "
                 "Type 2 accreditation and per-client data isolation.",
         "size": 15, "color": MUTED, "font": BODY_FONT, "line_spacing": 1.12}])
    deploy = [
        ("Cloud", "Fully managed in the EU (Google) or USA (AWS) regions. The "
                  "fastest way to stand a prototype up."),
        ("Hybrid", "Processing runs in Nuclia's cloud while your data stays in "
                   "your own NucliaDB instance."),
        ("On-premise", "The entire pipeline runs inside your own "
                       "infrastructure, the path to keep a client's data "
                       "in-country."),
    ]
    cw4, gap4 = 3.85, 0.35
    l0 = (SW - (3 * cw4 + 2 * gap4)) / 2
    for i, (head, body) in enumerate(deploy):
        l = l0 + i * (cw4 + gap4)
        card = add_card(s, l, 2.55, cw4, 2.7)
        add_tile(s, l + 0.32, 2.55 + 0.32, 0.56)
        fill_card(card, [
            {"text": head, "size": 17, "bold": True, "color": NAVY,
             "space_after": 8},
            {"text": body, "size": 13, "color": MUTED, "line_spacing": 1.16},
        ], pad_top=1.05, anchor=MSO_ANCHOR.TOP)
    note = add_card(s, 0.66, 5.5, 12.0, 0.85, fill=RGBColor(0xEF, 0xF3, 0xE6),
                    line=None, shadow=False)
    fill_card(note, [
        {"text": "For a South African client, on-premise or hybrid keeps data "
                 "in-country; there is no local cloud region today.",
         "size": 12.5, "color": NAVY, "line_spacing": 1.1,
         "align": PP_ALIGN.CENTER}],
        pad_top=0.16, anchor=MSO_ANCHOR.MIDDLE)
    add_footer(s, 13)

    # ---- Slide 14: Next steps (teal -> navy gradient) ----------------------
    s = blank(prs)
    gradient_bg(s)
    panel = add_card(s, 0.9, 0.66, 3.05, 1.06, fill=WHITE, line=None, shadow=True)
    s.shapes.add_picture(str(BRAND / LOGO), Inches(1.16), Inches(0.9),
                         width=Inches(2.5))
    progress_lockup(s, 12.43, 2.05, "IN PARTNERSHIP WITH", on_dark=True)
    add_text(s, 0.9, 2.0, 11.5, 0.9, [
        {"text": "NEXT STEPS", "size": 34, "bold": True, "color": WHITE,
         "font": HEAD_FONT}])
    pc = add_card(s, 0.9, 3.0, 6.0, 3.7, fill=WHITE, line=None, shadow=True)
    fill_card(pc, [
        {"text": "Let's get the team together", "size": 18, "bold": True,
         "color": NAVY, "space_after": 12},
        {"text": "Walk the ISVCO team through all three prototypes, live.",
         "size": 14, "color": DARK, "line_spacing": 1.16, "space_after": 8},
        {"text": "Pick the client and use case with the strongest pull.",
         "size": 14, "color": DARK, "line_spacing": 1.16, "space_after": 8},
        {"text": "Scope a focused pilot on that client's real content.",
         "size": 14, "color": DARK, "line_spacing": 1.16, "space_after": 8},
        {"text": "Agree how we measure success with REMi.",
         "size": 14, "color": DARK, "line_spacing": 1.16},
    ], pad_top=0.34, anchor=MSO_ANCHOR.TOP)
    cc = add_card(s, 7.2, 3.0, 5.2, 3.7, fill=WHITE, line=None, shadow=True)
    fill_card(cc, [
        {"text": "Let's talk", "size": 18, "bold": True, "color": NAVY,
         "space_after": 12},
        {"text": "Jay Sanderson", "size": 15, "bold": True, "color": DARK,
         "space_after": 3},
        {"text": "Progress Software", "size": 13.5, "color": MUTED,
         "space_after": 14},
        {"text": "Platform: Progress Agentic RAG", "size": 13, "color": DARK,
         "space_after": 3},
        {"text": "In partnership with ISVCO", "size": 13, "color": MUTED},
    ], pad_top=0.34, anchor=MSO_ANCHOR.TOP)

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(out_path))
    print(f"Saved {out_path} ({len(prs.slides)} slides)")


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "decks/isvco-progress-arag-2026-07-03.pptx"
    build(out)
