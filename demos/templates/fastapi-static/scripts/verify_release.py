"""Post-deploy verification for the three-fix release.

Verifies against WHAT THE SERVER SERVES, not what the commit says - a fix is not
done when the code is right, it is done when the deployed thing serves it.

    python scripts/verify_release.py https://your-app.fly.dev
"""
import json
import re
import sys
import time
import urllib.request

from playwright.sync_api import sync_playwright

ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
FLAGS = {a for a in sys.argv[1:] if a.startswith("--")}
BASE = (ARGS[0] if ARGS else "https://your-app.fly.dev").rstrip("/")


class Run:
    """Every verdict goes through check(), which PRINTS and REGISTERS in one call.

    This exists because a check in this file once printed FAIL and let the run
    exit "RELEASE VERIFIED" - the console-error check reported a real failure and
    never appended to the findings list. A check that cannot fail the build tells
    you nothing by passing. Routing every verdict through one function makes it
    structurally impossible to print a FAIL without recording it, rather than
    relying on each call site remembering to.
    """

    def __init__(self):
        self.fails = []
        self.checks = 0

    def check(self, ok, label, finding=None, note=""):
        self.checks += 1
        print(f"    {'PASS' if ok else 'FAIL'}  {label}  {note}".rstrip())
        if not ok:
            self.fails.append(finding or label)
        return ok


def selftest():
    """Positive control. A harness that has only ever passed is worth nothing."""
    ok = True
    r = Run()
    r.check(True, "control: a passing check registers nothing")
    r.check(False, "control: a failing check MUST register", "planted failure")
    if r.fails != ["planted failure"]:
        print("  SELFTEST FAIL: check() did not register a planted failure"); ok = False
    else:
        print("  PASS  a planted failure reaches the findings list and would exit non-zero")

    # And a static audit of this file: no verdict may be printed outside check().
    # check()'s own print is the one legitimate look-alike, so it is excluded by
    # POSITION rather than by pattern - a pattern loose enough to spare it would
    # be loose enough to spare a real stray.
    stray, in_helper, helper_indent = [], False, 0
    for ln in open(__file__, encoding="utf-8").read().splitlines():
        stripped = ln.lstrip()
        if stripped.startswith("def check("):
            in_helper, helper_indent = True, len(ln) - len(stripped)
            continue
        if in_helper and stripped.startswith(("def ", "class ")) \
                and (len(ln) - len(stripped)) <= helper_indent:
            in_helper = False
        if in_helper or stripped.startswith("#"):
            continue
        if "print(" in ln and ("'PASS'" in ln or '"PASS"' in ln or "SELFTEST FAIL" in ln
                               or "'FAIL'" in ln or '"FAIL"' in ln):
            if "SELFTEST" in ln:   # the selftest's own reporting is not a build verdict
                continue
            stray.append(stripped[:90])
    if stray:
        print(f"  SELFTEST FAIL: {len(stray)} verdict(s) printed outside check():")
        for x in stray:
            print("    ", x)
        ok = False
    else:
        print("  PASS  no verdict is printed outside check() - the decoration class cannot recur")
    print("\nSELFTEST " + ("PASS" if ok else "FAIL"))
    sys.exit(0 if ok else 1)

# The seven composed generative surfaces, named so the report can say WHICH.
COMPOSED = [
    ("surgeon desk", "/api/surgeon-desk", {"question": "In which procedures can Remplir be used?"}),
    ("patient guide", "/api/patient-guide", {"question": "What is Remplir and why might my surgeon use it?"}),
    ("claim check", "/api/claim-check", {"claim": "Striate+ is distributed globally by BioHorizons."}),
    ("investor digest", "/api/investor-digest", {"theme": "Regulatory and approvals"}),
    ("vac draft", "/api/vac-desk/draft", {"question": "How is Remplir manufactured, and to what quality management standards?"}),
    ("vac review", "/api/vac-desk/review", {"question": "How is Remplir manufactured, and to what quality management standards?"}),
    ("market access", "/api/market-access", {"product": "Remplir"}),
]
# The exact sentence the film has already captured under an unscoped decline.
# Held as a literal here so a change to it FAILS this run rather than silently
# invalidating footage. Do not "update" it to match a new value - if it no
# longer matches, either the change is wrong or the film must re-shoot, and
# that is a decision for the lead, not a fixture edit.
SHOT_FOOTER = ("Clinic's published material does not state this, "
               "so nothing has been generated to fill the gap.")

