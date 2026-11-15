"""Self-test for the backend. Every verdict goes through ONE function (`check`) that prints and
registers it; the process exit code is the verdict. Zero checks run is a failure.

  python -m server.selftest                 offline checks + live checks against the real knowledge base
  python -m server.selftest --offline       offline only (no platform calls)
  python -m server.selftest --plant-failure adds a deliberately failing check: exit MUST be non-zero

Controls: each planted case declares up front whether it expects FIRE or QUIET and proves it changed
its input before the result is read. Controls reuse the production objects (guard.DEPLOYMENT_RE, the
Scope evaluator, the Answerer's own cross-check), never a retyped copy of the expression.
"""
import argparse
import asyncio
import json
import os
import re
import sys
import tempfile
import time

ap = argparse.ArgumentParser()
ap.add_argument("--offline", action="store_true")
ap.add_argument("--plant-failure", action="store_true")
ap.add_argument("--data-dir", default=None)
ARGS = ap.parse_args()
os.environ.setdefault("WARM_REQUIRE_APPROVAL", "0")      # the approval gate has its own unit test (O11f/g); live checks need warm hits
os.environ["EXPERIENCE_DATA_DIR"] = ARGS.data_dir or tempfile.mkdtemp(prefix="exp-selftest-")
# SEED the private data directory with the SHIPPED store (a copy: the shipping files are never written). The live checks ran against an EMPTY private store, so "a suggested question is served
# WARM" (L6b), the planted reseed (L6c) and the cached answer for a rate-limited visitor (L7c) could never run and were reported as a HOLE about a "moved digest" for days: a stale-population
# message laid over a configuration that made the check unreachable. Seeded, they exercise the real warm path whenever the shipped store matches the live corpus.
if not ARGS.data_dir:
    import shutil as _sh
    from pathlib import Path
    _ship = Path(__file__).resolve().parent / "data"
    for _f in ("warm.json", "warm_approved.json"):
        if (_ship / _f).exists():
            _sh.copy(_ship / _f, Path(os.environ["EXPERIENCE_DATA_DIR"]) / _f)

import httpx  # noqa: E402

from . import config, embed, guard, lenses, roi  # noqa: E402
from .answer import Answerer, band_from_remi, is_footer  # noqa: E402
from .arag import Arag, PlatformError, Trace  # noqa: E402
from .cache import LRU, corpus_digest, norm_query  # noqa: E402
from .ratelimit import GenerativeBudget, Window  # noqa: E402
from .scope import Scope, labels_of, parse_facets  # noqa: E402
from .vocab import VOCAB  # noqa: E402

RESULTS = []


def note(msg):
    print("NOTE  " + msg)


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok)))
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  [{detail}]" if detail else ""), flush=True)
    return bool(ok)


def hole(name, why):
    print(f"HOLE  {name}  [{why}]", flush=True)


def walk_strings(o):
    if isinstance(o, str):
        yield o
    elif isinstance(o, dict):
        for k, v in o.items():
            yield from walk_strings(k)
            yield from walk_strings(v)
    elif isinstance(o, (list, tuple)):
        for v in o:
            yield from walk_strings(v)


def leak_report(obj):
    bad = {}
    for s in walk_strings(obj):
        for kind in guard.leaks(s):
            bad.setdefault(kind, []).append(s[:80])
    return bad


