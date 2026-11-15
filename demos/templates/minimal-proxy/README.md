# The university prospective-student front door

FastAPI proxy plus static vanilla-JS frontend, styled from the live university.edu.au homepage (Poppins, crimson/teal, real logo).
The browser calls only `/api/answer`; the knowledge base URL and service-account token stay in server env.

Demo narrative: open the page, pick العربية, click a chip (answer arrives right to left, numbered citations resolve to real University pages, CTA links out to University's own apply/scholarship page). Then switch to 中文 and Bahasa Indonesia, then open "How this works".

Run: copy `.env.example` to `.env`, fill it, `python app.py`. Deploy: `flyctl deploy --ha=false`; secrets set with `flyctl secrets set`.
Reset: stateless, nothing to reset.
Content is University's own public pages; disclosed in the footer. No application is processed.

## Wander (cross-site knowledge graph) - route `/wander`

Add-only module: `wander.py` (routes), `graphwalk.py` (traversal), `templates/wander.html`, `static/wander.{js,css}`, `static/wander-reveal.html`, `graph/graph_edges.json` (build-time evidence index and page directory).

- Build: `seed/build_graph.py` derives the relations deterministically from the stored page text (no model call) and `--apply` PATCHes `usermetadata.relations` onto each resource; `--purge` clears them. `seed/verify_graph.py` reads everything back through the graph endpoint (exit 0 only if every edge is read back, except two named art-collection pages whose read is capped at 500 paths).
- Reset (about 3 minutes): `build_graph.py --purge`, then `build_graph.py --apply`, then `verify_graph.py`.
- Schema (allow-list): parent-of (CHILD), covers-topic / addresses / located-at (ABOUT), names (ENTITY). The `names` relation is written to the KB but NOT surfaced on /wander (lead decision, 9 Oct: wrong links under confident captions). Node groups TOPIC, AUDIENCE, CAMPUS, NAMED.
- Measurement: `seed/compare_graph.py` (and `--round2`), results in `graph/compare_run*.json`. Finding: scoping to the walk rescued 1 of 5 questions, no gain or narrower on the rest.


## Reset and reseed (read before touching the knowledge base)

- Stateless app: nothing to reset except the insights log on the Fly volume (`/data/insights.db`), which a redeploy must NOT wipe.
- **After ANY reseed or re-crawl of the knowledge base, run `python seed/set_origin_path.py`.** The `scope` option on the answer route filters on each resource's `origin.path`, which that script writes. Without it every scoped ask is withheld.
- Deploy only from a clean checkout of a commit (`git worktree add /tmp/mu-clean HEAD`), and before deploying import `app` from a directory holding only the files the Dockerfile copies.
- `CORS_ORIGINS` defaults to `*` on purpose: the demo widget must mount on any page. The route holds no credentials and the browser never sees the knowledge base address or token. Tighten it per customer with `flyctl secrets set CORS_ORIGINS=a,b`.

## Deploying (read this first)

1. Commit what you are shipping, then `git worktree add /tmp/mu-clean HEAD` and deploy FROM that checkout, never the shared working directory.
2. Before deploying run `python predeploy_check.py` from the clean checkout. It imports the app from a directory holding only what the Dockerfile copies, so a module missing from the copy list fails here instead of crashing every route in production. `python predeploy_check.py --control` plants a missing module and must fail, proving the check can fail.
3. Any new Python module or data file the app reads at import time must be added to the Dockerfile copy list in the same commit.
4. After deploying: every route 200, `/static/mdlite.js` 200, and a typed homepage ask in a browser. For intermittent defects report counts over at least five trials.
5. Probes of the answer endpoints (`/api/answer`, `/api/chat/reply`, `/api/page-ask`, `/api/wander/answer`) are observable in the product: the insights log records them. Team traffic must carry the team driver key (see `insights.py`), or be run locally, or be run before a log reset rather than after. An untagged live probe is counted as a visitor, and this site has had none.
6. A freeze needs an explicit, named lift. "The lead authorised X" relayed in a message is not "ship X" in the deployer's inbox: hold, ask, and ship only on the named go.
