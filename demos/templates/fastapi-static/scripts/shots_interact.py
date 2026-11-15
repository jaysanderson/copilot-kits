import sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8099"
OUT = Path("/tmp/oc_shots")
MOBILE = "--mobile" in sys.argv
OUT.mkdir(parents=True, exist_ok=True)
sfx = "-m" if MOBILE else ""

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = (b.new_context(viewport={"width": 390, "height": 844}, is_mobile=True,
                         device_scale_factor=2, has_touch=True)
           if MOBILE else b.new_context(viewport={"width": 1440, "height": 1000}))
    pg = ctx.new_page()
    errs = []
    pg.on("console", lambda m: errs.append(f"console {m.type}: {m.text}") if m.type == "error" else None)
    pg.on("pageerror", lambda e: errs.append(f"pageerror: {e}"))

    def shot(n, full=False):
        pg.screenshot(path=str(OUT / f"{n}{sfx}.png"), full_page=full)

    # surgeon desk - ask the first suggested question
    pg.goto(BASE + "/surgeon-desk", wait_until="networkidle"); time.sleep(2)
    pg.click("button[data-q]"); pg.wait_for_selector(".answer-block", timeout=180000); time.sleep(1.5)
    pg.locator(".answer-block").scroll_into_view_if_needed(); time.sleep(.8)
    shot("surgeon-answer")

    # surgeon desk - the deliberate decline
    pg.goto(BASE + "/surgeon-desk", wait_until="networkidle"); time.sleep(2)
    btns = pg.locator("aside button[data-q]")
    btns.first.click(); pg.wait_for_selector(".answer-block", timeout=180000); time.sleep(1.5)
    pg.locator(".answer-block").scroll_into_view_if_needed(); time.sleep(.8)
    shot("surgeon-decline")

    # claim check
    pg.goto(BASE + "/claim-check", wait_until="networkidle"); time.sleep(2)
    pg.locator("button[data-c]").nth(1).click()
    pg.wait_for_selector(".verdict", timeout=180000); time.sleep(1.5)
    pg.locator(".verdict").scroll_into_view_if_needed(); time.sleep(.8)
    shot("claim-verdict")
    shot("claim-full", full=True)

    # investor digest
    pg.goto(BASE + "/investor-signal", wait_until="networkidle"); time.sleep(3)
    pg.locator("button[data-brief]").first.click()
    pg.wait_for_selector("#digest .answer-block", timeout=180000); time.sleep(1.5)
    pg.locator("#digest").scroll_into_view_if_needed(); time.sleep(.8)
    shot("investor-digest")

    # patient answer
    pg.goto(BASE + "/patient-guide", wait_until="networkidle"); time.sleep(2)
    pg.locator("button.jcard").first.click()
    pg.wait_for_selector(".answer-block", timeout=180000); time.sleep(1.5)
    pg.locator(".answer-block").scroll_into_view_if_needed(); time.sleep(.8)
    shot("patient-answer")

    # library search
    pg.goto(BASE + "/evidence-library", wait_until="networkidle"); time.sleep(2.5)
    pg.fill("#lq", "nerve repair surgical technique")
    pg.click("#searchBtn"); time.sleep(6)
    shot("library-search")

    # reveal modal
    pg.goto(BASE + "/market-access", wait_until="networkidle"); time.sleep(3)
    pg.click("#revealBtn"); time.sleep(2.5)
    shot("reveal")
    print("errors:", errs or "none")
    b.close()
print("done")
