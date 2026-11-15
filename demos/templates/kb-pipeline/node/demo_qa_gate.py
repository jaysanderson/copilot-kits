"""Independent functional QA gate for demo apps — module 4.5 (flagship rebuild).

Ported into the template itself (previously only lived at the outer factory's
own scripts/, so a generated demo's own repo carried no copy of its own gate -
module 4.5's whole point is wiring this INTO the scaffold/deploy loop, not
leaving it a manual step run from a different repo). scripts/deploy.sh (this
same directory) runs this automatically after every `flyctl deploy`.

Why this exists: builders self-certifying their own demo against the
DEFINITION-OF-PASS checklist misses real runtime defects - a route that 500s,
a console error, a raw error page, a leaked secret/region string, unrendered
markdown - because the person grading the work already believes it works.
This script actually drives a live demo in a real browser and reports what it
finds, independent of what the builder claims.

Usage:
    python scripts/demo_qa_gate.py --url https://slug.fly.dev --routes / /submit
    python scripts/demo_qa_gate.py --url https://slug.fly.dev --config demo.config.json
    python scripts/demo_qa_gate.py --app-dir . --config demo.config.json --interactions qa_flow.json
        # --app-dir resolves the live URL from fly.toml's `app =` field (fix 13,
        # Section 3.B) instead of guessing from the folder name - a real
        # incident: revolution-dms's actual app is "revolution-ignition-dms",
        # and a folder-name guess declared it "down" while it was live.

`--interactions <path>` (optional, per-app): a JSON list of simple steps run on the FIRST
route after it loads, to exercise one real end-to-end flow (e.g. upload a file, click
"Run", wait for a result) rather than only checking that pages load. Each step is one of:
    {"click": "<css selector>"}
    {"fill": "<css selector>", "value": "<text>"}
    {"set_input_files": "<css selector>", "path": "<file path, relative to the JSON file>"}
    {"wait_for_selector": "<css selector>", "timeout_ms": 20000}
    {"wait_ms": 2000}
Steps are best-effort: a failed step is recorded as a finding, not a crash.
"""
import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent

# Same leak patterns proven across real builds (CLAUDE.md / feedback memories) -
# every future demo gets the identical, already-proven check rather than each
# build reinventing its own grep.
SECRET_REGION_PATTERNS = [
    r"ARAG_[A-Z_]+",
    r"aws-[a-z]+-[a-z]+-\d",
    r"rag\.progress\.cloud",
    r"eyJhbGci",                 # JWT header fragment
    r"x-nuclia",
    r"nua[_-]?key",
    r"knowledge box",
    r"/ask\b",
    r"/find\b",
    r"/graph\b",
    # Compliance-co rework, 17 Aug 2026 (GM flagship-bar pass): this app exposes
    # its own /mcp server as ARAG's Retrieval Agent tool source (rao-workflow
    # pattern). The endpoint name is fine INSIDE the opt-in "How this works"
    # reveal (gate 11's designated place - the modal only mounts to the DOM
    # when opened, via createPortal, so a route-load check never sees it) but
    # must never leak into the default customer-facing view.
    r"/mcp\b",
    r"\bnuclia\b",
    # Module 4.5's two additions (Section 3, fixes 9-10): the OLD, renamed
    # capability strings, so a future rename doesn't silently drop coverage -
    # a demo showing these literally means it's still running the pre-fix
    # copy (the citation-count REMi proxy, or the ambiguous MCP naming).
    r"citation-count",
    r"mcp endpoint explorer",
]
SECRET_REGION_RE = re.compile("|".join(SECRET_REGION_PATTERNS), re.IGNORECASE)

# Gate 8's specific named defect: literal markdown syntax rendered as text instead of
# through a markdown component (real defect: literal "**Unit 14**" shown on screen).
RAW_MARKDOWN_RE = re.compile(r"\*\*[^*\n]{2,80}\*\*|^#{1,6}\s+\S|\[[^\]]+\]\([^)]+\)")

