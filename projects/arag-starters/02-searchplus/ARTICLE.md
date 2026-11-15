# SearchPlus: Site search that shows its evidence and its relevance, and lets the business pin, boost and bury results without a developer

<!-- Day 2 of ten. Target 700 words. Written after the build, from what actually happened. Australian English, no em dashes, no banned words (delve, leverage, unlock, seamless, game-changing). Run /write-article to draft from this skeleton. -->

"Our site search returns the wrong product first and we can't change it without a dev ticket. Every bad result is a lost sale."

## The problem nobody owns
<!-- 2 short paragraphs. Who has this problem this month, what it costs them, why the usual fix (a chatbot, a search box, a spreadsheet) did not solve it. Name the role, not a company. -->

## What I built in half a day
<!-- 1 paragraph + the 30-second description of the screen. One screenshot or 45-second clip goes here. -->

## Why naive RAG gets this wrong
<!-- 1 paragraph. The specific failure: no evidence, no score, no structure, no media, no action. -->

## What Agentic RAG does here
`/find` with `features: [keyword, semantic]` returns paragraph-level scores per resource (`resources_from_find` in `arag.py`), which is what makes a visible relevance score and a passage snippet possible. Label filters give facets. The rules re-rank the retrieved set in the app, so the index is never touched, which is what makes the rules safe for a non-developer. Remove ARAG and this is a keyword box with no passages and no semantics.

## How it works, in four lines
<!-- Four numbered lines a non-developer can follow. No endpoint names. -->

## Where to take it next
Three things I left out on purpose:
- Synonyms learned from zero-result queries
- A/B rule sets with a split and a report
- Search analytics: top queries, zero-result queries

## Try it
<!-- Repo link, live URL, one sentence on what to type first. Then: "Tag the person who has this problem." -->

<!-- Tag line for the post itself: Ecommerce manager, digital lead. -->
