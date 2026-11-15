import sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8099"
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else "/tmp/oc_shots")
MOBILE = "--mobile" in sys.argv
OUT.mkdir(parents=True, exist_ok=True)

ROUTES = ["/", "/surgeon-desk", "/market-access", "/claim-check",
          "/investor-signal", "/patient-guide", "/evidence-library"]

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = (b.new_context(viewport={"width": 390, "height": 844}, is_mobile=True,
                         device_scale_factor=2, has_touch=True)
           if MOBILE else b.new_context(viewport={"width": 1440, "height": 950}))
    pg = ctx.new_page()
    errs = []
    pg.on("console", lambda m: errs.append(f"console {m.type}: {m.text}") if m.type == "error" else None)
    pg.on("pageerror", lambda e: errs.append(f"pageerror: {e}"))
    for r in ROUTES:
        pg.goto(BASE + r, wait_until="networkidle")
        time.sleep(3.5)
        name = (r.strip("/") or "home") + ("-m" if MOBILE else "")
        pg.screenshot(path=str(OUT / f"{name}.png"), full_page=False)
    # reveal modal
    pg.goto(BASE + "/surgeon-desk", wait_until="networkidle"); time.sleep(2)
    pg.click("#revealBtn"); time.sleep(2.2)
    pg.screenshot(path=str(OUT / ("reveal-m.png" if MOBILE else "reveal.png")))
    print("errors:", errs or "none")
    b.close()
print("shots ->", OUT)