# GM correction, 17 Aug 2026 - real incident: an independent QA pass found em
# dashes shipped on all 6 routes of a demo, and this gate passed it anyway -
# it only ever checked for leaked secrets/region strings and raw markdown,
# never CLAUDE.md hard rule 2 (AU English, spaced hyphen only; banned words:
# delve, leverage, unlock, seamless, game-changing). Scanning for these here
# makes the whole class self-catching for every future build instead of
# relying on a human/QA reviewer to spot it by eye.
EM_EN_DASH_RE = re.compile(r"[–—]")  # en dash "–" / em dash "—"
BANNED_WORDS = ["delve", "leverage", "unlock", "seamless", "game-changing"]
BANNED_WORDS_RE = re.compile(r"\b(" + "|".join(re.escape(w) for w in BANNED_WORDS) + r")\b", re.IGNORECASE)

IGNORABLE_404_SUFFIXES = (".ico", ".map")


def resolve_url_from_fly_toml(app_dir: Path) -> str:
    """Fix 13 (Section 3.B): read fly.toml's `app =` field, never guess the
    hostname from the folder name - a real incident, revolution-dms's actual
    app is "revolution-ignition-dms", not the folder name "revolution-dms"."""
    for candidate in (app_dir / "fly.toml", app_dir / "portal" / "fly.toml"):
        if not candidate.exists():
            continue
        m = re.search(r'^\s*app\s*=\s*"([^"]+)"', candidate.read_text(), re.MULTILINE)
        if m:
            return f"https://{m.group(1)}.fly.dev"
    raise SystemExit(
        f"Could not resolve a live URL: no fly.toml with an `app =` field found under {app_dir} "
        f"(checked {app_dir / 'fly.toml'} and {app_dir / 'portal' / 'fly.toml'}). Pass --url explicitly."
    )


def discover_routes(args):
    if args.routes:
        return list(args.routes)
    if args.config:
        cfg = json.loads(Path(args.config).read_text())
        routes = [s["route"] for s in cfg.get("surfaces", []) if s.get("enabled", True)]
        if routes:
            return routes
    return ["/"]


def check_route(page, base_url, route, findings):
    url = urljoin(base_url, route)
    console_errors, page_errors, bad_responses = [], [], []

    def on_console(msg):
        if msg.type == "error":
            console_errors.append(msg.text)

    def on_pageerror(exc):
        page_errors.append(str(exc))

    def on_response(resp):
        if resp.status >= 400 and not resp.url.endswith(IGNORABLE_404_SUFFIXES):
            bad_responses.append(f"{resp.status} {resp.url}")

    page.on("console", on_console)
    page.on("pageerror", on_pageerror)
    page.on("response", on_response)

    ok, main_status = True, None
    try:
        resp = page.goto(url, wait_until="load", timeout=30000)
        main_status = resp.status if resp else None
        page.wait_for_timeout(1500)  # let async data-fetch renders settle
    except Exception as exc:  # noqa: BLE001 - report, don't crash the whole gate
        ok = False
        findings.append({"route": route, "severity": "FAIL",
                          "issue": f"page.goto failed: {exc}"})

    page.remove_listener("console", on_console)
    page.remove_listener("pageerror", on_pageerror)
    page.remove_listener("response", on_response)

    if main_status is not None and main_status >= 400:
        ok = False
        findings.append({"route": route, "severity": "FAIL",
                          "issue": f"main document returned HTTP {main_status}"})
    for err in console_errors:
        ok = False
        findings.append({"route": route, "severity": "FAIL", "issue": f"console error: {err}"})
    for err in page_errors:
        ok = False
        findings.append({"route": route, "severity": "FAIL", "issue": f"page error: {err}"})
    for br in bad_responses:
        ok = False
        findings.append({"route": route, "severity": "FAIL", "issue": f"network error: {br}"})

    body_text = page.content()
    leak = SECRET_REGION_RE.search(body_text)
    if leak:
        ok = False
        findings.append({"route": route, "severity": "FAIL",
                          "issue": f"secret/region/endpoint-name string leaked in page: "
                                   f"matched {leak.group(0)!r}"})

    visible_text = page.inner_text("body") if page.query_selector("body") else ""
    md_leak = RAW_MARKDOWN_RE.search(visible_text)
    if md_leak:
        ok = False
        findings.append({"route": route, "severity": "FAIL",
                          "issue": f"raw markdown syntax visible on screen (not rendered "
                                   f"through a markdown component): {md_leak.group(0)!r}"})

    dash_leak = EM_EN_DASH_RE.search(visible_text)
    if dash_leak:
        ok = False
        start = max(0, dash_leak.start() - 30)
        context = visible_text[start:dash_leak.start() + 30].replace("\n", " ")
        findings.append({"route": route, "severity": "FAIL",
                          "issue": f"em/en dash character in rendered text (hard rule 2 - AU "
                                   f"English, spaced hyphen only): {dash_leak.group(0)!r} near "
                                   f"\"...{context}...\""})

    banned_hits = sorted({m.group(0).lower() for m in BANNED_WORDS_RE.finditer(visible_text)})
    if banned_hits:
        ok = False
        findings.append({"route": route, "severity": "FAIL",
                          "issue": f"banned word(s) in rendered text (hard rule 2): {banned_hits}"})

    return ok