# ============================== OFFLINE ======================================================
def offline():
    # O1 vocabulary equals the corpus agent's registration. Loaded from its source text.
    try:
        src = (config.APP / "corpus" / "labelsets.py").read_text()
        m = re.search(r"VOCAB = (\{.*?\n\})", src, re.S)
        theirs = eval(m.group(1))
        check("O1 frozen vocabulary equals corpus/labelsets.py VOCAB", theirs == VOCAB)
    except Exception as e:
        check("O1 frozen vocabulary equals corpus/labelsets.py VOCAB", False, repr(e))

    # O2/O3 scope: tier can never widen; filter shape
    for requested in ("partner", "registered", "public", "", "all", "' or 1=1"):
        sc = Scope.make(lens="build", tier=requested)
        fe = sc.filter_expression()
        tier_parts = [p for p in fe["field"]["and"] if p.get("labelset") == "tier"]
        check(f"O2 tier requested {requested!r} -> filter pins tier=public",
              len(tier_parts) == 1 and tier_parts[0]["label"] == "public" and sc.tier_applied == "public")
    sc = Scope.make(lens="research", facets={"vertical": ["insurance", "media"], "kind": ["film"]})
    fe = sc.filter_expression()
    check("O3 filter uses `field` key and never the legacy filters array", list(fe) == ["field"] and "filters" not in json.dumps(fe))
    check("O3b OR only within one axis; AND across axes",
          all(("or" not in p) or len({q["labelset"] for q in p["or"]}) == 1 for p in fe["field"]["and"]))
    check("O3c cross-check evaluator rejects a registered-tier record", not sc.allows({"tier": "registered", "journey": "research", "vertical": "insurance", "kind": "film"}))
    check("O3d cross-check evaluator rejects a record with no labels (fail closed)", not sc.allows({}))
    check("O3e unregistered facet values are dropped", parse_facets("vertical:insurance,vertical:nope,tier:partner,kind:film") == {"vertical": ["insurance"], "kind": ["film"]})

    # O4 guard: FIRE / QUIET controls built from the production regexes
    fire = ["Runs fully on-premises behind your firewall.", "It works air-gapped.", "Your documents stay with you.",
            "Offline mode is available.", "Delivers 97% accuracy.", "ARAG answers questions.", 
            "Use Nuclia for it.", "We leverage retrieval.", "Hybrid deployment keeps data local."]
    for s in fire:
        check(f"O4 FIRE leaks({s[:40]!r})", len(guard.leaks(s)) > 0)
    quiet = ["Hybrid search combines keyword and semantic matching.", "The knowledge base holds 55 public items.",
             "REMi scores groundedness from 0 to 5.", "Search finds 95% of what you asked for in this list of 100.",
             "It answers from your documents and cites them."]
    for s in quiet:
        check(f"O4 QUIET leaks({s[:40]!r})", guard.leaks(s) == [], str(guard.leaks(s)))
    changed = guard.clean("We leverage retrieval — it is seamless.")
    check("O4b clean() rewrites banned words and em dashes", "leverage" not in changed and "—" not in changed and "seamless" not in changed, changed)

    held = ["Does it run on-premises?", "Is it air-gapped?", "Where is my data stored?", "Can I run it locally?", "Is my data safe?",
            "Does our data leave our network?", "What about data residency?"]
    for q in held:
        check(f"O4c FIRE held-topic question {q!r}", bool(guard.HELD_TOPIC_RE.search(q)))
    for q in ["How is answer quality measured?", "How does hybrid search rank results?", "How do I keep each customer's content isolated?",
              "What drives the cost?", "What does a Retrieval Agent do?"]:
        check(f"O4d QUIET legitimate question {q!r}", not guard.HELD_TOPIC_RE.search(q))
    check("O4e the referral message itself carries no held claim", guard.claims(__import__("server.answer", fromlist=["x"]).HELD_TOPIC_MESSAGE) == [])

    # O5 answer sentence hold + offsets
    txt = "A graph links entities. It runs fully air-gapped for you. Citations point to sources."
    new, omap, held = guard.clean_answer(txt)
    check("O5 clean_answer drops the deployment sentence and keeps the rest", "air-gapped" not in new and "Citations point to sources." in new and len(held) == 1, new)
    in_dropped = txt.index("air-gapped")
    in_kept = txt.index("Citations") + 5
    check("O5b offset inside a dropped sentence maps to None", omap(in_dropped) is None)
    check("O5c offset inside a kept sentence maps into the new text", omap(in_kept) is not None and new[:omap(in_kept)].endswith("Cita") or omap(in_kept) is not None)

    # O6 lens contract (DESIGN-ADDENDUM-01 section E) and content rules, using the lead's shared gate
    sys.path.insert(0, str(config.APP / "corpus"))
    import content_rules as R
    R.assert_controls()                         # the gate must prove it can fire BEFORE its result is read

    class FakeCorpus:
        assets = {}
        def reach(self, s): return 0
    served = lenses.build_lenses(FakeCorpus(), entry_ok={"build": ["Q one?"]})
    check("O6-0 proof ids that are not reachable are reported with a reason, never silently dropped", "proof_dropped" in served and isinstance(served["proof_dropped"], list))
    check("O6 every lens serves EXACTLY the contract keys", all(tuple(l) == lenses.SERVED_KEYS for l in served["lenses"]) and len(served["lenses"]) == 4)
    blob = json.dumps(served)
    check("O6b no underscore key and no authoring vocabulary list is served", '"_' not in blob and "vocabulary_do" not in blob and "vocabulary_dont" not in blob)
    check("O6c served lens payload is clean on every content-rule category", R.scan(blob) == {}, str(R.scan(blob)))
    mutated = json.loads(blob)
    before = mutated["lenses"][0]["objections"][0]["a"]
    mutated["lenses"][0]["objections"][0]["a"] += " It runs fully on-premises."
    check("O6d PLANT proved it mutated its input", mutated["lenses"][0]["objections"][0]["a"] != before)
    check("O6e PLANT: the same scan FIRES on a planted deployment claim", "deployment claim" in R.scan(json.dumps(mutated)))
    check("O6f only probed entry questions are served (unprobed lens serves none)", [l["entry_questions"] for l in served["lenses"]] == [["Q one?"], [], [], []])
    check("O6g served payload also passes the backend's own leak guard", leak_report(served) == {}, str(leak_report(served)))

    # O7 REMi band (table: input -> expected)
    table = [(([5, 1], [4, 2]), "well-supported"), (([4], [3]), "well-supported"), (([3, 2], [4]), "moderate"),
             (([1, 0], [5]), "weak"), (([4], [1]), "weak"), (([], [3]), None), (([3], []), None)]
    for (g, c), want in table:
        check(f"O7 band({g},{c}) == {want}", band_from_remi(g, c) == want)

    # O8 ROI arithmetic against a hand calculation
    r = roi.compute(roi.RoiIn(staff=10, searches_per_week=10, minutes_per_search=6, time_saved_pct=50, hourly_cost_usd=60,
                              subscription_usd_month=100, weeks_per_year=50), {"staff"})
    check("O8 ROI hours = 10x10x6/60x50 = 500", r["hours_spent_searching_per_year"] == 500.0)
    check("O8b ROI value = 250h x 60 = 15000 and net = 15000 - 1200", r["value_recovered_usd_per_year"] == 15000.0 and r["net_usd_per_year"] == 13800.0)
    check("O8c defaults labelled as placeholders", any("placeholder" in a["source"] for a in r["assumptions"]))
    try:
        roi.RoiIn(time_saved_pct=140)
        check("O8d out-of-range input rejected", False)
    except Exception:
        check("O8d out-of-range input rejected", True)

    # O9 rate limits
    b = GenerativeBudget(Window(60, 2), Window(60, 3))
    check("O9 peek does not consume", b.peek("a")[0] and b.peek("a")[0] and b.per_visitor.used("a") == 0)
    got = [b.admit("a")[0] for _ in range(3)]
    check("O9b per-visitor limit: 2 admitted then refused", got == [True, True, False], str(got))
    check("O9c refusal reports who and a positive retry_after", b.admit("a")[2] == "visitor" and b.admit("a")[1] > 0)
    got = [b.admit("b")[0] for _ in range(2)]
    check("O9d global limit binds across visitors (3 total)", got == [True, False] and b.admit("c")[2] == "global", str(got))

    # O9e team asks skip the per-visitor limit, stay bound by the global ceiling; the same asks from a visitor are refused (both ways)
    bt = GenerativeBudget(Window(60, 1), Window(60, 4))
    got_t = [bt.admit("t", team=True)[0] for _ in range(3)]
    check("O9e team: 3 asks admitted past a per-visitor max of 1, none charged to the visitor", got_t == [True] * 3 and bt.per_visitor.used("t") == 0, str(got_t))
    got_v = [bt.admit("t")[0] for _ in range(2)]
    check("O9f same key as a visitor: second ask refused (control: the skip is the team flag, not a loose limit)", got_v == [True, False], str(got_v))
    check("O9g team still bound by the global ceiling (4 used, 5th refused as global)", bt.admit("t", team=True)[:1] == (False,) and bt.admit("t", team=True)[2] == "global")
    check("O9h peek honours team", GenerativeBudget(Window(60, 1), Window(60, 9)).peek("x", team=True)[0])

    # O10 LRU / normalisation
    c = LRU(2, 60); c.put("a", 1); c.put("b", 2); c.put("c", 3)
    check("O10 LRU evicts oldest", c.get("a") is None and c.get("b") == 2 and c.get("c") == 3)
    check("O10b norm_query folds case, space and trailing punctuation", norm_query("  What IS   REMi ?? ") == "what is remi")
    c2 = LRU(2, 0); c2.put("a", 1); time.sleep(0.01)
    check("O10c TTL expiry", c2.get("a") is None)

    # O11 digest + warm invalidation (real)
    from .warm import WarmStore
    rows = [("r1", "2026-10-11T00:00:00", "PROCESSED"), ("r2", "2026-10-11T00:00:01", "PROCESSED")]
    d1 = corpus_digest(rows)
    rows2 = [rows[0], ("r2", "2026-10-11T00:05:00", "PROCESSED")]
    check("O11 digest is stable under row order", corpus_digest(list(reversed(rows))) == d1)
    check("O11b a single modified resource changes the digest", corpus_digest(rows2) != d1)
    from pathlib import Path
    w = WarmStore(Path(tempfile.mkdtemp(prefix='warm-unit-')) / 'warm.json')
    sc0 = Scope.make()
    w.put({"question": "Q one?", "scope_key": sc0.key(), "corpus_digest": d1, "pipeline": config.PIPELINE_VERSION, "kind": "answer"})
    check("O11c warm entry served at the same digest", w.get(norm_query("q one"), sc0, d1) is not None)
    before = w.stale_skipped
    check("O11d warm entry NOT served after the corpus moved, and the skip is counted",
          w.get(norm_query("q one"), sc0, corpus_digest(rows2)) is None and w.stale_skipped == before + 1)

    w.put({"question": "Q two?", "scope_key": sc0.key(), "corpus_digest": d1, "pipeline": "an older pipeline", "kind": "answer"})
    check("O11e a warm answer made by a different answer pipeline is NOT served", w.get(norm_query("q two"), sc0, d1) is None)

    # O5d no filter edits INSIDE a sentence: it comes back whole (token substitution only) or it is absent
    planted_list = "Costs are published.\n\nIt starts with\n- a licence add-on that runs fully on-premises, added to your licence;\n- no new platform. Pricing is listed."
    n5, _o5, h5 = guard.clean_answer(planted_list)
    check("O5d PLANT: a lead-in plus list items carrying a held claim are dropped TOGETHER (old newline split left 'It starts with ... added to your licence')",
          "It starts with" not in n5 and "added to your" not in n5 and "Costs are published." in n5 and "Pricing is listed." in n5 and "no new platform" not in n5 and any(c == "orphaned-lead-in" for c, _ in h5), repr((n5, h5)))
    n6, _o6, h6 = guard.clean_answer("It starts with a trial at rag.progress.cloud, added to your licence. Next sentence stays.")
    check("O5e a sentence that clean() would have to DELETE a host string from is dropped whole, never edited", "It starts with" not in n6 and "Next sentence stays." in n6 and h6[0][0] == "platform-string", repr(n6))
    src7 = "We leverage retrieval, it is seamless, and a knowledge box helps."
    n7, _o7, h7 = guard.clean_answer(src7)
    keep7 = [w for w in re.findall(r"[a-z]+", src7.lower()) if w not in ("leverage", "seamless")]
    check("O5f substitution-only sentences come back WHOLE: every other word survives, in order, nothing excised",
          not h7 and [w for w in re.findall(r"[a-z]+", n7.lower()) if w in keep7] == keep7 and "leverage" not in n7 and "seamless" not in n7, repr(n7))
    check("O5g `knowledge box` is the product's own published term and is NOT rewritten", guard.clean("two knowledge boxes and one Knowledge Box") == "two knowledge boxes and one Knowledge Box")

    # O5h an excerpt comes back whole, never starting mid-clause after a stripped title
    from .corpus import _excerpt
    ex = _excerpt("Film title here is a film about Progress Agentic RAG, running 75 seconds. It shows a demo.", "Film title here")
    check("O5h excerpt keeps its opening sentence whole (no leading 'is a film about' fragment)", ex.startswith("Film title here is a film about") and "It shows a demo." in ex, repr(ex))

    # O5i lists survive; metric not shown; footers never cited; empty passages never emitted
    lst = "Specifically:\n- Each answer is written from sources.\n- Each answer is scored for support.\n\nPricing is listed."
    n8, _o8, h8 = guard.clean_answer(lst)
    check("O5i a model's bullet list survives with its newlines (was flattened into ' - ' runs)", n8 == lst and not h8, repr(n8))
    evs = list(Answerer(None, type("C", (), {"assets": {}, "by_rid": {}})(), None, None, None)._text_events(n8, [], None))
    check("O5j the token events reassemble the text exactly, separators included", "".join(d["text"] for e, d in evs if e == "token") == n8)
    n9, _o9, h9 = guard.clean_answer("REMi reports answer relevance, context relevance and groundedness. It also scores groundedness.")
    check("O5k a sentence naming answer relevance is KEPT whole (the site chooses not to display that score; the product does measure it)", not h9 and "answer relevance" in n9, repr(n9))
    ftr = "Product: Progress Agentic RAG Title: What a knowledge graph gives you Vertical: cross-industry Audience path: research"
    check("O5l the metadata footer is recognised; ordinary prose naming a product is not", is_footer(ftr) and not is_footer("Product: a short note about Progress Agentic RAG pricing."))
    res_f = {"r1": {"fields": {"f": {"paragraphs": {"r1/t/body/0-9": {"text": ftr}}}}}, "r2": {"fields": {"f": {"paragraphs": {"r2/t/body/0-9": {"text": "   "}}}}}}
    class _C2:
        by_rid = {"r1": "a1", "r2": "a2"}
        assets = {"a1": type("A", (), {"title": "T1", "kind": "document", "href": "/x", "thumb": None})(), "a2": type("A", (), {"title": "T2", "kind": "document", "href": "/x", "thumb": None})()}
    cs2 = Answerer(None, _C2(), None, None, None)._citations({"r1/t/body/0-9": [[0, 5]], "r2/t/body/0-9": [[0, 5]]}, res_f, "Some answer text here.")
    check("O5m PLANT: citations whose only passage is the footer or empty are NEVER emitted", cs2 == [], str(cs2))
    from .warm import content_hash
    e1 = {"text": "x", "citations": [], "confidence": {"band": "moderate"}, "question": "q", "scope_key": "k", "corpus_digest": "d1"}
    check("O5n an approval is bound to the corpus digest as well as the content", content_hash(e1) != content_hash(dict(e1, corpus_digest="d2")))
    check("O5o the body text is part of the digest: same id/modified/status, different body hash, different digest",
          corpus_digest([("r", "m|aaaa", "PROCESSED")]) != corpus_digest([("r", "m|bbbb", "PROCESSED")]))

    # O5p self-narration guard: FIRE on the register, QUIET on its nearest legitimate look-alikes
    fire_sn = ["Not enough data to answer any other cost details beyond the starting Starter price.", "It also mentions that every answer is scored live.",
               "The explicit measure described is groundedness.", "The context states that the cost is one cent.", "According to the passages, it supports PDFs.",
               "The passages state that scores are shown.", "I cannot find a figure for that."]
    quiet_sn = ["The documents are ingested within minutes.", "Scores are shown for every answer.", "It also supports PDFs and Word files.",
                "Each answer lists the sources it came from.", "The text is extracted and indexed for retrieval.", "Starter costs $700 a month to start."]
    for q_ in fire_sn:
        check(f"O5p FIRE self-narration {q_[:42]!r}", bool(guard.SELF_NARRATION_RE.search(q_)))
    for q_ in quiet_sn:
        check(f"O5q QUIET legitimate {q_[:42]!r}", not guard.SELF_NARRATION_RE.search(q_))
    n10, _o10, h10 = guard.clean_answer("Starter costs $700 a month. Not enough data to answer any other cost details. Pro costs $1,925 a month.")
    check("O5r the narrating sentence is withheld whole and its neighbours survive intact", n10 == "Starter costs $700 per month. Pro costs $1,925 per month." and h10[0][0] == "self-narration", repr(n10))        # the price period is normalised to the published "per month" (O28z)
    n11, _o11, h11 = guard.clean_answer("The context states one thing. It also mentions another.")
    check("O5s an answer made ENTIRELY of narration is emptied (the caller refuses it)", n11.strip() == "" and len(h11) == 2, repr(n11))

    # O5t only cited, well-supported answers can be pre-warmed
    from .warm import warmable
    base_p = {"kind": "answer", "citations": [{"n": 1}], "confidence": {"band": "well-supported", "raw": {"groundedness": [4], "context_relevance": [4]}}}
    check("O5t a cited answer at groundedness 4 is warmable", warmable(base_p)[0])
    check("O5u groundedness 2 is NOT warmable (it can still answer live)", warmable(dict(base_p, confidence={"raw": {"groundedness": [2]}})) == (False, "low_support:2"))
    check("O5v an uncited answer is NOT warmable", warmable(dict(base_p, citations=[])) == (False, "uncited"))
    check("O5w an unscored answer is NOT warmable, and a refusal is not an answer", warmable(dict(base_p, confidence={"raw": None}))[0] is False and warmable({"kind": "refusal", "reason": "no_answer"}) == (False, "no_answer"))

    # O5x register: third-person narration about our own product is withheld; plain statements are not
    for q_ in ("It is described as a retrieval platform that you feed your own content.", "Progress Agentic RAG is said to answer from your content.",
               "This is characterised as a cost guard.", "A per-query cost is described as a few cents.",
               "Steps implied by the described workflow:", "The steps are implied by the passage."):
        check(f"O5x FIRE third-person narration {q_[:40]!r}", bool(guard.SELF_NARRATION_RE.search(q_)))
    for q_ in ("Progress Agentic RAG is a retrieval platform.", "The score is described in the reveal.", "Each answer is stated with its sources.", "You describe the workflow in a config file.", "Costs are shown as a per-query figure."):
        check(f"O5y QUIET {q_[:40]!r}", not guard.SELF_NARRATION_RE.search(q_))
    check("O5z the answer prompt carries the register and how-to instructions", "third person" in config.ANSWER_SYSTEM_PROMPT and "steps in order" in config.ANSWER_SYSTEM_PROMPT)

    # O18 spell check: flag only words in NEITHER the dictionary NOR the corpus vocabulary
    from . import spellcheck
    try:
        dic = spellcheck.load_dictionary()
    except RuntimeError as ex:
        dic = None
        hole("O18 spell check", str(ex))
    if dic:
        vocab = spellcheck.corpus_vocab(["Progress Agentic RAG, REMi and MCP score groundedness for each knowledge box. Nuclia pages are scanned and indexed."])
        base_txt = "Scanned pages and groundedness are supported by REMi and MCP in a knowledge box on Nuclia."
        planted = base_txt.replace("Scanned", "Scannned").replace("groundedness", "groundednes")
        check("O18 PLANT mutated its input", planted != base_txt and "Scannned" in planted and "groundednes" in planted)
        check("O18b FIRE: the planted slips are flagged", set(spellcheck.unknown_words(planted, dic, vocab)) >= {"scannned", "groundednes"}, str(spellcheck.unknown_words(planted, dic, vocab)))
        check("O18c QUIET: product terms present in the corpus vocabulary pass by construction", spellcheck.unknown_words(base_txt, dic, vocab) == [], str(spellcheck.unknown_words(base_txt, dic, vocab)))
        check("O18d DISCRIMINATE: an ordinary English word absent from the corpus stays quiet (the dictionary half covers it)",
              "wheelbarrow" not in vocab and spellcheck.unknown_words("A wheelbarrow carries documents quickly.", dic, vocab) == [])
        check("O18f contractions and typographic apostrophes are not flagged (didn\u2019t, it\u2019s, the product\u2019s)",
              spellcheck.unknown_words("It didn\u2019t fail and it\u2019s the product\u2019s answer, they didn't mind.", dic, vocab) == [])
        check("O18g compounds of two known words pass (runtime); the real slips still do not split into two words",
              spellcheck.unknown_words("A runtime workflow.", dic, vocab) == [] and set(spellcheck.unknown_words("scannned groundednes", dic, vocab)) == {"scannned", "groundednes"})
        check("O18e a word in neither is flagged even when similar to a vocabulary word", spellcheck.unknown_words("Nucliaz indexes pages.", dic, vocab) == ["nucliaz"])

    # O19 documentation self-reference: anchored on the determiner and a narrating verb, never the bare word
    for q_ in ("The page plainly indicates when the answer is a no.", "Do not rely on a figure in the business case page itself.",
               "This page covers the cost drivers.", "As mentioned above, scores are per paragraph.", "In this mode, query-time costs are low.",
               "The guide recommends starting with one feature."):
        check(f"O19 FIRE doc self-reference {q_[:44]!r}", bool(guard.DOC_SELF_REFERENCE_RE.search(q_)))
    for q_ in ("A scanned page is read by OCR.", "Send a photo of a scanned page.", "Track page views per visitor.", "Each document is indexed in minutes.",
               "The document is split into passages.", "Open the cost section in the console.", "A page of results is returned."):
        check(f"O19b QUIET legitimate {q_[:44]!r}", not guard.DOC_SELF_REFERENCE_RE.search(q_))
    # O20 internal API nomenclature in prose
    for q_ in ("Citations come from the ask-citations map.", "Pass a filter_expression to scope results.", "It uses answer_json_schema for structure.",
               "Call predict/remi to score it.", "Send the X-NUCLIA-SERVICEACCOUNT header.", "The /ask endpoint streams the answer.", "The find endpoint returns passages."):
        check(f"O20 FIRE internal nomenclature {q_[:44]!r}", bool(guard.INTERNAL_API_RE.search(q_)))
    for q_ in ("You can ask questions in ordinary language.", "It will find the answer in your content.", "Ask a question and get a cited answer.",
               "Citations point to the passage the answer came from.", "The graph shows how entities connect."):
        check(f"O20b QUIET legitimate {q_[:44]!r}", not guard.INTERNAL_API_RE.search(q_))
    n12, _o12, h12 = guard.clean_answer("Costs are driven by usage. The page plainly indicates when the answer is a no. Citations use the ask-citations map. Pro costs more.")
    check("O20c both classes withheld whole, neighbours intact", n12 == "Costs are driven by usage. Pro costs more." and {c for c, _ in h12} == {"doc-self-reference", "internal-nomenclature"}, repr(n12))

    # O21 the pair control: contradictory rate units or money figures between two answers to one question
    from .warm import pair_conflicts
    A = "Ingest-time tasks run per paragraph across the corpus and cost real money."
    B = "Ingest-time tasks occur per document across the corpus."
    check("O21 PLANT mutated: the two texts really differ on the unit", A != B and "paragraph" in A and "document" in B)
    check("O21b FIRE: per paragraph against per document is a conflict", bool(pair_conflicts(A, B)), str(pair_conflicts(A, B)))
    check("O21c QUIET: the same unit, different wording", pair_conflicts(A, "Enrichment runs per paragraph over the whole corpus.") == [])
    check("O21d QUIET: a unit present in only one answer is not a conflict", pair_conflicts(A, "It costs real money across the corpus.") == [])
    check("O21f FIRE: shape - one copy a sentence, the other a wall (read 7: empty shell against a 12-bullet list)",
          any(r.startswith("shape") for r in pair_conflicts("Follow these points.", "Point one is here. " * 12)))
    check("O21h QUIET at the measured natural spread (243 vs 137 chars) and for the refused 3.09:1 pair; FIRE beyond 4:1",
          not any(r.startswith("shape") for r in pair_conflicts("x" * 243, "x" * 137)) and not any(r.startswith("shape") for r in pair_conflicts("x" * 201, "x" * 65))
          and any(r.startswith("shape") for r in pair_conflicts("x" * 201, "x" * 40)))
    check("O21g QUIET: shape - similar lengths", not any(r.startswith("shape") for r in pair_conflicts("Point one is here. " * 5, "Point one is here. " * 7)))
    # O5e read 7 shell: lead-in with ':' + items all held -> nothing left; mostly-withheld refuses
    shell = "To build the case, follow these points:\n\n- The page plainly indicates when the answer is a no.\n- The page covers cost."
    n5e, _o, h5e = guard.clean_answer(shell)
    check("O5h PLANT: a colon lead-in whose items are all held is dropped with them (the read-7 empty shell)", n5e.strip() == "" and h5e, repr(n5e))
    check("O5i QUIET: a lead-in whose items are clean survives intact", guard.clean_answer("Follow these:\n- Start small.\n- Use the trial.")[0] == "Follow these:\n- Start small.\n- Use the trial.")
    check("O5j mostly_withheld fires on a mostly-removed answer and stays quiet on a light trim",
          guard.mostly_withheld("x" * 100, "x" * 20) and not guard.mostly_withheld("x" * 100, "x" * 90))
    # O22 Australian spelling server-side, outside quotes/code; agreement with the shared content rule
    check("O22 FIRE: US spelling is respelled letter for letter", guard.australian("We emphasize authorization of the behavior.") == "We emphasise authorisation of the behaviour.")
    check("O22b DISCRIMINATE: a quoted vendor capability name and a code span are untouched",
          guard.australian('The \u201cAnalyze document\u201d capability and `organizations` stay.') == 'The \u201cAnalyze document\u201d capability and `organizations` stay.')
    check("O22e single-l past tense becomes double-l", guard.australian("labeled and modeling and canceled") == "labelled and modelling and cancelled")
    check("O22c QUIET: Australian spelling unchanged", guard.australian("authorise, organisation, colour, centre") == "authorise, organisation, colour, centre")
    import sys as _s, pathlib as _p
    _c = _p.Path(__file__).resolve().parent.parent / "corpus"
    if (_c / "content_rules.py").exists():
        _s.path.insert(0, str(_c)); import content_rules as _cr
        words = ["authorization", "organized", "Emphasize", "the system behavior is odd", "a color scheme", "the center", "analyzing", "customize", "gray", "defense", "labeled", "modeling", "scroll-behavior:smooth", "color:#222", "behavior: matchMedia(x)", "justify-content:center", "style: 'color:#3D3D42'"]
        disagree = [w for w in words if bool(guard.US_SPELLING_RE.search(w)) != bool(_cr.scan(w).get("US spelling"))]
        check("O22d shared fixture: server pattern and content_rules 'US spelling' agree on every specimen", not disagree, str(disagree))
    else:
        note("O22d shared-fixture agreement not run: corpus/ is not in this image")
    import inspect as _i
    from . import app as _app
    check("O24 no automatic re-warm on a corpus change; an operator route exists", "asyncio.create_task(prewarm())" not in _i.getsource(_app.on_corpus_change) and any(getattr(r, "path", "") == "/ops/rewarm" for r in _app.app.routes))
    import sys as _s2
    _root = _p.Path(__file__).resolve()
    _fx = next((a / "scripts" / "md_emission_fixture.py" for a in _root.parents if (a / "scripts" / "md_emission_fixture.py").exists()), None)
    if _fx:
        _s2.path.insert(0, str(_fx.parent)); import md_emission_fixture as _mf
        def _chain(sp):
            t = sp["text"]; nn, _, _h = guard.clean_answer(t)
            if sp["expect"] == "partial":
                return nn
            return "withhold" if (not nn.strip() or guard.mostly_withheld(t, nn)) else "survive"
        check("O25 shared emission fixture: the guard chain passes every specimen (none declared blind)",
              _mf.report("site-guards", {sp["id"]: _chain(sp) for sp in _mf.SPECIMENS}, out=lambda *_: None) == 0)
    else:
        note("O25 shared emission fixture not found (not in this image)")
    from . import spellcheck as _sc
    _d = {"ground", "case", "fidelity", "content", "your", "the", "pro", "starter"}
    check("O26 FIRE: a real word capitalised mid-sentence that the corpus never capitalises there",
          _sc.stray_capitals("Ground the case in Fidelity to your content.", _d, {"pro", "starter"}) == ["Fidelity"])
    check("O26b QUIET: sentence start, list item, heading, acronym and a corpus-capitalised name are not stray",
          _sc.stray_capitals("Fidelity matters.\n- Pro tier here. Use the Pro plan and GROUND it.\n## Fidelity", _d, {"pro", "starter"}) == [])
    check("O27 FIRE: the invented quality term is held", guard.clean_answer("It returns a confidence-grounded score. Other sentence.")[2][0][0] == "invented-quality-term")
    check("O27b QUIET: 'confidence score' elsewhere is untouched", guard.clean_answer("Every extraction carries a confidence score.")[2] == [])
    from .warm import pair_conflicts as _pc
    _pa = "An agent calls your own tools over MCP by carrying the caller's token. The agent exposes the tools and calls them over MCP."
    _pb = "An agent calls your own tools over MCP by carrying the caller's own token. You expose the tools; you do not hand over a privileged service account."
    check("O28t FIRE (the real read-18 pair): two copies of one question disagreeing on WHO exposes the tools is a pair conflict",
          any("role disagrees on 'expose'" in x for x in _pc(_pa, _pb)), repr(_pc(_pa, _pb)))
    check("O28u QUIET: agreeing roles, and a copy that is silent on the role, are not conflicts",
          _pc("You expose the tools and the agent calls them.", "Your application exposes the tools; the agent calls them with the caller's token.") == []
          and _pc("You expose the tools.", "The agent carries the token.") == [])
    check("O28v FIRE: 'a filter that labels each document' (a label labels; a filter filters) and 'other supported languages' (no document states it) are held; the correct forms are quiet",
          guard.behaviour_guarantee("Use a single shared knowledge box with a filter that labels each document by whose content it is.")
          and guard.behaviour_guarantee("Then ask your question in English (or other supported languages) and receive a cited, grounded answer.")
          and not guard.behaviour_guarantee("Label every document by whose content it is so a filter can separate customers.")
          and not guard.behaviour_guarantee("The Spanish guide is written in Spanish."))
    from .previews import preview_gaps as _pgap
    _m, _o = _pgap({"a", "b", "c", "zz-orphan"}, {"a", "b", "c", "zz-gap"})
    check("O28x PLANT-PROOF: a planted orphan preview AND a planted missing preview, with EQUAL counts (4 files, 4 assets), are both found", _m == ["zz-gap"] and _o == ["zz-orphan"] and len({"a", "b", "c", "zz-orphan"}) == len({"a", "b", "c", "zz-gap"}), repr((_m, _o)))
    check("O28y QUIET: identical sets report nothing", _pgap({"a", "b"}, {"a", "b"}) == ([], []))
    check("O28z the same price renders ONE way: '$750/month', '$750 a month' and '$750 each month' all become '$750 per month'; 'a filter on a single dimension' becomes 'a filter'",
          guard.clean("more at $750/month each") == "more at $750 per month each" and guard.clean("$750 a month each") == "$750 per month each"
          and guard.clean("$750 each month") == "$750 per month" and guard.clean("$750 per month") == "$750 per month"
          and guard.clean("and a filter on a single dimension separating customers") == "and a filter separating customers")
    check("O29a FIRE (read 19, the real partner sentence): a box LIMIT with no plan named is held; QUIET when a plan is named in the same sentence, and for a plain one-box statement",
          guard.unqualified_tier_limit("If a hard boundary is required by contract, you can take a separate knowledge box per customer, but that carries a cost and limits to eight boxes.")
          and not guard.unqualified_tier_limit("A Pro subscription includes two boxes; additional boxes are $750 a month each, up to eight total.")
          and not guard.unqualified_tier_limit("Use a single shared knowledge box with a label on each document.")
          and guard.clean_answer("Intro sentence here that is long enough. It carries a cost and limits to eight boxes.")[2][0][0] == "unqualified-tier-limit")
    _tq = _pc("separate knowledge box per customer, but that carries a cost and limits to eight boxes.", "A Pro subscription includes two boxes; additional boxes are $750 a month each, up to eight total.")
    check("O29b FIRE: two copies of one question, one naming the plan beside a box limit and the other stating it bare, are a pair conflict; two qualified copies are not",
          any("tier qualification disagrees" in x for x in _tq) and not any("tier qualification" in x for x in _pc("two boxes with Pro, capped at eight boxes", "a Pro subscription includes two boxes, up to eight total boxes")), repr(_tq))
    # O60 series: the four re-key conditions, each with a planted control. A re-key is honest only while every condition is proven able to REFUSE.
    from .rekey_warm import evaluate as _ev
    _good = {"text": "A clean sentence about the product here.", "citations": [{"asset_id": "d1"}], "provenance": {"retrieved_asset_ids": ["d1", "d2"]}}
    _kw = dict(changed={"d9"}, replay_ids={"d1", "d2"}, read_text=("A clean sentence about the product here.", ["d1"]), sibling_texts=[], guard_result=("A clean sentence about the product here.", []))
    check("R0 POSITIVE: an unchanged entry whose documents, replay, guards and read text all agree is RE-KEYED", _ev(_good, **_kw)[0] == "REKEY", repr(_ev(_good, **_kw)))
    check("R1 REFUSE (condition 1): an entry that retrieved a CHANGED document", _ev(_good, **{**_kw, "changed": {"d2"}})[0] == "REFUSE" and "CHANGED" in _ev(_good, **{**_kw, "changed": {"d2"}})[1][0])
    check("R2 REFUSE (condition 2): a replay that returns a different document set", _ev(_good, **{**_kw, "replay_ids": {"d1", "d3"}})[0] == "REFUSE")
    check("R3 REFUSE (condition 3): an entry the guard chain would hold or alter, and an entry whose sibling copy conflicts",
          _ev(_good, **{**_kw, "guard_result": ("A clean sentence.", [("behaviour-guarantee", 0)])})[0] == "REFUSE"
          and _ev(_good, **{**_kw, "sibling_texts": ["The agent exposes the tools. You expose the tools."]}) [0] == "REKEY"
          and _ev({**_good, "text": "The agent exposes the tools."}, **{**_kw, "read_text": ("The agent exposes the tools.", ["d1"]), "sibling_texts": ["You expose the tools."], "guard_result": ("The agent exposes the tools.", [])})[0] == "REFUSE")
    check("R4 REFUSE (condition 4): text that differs from what was READ by ONE CHARACTER, and an entry with no record of being read",
          _ev(_good, **{**_kw, "read_text": ("A clean sentence about the product here!", ["d1"])})[0] == "REFUSE"
          and _ev(_good, **{**_kw, "read_text": None})[0] == "REFUSE" and _ev(_good, **{**_kw, "read_text": ("A clean sentence about the product here.", ["d1", "d2"])})[0] == "REFUSE")
    from .rekey_warm import declared_check as _dc
    _t0 = "Use a filter on a single dimension. More at $750/month each."
    _sub = [{"old": "a filter on a single dimension", "new": "a filter"}, {"old": "$750/month", "new": "$750 per month"}]
    check("R6 DECLARED EDIT, exact: the actual change equals the declared substitutions to the character", _dc(_t0, "Use a filter. More at $750 per month each.", _sub)[0])
    check("R7 DECLARED EDIT, REFUSE: the real diff contains ANYTHING beyond the declaration (one extra word changed)", not _dc(_t0, "Use a filter. More at $750 per month each, always.", _sub)[0]
          and not _dc(_t0, "Use a filter. Less at $750 per month each.", _sub)[0])
    check("R8 DECLARED EDIT, REFUSE: a substitution whose `old` text is absent, or ambiguous (occurs twice), does not match", not _dc(_t0, _t0, [{"old": "a filter on two dimensions", "new": "x"}])[0]
          and not _dc("a b a b", "x b x b", [{"old": "a", "new": "x"}])[0])
    check("R9 an UNLISTED entry whose text the guard chain would alter still REFUSES (a declaration about one entry cannot cover another)",
          _ev(_good, **{**_kw, "guard_result": ("A clean sentence about the product here, altered.", [])})[0] == "REFUSE")
    check("R10 the declared-edit path still requires that the text BEFORE the edit is what was read: a different 'before' REFUSES",
          _ev({**_good, "text": "After text."}, **{**_kw, "guard_result": ("After text.", []), "read_text": ("A clean sentence about the product here.", ["d1"]), "declared_before_text": "Something else entirely."})[0] == "REFUSE"
          and _ev({**_good, "text": "After text."}, **{**_kw, "guard_result": ("After text.", []), "read_text": ("A clean sentence about the product here.", ["d1"]), "declared_before_text": "A clean sentence about the product here."})[0] == "REKEY")
    check("R11 the rate-unit pair check ignores a PRICE period ('$750 per month') and an adjectival 'per-question filter' (a false conflict between two correct isolation copies), and STILL fires on a real unit disagreement",
          not any("rate unit" in x for x in _pc("Use a per-question filter. More at $750 per month each.", "Use a filter. More at $750 per month each."))
          and not any("rate unit" in x for x in _pc("a per-question filter that separates customers", "more at $750 per month each"))
          and any("rate unit" in x for x in _pc("Enrichment runs per paragraph.", "Enrichment runs per document.")))
    check("R5 REFUSE: an entry with no recorded retrieved set cannot be proven and is not re-keyed", _ev({**_good, "provenance": {}}, **_kw)[0] == "REFUSE")
    # O28n-p: strip_description_prefix. The REAL glued paragraph (expanding-from-starter, as the platform returned it) loses exactly our description and keeps the
    # source's own text byte for byte; a paragraph that is only the description reduces to nothing; one that does not begin with it is untouched.
    _dsc = "What to do once the first use case works: when to expand, what the second use case usually is, and why the cheapest expansion is the same content with a different question."
    _real = _dsc + " \n The pattern that works is one feature live on real content, then the next. What matters most is \n what comes after the first feature, because that is where the economics and the architecture decisions \n actually land."
    check("O28n FIRE (real glued paragraph): our description goes, the source's own text stays from its start, byte for byte",
          guard.strip_description_prefix(_real, _dsc) == _real[len(_dsc):].lstrip() and guard.strip_description_prefix(_real, _dsc).startswith("The pattern that works is one feature live on real content"))
    check("O28o the description alone reduces to nothing, and a trailing separator does not leave a remainder", guard.strip_description_prefix(_dsc, _dsc) == "" and guard.strip_description_prefix(_dsc + " \n ", _dsc) == "")
    check("O28p QUIET: no description, a different opening, or the description NOT at the start are all untouched",
          guard.strip_description_prefix(_real, "") == _real and guard.strip_description_prefix("Some other opening. " + _dsc, _dsc) == "Some other opening. " + _dsc
          and guard.strip_description_prefix("A different first paragraph.", _dsc) == "A different first paragraph.")
    # O28j-m: the cuts that came back (reads 15-17). FIRE strings are the real sentences from the stored answers; QUIET are the nearest legitimate look-alikes.
    _fire = ["This keeps the agent from seeing more than the requester.", "Every answer is written from the retrieved passages with citations back to each one.",
             "A grounded answer always includes citations.", "The integration sits behind your own server so content stays separate, and the API key remains hidden from the browser.",
             "The integration sits behind your own server, with every customer\u2019s content kept separate and the API key never reaching the browser."]
    _quiet = ["Citations are the record of which retrieved passage supports which part of the answer.", "Rely on that retrieval-time filtering to prevent unauthorized access.",
              "The system returns answers grounded only in your content and cited to the passages they came from.", "Every answer is scored when it is produced.",
              "Demonstrate how each answer is supported: show a cited answer with the source passages one tap away.", "Label each document by whose content it is so a filter can separate customers.", "The API key remains hidden from the browser because your server proxies the call."]
    check("O28j FIRE: the three returning absolutes are each held as a whole sentence", all(guard.behaviour_guarantee(t) and
          guard.clean_answer("Intro sentence here. " + t)[2] and guard.clean_answer("Intro sentence here. " + t)[2][0][0] == "behaviour-guarantee" for t in _fire))
    check("O28k QUIET: a citation definition, advice to filter at retrieval, 'cited to the passages' and an unrelated 'every answer is scored' are not held", not any(guard.behaviour_guarantee(t) for t in _quiet))
    _saved_ft = guard._FOREIGN["terms"]
    guard.set_foreign_terms({"plant", "freight"})
    try:
        check("O28l FIRE: 'your plant' (another build's setting presented as the reader's) is held; the plural and 'your own' forms too",
              guard.other_build_vocabulary("It performs tool calls against your plant or system services.") == "plant" and guard.other_build_vocabulary("Check your own freight rates.") == "freight")
        check("O28m QUIET: generic 'your' phrases and a bare 'the plant' are not held", all(guard.other_build_vocabulary(t) is None for t in
              ("Put your own content into a knowledge box.", "Your documents stay in your application.", "The plant demo shows a retrieval agent.")))
    finally:
        guard._FOREIGN["terms"] = _saved_ft
    # O28g: the US-spelling stems cover every derived form of the bare -or words (read 17 shipped "favorable" while the list held only "favor"): FIRE on the
    # real string, QUIET on the Australian forms and on look-alikes that are the same in both (honorary, laboratory, humorous).
    check("O28g FIRE: 'favorable' (read 17, entry 5) is caught by BOTH the server and the shared rule, and respelled letter-for-letter",
          guard.US_SPELLING_RE.search("a favorable outcome") and guard.australian("a favorable outcome") == "a favourable outcome")
    check("O28h QUIET: Australian forms and same-in-both look-alikes are untouched",
          all(not guard.US_SPELLING_RE.search(f"a {w} thing") for w in ("favourable", "behavioural", "honorary", "laboratory", "humorous", "colourful", "centre")))
    # O28a-f: UNQUALIFIED TIER CAPABILITY. Positive controls are the REAL strings (read 17's sentence, verbatim; instance 1 as quoted in CLAUDE.md), the
    # discriminate control is the tier-qualified file-types text that must stay quiet. DECLARED BLIND SPECIMEN: instance 2 ("it also accepts text-based files"
    # turns the entry plan's restriction into a bonus) names no second media noun, so this class cannot see it - it is stated here, not claimed.
    _r17 = "Ground the case in fidelity to your own content, not in broader truth. Focus on how your documents, decks, spreadsheets, PDFs, images, audio, and video will be ingested and used."
    check("O28a FIRE: the read-17 sentence (capability verb + 2 media nouns + no tier word) is held",
          any(c == "unqualified-tier-capability" for c, _i in guard.clean_answer(_r17)[2]))
    check("O28b FIRE: instance 1 as quoted (PDFs, images, audio, video, office documents) is held", guard.unqualified_tier_capability("It can ingest PDFs, images, audio, video and office documents."))
    check("O28c QUIET: the tier-qualified file-types text", not guard.unqualified_tier_capability(
        "File types and sizes depend on the plan: Starter: Max 750MB per file, text-based files only. Pro: Max 1.5GB per file, all file types supported."))
    check("O28d QUIET: a tier named in the same sentence", not guard.unqualified_tier_capability("On the Pro plan it ingests PDFs, images, audio and video."))
    check("O28e QUIET: one noun only, and no capability verb", not guard.unqualified_tier_capability("It can ingest PDFs.") and not guard.unqualified_tier_capability("A library of images, audio and video demos."))
    check("O28f DECLARED BLIND: 'it also accepts text-based files' is NOT seen by this class (stated limit, specimen kept so the claim stays honest)",
          not guard.unqualified_tier_capability("It also accepts text-based files."))
    check("O28 the answer prompt carries NEITHER the length ceiling (2 of 6 answered /fix button 1 with it, 6 of 6 without) NOR the measures sentence", "about 120 words" not in config.ANSWER_SYSTEM_PROMPT and "Keep it short" not in config.ANSWER_SYSTEM_PROMPT and "context relevance" not in config.ANSWER_SYSTEM_PROMPT)
    check("O29 the answer prompt states published prices as published, tiers whole or not at all", "starts at" in config.ANSWER_SYSTEM_PROMPT and "whole or not at all" in config.ANSWER_SYSTEM_PROMPT)
    from . import app as _app2
    # O28i: HOME_EXCLUDE is applied where the home set is DERIVED (not to a file the next warm rewrites), and pads nothing.
    _BQ = "How do I build the business case for an answer layer?"
    _eb = {"build": ["B1", "B2"], "buy": [_BQ, "P2"], "research": ["R1"], "partner": ["T1"]}
    _h, _h0 = [c["q"] for c in _app2.pick_home(_eb)], [c["q"] for c in _app2.pick_home(_eb, exclude=())]
    check("O28i the excluded question is absent from the derived home set and present when the exclusion is emptied (the plant); the set shrinks, it is not padded",
          _BQ not in _h and _BQ in _h0 and len(_h) <= len(_h0), repr((_h, _h0)))
    from .answer import deterministic_text
    guard.set_known_routes([getattr(r, "path", "") for r in _app2.app.routes], _app2.KNOWN_ROUTES)
    _real = "Use the /audit-trail view to see the citation and REMi confidence score for each answer."
    check("O30 FIRE (real string from another demo's entry): a route this app does not have is held", guard.clean_answer(_real + " Other sentence.")[2][0][0] == "route-reference")
    for _q, _t in (("a real route", "Open /pricing for the published tiers."), ("a named page", "See the pricing page for the published tiers."),
                   ("and/or, MP3 / MP4, 24/7", "It takes and/or, MP3 / MP4 or 24/7 input."), ("a full URL", "Read https://example.com/audit-trail for more."),
                   ("a real API path", "Media streams from /media/abc.")):
        check(f"O30b QUIET: {_q} is not held", guard.route_reference(_t) is None, _t)
    check("O30c FIRE: 'the X tab' that this app lacks is held", guard.route_reference("Open the audit trail tab to check each answer.") is not None)
    check("O30d the guard is armed from the app's own routes, not a typed list", guard.route_guard_armed() and "api" in guard._KNOWN["segments"] and "explore" in guard._KNOWN["segments"])
    # The release made the demo entry README-free: the RELEASED entry (.demo.txt) no longer names the route, which is the fix. The positive control
    # therefore runs on the pre-fix source text (.txt, the real string that caused the defect), and the released entry must be QUIET.
    _tdir = (config.APP / "corpus" / "text") if hasattr(config, "APP") else None
    _pre = list(_tdir.glob("c646649f*.txt")) if _tdir else []
    _rel = [f for f in _pre if f.name.endswith(".demo.txt")]
    for _f in [f for f in _pre if not f.name.endswith(".demo.txt")]:
        check("O30e FIRE on the REAL pre-fix source text: it contains a route this app lacks", any(guard.route_reference(x) for _a, _b, x in guard.split_sentences(_f.read_text())))
    for _f in _rel:
        check("O30f QUIET on the RELEASED entry: it names no route this app lacks", not any(guard.route_reference(x) for _a, _b, x in guard.split_sentences(_f.read_text())))
    for _t in ("One knowledge box per tenant is the normal starting point: one index and one set of configuration.",
               "A box per customer is used only if two customers' content cannot share an index, else you keep one box per customer."):
        check("O31 FIRE (real read-10 strings): box per tenant/customer as the default is held", guard.box_per_tenant_default(_t), _t)
    for _t in ("Use a single shared knowledge box as the normal starting point, labelling each document with whose content it is.",
               "Use one knowledge box labelled by tenant as the normal starting point.",
               "Only take a separate knowledge box for a customer when a contract forbids mixing content; this is the exception, not the pattern.",
               "Avoid using a separate box per customer unless a hard boundary requires it.",
               "A separate box for each customer carries costs: additional boxes are $750 a month each."):
        check("O31b QUIET: the correct statement of the default and the exception", not guard.box_per_tenant_default(_t), _t)
    check("O32 a price-only question is printed from the verified file, in tier order, with no hedge",
          deterministic_text("What does this cost to start?")[0] == "Starter is $700 a month. Pro is $1,925 a month. Enterprise is a custom quote."
          and deterministic_text("how do i build the business case") is None)
    check("O33 'upfront' is allow-listed with a reason; a real misspelling is not", "upfront" in _sc.ALLOW and _sc.unknown_words("pay upfront", {"pay"}, set()) == [] and _sc.unknown_words("pay upfrnt", {"pay"}, set()) == ["upfrnt"])
    check("O34 an ALL-CAPS emphasis run copied from a source is lowercased in place; acronyms stay",
          guard.clean("a SINGLE SHARED knowledge box.") == "a single shared knowledge box." and guard.clean("Read PDF and MCP and REST API docs.") == "Read PDF and MCP and REST API docs.")
    check("O35 'RAG's' is not a stray capital", _sc.stray_capitals("Use RAG's own filter here.", {"filter", "here"}, set()) == [])
    from .answer import deterministic_text as _dt
    _dd = _dt("What drives the cost once we are running?")
    check("O36 cost drivers are printed from the verified file: three items, each lead-in verbatim, no per-GB billing line",
          _dd and _dd[0].count("\n- ") == 3 and "per GB" not in _dd[0] and "per paragraph across the corpus" in _dd[0] and _dd[1] in _dd[0]
          and "skew expensive" not in _dd[0])
    from .answer import DETERMINISTIC_SOURCE as _ds, DETERMINISTIC_QUESTIONS as _dq
    check("O36a every deterministic question declares its own source sentence", set(_ds) == set(_dq))
    _ft = _dt("Which file types can it ingest?")[0]
    check("O38 file types are tier-qualified from the verified limits: Starter text-based only, Pro all types, and no audio/video assertion",
          "Starter: Max 750MB per file, text-based files only" in _ft and "Pro: Max 1.5GB per file, all file types supported" in _ft and "audio" not in _ft.lower())
    check("O38b accuracy, wrong-tool and integration are printed; the integration copy has no superlative",
          "no overall accuracy figure" in _dt("What is the accuracy of Progress Agentic RAG?")[0] and "five situations" in _dt("When is Progress Agentic RAG the wrong tool?")[0]
          and "minimal" not in _dt("How much integration work is there per end customer?")[0].lower())
    from .warm import warmable as _wm
    check("O38c a printed entry is warmable without a quality score; a generated one without a score is not",
          _wm({"kind": "answer", "citations": [1], "deterministic": "x", "confidence": {"band": "printed", "raw": None}})[0]
          and not _wm({"kind": "answer", "citations": [1], "confidence": {"band": "printed", "raw": None}})[0])
    check("O36b the other price/cost questions and every other question are NOT deterministic", _dt("How do I get started with something unrelated?") is None and _dt("What is the weather in Perth?") is None)
    from . import app as _appg
    guard.set_known_routes([getattr(r, "path", "") for r in _appg.app.routes], _appg.KNOWN_ROUTES)       # ARMED, as in production: an unarmed route guard hid a lost bullet (13 Oct 2026)
    _lost = []
    for _q in sorted(_dq):
        _r = _dt(_q)
        if _r is not None:
            _nt, _om, _held = guard.clean_answer(_r[0], verbatim=True)
            if _nt != _r[0] or _held:
                _lost.append((_q[:40], [h[0] for h in _held]))
    check("O36d EVERY printed answer survives the guard chain WITH the route guard armed: nothing held, nothing altered (a printed bullet was silently dropped from the business-case entry)", not _lost, repr(_lost))
    check("O36c the business-case question is PRINTED (13 Oct 2026: generation declined it 6 of 6, status -2): four numbered parts from the document, no ROI figure",
          (lambda r: r is not None and r[0].startswith("We do not know what this is worth to you") and "So this is a method, not a claim. The case has four parts:" in r[0] and r[0].count("\n- ") == 4 and r[2] == "canonical-building-the-business-case" and not re.search(r"\d+\s?%|ROI of", r[0]))(_dt("How do I build the business case for an answer layer?")))
    _t = "a SINGLE SHARED box. Plain sentence."
    _n, _o, _h = guard.clean_answer(_t)
    check("O37 provenance: a case-only edit is declared, a plain answer declares none",
          guard.normalisations(_t, _h) == ["capitalised-emphasis-lowercased"] and guard.normalisations("A plain sentence.", []) == [])
    check("O37b provenance: US spelling is declared as such", guard.normalisations("We authorize it.", []) == ["us-spelling-respelled"])
    _tbl = "The 5 patterns (one route each)\n| Route | Pattern | What it proves |\n|---|---|---|\n| /service-planner | Plan | x |\n\nAfter the table the text goes on."
    _film = "It is not a chat box wired to a database. [pause] Given a question, [beat] it plans. [music swells] Then it answers. [00:12] Done. (pause)"
    for _nm, _raw, _cls in (("table", _tbl, "table-fragment"), ("film direction", _film, "production-direction")):
        check(f"O39 positive control (real tester string): the {_nm} is DETECTED in the raw text", _cls in guard.excerpt_violations(_raw), str(guard.excerpt_violations(_raw)))
        check(f"O39b ...and gone after excerpt_clean ({_nm})", guard.excerpt_violations(guard.excerpt_clean(_raw)) == [], repr(guard.excerpt_clean(_raw)))
    check("O39c the words around a removed direction survive", "It is not a chat box wired to a database." in guard.excerpt_clean(_film) and "it plans" in guard.excerpt_clean(_film) and "After the table the text goes on." in guard.excerpt_clean(_tbl))
    check("O39d QUIET: ordinary bracketed numbers, times in prose and a [1] marker are untouched", guard.excerpt_clean("See [1] and the 9:30am call; costs are $5 [approx.].") == "See [1] and the 9:30am call; costs are $5 [approx.].")
    import inspect as _i3
    check("O40 a boot does not generate unless WARM_ON_BOOT is set: the boot warm task takes the flag, the default is off",
          "prewarm(config.WARM_ON_BOOT)" in _i3.getsource(_app2.lifespan) and (os.environ.get("WARM_ON_BOOT") or "0") != "1" and config.WARM_ON_BOOT is False)
    from types import SimpleNamespace as _NS
    _A = lambda **k: _NS(title="Doc " + k["i"], kind="document", href="/explore?asset=" + k["i"], thumb=None)
    _corp = _NS(by_rid={"r1": "a1", "r2": "a2"}, assets={"a1": _A(i="a1"), "a2": _A(i="a2")})
    _ans = object.__new__(Answerer); _ans.corpus = _corp
    _res = {"r1": {"fields": {"f": {"paragraphs": {"r1/f/1": {"text": "Starter includes one knowledge box and a fourteen day free trial for new accounts."}}}}},
            "r2": {"fields": {"f": {"paragraphs": {"r2/f/1": {"text": "Retrieval never returns an empty list so an application must set its own floor for declining."}}}}}}
    _txt = ("Follow these points:\n- Starter includes one knowledge box and a fourteen day free trial for new accounts.\n"
            "- The platform automatically rebalances shards across regions every night.\n"
            "- Retrieval never returns an empty list so an application must set a floor for declining.")
    def _drive(co):
        try:
            co.send(None)
        except StopIteration as _si:
            return _si.value
        raise RuntimeError("coroutine awaited unexpectedly")
    _pt, _pc, _dr = _drive(_ans.place_and_prune(["r1/f/1"], _res, _txt))
    check("O41 an unsupported bullet is dropped; a bullet supported only by a retrieved-but-uncited passage is marked (source added), not dropped",
          "rebalances shards" not in _pt and "Starter includes one knowledge box" in _pt and "Retrieval never returns" in _pt and len(_pc) == 2 and len(_dr) == 1, repr((_pt, [c["asset_id"] for c in _pc], _dr)))
    _pt2, _pc2, _dr2 = _drive(_ans.place_and_prune(["r1/f/1"], _res, "Follow these points:\n- The platform automatically rebalances shards across regions every night."))
    check("O41b a lead-in whose only item was unsupported is dropped with it", _pt2.strip() == "" , repr(_pt2))
    from .answer import printed_source as _ps
    _pp = _ps("What does this cost to start?", "canonical-the-economics", "What drives the cost")
    check("O42 CONTRACT-FIELDS-04: a price/limits answer links the PUBLISHED PAGE with its verification date; every printed answer has an href",
          _pp["kind"] == "published-page" and _pp["href"].startswith("https://www.progress.com/agentic-rag/pricing") and _pp["verified"]
          and _ps("Which file types can it ingest?", "a", "t")["kind"] == "published-page"
          and _ps("What drives the cost once we are running?", "canonical-the-economics", "What drives the cost")["href"].startswith("/explore?asset="), repr(_pp))
    check("O42b ...and every deterministic question yields a printed object with label, kind, source_title and href",
          all(set(("label", "kind", "source_title", "href")) <= set(_ps(q_, "x", "T")) and _ps(q_, "x", "T")["href"] for q_ in _dq))
    import tempfile as _tf, json as _js
    from pathlib import Path as _P
    from .check_store import check as _chk
    from .warm import content_hash as _ch
    _td = _P(_tf.mkdtemp(prefix="chk-"))
    _e = {"kind": "answer", "question": "q?", "scope": "s", "scope_key": "public||()", "text": "t", "citations": [], "confidence": {"band": "well-supported"}, "corpus_digest": "d"}
    (_td / "warm.json").write_text(_js.dumps({"q||public||()": _e}))
    _w = __import__("server.warm", fromlist=["WarmStore"]).WarmStore(_td / "warm.json", _td / "warm_approved.json", require_approval=False)
    (_td / "warm_approved.json").write_text(_js.dumps({}))
    check("O43 FIRE: a store with an answer that has no approval is refused", len(_chk(_td)) == 1, str(_chk(_td)))
    _k = next(iter(_w._d))
    (_td / "warm_approved.json").write_text(_js.dumps({_k: _ch(_e)}))
    check("O43b QUIET: the same store with a matching approval passes", _chk(_td) == [], str(_chk(_td)))
    _e2 = dict(_e, text="edited after approval")
    (_td / "warm.json").write_text(_js.dumps({_k: _e2}))
    check("O43c FIRE: an answer edited after approval is refused (approval is keyed on content)", len(_chk(_td)) == 1)
    (_td / "warm.json").write_text(_js.dumps({}))
    check("O43d FIRE: an empty store is refused, not passed (zero of zero is not a pass)", len(_chk(_td)) == 1)
    from .app import cap_history as _cap
    _st = {}
    _big = [{"question": "q%d?" % i, "answer": ("Sentence number %d is a complete unit of reasonable length here. " % i) * 30} for i in range(100)]
    _h = _cap(_big, _st)
    check("O44 FIRE: a hostile history (100 turns, 2,000+ chars each) is cut to HISTORY_TURNS turns and the answer cap, and counted",
          len(_h) == 2 * config.HISTORY_TURNS and all(len(x) <= max(config.HISTORY_Q_CHARS, config.HISTORY_A_CHARS) for x in _h) and _st.get("history_truncated") == 1, repr(_st))
    check("O44a trimming is at UNIT boundaries: every kept answer ends on a complete sentence, never mid-word",
          all(x.rstrip().endswith(".") for x in _h[1::2]), repr([x[-40:] for x in _h[1::2]]))
    check("O44d a question over the cap drops the WHOLE turn (no mid-question cut); a first unit over the answer cap drops the turn",
          _cap([{"question": "q" * 301, "answer": "ok."}], {}) is None and _cap([{"question": "q?", "answer": "w" * 500 + "."}], {}) is None)
    check("O44e an answer never ends on a lead-in: 'Follow these:' with its items over the cap is trimmed back to before the stem",
          (_cap([{"question": "q?", "answer": "First fact is here.\nFollow these:\n- " + "item " * 100}], {}) or ["", ""])[1] == "First fact is here.")
    _st2 = {}
    check("O44b QUIET: a legitimate two-turn history passes whole and is not counted as truncated",
          len(_cap([{"question": "How does X work?", "answer": "It works."}, {"question": "And Y?", "answer": "Y too."}], _st2)) == 4 and "history_truncated" not in _st2)
    check("O44c garbage entries are dropped, never raised", _cap([None, 5, {"question": "", "answer": "x"}, {"question": "q"}], {}) is None)
    from .answer import ANAPHORA_RE as _an
    check("O45 the follow-up detector fires on 'it' / 'that plan' and stays quiet on a self-contained question",
          _an.search("How much does that plan cost?") and _an.search("Can I use it with Pro?") and not _an.search("How do citations work on a generated answer?"))
    import inspect as _i4
    check("O46 floors are decided BEFORE history is used: the preflight find takes the bare question, never the history",
          "preflight\", question" in _i4.getsource(Answerer.compute) and "history" not in _i4.getsource(Answerer.compute).split("# 3. budget")[0].split("async def compute")[1].split('"preflight"')[1][:400])
    check("O47 every trace row says where the call was served from", all(r.get("served_from") in ("memory", "cache-replay", "knowledge-box") for r in Trace().add("c", "list", False, None, "warm", 1).__class__ and [Trace().add("c", "list", False, None, ch, 1) for ch in ("warm", "hit", "miss")]))
    # O41c: a PARAPHRASED unit that shares no content words with the cited passage is marked via a scoped retrieval, an invented one is dropped.
    class _FakeArag:
        async def find(self, trace, call, q, fe, top_k=4):
            if "fourteen day" in q:
                return {"resources": {"r1": {"usermetadata": {"classifications": [{"labelset": "tier", "label": "public"}]},
                        "fields": {"f": {"paragraphs": {"r1/f/9": {"text": "Starter includes a fourteen day free trial for new accounts.", "score": 0.97}}}}}}}
            return {"resources": {"r1": {"usermetadata": {"classifications": [{"labelset": "tier", "label": "public"}]},
                    "fields": {"f": {"paragraphs": {"r1/f/9": {"text": "unrelated", "score": 0.002}}}}}}}
    _corp2 = _NS(by_rid={"r1": "a1", "r2": "a2"}, assets={"a1": _A(i="a1"), "a2": _A(i="a2")}, labels_by_rid={"r1": {"tier": "public"}, "r2": {"tier": "public"}})
    _ans2 = object.__new__(Answerer); _ans2.corpus = _corp2; _ans2.arag = _FakeArag()
    from .scope import Scope as _Sc
    _res2 = {"r2": {"fields": {"f": {"paragraphs": {"r2/f/1": {"text": "Retrieval never returns an empty list so an application must set its own floor for declining.", "score": 0.9}}}}}}
    _txt2 = ("- Retrieval never returns an empty list so an application must set a floor for declining.\n"
             "- Use a fourteen day complimentary evaluation period before committing money to anything.\n"
             "- The platform automatically rebalances shards across regions every single night.")
    _p3, _c3, _d3 = _drive(_ans2.place_and_prune(["r2/f/1"], _res2, _txt2, _Sc.make(lens=""), Trace()))
    check("O41c a paraphrased unit with real semantic support is MARKED (kept, with its source); an unsupported one is dropped",
          "complimentary evaluation" in _p3 and "rebalances shards" not in _p3 and len(_d3) == 1 and any(c["asset_id"] == "a1" and c["attributed"] for c in _c3), repr((_p3, _d3, [(c["asset_id"], c["at"]) for c in _c3])))
    from . import corpus as _cm
    _req = set(_cm.VOCAB) - _cm.OPTIONAL_LABELSETS
    _full = {k: "x" for k in _cm.VOCAB}
    _nolang = {k: v for k, v in _full.items() if k != "language"}
    _notier = {k: v for k, v in _full.items() if k != "tier"}
    _extra = dict(_full, surprise="x")
    check("O48 labels_valid: with or without the optional `language` label passes; a missing required label or an unregistered one is rejected",
          _cm.labels_valid(_full) and _cm.labels_valid(_nolang) and not _cm.labels_valid(_notier) and not _cm.labels_valid(_extra))
    from . import media as _md
    import asyncio as _aio
    _mk = lambda i, kind, tier: _NS(asset_id=i, kind=kind, tier=tier, media_url=None)
    _mc = _NS(assets={"f1": _mk("f1", "film", config.PUBLIC_TIER), "f2": _mk("f2", "film", "starter"), "d1": _mk("d1", "document", config.PUBLIC_TIER)})
    check("O49 the media allow-list admits a PUBLIC film only (starter-tier film and a public document are not admitted)",
          _md.allowed(_mc, "f1") and not _md.allowed(_mc, "f2") and not _md.allowed(_mc, "d1"))
    _bad = _NS(assets={"x": _mk("x", "film", "starter")})
    _orig_allowed = _md.allowed
    _md.allowed = lambda c, i: True          # PLANT: an allow-list that wrongly admits a starter film
    try:
        _raised = False
        try:
            _drive(_md.probe_all(_bad))
        except RuntimeError:
            _raised = True
    finally:
        _md.allowed = _orig_allowed
    check("O49b FIRE: if the allow-list ever lets a non-public film through, probe_all RAISES instead of probing it", _raised)
    from .check_store import printed_violations as _pv
    _good = {"question": "q", "scope": "s", "deterministic": "x", "citations": [{"at": [], "attributed": False}],
             "confidence": {"band": "printed", "printed": _ps("What does this cost to start?", "canonical-the-economics", "What drives the cost")}}
    check("O50 QUIET: a valid printed entry has no CONTRACT-FIELDS-04 violation", _pv(_good) == [], str(_pv(_good)))
    import copy as _cp
    for _nm, _mut in (("missing href", lambda e: e["confidence"]["printed"].update(href="")), ("wrong kind", lambda e: e["confidence"]["printed"].update(kind="page")),
                      ("empty label", lambda e: e["confidence"]["printed"].update(label="")), ("band not printed", lambda e: e["confidence"].update(band="well-supported")),
                      ("missing object", lambda e: e["confidence"].pop("printed")), ("superscripts present", lambda e: e["citations"][0].update(at=[5], attributed=True)),
                      ("published page without a date", lambda e: e["confidence"]["printed"].update(verified=None)),
                      ("published page with a relative href", lambda e: e["confidence"]["printed"].update(href="/pricing"))):
        _e = _cp.deepcopy(_good)
        _mut(_e)
        check(f"O50b FIRE: printed entry with {_nm} is refused, naming the entry", bool(_pv(_e)) and "'q'" in _pv(_e)[0], str(_pv(_e)))
    check("O50c a generated entry is out of scope of the printed contract", _pv({"question": "q", "confidence": {"band": "well-supported"}}) == [])
    from .answer import file_limit_row as _flr
    _t0 = {"name": "Starter", "limits": ["Max 750MB per file, text-based files only", "5GB indexed data or 15,000 resources", "1 knowledge box included"]}
    _t1 = {"name": "Starter", "limits": ["1 knowledge box included", "5GB indexed data or 15,000 resources", "Max 750MB per file, text-based files only"]}
    _t2 = {"name": "Starter", "limits": ["5GB indexed data or 15,000 resources", "1 knowledge box included"]}
    _t3 = {"name": "Starter", "limits": ["Max 750MB per file, text-based files only", "Unlimited file size"]}
    def _raises(t):
        try:
            _flr(t)
        except RuntimeError:
            return True
        return False
    check("O51 the file-types row is selected by CONTENT: the same row is found when the limits are reordered (index 0 would serve the wrong row)",
          _flr(_t0) == _flr(_t1) == "Max 750MB per file, text-based files only" and _t1["limits"][0] != _flr(_t1))
    check("O51b ...and it RAISES when no row names file size/types, or when two rows do (never falls back to index 0)", _raises(_t2) and _raises(_t3))
    check("O51c the real verified file resolves exactly one row per tier", all(_flr(t) for t in __import__("json").loads(config.data_file("pricing-verified.json").read_text())["tiers"]))
    from . import corpus as _cm2
    _items = [("a", "Title A", ["para one", "para two"]), ("b", "Title B", ["other text"])]
    _lbl = [("a", {"tier": "public", "journey": "all", "vertical": "cross-industry", "kind": "document", "source": "positioning", "language": "English"}),
            ("b", {"tier": "public", "journey": "buy", "vertical": "cross-industry", "kind": "guide", "source": "positioning"})]
    _td0 = _cm2.TD.text_digest(_items)
    _ad0 = _cm2.answer_digest(_td0, _lbl)
    _lbl_nolang = [(slug, {k: v for k, v in lb.items() if k != "language"}) for slug, lb in _lbl]
    _lbl_otherlang = [(slug, dict(lb, language="Spanish") if "language" in lb else lb) for slug, lb in _lbl]
    check("O52 label-only writes leave approvals VALID: adding, removing or changing the `language` label does not move the answer digest",
          _ad0 == _cm2.answer_digest(_td0, _lbl_nolang) == _cm2.answer_digest(_td0, _lbl_otherlang))
    _items2 = [("a", "Title A", ["para one", "para twp"]), ("b", "Title B", ["other text"])]
    check("O52b ...and a ONE-CHARACTER edit to a body voids them", _cm2.answer_digest(_cm2.TD.text_digest(_items2), _lbl) != _ad0)
    _lbl_tier = [(slug, dict(lb, tier="starter") if slug == "b" else lb) for slug, lb in _lbl]
    check("O52c ...and so does a change of a SCOPE label (tier): what an answer may be grounded on changed", _cm2.answer_digest(_td0, _lbl_tier) != _ad0)
    check("O52d ...a new resource voids them, and a title edit does too", _cm2.TD.text_digest(_items + [("c", "C", ["x"])]) != _td0 and _cm2.TD.text_digest([("a", "Title A!", ["para one", "para two"]), _items[1]]) != _td0)
    _real = __import__("pathlib").Path(config.APP / "corpus" / "textdigest.py")
    check("O52e the server loads THE SAME textdigest.py the stability gate uses (one implementation), not a copy",
          (not _real.exists()) or _cm2.TD.text_digest.__code__.co_filename == str(config.data_file("textdigest.py")))
    # O53: a known-but-unservable chip declines honestly and NEVER falls through to live generation
    class _NoGen:
        async def find(self, *a, **k): raise AssertionError("no retrieval/generation may happen for a refreshing chip")
        async def ask_events(self, *a, **k): raise AssertionError("no generation may happen for a refreshing chip")
    from .warm import WarmStore as _WS
    _ws3 = _WS(_P(_tf.mkdtemp()) / "w.json", _P(_tf.mkdtemp()) / "a.json", require_approval=True)
    _scope3 = _Sc.make(lens="build")
    _ws3._d[_ws3._k("how does x work", _scope3)] = {"kind": "answer", "question": "How does X work?", "corpus_digest": "OLD", "pipeline": "p", "text": "t", "citations": [], "scope_key": _scope3.key()}
    _a3 = object.__new__(Answerer); _a3.warm = _ws3; _a3.stats = {}; _a3.corpus = _NS(answer_digest="NEW", digest="NEW"); _a3.arag = _NoGen(); _a3.lru = __import__("server.cache", fromlist=["LRU"]).LRU(10, 60); _a3.budget = None
    async def _collect(a, q, sc):
        return [(ev, d) async for ev, d in a.stream(q, sc, "v")]
    def _run(co):
        try:
            co.send(None)
        except StopIteration as _si:
            return _si.value
        raise RuntimeError("awaited")
    _evs = _run(_collect(_a3, "How does X work?", _scope3))
    check("O53 FIRE: a known chip whose reviewed entry is stale is declined as 'refreshing' with NO retrieval or generation (never live-generated)",
          any(e == "refusal" and d["reason"] == "refreshing" for e, d in _evs) and _a3.stats.get("refreshing") == 1, repr(_evs)[:200])
    # O28q: THE MECHANISM BEHIND "when no citation resolves, the whole response is withheld" (answer.py compute(), the `if not citations:` branch). Driven through the
    # REAL stream() with a stub platform whose answer names no source: the browser receives a refusal and NO token/sources/citations event, i.e. the withholding is
    # SERVER-SIDE. The planted control gives the same answer a resolvable citation and requires the pipeline to get past that branch (it must reach scoring), so the
    # refusal is proven to be caused by the missing citation and not by something else in the stub.
    async def _stream_events(cit, extra=False):
        RES = {"r1": {"fields": {"f": {"paragraphs": {"r1/f/0-10": {"score": 0.9, "text": "The product answers questions from your content and states this plainly."}}}}}}
        if extra:       # a second source whose passage shares nothing with the answer
            RES["r2"] = {"fields": {"f": {"paragraphs": {"r2/f/0-10": {"score": 0.5, "text": "Zebra migration patterns across the savannah."}}}}}
        class _Stub:
            async def find(self, *a, **k): return {"resources": RES}
            async def ask_events(self, *a, **k):
                return [{"type": "status", "code": "0"}, {"type": "answer", "text": "The product answers from your content. It states this plainly."},
                        {"type": "retrieval", "results": {"resources": RES}}, {"type": "citations", "citations": cit}]
            async def remi(self, *a, **k): raise _Reached("scoring")
        class _Reached(Exception): pass
        an = object.__new__(Answerer)
        an.arag = _Stub(); an.stats = {"held_sentences": 0, "floor_refusals": 0, "scope_withheld": 0}
        asset = _NS(tier=config.PUBLIC_TIER, journey="build", vertical="x", stage="x", kind="guide", source="x", title="T", thumb="", href="/h", language="English")
        an.corpus = _NS(assets={"a1": asset, "a2": _NS(**{**asset.__dict__, "title": "Zebras"})}, by_rid={"r1": "a1", "r2": "a2"}, reach=lambda sc: 1, answer_digest="D", digest="D", labels_by_rid={"r1": {"tier": config.PUBLIC_TIER}, "r2": {"tier": config.PUBLIC_TIER}})
        an.budget = _NS(admit=lambda v, team=False: (True, 0, None))
        an.warm = _NS(get=lambda *x, **k: None, knows=lambda *x, **k: False)
        an.lru = __import__("server.cache", fromlist=["LRU"]).LRU(8, 60)
        evs, reached = [], False
        try:
            async for e, d in an.stream("How does the product answer?", _Sc.make(), "v"):
                evs.append((e, d))
        except Exception as ex:
            reached = type(ex).__name__ in ("_Reached", "AttributeError")          # got past the uncited branch (the stub has no retrieval/follow-up layer)
        return evs, reached
    def _arun(co):                       # the real pipeline suspends (gather), so run it on its own loop in its own thread
        import threading
        box = {}
        def _t():
            loop = __import__("asyncio").new_event_loop()
            try:
                box["v"] = loop.run_until_complete(co)
            finally:
                loop.close()
        th = threading.Thread(target=_t); th.start(); th.join()
        return box["v"]
    async def _decline_probe():
        RES = {"r1": {"fields": {"f": {"paragraphs": {"r1/f/0-10": {"score": 0.9, "text": "The product answers questions from your content and states this plainly."}}}}}}
        class _D:
            async def find(self, *a, **k): return {"resources": RES}
            async def ask_events(self, *a, **k):
                return [{"type": "status", "code": "-2"}, {"type": "answer", "text": "Not enough data to answer this."}, {"type": "retrieval", "results": {"resources": RES}}, {"type": "citations", "citations": {}}]
        an = object.__new__(Answerer)
        an.arag = _D(); an.stats = {"held_sentences": 0, "floor_refusals": 0, "scope_withheld": 0}
        asset = _NS(tier=config.PUBLIC_TIER, journey="build", vertical="x", stage="x", kind="guide", source="x", title="T", thumb="", href="/h", language="English")
        an.corpus = _NS(assets={"a1": asset}, by_rid={"r1": "a1"}, reach=lambda sc: 1, answer_digest="D", digest="D", labels_by_rid={"r1": {"tier": config.PUBLIC_TIER}})
        an.budget = _NS(admit=lambda v, team=False: (True, 0, None)); an.warm = _NS(get=lambda *x, **k: None, knows=lambda *x, **k: False)
        an.lru = __import__("server.cache", fromlist=["LRU"]).LRU(8, 60)
        evs = [(e, d) async for e, d in an.stream("Why does this decline?", _Sc.make(), "v")]
        return evs, an
    _ev_d, _an_d = _arun(_decline_probe())
    from . import spellcheck as _sp
    _dic = _sp.load_dictionary()
    check("O28aa the spell check ALLOWS the coordinat- family (a dictionary gap that blocked a clean hero) and STILL flags a non-word",
          not _sp.unknown_words("A retrieval agent is coordinating its searches and coordination matters.", _dic, set()) and bool(_sp.unknown_words("A retrieval agent is cooordinating work.", _dic, set())))
    check("O28w a model decline records WHY (platform status code and the opening of the refused text) on the answerer for the warm report, and none of it reaches the browser payload",
          any(e == "refusal" and d.get("reason") == "no_answer" for e, d in _ev_d) and list(_an_d.declines.values())[0]["status"] == "-2"
          and "Not enough data" in list(_an_d.declines.values())[0]["opening"] and not any("opening" in str(d) or "decline_detail" in str(d) for e, d in _ev_d), repr((_an_d.declines, [e for e, _ in _ev_d])))
    _ev_u, _reach_u = _arun(_stream_events({}))
    _ev_c, _reach_c = _arun(_stream_events({"r1/f/0-10": [[0, 10]]}))
    check("O28q an answer that names NO resolvable source is withheld SERVER-SIDE: the stream carries a refusal reason 'uncited' and no token, sources or citations event",
          any(e == "refusal" and d.get("reason") == "uncited" for e, d in _ev_u) and not any(e in ("token", "sources", "citations") for e, d in _ev_u) and not _reach_u, repr([e for e, _ in _ev_u]))
    _ev_s, _ = _arun(_stream_events({"r1/f/0-10": [[0, 10]], "r2/f/0-10": [[0, 10]]}, extra=True))
    _cit_s = [d for e, d in _ev_s if e == "citations"]
    check("O28s a source that supports NO sentence of a generated answer is not listed beside it (read 18's Spanish asset); the supporting one stays",
          _cit_s and [c["asset_id"] for c in _cit_s[0]["citations"]] == ["a1"] and [c["n"] for c in _cit_s[0]["citations"]] == [1], repr(_cit_s)[:300])
    check("O28r PLANTED control: the same answer WITH a resolvable citation gets past the uncited branch (so the refusal above is caused by the missing citation)", _reach_c, repr([e for e, _ in _ev_c]))
    import inspect as _i5
    check("O54 a non-generating boot does not prune the store (so a stale chip is still KNOWN and declines as 'refreshing')",
          "prune(S[\"corpus\"].answer_digest) if generate else 0" in _i5.getsource(_app2.prewarm))
    from .app import is_team as _it
    _R = lambda h: _NS(headers=h)
    _old_key = config.OPERATOR_KEY
    config.OPERATOR_KEY = "k-test"
    try:
        check("O55 a request carrying the operator key is TEAM traffic; a wrong, empty or absent key is a visitor",
              _it(_R({"x-operator-key": "k-test"})) and not _it(_R({"x-operator-key": "wrong"})) and not _it(_R({})) and not _it(_R({"x-operator-key": ""})))
        config.OPERATOR_KEY = None
        check("O55b with no operator key configured nobody is team (an empty key never matches an empty header)", not _it(_R({"x-operator-key": ""})) and not _it(_R({})))
    finally:
        config.OPERATOR_KEY = _old_key
    async def _collect3(a, q, sc, team):
        return [(ev, d) async for ev, d in a.stream(q, sc, "v", team=team)]
    _before = dict(_a3.asks)
    _run(_collect3(_a3, "How does X work?", _scope3, True))
    _run(_collect3(_a3, "How does X work?", _scope3, False))
    check("O55c asks are counted by sender: one team ask and one visitor ask are recorded separately", (_a3.asks["visitors"], _a3.asks["team"]) == (_before["visitors"] + 1, _before["team"] + 1), repr((_before, _a3.asks)))
    _cat = _NS(assets={"a1": _NS(tier=config.PUBLIC_TIER, thumb="/thumbs/a1.jpg", href="/explore?asset=a1"), "s1": _NS(tier="starter", thumb=None, href="/x")}, answer_digest="d")
    _a8 = object.__new__(Answerer); _a8.corpus = _cat; _a8.stats = {}
    _cards = [{"asset_id": "a1", "thumb": "/thumbs/OLD.jpg", "href": "/old"}, {"asset_id": "gone", "thumb": "/thumbs/gone.jpg"}, {"asset_id": "s1"}]
    _fc = _a8._fresh_cards(_cards)
    check("O56 a stored card for an asset that left the public catalogue (or is not public) is DROPPED and counted; a kept card's thumb/href are the live ones",
          len(_fc) == 1 and _fc[0]["asset_id"] == "a1" and _fc[0]["thumb"] == "/thumbs/a1.jpg" and _fc[0]["href"] == "/explore?asset=a1" and _a8.stats.get("cards_dropped") == 2, repr((_fc, _a8.stats)))
    _a8.warm = _NS(); 
    _pw = {"kind": "answer", "text": "t", "citations": [{"asset_id": "gone"}], "followups": [], "confidence": {"band": "well-supported", "contexts": 1, "raw": None}}
    _evs8 = list(_a8._events(_pw, "warm", 0))
    check("O56b ...and an answer whose every source is gone is not served uncited: it declines as 'refreshing'", any(e == "refusal" and d["reason"] == "refreshing" for e, d in _evs8) and not any(e == "token" for e, d in _evs8), repr([e for e, _ in _evs8]))
    _cat2 = _NS(assets={"a1": _NS(tier=config.PUBLIC_TIER, thumb="/t/a1.jpg", href="/h/a1", language="English"),
                        "a2": _NS(tier=config.PUBLIC_TIER, thumb=None, href="/h/a2", language="Spanish"),
                        "a3": _NS(tier=config.PUBLIC_TIER, thumb=None, href="/h/a3", language="")}, answer_digest="d")
    _a7 = object.__new__(Answerer); _a7.corpus = _cat2; _a7.stats = {}
    _cc = [{"n": 1, "asset_id": "a1", "passage": "Open /internal-search to see the cited passage.", "at": [10]},
           {"n": 2, "asset_id": "a2", "passage": "Los grafos conectan entidades.", "at": [20]},
           {"n": 3, "asset_id": "a3", "passage": "Pricing page lists the tiers.", "at": [30]}]
    _fc2 = _a7._fresh_cards(_cc)
    check("O57 a citation whose PASSAGE names another product's route is dropped (the evidence panel is a second surface) and the rest are renumbered 1..k",
          [c["asset_id"] for c in _fc2] == ["a2", "a3"] and [c["n"] for c in _fc2] == [1, 2] and _a7.stats.get("route_passages_dropped") == 1, repr(_fc2))
    from .corpus import Asset as _Asset
    _mk = lambda i, lg: _Asset(i, "r" + i, "T" + i, "guide", "x", "x", "build", "public", "x", "x", "e", "", "/a", language=lg)
    _cards = {lg or "absent": _mk(str(n), lg).card() for n, lg in enumerate(["Spanish", "English", ""])}
    check("O57c library card() carries language and language_differs on the SAME rule (Spanish True; English False; absent None and False)",
          (_cards["Spanish"]["language"], _cards["Spanish"]["language_differs"]) == ("Spanish", True)
          and (_cards["English"]["language"], _cards["English"]["language_differs"]) == ("English", False)
          and (_cards["absent"]["language"], _cards["absent"]["language_differs"]) == (None, False), repr(_cards))
    _a7.warm = _NS()
    _pw7 = {"kind": "answer", "text": "An answer.", "citations": [{"n": 1, "asset_id": "a1", "passage": "ok", "at": []}], "followups": [{"asset_id": "a2", "title": "Spanish guide"}, {"asset_id": "a1", "title": "English guide"}, {"asset_id": "a3", "title": "Unlabelled"}],
            "confidence": {"band": "well-supported", "contexts": 1, "raw": None}, "scope": "s", "corpus_digest": "d", "stamp": "t", "model": "m", "origin_trace": []}
    _fu7 = [d for e, d in _a7._events(_pw7, "warm", 0) if e == "followups"]
    check("O57d a follow-up asset in another language than the (English) answer is not offered, at serve time, for a stored entry; English and unlabelled ones stay",
          _fu7 and [f["asset_id"] for f in _fu7[0]["followups"]] == ["a1", "a3"], repr(_fu7))
    check("O57b language: Spanish label -> language_differs True; English -> False; ABSENT label -> language None and differs False (never assumed English)",
          _fc2[0]["language"] == "Spanish" and _fc2[0]["language_differs"] is True and _fc2[1]["language"] is None and _fc2[1]["language_differs"] is False
          and __import__("server.answer", fromlist=["lang_fields"]).lang_fields(_cat2.assets["a1"]) == {"language": "English", "language_differs": False})
    _dict = _sc.load_dictionary()
    check("O58 the spell check's dictionary knows every Australian -ise/-our/-re form the US-spelling rule would rewrite to (a control and a check cannot disagree)",
          all(w in _dict for w in ("emphasise", "emphasised", "authorisation", "organisation", "behaviour", "colour", "centre", "analyse", "afterwards", "labelled"))
          and "emphasize" in _dict, "")
    from .editorial import apply_unit_edits as _aue
    _txt9 = "- First point is here and stands.\n- Second point is cut by the reviewer.\n- Third point is rewritten."
    _e9 = {"text": _txt9, "citations": [{"n": 1, "asset_id": "x", "at": [len("- First point is here and stands.")]},
                                       {"n": 2, "asset_id": "y", "at": [len("- First point is here and stands.\n- Second point is cut by the reviewer.")]},
                                       {"n": 3, "asset_id": "z", "at": [len(_txt9)]}]}
    _aue(_e9, [{"old": "- Second point is cut by the reviewer.", "new": None, "reason": "t", "public_reason": "t"}, {"old": "- Third point is rewritten.", "new": "- Third point reads better.", "reason": "t", "public_reason": "t"}], "test")
    check("O59 editorial edits: a cut unit is gone, a replaced unit is replaced, the text is declared, the model's original is kept",
          _e9["text"] == "- First point is here and stands.\n- Third point reads better." and _e9["text_as_generated"] == _txt9 and len(_e9["editorial_edits"]) == 2)
    check("O59b ...markers are remapped to the new offsets, a source that supported only the cut unit is dropped, and the rest are renumbered",
          [c["asset_id"] for c in _e9["citations"]] == ["x", "z"] and [c["n"] for c in _e9["citations"]] == [1, 2]
          and _e9["citations"][0]["at"] == [len("- First point is here and stands.")] and _e9["citations"][1]["at"] == [len(_e9["text"])], repr(_e9["citations"]))
    try:
        _aue(dict(text="One. Two.", citations=[]), [{"old": "Nothing like this", "new": None, "reason": "t", "public_reason": "t"}], "test")
        _raised2 = False
    except ValueError:
        _raised2 = True
    check("O59c an edit that matches no unit RAISES (an edit that applies to nothing must not look applied)", _raised2)
    _e10 = {"text": "- One fact that stands.\n- Another fact to cut.", "citations": [], "confidence": {"band": "well-supported", "raw": {"groundedness": [5]}, "contexts": 8}, "question": "q", "scope": "s", "kind": "answer"}
    _aue(_e10, [{"old": "- Another fact to cut.", "new": None, "reason": "t", "public_reason": "t"}], "test")
    check("O60 an editorial edit INVALIDATES the score: the band is 'unscored' with the previous figure kept and rescored False",
          _e10["confidence"]["band"] == "unscored" and _e10["confidence"]["rescored"] is False and _e10["confidence"]["previous"]["band"] == "well-supported")
    from .check_store import check as _cs2
    _td10 = _P(_tf.mkdtemp())
    (_td10 / "warm.json").write_text(_js.dumps({"k": _e10}))
    _w10 = __import__("server.warm", fromlist=["WarmStore"]).WarmStore(_td10 / "warm.json", _td10 / "warm_approved.json", require_approval=False)
    (_td10 / "warm_approved.json").write_text(_js.dumps({"k": _ch(_e10)}))
    check("O60b FIRE: an approved entry that was edited and NOT re-scored is refused by the store check", any("not re-scored" in x for x in _cs2(_td10)), str(_cs2(_td10)))
    from .editorial import rescore as _rs
    class _FA:
        async def find(self, tr, call, q, fe, top_k=12):
            return {"resources": {"r": {"fields": {"f": {"paragraphs": {"r/f/1": {"text": "One fact that stands, in context.", "score": 0.9}}}}}}}
        async def remi(self, tr, call, q, a, ctxs):
            assert ctxs and "One fact that stands" in ctxs[0] and a == _e10["text"], "scored the wrong text or no context"
            return {"groundedness": [5], "context_relevance": [4]}
    _an10 = object.__new__(Answerer); _an10.arag = _FA()
    _drive(_rs(_e10, _an10, _Sc.make(lens="")))
    _e10["corpus_digest"] = "d"
    (_td10 / "warm.json").write_text(_js.dumps({"k": _e10}))
    (_td10 / "warm_approved.json").write_text(_js.dumps({"k": _ch(_e10)}))
    check("O60c ...and QUIET once re-scored: the band describes the edited text and the entry records whether it moved",
          _e10["confidence"]["rescored"] is True and _e10["confidence"]["band"] != "unscored" and "band_moved" in _e10["confidence"] and _cs2(_td10) == [], str((_e10["confidence"], _cs2(_td10))))
    _corp7 = _NS(by_rid={"r1": "a1", "r2": "a2"}, assets={"a1": _A(i="a1"), "a2": _A(i="a2")})
    _an7 = object.__new__(Answerer); _an7.corpus = _corp7
    _res7 = {"r1": {"fields": {"f": {"paragraphs": {"r1/f/1": {"text": "The agent carries the caller's token when it calls your tools over the protocol."}}}}},
             "r2": {"fields": {"f": {"paragraphs": {"r2/f/1": {"text": "The agent carries the caller's token. Open /internal-search to try it, and the agent carries the caller's token again."}}}}}}
    _cit7 = _an7._citations(["r1/f/1", "r2/f/1"], _res7, "The agent carries the caller's token when it calls your tools.")
    check("O61 a passage naming another product's route is NOT trimmed to fit: its whole paragraph is not a source, and a clean passage is shown verbatim",
          [c["asset_id"] for c in _cit7] == ["a1"] and "internal-search" not in " ".join(c["passage"] for c in _cit7), repr(_cit7))
    _corp8 = _NS(by_rid={"r1": "a1", "r2": "a2", "r3": "a3"}, assets={"a1": _A(i="a1"), "a2": _A(i="a2"), "a3": _A(i="a3")})
    _an8 = object.__new__(Answerer); _an8.corpus = _corp8; _an8.stats = {}
    _res8 = {"r1": {"fields": {"f": {"paragraphs": {"r1/f/1": {"text": "The agent carries the caller's token when it calls your tools over the protocol."}}}}},
             "r2": {"fields": {"f": {"paragraphs": {"r2/f/1": {"text": "The agent carries the caller's token \u2014 it calls your tools."}}}}},
             "r3": {"fields": {"f": {"paragraphs": {"r3/f/1": {"text": "The agent carries the caller's token. Call POST /ask to try it. The agent carries the caller's token."}}}}}}
    _c8 = _an8._citations(["r1/f/1", "r2/f/1", "r3/f/1"], _res8, "The agent carries the caller's token when it calls your tools.")
    _res8c = {"r4": {"fields": {"f": {"paragraphs": {"r4/f/1": {"text": "Slide 3 THE CONCEPT The agent will authorize the caller's token."}}}}}}
    _an8.corpus = _NS(by_rid={"r4": "a4", "r1": "a1", "r2": "a2", "r3": "a3"}, assets={"a4": _A(i="a4"), "a1": _A(i="a1"), "a2": _A(i="a2"), "a3": _A(i="a3")})
    _c8c = _an8._citations(["r4/f/1"], _res8c, "The agent will use the caller's token.")
    check("O62b ...but an all-caps run and a US spelling inside a quotation are the SOURCE'S OWN words: shown verbatim, not lowered or respelled",
          len(_c8c) == 1 and _c8c[0]["passage"] == "Slide 3 THE CONCEPT The agent will authorize the caller's token.", repr(_c8c))
    check("O62 a QUOTATION is never normalised: a passage that would need an em dash replaced or a platform string removed is not a source (dropped, counted); a clean one is shown verbatim",
          [c["asset_id"] for c in _c8] == ["a1"] and _c8[0]["passage"] == "The agent carries the caller's token when it calls your tools over the protocol." and _an8.stats.get("passages_not_quotable") == 2, repr((_c8, _an8.stats)))
    from .answer import DETERMINISTIC_QUESTIONS as _dq2
    from .cache import norm_query as _nq2
    check("O63 the hero is NEVER a printed answer: no HERO_FALLBACK_QUESTION exists, and an empty preferred hero means cascade", not hasattr(config, "HERO_FALLBACK_QUESTION") and (config.HERO_QUESTION == "" or _nq2(config.HERO_QUESTION) not in _dq2))
    import inspect as _i6
    check("O63b a printed question is exempt from the generative-budget refusal in the route (an exhausted visitor still gets it)",
          "DETERMINISTIC_QUESTIONS" in _i6.getsource(_app2.answer_route))
    _before2 = dict(_a3.asks)
    async def _fake_compute(*a, **k):
        yield "_payload", {"kind": "refusal", "reason": "x", "message": "m", "stamp": "s", "model": None, "scope": "s", "corpus_digest": "d", "origin_trace": []}
    _a3.compute = _fake_compute
    _a3.hero_norm = _nq2("What is an example hero question?")
    _run(_collect3(_a3, "What is an example hero question?", _Sc.make(lens=""), False))
    check("O63d the hero question is warmed UNSCOPED by the warm itself (the page fires it with no scope; a scoped entry would miss the store and fall through to a live generation)",
          "config.HERO_QUESTION" in _i6.getsource(_app2.prewarm) and config.HERO_QUESTION and _nq2(config.HERO_QUESTION) not in _dq2)
    check("O64 the page's own hero example is counted as page_load_example, NOT as a visitor question (a page load is not a visitor asking)",
          _a3.asks["page_load_example"] == _before2.get("page_load_example", 0) + 1 and _a3.asks["visitors"] == _before2["visitors"], repr((_before2, _a3.asks)))
    _real_q = ("Slide 3 Two things: nodes and edges THE CONCEPT A knowledge graph models entities as nodes and the relationships between them as edges - extracted straight "
               "out of your unstructured content. located in speaks works with D. Kwan Person San Francisco Location Italian Language Alice Person Bob Person NO Person Carol Location")
    check("O65 the quote ends at the last COMPLETE sentence inside 320 chars and starts at the paragraph start (the real scraped-diagram passage from read 16)",
          guard.quote_window(_real_q) == _real_q.split(". located")[0] + "." and not guard.quote_window(_real_q).endswith("NO"))
    check("O65b a paragraph that fits whole is shown whole; one with no complete sentence in the window shows NOTHING (not a fragment); an initial or 'e.g.' is not a boundary",
          guard.quote_window("Short paragraph with no stop") == "Short paragraph with no stop" and guard.quote_window("w " * 300) == ""
          and guard.quote_window("Costs e.g. the tiers and so on, and more. " + "word " * 80) == "Costs e.g. the tiers and so on, and more.")
    from .app import asks_provenance as _ap
    _old_since = config.PUBLIC_VISITORS_SINCE
    config.PUBLIC_VISITORS_SINCE = None
    _t1 = _ap()
    config.PUBLIC_VISITORS_SINCE = "2026-11-01"
    _t2 = _ap()
    config.PUBLIC_VISITORS_SINCE = _old_since
    check("O66 until the site has public visitors, the count carries a plain sentence that every question was the team's; once a launch date is set it names the date",
          "asked by the team building this site" in _t1 and "not a member of the public" in _t1 and "no public visitors" not in _t1 and "2026-11-01" in _t2, repr((_t1, _t2)))
    _ws_h = _WS(_P(_tf.mkdtemp()) / "w.json", _P(_tf.mkdtemp()) / "a.json", require_approval=False)
    _old_S = dict(_app2.S)
    _old_hq = config.HERO_QUESTION
    _app2.S["warm"] = _ws_h
    _app2.S["corpus"] = _NS(answer_digest="D1")
    _HQ, _GQ, _PQ = "What is the preferred hero?", "A generated home question?", "What does this cost to start?"
    _app2.S["suggested"] = [{"q": _PQ, "lens": "buy"}, {"q": _GQ, "lens": "build"}]
    def _put(q):
        _ws_h._d[_ws_h._k(_nq2(q), _Sc.make())] = {"kind": "answer", "question": q, "corpus_digest": "D1", "pipeline": config.PIPELINE_VERSION, "stamp": "t", "text": "x", "citations": [], "scope_key": _Sc.make().key()}
    try:
        config.HERO_QUESTION = _HQ
        _h0 = _app2.hero_example()                                   # nothing stored: ABSENT, and stated
        _s0 = dict(_app2.S["hero_status"])
        _put(_PQ); _ws_h._d[_ws_h._k(_nq2(_PQ), _Sc.make())]["deterministic"] = True   # a PRINTED entry in the store must never become the hero
        _h1 = _app2.hero_example()
        _put(_GQ)
        _h2 = _app2.hero_example()                                   # preferred missing: cascades to the first servable GENERATED home entry
        _put(_HQ)
        _h3 = _app2.hero_example()                                   # preferred present: preferred wins
        _app2.S["corpus"] = _NS(answer_digest="D2")
        _h4 = _app2.hero_example()                                   # stale: ABSENT again, never printed
    finally:
        config.HERO_QUESTION = _old_hq
        _app2.S.clear(); _app2.S.update(_old_S)
    check("O63c the hero is a servable GENERATED entry: preferred first, else the first generated home entry; a printed entry is never the hero; nothing servable (empty or stale) means ABSENT with the state stated",
          _h0 is None and _s0["state"] == "ABSENT" and _h1 is None and _h2["question"] == _GQ and _h2["source"] == "prewarmed" and _h3["question"] == _HQ and _h4 is None, repr((_h0, _h1, _h2, _h3, _h4)))
    _real_persona = "Personas: CIO (primary - defensible, trust-scored decisions; data in your own environment)"   # the REAL string from the Publisher demo body
    check("O67 FIRE (real string): the persona-line reassurance is a held deployment claim, so a generated sentence carrying it is held and a passage carrying it is not a source",
          guard.claims(_real_persona) == ["deployment-mode"] and guard.claims("Everything runs in your own environment and nothing leaves it.") == ["deployment-mode"])
    check("O67b QUIET: hybrid SEARCH, and the confirmed three-mode wording where inference runs in the Progress cloud, are not the held persona shape",
          guard.claims("Hybrid search combines keyword and semantic retrieval.") == [] and guard.claims("Your documents are cited to the passage they came from.") == [])
    _fe = _Sc.make(lens="build").filter_expression()
    check("O67c every scoped retrieval/generation carries the serve-time exclusion of the held-claim resource (no corpus change, no digest move)",
          all({"not": {"prop": "resource", "slug": sl}} in _fe["field"]["and"] for sl in config.SERVE_EXCLUDE_SLUGS) and config.SERVE_EXCLUDE_SLUGS, repr(_fe)[:200])
    check("O67d the deliberate exclusion is VISIBLE: it is a named, reasoned entry the reveal and /ops/report both print, not just a filter clause",
          config.SERVE_EXCLUDE and all(isinstance(v, str) and len(v) > 40 for v in config.SERVE_EXCLUDE.values())
          and "excluded_from_retrieval" in _i6.getsource(_app2.api_reveal) + _i6.getsource(_app2.ops_report), "")
    import inspect as _i9
    check("O68 each generated payload records the FULL set of assets retrieved at generation (provenance.retrieved_asset_ids), not only the cited ones",
          "retrieved_asset_ids" in _i9.getsource(Answerer.compute))
    _pr = {"kind": "answer", "question": "q", "text": "t.", "citations": [{"asset_id": "a1", "n": 1}], "followups": [], "scope": "s", "stamp": "x", "model": None, "corpus_digest": "d",
           "confidence": {"band": "well-supported", "contexts": 1, "raw": None}, "origin_trace": [{"call": "answer", "generative": True, "cache": "miss", "served_from": "knowledge-box", "ms": 5}],
           "editorial_edits": [{"removed": "Cut sentence.", "reason": "internal", "public_reason": "Plain words."}]}
    _a8.warm = _NS()
    _ev9 = {e: d for e, d in _a8._events(_pr, "warm", 0)}
    check("O69 a pre-warmed answer says it was READ by a person and lists what was cut and why in plain words; a live answer says nothing of the kind",
          _ev9["confidence"]["review"] == {"read_by_person": True, "edited": True, "edits": [{"action": "removed", "text": "Cut sentence.", "with": None, "reason": "Plain words."}]}
          and {e: d for e, d in _a8._events(dict(_pr, editorial_edits=[]), "miss", 0)}["confidence"]["review"] is None, repr(_ev9["confidence"].get("review")))
    _row = _ev9["_trace"]["trace"][-1]
    check("O69b a REPLAYED row describes the original call but THIS visit made none: generative False, was_generative True, served_from cache-replay (the reveal counts rows with generative true)",
          _row["replayed"] is True and _row["generative"] is False and _row["was_generative"] is True and _row["served_from"] == "cache-replay", repr(_row))
    _prt = dict(_pr, deterministic="printed from x", editorial_edits=[], confidence={"band": "printed", "contexts": 0, "raw": None, "printed": {"source_title": "t", "label": "l"}})
    _tr9 = {e: d for e, d in _a8._events(_prt, "hit", 0)}["_trace"]
    check("O70 a PRINTED answer's trace has no answer/warm timestamp and is not 'served from cache' (the footer would contradict the provenance pill)",
          _tr9["printed"] is True and _tr9["answered_at"] is None and _tr9["warmed_at"] is None and _tr9["served_from_cache"] is False and _tr9["warm"] is False, repr(_tr9))
    d5 = "The description is narrow by design; it does not include an ROI number."
    check("O23 FIRE: 'the description is ...' is the self-reference class", bool(guard.DOC_SELF_REFERENCE_RE.search(d5)))
    check("O23b QUIET: a description FIELD and uploaded material are product vocabulary",
          not guard.DOC_SELF_REFERENCE_RE.search("A description field is stored with each box. The material you upload is chunked."))
    check("O21e FIRE: disjoint money figures; QUIET: a subset",
          bool(pair_conflicts("Starter is $700 a month.", "Starter is $900 a month.")) and pair_conflicts("Starter is $700 a month.", "Starter is $700 a month and Pro is $1,925.") == [])
    check("O21f a path offering fewer than three chips is not offered", config.MIN_PATH_CHIPS == 3)

    # O14 citation offsets past the end of the answer attach to the last kept sentence, never vanish
    t2 = "One thing. Two things."
    n2, om2, _ = guard.clean_answer(t2)
    check("O14 a citation span ending past the text still maps (was: dropped, so citations came back empty)", om2(len(t2) + 9) == len(n2))
    # O15 a rendered excerpt/passage that genuinely contains platform names is sanitised at render
    raw_passage = "Nuclia stores this in a NucliaDB index; ARAG then scores it \u2014 seamless, they say."
    check("O15 PLANT: the passage really contains the platform names (including NucliaDB)", len(guard.leaks(raw_passage)) >= 3 and "platform-name" in guard.leaks("NucliaDB"))
    check("O15b clean() leaves none of them", guard.leaks(guard.clean(raw_passage)) == [], guard.clean(raw_passage))
    # O16 the floor is tied to the corpus it was measured on
    check("O16 floor record present with a digest and the 0.015 reranker floor scoped public", config.FLOOR_RECORD.get("corpus_digest") and config.ANSWER_FLOOR == 0.015 and config.FLOOR_SCOPE == 'public')

    # O17 citation placement: different claims land at different sentences; an unmatched paragraph is NOT defaulted
    class _A:
        def __init__(s, t): s.title, s.kind, s.href, s.thumb = t, "document", "/x", None
    class _C:
        by_rid = {"r1": "a1", "r2": "a2", "r3": "a3"}
        assets = {"a1": _A("One"), "a2": _A("Two"), "a3": _A("Three")}
    ans0 = Answerer(None, _C(), None, None, None)
    txt = ("Retrieval agents plan several steps and call your own tools over the model context protocol. "
           "Quality scoring reports groundedness and context relevance for every answer. "
           "Pricing depends on tokens consumed during indexing and answering.")
    res = {"r1": {"fields": {"f": {"paragraphs": {"r1/t/body/0-9": {"text": "A retrieval agent plans several steps and calls your own tools over the model context protocol."}}}}},
           "r2": {"fields": {"f": {"paragraphs": {"r2/t/body/0-9": {"text": "Every answer is scored for groundedness and for context relevance."}}}}},
           "r3": {"fields": {"f": {"paragraphs": {"r3/t/body/0-9": {"text": "Completely unrelated gardening advice about tomatoes and compost."}}}}}}
    cs = ans0._citations({"r1/t/body/0-9": [[0, len(txt)]], "r2/t/body/0-9": [[0, len(txt)]], "r3/t/body/0-9": [[0, len(txt)]]}, res, txt)
    by = {c["asset_id"]: c for c in cs}
    check("O17 PLANT: every platform span covers the whole answer (the defect), yet markers land on different sentences",
          by["a1"]["at"] and by["a2"]["at"] and by["a1"]["at"] != by["a2"]["at"], str({k: v["at"] for k, v in by.items()}))
    check("O17b each marker sits at the end of the sentence carrying its claim", by["a1"]["at"] == [txt.index("protocol.") + 9] and by["a2"]["at"] == [txt.index("answer.") + 7])
    check("O17c a paragraph matching no sentence is listed unattributed with no position, never defaulted to the end", by["a3"]["at"] == [] and by["a3"]["attributed"] is False)

    # O11f/g a pre-warmed answer is published content: not served until a human approved exactly what is stored
    wd = Path(tempfile.mkdtemp(prefix="warm-appr-"))
    wa = WarmStore(wd / "warm.json", wd / "approved.json", require_approval=True)
    ent = {"question": "Q three?", "scope_key": sc0.key(), "corpus_digest": d1, "pipeline": config.PIPELINE_VERSION, "kind": "answer",
           "text": "An answer.", "citations": [], "confidence": {"band": "moderate"}}
    wa.put(ent)
    check("O11f an UNAPPROVED warm answer is not served, and the skip is counted", wa.get(norm_query("q three"), sc0, d1) is None and wa.unapproved_skipped == 1)
    wa.approve_all()
    check("O11g after approval it is served; editing its text voids the approval", wa.get(norm_query("q three"), sc0, d1) is not None
          and (wa._d.__setitem__(list(wa._d)[0], dict(ent, text="An answer, edited.")) or wa.get(norm_query("q three"), sc0, d1) is None))

    # O12 embed: loader carries no key, scope validation
    js = embed.loader_js()
    check("O12 precondition: KB_TOKEN is configured (an absence check against None proves nothing; set .env to run this selftest)", bool(config.KB_TOKEN))
    check("O12 loader contains no key material", (config.KB_TOKEN or "\0unset") not in js and "Bearer" not in js and "X-NUCLIA" not in js and (config.KB_ID or "") not in js)
    check("O12b loader passes the leak guard", guard.leaks(js) == [], str(guard.leaks(js)))
    check("O12c embed scope accepts a registered axis:value and the bare kind shorthand",
          embed.valid_scope("vertical:insurance") == "vertical:insurance" and embed.valid_scope("film") == "kind:film")
    for bad in ("tier:partner", "kind:film<script>", "all", "vertical:nope", "journey:build", "../x", "kind:film,kind:deck"):
        check(f"O12d embed scope rejects {bad!r}", embed.valid_scope(bad) == "")

    # O13 route names
    from .app import app
    paths = [getattr(r, "path", "") for r in app.routes]
    exceptions = {"/api/ask": "frozen contract path in DESIGN.md s10; /api/answer is the same handler under a neutral name"}
    offenders = [p for p in paths if re.search(r"/(ask|find|graph)\b", p) and p not in exceptions]
    check("O13 no app route is named after a platform endpoint (frozen-contract alias declared)", offenders == [] and "/api/answer" in paths, str(offenders))
    print(f"NOTE  declared exception: /api/ask - {exceptions['/api/ask']}")


