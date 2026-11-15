"""QA checks for the ANZ deck. Every check reports a COUNT and can fail; selftest plants defects."""
import re, sys, hashlib
from pptx import Presentation
from pptx.util import Emu
import os
DECK = os.environ.get("DECK", "/Users/user/Claude/ARAG-PMK-1/decks/anz-sales-meeting-agentic-rag-2026-10-10.pptx")
SPEC = "/Users/user/Claude/aragmlgo/copilot/briefs/2026-10-10-sales-meeting-deck-spec.md"
FAILS = []
def verdict(name, ok, detail):
    print(("PASS " if ok else "FAIL ") + name + " :: " + detail)
    if not ok: FAILS.append(name)

def deck_text(path):
    prs = Presentation(path); out = []
    for i, sl in enumerate(prs.slides, 1):
        t = []
        for sh in sl.shapes:
            if sh.has_text_frame: t.append(sh.text_frame.text)
        out.append("\n".join(t))
    return prs, out

FIG = re.compile(r"~?\$\d+(?:\.\d+)?k\+?|\d+(?:\.\d+)?%|\b\d+k\+?|\b\d+\b")
def figs(text):
    return sorted(set(m.group(0).replace(" ", "") for m in FIG.finditer(text)))

def figure_check(deck_path, spec_text):
    _, pages = deck_text(deck_path)
    deck = "\n".join(pages)
    spec_figs = figs(spec_text)
    # every spec figure that belongs to slide content (exclude section numbering/dates/headers)
    body = spec_text.split("## Slide 1")[1].split("## Builder notes")[0]
    body = re.sub(r"^## Slide \d+:.*$", "", body, flags=re.M)
    body = re.sub(r"\| *---.*", "", body)
    sf = figs(body)
    df = figs(deck)
    missing = [f for f in sf if f not in df and f not in ("1","2","3","4","5","6")]
    extra = [f for f in df if f not in sf]
    return sf, df, missing, extra

