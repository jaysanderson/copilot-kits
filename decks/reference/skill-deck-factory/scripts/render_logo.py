"""Render the brand SVG logo to transparent PNGs (black + white variants).

Inlines the SVG markup and sets fill via CSS so the local file loads reliably.
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

# Pass the captured SVG path as argv[1] (from brand.json "logo"); outputs to brand/.
SVG = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("brand/logo.svg")
OUT_BLACK = Path("brand/logo-black.png")
OUT_WHITE = Path("brand/logo-white.png")

WIDTH = 1400  # high-res; aspect from viewBox 540.4 x 181.4
HEIGHT = round(WIDTH * 181.4 / 540.4)
svg_markup = SVG.read_text()


def render(fill, out):
    html = f"""<!doctype html><html><head><style>
      html,body{{margin:0;padding:0;background:transparent}}
      #wrap{{width:{WIDTH}px;height:{HEIGHT}px}}
      #wrap svg{{width:100%;height:100%}}
      #wrap svg path, #wrap svg polygon, #wrap svg rect{{fill:{fill} !important}}
    </style></head><body><div id="wrap">{svg_markup}</div></body></html>"""
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        pg = b.new_context(viewport={"width": WIDTH, "height": HEIGHT}).new_page()
        pg.set_content(html, wait_until="load")
        pg.wait_for_timeout(400)
        pg.locator("#wrap").screenshot(path=str(out), omit_background=True)
        b.close()
    print(f"saved {out.name} ({WIDTH}x{HEIGHT})")


if __name__ == "__main__":
    render("#111111", OUT_BLACK)
    render("#ffffff", OUT_WHITE)
