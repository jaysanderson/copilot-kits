#!/usr/bin/env python3
"""estate_health.py - standing health check across every live ARAG demo in the estate.

WHY THIS EXISTS (29 Sep 2026): the Clinic demo passed every build-time gate,
was submitted to the GM's review queue at 07:59, and at ~08:02 the ARAG platform's
Azure-hosted generative models started failing platform-wide - every question on
the live demo started 530ing. The GM opened it in front of a customer and got
errors. Every gate this factory runs (demo_qa_gate.py, demo-tester, qa-reviewer)
is a ONE-TIME gate at submission. Nothing watches a shipped demo afterward. This
script is that standing watch.

WHAT IT CHECKS (and what it deliberately does NOT):
  - It probes each demo's REAL answer path - the app's own server-side proxy route
    that makes a live ARAG call - not just the homepage. A 200 on the SPA shell
    proves nothing; that is exactly the failure mode that bit us (the app was up,
    the answers were dead).
  - It asserts: HTTP 2xx, a non-empty answer body, response time under a
    threshold, and the answer is not a known platform/config error string. A
    genuine honest decline ("I don't have information about that in the
    published content") is NOT a failure - that is the product working
    correctly. An infra error rendered with a 200 status IS a failure.
  - It does NOT judge answer quality, groundedness, or brand fit - that is
    demo-tester's and qa-reviewer's job at ship time. This is liveness, not QA.

SELFTEST IS MANDATORY (memory: prove-a-scanner-can-fail-before-trusting-clean).
A green sweep from an unproven checker is worthless. `selftest()` runs the exact
assertion logic used on real probes against planted BAD samples (a 530 body, an
empty answer, a known error string riding a 200) and planted GOOD samples (a
real-shaped grounded answer), and refuses to run the real sweep unless every
one of them comes back the way it should. Run standalone with `--selftest-only`.

TIMEOUTS ARE MANDATORY (Clinic postmortem: an await with no timeout never
rejects on a stalled connection - a one-in-thirty stall rate went undiagnosed
for weeks because nothing ever timed out to report it). Every request below
carries an explicit (connect, read) timeout; a timeout is scored as a FAIL,
never silently skipped.

USAGE
    .venv/bin/python scripts/estate_health.py                     # full sweep
    .venv/bin/python scripts/estate_health.py --selftest-only
    .venv/bin/python scripts/estate_health.py --only clinic,experience-co-ops
    .venv/bin/python scripts/estate_health.py --json-out /tmp/health.json
    .venv/bin/python scripts/estate_health.py --skip-fly-discovery    # faster, skips
                                                                       # the uncovered-app diff

Exit code: 0 only if selftest passes AND no probed target FAILed (SKIPped
targets - suspended Fly apps, not-yet-deployed builds, liveness-only apps that
merely load - never affect the exit code, since they carry nothing to fail on
the real-answer-path assertion). Non-zero otherwise.

ADDING A NEW DEMO: add one entry to TARGETS below. Read the app's own server
code (app.py / server/index.mjs / route.ts) to find the real answer-path route
and its request/response shape - do not guess. This script's own discovery
pass (`discover_uncovered_fly_apps`) prints any live, non-suspended Fly app
under the personal account that isn't claimed by any TARGETS entry, precisely
so a new demo cannot silently escape coverage - check that list on every run.
"""
import argparse
import base64
import datetime
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TIMEOUT = (10, 45)          # (connect, read) seconds - a stalled read WILL raise
LATENCY_FAIL_THRESHOLD_S = 45.0     # a successful call slower than this is still a FAIL

# 29 Sep 2026 JWT-TTL sweep: NO single common TTL exists across the estate - decoded
# `exp` claims cluster into at least three bands (roughly: ~3yr-from-mint tokens minted
# mid-2026, ~1yr-from-mint tokens on recently-rebuilt apps, and two anomalously
# short-lived tokens - pay-co-pay and intel-co-intel - that had already expired).
# Since there's no fixed TTL to hang a single rule on, this checks each app's OWN
# decoded expiry and warns/fails ahead of the actual expiry rather than only after -
# the two dead tokens were found by their live 401, which is one incident too late.
TOKEN_ENV_KEYS = ("NUCLIA_SERVICEACCOUNT", "KB_TOKEN", "ARAG_SERVICEACCOUNT")
TOKEN_EXPIRY_WARNING_DAYS = 14

