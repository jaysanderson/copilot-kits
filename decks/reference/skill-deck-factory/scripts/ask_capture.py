"""Capture the ARAG Ask playground answering a real question with citations.

Uses the saved storage_state, types a question, waits for the generated answer
and its Sources panel to render, then screenshots.

Usage:
    python scripts/ask_capture.py <kb-base-url> "<question>" out.png [auth.json]
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright


def main():
    BASE = sys.argv[1].rstrip("/")
    question = sys.argv[2]
    out = sys.argv[3]
    AUTH = str(Path(sys.argv[4] if len(sys.argv) > 4 else "brand/arag-auth.json"))

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080}, storage_state=str(AUTH)
        )
        page = context.new_page()
        page.goto(f"{BASE}/search", wait_until="load", timeout=60000)
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass

        box = page.get_by_placeholder("Type your question here")
        box.click()
        box.fill(question)
        box.press("Enter")

        # Generation streams in; the "Ask more" control only appears once the
        # answer is fully rendered (with its Sources panel). Wait for that, and
        # also let the streaming request settle to networkidle.
        try:
            page.get_by_text("Ask more", exact=False).first.wait_for(timeout=90000)
            print("answer fully rendered")
        except Exception:
            print("WARNING: 'Ask more' end-marker not detected within timeout")
        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass
        page.wait_for_timeout(2000)

        page.screenshot(path=out, full_page=True)
        print(f"Saved {out}")
        browser.close()


if __name__ == "__main__":
    main()
