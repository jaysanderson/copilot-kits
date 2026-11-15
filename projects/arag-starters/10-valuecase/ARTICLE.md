# ValueCase: A business case where every number came from the prospect's own documents, with the citation to prove it

<!-- Day 10 of ten. Target 700 words. Written after the build, from what actually happened. Australian English, no em dashes, no banned words (delve, leverage, unlock, seamless, game-changing). Run /write-article to draft from this skeleton. -->

"We built a business case for AI from guesses. The prospect's own documents held the real numbers and nobody looked."

## The problem nobody owns
<!-- 2 short paragraphs. Who has this problem this month, what it costs them, why the usual fix (a chatbot, a search box, a spreadsheet) did not solve it. Name the role, not a company. -->

## What I built in half a day
<!-- 1 paragraph + the 30-second description of the screen. One screenshot or 45-second clip goes here. -->

## Why naive RAG gets this wrong
<!-- 1 paragraph. The specific failure: no evidence, no score, no structure, no media, no action. -->

## What Agentic RAG does here
`ask_structured` with a per-lever schema (`value`, `unit`, `source_title` as an enum of the retrieved titles, `quote`), scoped to the prospect's KB; the claim-check route in `reference/clinic-app.py` (lines 1002 to 1074) is the pattern for checking a figure against documents. Remove ARAG and this is a calculator.

## How it works, in four lines
<!-- Four numbered lines a non-developer can follow. No endpoint names. -->

## Where to take it next
Three things I left out on purpose:
- Portfolio view across prospects
- Export the case to a slide deck
- Re-propose when the documents change

## Try it
<!-- Repo link, live URL, one sentence on what to type first. Then: "Tag the person who has this problem." -->

<!-- Tag line for the post itself: CFO, sales leader, value engineer. -->