# ---------------------------------------------------------------------------
# 1. TARGET LIST - one editable dict. `kind` selects the probe shape; see
#    probe_target() for what each kind does. Every entry was built by reading
#    the app's own source (not guessed) - see the git history of this file /
#    the estate-health build report for the exact line numbers checked.
# ---------------------------------------------------------------------------
TARGETS = [
    # --- arag-demo-factory scaffold apps: Express server/index.mjs, uniformly
    #     POST /api/ask {query}, streamed NDJSON with {"item":{"type":"answer",
    #     "text":...}} chunks (portal/src/lib/arag.ts is the shared client). ---
    dict(slug="compliance-co-compliance-desk", fly_app="compliance-co-compliance-desk", kind="ndjson_ask",
         path="/api/ask", field="query",
         question="What is Compliance-co's process for a Best Interests Duty check on a client recommendation?"),
    dict(slug="nma-co-nma", fly_app="nma-co-nma", kind="json_ask",
         path="/api/ask", field="query", answer_path=("answer",),
         question="What are the current registration renewal requirements for a nurse?",
         note="Was declared ndjson_ask and FAILED two consecutive sweeps with 'no answer-type "
              "chunk found (empty answer)' - which read as a platform fault and was reported as "
              "one. It was a CHECKER defect: the live deployment returns flat JSON "
              "{\"answer\":...}, not a stream. Three direct probes on 29 Sep 2026 all returned "
              "real grounded answers listing the BNS series with versions and effective dates. "
              "Same live-vs-local divergence as araks above, and the same scaffold lineage - "
              "check the response SHAPE against the live deployment when adding any target, "
              "because a wrong shape produces a confident false failure, not a silent one."),
    dict(slug="home-co-home", fly_app="home-co-home", kind="ndjson_ask",
         path="/api/ask", field="query",
         question="A member has a burst pipe at 11pm - what's covered under their plan?"),
    dict(slug="mediaportal-video", fly_app="mediaportal-video", kind="ndjson_ask",
         path="/api/ask", field="query",
         question="Find the moment a speaker talks about reducing churn."),
    dict(slug="retailer-tackle", fly_app="retailer-tackle", kind="ndjson_ask",
         path="/api/ask", field="query",
         question="What lure would you recommend for murky water and bream?"),
    dict(slug="fanclub-companion", fly_app="fanclub-companion", kind="ndjson_ask",
         path="/api/ask", field="query",
         question="Who is the captain of the starship in this universe?"),
    dict(slug="home-two-home", fly_app="home-two-home", kind="ndjson_ask",
         path="/api/ask", field="query",
         question="What's the current lead time on a made-to-order sofa?"),
    dict(slug="auto-co-auto", fly_app="auto-co-auto", kind="ndjson_ask",
         path="/api/ask", field="query",
         question="What condition issues were noted on the most recent trade-in intake?"),
    dict(slug="pay-co-pay", fly_app="pay-co-pay", kind="ndjson_ask",
         path="/api/ask", field="query",
         question="What is Pay-co's policy on refunding a disputed card transaction?"),
    dict(slug="operator-fleet", fly_app="operator-fleet", kind="ndjson_ask",
         path="/api/ask", field="query",
         question="When is the next scheduled service due on the excavator fleet?"),
    dict(slug="support-co-support", fly_app="support-co-support", kind="ndjson_ask",
         path="/api/ask", field="query",
         question="My Support-co fridge is making a buzzing noise - what should I check first?"),
    dict(slug="overbuilt-companion", fly_app="overbuilt-companion", kind="ndjson_ask",
         path="/api/ask", field="query",
         question="What build did the winning team present in the season finale?"),
    dict(slug="intel-co-intel", fly_app="intel-co-intel", kind="ndjson_ask",
         path="/api/ask", field="query",
         question="What is Intel-co's flagship chocolate product known for?"),
    dict(slug="revolution-dms", fly_app="revolution-ignition-dms", kind="ndjson_ask",
         path="/api/ask", field="query",
         question="What finance and insurance products are available on this deal?"),
    dict(slug="register-co-register", fly_app="register-co-register", kind="ndjson_ask",
         path="/api/ask", field="query",
         question="What is recorded in the town register about the old lighthouse?"),
    dict(slug="publisher-claims", fly_app="publisher-claims", kind="ndjson_ask",
         path="/api/ask", field="query",
         question="Is storm damage to a roof covered under a standard home policy?"),
    dict(slug="digital-co-digital-experience", fly_app="digital-co-digital-experience", kind="ndjson_ask",
         path="/api/ask", field="query",
         question="What smart-home hubs are compatible with your thermostats?"),
    dict(slug="almanac-co-almanac", fly_app="almanac-co-almanac", kind="ndjson_ask",
         path="/api/ask", field="query",
         question="What does the almanac say happened at the harbour in the founding year?"),
    dict(slug="araks", fly_app="thornfield-vet-institute", kind="json_ask",
         path="/api/ask", field="query", answer_path=("answer",),
         question="What's the recommended post-operative care after a routine desexing procedure?",
         note="apps/araks/app/server/index.mjs's local source streams NDJSON like the standard "
              "scaffold, but the LIVE deployment returns flat JSON {\"answer\":...} instead "
              "(confirmed live, 29 Sep 2026) - local source and the live deploy have diverged "
              "for this app; worth a git-vs-live diff next time someone touches it. fly.toml's "
              "app name is thornfield-vet-institute, a later repurposing of this scaffold; "
              "araks-archive (suspended) is the original."),
    dict(slug="bioscience-demo", fly_app="bioscience-demo", kind="ndjson_ask",
         path="/api/ask", field="query",
         question="What is BSI's current research focus in the bioeconomy?",
         expected_suspended=True),

    # --- Next.js app, resource-scoped ask: resolve a real call id from
    #     /api/calls first, then POST /api/calls/{id}/ask {question}. Same
    #     nested {"item":{"type":"answer",...}} NDJSON shape as the scaffold. ---
    dict(slug="call-analysis", fly_app="call-analysis-arag", kind="ndjson_ask",
         path="/api/calls/{id}/ask", field="question",
         resolve_id={"path": "/api/calls", "json_path": ("calls", 0, "id")},
         question="What was the outcome of this call?"),

    # --- Custom Node app, same NDJSON shape but flat {"type":"answer"} chunks
    #     (no nested "item") - server/index.mjs is hand-rolled, not the scaffold. ---
    dict(slug="experience-co-experience", fly_app="experience-co-experience", kind="ndjson_ask",
         path="/api/answer", field="query", extra_body={"mode": "general", "lang": "en"},
         question="What glazing options do you offer for a coastal property?"),

    # --- Bespoke FastAPI apps: plain JSON POST, top-level {"answer": "..."} ---
    dict(slug="global-express", fly_app="cartwright-freight-demo", kind="json_ask",
         path="/api/ask", field="query", answer_path=("answer",),
         question="What are the handling requirements for a shipment marked as damaged?"),
    dict(slug="ignition-dms", fly_app="ignition-dms", kind="json_ask",
         path="/api/assistant", field="question", answer_path=("answer",),
         question="What used SUVs do you have on the lot under $30,000?"),
    dict(slug="bay-co-bay", fly_app="bay-co-bay-arag", kind="json_ask",
         path="/api/assistant", field="query", answer_path=("answer",),
         question="What's a good family activity in Bay-co Bay this weekend?"),
    dict(slug="clinic", fly_app="clinic-knowledge-desk", kind="json_ask",
         path="/api/surgeon-desk", field="question", answer_path=("answer",),
         question="What is CelGro indicated for?",
         note="This is the app that 530'd platform-wide at 08:02 on 29 Sep 2026 minutes "
              "after DAM submission - the incident that produced this script."),
    dict(slug="holidayisle-island", fly_app="holidayisle-island-arag", kind="json_ask",
         path="/api/assistant", field="query", answer_path=("answer",),
         question="What's the best way to see the quokkas on Holidayisle Island?"),
    dict(slug="telerik-kendo-embed", fly_app="telerik-kendo-embed", kind="json_ask",
         path="/api/assistant", field="question", answer_path=("answer",),
         question="How do I reset a device that's stuck offline in FieldPilot?"),
    dict(slug="cinema-group-concierge", fly_app="vrtp-concierge-demo", kind="json_ask",
         path="/api/assistant", field="query", answer_path=("answer",),
         question="What's a good ride for a 6 year old at Movie World?"),
    dict(slug="keystone-relsync", fly_app="keystone-relsync", kind="json_ask",
         path="/api/answer", field="question", answer_path=("with_relationships", "answer"),
         question="Is this unit still under warranty?"),
    dict(slug="llm-economics", fly_app="llm-economics-demo", kind="json_ask",
         path="/api/compare/answer", field="query", answer_path=("results", 0, "answer"),
         question="What does Progress Agentic RAG cost to run per query?",
         timeout=(10, 75), note="fans out to 3 models in parallel - needs a longer read timeout."),

    # --- studycity uses the same shape as bay-co-bay/holidayisle (POST /api/concierge,
    #     {"query":...}, top-level {"answer":...}) but is NOT YET on `flyctl apps list`
    #     as of 29 Sep 2026 - studycity-kb is actively building it. Kept here,
    #     commented out of live probing via `not_deployed`, so it is claimed the
    #     moment it ships instead of surfacing as a mystery "uncovered" app. ---
    dict(slug="studycity", fly_app="studycity-concierge-arag", kind="json_ask",
         path="/api/concierge", field="query", answer_path=("answer",),
         question="What's the difference between a diploma and a bachelor pathway?",
         note="not_deployed was set while this app was still being built, and went STALE the "
              "moment it shipped (29 Sep 2026, deployed 18:18) - the sweep kept reporting "
              "'not yet deployed (build in progress)' about a live app, which is a permanent "
              "blind spot dressed as a SKIP. A hand-set skip flag that nobody clears excludes a "
              "target from coverage forever; prefer a run-time check against the real Fly app "
              "list over a literal. Expect this target to FAIL on connection while its DNS "
              "defect is open: the app is HEALTHY (forcing the shared v4 66.241.125.167 returns "
              "200 in 0.26s) but your-app.fly.dev has NO A RECORD - confirmed "
              "against 8.8.8.8 and 1.1.1.1 with a known-good app as the control, so it is "
              "neither resolver caching nor a local view. A FAIL here is the honest state and "
              "should stay visible until an IPv4 is properly published."),

    # --- Session-cookie auth in front of a raw Nuclia proxy: log in with the
    #     app's own APP_PASSWORD (read from apps/ragverse/.env, never printed),
    #     then POST straight to Nuclia's /ask through the proxy. X-Synchronous
    #     forces a plain JSON response instead of NDJSON (CLAUDE.md gotcha). ---
    dict(slug="ragverse", fly_app="ragverse-enablement", kind="json_ask",
         path="/api/kb/ask", field="query", answer_path=("answer",),
         auth={"type": "session_cookie", "login_path": "/api/session",
               "password_env_file": "apps/ragverse/.env", "password_env_key": "APP_PASSWORD"},
         extra_headers={"x-synchronous": "true"},
         question="What is Progress Agentic RAG?"),

    # --- Bearer-login apps: demo credentials are baked into the seeded app
    #     itself (documented in-code, not secrets) - log in, then call the
    #     real ask route with the token. ---
    dict(slug="experience-co-ops", fly_app="experience-co-ops", kind="ndjson_ask",
         path="/api/ai/ask", field="question",
         auth={"type": "bearer_login", "login_path": "/api/auth/login",
               "username": "k.brennan", "password": "demo", "token_path": ("token",)},
         question="Which high-priority service cases are currently open?",
         note="ai.py's /api/ai/ask streams the same nested NDJSON shape as the scaffold "
              "({\"item\":{\"type\":\"answer\"}}), not a flat JSON body - confirmed live."),
    dict(slug="marty-vdr", fly_app="marty-vdr", kind="sse_ask",
         path="/api/agent-ask", field="query",
         auth={"type": "bearer_login", "login_path": "/api/login",
               "username": "alex.chen", "password": "kestrel", "token_path": ("token",)},
         question="What are the key risks disclosed in the data room?",
         timeout=(10, 60),
         note="Goes through ARAG's own Retrieval Agent (/session/ephemeral) - a platform "
              "path with documented intermittent flakiness (see the "
              "rao_session_ephemeral_platform_bug memory). A FAIL here needs a second look "
              "before concluding the app is broken."),

    # --- Connectivity-only probe (this app has no conversational ask surface -
    #     it's a taxonomy-generation tool; /api/arag/test is its own built-in
    #     connectivity check). ---
    dict(slug="arag-taxonomy-builder", fly_app="arag-taxonomy-builder", kind="connectivity",
         path="/api/arag/test"),

    # --- Liveness-only: no real ARAG answer path exists to probe. ---
    dict(slug="roi-calculator", fly_app="arag-roi-calculator", kind="liveness_only",
         note="Makes zero ARAG API calls by design (app.py line 11) - it's a deterministic "
              "ROI/business-case calculator, not a grounded-answer demo. Liveness-only is "
              "the complete check for this app, not a gap."),
    dict(slug="gov-degree-triage", fly_app="akademdocs-precheck", kind="liveness_only",
         note="Real answer path is a multipart file-upload pipeline (/api/submit), not a "
              "text question - out of scope for a simple POST probe. Recommend the app "
              "grow a lightweight text-only health route if this needs tighter coverage."),
    dict(slug="arag-photo-mosaic", fly_app="arag-photo-mosaic", kind="liveness_only",
         note="Real answer path (/api/retrieve) takes a tile-stats payload from an actual "
              "photo upload, not a text question - liveness-only until a synthetic probe "
              "payload is worked out."),
]

