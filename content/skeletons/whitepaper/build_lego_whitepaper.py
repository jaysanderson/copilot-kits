#!/usr/bin/env python3
"""Build the 'box of bricks for builders' Agentic RAG whitepaper.

Reads the template HTML, embeds every asset (logo, hex loop, screenshots) as a
base64 data URI so the file is fully self-contained, writes the final HTML, then
renders it to PDF with Playwright (print CSS, A4, backgrounds on).
"""
import base64, mimetypes, pathlib
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path("/Users/user/Claude/ARAG-PMK-1")
HERE = ROOT / "content/whitepapers"
TEMPLATE = HERE / "lego-set-for-builders.template.html"
OUT_HTML = HERE / "progress-agentic-rag-box-of-bricks.html"
OUT_PDF  = HERE / "progress-agentic-rag-box-of-bricks.pdf"

BRAND = ROOT / ".claude/skills/progress-arag-branding/assets"
SHOTS = ROOT / "shots/steal-our-ideas"
# Whitepaper-local crops. SHOT_GROUNDED and SHOT_OPS are re-cropped from the pristine
# presentation-library sources into content/whitepapers/assets/ so the whitepaper never
# mutates the shared shots/steal-our-ideas/ campaign library. SHOT_GROUNDED drops the
# 0-100 score row (those are REMi's three metric names, and REMi's real scale is 0-5 -
# see the trust page); SHOT_OPS is a legible headline+KPI+table band.
WPA = HERE / "assets"

ASSETS = {
    "HEXLOOP":       BRAND / "hex-loop/hex-loop-rgb.svg",
    "LOGO_DARK":     BRAND / "logos/primary-horizontal-alternate.svg",
    "SHOT_GROUNDED": WPA / "wp-grounded-answer.png",
    "SHOT_TRACE":    SHOTS / "agent-tool-trace__software.png",
    "SHOT_TRIAGE":   SHOTS / "document-triage-pipeline__insurance.png",
    "SHOT_GRAPH":    SHOTS / "knowledge-graph__supply-chain.png",
    "SHOT_ANALYTICS":SHOTS / "analytics-dashboard__contact-center-insurance.png",
    "SHOT_OPS":      WPA / "wp-ops-live.png",
}

def data_uri(p: pathlib.Path) -> str:
    mime = "image/svg+xml" if p.suffix == ".svg" else (mimetypes.guess_type(str(p))[0] or "application/octet-stream")
    b64 = base64.b64encode(p.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{b64}"

html = TEMPLATE.read_text()
for token, path in ASSETS.items():
    assert path.exists(), f"missing asset: {path}"
    html = html.replace("{{" + token + "}}", data_uri(path))

# fail loudly if any token was left unfilled
assert "{{" not in html, "unfilled template token remains"
OUT_HTML.write_text(html)
print(f"wrote {OUT_HTML}  ({len(html)//1024} KB)")

with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page()
    page.goto(OUT_HTML.as_uri(), wait_until="networkidle")
    page.emulate_media(media="print")
    page.pdf(path=str(OUT_PDF), prefer_css_page_size=True, print_background=True)
    b.close()
print(f"wrote {OUT_PDF}  ({OUT_PDF.stat().st_size//1024} KB)")