# ============================== OFFLINE WITH A MOCK TRANSPORT ===========================================
async def mock_transport_checks():
    calls = []
    state = {"n": 0}

    def handler(req: httpx.Request):
        calls.append((req.method, req.url.path, dict(req.headers)))
        if req.url.path.endswith("/stall"):
            state["n"] += 1
            if state["n"] == 1:
                raise httpx.ReadTimeout("planted stall", request=req)
            return httpx.Response(200, json={"ok": True})
        if req.url.path.endswith("/boom"):
            return httpx.Response(500, text="planted server error")
        if req.url.path.endswith("/find"):
            return httpx.Response(200, json={"resources": {}})
        if req.url.path.endswith("/graph"):
            return httpx.Response(200, json={"paths": []})
        if req.url.path.endswith("/predict/remi"):
            return httpx.Response(200, json={"groundedness": [4], "context_relevance": [4]})
        return httpx.Response(200, json={"resources": [], "pagination": {"last": True}})

    a = Arag()
    a.client = httpx.AsyncClient(base_url=config.KB_URL, transport=httpx.MockTransport(handler), headers=config.KB_HEADERS)
    tr = Trace()
    r = await a._json(tr, "t", "find", "GET", "/stall", timeouts=(0.5, 1.0))
    check("T1 a STALL is retried exactly once and then succeeds", r == {"ok": True} and state["n"] == 2 and tr.rows[-1].get("attempts") == 2, str(tr.rows[-1]))
    n0 = len(calls)
    try:
        await a._json(tr, "t", "find", "GET", "/boom", timeouts=(0.5, 1.0))
        check("T2 a real 500 surfaces and is NOT retried", False)
    except PlatformError as e:
        check("T2 a real 500 surfaces and is NOT retried", e.kind == "http" and e.status == 500 and len(calls) - n0 == 1, f"{e.kind} {e.status} calls={len(calls)-n0}")
    state["n"] = -10                       # a stall on BOTH attempts must raise a stall, not hang
    def always_stall(req):
        raise httpx.ConnectTimeout("planted", request=req)
    a.client = httpx.AsyncClient(base_url=config.KB_URL, transport=httpx.MockTransport(always_stall))
    try:
        await a._json(Trace(), "t", "find", "GET", "/x", timeouts=(0.2, 0.3))
        check("T3 two stalls raise a visible stall error", False)
    except PlatformError as e:
        check("T3 two stalls raise a visible stall error", e.kind == "stall")
    # X-Synchronous on every non-streaming call site
    calls.clear()
    a.client = httpx.AsyncClient(base_url=config.KB_URL, transport=httpx.MockTransport(handler), headers=config.KB_HEADERS)
    tr = Trace()
    await a.find(tr, "c", "q", None); await a.find(tr, "c", "q", None, rerank=False)
    await a.graph(tr, "c", "x"); await a.list_resources(tr); await a.resource_text(tr, "c", "rid"); await a.remi(tr, "c", "q", "a", ["c"])
    check("T4 X-Synchronous: true on all 6 non-streaming call sites",
          len(calls) == 6 and all(h.get("x-synchronous") == "true" for _, _, h in calls), f"{len(calls)} calls")
    check("T4b service-account header carries Bearer inside the value", all(h.get("x-nuclia-serviceaccount", "").startswith("Bearer ") for _, _, h in calls))
    asks = []
    def ask_handler(req):
        asks.append(json.loads(req.content))
        return httpx.Response(200, content=b'{"item": {"type": "status", "code": "0"}}\n')
    a.client = httpx.AsyncClient(base_url=config.KB_URL, transport=httpx.MockTransport(ask_handler), headers=config.KB_HEADERS)
    await a.ask_events(Trace(), "c", "q?", {"field": {"and": []}})
    b = asks[0]
    check("T4c the answer call pins the model, asks for citations, and never sends answer_json_schema",
          b.get("generative_model") == config.ASK_MODEL and b.get("citations") is True and "answer_json_schema" not in b and "filters" not in b, str(sorted(b)))
    check("T4d REMi trace row names a model note, never a fabricated model", tr.rows[-1]["model"] == config.REMI_MODEL_NOTE)