# Infra/config error phrasings seen in the apps' own code (never a legitimate
# honest decline - those read as "I don't have information about that", which
# is the product working correctly and must NOT be flagged). Keep this list to
# strings that only ever mean "something upstream broke", not "no citation".
ERROR_MARKERS = [
    "something went wrong answering",
    "upstream arag call failed",
    "not connected to the live agent",
    "credentials not configured",
    "could not reach the knowledge base",
    "arag credentials not configured",
    "is not configured on the server",
    "internal server error",
    "bad gateway",
    "service unavailable",
    "upstream request failed",
    "upstream error",
    "couldn't reach the live agent",
]


# ---------------------------------------------------------------------------
# 2. CORE ASSERTION LOGIC - shared by selftest() and every real probe. This is
#    the one function that decides PASS/FAIL; selftest proves it can fail
#    before the real sweep ever trusts it.
# ---------------------------------------------------------------------------
## RAO agent stream (marty-vdr's agent-proxy.mjs) surfaces a genuine "I looked
## and found nothing grounded" decline as {"type":"error","stage":"no_grounded_data",
## "friendly":"..."} - that is the agent mechanism working correctly (it ran real
## tool calls, then honestly declined), not an infra failure, so its friendly text
## counts as a legitimate answer. Every OTHER error stage from that same code path
## (config / timeout / transport) IS a genuine infra failure and must fail the probe.
HONEST_DECLINE_STAGES = {"no_grounded_data"}


