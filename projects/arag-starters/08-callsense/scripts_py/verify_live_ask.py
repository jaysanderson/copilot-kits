"""
Drive the live "Ask this call" panel on a real call detail page, confirm a
grounded cited answer renders, and click a citation to confirm it resolves to
a real timestamp in the new ElevenLabs audio.

Run: .venv/bin/python apps/call-analysis/scripts_py/verify_live_ask.py
"""
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_URL = "https://your-app.fly.dev"
OUT_DIR = Path(__file__).parent / "live_verify_shots"
OUT_DIR.mkdir(exist_ok=True)

SLUG = "062c84882e60444da88d7f975207bd7a"  # call-enrollment-newborn-0005


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1400, "height": 1000})
        page.goto(f"{BASE_URL}/calls/{SLUG}", wait_until="load", timeout=30000)
        page.wait_for_timeout(1500)

        print("Clicking suggested question chip: 'Summarize this call'")
        page.click("text=Summarize this call")
        page.wait_for_timeout(9000)
        page.screenshot(path=str(OUT_DIR / "06_ask_answer.png"), full_page=True)

        body_text = page.inner_text("body")
        # crude slice around "Ask this call" panel content
        idx = body_text.find("Summarize this call")
        print("Page text near Ask panel after asking:\n", body_text[idx: idx + 1200])

        # try to find and click a citation marker
        page.wait_for_timeout(1000)
        candidates = page.query_selector_all("sup, [class*='citation'], [class*='cite'], button:has-text('0:')")
        print(f"\nFound {len(candidates)} possible citation elements")
        if candidates:
            candidates[0].scroll_into_view_if_needed()
            page.screenshot(path=str(OUT_DIR / "07_before_citation_click.png"), full_page=True)
            candidates[0].click()
            page.wait_for_timeout(1500)
            page.screenshot(path=str(OUT_DIR / "08_after_citation_click.png"), full_page=True)
            # check video currentTime jumped to a real timestamp
            current_time = page.evaluate("() => { const v = document.querySelector('video, audio'); return v ? v.currentTime : null; }")
            print(f"media currentTime after citation click: {current_time}")

        browser.close()


if __name__ == "__main__":
    main()
