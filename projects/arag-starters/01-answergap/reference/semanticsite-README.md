# SemanticSite

Turns a website into structured, AI-ready knowledge: JSON-LD proposals with the evidence beside each claim, built on Progress Agentic RAG. A person approves each record before anything is exported.

## Reproducing from a fresh clone

The product needs nothing from `fixture/` or `web/screenshots/` to run. It crawls the example site over HTTP like any other site.

1. `git clone` this repository, then follow "Run it locally" below. Point a crawl at the deployed example site, `https://your-app.fly.dev/`.
2. Only if you want the example site's source (to change it or redeploy it): `git clone https://github.com/jaysanderson/sitecrawl-coffee-fixture fixture` from the app root. It is a separate repository and is ignored here on purpose.

`web/screenshots/` holds review evidence only and is not part of the build.

## Run it locally

```
cp .env.example .env            # fill KB_URL / KB_TOKEN (the knowledge box coordinates)
SS_ALLOW_OPEN=1 SS_ALLOW_PRIVATE_HOSTS=1 ../../.venv/bin/python -m uvicorn server.app:app --port 8811
```

`SS_ALLOW_OPEN=1` and `SS_ALLOW_PRIVATE_HOSTS=1` are for local development only. Never set either on a public deployment.

## The operator key

Browsing is open, and so is asking a question (limited to 8 an hour per visitor, 150 an hour overall; a visitor with the key skips the per-visitor limit). Starting a crawl, re-crawling, approving a record, settling a conflict or an ambiguous match, and deleting a site all need the header `X-SemanticSite-Key`, whose value is the secret `SS_ACCESS_KEY`. If `SS_ACCESS_KEY` is unset those routes refuse everyone. On Fly: `flyctl secrets set SS_ACCESS_KEY=... -a semanticsite` (run by the operator; the value never goes in git or in page source).

The crawl limits are environment settings, never request parameters: `SS_HOURLY_PAGE_BUDGET` (code default 300 pages an hour, all callers together), `SS_MAX_PAGES_CAP` (code default 500 pages a crawl) and `SS_MAX_CONCURRENT_RUNS` (default 3). The deployed instance sets 200 pages an hour and 60 pages a crawl as Fly secrets.

Why those numbers: the example site is 20 pages and a prospect's site for a demo is about 60 at most. Measured cost is about 2 model calls and about 5,300 model tokens a page (model tokens, not Progress Agentic RAG consumption tokens, which are a different unit), so 60 pages is about 120 calls and 200 pages an hour is about 400 calls an hour in the worst case, which is a bound this account can absorb. Raising either number raises that worst case in proportion, so change it only with the arithmetic above in hand. `server/tests/cost_caps.py` proves the caps hold by hitting them.

## Reset

Removing a site takes seconds. Putting a crawled demo back takes a fresh crawl: measured 80 seconds for the 10-page Ottermere site and 135 seconds for the 20-page Sitecrawl site (9 Oct 2026), so a full reset to a populated demo is about two minutes, not thirty seconds. The crawl is a real run, so entity and relationship counts can differ slightly between draws (conflicts and ambiguities were the same across three Sitecrawl crawls on record; prose relationship counts were not).

Remove one site and the page text it put in the knowledge base:

```
curl -X DELETE -H "X-SemanticSite-Key: $SS_ACCESS_KEY" https://your-app.fly.dev/api/sites/<site id>
```

Remove everything in the knowledge base and the local review store (run where the data volume is mounted):

```
python server/scripts/purge_kb.py            # resources and local store
python server/scripts/purge_kb.py --keep-db  # resources only
```

Reseed the demo with a real crawl (nothing is pre-canned; indexing, extraction and proposals are produced fresh):

```
SS_ACCESS_KEY=... python server/scripts/seed.py --api https://your-app.fly.dev --url https://your-app.fly.dev/ --purge
```

## Demo narrative

1. Start with the example site (the fixture is a separate deployment with its own sitemap and robots.txt). Watch the crawl report what it took and what it left, with the reason.
2. Open the explorer. Relationships read from markup are labelled extracted; those a model read from page text are suggested and carry a verbatim quote.
3. Open a page in the Studio: source on the left, proposed JSON-LD on the right. Settle a conflict or an ambiguous match, then approve.
4. Export: approved records only, with a provenance file that has one row per property.
5. Ask a question. The answer cites pages, and a sentence with no source page is withheld or marked.