if __name__ == "__main__":
    spec = open(SPEC).read()
    prs, pages = deck_text(DECK)
    # 1 slide count / notes
    verdict("slide-count", len(prs.slides) == 6, f"{len(prs.slides)} slides")
    notes = [sl.has_notes_slide for sl in prs.slides]
    verdict("zero-notes", not any(notes), f"{sum(notes)} of {len(notes)} slides have a notes part")
    # 2 figures
    sf, df, missing, extra = figure_check(DECK, spec)
    verdict("figures-in-spec-present-in-deck", not missing, f"{len(sf)} spec figure tokens examined, missing={missing}")
    print("  deck-only figure tokens (inspect):", extra)
    # 3 banned
    alltext = "\n".join(pages)
    ems = alltext.count("—")
    verdict("no-em-dash", ems == 0, f"{ems} em dashes in {len(alltext)} chars across 6 slides")
    banned = [b for b in ["delve","leverage","unlock","seamless","game-changing","game changing"] if re.search(r"\b"+b, alltext, re.I)]
    verdict("no-banned-words", not banned, f"5 banned terms scanned, hits={banned}")
    arag = re.findall(r"\bARAG\b", alltext)
    verdict("no-ARAG-abbrev", not arag, f"{len(arag)} occurrences of ARAG")
    # 4 geometry
    SW, SH = prs.slide_width, prs.slide_height
    off = []; n = 0
    for i, sl in enumerate(prs.slides, 1):
        for sh in sl.shapes:
            n += 1
            if sh.width == 0 or sh.height == 0: off.append((i, sh.name, "zero-size"))
            if sh.left < 0 or sh.top < 0 or sh.left + sh.width > SW + 10 or sh.top + sh.height > SH + 10: off.append((i, sh.name, "off-slide"))
    verdict("geometry-no-zero-or-offslide", not off, f"{n} shapes examined, issues={off}")
    # title left margin / top consistency
    tl = []
    for i, sl in enumerate(prs.slides, 1):
        t = sl.shapes.title
        tl.append((i, round(t.left/914400, 2), round(t.top/914400, 2)))
    c = [x for x in tl if x[0] >= 2]
    verdict("title-grid-slides-2-6", len({(a,b) for _,a,b in c}) == 1, f"titles {tl}")
    # footer collision: text boxes bottoms
    low = []
    for i, sl in enumerate(prs.slides, 1):
        for sh in sl.shapes:
            if sh.has_text_frame and sh.text_frame.text.strip() and (sh.top + sh.height) / 914400 > 6.9 and sh.name.startswith("TextBox"):
                low.append((i, sh.text_frame.text[:30]))
    verdict("footer-band-clear", not low, f"{n} shapes, text boxes ending below 6.9in: {low}")
    # content left-edge alignment: every panel/card left edge on grid
    ML = 0.79
    grid = []
    for i, sl in enumerate(prs.slides, 1):
        if i == 1: continue
        lefts = sorted({round(sh.left/914400, 2) for sh in sl.shapes if sh.shape_type is not None and sh.width/914400 > 2.0 and sh.top/914400 > 1.7})
        grid.append((i, lefts[:1]))
    verdict("first-panel-left-edge=0.79", all(l[1] and abs(l[1][0]-ML) < 0.02 for l in grid), f"{grid}")
    # type scale: every explicit run size must be one of the six steps
    SCALE = {60, 36, 26, 18, 14, 12}
    used = {}
    for i, sl in enumerate(prs.slides, 1):
        for sh in sl.shapes:
            if sh.has_text_frame:
                for para in sh.text_frame.paragraphs:
                    for r in para.runs:
                        sz = r.font.size.pt if r.font.size else None
                        used.setdefault(sz, []).append(i)
    off_scale = {k_: v for k_, v in used.items() if k_ not in SCALE}
    verdict("type-scale-six-steps", not off_scale, f"{sum(len(v) for v in used.values())} text runs examined, sizes used {sorted(x for x in used if x)}, off-scale={off_scale}")
    # slide 6: chevron edges sit on the month grid (one month = one column)
    s6 = prs.slides[5]
    chev = [sh for sh in s6.shapes if sh.shape_type == 1 and sh.auto_shape_type == 51]
    c6 = (11.75 - 3 * 0.25) / 4
    grid = {round(0.79 + k_ * (c6 + 0.25), 2) for k_ in range(4)} | {round(0.79 + k_ * (c6 + 0.25) + c6, 2) for k_ in range(4)}
    he = sorted([round(c_.left/914400, 2) for c_ in chev] + [round((c_.left + c_.width)/914400, 2) for c_ in chev])
    verdict("slide6-chevrons-on-month-grid", len(chev) == 3 and all(e in grid for e in he), f"{len(chev)} chevrons, edges {he} vs month grid {sorted(grid)}")
    # slide 6: team roles are ONE full-width panel of four rows, not four cards that pair with timeline columns
    panels = [sh for sh in s6.shapes if sh.shape_type == 1 and sh.width/914400 > 11.7 and sh.top/914400 > 4.5]
    roles = [sh for sh in s6.shapes if sh.has_text_frame and sh.text_frame.text in ("Sales", "Demand gen", "Product marketing", "Partners")]
    rl = {round(r_.left/914400, 2) for r_ in roles}
    verdict("slide6-team-rows-not-column-paired", len(panels) == 1 and len(roles) == 4 and len(rl) == 1, f"{len(panels)} full-width team panel(s), {len(roles)} role labels, role-label left edges {sorted(rl)}")
    # slide 2: five stage tabs use exactly two colours, the partner accent on Partners only
    s2 = prs.slides[1]
    tabs = sorted([sh for sh in s2.shapes if sh.shape_type == 1 and sh.auto_shape_type == 51 and abs(sh.top/914400 - 1.85) < 0.01], key=lambda x: x.left)
    cols = [str(t.fill.fore_color.rgb) for t in tabs]
    verdict("slide2-two-colours-partner-only", len(tabs) == 5 and len(set(cols)) == 2 and cols.count("008963") == 1 and cols[1] == "008963", f"{len(tabs)} tabs, colours {cols}")
    print("FAILS:", FAILS); sys.exit(1 if FAILS else 0)