MARKER = re.compile(r"(?:^|[.!?:;])\s+[*•]\s+\S|\*\*|__|`[^`]")

# The sources heading, case-folded on purpose. innerText reflects CSS
# text-transform and .sect h4 is uppercase, so a case-SENSITIVE test against
# the source wording can never match what renders and passes whatever is on
# screen. Compare `text.lower()` against this, never the mixed-case literal.
SRC_HEAD = "sources read for this answer"


def post(path, payload, timeout=180):
    req = urllib.request.Request(BASE + path, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    return json.loads(urllib.request.urlopen(req, timeout=timeout).read()), time.time() - t0


def main():
    if "--selftest" in FLAGS:
        selftest()
    run = Run()

    # 1. the deployed BUNDLE, not the commit
    js = urllib.request.urlopen(BASE + "/assets/app.js", timeout=30).read().decode()
    tokens = [("DECLINE_NOTE", "served bundle carries the labelled decline footer"),
              ("splitInlineLists", "served bundle carries the shared-renderer list fix"),
              ("slowMs = 90000", "served bundle carries the asymmetric retry"),
              ("!declined && src.length", "served bundle gates the sources panel on the decline"),
              ("if (res.declined)", "served bundle carries the claim-check decline state")]
    if "--plant" in FLAGS:
        # live positive control: an expectation that cannot be satisfied
        tokens.append(("__PLANTED_TOKEN_THAT_CANNOT_EXIST__", "planted control (must FAIL)"))
    for token, what in tokens:
        run.check(token in js, what)

    # 2. every composed surface on the common path.
    # The surface list is printed BY NAME, not counted. A future reader inherits
    # the list that way - and enumerating the surfaces rather than the mechanism
    # is the check that catches a guard which covers every path but one.
    print(f"\n  the {len(COMPOSED)} composed generative surfaces this harness drives, by name:")
    for i, (name, path, _) in enumerate(COMPOSED, 1):
        print(f"    {i}. {name:16s} {path}")
    print("\n  normal round trip:")
    payloads = {}
    for name, path, body in COMPOSED:
        try:
            data, secs = post(path, body)
            payloads[name] = data
            run.check(secs <= 30, f"{name:16s} {secs:5.1f}s",
                      f"{name} took {secs:.0f}s - inside the retry budget")
        except Exception as exc:
            run.check(False, f"{name:16s} {exc}", name)

    # 3. both decline paths, labelled
    print("\n  decline labelling:")
    ref, _ = post("/api/surgeon-desk", {"question": "How does Remplir compare with a competitor "
                                                    "nerve wrap in a head-to-head randomised trial?"})
    run.check(ref.get("decline") == "not_published",
              "model refusal labelled not_published", "refusal label")
    run.check(not (ref.get("answer") or "").strip().startswith("This desk answers only"),
              "refusal payload carries its own wording", "refusal wording")
    # The FOOTER is what the film actually shot, and it is rendered client-side
    # from DECLINE_NOTE - it never appears in this payload at all. The check
    # above was labelled "film footage valid" while probing a layer the footer
    # does not live in: correctly wired, measuring the wrong thing. Verified in
    # the rendered DOM below instead.

    # 3b. a decline carries NOTHING. Three controls, because an emptiness check
    # on its own is satisfied by a fix that simply stopped returning sources.
    # The defect: a refusal came back fully composed, honestly labelled, and
    # still shipped every retrieved card. The patient desk then rendered them
    # under a heading reading "Sources read for this answer" - and the cards are
    # real patient pages that genuinely name a hospital and a surgeon, which is
    # what made a correct refusal read as the list the patient asked for.
    print("\n  a decline carries nothing:")
    POS_Q = "which hospitals near me offer this procedure?"
    pos, _ = post("/api/patient-guide", {"question": POS_Q})
    run.check(pos.get("decline") == "not_published",
              "positive control declines (patient desk, hospitals question)",
              "positive control did not decline - the control itself is invalid",
              f"got decline={pos.get('decline')!r}")
    carried = {k: v for k, v in (("sources", len(pos.get("sources") or [])),
                                 ("sentences", len(pos.get("sentences") or [])),
                                 ("statements", pos.get("statements") or 0),
                                 ("retrieved", pos.get("retrieved") or 0)) if v}
    run.check(not carried and (pos.get("confidence") or {}).get("label") == "Answer withheld",
              "positive control: no sources, sentences, statements or support reading",
              "a decline still carries payload", str(carried) if carried else "")
    # NEGATIVE control on the SAME surface. Without it, deleting the sources
    # payload outright would pass the positive control perfectly.
    neg, _ = post("/api/patient-guide",
                  {"question": "What is Remplir and why might my surgeon use it?"})
    run.check(neg.get("decline") is None and len(neg.get("sources") or []) > 0,
              f"negative control: a real patient question still returns "
              f"{len(neg.get('sources') or [])} sources",
              "negative control lost its sources - the fix is too broad")
    # LOOK-ALIKE. The lead asked for a scope withhold on the practitioner desk;
    # that desk is UNSCOPED, so a scope withhold cannot arise there and asking
    # for one would be a control that can never fire. The nearest real
    # look-alike is the same desk's own refusal: it must ALSO carry nothing,
    # while keeping a decline reason distinct from the patient desk's, because
    # collapsing the two into one event would satisfy every emptiness check
    # above and silently make the rendered footer wrong on one path. The scope
    # path itself is controlled in the rendered DOM below.
    run.check(not ref.get("sources") and not ref.get("sentences"),
              "look-alike: unscoped practitioner refusal also carries nothing",
              "practitioner desk refusal still carries sources",
              f"sources={len(ref.get('sources') or [])}")
    run.check(ref.get("scoped") is False and pos.get("scoped") is True,
              "look-alike: the two declines stay distinguishable (scoped flag intact)",
              "decline surfaces collapsed - the footer will be wrong on one path",
              f"practitioner scoped={ref.get('scoped')!r} patient scoped={pos.get('scoped')!r}")
    # The patient safety rail describes the answer it sits under, so a decline
    # cannot carry the answer-path wording. BOTH halves, because a presence-only
    # test passes a rail carrying the new sentence AND the old false one.
    psafe, nsafe = pos.get("safety") or "", neg.get("safety") or ""
    run.check("general information" not in psafe and "surgeon or treating clinician" in psafe,
              "positive control: decline rail drops the false claim, keeps the clinician route",
              "decline rail still calls a withheld answer general information from the pages",
              f"got: {psafe[:64]!r}")
    run.check("general information" in nsafe,
              "negative control: a real answer keeps the full safety rail",
              "the answer path lost its safety rail")

    # 4. rendered DOM - the list fix and the scope footer
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_context(viewport={"width": 1440, "height": 1000}).new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("console", lambda m: errs.append(m.text[:120]) if m.type == "error" else None)
        pg.goto(BASE + "/surgeon-desk", wait_until="networkidle")
        time.sleep(2)

        print("\n  rendered DOM, every composed payload through the real renderer:")
        for name, data in payloads.items():
            if "answer" not in data:
                continue
            txt = pg.evaluate("""(res)=>{const d=document.createElement('div');
                d.innerHTML=answerHTML(res,{question:'x'});document.body.appendChild(d);
                const t=d.innerText;d.remove();return t;}""", data)
            hit = MARKER.findall(txt)
            run.check(not hit, f"{name:16s} no raw markdown",
                      f"{name} renders a literal marker", str(hit[:2]) if hit else "")

        scope = {"answer": "This desk answers only from the pages Clinic publishes for patients.",
                 "decline": "scope", "scoped": True, "sentences": [], "matched": 0,
                 "statements": 0, "sources": [],
                 "confidence": {"label": "Answer withheld", "tone": "unknown", "detail": ""},
                 "retrieved": 0, "grounded_in": 0, "withheld": True}
        txt = pg.evaluate("""(res)=>{const d=document.createElement('div');
            d.innerHTML=answerHTML(res,{question:'x'});document.body.appendChild(d);
            const t=d.innerText;d.remove();return t;}""", scope)
        # BOTH halves: the new sentence present AND the old claim absent. A
        # presence-only assertion passes a page carrying both.
        run.check("The material exists" in txt and "does not state this" not in txt,
                  "scope decline shows the true footer AND not the absence claim", "scope footer")
        # The scope path is the look-alike for the rendered half: a decline for
        # the OTHER reason must also render no cards.
        run.check(SRC_HEAD not in txt.lower(),
                  "scope decline renders no sources heading", "scope decline renders sources")

        # The positive control at the layer the reader actually sees. Checking
        # the payload is empty does not establish what the renderer does with a
        # decline, and the heading is the specific harm: it asserts the cards
        # were read FOR an answer that was refused.
        CARDS = """(res)=>{const d=document.createElement('div');
            d.innerHTML=answerHTML(res,{question:'x'});document.body.appendChild(d);
            const r={text:d.innerText,cards:d.querySelectorAll('.sourcecard').length};
            d.remove();return r;}"""
        pdom = pg.evaluate(CARDS, pos)
        run.check(pdom["cards"] == 0 and SRC_HEAD not in pdom["text"].lower(),
                  "positive control: zero source cards in the rendered DOM",
                  "a decline renders source cards on screen",
                  f"cards={pdom['cards']}")
        # and the renderer must still SHOW cards on a real answer, or the
        # rendered positive control above proves only that nothing ever renders.
        # This control earned its place immediately: it FAILED on first run and
        # the cause was in the positive control, not here. innerText reflects CSS
        # text-transform, .sect h4 is uppercase, so the heading renders as
        # "SOURCES READ FOR THIS ANSWER" and a case-sensitive `not in` above was
        # passing on a string that could never have matched - a false pass that
        # would have held even with the heading on screen. Compared case-folded
        # now: the unit was wrong, so the unit is converted rather than the
        # assertion loosened.
        ndom = pg.evaluate(CARDS, neg)
        run.check(ndom["cards"] > 0 and SRC_HEAD in ndom["text"].lower(),
                  f"negative control: {ndom['cards']} source cards still render on a real answer",
                  "the renderer no longer shows sources at all")
        # The client gate is a SECOND layer, and with the server fixed it never
        # has anything to hide - so on live payloads alone it is indistinguishable
        # from not existing. This injects the state it exists for: a decline that
        # still carries sources, i.e. a future surface composing its own payload
        # without routing through declined(). Without this the second layer is
        # decoration we could not tell from a working guard.
        leak = dict(neg, decline="not_published", scoped=False,
                    answer="NOT IN PUBLISHED CONTENT - nothing states this.")
        ldom = pg.evaluate(CARDS, leak)
        run.check(ldom["cards"] == 0 and SRC_HEAD not in ldom["text"].lower(),
                  f"second layer: renderer hides {len(neg.get('sources') or [])} sources "
                  f"on an injected decline that still carries them",
                  "client gate does not hide sources on a decline",
                  f"cards={ldom['cards']}")

        # a real end-to-end drive, not just an injected payload
        pg.goto(BASE + "/surgeon-desk", wait_until="domcontentloaded")
        pg.wait_for_selector(".prompts .chip", timeout=30000)
        pg.locator(".prompts .chip").nth(1).click()
        pg.wait_for_selector(".answer-body", timeout=120000)
        time.sleep(1)
        run.check(not MARKER.findall(pg.inner_text(".answer-body")),
                  "live surgeon-desk drive renders clean", "live drive")
        # the sentence the film has on tape, read where it actually renders
        shot = pg.evaluate("""(res)=>{const d=document.createElement('div');
            d.innerHTML=answerHTML(res,{question:'x'});document.body.appendChild(d);
            const t=d.innerText;d.remove();return t;}""", ref)
        rendered = [ln.strip() for ln in shot.split("\n")
                    if "nothing has been generated" in ln.lower()]
        run.check(bool(rendered) and rendered[0] == SHOT_FOOTER,
                  "unscoped decline footer is byte-identical to the filmed sentence",
                  "unscoped footer changed - footage invalid",
                  "" if rendered and rendered[0] == SHOT_FOOTER else f"got: {rendered[:1]}")

        run.check(not errs, "no console or page errors",
                  f"{len(errs)} console/page error(s)", str(errs[:2]) if errs else "")
        b.close()

    print(f"\n  drove {len(payloads)} of {len(COMPOSED)} composed surfaces: "
          + (", ".join(payloads) or "none"))
    print(f"  {run.checks} checks ran, {len(run.fails)} failed")
    print("\n" + ("RELEASE VERIFIED - no findings" if not run.fails
                  else "FINDINGS: " + "; ".join(run.fails)))
    sys.exit(1 if run.fails else 0)


if __name__ == "__main__":
    main()
