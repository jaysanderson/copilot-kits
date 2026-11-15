#!/usr/bin/env python3
"""Convert an enablement markdown file to a clean .docx.

Minimal, dependency-light markdown -> docx renderer purpose-built for this
factory's enablement docs: headings (#/##/###), bold (**), pipe tables,
bullet lists, horizontal rules, and plain paragraphs. Not a general markdown
engine - just enough to render these three documents faithfully.
"""
import re
import sys
from pathlib import Path

from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH


def add_runs_with_bold(paragraph, text):
    """Split text on **bold** and *italic* markers and add runs accordingly.

    Italic support added 5 Oct 2026 after a delivered .docx rendered every
    *emphasised* event name as literal asterisks, in the one section the
    document told the reader to read first. Bold had always worked, which is
    why the gap survived: a renderer that handles the common marker looks
    correct until a document uses the other one.

    The italic pattern deliberately requires the opening asterisk to be
    preceded by a non-word character (or start of string) and the closing one
    to be followed by a non-word character (or end), so a stray asterisk in
    prose, a footnote marker, or a multiplication sign is left alone rather
    than swallowed along with everything up to the next asterisk. Bold is
    split first so the two markers cannot interfere.
    """
    def emit_code(fragment, bold=False, italic=False):
        """Innermost level: split on inline `code` and emit runs, carrying any
        bold or italic the outer levels established. Code is handled last and
        unconditionally, so a filename inside an italic sentence still renders
        as code rather than arriving with literal backticks - which is exactly
        how the first version of this leaked one through."""
        for frag in re.split(r"(`[^`\n]+`)", fragment):
            if not frag:
                continue
            is_code = len(frag) > 2 and frag.startswith("`") and frag.endswith("`")
            run = paragraph.add_run(frag[1:-1] if is_code else frag)
            run.bold = bold
            run.italic = italic
            if is_code:
                run.font.name = "Consolas"

    for part in re.split(r"(\*\*[^*]+\*\*)", text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            emit_code(part[2:-2], bold=True)
            continue
        for sub in re.split(r"((?<![\w*])\*(?!\s)[^*]*[^\s*]\*(?![\w*]))", part):
            if not sub:
                continue
            if len(sub) > 2 and sub.startswith("*") and sub.endswith("*"):
                emit_code(sub[1:-1], italic=True)
            else:
                emit_code(sub)


def _is_block_start(stripped_line: str) -> bool:
    """True if this line starts a new markdown block (so paragraph-joining stops)."""
    if stripped_line.startswith("#"):
        return True
    if stripped_line == "---":
        return True
    if stripped_line.startswith("|"):
        return True
    if re.match(r"^[-*]\s+", stripped_line):
        return True
    if re.match(r"^\d+\.\s+", stripped_line):
        return True
    return False


def parse_table(lines, start_idx):
    """Parse a pipe-table starting at lines[start_idx]. Returns (rows, next_idx)."""
    rows = []
    i = start_idx
    while i < len(lines) and lines[i].strip().startswith("|"):
        line = lines[i].strip()
        if re.match(r"^\|[\s:|-]+\|$", line):
            i += 1
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        rows.append(cells)
        i += 1
    return rows, i


def build_docx(md_path: Path, docx_path: Path, title: str):
    text = md_path.read_text()
    lines = text.split("\n")

    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(10.5)

    for section in doc.sections:
        section.left_margin = Inches(0.9)
        section.right_margin = Inches(0.9)
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)

    i = 0
    first_h1_done = False
    in_list = False
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped == "":
            i += 1
            continue

        if stripped.startswith("```"):
            # fenced code block / ASCII diagram - render verbatim in monospace,
            # one paragraph per line so leading spaces survive.
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_p = doc.add_paragraph()
                code_p.paragraph_format.space_after = Pt(0)
                run = code_p.add_run(lines[i] if lines[i] else " ")
                run.font.name = "Consolas"
                run.font.size = Pt(9)
                i += 1
            i += 1  # skip closing fence
            doc.add_paragraph()
            continue

        if stripped == "---":
            doc.add_paragraph("_" * 60).alignment = WD_ALIGN_PARAGRAPH.CENTER
            i += 1
            continue

        if stripped.startswith("#"):
            level = len(stripped) - len(stripped.lstrip("#"))
            heading_text = stripped.lstrip("#").strip()
            if level == 1:
                h = doc.add_heading(level=0)
                add_runs_with_bold(h, heading_text)
                first_h1_done = True
            elif level == 2:
                h = doc.add_heading(level=1)
                add_runs_with_bold(h, heading_text)
            elif level == 3:
                h = doc.add_heading(level=2)
                add_runs_with_bold(h, heading_text)
            else:
                h = doc.add_heading(level=3)
                add_runs_with_bold(h, heading_text)
            i += 1
            continue

        if stripped.startswith("|"):
            rows, i = parse_table(lines, i)
            if rows:
                ncols = len(rows[0])
                table = doc.add_table(rows=0, cols=ncols)
                table.style = "Light Grid Accent 1"
                for r_idx, row in enumerate(rows):
                    cells = table.add_row().cells
                    for c_idx in range(ncols):
                        text_cell = row[c_idx] if c_idx < len(row) else ""
                        cell_para = cells[c_idx].paragraphs[0]
                        add_runs_with_bold(cell_para, text_cell)
                        if r_idx == 0:
                            for run in cell_para.runs:
                                run.bold = True
                doc.add_paragraph()
            continue

        if re.match(r"^[-*]\s+", stripped):
            item_text = re.sub(r"^[-*]\s+", "", stripped)
            j = i + 1
            while j < len(lines) and lines[j].strip() and not _is_block_start(lines[j].strip()):
                item_text += " " + lines[j].strip()
                j += 1
            p = doc.add_paragraph(style="List Bullet")
            add_runs_with_bold(p, item_text)
            i = j
            continue

        num_match = re.match(r"^(\d+)\.\s+", stripped)
        if num_match:
            item_text = stripped[num_match.end():]
            # join wrapped continuation lines (blank line or new block ends it)
            j = i + 1
            while j < len(lines) and lines[j].strip() and not _is_block_start(lines[j].strip()):
                item_text += " " + lines[j].strip()
                j += 1
            # Keep the markdown's own literal number rather than Word's "List Number"
            # style: that style continues its counter across every list in the document,
            # so a later section's "1." silently renders as "6." and breaks in-text
            # references to numbered items. The source number is the truth.
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.25)
            p.add_run(f"{num_match.group(1)}. ")
            add_runs_with_bold(p, item_text)
            i = j
            continue

        # plain paragraph - join wrapped continuation lines until blank/new block
        para_text = stripped
        j = i + 1
        while j < len(lines) and lines[j].strip() and not _is_block_start(lines[j].strip()):
            para_text += " " + lines[j].strip()
            j += 1
        p = doc.add_paragraph()
        add_runs_with_bold(p, para_text)
        i = j

    doc.core_properties.title = title
    docx_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(docx_path))
    print(f"Wrote {docx_path}")


if __name__ == "__main__":
    base = Path("/Users/user/Claude/ARAG-PMK-1/content/enablement")
    jobs = [
        ("discovery-qualification-framework.md", "discovery-qualification-framework.docx",
         "ARAG Discovery & Qualification Framework"),
        ("roi-value-model.md", "roi-value-model.docx", "ARAG ROI & Value Model"),
        ("objection-handling-guide.md", "objection-handling-guide.docx",
         "ARAG Objection-Handling Guide"),
        ("pov-playbook.md", "pov-playbook.docx",
         "ARAG Proof-of-Value Playbook"),
        ("expansion-playbook.md", "expansion-playbook.docx",
         "ARAG Expansion Playbook"),
        ("arag-in-agent-stack.md", "arag-in-agent-stack.docx",
         "ARAG as a Component in an Enterprise Agent Stack"),
    ]
    for md_name, docx_name, title in jobs:
        build_docx(base / md_name, base / docx_name, title)