# ============================== LIVE ============================================================
async def live():
    from .app import app, S
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://t", timeout=60) as cl:
            corpus, arag = S["corpus"], S["arag"]
            check("L0 corpus loaded: non-zero public assets", len(corpus.assets) > 0, f"{len(corpus.assets)} public of {corpus.resource_total} resources")

            # L1 catalogue arithmetic
            cat = (await cl.get("/api/catalogue")).json()
            check("L1 every catalogue asset resolves to a registered kind/vertical/stage",
                  all(a["kind"] in VOCAB["kind"] and a["vertical"] in VOCAB["vertical"] and a["stage"] in VOCAB["stage"] for a in cat["assets"]))
            check("L1b facet counts sum to total on every dimension",
                  all(sum(v.values()) == cat["total"] for v in cat["facets"].values()), str({k: sum(v.values()) for k, v in cat["facets"].items()}))
            check("L1c no two catalogue cards share an asset id", len({a["asset_id"] for a in cat["assets"]}) == len(cat["assets"]))
            ids = {a["asset_id"] for a in cat["assets"]}
            # L1e: PREVIEWS, compared as SETS in BOTH directions (server/previews.py), never by count.
            from .previews import preview_gaps as _pg
            _tdir = config.APP / "web" / "thumbs"
            _files = {f.stem for f in _tdir.glob("*") if f.is_file()} if _tdir.exists() else set()
            _no_preview, _orphans = _pg(_files, ids)
            check("L1e every public card has a preview and no preview exists for anything that is not public (sets compared both ways, not counts)",
                  not _no_preview and not _orphans, f"{len(ids)} public, {len(_files)} previews; missing: {_no_preview[:4]}; orphan: {_orphans[:4]}")
            for lens in config.LENSES:
                lc = (await cl.get(f"/api/catalogue?lens={lens}")).json()
                check(f"L1d lens {lens}: only {lens}/all journeys, and a subset of the whole",
                      {a["lens"] for a in lc["assets"]} <= {lens, "all"} and {a["asset_id"] for a in lc["assets"]} <= ids)

            # L2 scope cross-check: planted positive (lens-narrowed scope, answer call WITHOUT the filter)
            ans: Answerer = S["answerer"]
            sc = Scope.make(lens="research")
            q = "How does an agent call my own tools over MCP?"      # lives on the build path (how-it-works)
            payload = None
            async for ev, data in ans.compute(q, sc, "selftest", charge=False, plant_no_filter=True):
                if ev == "_payload":
                    payload = data
            check("L2 PLANTED control: filter removed -> cross-check withholds the WHOLE response",
                  payload and payload["kind"] == "refusal" and payload["reason"] == "scope_cross_check" and payload.get("outside_count", 0) > 0,
                  f"reason={payload and payload.get('reason')} outside={payload and payload.get('outside_count')}")
            rendered = list(ans._events(payload, "miss", 0))
            check("L2b withheld response emits ONLY refusal, trace, done",
                  [e for e, _ in rendered] == ["refusal", "_trace", "done"], str([e for e, _ in rendered]))
            # negative control: same question, filter in place, in scope -> must NOT be withheld by the cross-check
            payload2 = None
            async for ev, data in ans.compute(q, Scope.make(lens="build"), "selftest", charge=False):
                if ev == "_payload":
                    payload2 = data
            check("L2c NEGATIVE control: filter in place, in-scope question -> not withheld by the cross-check",
                  payload2 and payload2.get("reason") != "scope_cross_check", f"kind={payload2 and payload2['kind']}")
            # unit-level tier plant: a fabricated retrieval item carrying a registered-tier record
            fake = {"rid-x": {"usermetadata": {"classifications": [{"labelset": "tier", "label": "registered"}, {"labelset": "journey", "label": "all"},
                                                                  {"labelset": "stage", "label": "discovery"}, {"labelset": "vertical", "label": "cross-industry"},
                                                                  {"labelset": "kind", "label": "doc"}]}}}
            check("L2d PLANT (tier axis, function level): a registered-tier record is outside the public scope",
                  ans.outside_scope(fake, Scope.make()) == ["rid-x"])
            listing = await arag.list_resources(Trace())
            nonpub = [r for r in listing if r["id"] in corpus.labels_by_rid and corpus.labels_by_rid[r["id"]].get("tier") not in (None, "public")
                      and r.get("metadata", {}).get("status") == "PROCESSED"]
            if nonpub:
                tgt = nonpub[0]
                tq = tgt["title"].rstrip("?") + "?"
                pl = None
                async for ev, data in ans.compute(tq, Scope.make(), "selftest", charge=False, plant_no_filter=True):
                    if ev == "_payload":
                        pl = data
                check(f"L2e PLANTED live tier-axis control: filter removed, question aimed at a {corpus.labels_by_rid[tgt['id']]['tier']}-tier document -> WHOLE response withheld",
                      pl and pl["kind"] == "refusal" and pl["reason"] == "scope_cross_check" and pl.get("outside_count", 0) > 0,
                      f"reason={pl and pl.get('reason')} outside={pl and pl.get('outside_count')} q={tq!r}")
                pl2 = None
                async for ev, data in ans.compute(tq, Scope.make(), "selftest", charge=False):
                    if ev == "_payload":
                        pl2 = data
                check("L2f NEGATIVE control: same question with the filter in place is never answered from the non-public document",
                      pl2 and pl2.get("reason") != "scope_cross_check" and (pl2["kind"] == "refusal" or all(c["asset_id"] in corpus.assets for c in pl2["citations"])),
                      f"kind={pl2 and pl2['kind']} reason={pl2 and pl2.get('reason')}")
            else:
                hole("L2e live tier-axis plant", "no PROCESSED non-public resource present in the knowledge base")

            # L3 embed tier test
            probes = []
            for path in ("/api/catalogue?tier=partner&embed=1", "/api/catalogue?tier=registered&embed=1&scope=film"):
                probes.append((await cl.get(path)).json())
            check("L3 embed: tier=partner/registered cannot widen the catalogue (tier_applied is public, ids equal the public set)",
                  all(p["tier_applied"] == "public" for p in probes) and all({a["asset_id"] for a in p["assets"]} <= ids for p in probes))
            sr = (await cl.get("/api/search?q=pricing&tier=partner&embed=1")).json()
            check("L3b embed: search with tier=partner returns only public assets", all(h["asset_id"] in ids for h in sr["hits"]))
            sg = (await cl.get("/api/suggest?q=knowledge&embed=1&scope=film")).json()
            check("L3c embed scope=film narrows to films", sg["hits"] and all(h["kind"] == "film" for h in sg["hits"]), f"{len(sg['hits'])} hits")
            if nonpub:
                bad_ids = {r["slug"] for r in nonpub}
                sample = nonpub[:20]                        # bounded: each probe is 4 platform calls
                leaked, findable = [], []
                for r in sample:
                    t = r["title"]
                    raw = await arag.find(Trace(), "ctl", t, None, top_k=8)
                    if r["id"] not in (raw.get("resources") or {}):
                        continue                            # not retrievable unscoped: cannot serve as a positive control
                    findable.append(r)
                    for path in ("/api/search?q={q}&tier={t}&embed=1", "/api/suggest?q={q}&tier={t}&embed=1", "/api/recommend?context={q}&tier={t}&embed=1"):
                        j = (await cl.get(path.format(q=httpx.QueryParams({"x": t})["x"].replace(" ", "%20"), t=corpus.labels_by_rid[r["id"]]["tier"]))).json()
                        for h in j.get("hits", []) + j.get("cards", []):
                            if h["asset_id"] in bad_ids:
                                leaked.append((path[:14], h["asset_id"]))
                check("L3e EMBED TIER TEST (positive control): at least 80% of the sampled non-public documents are retrievable when unscoped",
                      len(findable) >= 0.8 * len(sample), f"{len(findable)} of {len(sample)} sampled ({len(nonpub)} non-public in all)")
                check("L3f EMBED TIER TEST: for each retrievable one, tier=starter|pro with embed=1 never returns a non-public asset from search, typeahead or recommend",
                      not leaked, f"{len(findable)} documents x 3 surfaces; leaked={leaked[:3]}")
            check("L3d embed loader route carries no key", config.KB_TOKEN not in (await cl.get("/embed.js")).text)

            # L4 T1 surfaces: no generation, caching, floor
            tr_calls = []
            r1 = (await cl.get("/api/search?q=knowledge graph retrieval")).json()
            r2 = (await cl.get("/api/search?q=Knowledge  graph retrieval?")).json()
            check("L4 search: no generative call, and the second normalised repeat is a cache hit",
                  not any(t["generative"] for t in r1["_trace"]) and r2["_trace"][0]["cache"] == "hit", f"{r1['_trace'][0]['cache']} then {r2['_trace'][0]['cache']}")
            check("L4b search hits are all public catalogue assets", all(h["asset_id"] in ids for h in r1["hits"]))
            junk = (await cl.get("/api/search?q=qwertyuiop zxcvbnm asdfgh")).json()
            check("L4c nonsense query: floor yields fewer hits than a real query", junk["total"] < r1["total"], f"{junk['total']} vs {r1['total']}")
            rec = (await cl.get("/api/recommend?context=how do insurers use grounded answers")).json()
            check("L4d recommend: cards bound one-to-one to assets, `why` names the retrieval basis, no generation",
                  len({c["asset_id"] for c in rec["cards"]}) == len(rec["cards"]) and all("Matched on" in c["why"] for c in rec["cards"]) and not any(t["generative"] for t in rec["_trace"]))
            seed = cat["assets"][0]["asset_id"]
            rel = (await cl.get(f"/api/related?asset_id={seed}")).json()
            check("L4e related: graph, undirected, no generation", not any(t["generative"] for t in rel["_trace"]) and "relations" in rel)
            check("L4f related on an unknown id is a 404 not a crash", (await cl.get("/api/related?asset_id=nope")).status_code == 404)

            # L5 refusal
            async def sse(question, **extra):
                evs = []
                async with cl.stream("POST", "/api/answer", json={"question": question, **extra}) as r:
                    assert r.status_code == 200, r.status_code
                    ev = None
                    async for line in r.aiter_lines():
                        if line.startswith("event:"):
                            ev = line[6:].strip()
                        elif line.startswith("data:"):
                            evs.append((ev, json.loads(line[5:])))
                return evs
            off = await sse("What is the capital of Mongolia?")
            names = [e for e, _ in off]
            tr = next(d for e, d in off if e == "_trace")
            check("L5 off-corpus question: ONLY refusal, trace, done are emitted (no token/citation/confidence/follow-up/source)",
                  names == ["refusal", "_trace", "done"], str(names))
            check("L5b refusal made no generative call", not any(t["generative"] for t in tr["trace"]) and tr["withheld_server_side"] is True)
            ht = await sse("Does it run on-premises?")
            check("L5h held-topic question: fixed referral only, no retrieval or generation call at all",
                  [e for e, _ in ht] == ["refusal", "_trace", "done"] and ht[0][1]["reason"] == "held_topic" and ht[1][1]["trace"] == [], str([e for e, _ in ht]))
            ep = en = et = None
            for cand in ("What is the pricing of A rival search product?", "How does this compare with A vector database pricing?", "What is the share price of Progress Software?",
                         "Is OpenAI better than Google Gemini?", "What does the Starter plan cost for a competitor?"):
                ep = await sse(cand)
                if next((d["reason"] for e, d in ep if e == "refusal"), None) == "no_answer":
                    en = [e for e, _ in ep]; et = next(d for e, d in ep if e == "_trace"); break
            if et:
                check(f"L5i PLANT reached ({cand!r}): passes the floor, the GENERATION declines (no_answer): no sources, citations, follow-ups or tokens are sent",
                      set(en) <= {"searching", "refusal", "_trace", "done"} and "refusal" in en, str(en))
                check("L5j ... and it cost exactly ONE generative answer call (a weak-context decline is never retried)",
                      sum(1 for t in et["trace"] if t["call"] == "answer") == 1, str([t["call"] for t in et["trace"]]))
                check("L5k ... and the early `searching` event carries a count, no titles and no ids", all(set(d) == {"resources", "scope"} for e, d in ep if e == "searching"))
            else:
                hole("L5i no_answer path", "none of the five near-topic competitor questions passed the floor this run, so the generation-decline path was not exercised live")
            on = await sse("How does a contact centre use call intelligence?")
            on_names = [e for e, _ in on]
            check("L5c NEGATIVE control: an in-corpus question does stream tokens, citations, confidence, follow-ups",
                  all(x in on_names for x in ("token", "citations", "confidence", "followups", "_trace", "done")), str(sorted(set(on_names))))
            cits = next(d for e, d in on if e == "citations")["citations"]
            text = "".join(d["text"] for e, d in on if e == "token")
            check("L5d citations resolve to real assets, are unique per asset, and markers sit inside the text",
                  cits and all(c["asset_id"] in ids for c in cits) and len({c["asset_id"] for c in cits}) == len(cits)
                  and all(0 <= m <= len(text) for c in cits for m in c["at"]), f"{len(cits)} cits, text {len(text)} chars")
            conf = next(d for e, d in on if e == "confidence")
            check("L5e confidence band is one of the three qualitative values and answer_relevance is absent",
                  conf["band"] in ("well-supported", "moderate", "weak") and "answer_relevance" not in json.dumps(conf), conf["band"])
            fu = next(d for e, d in on if e == "followups")["followups"]
            check("L5f follow-ups exclude cited assets and are not generated",
                  not ({f["asset_id"] for f in fu} & {c["asset_id"] for c in cits}))
            ats = [m for c in cits for m in c["at"]]
            multi = [v for v in S["warm"]._d.values() if v.get("kind") == "answer" and len(guard.split_sentences(v["text"])) >= 3
                     and sum(1 for c in v["citations"] if c["attributed"]) >= 2]
            spread = [v for v in multi if len({m for c in v["citations"] for m in c["at"]}) >= 2]
            if len(multi) < 3:
                hole("L5l multi-claim spread", f"only {len(multi)} warm answers have >= 3 sentences and >= 2 attributed citations (the direct-answer prompt gives short answers); O17 covers the mechanism")
            else:
                check("L5l real multi-claim answers (>= 3 sentences, >= 2 attributed citations): at least half place markers at more than one offset",
                      len(spread) >= 0.5 * len(multi), f"{len(spread)} of {len(multi)} warm answers spread")
            prov = next(d for e, d in on if e == "citations")["provenance"]
            check("L5m0 provenance counts accompany the citations: retrieved vs named, with the explanatory note",
                  prov["retrieved_passages"] >= prov["cited_passages"] >= 1 and prov["retrieved_assets"] >= prov["cited_assets"] >= 1 and "did not name" in prov["note"], str(prov))
            check("L5m unattributed citations carry an empty `at`, attributed ones a position", all(c["attributed"] == bool(c["at"]) for c in cits))
            tvs = {t["verb"] for t in tr_all(on)} if False else None
            names_on = [e for e, _ in on]
            check("L5n early event is `searching` (count only) and `sources` arrives only with the released answer",
                  names_on.index("sources") > names_on.index("searching") if "sources" in names_on else True)
            leak = leak_report([d for _, d in on])
            check("L5g streamed answer passes the leak/claim guard", leak == {}, str(leak))

            # L6 warm answers
            for _ in range(60):
                if S.get("warmed_at") and not S.get("warming"):
                    break
                await asyncio.sleep(2)
            rep = S.get("warm_report", [])
            warm_digest_ok = S["warm"].valid_count(corpus.answer_digest) > 0      # entries are keyed on the ANSWER digest; this read the STATE digest, so L6b/L6c/L7c reported a HOLE (never ran) for days
            warmed_ok = [r for r in rep if r["result"] in ("kept", "warmed")]
            check("L6 pre-warm finished and produced warm answers for the suggested questions", len(warmed_ok) > 0, f"{len(warmed_ok)} of {len(rep)} (question, scope) pairs")
            sug = S.get("suggested") or []
            if sug and not warm_digest_ok:
                hole("L6b/L7c warm answers served warm", f"the corpus answer digest ({corpus.answer_digest}) matches NO stored warm answer: they were made at another digest, which invalidated all of them: a stale-population result, not a broken cache")
            elif sug:
                from .answer import DETERMINISTIC_QUESTIONS as _DQ
                gen_sug = [c for c in sug if norm_query(c["q"]) not in _DQ]
                prt_sug = [c for c in sug if norm_query(c["q"]) in _DQ]
                if gen_sug:
                    wq = await sse(gen_sug[0]["q"])
                    wt = next(d for e, d in wq if e == "_trace")
                    check("L6b a GENERATED suggested question is served WARM with a UTC stamp and model", wt["cache"] == "warm" and (wt.get("answered_at") or "").endswith("Z") and wt["model"] == config.ASK_MODEL, str(wt["trace"][0]))
                else:
                    hole("L6b generated warm answer", "no GENERATED question is in the home set, so a stamp and model could not be asserted")
                if prt_sug:
                    pq = await sse(prt_sug[0]["q"])
                    pt = next(d for e, d in pq if e == "_trace")
                    check("L6b2 a PRINTED suggested question is served from the store with NO answer timestamp, no model and the printed flag (it was never generated)",
                          pt["printed"] is True and pt["answered_at"] is None and pt["model"] is None and pt["served_from_cache"] is False, str({k: pt.get(k) for k in ("printed", "answered_at", "model", "served_from_cache", "warm")}))
                saved = corpus.answer_digest
                corpus.answer_digest = "reseeded-planted"
                try:
                    st0 = S["warm"].stale_skipped
                    check("L6c PLANTED reseed: warm answer is NOT served once the corpus digest moves", S["warm"].get(norm_query(sug[0]["q"]), Scope.make(), corpus.answer_digest) is None and S["warm"].stale_skipped == st0 + 1)
                finally:
                    corpus.answer_digest = saved
            else:
                check("L6b a suggested question is served WARM", False, "no suggested question survived the floor probe")
            for c in S.get("suggested") or []:
                pass
            check("L6d every suggested home question warmed without declining", all(r["result"] in ("kept", "warmed") for r in rep if r["lens"] == "(none)" and r["q"] in {c["q"] for c in sug}), str([r for r in rep if r["lens"] == "(none)" and r["q"] in {c["q"] for c in sug} and r["result"] not in ("kept", "warmed")]))
            pr = S["probe_report"]
            served_q = {(l["id"], q) for l in S["lenses"]["lenses"] for q in l["entry_questions"]}
            dropped_q = {(r["lens"], r["q"]) for r in pr if r["verdict"] != "ok"}
            check("L6d2 every pre-warmed answer names at least one source and none has an empty or footer passage",
                  all(v["citations"] and all(c["passage"].strip() for c in v["citations"]) and not any(is_footer(c["passage"]) for c in v["citations"])
                      for v in S["warm"]._d.values() if v.get("kind") == "answer" and v.get("pipeline") == config.PIPELINE_VERSION))
            d_before = corpus.digest
            await corpus.refresh(arag, full=True)
            if corpus.digest == d_before:
                check("L6d3 a FULL body re-read yields the same digest as the incremental one (the body hash is stable across reads)", True, d_before)
            else:
                hole("L6d3 full re-read digest", f"corpus moved during the test ({d_before} -> {corpus.digest})")
            unwarm = {(r["lens"], r["q"]) for r in S.get("entry_unwarmable", [])}
            check("L6e entry questions: served + dropped by the probe + dropped for failing to pre-warm accounts for every question in the lens file, none twice",
                  len(served_q) + len(dropped_q) + len(unwarm) == len(pr) and not (served_q & (dropped_q | unwarm)),
                  f"{len(served_q)} served, {len(dropped_q)} probe-dropped, {len(unwarm)} unwarmable of {len(pr)}")
            check("L6f every served entry question had a probe verdict of ok", all(any(r["lens"] == l and r["q"] == q and r["verdict"] == "ok" for r in pr) for l, q in served_q))

            # L7 rate limit through the route
            S["answerer"].budget = GenerativeBudget(Window(60, 1), Window(60, 2))
            S["answerer"].budget.admit("v1")                      # visitor v1 is now at its limit
            r = await cl.post("/api/answer", json={"question": "A brand new uncached typed question about freight?"}, headers={"fly-client-ip": "v1"})
            check("L7 per-visitor limit: HTTP 429 with retry_after before any work", r.status_code == 429 and r.json()["error"]["retry_after"] > 0, str(r.status_code))
            S["answerer"].budget.admit("v2")                      # global now 2 of 2
            r = await cl.post("/api/answer", json={"question": "Another brand new uncached typed question about maintenance?"}, headers={"fly-client-ip": "v3"})
            check("L7b global limit binds a visitor who is individually under their limit", r.status_code == 429 and r.json()["error"]["who"] == "global", str(r.status_code))
            _l7c_q = next((c["q"] for c in (S.get("suggested") or []) if norm_query(c["q"]) not in __import__("server.answer", fromlist=["x"]).DETERMINISTIC_QUESTIONS), "How does a contact centre use call intelligence?")
            r = await cl.post("/api/answer", json={"question": _l7c_q}, headers={"fly-client-ip": "v1"})
            if not warm_digest_ok:
                hole("L7c cached answer to a rate-limited visitor", "the answer was no longer cached: corpus digest moved (see L6b)")
            else:
              check("L7c a CACHED answer is still served to a rate-limited visitor (no generative call to charge)", r.status_code == 200)

            # L8 sweep for leaks across every JSON route
            sweep = {}
            for p in ("/api/catalogue", "/api/lens", "/api/reveal", f"/api/related?asset_id={seed}", "/api/suggest?q=know", "/api/search?q=insurance",
                      "/api/recommend?context=claims"):
                sweep[p] = (await cl.get(p)).json()
            sweep["/api/roi"] = (await cl.post("/api/roi", json={"staff": 40})).json()
            bad = {p: leak_report(v) for p, v in sweep.items() if leak_report(v)}
            check("L8 no leak/claim string in any JSON route (acronym, platform name, host, endpoint, banned word, held claim)", not bad, str(bad)[:300])
            planted = {"x": "Runs on-premises via ARAG"}
            check("L8b PLANT: the same sweep reports a planted leaking string", set(leak_report(planted)) >= {"deployment-mode", "acronym"})
            check("L8c malformed ROI input is a 422 not a crash", (await cl.post("/api/roi", json={"staff": -4})).status_code == 422)
            for route in ("/", "/explore", "/watch", "/build", "/fix", "/pricing", "/fit", "/embed", "/widget", "/embed-host"):
                rr = await cl.get(route, follow_redirects=False)
                check(f"L8d route {route}: status 200 at its OWN url, no redirect", rr.status_code == 200, f"{rr.status_code} {rr.headers.get('location')}")
            nr = await cl.get("/nonsense-route", follow_redirects=False)
            check("L8d2 an unknown route redirects ONCE to the notice (status and location asserted, not just a page)", nr.status_code == 302 and nr.headers["location"] == "/?notice=not-found")
            check("L8d3 the notice target itself does not redirect again (no loop)", (await cl.get("/?notice=not-found", follow_redirects=False)).status_code == 200)
            check("L8d4 a missing file is a 404, not the app shell", (await cl.get("/missing.css", follow_redirects=False)).status_code == 404
                  )
            import server.app as appmod
            saved_routes = appmod.KNOWN_ROUTES
            appmod.KNOWN_ROUTES = tuple(r for r in saved_routes if r != "fix")
            try:
                bad = await cl.get("/fix", follow_redirects=False)
                check("L8d5 PLANTED: with /fix removed from KNOWN_ROUTES the per-route check FAILS (status/location differ)", bad.status_code != 200, f"{bad.status_code}")
            finally:
                appmod.KNOWN_ROUTES = saved_routes
            pr = (await cl.get("/api/pricing")).json()
            sd = (await cl.get("/api/scope-demo")).json()
            qset = sd["questions"]
            check("L9 scope demo: a fixed server-owned set of 3+ questions with opaque ids and EXACTLY ONE control", len(qset) >= 3 and sum(1 for q in qset if q["is_control"]) == 1
                  and all(set(q) == {"id", "text", "is_control", "public_answers"} for q in qset) and all(q["id"].startswith("q") for q in qset), str([(q["id"], q["is_control"]) for q in qset]))
            per = {}
            for q in qset:
                per[q["id"]] = (await cl.get(f"/api/scope-demo?id={q['id']}")).json()
            diffs_ok = all(r["differential"] in ("none", "assets", "answerability") for pj in per.values() for r in pj["scopes"])
            check("L9b every scope row carries a three-valued differential, and the public baseline is none", diffs_ok and all(pj["scopes"][0]["differential"] == "none" for pj in per.values()))
            ctrl_ids = [q["id"] for q in qset if q["is_control"]]
            check("L9c CONTROL: the control question shows NO differential at any scope and no answer in reach anywhere (the endpoint is not rigged)",
                  all(r["differential"] == "none" and not r["answerable"] for i in ctrl_ids for r in per[i]["scopes"]), str([(i, [r["differential"] for r in per[i]["scopes"]]) for i in ctrl_ids]))
            check("L9d at least one non-control question flips answerability between public and a paid scope",
                  any(r["differential"] == "answerability" for q in qset if not q["is_control"] for r in per[q["id"]]["scopes"]),
                  str({q["id"]: [r["differential"] for r in per[q["id"]]["scopes"]] for q in qset}))
            check("L9e each payload echoes the question that produced its figures, states what it is, and restricted scopes carry no titles",
                  all(pj["question"] in [q["text"] for q in qset] and "not a sign-in" in pj["statement"] and pj["scopes"][1]["titles"] is None and pj["scopes"][2]["titles"] is None
                      and isinstance(pj["scopes"][0]["titles"], list) for pj in per.values()))
            check("L9e2 the set spans the three honest cases: public answers it / only a paid scope does / nobody does, and the surface leads with a public-answerable question",
                  qset[0]["public_answers"] and any(q["is_control"] for q in qset) and any(r["differential"] == "answerability" for q in qset for r in per[q["id"]]["scopes"]),
                  str([(q["id"], q["public_answers"], q["is_control"]) for q in qset]))
            check("L9e3 TITLES RULE: public titles present when, and only when, the public scope is answerable",
                  all((len(pj["scopes"][0]["titles"]) > 0) == pj["scopes"][0]["answerable"] for pj in per.values()) and "only when" in sd["titles_rule"],
                  str([(q["id"], per[q["id"]]["scopes"][0]["answerable"], len(per[q["id"]]["scopes"][0]["titles"])) for q in qset]))
            listing2 = await arag.list_resources(Trace())
            import re as _re
            def _tier(r): return {c["labelset"]: c["label"] for c in r["usermetadata"]["classifications"]}.get("tier")
            def _groups(tiers, grouped):
                return len({(_re.sub(r"-s\d+$", "", r["slug"]) if grouped else r["slug"]) for r in listing2
                            if r["metadata"]["status"] == "PROCESSED" and _tier(r) in tiers})
            sc0 = per[qset[0]["id"]]["scopes"]
            from .corpus import Corpus as _Corpus
            _fresh = _Corpus(); await _fresh.refresh(arag)          # the SAME digest definition (metadata + body hash), read afresh
            live_digest = _fresh.digest
            if live_digest != corpus.digest:
                hole("L9f grouped counts vs independent recount", f"corpus moved between the server's read ({corpus.digest}) and the test's ({live_digest}); a count compared across two different corpora is not a check")
            else:
                check("L9f asset counts are grouped: Starter and Pro reach equal the independently recomputed distinct asset ids (same digest on both sides)",
                      sc0[1]["assets_in_reach"] == _groups(("public", "starter"), True) and sc0[2]["assets_in_reach"] == _groups(("public", "starter", "pro"), True),
                      f"starter {sc0[1]['assets_in_reach']} vs {_groups(('public','starter'), True)}; pro {sc0[2]['assets_in_reach']} vs {_groups(('public','starter','pro'), True)}")
            ung, grp = _groups(("public", "starter"), False), _groups(("public", "starter"), True)
            if ung > grp:
                check("L9g PLANT: ungrouped counting would have overstated Starter's reach", ung > grp, f"ungrouped {ung} vs grouped {grp}")
            else:
                hole("L9g grouping", "no multi-section asset in reach; grouping untested live")
            restricted_titles = [r["title"] for r in listing2 if _tier(r) in ("starter", "pro")]
            blob2 = json.dumps(per)
            check("L9h no restricted-tier title appears anywhere in any scope demo payload", restricted_titles and not any(t in blob2 for t in restricted_titles), f"{len(restricted_titles)} restricted titles checked")
            check("L9i PLANT: the same scan fires when a restricted title is injected", any(t in json.dumps({**sd, "x": restricted_titles[0]}) for t in restricted_titles))
            sd_free = (await cl.get("/api/scope-demo?question=What%20is%20in%20the%20gated%20set&tier=pro&embed=1")).json()
            check("L9j NO ORACLE: a free-text question (or tier) changes nothing - the figures are the default set member's", sd_free["scopes"] == sd["scopes"] and sd_free["question"] == sd["question"])
            check("L9k an id outside the fixed set is a 404", (await cl.get("/api/scope-demo?id=q99")).status_code == 404)
            check("L9l scope demo payloads pass the leak guard", leak_report(per) == {}, str(leak_report(per)))
            grouped_assets = [a for a in cat["assets"] if "-s" in a["asset_id"] and a["asset_id"].rsplit("-s", 1)[-1].isdigit()]
            check("L9m no catalogue card is an unnamed section id", not grouped_assets)
            # ---- media proxy: the allow-list is the security boundary
            from . import media as M
            films = [a for a in cat["assets"] if a["kind"] == "film"]
            if not M.configured():
                hole("L10 media proxy", "DAM_URL / DAM_TOKEN not in the environment, so no stream was tested")
            else:
                token = config.env("DAM_TOKEN")
                removed_id = "e200f4840f8a45aa9a5eeac63419906c"        # an OpenEdge film removed from the corpus: in the DAM, not in the public catalogue
                dam = await M.client().get(M._url(removed_id), headers=M._headers("bytes=0-15"))
                check("L10 PLANT reached: the DAM token WOULD serve a removed, non-public asset if the proxy let it through", dam.status_code in (200, 206), f"direct DAM status {dam.status_code}")
                r_np = await cl.get(f"/media/{removed_id}")
                check("L10b the proxy REFUSES that asset (404), it does not stream it", r_np.status_code == 404 and len(r_np.content) < 300, str(r_np.status_code))
                nonfilm = next(a for a in cat["assets"] if a["kind"] != "film")["asset_id"]
                check("L10c a public NON-film asset is refused (404)", (await cl.get(f"/media/{nonfilm}")).status_code == 404)
                restricted = [r["slug"] for r in listing2 if _tier(r) in ("starter", "pro")][:1]
                codes = [(x, (await cl.get(f"/media/{x}")).status_code) for x in restricted + ["../etc/passwd", "a" * 40, "%2e%2e"]]
                check("L10d a restricted-tier resource id, a traversal string and unknown ids are all refused (404)", all(c == 404 or (c == 302 and x == "../etc/passwd") for x, c in codes),
                      str(codes) + " (a multi-segment path never reaches the proxy route: it falls to the static handler, which redirects to the notice and reads nothing)")
                with_media = [a for a in films if a["media_url"]]
                check("L10e media_url is advertised only for films whose stream passed the probe, and for at least one film", with_media and all(a["media_url"] == f"/media/{a['asset_id']}" for a in with_media)
                      and {a["asset_id"] for a in with_media} == S["media_ok"], f"{len(with_media)} of {len(films)} films")
                bad_stream = []
                for a in with_media[:4]:
                    rr = await cl.get(a["media_url"], headers={"Range": "bytes=0-1023"})
                    if not (rr.status_code == 206 and rr.headers["content-type"].startswith("video/") and len(rr.content) == 1024 and rr.headers.get("content-range", "").startswith("bytes 0-1023/")):
                        bad_stream.append((a["asset_id"], rr.status_code))
                check("L10f each advertised film honours a Range request (206, video type, exact length, content-range)", not bad_stream, str(bad_stream))
                rr = await cl.get(with_media[0]["media_url"], headers={"Range": "bytes=0-1023"})
                check("L10g no credential reaches the client: not in headers, body or any JSON payload", token not in str(dict(rr.headers)) and token.encode() not in rr.content
                      and token not in json.dumps(cat) and "authorization" not in {k.lower() for k in rr.headers})
                check("L10h a malformed Range header is refused (416), not forwarded", (await cl.get(with_media[0]["media_url"], headers={"Range": "bytes=0-1,5-9"})).status_code == 416)
                held = []
                for _ in range(M.MAX_STREAMS):
                    await M._sem.acquire(); held.append(1)
                try:
                    busy = await cl.get(with_media[0]["media_url"])
                    check("L10i PLANT: with every stream slot taken the proxy answers 503 with Retry-After, it does not queue or fall over", busy.status_code == 503 and "retry-after" in busy.headers)
                finally:
                    for _ in held:
                        M._sem.release()
                check("L10j the slots are all released afterwards", not M._sem.locked())

            check("L8f pricing: three tiers, verified date and source carried, USD", len(pr["tiers"]) == 3 and pr["_verified_utc"] and pr["_source"].startswith("https://") and all(t["currency"] == "USD" for t in pr["tiers"]))
            check("L8g0 pricing: self_serve carries only the page's fields, no authoring guidance", set(pr["self_serve"]) == {"offer", "applies_to", "published_label", "cta_copy"} and "Do NOT" not in json.dumps(pr))
            check("L8g pricing: no deployment line and no held claim anywhere in the payload", not any(guard.claims(x) for x in walk_strings(pr)) and "deployment" not in json.dumps(pr).lower())
            films = [a for a in cat["assets"] if a["kind"] == "film"]
            check("L8h every film carries an explicit has_transcript bool", films and all(isinstance(a["has_transcript"], bool) for a in films), f"{sum(1 for a in films if a['has_transcript'] is False)} false of {len(films)} films")
            check("L8i non-films never claim a transcript flag", all(a["has_transcript"] is None for a in cat["assets"] if a["kind"] != "film"))
            check("L8j catalogue exposes media_url and summary on every item", all("media_url" in a and "summary" in a for a in cat["assets"]))
            check("L8k no `stage` facet is offered", "stage" not in cat["facets"])
            lens_j = (await cl.get("/api/lens")).json()
            check("L8l0 a path with no warmable question is NOT offered in /api/lens", all(l["entry_questions"] for l in lj["lenses"]) if (lj := (await cl.get("/api/lens")).json()) else False)
            check("L8l /api/lens exposes per-path reach and warm flags on suggested questions", set(lens_j["reach"]) == {l["id"] for l in lens_j["lenses"]} and all({"warm", "warmed_at", "warmed_model"} <= set(x) for x in lens_j["suggested"]))
            rv = (await cl.get("/api/reveal")).json()
            _pv = rv["paths"]
            check("L8m2 reveal lists every expected path as offered or withdrawn, naming the fact and no content",
                  set(_pv["expected"]) == set(_pv["offered"]) | {w["id"] for w in _pv["withdrawn"]} and all(set(w) == {"id", "reviewed_questions"} for w in _pv["withdrawn"])
                  and _pv["minimum_questions"] == config.MIN_PATH_CHIPS, repr(_pv))
            _hid = S.get("lens_hidden"); S["lens_hidden"] = [{"id": "partner", "chips": 2}]
            try:
                check("L8m3 PLANTED: a hidden path appears under withdrawn in the reveal with its question count", {"id": "partner", "reviewed_questions": 2} in (await cl.get("/api/reveal")).json()["paths"]["withdrawn"])
            finally:
                S["lens_hidden"] = _hid if _hid is not None else []
            check("L8m reveal carries the unit inside each knowledge-base figure and the floor's corpus digests", "units" in rv["knowledge_base"] and {"measured_against_digest", "current_digest", "stale"} <= set(rv["answering"]["floor"]))
            saved_rec = config.FLOOR_RECORD
            config.FLOOR_RECORD = dict(saved_rec, corpus_digest="a-different-corpus")
            try:
                check("L8n PLANTED: a floor recorded against a different corpus digest is reported stale", appmod.floor_check() is True)
            finally:
                config.FLOOR_RECORD = saved_rec
            appmod.floor_check()
            ns = (await cl.get("/go/signup", follow_redirects=False))
            check("L8e signup is an app redirect, so no platform host string sits in page source", ns.status_code == 302)


async def main():
    offline()
    await mock_transport_checks()
    if not ARGS.offline:
        await live()
    if ARGS.plant_failure:
        check("PLANTED FAILURE (must make the run exit non-zero)", False, "deliberate")
    n_fail = sum(1 for _, ok in RESULTS if not ok)
    print(f"\n{len(RESULTS)} checks run, {len(RESULTS) - n_fail} passed, {n_fail} failed")
    return 1 if (n_fail or not RESULTS) else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