def run_interactions(page, steps_path, findings):
    steps = json.loads(Path(steps_path).read_text())
    base = Path(steps_path).resolve().parent
    for i, step in enumerate(steps):
        try:
            if "click" in step:
                page.click(step["click"], timeout=10000)
            elif "fill" in step:
                page.fill(step["fill"], step["value"], timeout=10000)
            elif "set_input_files" in step:
                page.set_input_files(step["set_input_files"],
                                      str((base / step["path"]).resolve()), timeout=10000)
            elif "wait_for_selector" in step:
                page.wait_for_selector(step["wait_for_selector"],
                                        timeout=step.get("timeout_ms", 20000))
            elif "wait_ms" in step:
                page.wait_for_timeout(step["wait_ms"])
            else:
                findings.append({"route": "[interaction]", "severity": "FAIL",
                                  "issue": f"step {i} has no recognised action: {step}"})
        except Exception as exc:  # noqa: BLE001
            findings.append({"route": "[interaction]", "severity": "FAIL",
                              "issue": f"step {i} ({step}) failed: {exc}"})


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--url", help="Live base URL, e.g. https://slug.fly.dev")
    p.add_argument("--app-dir", help="App root to resolve --url from fly.toml's `app =` field (fix 13) when --url is omitted")
    p.add_argument("--routes", nargs="*", help="Explicit route paths to check, e.g. / /submit")
    p.add_argument("--config", help="Path to a demo.config.json to discover routes from")
    p.add_argument("--interactions", help="Path to a JSON interaction-steps file (see docstring)")
    p.add_argument("--json", help="Optional path to write a machine-readable report")
    args = p.parse_args()

    url = args.url or resolve_url_from_fly_toml(Path(args.app_dir or "."))

    routes = discover_routes(args)
    findings = []
    checked = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        for i, route in enumerate(routes):
            page = context.new_page()
            ok = check_route(page, url, route, findings)
            checked.append({"route": route, "ok": ok})
            if i == 0 and args.interactions:
                run_interactions(page, args.interactions, findings)
                # re-check the same page's state after interacting, for errors the
                # interaction itself triggered (e.g. a submit that 500s)
                ok2 = check_route(page, url, route, findings)
                checked[-1]["ok"] = checked[-1]["ok"] and ok2
            page.close()
        browser.close()

    overall_pass = not findings
    report = {"url": url, "routes_checked": checked, "findings": findings,
              "overall": "PASS" if overall_pass else "FAIL"}

    print(f"\nDemo QA gate - {url}")
    print(f"Routes checked: {', '.join(r['route'] for r in checked)}")
    if overall_pass:
        print(f"Result: PASS - {len(checked)} route(s), zero findings\n")
    else:
        print(f"Result: FAIL - {len(findings)} finding(s):\n")
        for f in findings:
            print(f"  [{f['severity']}] {f['route']}: {f['issue']}")
        print()

    if args.json:
        Path(args.json).write_text(json.dumps(report, indent=2))
        print(f"Machine-readable report written to {args.json}")

    sys.exit(0 if overall_pass else 1)


if __name__ == "__main__":
    main()
