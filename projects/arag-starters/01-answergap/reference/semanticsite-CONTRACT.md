# SemanticSite: the frozen contract

**Frozen by the lead, 8 Oct 2026. Do not edit without asking the lead.** Three agents build
against this in parallel. If it is wrong, say so and I will change it centrally rather than
you working around it locally; a local workaround here becomes an integration failure later.

Work item: `7c47dfda` in the PMK-1 queue. The PRD is in that brief's objective and is the
spec. This file is the seam, not the spec.

---

## 1. Two deployments, and why that matters

| | What | Host |
|---|---|---|
| **The product** | SemanticSite itself | `your-app.fly.dev` |
| **The fixture** | A 20-page website it crawls | its own Fly app, its own domain |

The fixture is a **separate deployment on its own hostname**, fetched over real HTTP with a
real `sitemap.xml`. It is never imported, never read off disk by the product, and never
special-cased. If SemanticSite can only crawl a site we happen to host in the same process,
it does not crawl websites, and the demo's central claim is false.

## 2. Writer lock, so three agents do not collide

| Directory | Owner | Nobody else writes here |
|---|---|---|
| `fixture/` | ss-fixture | yes |
| `server/` | ss-core | yes |
| `web/` | ss-web | yes |
| `CONTRACT.md`, `.env`, root config | the lead | yes |

Shared read-only facts live in `server/schema.py` (the API response shapes). Import them;
never retype a field name.

## 3. The fixture is also the evaluation set

The PRD sets precision targets: entity extraction at or above 90 per cent, relationships at
or above 85 per cent, on "a reviewed evaluation set". **The fixture IS that set**, and it
only works if we know the right answer in advance.

`fixture/ground-truth.json` is therefore a required deliverable, not documentation. It lists
every entity and every relationship the site genuinely contains, each keyed to the page or
pages that support it. It is authored BY HAND alongside the pages, never generated from the
product's own output, because a ground truth derived from the thing it measures measures
nothing.

Precision is then a number we compute, not a claim we make.

## 4. What the fixture must contain

Twenty pages is small enough to hand-author well and large enough to carry a real graph. The
site must exercise every path the product claims, including the unhappy ones.

**Structured-data coverage, deliberately uneven** - this is the product's whole reason to
exist, so a site with clean markup everywhere would prove nothing:
- some pages with complete, valid JSON-LD
- some with **partial or subtly invalid** markup: a wrong `@type`, a missing required
  property, a malformed date, a `@id` that points nowhere
- the rest with none at all

**At least two genuine conflicts**, each recorded in the ground truth as a conflict: the same
fact stated differently in two places. Opening hours that disagree between a location page
and a listing; a price that differs between a product page and an index.

**At least two entity-resolution traps**: the same person or product named two ways, so
"ambiguous entity matches require review" has something real to catch.

**Relationships that exist only in prose**, not in any markup, so extraction has to earn its
result rather than reading it off a `<script>` tag.

**Honest crawl edges**: a `robots.txt`, at least one URL excluded by it, and a page the
sitemap lists that returns 404, so crawl-coverage reporting has a real gap to report.

## 5. The product's API, which `web/` codes against

All responses JSON. Route names are ours, never the platform's: the demo leak scan greps raw
page source for the platform's own endpoint names, so a head fetching `/api/ask` fails the
gate on every route that loads it.

- `POST /api/sites` - start a crawl from a URL or sitemap URL. Returns a site id.
- `GET  /api/sites/{id}` - crawl status, page counts, coverage.
- `GET  /api/sites/{id}/pages` - ingested URLs with extraction results, existing schema,
  proposed schema.
- `GET  /api/sites/{id}/entities` - entities and relationships for the explorer.
- `GET  /api/pages/{id}/schema` - source content beside proposed JSON-LD.
- `POST /api/pages/{id}/schema/approve` - human approval. Export is gated on it.
- `GET  /api/sites/{id}/export` - approved JSON-LD only.
- `POST /api/question` - grounded question answering with citations.

**Corrected by the lead, 8 Oct 2026, and the mistake is instructive.** This section
originally named two routes `/api/ask` and `/api/sites/{id}/graph`. Both would have tripped
the demo leak scan, which fires on a platform mechanism name not followed by a word
character or a hyphen - so `/api/ask` matches, and so does anything ending `/graph`. I wrote
the rule two paragraphs above and then broke it in my own example. ss-web caught it.

The fix is to RENAME, never to construct the string indirectly so the scanner cannot see it.
Hiding a string from a gate defeats the gate while leaving the thing it guards against
exactly where it was; the point was never the scanner's opinion, it was not shipping our
platform's endpoint names on a customer-facing surface.

Every record the product generates carries `provenance`: the source URL, the resource id it
came from, and whether it was **extracted** from existing markup or **suggested** by the
model. Those two must never be presented as the same kind of thing, in the API or on screen.

## 6. The platform facts you inherit (do not rediscover these)

