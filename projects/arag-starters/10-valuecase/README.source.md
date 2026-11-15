# ROI & Value Case Tool - Progress Agentic RAG

A day-to-day value-engineering tool, not a demo page. Rebuilt (DAM work item
`0be7b846`) after the GM's rejection of the original client-side calculator:
*"This seems more like a demo page and not something that a value engineer
would use day-to-day... this needs to be better than other products on the
market for this task, such as Shark Finesse."*

The rebuild follows `content/enablement/ve-tool-research.md` (the market
teardown of Shark Finesse, Ecosystems, Cuvama, DecisionLink/ValueCore and
Mediafly, and the eight ranked MUSTs a world-class VE tool needs) and
`content/enablement/roi-value-model.md` v2.0 (the five value levers,
formulas and honesty rules - carried forward unchanged, because the
research confirmed the arithmetic and honesty discipline were never the
problem; the structural gaps were).

## What changed from the original build

| Gap (from the market teardown) | Fixed how |
|---|---|
| No case persistence | FastAPI + SQLite on a Fly volume - every case is a reopenable object at its own URL |
| No provenance | Every input carries who supplied it, their role, the date, and a source type |
| No discovery-to-case flow | A short Discovery step (drawn from the discovery & qualification framework) runs before any number |
| No scenario comparison | Conservative / Expected / Aggressive columns on every input, natively |
| No sensitivity view | A tornado chart ranks inputs by a +/-20% swing in the expected case |
| No real financial modelling | Time-phased monthly NPV, IRR and Payback (`finance.py`), with Shark-Finesse-style credibility coaching (e.g. flags an IRR over 1,000% or a sub-one-month payback as implausible rather than headlining it) |
| No stakeholder-ready export | Branded, editable Word (`.docx`) and PowerPoint (`.pptx`) exports, replacing the old flat print-to-PDF |
| No owner attribution | One accountable buyer-side owner per lever |

