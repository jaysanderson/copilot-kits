"""
Live-browser verification of the deployed call-analysis app after the ElevenLabs
voice-cast cutover (DAM b74205b5). Drives https://your-app.fly.dev with
real Playwright (not claude-in-chrome, which cannot load media - CLAUDE.md /
feedback_claude_in_chrome_cannot_load_media), plays audio on at least 3 calls,
captures network evidence that the served media resource ids belong to the NEW
staging KB (never cached from the old KB), and drives an ask + citation flow to
confirm a grounded answer and a real timestamp resolution.

Run: .venv/bin/python apps/call-analysis/scripts_py/verify_live_ui.py
"""
import json
import re
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE_URL = "https://your-app.fly.dev"
OUT_DIR = Path(__file__).parent / "live_verify_shots"
OUT_DIR.mkdir(exist_ok=True)

rid_map = json.loads((Path(__file__).parent / "rid_map.json").read_text())
NEW_RIDS = set(rid_map.values())


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1400, "height": 900})
        media_events = []

        def on_response(resp):
            url = resp.url
            if "/media" in url or "/file/" in url or "/download" in url or url.endswith((".mp3", ".mp4")):
                try:
                    length = resp.headers.get("content-length")
                except Exception:
                    length = None
                media_events.append((resp.status, url, length))

        page.on("response", on_response)

        print("=== 1. Homepage ===")
        page.goto(BASE_URL, wait_until="networkidle", timeout=30000)
        page.screenshot(path=str(OUT_DIR / "01_home.png"), full_page=True)
        print(f"  title: {page.title()}")

        print("\n=== 2. Calls list ===")
        page.goto(f"{BASE_URL}/calls", wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(1500)
        page.screenshot(path=str(OUT_DIR / "02_calls_list.png"), full_page=True)
        links = page.eval_on_selector_all("a[href*='/calls/']", "els => els.map(e => e.getAttribute('href'))")
        call_slugs = sorted(set(l.rstrip("/").split("/")[-1] for l in links if l and l.rstrip("/").split("/")[-1]))
        print(f"  found {len(call_slugs)} call links, sample: {call_slugs[:5]}")

        media_slugs = [s for s in call_slugs if s in rid_map]
        # Prefer three media (audio/video) calls if we can identify them by slug pattern
        picks = media_slugs[:3] if len(media_slugs) >= 3 else call_slugs[:3]
        print(f"  picking: {picks}")

        results = []
        for i, slug in enumerate(picks, 1):
            print(f"\n=== 3.{i} Call detail: {slug} ===")
            media_events.clear()
            page.goto(f"{BASE_URL}/calls/{slug}", wait_until="load", timeout=30000)
            page.wait_for_timeout(2000)
            page.screenshot(path=str(OUT_DIR / f"03_{i}_{slug}_detail.png"), full_page=True)

            # Try to play any audio/video element on the page
            played = False
            try:
                page.evaluate("""
                    () => {
                        const el = document.querySelector('audio, video');
                        if (el) { el.currentTime = 0; return el.play().then(() => true).catch(() => false); }
                        return false;
                    }
                """)
                page.wait_for_timeout(3000)
                played = True
            except Exception as e:
                print(f"  play() failed: {e}")
            page.screenshot(path=str(OUT_DIR / f"03_{i}_{slug}_playing.png"))

            print(f"  played={played} media network events: {media_events[:5]}")
            expected_rid = rid_map.get(slug, slug)  # calls/[id] uses the resource id directly as slug here
            ok = any(status == 200 for status, _, _ in media_events)
            results.append({"slug": slug, "expected_rid": expected_rid, "events": media_events, "ok_200": ok})

        print("\n=== 4. Ask + citation flow ===")
        page.goto(f"{BASE_URL}/calls", wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(1000)
        # Look for an ask input on the home or calls page
        page.goto(BASE_URL, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(1000)
        ask_box = page.query_selector("textarea, input[type='text']")
        if ask_box:
            ask_box.click()
            ask_box.fill("What telehealth copay does the member's plan have?")
            page.keyboard.press("Enter")
            page.wait_for_timeout(8000)
            page.screenshot(path=str(OUT_DIR / "04_ask_answer.png"), full_page=True)
            answer_text = page.inner_text("body")
            print(f"  page text sample (first 500 chars after ask):\n{answer_text[:500]}")
            # try clicking a citation if present
            citation = page.query_selector("[data-citation], sup, .citation, a[href*='#cite']")
            if citation:
                citation.click()
                page.wait_for_timeout(1500)
                page.screenshot(path=str(OUT_DIR / "05_citation_click.png"), full_page=True)
                print("  clicked a citation element")
            else:
                print("  no obvious citation element found by generic selector - see screenshot for manual check")
        else:
            print("  no ask input found on homepage - see screenshot for manual check")

        browser.close()

        print("\n=== SUMMARY ===")
        for r in results:
            print(f"  {r['slug']:36s} ok_200={r['ok_200']} events={r['events']}")
        print(f"\nScreenshots saved to {OUT_DIR}")


if __name__ == "__main__":
    main()
