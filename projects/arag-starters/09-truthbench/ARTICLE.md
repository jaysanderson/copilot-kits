# TruthBench: Paste ten questions. See which answers your knowledge base can actually back up, before a customer finds out

<!-- Day 9 of ten. Target 700 words. Written after the build, from what actually happened. Australian English, no em dashes, no banned words (delve, leverage, unlock, seamless, game-changing). Run /write-article to draft from this skeleton. -->

"The AI pilot demoed beautifully and we have no way to know whether it's making things up in production."

## The problem nobody owns
<!-- 2 short paragraphs. Who has this problem this month, what it costs them, why the usual fix (a chatbot, a search box, a spreadsheet) did not solve it. Name the role, not a company. -->

## What I built in half a day
<!-- 1 paragraph + the 30-second description of the screen. One screenshot or 45-second clip goes here. -->

## Why naive RAG gets this wrong
<!-- 1 paragraph. The specific failure: no evidence, no score, no structure, no media, no action. -->

## What Agentic RAG does here
`/predict/remi` groundedness against the full retrieved context (`groundedness` in `arag.py`; enterprise KBs), `contexts_from_ask`, and a `/find` versus `/ask` agreement check. Remove ARAG and this is a spreadsheet of vibes.

## How it works, in four lines
<!-- Four numbered lines a non-developer can follow. No endpoint names. -->

## Where to take it next
Three things I left out on purpose:
- Regression history: diff two runs
- CI gate: non-zero exit when a score drops
- Generate the question set from the KB itself

## Try it
<!-- Repo link, live URL, one sentence on what to type first. Then: "Tag the person who has this problem." -->

<!-- Tag line for the post itself: CIO, risk, the sponsor who signed. -->