These are measured, not assumed. The brief's objective carries the full list; these are the
ones that change what you build.

- **Text ingests to `POST /kb/{id}/resources`** with `title`, `texts.body.body` and
  `origin.url` - NOT `/upload`, which silently corrupts self-supplied text by OCRing it while
  retrieval keeps working. `origin.url` carries the page URL and is the backbone of
  provenance. A resource's title is not searchable body text.
- **Structured JSON generation**: query-time `answer_json_schema` on `/ask` works. The
  ingest-time generator's JSON path 422s regardless of schema. Never send `citations: true`
  in the same call as a schema; it 500s.
- **The provenance trap**: a free-text source field inside a schema IS HALLUCINATED even when
  retrieval is grounded. Fire `/find` first and constrain the source to an **enum of the real
  retrieved ids**. Then bind record to source structurally, because the enum proves the
  source exists, not that the record is about it.
- **Relationships without model cost**: explicit foreign keys as `usermetadata.relations` at
  create time are free. They index but do not read back off the resource; the graph endpoint
  is the only read-back, and anchored queries are source-only unless `undirected: true`.
- **Pin the cheapest capable model on every generative call.** On an extract strategy
  `llm.model` is silently ignored; the key is `llm.generative_model`.
- `X-Synchronous: true` on every non-streaming call. Retrieval never returns empty, so
  threshold client-side.

## 7. Cost is a first-class output, not a footnote

Ingest-time extraction runs one model call **per paragraph**. Twenty pages is cheap and that
is exactly why it is the right fixture: it lets us measure the real per-page cost safely and
extrapolate honestly to the PRD's 500-page target.

**Instrument it.** Count platform calls and tokens per ingestion run and report cost per page
as a real figure in the product's own interface. A product whose running cost is invisible to
its operator is how an account gets budget-blocked, which happened here on 6 Oct and took down
33 of 39 live demos.

Exhaust the free path before the paid one: anything derivable from the HTML itself - existing
JSON-LD, `@id` references, navigation, breadcrumbs - is extracted deterministically at zero
model cost, and only what genuinely needs inference goes to a model.

## 8. Rules every part obeys

- **Nothing is faked, mocked, pre-canned or staged.** Every capability the application appears
  to perform is genuinely performed by a real call at run time. Where we orchestrate something
  the platform does not do natively, the application says so visibly in its reveal. When
  unsure, treat it as faked until proven real.
- **An unsupported relationship is never presented as a fact.** This is the PRD's own section 8
  and this factory's hard rule 3 saying the same thing.
- **Confidence is never a headline.** A qualitative band is default-visible; the number sits
  beneath it as evidence. A high band never implies a record is correct.
- **Approval gates export.** Nothing leaves the product as approved JSON-LD without a human
  having said yes to that specific record.
- **Crawling is outbound behaviour.** Respect `robots.txt`, rate-limit politely, identify the
  crawler honestly in its user agent, and never fetch a site the user did not ask for.
- Australian English, no em dashes, none of `delve`, `leverage`, `unlock`, `seamless`,
  `game-changing`. Spell out "Progress Agentic RAG"; never a bare acronym on a served surface.
- Genuine 390px is a first-class target, not a reasoning exercise.

## 9. Stack

Python only for the product: FastAPI, server-rendered templates and vanilla JavaScript,
matching `apps/bank-co`. Use `/Users/user/Claude/ARAG-PMK-1/.venv/bin/python`. No npm,
no npx.

The fixture is plain static HTML. It is a website, not an application: no framework, no build
step, no JavaScript required to read a page. If a crawler needs to execute JavaScript to see
the content, the fixture is testing the wrong thing, because the PRD explicitly excludes
JavaScript-heavy rendering from the MVP.

## 10. What done looks like for your piece

- It runs against the real platform, with real calls.
- Its failure paths have been OBSERVED by forcing them, not reasoned about.
- Its claims are measured, with the measurement reproducible by someone else.
- It reads well at 390px and at desktop.
- You can name, as a yes or no list, which of section 8's rules you verified and how.

## 11. Verifying a route: the state has to be in the URL

Added 8 Oct 2026, after I got this wrong myself.

Every interface route here is rendered client-side and reads the active site from
`?site=<id>`, falling back to `localStorage`. A headless sweep carries no local storage, so
a gate that visits `/studio` visits an EMPTY Studio, and every check on it passes for the
wrong reason. I ran the automated route gate over six routes, reported a clean pass, and an
adversarial tester then found raw markdown rendering on Schema Studio - a named blocking
rule - because it loaded a site first.

So: drive every route with its state in the query string
(`/studio?site=<id>`, `/studio?site=<id>&page=<pid>`), and before trusting a clean sweep,
run the same sweep against a build that still carries the defect and read a NON-ZERO exit.
A pass whose matching failure was never observed is not evidence.

`?force=timeout|500|offline` (and the `-post` variants) exist for the same reason on the
failure paths: observe the state, do not reason about it.
