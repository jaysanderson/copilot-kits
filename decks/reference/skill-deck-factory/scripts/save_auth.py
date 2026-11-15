"""Capture an authenticated Playwright storage_state for the ARAG dashboard.

Launches a HEADED browser, waits for you to log in manually (auto-detecting the
loaded dashboard, or press Enter in the terminal to save immediately), then
writes the session to brand/arag-auth.json.

Usage:
    python scripts/save_auth.py <dashboard-url> [output.json]
"""
import sys
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

LOGIN_URL = sys.argv[1] if len(sys.argv) > 1 else ""
AUTH_PATH = Path(sys.argv[2] if len(sys.argv) > 2 else "brand/arag-auth.json")


def wait_for_enter(flag):
    """Block on stdin; set the flag once the user presses Enter.

    If there's no interactive terminal (EOF), just exit quietly and let the
    dashboard auto-detection drive the save — do NOT trip the stop flag, or
    we'd save an unauthenticated session immediately.
    """
    try:
        input()
    except EOFError:
        return
    flag["stop"] = True


def dashboard_ready(page):
    """Heuristic: we're past the login screen and on the app itself."""
    url = page.url
    # Still sitting on an auth/login/SSO page -> not ready yet.
    if any(k in url.lower() for k in ("login", "signin", "sign-in", "auth", "sso")):
        return False
    # Back on the target app host with real content rendered.
    if "rag.progress.cloud" not in url:
        return False
    # A logged-in SPA has no visible password field; the "Resources list" nav
    # item only renders inside the authenticated Knowledge Box UI.
    try:
        if page.locator("input[type='password']").count() > 0:
            return False
        if page.get_by_text("Resources list", exact=False).count() > 0:
            return True
        body_text = page.inner_text("body", timeout=2000)
    except Exception:
        return False
    return len(body_text.strip()) > 400


def main():
    if not LOGIN_URL:
        print("Usage: python save_auth.py <dashboard-url> [output.json]",
              file=sys.stderr)
        sys.exit(1)
    AUTH_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()
        page.goto(LOGIN_URL, wait_until="load", timeout=60000)

        print("=" * 70)
        print("A headed Chromium window is open. Log in manually.")
        print("I'll auto-detect the dashboard once it loads,")
        print("or press Enter here to save the session immediately.")
        print("=" * 70)
        sys.stdout.flush()

        flag = {"stop": False}
        listener = threading.Thread(target=wait_for_enter, args=(flag,), daemon=True)
        listener.start()

        stable = 0  # require a couple consecutive "ready" polls to avoid races
        while not flag["stop"]:
            try:
                if dashboard_ready(page):
                    stable += 1
                    if stable >= 2:
                        print("Dashboard detected — saving session.")
                        break
                else:
                    stable = 0
            except Exception:
                stable = 0
            page.wait_for_timeout(1000)

        context.storage_state(path=str(AUTH_PATH))
        print(f"Saved storage_state to {AUTH_PATH}")
        browser.close()


if __name__ == "__main__":
    main()