def extract_ndjson_answer(body_text):
    """Concatenate every answer-type chunk out of a streamed NDJSON/SSE body.
    Handles both the scaffold's nested {"item":{"type":"answer","text":...}}
    and the flat {"type":"answer","text":...} shape some hand-rolled apps use.
    SSE lines are prefixed "data: " - stripped before parsing.

    Returns (answer_text, infra_error_reason). infra_error_reason is set (and
    should force a FAIL regardless of any partial answer text) when a stream
    reports a genuine infra-stage error; a HONEST_DECLINE_STAGES error instead
    contributes its friendly text to the answer, same as a real answer chunk."""
    parts = []
    infra_error_reason = None
    for line in body_text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("data:"):
            line = line[len("data:"):].strip()
        try:
            obj = json.loads(line)
        except (ValueError, json.JSONDecodeError):
            continue
        if not isinstance(obj, dict):
            continue
        item = obj.get("item")
        if isinstance(item, dict) and item.get("type") == "answer" and item.get("text"):
            parts.append(item["text"])
        elif obj.get("type") == "answer" and obj.get("text"):
            parts.append(obj["text"])
        elif obj.get("type") == "error":
            stage = obj.get("stage")
            friendly = obj.get("friendly") or obj.get("message") or ""
            if stage in HONEST_DECLINE_STAGES:
                parts.append(friendly)
            else:
                infra_error_reason = f"stream reported a genuine infra error (stage={stage!r}): {friendly}"
    return "".join(parts), infra_error_reason


def walk_json_path(obj, path):
    """Walk a tuple of keys/list-indices into a parsed JSON value. Returns
    (value, error) - value of whatever type is found at that path, unlike
    extract_json_answer() which additionally requires a string."""
    cur = obj
    for step in path:
        try:
            cur = cur[step]
        except (KeyError, IndexError, TypeError):
            return None, f"path {path!r} not found in response (stopped at {step!r})"
    return cur, None


def extract_json_answer(body_text, answer_path):
    """Walk a dotted path of keys/list-indices into a parsed JSON body,
    requiring the resolved value to be a non-empty string (an answer)."""
    try:
        obj = json.loads(body_text)
    except (ValueError, json.JSONDecodeError):
        return None, "response body is not valid JSON"
    cur, err = walk_json_path(obj, answer_path)
    if err:
        return None, err
    if not isinstance(cur, str):
        return None, f"value at {answer_path!r} is not a string ({type(cur).__name__})"
    return cur, None


def looks_like_infra_error(text):
    low = text.lower()
    return any(marker in low for marker in ERROR_MARKERS)


# ---------------------------------------------------------------------------
# 2b. KB SERVICE-ACCOUNT TOKEN EXPIRY - a forward-looking check, added 29 Sep
#     2026 after pay-co-pay and intel-co-intel were found already dead
#     with "Jwt has expired". Decodes the `exp` claim ONLY - never prints, logs,
#     or returns the token value itself (hard rule 5).
# ---------------------------------------------------------------------------
def decode_jwt_exp(token):
    """Returns (expiry_datetime_utc_or_None, error_or_None). Pure function - never
    touches disk or the network, so selftest can prove it on a synthetic token
    without needing a real credential."""
    if not token or token.count(".") < 2:
        return None, "not a JWT-shaped value (fewer than two '.' separators)"
    payload_b64 = token.split(".")[1]
    padded = payload_b64 + "=" * (-len(payload_b64) % 4)
    try:
        payload = json.loads(base64.urlsafe_b64decode(padded))
    except Exception as e:
        return None, f"could not base64/json-decode the JWT payload segment: {type(e).__name__}"
    exp = payload.get("exp")
    if exp is None:
        return None, "no 'exp' claim in the token payload"
    try:
        return datetime.datetime.fromtimestamp(int(exp), tz=datetime.timezone.utc), None
    except Exception as e:
        return None, f"'exp' claim is not a valid timestamp: {e}"


def make_fake_jwt(exp_epoch_seconds):
    """Builds a syntactically-real (but unsigned, worthless) JWT carrying only an
    `exp` claim, for selftest use - never a real credential."""
    header = base64.urlsafe_b64encode(json.dumps({"alg": "none"}).encode()).decode().rstrip("=")
    payload = base64.urlsafe_b64encode(json.dumps({"exp": exp_epoch_seconds}).encode()).decode().rstrip("=")
    return f"{header}.{payload}.sig"


def evaluate_token_expiry(exp_dt, now, warning_days=TOKEN_EXPIRY_WARNING_DAYS):
    """(verdict, reason). verdict is one of PASS / FAIL / SKIP - SKIP means "no
    token/expiry to judge", which must never flip an otherwise-PASSing probe to FAIL."""
    if exp_dt is None:
        return "SKIP", "no service-account token with a decodable expiry was found for this app"
    days_left = (exp_dt - now).total_seconds() / 86400.0
    if days_left < 0:
        return "FAIL", f"KB service-account token EXPIRED {abs(days_left):.1f} days ago ({exp_dt.date()})"
    if days_left < warning_days:
        return "FAIL", (f"KB service-account token expires in {days_left:.1f} days "
                         f"({exp_dt.date()}) - inside the {warning_days}-day warning window")
    return "PASS", f"token valid for {days_left:.0f} more days (expires {exp_dt.date()})"


def find_service_account_token_expiry(slug):
    """Walks apps/<slug>/ for any .env file and tries each known service-account
    token env-var name, returning (expiry_datetime_or_None, note). Read file-to-file;
    the token value itself never leaves this function."""
    app_dir = ROOT / "apps" / slug
    if not app_dir.is_dir():
        return None, "no local apps/<slug> directory to check"
    for dirpath, dirnames, filenames in os.walk(app_dir):
        dirnames[:] = [d for d in dirnames if d not in ("node_modules", ".git", "dist", "build")]
        if ".env" not in filenames:
            continue
        env_path = Path(dirpath) / ".env"
        env = {}
        try:
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                if "#" in v:
                    v = v.split("#", 1)[0]
                env[k.strip()] = v.strip().strip('"').strip("'")
        except OSError:
            continue
        for key in TOKEN_ENV_KEYS:
            if env.get(key):
                dt, err = decode_jwt_exp(env[key])
                if dt:
                    return dt, f"decoded from {key} in {env_path.relative_to(ROOT)}"
    return None, "no service-account token env var found in any local .env under this app"


