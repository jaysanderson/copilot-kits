"""Independent functional QA gate for demo apps (Workflow 5).

INCIDENT 24 Oct 2026: a deployer gave this gate 24 hash routes of a single-page app as ONE
space-separated --routes argument and it printed "Distinct page content 1 of 1, reveal
clicked 1 of 1" and exited 0 against a catch-all SPA - 24 routes requested, one nonsense path
("/#a /#b ...") driven. Cause: discover_routes split only on commas, and the denominators
were honest about what ran but nobody compared them with what was asked. Fixed: routes split
on commas AND whitespace, and a route not starting with '/' or 'http' exits 2. Control:
scripts/selftest_hash_routes.py (a fixture SPA with three distinct hash routes plus one
that errors; pre-fix this gate reported 1 of 1, now 3 distinct pages and FAIL on the fourth).

Why this exists: builders self-certifying their own demo against the DEFINITION-OF-PASS
checklist misses real runtime defects - a route that 500s, a console error, a raw error
page, a leaked secret/region string, unrendered markdown - because the person grading the
work already believes it works. This script actually drives a live demo in a real browser
and reports what it finds, independent of what the builder claims. It does not replace
qa-reviewer's judgement calls (brand fit, "does this survive the room") - it catches the
mechanical defects that are cheap to automate and expensive to miss.

Usage:
    python scripts/demo_qa_gate.py --url https://slug.fly.dev --routes / /submit /codes
    python scripts/demo_qa_gate.py --url https://slug.fly.dev --config apps/slug/demo.config.json
    python scripts/demo_qa_gate.py --url https://slug.fly.dev --routes / --interactions apps/slug/qa_flow.json

Exit code is non-zero if any route FAILs. Always prints a human-readable report; --json
also writes a machine-readable one for a follow-up qa-reviewer pass to consume.

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

# Same leak patterns used in the gov-degree-triage APPROVED.md evidence pass - kept here so
# every future demo gets the identical, already-proven check rather than each build
# reinventing its own grep.
SECRET_REGION_PATTERNS = [
    r"ARAG_[A-Z_]+",
    r"aws-[a-z]+-[a-z]+-\d",
    r"rag\.progress\.cloud",
    r"eyJhbGci",                 # JWT header fragment
    r"x-nuclia",
    r"nua[_-]?key",
    r"knowledge box",
    r"/ask(?![\w-])",
    r"/find(?![\w-])",
    r"/graph(?![\w-])",
    r"/predict/remi(?![\w-])",
    r"/predict(?![\w-])",
    r"\bnuclia",   # no trailing \b: must also catch NucliaDB, Nuclia\'s, nuclia-db
]
SECRET_REGION_RE = re.compile("|".join(SECRET_REGION_PATTERNS), re.IGNORECASE)

# --- route-scoped waiver (added 11 Oct 2026, lead) -------------------------------------------------
# One build legitimately needs a banned string on ONE page: a developer quickstart that prints the
# real endpoint shapes a reader must type. The honest mechanism is a waiver that is NARROW (one
# route, exact literals), VISIBLE (printed in the report, never silent) and TESTED BOTH WAYS - not a
# widened regex, which would stop the check seeing that string anywhere, and not a removed check.
#
# Shape: --allow-on-route "/build=X-NUCLIA-SERVICEACCOUNT,/find,/ask"
# The literals are REMOVED from the page text before scanning, so every OTHER leak on that route
# still fails. A declared literal that matches nothing is reported as UNUSED, because a waiver that
# outlives its reason is how a hole gets left open.
ROUTE_WAIVERS = {}          # {route: [literal, ...]} - populated from the command line
WAIVER_USE = {}             # {(route, literal): count} - what was actually waived


# A DEMO WHOSE ARGUMENT IS ROLE-SCOPED ANSWERS CANNOT BE GATED BY A RULE THAT FAILS ON
# EVERY 4xx - AND LOOSENING THE RULE IS THE WRONG FIX.
#
# Raised by an independent tester on a flagship build: signed out, /#suppliers fires
# /api/suppliers, the server refuses with 403 and the page renders the server's own
# words. That is the product working. This gate counts any response >= 400 as a network
# error, so the only reason it reported clean is that it never drove that route signed
# out - the whole visitor half of an entitlement demo was ungated, which is worse than a
# false failure because nothing says so.
#
# An exemption alone would be a blind spot with a flag on it. A DECLARED refusal is the
# opposite: the gate stops failing on exactly that status at exactly that URL on exactly
# that route, and FAILS if it never happens. A refusal that stops being produced means
# the scoping has broken, which is the thing an entitlement demo most needs caught, so
# the declaration turns a hole into a positive assertion.
#
# Same discipline as the leak waivers below: narrow to one route, printed in the report,
# and reported when it matches nothing.
EXPECTED_REFUSALS = {}        # route -> [(status, url_substring), ...]
REFUSALS_SEEN = set()         # (route, status, url_substring) actually observed


def parse_refusals(specs):
    out = {}
    for spec in specs or []:
        if "=" not in spec:
            raise SystemExit(
                f"--expect-refusal needs ROUTE=STATUS:URL_SUBSTRING; got {spec!r}")
        route, rest = spec.split("=", 1)
        if ":" not in rest:
            raise SystemExit(
                f"--expect-refusal {spec!r} needs STATUS:URL_SUBSTRING after the '='")
        status, frag = rest.split(":", 1)
        status, frag = status.strip(), frag.strip()
        if not status.isdigit() or not frag:
            raise SystemExit(f"--expect-refusal {spec!r} is not STATUS:URL_SUBSTRING")
        # A refusal is a 4xx. Declaring a 5xx would waive a crash, which is never a
        # thing a demo is supposed to do.
        if not 400 <= int(status) < 500:
            raise SystemExit(
                f"--expect-refusal {spec!r}: only a 4xx can be an expected refusal; "
                f"a 5xx is a crash and is never declared away")
        out.setdefault(route.strip(), []).append((int(status), frag))
    return out


def _console_is_declared_refusal(route: str, text: str) -> bool:
    """A console entry for a refusal this route is DECLARED to produce AND has produced.

    Two conditions, both needed. Declared, so a route with no declaration is unaffected.
    And actually SEEN in the response buffer on this route, so the forgiveness cannot be
    claimed by a status nothing produced - which keeps the flag from becoming a blanket
    "ignore 403 here".
    """
    import re as _re
    m = _re.search(r"status of (\d{3})", text or "")
    if not m:
        return False
    status = int(m.group(1))
    return any(st == status and (route, st, frag) in REFUSALS_SEEN
               for st, frag in EXPECTED_REFUSALS.get(route, []))


def is_expected_refusal(route: str, entry: str) -> bool:
    """`entry` is the recorded "STATUS URL" string. Marks the declaration as seen."""
    try:
        status_s, url = entry.split(" ", 1)
        status = int(status_s)
    except ValueError:
        return False
    for want_status, frag in EXPECTED_REFUSALS.get(route, []):
        if status == want_status and frag in url:
            REFUSALS_SEEN.add((route, want_status, frag))
            return True
    return False


def parse_waivers(specs):
    out = {}
    for spec in specs or []:
        if "=" not in spec:
            raise SystemExit(f"--allow-on-route needs ROUTE=literal[,literal]; got {spec!r}")
        route, lits = spec.split("=", 1)
        vals = [l for l in (x.strip() for x in lits.split(",")) if l]
        if not vals:
            raise SystemExit(f"--allow-on-route {spec!r} declares no literals")
        out.setdefault(route.strip(), []).extend(vals)

    # ENTITY-ENCODING TRAP (12 Oct 2026, cost the lead four tool calls and a wrong
    # conclusion about the page). The waiver is applied to page.content() - RAW HTML -
    # so a literal containing a character HTML escapes can never match, no matter how
    # exactly it matches what a human sees. The real case: the authored sample reads
    # curl "https://<ZONE>.rag.progress.cloud/..." and the DOM holds
    # &lt;ZONE&gt;.rag.progress.cloud, so the waiver '<ZONE>.rag.progress.cloud' waived 0
    # and the route still FAILED. The UNUSED report caught it correctly; what was missing
    # was anyone saying WHY, so the lead went looking for the string in the page and an
    # over-constrained context regex told it the string was absent. Twice wrong about the
    # artifact, from one unescaped angle bracket.
    # Same family as the typographic-apostrophe trap in CLAUDE.md - a pattern written in
    # the AUTHORED form returning zero against the RENDERED form - different mechanism.
    # NARROWED on its own negative control (same session): the first draft fired on an
    # ALREADY-ENCODED literal, because '&lt;ZONE&gt;' contains '&' - and it then advised
    # double-encoding it to '&amp;lt;'. Over-firing with wrong advice is worse than silence,
    # so a literal that is already escaped is recognised and left alone. The population is
    # unchanged: every declared waiver is still examined.
    import html as _html
    for route, lits in out.items():
        for lit in lits:
            if _html.unescape(lit) != lit:
                continue        # already in the encoded form the DOM holds - correct as declared
            bad = [c for c in '<>&"' if c in lit]
            if bad:
                print(f"  NOTE: waiver {route}={lit!r} contains {bad} which HTML-escapes. "
                      f"The scan reads raw HTML, so this literal will match 0 times unless the page "
                      f"emits it unescaped. The encoded form is {_html.escape(lit, quote=True)!r} - "
                      f"declare whichever one the DOM actually holds.")
    return out


def apply_waivers(route, text):
    """Remove waived literals for this route, counting each removal.

    Route "*" waives a literal on EVERY route. Use it only for a term the PRODUCT
    ITSELF publishes, where the pattern is right for other builds and wrong for this
    one. The case it was added for: "knowledge box" is banned because on a demo app
    pretending to be a customer's own product it leaks the underlying platform - but
    Progress publishes "knowledge boxes included, $750 per month for each additional"
    on its own pricing page and titles a published asset "Your first Knowledge Box in
    minutes". On the product's own site it is the correct noun. Widening the regex
    instead would stop the check working on every demo build, where it is a real leak.
    CORRECTED 12 Oct 2026, and the correction is the point. This docstring used to say
    '"nuclia" stays banned, because the vendor name is not published by Progress on a
    customer surface'. That sentence was written by the lead from memory and is FALSE.
    Progress publishes, on its own documentation at docs.rag.progress.cloud (footer
    "Copyright (c) 2026 Progress Software Corporation"), the authentication header names
    X-NUCLIA-SERVICEACCOUNT and X-NUCLIA-NUAKEY verbatim, the host patterns
    <ZONE>.dp.progress.cloud (data plane) and accounts.progress.cloud, and the product name
    NucliaDB in body text. Verified by fetching that page, not by reading our own.

    Three consequences, because the corrected fact is narrower than either the old
    sentence or its opposite:
      * The HEADER NAME is a published API identifier. A developer quickstart that
        prints X-NUCLIA-SERVICEACCOUNT is reproducing Progress's own instructions, and
        suppressing it would make the code sample WRONG. Waivable on that route.
      * NO HOST WAIVER - the half the lead got WRONG. See the block below.
        It waived '<ZONE>.rag.progress.cloud' as 'the published documentation form' on the
        strength of a WEB-SEARCH SUMMARY quoting a curl example on that host. site-backend
        fetched the pages directly and found otherwise, and a direct fetch of the account
        API page settles it: Progress documents accounts.progress.cloud for the account
        API and <zone>.dp.progress.cloud for the data plane (/find, /ask, KB operations),
        while rag.progress.cloud appears ONLY as a dashboard redirect for a test token. It
        does answer API calls - it is a live alias, and hard rule 14's own account check
        uses it - but a quickstart that teaches it teaches an UNDOCUMENTED host. So the
        SAMPLE was changed to the published data-plane host and the waiver withdrawn: a
        correctness fix in the artifact beat an exception in the gate. A REAL zone
        (<zone>.dp.progress.cloud) is still a residency leak, so the host
        pattern keeps firing on every build.
        **The transferable error: a WebSearch result is a SMALL MODEL'S SUMMARY of a page
        and it is not a fetch.** The lead cited it as primary against a peer who had
        fetched - inverting its own rule that where someone else enumerated and you
        sampled, theirs wins. And it wrote the unsupported host into THIS docstring in the
        very commit that corrected a different false sentence here: a correction pass is
        when a new false fact gets written, because the author is in the mood of being
        right.
      * A bare "nuclia" as PROSE on a Progress surface is still a FAIL, and the reason
        is now editorial rather than secrecy: it is the wrong noun for us to write, not
        a string nobody has published. Keep the pattern; it just no longer gets to
        claim the stronger justification.

    The general rule this earns: an instrument's stated REASON is a claim, and a claim
    in a docstring is read as a citation by the next person. This one would have made a
    future reader refuse a legitimate waiver on authority that did not exist.
    """
    # CASE-INSENSITIVE, because SECRET_REGION_RE is re.IGNORECASE. The first version of
    # this used str.count/str.replace and was case-SENSITIVE, so "Knowledge Box" in title
    # case escaped a waiver for "knowledge box" and failed the gate while a waiver appeared
    # to be in place. A waiver must match on the same terms as the check it narrows -
    # the same rule as a control being built from the check's own expression.
    for lit in ROUTE_WAIVERS.get("*", []) + ROUTE_WAIVERS.get(route, []):
        pat = re.compile(re.escape(lit), re.IGNORECASE)
        text, n = pat.subn(" ", text)
        key = ("*", lit) if lit in ROUTE_WAIVERS.get("*", []) else (route, lit)
        WAIVER_USE[key] = WAIVER_USE.get(key, 0) + n
    return text

# A positive sample of the exact leak each pattern above exists to catch. Keyed by
# the pattern string itself so selftest() below can never drift out of sync with
# SECRET_REGION_PATTERNS - add a pattern without a sample and selftest fails loudly
# rather than silently skipping it.
SECRET_REGION_POSITIVE_SAMPLES = {
    r"ARAG_[A-Z_]+": "export ARAG_NUA_KEY=eyJ...",
    r"aws-[a-z]+-[a-z]+-\d": "hosted in <zone>",
    r"rag\.progress\.cloud": "https://rag.progress.cloud/api/v1/kb",
    r"eyJhbGci": "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.payload.sig",
    r"x-nuclia": "X-NUCLIA-SERVICEACCOUNT: abc123",
    r"nua[_-]?key": "the raw nua_key leaked in the response",
    r"knowledge box": "ingested into the Knowledge Box",
    r"/ask(?![\w-])": "the app calls /ask to retrieve",
    r"/find(?![\w-])": "scoped with /find and a filter",
    r"/graph(?![\w-])": "renders the /graph response",
    r"/predict/remi(?![\w-])": "scored via POST /predict/remi",
    r"/predict(?![\w-])": "hits the /predict endpoint",
    r"\bnuclia": "built on NucliaDB under the hood",
}

# A NEGATIVE sample per endpoint-name pattern (added 1 Oct 2026, Studycity false
# positive): a legitimate app route that merely SHARES A PREFIX with the ARAG
# mechanism name must NOT fire. The real incident - Studycity's own "Find Your
# Path" persona page lives at /find-your-path, and its href="/find-your-path"
# attribute (the gate scans page.content(), the full raw HTML, not just visible
# text) matched the old r"/find\b" pattern, because \b only requires the NEXT
# CHARACTER not be a word character - a hyphen satisfies that, so "/find-" reads
# as a word boundary too. Fixed by requiring the character after the mechanism
# name be neither a word character NOR a hyphen ((?![\w-])), which still fires on
# every real leak (proven by the positive samples above, unchanged) and now
# correctly stays quiet on a hyphenated continuation of the same word. selftest()
# below proves both halves for every pattern listed here - do not add a pattern
# to SECRET_REGION_PATTERNS whose trailing edge can abut a hyphen without also
# registering its negative sample here.
SECRET_REGION_NEGATIVE_SAMPLES = {
    r"/ask(?![\w-])": '<a href="/ask-a-mentor">Ask a mentor</a>',
    r"/find(?![\w-])": '<a class="sp-btn sp-btn-ghost" href="/find-your-path">Find your path &rarr;</a>',
    r"/graph(?![\w-])": '<a href="/graphing-your-progress">Graphing your progress</a>',
    r"/predict(?![\w-])": '<a href="/predictive-text-helper">Predictive text helper</a>',
}

# Gate 8's specific named defect: literal markdown syntax rendered as text instead of
# through a markdown component (real defect: literal "**Unit 14**" shown on screen).
# MULTILINE matters: the heading alternative's `^` must anchor to the start of any
# LINE in the page's full body text, not just character 0 of the whole string - a
# heading is never the very first character Playwright's inner_text("body") returns
# (nav/hero copy always precedes it), so without MULTILINE that branch is dead code
# that can never fire against a real page (found via selftest() below, 24 Aug 2026).
RAW_MARKDOWN_RE = re.compile(r"\*\*[^*\n]{2,80}\*\*|^#{1,6}\s+\S|\[[^\]]+\]\([^)]+\)",
                              re.MULTILINE)

# One positive sample per alternative in RAW_MARKDOWN_RE, each isolating just that
# branch so selftest() proves every branch fires independently, not just that the
# combined regex fires on some string (a bold-only sample would hide a dead heading
# or link branch).
RAW_MARKDOWN_POSITIVE_SAMPLES = [
    ("bold", "Some text before **Unit 14** and after"),
    ("heading", "Portfolio Dashboard\n## Renewal window\nmore content follows"),
    ("link", "See [the contract](https://example.com/doc) for details"),
]

# No separate false-positive SUPPRESSION FILTER exists in this gate (unlike the OCR
# sweep's remittance/REMi guard) - the discrimination is built into the patterns
# themselves via the (?![\w-]) trailing guard above, not a second filtering pass.
# Audited 24 Aug 2026 against \b word boundaries and found no collision; the 1 Oct
# 2026 Studycity incident proved that audit wrong for exactly the endpoint-name
# patterns (\b tolerates a trailing hyphen, and a real app route - /find-your-path -
# collided with it), which is why those patterns now carry their own negative
# samples in SECRET_REGION_NEGATIVE_SAMPLES instead of a trust-the-boundary
# assumption. If a suppression filter is ever added here, scope it to the specific
# pattern family it guards (per the oe3_text_sweep.py precedent) - never let it
# touch a pattern outside the collision it was written for.

# Word-spacing corruption detector (Fanclub 4 Sep 2026): a hyphen between every
# word ("The - Klingon - Empire - and ..."). Detect the CONTIGUOUS RUN, not a
# page-wide count - a content-rich page legitimately carries a dozen scattered
# spaced-hyphens (Australian-English house style replaces em dashes with " - "),
# which a page-wide count false-positives on (Home-two, 4 Sep 2026: 12 legit
# hyphens flagged). Real corruption puts " - " between EVERY word, so 6+
# consecutive `word - ` sequences in one text run is the unambiguous signature
# and legitimate copy essentially never produces it.
WORD_HYPHEN_WORD_RE = re.compile(r"(?:[A-Za-z0-9]+ - ){6,}[A-Za-z0-9]")
WORD_HYPHEN_POSITIVE_SAMPLE = (
    "The - Klingon - Empire - and - the - Romulan - Star - Empire - exhibit - "
    "distinct - characteristics - and - governing - philosophies - across - space")
WORD_HYPHEN_NEGATIVE_SAMPLE = (  # legit scattered spaced-hyphens must NOT fire
    "Grounded - cited answers. Net 30 terms. The FY25 report - a summary - is "
    "here. Open one below, or refine. Rate lock - peak season - applies.")

IGNORABLE_404_SUFFIXES = (".ico", ".map")

# Blank-page floor. 120 characters is below any real page and far above an empty
# body; measured against the self-serve site's thinnest route, which renders ~900.
MIN_VISIBLE_CHARS = 120


def selftest():
    """Prove every leak-detection pattern in this gate can actually fire before
    trusting a PASS from it.

    This gate is layer 1 of the independent QA gate on every demo the factory
    ships - the thing standing between a shipped demo and a leaked ARAG endpoint
    name, region string, or JWT fragment. A CLEAN result from a detector nobody
    has demonstrated capable of firing is not evidence a demo is clean; it's an
    unverified assumption. Run as a precondition at gate start, every run - if any
    pattern here cannot fire on the exact string it exists to catch, the gate must
    refuse to report PASS on anything.
    """
    bad = []
    for pattern in SECRET_REGION_PATTERNS:
        sample = SECRET_REGION_POSITIVE_SAMPLES.get(pattern)
        if sample is None:
            bad.append(f"SECRET_REGION pattern {pattern!r} has no registered positive "
                       f"sample - selftest cannot prove it fires")
            continue
        if not re.search(pattern, sample, re.IGNORECASE):
            bad.append(f"SECRET_REGION pattern {pattern!r} did NOT fire on its own "
                       f"positive sample {sample!r}")
    for pattern, sample in SECRET_REGION_NEGATIVE_SAMPLES.items():
        if re.search(pattern, sample, re.IGNORECASE):
            bad.append(f"SECRET_REGION pattern {pattern!r} FALSE-fired on its "
                       f"registered negative sample {sample!r} - a legitimate "
                       f"hyphenated route would be reported as a leak")
    for label, sample in RAW_MARKDOWN_POSITIVE_SAMPLES:
        if not RAW_MARKDOWN_RE.search(sample):
            bad.append(f"RAW_MARKDOWN {label!r} branch did NOT fire on its own "
                       f"positive sample {sample!r}")

    if not WORD_HYPHEN_WORD_RE.search(WORD_HYPHEN_POSITIVE_SAMPLE):
        bad.append("WORD_HYPHEN_WORD detector did NOT fire on its corruption "
                   "positive sample - cannot prove it catches word-spacing corruption")
    if WORD_HYPHEN_WORD_RE.search(WORD_HYPHEN_NEGATIVE_SAMPLE):
        bad.append("WORD_HYPHEN_WORD detector FALSE-fired on legit scattered "
                   "spaced-hyphens - it would cry wolf on normal Australian-English copy")

    if bad:
        print("GATE SELFTEST: FAIL - this gate cannot be trusted to detect what it "
              "claims to. Refusing to run.")
        for b in bad:
            print(f"  - {b}")
        return False
    print(f"Gate selftest: PASS - all {len(SECRET_REGION_PATTERNS)} secret/region/"
          f"endpoint-name patterns, all {len(RAW_MARKDOWN_POSITIVE_SAMPLES)} raw-"
          f"markdown branches, and the word-spacing-corruption detector fire on "
          f"their own positive sample; all {len(SECRET_REGION_NEGATIVE_SAMPLES)} "
          f"endpoint-name patterns with a registered negative sample stayed quiet "
          f"on it.")
    return True


def selftest_blank_page():
    """Prove the blank-page detector fires on an empty body and stays quiet on a real one.

    Offline, through the shipped check_route, because the defect it exists for was invisible to
    every other axis of this gate and a detector nobody has watched fire is not evidence.
    """
    import tempfile
    from playwright.sync_api import sync_playwright
    cases = [
        ("blank", "<!doctype html><html><head><title>t</title></head><body></body></html>", True),
        ("no-h1", "<!doctype html><html><head><title>t</title></head><body><main><p>"
                  + ("Real body copy that easily clears the floor. " * 6) + "</p></main></body></html>", True),
        ("good", "<!doctype html><html><head><title>t</title></head><body><main><h1>A page</h1><p>"
                 + ("Real body copy that easily clears the floor. " * 6) + "</p></main></body></html>", False),
    ]
    bad = False
    with tempfile.TemporaryDirectory() as td, sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        for name, html, want_fail in cases:
            f = Path(td) / f"{name}.html"
            f.write_text(html)
            page = browser.new_context().new_page()
            buf = install_listeners(page)
            findings = []
            check_route(page, f.as_uri(), "", findings, buf)
            got = [x for x in findings if "rendered almost nothing" in x["issue"]
                   or "no h1" in x["issue"]]
            if want_fail and not got:
                bad = True
                print(f"  - {name}: should have been reported and was not")
            if not want_fail and got:
                bad = True
                print(f"  - {name}: a real page was reported as blank: {got}")
            page.close()
        browser.close()
    if bad:
        print("BLANK-PAGE CONTROL: FAIL")
        return False
    print("Blank-page control: PASS - an empty body and a body with no h1 are both reported, "
          "a real page with an h1 stays quiet.")
    return True


def selftest_interaction_capture():
    """Prove the gate can SEE a console error raised by an --interactions step.

    Offline and self-contained: a local page with two buttons, one that raises
    console.error on click and one that does not. Runs the real install_listeners /
    check_route / run_interactions path, so it tests the shipped code rather than a
    retyped copy of it. Both ways, because the version of this gate before 11 Oct 2026
    returned a serene PASS either way and a one-sided control cannot tell the difference.

    Also asserts the post-interaction pass does NOT navigate: the page mutates a marker
    on click, and that marker must still be in the DOM when the second pass inspects it.
    """
    import tempfile
    from playwright.sync_api import sync_playwright

    html = (
        "<!doctype html><html><head><meta charset='utf-8'><title>ctl</title></head><body>"
        "<main><h1>Control page</h1><p id='m'>clean</p>"
        "<button id='bad' onclick=\"console.error('planted interaction error');"
        "document.getElementById('m').textContent='mutated'\">bad</button>"
        "<button id='ok' onclick=\"document.getElementById('m').textContent='mutated'\">ok</button>"
        "</main></body></html>"
    )
    bad = False
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        (d / "index.html").write_text(html)
        (d / "bad.json").write_text(json.dumps([{"click": "#bad"}, {"wait_ms": 200}]))
        (d / "ok.json").write_text(json.dumps([{"click": "#ok"}, {"wait_ms": 200}]))
        base = (d / "index.html").as_uri()

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            for name, steps, want_error in (("plant", d / "bad.json", True),
                                            ("quiet", d / "ok.json", False)):
                page = browser.new_context().new_page()
                buf = install_listeners(page)
                findings = []
                check_route(page, base, "", findings, buf)
                load_findings = len(findings)
                run_interactions(page, str(steps), findings)
                check_route(page, base, "", findings, buf, navigate=False,
                            label="[after interactions]")
                got = [f for f in findings[load_findings:]
                       if "planted interaction error" in f.get("issue", "")]
                if want_error and not got:
                    bad = True
                    print(f"  - {name}: an interaction raised console.error and the gate "
                          f"did NOT report it (this is the pre-fix behaviour)")
                if not want_error and got:
                    bad = True
                    print(f"  - {name}: the gate reported a planted error that was never raised")
                marker = page.inner_text("#m") if page.query_selector("#m") else ""
                if marker != "mutated":
                    bad = True
                    print(f"  - {name}: post-interaction pass lost the page state "
                          f"(#m reads {marker!r}, not 'mutated') - it re-navigated")
                page.close()
            browser.close()

    if bad:
        print("INTERACTION-CAPTURE CONTROL: FAIL")
        return False
    print("Interaction-capture control: PASS - a console error raised by an interaction is "
          "reported, a clean interaction stays quiet, and the post-interaction pass inspects "
          "the state the interaction left behind rather than re-navigating.")
    return True


def discover_routes(args):
    if args.routes:
        # A comma-separated list is the natural thing to type and this flag is nargs="*", so
        # `--routes "/,/explore,/build"` arrives as ONE string. It used to be driven as a single
        # nonsense path - and against an SPA with a catch-all route that returns 200 with the
        # shell, the gate then reported "PASS - 1 route(s), zero findings" having checked nothing.
        # The only tell was the route COUNT in a line nobody reads. 11 Oct 2026: a lead ran the
        # live gate that way and nearly recorded it as a clean sweep of eight routes. Split it,
        # because refusing would make the obvious spelling an error for no benefit.
        out = []
        for r in args.routes:
            # Split on WHITESPACE as well as commas (24 Oct 2026, see the docstring incident):
            # a route never contains a space, so a space is always a separator.
            out.extend(s for s in re.split(r"[,\s]+", r.strip()) if s)
        bad = [r for r in out if not (r.startswith("/") or r.startswith("http"))]
        if bad:
            print(f"ERROR: route(s) {bad} do not start with '/' or 'http' - refusing to "
                  f"guess what was meant.", file=sys.stderr)
            sys.exit(2)
        if len(out) != len(args.routes):
            print(f"Note: --routes was given {len(args.routes)} argument(s) containing "
                  f"{len(out)} comma-separated path(s); driving all {len(out)}.")
        return out
    if args.config:
        cfg = json.loads(Path(args.config).read_text())
        routes = [s["route"] for s in cfg.get("surfaces", []) if s.get("enabled", True)]
        if routes:
            return routes
    return ["/"]


def install_listeners(page):
    """Attach console/pageerror/response listeners for the LIFETIME of the page.

    These used to be attached inside check_route around page.goto and REMOVED before
    --interactions ran, so a console error raised BY an interaction was invisible to the
    gate. Found 11 Oct 2026 by a builder trying to prove its own withheld-answer guard
    fails the gate: its clean run and its deliberately-broken run both exited 0, and it
    correctly refused to read that as a pass. The companion defect was worse - the
    post-interaction "re-check" called check_route again, which NAVIGATES, so it destroyed
    the interaction's state and then inspected a freshly loaded page while its comment
    claimed it was checking "the same page's state after interacting". A check whose
    comment describes an intention its implementation does not perform.

    Buffers are DRAINED at each inspection point, so the post-interaction pass reports only
    what the interaction itself produced and nothing is double-counted.
    """
    buf = {"console": [], "page": [], "resp": []}

    def on_console(msg):
        if msg.type == "error":
            buf["console"].append(msg.text)

    def on_pageerror(exc):
        buf["page"].append(str(exc))

    def on_response(resp):
        if resp.status >= 400 and not resp.url.endswith(IGNORABLE_404_SUFFIXES):
            buf["resp"].append(f"{resp.status} {resp.url}")

    page.on("console", on_console)
    page.on("pageerror", on_pageerror)
    page.on("response", on_response)
    return buf


# The settle tally spans routes while `buf` is created per page, so it cannot live in
# `buf`. Module level, reset by main(), and printed in the report - because a route
# scanned with its data present and one scanned 1.5s after load are different coverage
# and must not be summed into a single pass.
SETTLE = {"settled": [], "unsettled": []}

# DID THE ROUTES ACTUALLY DIFFER? A digest of the scanned text per route, so the one
# question this gate could never answer about itself becomes a line in its own output.
#
# An adversarial tester asked it directly: "I passed hash routes as /#... I did not check
# whether the gate navigates to the hash or just reloads /. If it ignores the fragment, my
# 5 routes were 1 page loaded 5 times." That is the right question and it applies to every
# run this gate has ever reported - including the 21-route passes I had been quoting as
# evidence. A fragment-only change is a SAME-DOCUMENT navigation, so page.goto returns no
# response for it and nothing in the old output distinguished twenty-one routes from one
# page counted twenty-one times.
#
# Reported as a fraction rather than a verdict: distinct digests over routes scanned.
ROUTE_DIGESTS: dict[str, str] = {}
# HOW MANY REVEALS WERE ACTUALLY CLICKED AND OPENED. Without this the check's zero
# findings read the same whether it ran on nineteen routes or on none - which is the
# zero-of-zero trap, and the third time in one session that one of my own instruments
# needed its denominator printed rather than implied.
REVEAL = {"opened": [], "navigated": [], "failed": []}


# THE REVEAL IS BINDING ON EVERY DEMO, AND NOTHING WAS CHECKING THAT IT OPENS.
#
# 21 Oct 2026: a backtick inside a comment closed a template literal, so a demo's reveal
# module failed to PARSE, its dynamic import() rejected, and every "How this works"
# button on the deployed site did nothing. A clean 19-route run of this gate, a clean
# 100-test suite and a console read all reported green, because the module is imported
# on CLICK - a page load produces no error at all. An outside tester found it with a
# JavaScript syntax check on the served file.
#
# A gate that stops at page load cannot see a lazily-imported module, and that is where
# code-split and on-demand imports live. So this clicks it.
#
# The selector comes from the BINDING RULE rather than from one app's markup: the demo
# standard requires a "How this works" control on every route, so matching its visible
# text covers every build without a per-app configuration to keep in step.
_REVEAL_TEXT = re.compile(r"how\s+(?:this|it)\b.{0,24}\bworks", re.I)


def check_reveal_opens(page, label, findings):
    """Click the reveal and require that something opens, with no page error.

    Three findings, kept separate because the remedies differ: absent (the standard is
    not met), present but opens nothing (the handler or its module is broken), and a
    page error on click (which names the real cause and is the one that was silent).
    """
    btns = page.locator("button, a").filter(has_text=_REVEAL_TEXT)
    try:
        n = btns.count()
    except Exception:
        n = 0
    if not n:
        findings.append({"route": label, "severity": "FAIL",
                         "issue": ("no 'How this works' control on this route; the demo "
                                   "standard requires one on every route")})
        return
    errs: list[str] = []
    page.on("pageerror", lambda e: errs.append(str(e)[:160]))
    before = page.evaluate("() => document.body.innerHTML.length")
    url_before = page.url
    try:
        btns.first.click(timeout=8000)
        page.wait_for_timeout(1200)
    except Exception as exc:
        findings.append({"route": label, "severity": "FAIL",
                         "issue": f"the reveal control could not be clicked: {exc}"[:200]})
        return
    after = page.evaluate("() => document.body.innerHTML.length")
    navigated = page.url != url_before

    # A REVEAL NEED NOT BE AN OVERLAY, and assuming it was gave this check a false
    # positive on its first run against another build. On arag-realestate the control is
    # an <a href="/t/realestate/how-it-works"> - its own page - so clicking NAVIGATES and
    # the body legitimately SHRINKS, 45,921 chars to 13,050. "The document did not grow"
    # reported that working reveal as opening nothing, which is worse than not checking.
    #
    # The discriminator is whether the click went anywhere: a URL change into a
    # non-trivial document is a reveal of a different SHAPE, not a broken one. Narrowed
    # on the pattern rather than by excluding that build, and arag-realestate is the
    # named control for it.
    # ONE CHAIN, because two were counting the same route twice. The tally and the
    # findings were separate if/else blocks after a line-by-line edit, so a navigation
    # landed in `navigated` AND in `failed` and the report read "1 of 2 route(s)" for a
    # single route. A denominator that disagrees with its own numerator is worse than no
    # denominator: it was added to stop a zero reading as a pass, and it had itself
    # become the unreliable figure.
    if errs:
        REVEAL["failed"].append(label)
        findings.append({"route": label, "severity": "FAIL",
                         "issue": ("clicking the reveal raised a page error, so its "
                                   f"module did not load: {errs[0]}")})
    elif after > before:
        REVEAL["opened"].append(label)
    elif navigated and after > 2000:
        REVEAL["navigated"].append(label)
    else:
        # Nothing was added and nothing was navigated to. A dead dynamic import looks
        # exactly like this and raises nothing a load-time check can see.
        REVEAL["failed"].append(label)
        findings.append({"route": label, "severity": "FAIL",
                         "issue": ("the reveal control opened nothing: the document did "
                                   "not grow and the page did not navigate, which is "
                                   "what a failed dynamic import looks like")})


def check_route(page, base_url, route, findings, buf, navigate=True, label=None):
    """Inspect a route. navigate=False inspects the CURRENT page state without reloading,
    which is the only way to see what an interaction did."""
    url = urljoin(base_url, route)
    label = label or route

    ok, main_status = True, None
    if navigate:
        try:
            resp = page.goto(url, wait_until="load", timeout=30000)
            main_status = resp.status if resp else None
            # SETTLE BEFORE SCANNING, or this gate reads the SHELL.
            #
            # `load` fires before a single-page app has fetched anything, so on a
            # hash-routed demo every route scanned identical markup and the gate's
            # "19 routes, zero findings" was one document counted nineteen times.
            # Everything this file checks - leaks, raw markdown, console errors,
            # failed responses - lives in the content that arrives AFTER load.
            #
            # This changes the input of every check in this file, which is the point:
            # they see more. It can surface pre-existing findings in other builds, and
            # those are real findings rather than a regression. Whether the wait
            # succeeded is RECORDED and printed per route, because a settle that timed
            # out and a settle that worked must not report the same way.
            try:
                page.wait_for_load_state("networkidle", timeout=8000)
                SETTLE["settled"].append(label)
                try:
                    import hashlib as _hl
                    _txt = page.evaluate("document.body.innerText")
                    ROUTE_DIGESTS[label] = _hl.sha256(
                        (_txt or "").encode()).hexdigest()[:12]
                except Exception:
                    ROUTE_DIGESTS[label] = "unreadable"
            except Exception:
                # A surface that polls never goes idle. Give the first paint of data a
                # fixed moment rather than scanning the shell, and say it was partial.
                page.wait_for_timeout(1500)
                SETTLE["unsettled"].append(label)
            page.wait_for_timeout(1500)  # let async data-fetch renders settle
        except Exception as exc:  # noqa: BLE001 - report, don't crash the whole gate
            ok = False
            findings.append({"route": label, "severity": "FAIL",
                              "issue": f"page.goto failed: {exc}"})
    else:
        page.wait_for_timeout(1500)  # let the interaction's own renders settle

    console_errors = list(buf["console"]); buf["console"].clear()
    page_errors = list(buf["page"]);       buf["page"].clear()
    bad_responses = list(buf["resp"]);     buf["resp"].clear()

    if main_status is not None and main_status >= 400:
        ok = False
        findings.append({"route": label, "severity": "FAIL",
                          "issue": f"main document returned HTTP {main_status}"})
    for br in bad_responses:
        if is_expected_refusal(route, br):
            findings.append({"route": label, "severity": "NOTE",
                              "issue": f"declared refusal observed: {br}"})
            continue
        ok = False
        findings.append({"route": label, "severity": "FAIL", "issue": f"network error: {br}"})
    for err in console_errors:
        # THE SAME REFUSAL ARRIVES IN TWO BUFFERS. A declared 403 was correctly
        # downgraded in the response buffer and still failed the route here, because the
        # browser ALSO logs a failed fetch as a console error - "Failed to load
        # resource: the server responded with a status of 403 ()". The declaration
        # covered one of the two places one event lands.
        #
        # It cannot be matched on the URL, because Playwright's console text does not
        # carry one. So it is tied to the OBSERVED refusal instead: only a status this
        # route has actually produced as a declared refusal is forgiven, which means a
        # console 403 from anywhere else on a route with no such declaration still
        # fails. The dependency runs the right way - the response buffer is read before
        # this loop (deliberately reordered - it used to run after, which left the
        # set empty and the declared refusal still failing), so REFUSALS_SEEN is
        # populated for this route by the time this runs.
        if _console_is_declared_refusal(route, err):
            findings.append({"route": label, "severity": "NOTE",
                              "issue": f"console entry for the declared refusal: {err}"})
            continue
        ok = False
        findings.append({"route": label, "severity": "FAIL", "issue": f"console error: {err}"})
    for err in page_errors:
        ok = False
        findings.append({"route": label, "severity": "FAIL", "issue": f"page error: {err}"})

    # EVERY distinct leak, not the first. This used to be a single .search(), so a route
    # with four leaks reported one finding - and "1 finding" reads as "one problem", so each
    # fix or waiver revealed the next on the following run, one at a time, with no way to see
    # the real population before deciding what was legitimate. 11 Oct 2026: /build on the
    # self-serve site reported only rag.progress.cloud while also carrying a vendor header
    # name the same pattern set bans. Report every finding, never narrow scope.
    body_text = page.content()
    seen = []
    for m in SECRET_REGION_RE.finditer(apply_waivers(route, body_text)):
        if m.group(0).lower() not in [x.lower() for x in seen]:
            seen.append(m.group(0))
    for lit in seen:
        ok = False
        findings.append({"route": label, "severity": "FAIL",
                          "issue": f"secret/region/endpoint-name string leaked in page: "
                                   f"matched {lit!r}"})

    # A ROUTE THAT RENDERS NOTHING CAN STILL BE GREEN ON EVERY OTHER AXIS (11 Oct 2026).
    # A deploy from an inconsistent commit left every route of a live site rendering an empty
    # body - no h1, no copy - for about four minutes. healthz, the JSON API and the lens
    # endpoint were all fine throughout, so nothing server-side could see it, and it was found
    # by a person loading the page in a browser. This gate would have caught the module 404 as
    # a bad response, but a page that renders nothing while fetching nothing broken would still
    # have passed: there was no assertion that a route puts WORDS ON THE SCREEN.
    # Thresholds are deliberately low - this is a blank-page detector, not a content judge.
    visible_text = page.inner_text("body") if page.query_selector("body") else ""
    headline = page.query_selector("h1, [role=heading][aria-level='1']")
    if len(visible_text.strip()) < MIN_VISIBLE_CHARS:
        ok = False
        findings.append({"route": label, "severity": "FAIL",
                          "issue": f"route rendered almost nothing: "
                                   f"{len(visible_text.strip())} visible characters "
                                   f"(floor {MIN_VISIBLE_CHARS}) - a blank page is green on "
                                   f"every other axis of this gate"})
    elif headline is None:
        ok = False
        findings.append({"route": label, "severity": "FAIL",
                          "issue": "route rendered text but has no h1 - on a single-page app "
                                   "this is usually a partly-mounted view"})

    md_leak = RAW_MARKDOWN_RE.search(visible_text)
    if md_leak:
        ok = False
        findings.append({"route": label, "severity": "FAIL",
                          "issue": f"raw markdown syntax visible on screen (not rendered "
                                   f"through a markdown component): {md_leak.group(0)!r}"})

    # Word-spacing corruption: a hyphen jammed between EVERY word ("The - Klingon -
    # Empire ...") - the Fanclub 4 Sep 2026 defect a broken dash-normalising regex
    # produced on every generated answer. It slipped the automated gate, the DoP AND
    # the demo-tester twice, because none of them detected word-spacing corruption -
    # the raw-markdown check above only catches literal **/##/[](), valid characters
    # here. Detect the CONTIGUOUS RUN (6+ consecutive `word - ` sequences), not a
    # page-wide count: legitimate scattered spaced-hyphens (hard rule 2's em-dash
    # replacement) are common on a content page and a count false-positives on them
    # (Home-two, 4 Sep 2026), but real corruption puts " - " between every word.
    whw = WORD_HYPHEN_WORD_RE.search(visible_text)
    if whw:
        ok = False
        findings.append({"route": label, "severity": "FAIL",
                          "issue": f"word-spacing corruption: a hyphen between every word "
                                   f"(6+ consecutive 'word - ' joins) - a generated answer is "
                                   f"rendering broken dash-normalisation: {whw.group(0)[:80]!r}"})

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
    p.add_argument("--url", required=True, help="Live base URL, e.g. https://slug.fly.dev")
    p.add_argument("--routes", nargs="*", help="Explicit route paths to check, e.g. / /submit")
    p.add_argument("--no-reveal", action="store_true",
                   help="Skip the 'How this works' click. The reveal is binding on every "
                        "demo, so this is an exception to record, not a convenience.")
    p.add_argument("--config", help="Path to a demo.config.json to discover routes from")
    p.add_argument("--interactions", help="Path to a JSON interaction-steps file (see docstring)")
    p.add_argument("--selftest-interactions", action="store_true",
                   help="Run the offline both-ways control proving the gate sees a console "
                        "error raised by an interaction step, then exit.")
    p.add_argument("--json", help="Optional path to write a machine-readable report")
    p.add_argument("--expect-refusal", action="append", default=[],
                   help="ROUTE=STATUS:URL_SUBSTRING - a refusal this demo is SUPPOSED "
                        "to produce on that route, for example "
                        "'/#suppliers=403:/api/suppliers'. It stops counting as a "
                        "network error AND the route FAILS if it never happens.")
    p.add_argument("--allow-on-route", action="append", default=[],
                   help="ROUTE=literal[,literal] - permit these EXACT strings on that ONE "
                        "route only. Every other leak there still fails. Usage is printed "
                        "in the report; a waiver that matches nothing is reported UNUSED.")
    args = p.parse_args()

    EXPECTED_REFUSALS.update(parse_refusals(args.expect_refusal))
    if EXPECTED_REFUSALS:
        print("Expected refusals declared (each MUST occur or its route fails):")
        for r, pairs in EXPECTED_REFUSALS.items():
            for st, frag in pairs:
                print(f"  {r}: HTTP {st} on a URL containing {frag!r}")
    ROUTE_WAIVERS.update(parse_waivers(args.allow_on_route))
    if ROUTE_WAIVERS:
        print("Route-scoped waivers declared (every other leak on these routes still fails):")
        for r, lits in ROUTE_WAIVERS.items():
            print(f"  {r}: {', '.join(repr(l) for l in lits)}")

    # Precondition: refuse to run at all if this gate cannot prove its own leak
    # detectors work. A PASS from an unproven detector is not evidence.
    if args.selftest_interactions:
        ok_i = selftest_interaction_capture()
        ok_b = selftest_blank_page()
        sys.exit(0 if (ok_i and ok_b) else 1)

    if not selftest():
        sys.exit(2)

    routes = discover_routes(args)
    findings = []
    checked = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        for i, route in enumerate(routes):
            page = context.new_page()
            buf = install_listeners(page)
            ok = check_route(page, args.url, route, findings, buf)
            # ON BY DEFAULT, because the reveal is binding on every demo rather than a
            # nice-to-have: a build without one is a FAIL by the standard, and a gate
            # that only checks it when asked is a gate nobody asks. --no-reveal exists
            # for a surface the rule genuinely does not cover, and using it is a
            # decision somebody records rather than a default.
            # ORDER IS LOAD-BEARING: the leak scan inside check_route must finish
            # BEFORE this click, and must never re-run after it.
            #
            # The reveal is the one deliberate place ARAG branding and mechanics are
            # ALLOWED to show - that is what the standard says it is for - so its
            # contents are full of the exact strings the leak patterns hunt: "Knowledge
            # box", "/ask", "/find". Scanning the page with the sheet open would fail
            # every compliant demo for being compliant.
            #
            # Verified rather than assumed: forge-co's reveal contains "Knowledge
            # box" and the gate passes it on 19 of 19 routes. The live trap is the
            # --interactions path, which re-inspects post-interaction state with
            # navigate=False - an interactions flow that opens the reveal WOULD be
            # scanned, and the finding would be false.
            if ok and not args.no_reveal:
                check_reveal_opens(page, route, findings)
            checked.append({"route": route, "ok": ok})
            if i == 0 and args.interactions:
                run_interactions(page, args.interactions, findings)
                # Inspect the state the interaction LEFT BEHIND. navigate=False is
                # load-bearing: this used to re-goto, which threw that state away.
                ok2 = check_route(page, args.url, route, findings, buf, navigate=False,
                                  label=f"{route} [after interactions]")
                checked[-1]["ok"] = checked[-1]["ok"] and ok2
                checked.append({"route": f"{route} [after interactions]", "ok": ok2})
            page.close()
        browser.close()

    # THE VERDICT COUNTED FINDINGS, AND A NOTE IS NOT A FINDING. Both halves of a
    # DECLARED refusal came through as NOTE - the right severity, visible in the report -
    # and `not findings` still failed the run, so the flag downgraded two failures into
    # two differently-worded failures. A severity nothing reads is decoration, which is
    # this repo's own rule about a check that prints FAIL without failing the run,
    # pointed the other way: a check that prints NOTE and fails anyway.
    overall_pass = not [f for f in findings if f.get("severity") != "NOTE"]
    report = {"url": args.url, "routes_checked": checked, "findings": findings,
              "overall": "PASS" if overall_pass else "FAIL"}

    print(f"\nDemo QA gate - {args.url}")
    print(f"Routes checked: {', '.join(r['route'] for r in checked)}")
    if ROUTE_DIGESTS:
        distinct = len(set(ROUTE_DIGESTS.values()))
        print(f"Distinct page content across those routes: {distinct} of "
              f"{len(ROUTE_DIGESTS)}")
        if distinct == 1 and len(ROUTE_DIGESTS) > 1:
            print("  WARNING: every route scanned IDENTICAL text. This run checked one "
                  "page N times, whatever the route count says - the fragment did not "
                  "change what was rendered, or nothing settled before the scan.")
        elif distinct < len(ROUTE_DIGESTS):
            same: dict[str, list[str]] = {}
            for k, v in ROUTE_DIGESTS.items():
                same.setdefault(v, []).append(k)
            for v, ks in same.items():
                if len(ks) > 1:
                    print(f"  NOTE: identical content on {ks} - legitimate if those "
                          f"routes alias each other, a coverage hole otherwise.")
    # NAME WHAT WAS MEASURED, WHICH IS THE NETWORK GOING QUIET - NOT "the data arrived".
    #
    # The first version of this line said "Settled before scanning", which reads as full
    # coverage. Measured against a live build: networkidle SUCCEEDED on a route whose
    # generative content had still not appeared (5,399 chars of shell, the expected term
    # absent), while on another route the same wait took the scanned DOM from 5,399 to
    # 14,200 characters and the expected content from absent to present. Both counted as
    # settled. A surface that fetches on a later tick, or takes longer than the cap, is
    # still scanned incomplete and this line must not imply otherwise.
    _set, _unset = SETTLE["settled"], SETTLE["unsettled"]
    if _set or _unset:
        print(f"Network quiet before scanning: {len(_set)} of {len(_set) + len(_unset)} "
              f"route(s)"
              + (f"   NOT QUIET, scanned ~1.5s after load: {', '.join(_unset)}"
                 if _unset else ""))
        print("  Note: network quiet is not proof the content arrived. A route that "
              "fetches on a later\n  tick, or whose generative call outlasts the 8s cap, "
              "is scanned incomplete and this\n  gate cannot tell you which.")
    _op, _nv, _fl = REVEAL["opened"], REVEAL["navigated"], REVEAL["failed"]
    if _op or _nv or _fl:
        print(f"Reveal clicked and worked: {len(_op) + len(_nv)} of "
              f"{len(_op) + len(_nv) + len(_fl)} route(s)"
              + (f"   as a NAVIGATION rather than an overlay on: "
                 f"{', '.join(_nv)}" if _nv else ""))
    elif not args.no_reveal:
        print("Reveal check: NOT RUN on any route - treat the zero findings above as "
              "covering routes only, not the reveal.")
    if ROUTE_WAIVERS:
        print("Waiver usage:")
        for r, lits in ROUTE_WAIVERS.items():
            for lit in lits:
                n = WAIVER_USE.get((r, lit), 0)
                print(f"  {r}: {lit!r} waived {n} occurrence(s)"
                      + ("  <- UNUSED: this waiver matched nothing. Remove it; a waiver that "
                         "outlives its reason is how a hole stays open." if n == 0 else ""))
    # A DECLARED REFUSAL THAT NEVER HAPPENED IS THE FAILURE THIS FLAG EXISTS TO CATCH.
    # The leak waivers above only WARN when unused, because a waiver matching nothing is
    # untidy. This is the other way round: declaring that a role is refused and then not
    # being refused means the scoping has stopped working, so it fails the run.
    if EXPECTED_REFUSALS:
        print("Expected-refusal usage:")
        for r, pairs in EXPECTED_REFUSALS.items():
            for st, frag in pairs:
                seen = (r, st, frag) in REFUSALS_SEEN
                print(f"  {r}: HTTP {st} on {frag!r} - "
                      + ("observed" if seen else
                         "NEVER OBSERVED. Either the route was not driven in the state "
                         "that produces it, or the refusal has stopped happening - and "
                         "the second is a broken entitlement, so this fails."))
                if not seen:
                    overall_pass = False
                    findings.append({"route": r, "severity": "FAIL",
                                     "issue": f"declared refusal HTTP {st} on {frag!r} "
                                              f"never occurred"})
    if overall_pass:
        notes = [f for f in findings if f.get("severity") == "NOTE"]
        print(f"Result: PASS - {len(checked)} route(s), zero findings"
              + (f", {len(notes)} note(s):" if notes else "\n"))
        for f in notes:
            print(f"  [NOTE] {f['route']}: {f['issue']}")
        if notes:
            print()
    else:
        real = [f for f in findings if f.get("severity") != "NOTE"]
        print(f"Result: FAIL - {len(real)} finding(s):\n")
        for f in findings:
            print(f"  [{f['severity']}] {f['route']}: {f['issue']}")
        print()

    if args.json:
        Path(args.json).write_text(json.dumps(report, indent=2))
        print(f"Machine-readable report written to {args.json}")

    sys.exit(0 if overall_pass else 1)


if __name__ == "__main__":
    main()
