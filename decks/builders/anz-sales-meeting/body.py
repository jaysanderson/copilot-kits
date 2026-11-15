# ------------------------------------------------------------------ helpers
import math
def pill_text(shape, text, size, bold, color, align=PP_ALIGN.LEFT, ml=0.3, mr=0.2, wrap=True):
    tf = shape.text_frame; tf.margin_left = Inches(ml); tf.margin_right = Inches(mr); tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE; tf.word_wrap = wrap
    p = tf.paragraphs[0]; p.alignment = align
    r = p.add_run(); r.text = text; r.font.size = Pt(size); r.font.bold = bold; r.font.color.rgb = color; r.font.name = "Arial"

def wrap_lines(parts, size, width):
    nl, cur = 1, 0.0
    for t, b in parts:
        for wd in t.split(" "):
            ww = text_w(wd + " ", size, b)
            if cur + ww > width and cur > 0: nl += 1; cur = 0.0
            cur += ww
    return nl

prs = Presentation(str(TEMPLATE))
drop_slides(prs)

# ========== Slide 1 - Statement slide 1 (native full-bleed ribbon art); the numbers are the visual
s = prs.slides.add_slide(layout(prs, "Statement slide 1"))
set_title(s, "Agentic RAG in ANZ: from one-off deals to a repeatable engine", WHITE, SZ_COVER, ML, 0.7, 9.4, 1.5)
pill = rect(s, 11.05, 0.72, 1.5, 0.34, None, MSO_SHAPE.ROUNDED_RECTANGLE, 0.5, line=(WHITE, 0.75))
pill_text(pill, "INTERNAL ONLY", SZ_CAP, True, WHITE, PP_ALIGN.CENTER, 0, 0, False)
stats = [("$268k", "Open ANZ pipeline", False), ("16", "Active opportunities", False),
         ("45%", "Through partner accounts", True), ("7", "Government, public & research opps", False)]
pitch = CW / 4   # true 4-column grid: left edges 0.79 / 3.73 / 6.66 / 9.60
for i, (num, lab, partner) in enumerate(stats):
    x = ML + i * pitch
    txt(s, x, 2.65, pitch - 0.1, 1.2, [run(num, SZ_DISPLAY, True, WHITE)], anchor=MSO_ANCHOR.BOTTOM)
    txt(s, x, 4.03, pitch - 0.3, 0.8, [run(lab, SZ_SUB, False, WHITE, line_spacing=1.05)])   # no unexplained marker on the cover
# as-of line belongs to the four figures above only (ISVCO is NOT from this CRM view)
txt(s, ML, 4.92, 9.0, 0.22, [run("CRM, ANZ Agentic RAG opportunities, 10 Oct 2026", SZ_CAP, False, RGBColor(0xC9, 0xCE, 0xF5))])
isvco = rect(s, ML, 5.35, CW, 0.55, NAVY, MSO_SHAPE.ROUNDED_RECTANGLE, 0.5, line=(WHITE, 1.0))
pill_text(isvco, "+ ISVCO: $100k+ software vendor opportunity (hackathon underway)", SZ_SUB, True, WHITE)
txt(s, ML, 6.14, 8.0, 0.26, [run("Every APJ deal is a full one-year commitment.", SZ_BODY, False, WHITE)])
txt(s, ML, 6.55, 8.0, 0.2, [run("Jay Sanderson, Agentic RAG go-to-market, APAC", SZ_CAP, False, RGBColor(0xC9, 0xCE, 0xF5))])  # attribution: caption step, muted, set apart from the sub-line