## Exports and cross-page references

Each approved record is one page's JSON-LD, and records refer to each other by `@id` (an organisation's offers point at product records that sit on other pages). Validating a single record on its own therefore shows those references as unresolved. They resolve once the pages are published together on the site. The export carries this as a `note`.

## What is registered on the knowledge base, and what deliberately is not

Registered as real objects, visible in the console: the answer configuration `site-question-answering` (model, prompt and top_k live there) and the labelset `markup-status` (complete, partial_or_invalid, none), assigned to each page at ingest from the crawl's own classification of the markup already on it. No model runs for that and no faceted count is used.

Measured cost: 2 model calls and about 5,288 model tokens a page (40 calls, 66,937 model input tokens and 38,816 model output tokens for a 20-page crawl, read from the platform's own responses, 9 Oct 2026; these are model tokens, not Progress Agentic RAG consumption tokens, which are a different unit and were not measured). A 500-page site is therefore about 1,000 calls. That figure is possible because no ingest-time tasks are registered.

Not registered, by design: ingest-time extraction tasks and graph tasks. They run one model call per paragraph across the whole site, which is the cost pattern the cost-safety rule forbids. Extraction here is one measured call per page (two with the recall pass), so the cost per page is a number the product shows. A 500-page site would be about 1,000 calls; measure on the target site before any large crawl.

## Builds and gate verdicts

Deployed build at the time of the 9 Oct 2026 gates: Fly version 27, commit `c3d1fde358d5d4f8f950b5c1c82975841614c3a2`. Later README, test-script and deploy-script commits do not change the running image; a commit that does is stated here with its own verdict. From the build after this one, `GET /api/health` reports the commit it runs.

Gate verdicts, each recorded with the commit it measured and written after it was issued:
- Simulated authority (composite critic), against `c3d1fde`: **APPROVE**. Conditions 3, 4 and 5 cleared.
- Definition of Pass, against `c3d1fde`: **FAIL**, one narrow defect. The Studio labelled breadcrumb rows that the provenance file calls `derived` as SUGGESTED. Blockers 2, 3 and 4 pass.
- Definition of Pass re-check, against `692a54e`: **that defect is CLOSED**. The Studio renders DERIVED on the breadcrumb row, the provenance export agrees on the label and on its definition, and across 34 pages no origin value falls outside the four the client maps. Evidence and the stated limits of each figure: `GATE-RECHECK-2026-10-12.md`. The re-check does not re-walk blockers 2, 3 and 4.

## Deploying

`python server/scripts/deploy.py` refuses a dirty tree or a commit that is not on origin/main, builds with the commit baked in (`GIT_SHA`), deploys, and then reads the commit back from `GET /api/health`, failing if the live service does not report it. The same field lets any gate pin itself to a build from the service itself: `curl https://your-app.fly.dev/api/health` returns `{"ok":..., "configured":..., "commit":"<sha>"}`.

## Tests

Run each with `python -m server.tests.<name>` from the app root. Exit 0 means every check that ran passed; exit 77 means nothing ran. A section that needs something this clone does not have prints `SKIP`, is named at the end, and is not counted as passed.

- **Run anywhere, with no `.env`, no knowledge base and no crawl:** `export_quality`, `access_gate`, `cost_caps`, `reviewer_edits`, `provenance_rows`, `alias_routing`, `ssrf` (needs DNS for one public hostname), and the logic sections of `identity`, `robots_spec` and `answers_offline`.
- **Skipped without a configured knowledge base:** the crawl sections of `identity`, `robots_spec`, `scope` and `collision` (they crawl a local test site through the whole pipeline and ingest it); all of `scope` and `collision` therefore exit 77 in a clean clone.
- **Skipped without a store populated by an earlier crawl of the example site:** the alias and entity-fact checks in `answers_offline`.
- **Always live, call the platform (cost model calls; run for a final pass, not after every edit):** `failure_paths`, `approval_gate`, `isolation`.
