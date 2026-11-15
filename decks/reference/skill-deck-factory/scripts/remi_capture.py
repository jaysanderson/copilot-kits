"""Capture the REMi RAG-evaluation page with the period set to its max range.

Usage:
    python scripts/remi_capture.py <remi_url> shots/backend-raw-remi.png
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright


def main():
    url = sys.argv[1]
    out = sys.argv[2]
    AUTH = Path(sys.argv[3] if len(sys.argv) > 3 else "brand/arag-auth.json")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080}, storage_state=str(AUTH)
        )
        page = context.new_page()
        page.goto(url, wait_until="load", timeout=60000)
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass
        page.wait_for_timeout(2000)

        # Open the period dropdown and pick the widest range available.
        try:
            page.get_by_text("last 7 days", exact=False).first.click()
            page.wait_for_timeout(500)
            page.get_by_text("last 30 days", exact=False).first.click()
            print("period set to last 30 days")
            page.wait_for_timeout(4000)
        except Exception as exc:
            print(f"period-change issue: {exc}")

        page.screenshot(path=out, full_page=True)
        print(f"Saved {out}")
        browser.close()


if __name__ == "__main__":
    main()
