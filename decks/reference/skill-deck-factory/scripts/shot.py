"""Single-step browser helper: screenshot a URL, or dump its links.

Examples:
    python scripts/shot.py --url https://example.com --out shots/home.png --full
    python scripts/shot.py --url https://example.com --out shots/x.png --wait 2000 \
        --click "button.search"
    python scripts/shot.py --url https://example.com --links
    python scripts/shot.py --url https://example.com --out shots/x.png --auth state.json
"""
import argparse
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright


def main():
    parser = argparse.ArgumentParser(description="Browser screenshot / link helper")
    parser.add_argument("--url", required=True, help="URL to load")
    parser.add_argument("--out", help="Output PNG path (required unless --links)")
    parser.add_argument("--full", action="store_true", help="Full-page screenshot")
    parser.add_argument("--wait", type=int, default=0, help="Extra wait in ms after idle")
    parser.add_argument("--click", help="CSS selector to click before capture")
    parser.add_argument("--auth", help="Playwright storage_state JSON for auth")
    parser.add_argument(
        "--links",
        action="store_true",
        help="Print all nav/anchor links as JSON instead of screenshotting",
    )
    args = parser.parse_args()

    if not args.links and not args.out:
        parser.error("--out is required unless --links is given")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context_kwargs = {"viewport": {"width": 1920, "height": 1080}}
        if args.auth:
            context_kwargs["storage_state"] = args.auth
        context = browser.new_context(**context_kwargs)
        page = context.new_page()

        page.goto(args.url, wait_until="load", timeout=60000)
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass  # best effort; SPAs may never fully idle
        if args.wait:
            page.wait_for_timeout(args.wait)

        if args.links:
            links = page.eval_on_selector_all(
                "a[href], nav a",
                """els => els.map(a => ({
                    text: (a.innerText || a.textContent || '').trim(),
                    href: a.href
                })).filter(l => l.href)""",
            )
            # De-dupe by (text, href) while preserving order.
            seen = set()
            unique = []
            for l in links:
                key = (l["text"], l["href"])
                if key not in seen:
                    seen.add(key)
                    unique.append(l)
            print(json.dumps(unique, indent=2))
            browser.close()
            return

        if args.click:
            try:
                page.click(args.click, timeout=10000)
                try:
                    page.wait_for_load_state("networkidle", timeout=10000)
                except Exception:
                    pass
                page.wait_for_timeout(500)
            except Exception as exc:
                print(f"click failed ({args.click}): {exc}", file=sys.stderr)

        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(out_path), full_page=args.full)
        print(f"Saved {out_path}")
        browser.close()


if __name__ == "__main__":
    main()