# ========== Slide 2 - Title Only: the engine (arrow-tab flow, no decorative icons)
s = prs.slides.add_slide(layout(prs, "Title Only"))
set_title(s, "One engine: demand → partners → sellers → delivery → expansion")
stages = [
 ("Demand", False, ["Events (ECU World Tourism Day)", "LinkedIn", "Nov founder webinar", "Public reference OPAX (620k+ docs)"]),
 ("Partners", True, ["equ", "Pingworks", "The Brand Agency", "BlueChip / Noice", "Plus partners on not-for-resale accounts"]),
 ("Sellers", False, ["ANZ seller + Agentic RAG team", "Any seller can retire quota on Agentic RAG"]),
 ("Delivery", False, ["Partners deliver on CorpusKit (open source)", "Customers buy partner hours on Progress paper"]),
 ("Expansion", False, ["More knowledge boxes and use cases", "e.g. FRDC +2 KBs; GRDC converting from FRDC’s licence"]),
]
sw_, sg = 2.15, 0.25
ICON_KEYS = ["demand", "partners", "sellers", "delivery", "expansion"]
for i, (name, partner, lines) in enumerate(stages):
    x = ML + i * (sw_ + sg)
    rect(s, x, 2.65, sw_, 3.45, PALE, MSO_SHAPE.RECTANGLE)
    tab = rect(s, x, BODY_T, sw_, 0.7, PARTNER if partner else BLUE, MSO_SHAPE.PENTAGON)   # two colours only: partner accent, all else one blue
    rect(s, x + 0.25, 2.65 + 0.22, 0.62, 0.62, PARTNER if partner else BLUE, MSO_SHAPE.OVAL)
    s.shapes.add_picture(str(icon_png(ICON_KEYS[i])), Inches(x + 0.25 + 0.14), Inches(2.65 + 0.22 + 0.14), Inches(0.34), Inches(0.34))
    tab.adjustments[0] = 0.3
    txt(s, x + 0.25, BODY_T, sw_ - 0.6, 0.7, [run(name, SZ_SUB, True, WHITE)], anchor=MSO_ANCHOR.MIDDLE)
    txt(s, x + 0.25, 2.65 + 0.98, sw_ - 0.45, 2.3, [run(l, SZ_BODY, False, INK, space_after=7, line_spacing=1.05) for l in lines])
cb = rect(s, ML, 6.28, CW, 0.45, PALE_DEEP, MSO_SHAPE.ROUNDED_RECTANGLE, 0.3)
pill_text(cb, "Developer training program launched: first 3 developers through.", SZ_BODY, True, NAVY)

# ========== Slide 3 - Title Only: the pipeline; the close-by-month chart is the dominant visual
s = prs.slides.add_slide(layout(prs, "Title Only"))
set_title(s, "$268k across 16 opportunities,\vand 87% of it closes by end of November")
gap = 0.3
pws = [3.0, 3.0, CW - 6.0 - 2 * gap]          # route, stage (supporting pair), close (dominant, 5.15in)
pxs = [ML, ML + pws[0] + gap, ML + pws[0] + pws[1] + 2 * gap]
ptop, ph_ = BODY_T, 3.9
labels = ["By route", "By stage", "By expected close"]
for i in range(3):
    rect(s, pxs[i], ptop, pws[i], ph_, PALE, MSO_SHAPE.ROUNDED_RECTANGLE, 0.03)
    txt(s, pxs[i] + 0.3, ptop + 0.25, pws[i] - 0.6, 0.25, [run(labels[i].upper(), SZ_CAP, True, BLUE)])

# A. route donut (freeform ring segments - editable, renders identically everywhere)
x0, pw0 = pxs[0], pws[0]
dcx, dcy, R_OUT, R_IN = x0 + pw0 / 2, ptop + 1.5, 0.95, 0.66
def ring_segment(slide, a0, a1, col):
    n = max(8, int(abs(a1 - a0) / 2))
    def pt(a, r):
        t = math.radians(a); return (dcx + r * math.sin(t), dcy - r * math.cos(t))
    pts = [pt(a0 + (a1 - a0) * k / n, R_OUT) for k in range(n + 1)] + [pt(a1 - (a1 - a0) * k / n, R_IN) for k in range(n + 1)]
    sc = 1000
    fb = slide.shapes.build_freeform(int(pts[0][0] * sc), int(pts[0][1] * sc), scale=Inches(1) / sc)
    fb.add_line_segments([(int(x * sc), int(y * sc)) for x, y in pts[1:]], close=True)
    sh = fb.convert_to_shape(); sh.fill.solid(); sh.fill.fore_color.rgb = col; sh.line.fill.background(); sh.shadow.inherit = False
    return sh