def evaluate_probe(kind, status_code, elapsed_s, body_text, answer_path=None,
                    latency_threshold=LATENCY_FAIL_THRESHOLD_S):
    """The one PASS/FAIL decision, used identically by selftest() and by every
    real probe. Returns (verdict, reason, answer_preview)."""
    if status_code is None:
        return "FAIL", "request did not complete (timeout or connection error)", ""
    if not (200 <= status_code < 300):
        return "FAIL", f"HTTP {status_code}", (body_text or "")[:200]

    if kind == "connectivity":
        try:
            obj = json.loads(body_text)
        except (ValueError, json.JSONDecodeError):
            return "FAIL", "connectivity response is not valid JSON", (body_text or "")[:200]
        if not obj.get("ok"):
            return "FAIL", f"connectivity check reported ok={obj.get('ok')!r}", json.dumps(obj)[:200]
        answer = json.dumps(obj)[:200]
    elif kind == "liveness_only":
        answer = "(liveness only - no answer path probed)"
    elif kind in ("ndjson_ask", "sse_ask"):
        answer, infra_error_reason = extract_ndjson_answer(body_text or "")
        if infra_error_reason:
            return "FAIL", infra_error_reason, (body_text or "")[:200]
        if not answer.strip():
            return "FAIL", "no answer-type chunk found in the streamed response (empty answer)", (body_text or "")[:200]
    elif kind == "json_ask":
        answer, err = extract_json_answer(body_text or "", answer_path or ("answer",))
        if err:
            return "FAIL", err, (body_text or "")[:200]
        if not answer.strip():
            return "FAIL", "answer field was present but empty", ""
    else:
        return "FAIL", f"unknown probe kind {kind!r}", ""

    if kind != "liveness_only" and looks_like_infra_error(answer):
        return "FAIL", f"answer text matches a known infra/config error marker: {answer[:150]!r}", answer[:200]

    if elapsed_s is not None and elapsed_s > latency_threshold:
        return "FAIL", f"latency {elapsed_s:.1f}s exceeded the {latency_threshold:.0f}s threshold", answer[:200]

    return "PASS", "ok", answer[:200]


# ---------------------------------------------------------------------------
# 3. SELFTEST - proves evaluate_probe() can actually fail, on both directions,
#    before the real sweep is allowed to trust a PASS from it.
# ---------------------------------------------------------------------------
def selftest():
    cases = []

    # --- planted BAD samples: each must come back FAIL ---
    cases.append(("530 platform outage (the exact Clinic incident shape)",
                   evaluate_probe("json_ask", 530, 1.2, "<html>502 Bad Gateway</html>", ("answer",)),
                   "FAIL"))
    cases.append(("200 with a completely empty answer field",
                   evaluate_probe("json_ask", 200, 1.0, json.dumps({"answer": ""}), ("answer",)),
                   "FAIL"))
    cases.append(("200 whose body isn't JSON at all",
                   evaluate_probe("json_ask", 200, 1.0, "not json", ("answer",)),
                   "FAIL"))
    cases.append(("200 but the infra error string rides inside the answer field",
                   evaluate_probe("json_ask", 200, 1.0,
                                  json.dumps({"answer": "Something went wrong answering that. Try again in a moment."}),
                                  ("answer",)),
                   "FAIL"))
    cases.append(("NDJSON stream with only a retrieval chunk, no answer chunk ever arrives",
                   evaluate_probe("ndjson_ask", 200, 1.0,
                                  json.dumps({"item": {"type": "retrieval", "resources": {}}}) + "\n"),
                   "FAIL"))
    cases.append(("nested answer_path missing a level (with_relationships.answer)",
                   evaluate_probe("json_ask", 200, 1.0, json.dumps({"with_relationships": {"error": "no data"}}),
                                  ("with_relationships", "answer")),
                   "FAIL"))
    cases.append(("request never completed (connect/read timeout -> status_code=None)",
                   evaluate_probe("json_ask", None, None, None, ("answer",)),
                   "FAIL"))
    cases.append(("a real, well-formed answer that simply arrived too slowly",
                   evaluate_probe("json_ask", 200, 90.0, json.dumps({"answer": "Yes, coverage applies here."}),
                                  ("answer",)),
                   "FAIL"))
    cases.append(("connectivity probe reporting ok=false",
                   evaluate_probe("connectivity", 200, 1.0, json.dumps({"ok": False, "error": "no creds"})),
                   "FAIL"))

    # --- planted GOOD samples: each must come back PASS ---
    cases.append(("a real grounded json_ask answer",
                   evaluate_probe("json_ask", 200, 2.1,
                                  json.dumps({"answer": "CelGro is indicated for guided bone regeneration."}),
                                  ("answer",)),
                   "PASS"))
    cases.append(("an HONEST DECLINE is not an infra error and must PASS",
                   evaluate_probe("json_ask", 200, 1.5,
                                  json.dumps({"answer": "I don't have information about that in the published content."}),
                                  ("answer",)),
                   "PASS"))
    cases.append(("a real NDJSON stream with a genuine answer chunk",
                   evaluate_probe("ndjson_ask", 200, 3.0,
                                  json.dumps({"item": {"type": "retrieval", "resources": {}}}) + "\n"
                                  + json.dumps({"item": {"type": "answer", "text": "Here is the grounded answer."}}) + "\n"),
                   "PASS"))
    cases.append(("a real SSE stream (marty-vdr shape) with a genuine answer event",
                   evaluate_probe("sse_ask", 200, 4.0,
                                  "data: " + json.dumps({"type": "heartbeat"}) + "\n\n"
                                  + "data: " + json.dumps({"type": "answer", "text": "Three risks are disclosed: ..."}) + "\n\n"),
                   "PASS"))
    cases.append(("an SSE agent stream that ran real tool calls then HONESTLY DECLINED "
                   "(stage=no_grounded_data) must PASS - the mechanism worked",
                   evaluate_probe("sse_ask", 200, 6.0,
                                  "data: " + json.dumps({"type": "tool_call", "tool": "search"}) + "\n\n"
                                  + "data: " + json.dumps({"type": "error", "stage": "no_grounded_data",
                                                            "friendly": "I looked, but nothing answers this."}) + "\n\n"),
                   "PASS"))
    cases.append(("an SSE agent stream that hit a genuine infra stage (timeout) must FAIL "
                   "even though it never reached an answer chunk",
                   evaluate_probe("sse_ask", 200, 6.0,
                                  "data: " + json.dumps({"type": "tool_call", "tool": "search"}) + "\n\n"
                                  + "data: " + json.dumps({"type": "error", "stage": "timeout",
                                                            "friendly": "This is taking longer than expected."}) + "\n\n"),
                   "FAIL"))
    cases.append(("a nested answer_path that resolves correctly (keystone shape)",
                   evaluate_probe("json_ask", 200, 1.0,
                                  json.dumps({"with_relationships": {"answer": "Yes, warranty is active until 2027."}}),
                                  ("with_relationships", "answer")),
                   "PASS"))
    cases.append(("a list-indexed answer_path (llm-economics shape)",
                   evaluate_probe("json_ask", 200, 1.0,
                                  json.dumps({"results": [{"model": "a", "answer": "Roughly $0.02 per query."}]}),
                                  ("results", 0, "answer")),
                   "PASS"))
    cases.append(("a connectivity probe reporting ok=true",
                   evaluate_probe("connectivity", 200, 0.3, json.dumps({"ok": True, "kbId": "abc"})),
                   "PASS"))
    cases.append(("liveness_only always passes on a clean 200",
                   evaluate_probe("liveness_only", 200, 0.5, "<html>ok</html>"),
                   "PASS"))

    # --- token-expiry planted cases (29 Sep 2026 JWT-TTL follow-up) ---
    now = datetime.datetime.now(datetime.timezone.utc)
    token_cases = []
    already_expired_token = make_fake_jwt(int((now - datetime.timedelta(days=4)).timestamp()))
    token_cases.append(("an already-expired token (the exact pay-co-pay/intel-co-intel shape) must FAIL",
                         evaluate_token_expiry(decode_jwt_exp(already_expired_token)[0], now),
                         "FAIL"))
    soon_token = make_fake_jwt(int((now + datetime.timedelta(days=3)).timestamp()))
    token_cases.append(("a token expiring in 3 days (inside the warning window) must FAIL ahead of time",
                         evaluate_token_expiry(decode_jwt_exp(soon_token)[0], now),
                         "FAIL"))
    healthy_token = make_fake_jwt(int((now + datetime.timedelta(days=300)).timestamp()))
    token_cases.append(("a token with 300 days left must PASS",
                         evaluate_token_expiry(decode_jwt_exp(healthy_token)[0], now),
                         "PASS"))
    token_cases.append(("no token found at all (e.g. roi-calculator, which makes zero ARAG calls) "
                         "must SKIP, never FAIL - absence of a token is not evidence of an expired one",
                         evaluate_token_expiry(None, now),
                         "SKIP"))
    not_a_jwt_dt, not_a_jwt_err = decode_jwt_exp("not-a-real-token")
    token_cases.append(("a garbage/non-JWT value must decode to None (unparseable), not crash",
                         (("SKIP" if not_a_jwt_dt is None and not_a_jwt_err else "FAIL"), not_a_jwt_err),
                         "SKIP"))

    bad = []
    for label, (verdict, reason, _preview), expected in cases:
        if verdict != expected:
            bad.append(f"{label!r}: expected {expected}, got {verdict} ({reason})")
    for label, (verdict, reason), expected in token_cases:
        if verdict != expected:
            bad.append(f"{label!r}: expected {expected}, got {verdict} ({reason})")

    if bad:
        print(f"SELFTEST: FAIL - {len(bad)} of {len(cases) + len(token_cases)} planted cases did not behave "
              f"as expected. Refusing to run the real sweep.")
        for b in bad:
            print(f"  - {b}")
        return False

    print(f"SELFTEST: PASS - all {len(cases) + len(token_cases)} planted cases "
          f"({sum(1 for *_, e in cases if e == 'FAIL')} bad probe, "
          f"{sum(1 for *_, e in cases if e == 'PASS')} good probe, "
          f"{len(token_cases)} token-expiry) evaluated correctly.")
    return True


