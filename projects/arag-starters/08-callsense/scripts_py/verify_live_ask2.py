from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_URL = "https://your-app.fly.dev"
OUT_DIR = Path(__file__).parent / "live_verify_shots"
SLUG = "062c84882e60444da88d7f975207bd7a"

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1400, "height": 1000})
    page.goto(f"{BASE_URL}/calls/{SLUG}", wait_until="load", timeout=30000)
    page.wait_for_timeout(1500)
    page.click("text=Summarize this call")
    page.wait_for_timeout(9000)

    # click the "..." expander next to the ask input (likely REMi/quality/citations detail)
    more_btn = page.query_selector("button:has-text('...')")
    if more_btn:
        more_btn.click()
        page.wait_for_timeout(1000)
        page.screenshot(path=str(OUT_DIR / "09_after_more_click.png"), full_page=True)
        print("clicked '...' expander, screenshot saved")
    else:
        print("no '...' button found")

    # click a transcript timestamp to test seek-on-citation behaviour
    ts = page.query_selector("text=0:16")
    if ts:
        ts.click()
        page.wait_for_timeout(1000)
        cur = page.evaluate("() => { const v = document.querySelector('video, audio'); return v ? v.currentTime : null; }")
        print(f"after clicking transcript timestamp 0:16, media currentTime = {cur}")
        page.screenshot(path=str(OUT_DIR / "10_after_timestamp_click.png"), full_page=True)
    else:
        print("no 0:16 timestamp element found")

    browser.close()