share = 119.9 / (119.9 + 147.7) * 360
ring_segment(s, 0, share, PARTNER); ring_segment(s, share, 360, BLUE)
txt(s, dcx - 0.65, dcy - 0.25, 1.3, 0.5, [run("45%", SZ_TITLE, True, PARTNER, align=PP_ALIGN.CENTER)], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
for j, (col, nm, val) in enumerate([(PARTNER, "Partner accounts", "$119.9k (45%)"), (BLUE, "Direct", "$147.7k (55%)")]):
    yy = ptop + 2.7 + j * 0.55
    rect(s, x0 + 0.3, yy + 0.04, 0.16, 0.16, col, MSO_SHAPE.OVAL)
    txt(s, x0 + 0.58, yy, 2.2, 0.25, [run(nm, SZ_CAP, False, INK)])
    txt(s, x0 + 0.58, yy + 0.22, 2.2, 0.25, [run(val, SZ_CAP, True, INK)])

# B. stage bars
x1, pw1 = pxs[1], pws[1]
stages_d = [("Qualify", 35.0, 2), ("Build", 200.9, 11), ("Prove", 17.3, 2), ("Negotiate", 14.4, 1)]
lab_w = 0.8
bar_x = x1 + 0.3 + lab_w
bar_max_w = pw1 - 0.3 - lab_w - 0.25
row_h, row_gap, y0 = 0.5, 0.25, ptop + 0.85
for j, (nm, v, n) in enumerate(stages_d):
    y = y0 + j * (row_h + row_gap)
    hi = nm == "Build"
    txt(s, x1 + 0.3, y, lab_w, row_h, [run(nm, SZ_CAP, hi, INK)], anchor=MSO_ANCHOR.MIDDLE)
    bw = max(0.06, bar_max_w * v / 200.9)
    rect(s, bar_x, y, bw, row_h, BLUE if hi else BLUE_SOFT)
    if hi:
        txt(s, bar_x, y, bw - 0.1, row_h, [run(f"${v:.1f}k ({n})", SZ_CAP, True, WHITE, align=PP_ALIGN.RIGHT)], align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)
    else:
        txt(s, bar_x + bw + 0.08, y, 1.1, row_h, [run(f"${v:.1f}k ({n})", SZ_CAP, True, INK)], anchor=MSO_ANCHOR.MIDDLE)

# C. expected close columns (dominant)
x2, pw2 = pxs[2], pws[2]
months = [("Oct", 117.3, 7, True), ("Nov", 118.4, 7, True), ("Dec", 16.0, 1, False), ("Jan", 16.0, 1, False)]
cw_ = 0.95
cgap = (pw2 - 0.8 - 4 * cw_) / 3
base_y = ptop + ph_ - 0.65
col_max_h = 2.1
for j, (nm, v, n, hi) in enumerate(months):
    cx = x2 + 0.4 + j * (cw_ + cgap)
    h = max(0.06, col_max_h * v / 118.4)
    rect(s, cx, base_y - h, cw_, h, BLUE if hi else BLUE_SOFT)
    txt(s, cx - 0.2, base_y - h - 0.5, cw_ + 0.4, 0.46,
        [run(f"${v:.1f}k", SZ_CAP, True, INK, align=PP_ALIGN.CENTER), run(f"({n})", SZ_CAP, False, GREYTXT, align=PP_ALIGN.CENTER)],
        align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.BOTTOM)
    txt(s, cx - 0.2, base_y + 0.1, cw_ + 0.4, 0.25, [run(nm, SZ_CAP, hi, INK, align=PP_ALIGN.CENTER)], align=PP_ALIGN.CENTER)
txt(s, ML, ptop + ph_ + 0.08, CW, 0.22, [run("Source: CRM, ANZ Agentic RAG opportunities, 10 Oct 2026. Figures in brackets are opportunity counts.", SZ_CAP, False, GREYTXT)])
cb3 = rect(s, ML, 6.08, CW, 0.7, WHITE, MSO_SHAPE.ROUNDED_RECTANGLE, 0.15, line=(NAVY, 1.5))
tf = cb3.text_frame; tf.margin_left = tf.margin_right = Inches(0.3); tf.margin_top = tf.margin_bottom = 0
tf.vertical_anchor = MSO_ANCHOR.MIDDLE; tf.word_wrap = True
p_ = tf.paragraphs[0]; p_.alignment = PP_ALIGN.LEFT; p_.line_spacing = 1.05
for t_, b_ in [("Beyond ANZ: ISVCO (South Africa). ", True),
               ("$100k+ potential. Agentic RAG being evaluated in an internal hackathon to decide which offerings ISVCO takes to market. Not included in the totals above.", False)]:
    r_ = p_.add_run(); r_.text = t_; r_.font.size = Pt(SZ_BODY); r_.font.bold = b_; r_.font.color.rgb = NAVY; r_.font.name = "Arial"

# ========== Slide 4 - Title Only: where we are winning
s = prs.slides.add_slide(layout(prs, "Title Only"))
set_title(s, "Strong in government and research, breaking into enterprise")
clusters = [
 ("Government, public & research", "~$116k", "7 opps",
  ["Telstra Health (National Cancer Screening Register)", "NSW Dept of Planning, Housing & Infrastructure",
   "Water Corporation WA", "Racing WA", "Holidayisle Island Authority", "FRDC", "GRDC"]),
 ("Enterprise & commercial", "~$151k", "9 opps",
  ["South32", "Cinema-group Theme Parks", "Team Global Express", "GPC Asia Pacific", "Hunter Douglas Australia",
   "MLC", "More Telecom", "Clinic", "Wesley Mission Queensland"]),
]
pw, gap = 5.7, 0.35
ptop, ph_ = BODY_T, 4.1
CHIP_H, CHIP_G = 0.4, 0.12
for i, (head, big, cnt, names) in enumerate(clusters):
    x = ML + i * (pw + gap)
    rect(s, x, ptop, pw, ph_, PALE, MSO_SHAPE.ROUNDED_RECTANGLE, 0.03)
    txt(s, x + 0.3, ptop + 0.22, pw - 0.6, 0.25, [run(head.upper(), SZ_CAP, True, BLUE)])
    bigw = text_w(big, SZ_DISPLAY, True)
    txt(s, x + 0.3, ptop + 0.5, bigw + 0.1, 1.0, [run(big, SZ_DISPLAY, True, NAVY)], anchor=MSO_ANCHOR.MIDDLE)
    txt(s, x + 0.3 + bigw + 0.2, ptop + 0.5, 1.5, 1.0, [run(cnt, SZ_SUB, True, GREYTXT)], anchor=MSO_ANCHOR.MIDDLE)
    cx, cy, maxw = x + 0.3, ptop + 1.75, pw - 0.6
    for nm in names:
        w = text_w(nm, SZ_CAP, True) + 0.36
        if cx > x + 0.3 and cx + w > x + 0.3 + maxw + 0.001:
            cx = x + 0.3; cy += CHIP_H + CHIP_G
        chip = rect(s, cx, cy, w, CHIP_H, WHITE, MSO_SHAPE.ROUNDED_RECTANGLE, 0.5)
        pill_text(chip, nm, SZ_CAP, True, NAVY, PP_ALIGN.CENTER, 0.05, 0.05, False)
        cx += w + CHIP_G
ty = 6.2
txt(s, ML, ty, 1.2, 0.4, [run("Use cases", SZ_CAP, True, GREYTXT)], anchor=MSO_ANCHOR.MIDDLE)
tx = ML + 1.15
for tag in ["Research portals", "Citizen/visitor information", "Document processing", "Knowledge assistants"]:
    w = text_w(tag, SZ_CAP, True) + 0.4
    t_ = rect(s, tx, ty, w, 0.4, None, MSO_SHAPE.ROUNDED_RECTANGLE, 0.5, line=(BLUE, 1.0))
    pill_text(t_, tag, SZ_CAP, True, BLUE, PP_ALIGN.CENTER, 0.05, 0.05, False)
    tx += w + 0.14

# ========== Slide 5 - Title Only: three plays, Trigger -> Asset -> Proof
s = prs.slides.add_slide(layout(prs, "Title Only"))
set_title(s, "Three plays any region can run")
plays = [
 ("Agency play", ["A partner has a live client proposal"], ["Demo + CorpusKit"], ["Closed in under 6 weeks"]),
 ("Research portal", ["A research body with content nobody can find"], ["CorpusKit portal"],
  ["FRDC in production, GRDC converting, OPAX live (620k+ docs)", "15 rural RDCs in reach"]),
 ("ISV embed", ["An OpenEdge ISV adding AI to its product"], ["Agentic RAG + OpenEdge MCP (+ Domo)"],
  ["ISVCO: $100k+ potential, hackathon underway", "Wholesaler use-case workshop proposed"]),
]
pw, gap = 3.75, 0.25
ctop = BODY_T
for i, (nm, trig, asset, proof) in enumerate(plays):
    x = ML + i * (pw + gap)
    rect(s, x, ctop, pw, 4.75, PALE, MSO_SHAPE.ROUNDED_RECTANGLE, 0.03)
    hd = rect(s, x, ctop, pw, 0.72, NAVY, MSO_SHAPE.ROUND_2_SAME_RECTANGLE)
    hd.adjustments[0] = 0.18; hd.adjustments[1] = 0
    txt(s, x + 0.3, ctop, 0.5, 0.72, [run(str(i + 1), SZ_TITLE, True, BLUE_SOFT)], anchor=MSO_ANCHOR.MIDDLE)
    txt(s, x + 0.8, ctop, pw - 1.0, 0.72, [run(nm, SZ_SUB, True, WHITE)], anchor=MSO_ANCHOR.MIDDLE)
    rows = [("TRIGGER", trig, False, 2.8, 0.6), ("ASSET", asset, False, 3.9, 0.6), ("PROOF", proof, True, 5.0, 1.45)]
    for lab, lines, bold, yy, hh in rows:
        txt(s, x + 0.3, yy, pw - 0.6, 0.22, [run(lab, SZ_CAP, True, BLUE)])
        paras = []
        for l in lines:
            lead = bold and l.startswith("ISVCO")
            paras.append(run(l, SZ_BODY, bold, NAVY if bold else INK, space_after=4, line_spacing=1.05))
        txt(s, x + 0.3, yy + 0.27, pw - 0.6, hh, paras)
    for ay in (3.65, 4.77):
        tri = rect(s, x + 0.3, ay, 0.26, 0.16, BLUE, MSO_SHAPE.ISOSCELES_TRIANGLE)
        tri.rotation = 180

# ========== Slide 6 - Title Only: next 90 days; timeline and team cards share ONE 4-column grid (Oct, Nov, Dec, Jan)
s = prs.slides.add_slide(layout(prs, "Title Only"))
set_title(s, "Next 90 days: convert, scale, repeat")
g6 = 0.25
c6 = (CW - 3 * g6) / 4                       # one month = one column = 2.7125in
def colx(k): return ML + k * (c6 + g6)
tl = [("Oct–Nov", NAVY, 0, 2, [[("Convert ", False), ("$235k", True), (" due to close", False)],
                                      [("ISVCO hackathon outcome → potential first ", False), ("$100k+", True), (" Agentic RAG deal", False)],
                                      [("Nov founder webinar", False)]]),
      ("Dec", BLUE, 2, 1, [[("First ", False), ("$100k+", True), (" Agentic RAG deal target (ISV or sector deal)", False)], [("SKO", False)]]),
      ("Jan", BLUE_BRIGHT, 3, 1, [[("Partner program at scale: more partners trained and delivering", False)]])]
for mon, col, k0, span, items in tl:
    x = colx(k0); w = span * c6 + (span - 1) * g6
    sh = rect(s, x, BODY_T, w, 0.62, col, MSO_SHAPE.PENTAGON); sh.adjustments[0] = 0.35
    txt(s, x + 0.3, BODY_T, w - 0.8, 0.62, [run(mon, SZ_SUB, True, WHITE)], anchor=MSO_ANCHOR.MIDDLE)
    yy = BODY_T + 0.85
    for it in items:
        nl = wrap_lines(it, SZ_BODY, w - 0.3 - 0.45)
        h_ = 0.25 * nl + 0.04
        rich(s, x + 0.3, yy, w - 0.5, h_, it, SZ_BODY, INK)
        yy += h_ + 0.12
txt(s, ML, 4.42, CW, 0.25, [run("HOW EACH TEAM PLUGS IN", SZ_CAP, True, BLUE)])
tiles = [("Sales", "Route content-heavy accounts; partners deliver"),
         ("Demand gen", "Campaigns around the research portal and gov AI deadlines"),
         ("Product marketing", "Package the three plays + case studies (e.g. a school case study, FRDC)"),
         ("Partners", "Onboarding and the developer training program")]
# One panel, four ruled rows: the roles are standing, not tied to a month, so they must not pair with a timeline column
TEAM_T, ROW_H = 4.75, 0.47
rect(s, ML, TEAM_T, CW, ROW_H * 4, PALE, MSO_SHAPE.ROUNDED_RECTANGLE, 0.04)
for k, (nm, body) in enumerate(tiles):
    yy = TEAM_T + k * ROW_H
    if k:
        rect(s, ML + 0.3, yy - 0.01, CW - 0.6, 0.02, WHITE, MSO_SHAPE.RECTANGLE)
    txt(s, ML + 0.3, yy, 2.7, ROW_H, [run(nm, SZ_SUB, True, NAVY)], anchor=MSO_ANCHOR.MIDDLE)
    txt(s, ML + 3.2, yy, CW - 3.5, ROW_H, [run(body, SZ_BODY, False, INK)], anchor=MSO_ANCHOR.MIDDLE)

prs.core_properties.title = "Agentic RAG in ANZ: building a repeatable go-to-market engine"
prs.core_properties.author = "Jay Sanderson"
prs.save(str(OUT))
from build_from_template import sanitise_package
print("sanitise:", sanitise_package(OUT, author="Jay Sanderson", slide_count=len(prs.slides)))
print("saved", OUT)