# ---------------------------------------------------------------------------
# 4. REAL PROBES
# ---------------------------------------------------------------------------
def read_env_value(env_file, key):
    """Read one KEY=value line from a local .env file, file-to-file, never
    printed (hard rule 5). Returns None if the file or key is absent."""
    p = ROOT / env_file
    if not p.exists():
        return None
    for line in p.read_text().splitlines():
        line = line.strip()
        if line.startswith(f"{key}="):
            val = line[len(key) + 1:].strip()
            if "#" in val:
                val = val.split("#", 1)[0].strip()
            return val.strip('"').strip("'")
    return None


def do_auth(session, base_url, auth, timeout):
    """Returns (ok, extra_headers, error_reason)."""
    if not auth:
        return True, {}, None
    if auth["type"] == "session_cookie":
        password = read_env_value(auth["password_env_file"], auth["password_env_key"])
        if not password:
            return False, {}, (f"could not read {auth['password_env_key']} from "
                                f"{auth['password_env_file']} to log in")
        try:
            r = session.post(base_url + auth["login_path"], json={"password": password}, timeout=timeout)
        except requests.RequestException as e:
            return False, {}, f"login request failed: {e}"
        if r.status_code >= 300:
            return False, {}, f"login returned HTTP {r.status_code}"
        return True, {}, None
    if auth["type"] == "bearer_login":
        try:
            r = session.post(base_url + auth["login_path"],
                              json={"username": auth["username"], "password": auth["password"]},
                              timeout=timeout)
        except requests.RequestException as e:
            return False, {}, f"login request failed: {e}"
        if r.status_code >= 300:
            return False, {}, f"login returned HTTP {r.status_code}"
        token, err = extract_json_answer(r.text, auth["token_path"])
        if err or not token:
            return False, {}, f"could not extract token from login response: {err}"
        return True, {"Authorization": f"Bearer {token}"}, None
    return False, {}, f"unknown auth type {auth['type']!r}"


