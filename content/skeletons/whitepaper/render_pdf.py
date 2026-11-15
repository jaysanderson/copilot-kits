#!/usr/bin/env python
"""Render the grants report to A4 PDF.

Two-pass render: (1) full-bleed pass for the cover page (margin 0), (2) body pass
with running footer (page numbers) and a bottom margin, then merge cover + body.
Usage: .venv/bin/python content/grants/render_pdf.py <in.html> <out.pdf>
"""
import sys
import subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright
from pypdf import PdfReader, PdfWriter

FOOTER = """
<div style="width:100%; font-size:7pt; font-family:Arial, sans-serif; color:#3D3D42;
            padding:0 16mm; display:flex; justify-content:space-between;">
  <span>Australian AI grant intelligence and target-account strategy - Progress Agentic RAG</span>
  <span>Verified 3 September 2026 &nbsp;-&nbsp; Page <span class="pageNumber"></span> of <span class="totalPages"></span></span>
</div>"""

def main():
    src = Path(sys.argv[1]).resolve()
    out = Path(sys.argv[2]).resolve()
    cover_pdf = out.with_suffix(".cover.pdf")
    body_pdf = out.with_suffix(".body.pdf")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(src.as_uri())
        page.wait_for_load_state("networkidle")
        page.emulate_media(media="print")
        # Pass 1: cover, full bleed
        page.pdf(path=str(cover_pdf), format="A4", print_background=True,
                 margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
                 page_ranges="1")
        # Pass 2: whole doc with running footer; we discard its page 1
        page.pdf(path=str(body_pdf), format="A4", print_background=True,
                 display_header_footer=True,
                 header_template="<span></span>", footer_template=FOOTER,
                 margin={"top": "0", "bottom": "14mm", "left": "0", "right": "0"})
        browser.close()

    writer = PdfWriter()
    writer.append(str(cover_pdf))
    body = PdfReader(str(body_pdf))
    for i in range(1, len(body.pages)):
        writer.add_page(body.pages[i])
    with open(out, "wb") as f:
        writer.write(f)
    cover_pdf.unlink(); body_pdf.unlink()
    print(f"PDF written: {out} ({out.stat().st_size} bytes)")
    info = subprocess.run(["pdfinfo", str(out)], capture_output=True, text=True)
    for line in info.stdout.splitlines():
        if line.startswith("Pages:"):
            print(line)

if __name__ == "__main__":
    main()
