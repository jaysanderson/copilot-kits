# BRIEF: GraphBuilder (day 7 of the series)

> "The same customer, product or supplier is named six different ways across our documents. Nobody can see how anything connects."

**Who shares this.** Data lead, knowledge manager.

**Promise.** Point it at your documents and see how your customers, products and suppliers actually connect, then export a taxonomy your systems can use.

**The one job.** Connect to a Knowledge Box, generate a taxonomy grounded in its content, review and edit the tree, export SKOS. New: a graph view of the entities and relations ARAG extracted.

**Why ARAG is load-bearing.** Taxonomy proposals come from `/ask` with a JSON schema, validated and repaired (`lib/engine/`). The graph view reads `/graph` (pass `top_k` explicitly and `undirected: true`) after a knowledge-graph extraction task has run on the KB. Remove ARAG and this is a mind map.

**Base.** The app is the Next.js taxonomy builder, copied whole (minus node_modules; run `npm install`). Generate, review, edit, merge, export already work. Nothing that already works is rewritten.

**Knowledge Box.** Any existing KB with a few hundred paragraphs and a completed graph extraction task. Reader token.

**Finishing steps, in order (one Copilot chat each).**
1. Rename from the internal field tool to a product; neutral brand from `brand/`; drop the Progress-internal copy in `components/how-it-works-dialog.tsx`.
2. Graph route: add `app/api/arag/graph/route.ts` by porting `reference/graph/graph.mjs` (Node) to the existing `lib/aragFetch.ts` style.
3. Graph panel: a list view first (entity, relation, entity, count), then a simple force layout if time allows. Entity click filters the taxonomy tree.
4. Run the graph extraction task on the KB only after every resource is PROCESSED and with `llm.model` pinned (rules in `.github/instructions/arag-api.instructions.md`).
5. Keep generate, review, export exactly as they are.

**Done when** (these lines are section 0 of `STANDARD.md`; every (B) line there must also be done):
- `/graph` shows at least 20 entities and 20 relations from the seeded KB.
- A taxonomy generated to depth 2 and exported as SKOS Turtle.
- No Progress-internal copy remains; the app presents as a product.
- 390 px render clean.

**Deliberately not built (the article's "where to take it next").**
- Edit and merge entities back into the graph
- Governance workflow with approvals
- Push the taxonomy to a semantic platform

**Copilot prompts.** `/finish-starter` for each step above, `/qa-gate` at the end, `/write-article` last. Cheapest model for renames and copy; the premium model only for the step marked hardest in `README.md`.

**Token rule.** Copy from `reference/` and the chassis; never generate a client, a renderer or a Dockerfile. If a step needs a mechanism not confirmed in `.github/instructions/arag-api.instructions.md` or `reference/arag-platform-quirks.md`, stop and flag it; do not invent an endpoint.