def probe_target(target):
    slug = target["slug"]
    kind = target["kind"]
    timeout = target.get("timeout", DEFAULT_TIMEOUT)

    if target.get("not_deployed"):
        return dict(slug=slug, fly_app=target.get("fly_app"), status_code=None, latency_s=None,
                    verdict="SKIP", reason="not yet deployed to Fly (build in progress)", answer_preview="",
                    note=target.get("note", ""))

    fly_app = target["fly_app"]
    base_url = f"https://{fly_app}.fly.dev"
    session = requests.Session()

    ok, extra_headers, auth_err = do_auth(session, base_url, target.get("auth"), timeout)
    if not ok:
        return dict(slug=slug, fly_app=fly_app, status_code=None, latency_s=None,
                    verdict="FAIL", reason=f"auth failed: {auth_err}", answer_preview="",
                    note=target.get("note", ""))

    headers = dict(target.get("extra_headers", {}))
    headers.update(extra_headers)

    # Some apps scope the ask route to a record id that has to be resolved
    # live first (e.g. call-analysis's /api/calls/{id}/ask) - do that GET,
    # pull the id out with walk_json_path, and substitute it into `path`.
    path = target.get("path", "/")
    if target.get("resolve_id"):
        rid_spec = target["resolve_id"]
        try:
            rr = session.get(base_url + rid_spec["path"], timeout=timeout, headers=headers)
        except requests.RequestException as e:
            return dict(slug=slug, fly_app=fly_app, status_code=None, latency_s=None,
                        verdict="FAIL", reason=f"could not resolve a record id ({rid_spec['path']}): {e}",
                        answer_preview="", note=target.get("note", ""))
        if rr.status_code >= 300:
            return dict(slug=slug, fly_app=fly_app, status_code=rr.status_code, latency_s=None,
                        verdict="FAIL", reason=f"id-resolution call to {rid_spec['path']} returned "
                                                f"HTTP {rr.status_code}", answer_preview="",
                        note=target.get("note", ""))
        try:
            rid_obj = rr.json()
        except ValueError:
            return dict(slug=slug, fly_app=fly_app, status_code=rr.status_code, latency_s=None,
                        verdict="FAIL", reason=f"id-resolution call to {rid_spec['path']} did not return JSON",
                        answer_preview="", note=target.get("note", ""))
        rid, err = walk_json_path(rid_obj, rid_spec["json_path"])
        if err or not rid:
            return dict(slug=slug, fly_app=fly_app, status_code=rr.status_code, latency_s=None,
                        verdict="FAIL", reason=f"could not extract a record id via {rid_spec['json_path']}: "
                                                f"{err or 'empty value'} - corpus may be empty",
                        answer_preview="", note=target.get("note", ""))
        path = path.format(id=rid)

    t0 = time.monotonic()
    status_code = None
    body_text = ""
    try:
        if kind == "liveness_only":
            r = session.get(base_url + "/", timeout=timeout, headers=headers)
        elif kind == "connectivity":
            r = session.post(base_url + path, timeout=timeout, headers=headers)
        else:
            body = {target["field"]: target["question"]}
            body.update(target.get("extra_body", {}))
            r = session.post(base_url + path, json=body, timeout=timeout, headers=headers)
        status_code = r.status_code
        body_text = r.text
    except requests.exceptions.Timeout:
        elapsed = time.monotonic() - t0
        return dict(slug=slug, fly_app=fly_app, status_code=None, latency_s=round(elapsed, 1),
                    verdict="FAIL", reason=f"request timed out after {elapsed:.1f}s (connect/read timeout "
                                            f"{timeout} exceeded - stalled connection, not a fast error)",
                    answer_preview="", note=target.get("note", ""))
    except requests.RequestException as e:
        elapsed = time.monotonic() - t0
        return dict(slug=slug, fly_app=fly_app, status_code=None, latency_s=round(elapsed, 1),
                    verdict="FAIL", reason=f"connection error: {e}", answer_preview="",
                    note=target.get("note", ""))
    elapsed = time.monotonic() - t0

    verdict, reason, preview = evaluate_probe(kind, status_code, elapsed, body_text,
                                               answer_path=target.get("answer_path"))

    # Forward-looking token-expiry check, independent of whether the live call
    # just happened to succeed - a token can still answer today and die tomorrow.
    # Never let a SKIP (no token found - e.g. roi-calculator makes no ARAG calls
    # at all) override or downgrade an otherwise-good verdict.
    exp_dt, exp_note = find_service_account_token_expiry(slug)
    exp_verdict, exp_reason = evaluate_token_expiry(exp_dt, datetime.datetime.now(datetime.timezone.utc))
    token_expiry = dict(checked=exp_verdict != "SKIP", verdict=exp_verdict, reason=exp_reason, source=exp_note)
    if exp_verdict == "FAIL" and verdict != "FAIL":
        verdict, reason = "FAIL", f"token-expiry check failed even though the live call succeeded: {exp_reason}"

    return dict(slug=slug, fly_app=fly_app, status_code=status_code, latency_s=round(elapsed, 1),
                verdict=verdict, reason=reason, answer_preview=preview, note=target.get("note", ""),
                token_expiry=token_expiry)


# ---------------------------------------------------------------------------
# 5. FLY DISCOVERY - prove new demos can't silently escape coverage.
# ---------------------------------------------------------------------------
def discover_uncovered_fly_apps(targets):
    """Lists every deployed (non-suspended) Fly app on the personal account and
    flags anything not claimed by a TARGETS entry, so a new demo shipped
    without updating this file shows up here instead of going unmonitored."""
    try:
        out = subprocess.run(["flyctl", "apps", "list", "--json"], capture_output=True,
                              text=True, timeout=30, check=True)
        apps = json.loads(out.stdout)
    except Exception as e:
        return None, f"could not run `flyctl apps list --json`: {e}"

    known = {t["fly_app"] for t in targets if t.get("fly_app")}
    # Fly apps that are known-not-ours (platform/reference/inherited, not built
    # via this factory's apps/<slug> Workflow-5 path) - excluded from the
    # "uncovered" flag so it doesn't cry wolf on the same handful every run.
    # This list is a courtesy, not a source of truth - anything added here
    # should have a one-line reason.
    known_excluded = {
        "agentic-dam",              # Field Kit platform itself - internal ops, never a GTM demo
        "arag-research-portal",     # reference-repos demo, owner arag-sales-engineering, not built here
        "capstone-atlas-operations", "capstone-aurora-concierge", "capstone-legal",  # reference demos
        "plant-demo-plant",            # original reference KB/demo, pre-dates apps/
        "sitefinity-mcp-eftm2",     # reference demo (currently under active work by other agents)
        "maintenanceos",            # reference-repos/maintenanceOS demo
        "umbraco-arag-perso", "umbraco-site", "wordpress-arag-perso", "wordpress-arag-perso-db",  # reference CMS demos
    }

    uncovered = []
    for app in apps:
        name = app.get("Name") or app.get("name")
        status = (app.get("Status") or app.get("status") or "").lower()
        if not name or status == "suspended":
            continue
        if name in known or name in known_excluded:
            continue
        uncovered.append(name)
    return sorted(uncovered), None