What carries forward unchanged: the five value levers and formulas, the
honesty discipline (nothing pre-filled - every number is the buyer's own),
the "Measure in POV" pattern, and USD Locked Facts pricing (Starter
$700/mo, Pro $1,925/mo).

## Access

This tool holds real account names and real buyer numbers - unlike a
synthetic demo KB, it cannot sit on an unauthenticated public URL behind an
unguessable slug alone. It is gated by a single shared team passphrase
(`ROI_PASSPHRASE`, a Fly secret), checked server-side on every `/api/*`
route, remembered in the browser via a signed httpOnly cookie for 30 days.
There are no user accounts - one passphrase, shared by the field team.

## Architecture

- `app.py` - FastAPI app: the passphrase gate, case CRUD, lever-input and
  owner endpoints, the `/compute` endpoint (scenario totals, sensitivity,
  financial view), and the export endpoints. Also serves the static
  frontend.
- `db.py` - SQLite persistence (cases, per-scenario input values, per-input
  provenance/POV metadata, per-lever owners).
- `levers.py` - the five value levers and their formulas, in Python
  (server-side twin of `static/js/levers-data.js` - keep both in lockstep
  with `content/enablement/roi-value-model.md`).
- `finance.py` - NPV/IRR/Payback and sensitivity. This is the one piece of
  new maths that is **not** KB-grounded - it is standard corporate-finance
  convention (monthly discounting), not an ARAG product claim, so it is
  verified against textbook arithmetic in `tests_finance_selftest.py`
  rather than against the KB. Run it before trusting any change here.
- `exports.py` - branded `.docx`/`.pptx` generation (python-docx /
  python-pptx), using the app's own Progress Agentic RAG logo
  (`static/assets/logo-primary-horizontal.png`, rasterised from the app's
  existing SVG lockup - **do not** reach for `brand/logo-black.png` or
  `brand/logo-white.png` in the shared brand folder for this or any future
  build: those two files are mislabelled and actually contain a different,
  unrelated customer's logo).
- `auth.py` - the passphrase check and signed-cookie session (itsdangerous;
  no server-side session table).
- `static/index.html` + `static/js/*.js` (ES modules, no bundler, no npm -
  Python-only stack per hard rule 1) - the SPA: a left-rail nav (a
  horizontally-scrollable stacked header at <=860px, never one crammed
  strip), case list, Discovery, Levers (scenario columns + provenance +
  owner), Sensitivity, Financial, Scenarios, Export.

## Demo / walkthrough narrative

1. **Case list** - "Your cases", persistent, reopenable. Create a new case
   with an account name and your own name.
2. **Discovery** - three short prompts (content/personnel profile, pain and
   use-case shape, budget anchor) plus a champion name/role. Skippable if
   discovery already happened live.
3. **Levers** - select one or two levers. Fill the Conservative / Expected
   / Aggressive columns with the buyer's own numbers. Tick "Measure in
   POV" on an input the model doc says never to assume (Lever 1's minutes
   saved, Lever 2's deflection fraction) - it disables that input across
   all three scenarios and lists it as an agreed POV metric instead. Try
   "I can't estimate this - show me a labelled benchmark" on either
   POV-eligible input - it fills the Expected value with the model doc's
   own illustrative figure, visibly tagged, never silently.
4. **Sensitivity** - the tornado chart ranks which inputs actually swing
   the outcome from a +/-20% change - spend discovery time there, not
   evenly across every field.
5. **Financial** - enter a discount rate (the buyer's own WACC or hurdle
   rate - never assumed) and see real NPV, IRR and Payback. On a typical
   low-cost, no-upfront-cost case, IRR is honestly reported as undefined
   (every cash flow is positive, so there's no outflow for a return to be
   measured against) - exactly Shark Finesse's own documented "don't show
   a misleading metric" discipline, applied automatically.
6. **Scenarios** - Conservative / Expected / Aggressive side by side, so
   "what if adoption is half" already has an answer before the room asks.
7. **Export** - download a branded, editable `.docx` business case or a
   five-slide `.pptx`, both carrying every input's provenance and owner.

## Hand-checked arithmetic

The illustrative worked example from `roi-value-model.md` section 5
(6 staff x 15 lookups/week x 5 minutes saved x $60/hr = $1,950/mo; 400
contacts x 40% deflected x $12 = $1,920/mo; combined $3,870/mo) reproduces
exactly through the full stack - lever input -> `/compute` -> the live
preview on the Levers page - verified live via Playwright, 22 September
2026.

The financial-view maths (`finance.py`) is verified in
`tests_finance_selftest.py` against a classic textbook NPV/IRR problem
(-1000 upfront, +300/year for 5 years -> NPV(10%) = 137.24, IRR = 15.238%),
a constant-cash-flow payback case, the undefined-IRR case (all-positive
cash flows), and an annual/monthly discount-rate round-trip. Run it after
any change to `finance.py`:

```
../../.venv/bin/python tests_finance_selftest.py
```

## Run locally

```
cp .env.example .env   # set ROI_PASSPHRASE and ROI_SECRET_KEY
../../.venv/bin/python -m uvicorn app:app --port 8098
```

## Reset (the 30-second reset)

There is now real server-side state, so the reset is a real endpoint, not
"nothing to reset":

```
curl -X POST https://your-app.fly.dev/api/admin/purge \
  -H 'Content-Type: application/json' \
  -d '{"passphrase":"<the current ROI_PASSPHRASE>"}'
```

Wipes every case. Requires the passphrase again (not just the session
cookie) as a deliberate guard against an idle-browser misclick wiping every
seller's live cases.

## Deploy

Single machine, no HA pair - this app now holds real state on a Fly
volume, so a second machine would see an empty copy of it (Fly volumes are
single-machine, not shared). `--ha=false` is required on every deploy:

```
flyctl volumes create roi_case_data --region syd --size 1 -a arag-roi-calculator   # first deploy only
flyctl secrets set ROI_PASSPHRASE=<value> ROI_SECRET_KEY=<value> -a arag-roi-calculator
flyctl deploy -a arag-roi-calculator --ha=false
flyctl status -a arag-roi-calculator   # confirm exactly one machine
```

Repo: `jaysanderson/arag-roi-calculator`. Live: `your-app.fly.dev`.
