"""ANZ sales meeting pre-read deck (6 slides) on the Progress corporate template.
Spec: /Users/user/Claude/aragmlgo/copilot/briefs/2026-10-10-sales-meeting-deck-spec.md
Python only. Reuses scripts/build_from_template.py (drop_slides) and scripts/deck_design.py (txt, add_shadow)."""
import sys, datetime
from pathlib import Path
ROOT = Path("/Users/user/Claude/ARAG-PMK-1")
sys.path.insert(0, str(ROOT / "scripts"))
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from PIL import ImageFont
import cairosvg
from build_from_template import drop_slides
from deck_design import txt, add_shadow, WHITE, MUTED

HERE = ROOT / "decks" / "anz-sales-meeting"
OUT = ROOT / "decks" / f"anz-sales-meeting-agentic-rag-2026-10-10.pptx"
TEMPLATE = ROOT / "brand/templates/progress-corporate-fy26.pptx"

# Template theme palette (theme1.xml): dk2 navy, accent3/4 blues, lt2/accent5 pale, accent1 green
NAVY = RGBColor(0x00, 0x20, 0x6B)
BLUE = RGBColor(0x2B, 0x2B, 0xB2)
BLUE_BRIGHT = RGBColor(0x4B, 0x4B, 0xF7)
PALE = RGBColor(0xEE, 0xF5, 0xFF)
PALE_DEEP = RGBColor(0xDC, 0xEC, 0xFF)
BLUE_SOFT = RGBColor(0xA9, 0xB4, 0xF0)   # tint of the template blue for de-emphasised bars
PARTNER = RGBColor(0x00, 0x89, 0x63)     # THE one accent: partner-sourced only
INK = RGBColor(0x1A, 0x1A, 0x2E)
GREYTXT = RGBColor(0x4A, 0x52, 0x68)

ML, CW = 0.79, 11.75          # left margin and content width, from the template title placeholder
TITLE_T, TITLE_H = 0.59, 1.25
BODY_T = 1.85
FOOT_LIMIT = 6.7

F_REG = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 100)
F_BLD = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 100)
def text_w(s, pt, bold=False):
    return (F_BLD if bold else F_REG).getlength(s) / 100 * pt / 72

# ---- TYPE SCALE: six steps, same role = same size on every slide
SZ_DISPLAY = 60   # hero numerals (slide 1 stats, slide 4 cluster totals)
SZ_COVER = 36     # slide 1 headline only
SZ_TITLE = 26     # slide headline, slides 2-6
SZ_SUB = 18       # sub-heads: stage names, play names, month labels, team names, stat labels, ISVCO tile, "7 opps"
SZ_BODY = 14      # all running copy
SZ_CAP = 12       # captions: section labels, chart text, chips, tags, source and as-of lines, pill
def layout(prs, name):
    for ly in prs.slide_layouts:
        if ly.name == name: return ly
    raise KeyError(name)

def set_title(slide, text, color=NAVY, size=SZ_TITLE, l=ML, t=TITLE_T, w=CW, h=TITLE_H):
    ph = slide.shapes.title
    ph.left, ph.top, ph.width, ph.height = Inches(l), Inches(t), Inches(w), Inches(h)  # all four: no zero-width trap
    tf = ph.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.TOP
    tf.text = text
    for r in tf.paragraphs[0].runs:
        r.font.size = Pt(size); r.font.bold = True; r.font.color.rgb = color; r.font.name = "Arial"
    return ph

def rect(slide, l, t, w, h, fill, shape=MSO_SHAPE.RECTANGLE, radius=None, line=None):
    s = slide.shapes.add_shape(shape, Inches(l), Inches(t), Inches(w), Inches(h))
    if radius is not None and shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        s.adjustments[0] = radius
    if fill is None: s.fill.background()
    else:
        s.fill.solid(); s.fill.fore_color.rgb = fill
    if line is None: s.line.fill.background()
    else:
        s.line.color.rgb = line[0]; s.line.width = Pt(line[1])
    s.shadow.inherit = False
    return s

def run(text, size, bold=False, color=INK, **kw):
    d = {"text": text, "size": size, "bold": bold, "color": color}; d.update(kw); return d

def rich(slide, l, t, w, h, parts, size, color=INK, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, line_spacing=1.1):
    """One paragraph of mixed bold/regular runs."""
    tb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = True; tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]; p.alignment = align; p.line_spacing = line_spacing
    for s, b in parts:
        r = p.add_run(); r.text = s; r.font.size = Pt(size); r.font.bold = b
        r.font.color.rgb = color; r.font.name = "Arial"
    return tb

# ------------------------------------------------------------------ icons: one line-icon set, each says something specific about its stage
ICONS = {
 "demand": '<path d="M3 4h18l-7 8v6l-4 2v-8z"/>',                                             # funnel: demand generation
 "partners": '<circle cx="8.5" cy="12" r="5"/><circle cx="15.5" cy="12" r="5"/>',            # two linked rings: joint delivery
 "sellers": '<circle cx="10" cy="8" r="4"/><path d="M2.5 21a7.5 7.5 0 0 1 15 0"/><polyline points="15.5 12.5 18 15 22.5 9.5"/>',  # person with tick: quota retired
 "delivery": '<polyline points="8 7 3 12 8 17"/><polyline points="16 7 21 12 16 17"/><line x1="14" y1="5" x2="10" y2="19"/>',  # code brackets: open-source CorpusKit
 "expansion": '<ellipse cx="11" cy="5" rx="7" ry="2.8"/><path d="M4 5v10c0 1.5 3.1 2.8 7 2.8s7-1.3 7-2.8V5"/><path d="M4 10c0 1.5 3.1 2.8 7 2.8s7-1.3 7-2.8"/><line x1="19" y1="17" x2="19" y2="23"/><line x1="16" y1="20" x2="22" y2="20"/>',  # knowledge box + plus: more boxes
}
def icon_png(name):
    p = HERE / "icons" / f"{name}.png"
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" '
           f'stroke="#FFFFFF" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">{ICONS[name]}</svg>')
    cairosvg.svg2png(bytestring=svg.encode(), write_to=str(p), output_width=384, output_height=384)
    return p