# ---------------------------------------------------------------------------
# 6. MAIN
# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest-only", action="store_true", help="run selftest() and exit")
    ap.add_argument("--only", help="comma-separated list of slugs to probe (default: all)")
    # TRAP, committed by the lead on 5 Oct 2026 while running the standing sweep.
    # This default IS the baseline the next sweep compares against. Passing
    # --json-out to send the summary somewhere convenient (a /tmp file you intend
    # to read) silently diverts the baseline write too, so the baseline never
    # rolls forward and every later sweep keeps comparing against a stale run.
    # Nothing warns you: the run looks completely normal and the comparison still
    # "works", it just compares against the wrong day. For the standing health
    # sweep, run with NO --json-out and read scripts/estate_health_last_run.json
    # afterwards. Use --json-out only for a genuinely throwaway probe where you do
    # not want the baseline touched, which is the one case it is right for.
    ap.add_argument("--json-out", default=str(ROOT / "scripts" / "estate_health_last_run.json"),
                     help="path to write the machine-readable summary; CAUTION, this is also "
                          "the baseline the next run compares against - see the note above")
    ap.add_argument("--skip-fly-discovery", action="store_true",
                     help="skip the flyctl-based uncovered-app diff (faster, less complete)")
    args = ap.parse_args()

    if not selftest():
        sys.exit(2)
    if args.selftest_only:
        sys.exit(0)

    targets = TARGETS
    if args.only:
        wanted = set(s.strip() for s in args.only.split(","))
        targets = [t for t in targets if t["slug"] in wanted]

    results = []
    for t in targets:
        if t.get("expected_suspended"):
            # Pre-flagged as not in the live rotation (e.g. a suspended Fly app) -
            # still worth a real probe so a re-activation is caught, but a
            # failure here is reported as SKIP context, not counted against exit code.
            r = probe_target(t)
            if r["verdict"] == "FAIL":
                r["verdict"] = "SKIP"
                r["reason"] = f"expected-suspended app did not respond ({r['reason']}) - not counted as a failure"
            results.append(r)
        else:
            results.append(probe_target(t))

    # --- print table ---
    col = "{:<28} {:<32} {:<6} {:>8}  {:<16} {}"
    print(col.format("SLUG", "ENDPOINT", "HTTP", "LATENCY", "TOKEN EXPIRY", "VERDICT / REASON"))
    print("-" * 160)
    for r in results:
        endpoint = next((f"{t['path']}" for t in targets if t["slug"] == r["slug"] and "path" in t), "/")
        http = str(r["status_code"]) if r["status_code"] else "-"
        lat = f"{r['latency_s']}s" if r["latency_s"] is not None else "-"
        tok = r.get("token_expiry") or {}
        tok_str = tok.get("verdict", "-") if tok.get("checked") else "-"
        print(col.format(r["slug"], endpoint, http, lat, tok_str, f"{r['verdict']} - {r['reason']}"))

    fails = [r for r in results if r["verdict"] == "FAIL"]
    skips = [r for r in results if r["verdict"] == "SKIP"]
    passes = [r for r in results if r["verdict"] == "PASS"]
    print("-" * 140)
    print(f"{len(passes)} PASS, {len(fails)} FAIL, {len(skips)} SKIP (of {len(results)} targets probed)")

    uncovered, disc_err = (None, "skipped (--skip-fly-discovery)") if args.skip_fly_discovery \
        else discover_uncovered_fly_apps(TARGETS)
    if disc_err:
        print(f"\nFly discovery: {disc_err}")
    elif uncovered:
        print(f"\nFly discovery: {len(uncovered)} deployed app(s) on the account are NOT claimed by any "
              f"TARGETS entry - add them or confirm they're out of scope:")
        for name in uncovered:
            print(f"  - {name}")
    else:
        print("\nFly discovery: every deployed, non-suspended Fly app is accounted for in TARGETS.")

    # --- coverage as a fraction, against the FULL TARGETS list, not just whatever
    #     --only happened to select - a clean run must never read as a clean estate
    #     when a third of it was never actually asked a question (GM follow-up,
    #     29 Sep 2026: "state coverage as a fraction, never as a verdict"). ---
    real_answer = [t for t in TARGETS if t["kind"] in ("ndjson_ask", "json_ask", "sse_ask") and not t.get("not_deployed")]
    connectivity_only = [t for t in TARGETS if t["kind"] == "connectivity"]
    liveness_only = [t for t in TARGETS if t["kind"] == "liveness_only"]
    not_yet_deployed = [t for t in TARGETS if t.get("not_deployed")]
    n_uncovered = len(uncovered) if uncovered is not None else None
    n_known = len(TARGETS)
    denom = n_known + (n_uncovered or 0)
    print(f"\nCOVERAGE (of the full estate this script currently knows about, not just this run's --only "
          f"selection):")
    print(f"  {len(real_answer)}/{denom} probed on a REAL ARAG answer path (the only rows that prove the "
          f"platform actually answers)")
    print(f"  {len(connectivity_only)}/{denom} connectivity-only (no conversational ask surface exists)")
    print(f"  {len(liveness_only)}/{denom} liveness-only (homepage 200 only - no ARAG call probed; "
          f"see each entry's `note` for why)")
    print(f"  {len(not_yet_deployed)}/{denom} not yet deployed (SKIP, tracked for the moment they ship)")
    print(f"  {n_uncovered if n_uncovered is not None else '?'}/{denom} deployed Fly apps with NO TARGETS "
          f"entry at all (0 questions asked, 0 evidence of health either way)")
    if args.only:
        print(f"  NOTE: this run's --only={args.only!r} probed a subset ({len(targets)} targets) of the "
              f"{len(real_answer) + len(connectivity_only) + len(liveness_only)} normally probed - the "
              f"PASS/FAIL counts above are scoped to that subset, the coverage fractions are not.")

    summary = dict(
        run_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        selftest="PASS",
        results=results,
        pass_count=len(passes), fail_count=len(fails), skip_count=len(skips),
        uncovered_fly_apps=uncovered,
        coverage=dict(
            denominator_note="known TARGETS entries + uncovered live Fly apps found by discovery",
            denominator=denom,
            real_answer_path=len(real_answer),
            connectivity_only=len(connectivity_only),
            liveness_only=len(liveness_only),
            not_yet_deployed=len(not_yet_deployed),
            uncovered_fly_apps=n_uncovered,
        ),
    )
    # ROTATE BEFORE WRITING. The standing sweep compares this run's FAIL set against the
    # previous one, and until 1 Oct 2026 this line overwrote the only copy of that previous
    # summary - so the comparison the job exists to make had nothing to compare against, and
    # a "same as last sweep" verdict rested on whoever ran it remembering. That is a
    # "stop if it changed" instruction with no recorded baseline. Keep the rotation.
    # SHAPE OF THIS FILE, for whoever writes the comparison. The rows live under `results`,
    # each keyed `slug` with its outcome in `verdict` - NOT `targets`/`target`/`status`. Read
    # the wrong key with a `.get(..., [])` and you get an EMPTY fail set, which is
    # indistinguishable from a clean estate: exactly the zero-of-zero failure, committed by
    # the lead on 1 Oct 2026 while running this very job. Any comparison over this file must
    # assert the row list is non-empty before trusting a "no failures" reading.
    out = Path(args.json_out)
    if out.exists():
        prev = out.with_name(out.name.replace("_last_run", "_prev_run"))
        if prev == out:                      # non-standard --json-out name
            prev = out.with_suffix(out.suffix + ".prev")
        prev.write_text(out.read_text())
        print(f"Previous summary rotated to {prev.name}")
    out.write_text(json.dumps(summary, indent=2))
    print(f"\nJSON summary written to {args.json_out}")

    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
