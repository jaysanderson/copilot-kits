# GraphBuilder: Point it at your documents and see how your customers, products and suppliers actually connect, then export a taxonomy your systems can use

<!-- Day 7 of ten. Target 700 words. Written after the build, from what actually happened. Australian English, no em dashes, no banned words (delve, leverage, unlock, seamless, game-changing). Run /write-article to draft from this skeleton. -->

"The same customer, product or supplier is named six different ways across our documents. Nobody can see how anything connects."

## The problem nobody owns
<!-- 2 short paragraphs. Who has this problem this month, what it costs them, why the usual fix (a chatbot, a search box, a spreadsheet) did not solve it. Name the role, not a company. -->

## What I built in half a day
<!-- 1 paragraph + the 30-second description of the screen. One screenshot or 45-second clip goes here. -->

## Why naive RAG gets this wrong
<!-- 1 paragraph. The specific failure: no evidence, no score, no structure, no media, no action. -->

## What Agentic RAG does here
Taxonomy proposals come from `/ask` with a JSON schema, validated and repaired (`lib/engine/`). The graph view reads `/graph` (pass `top_k` explicitly and `undirected: true`) after a knowledge-graph extraction task has run on the KB. Remove ARAG and this is a mind map.

## How it works, in four lines
<!-- Four numbered lines a non-developer can follow. No endpoint names. -->

## Where to take it next
Three things I left out on purpose:
- Edit and merge entities back into the graph
- Governance workflow with approvals
- Push the taxonomy to a semantic platform

## Try it
<!-- Repo link, live URL, one sentence on what to type first. Then: "Tag the person who has this problem." -->

<!-- Tag line for the post itself: Data lead, knowledge manager. -->
