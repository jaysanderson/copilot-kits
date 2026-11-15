# TriageDesk: Every case read the same way: a decision, a confidence and the evidence, in seconds, with a human in charge

<!-- Day 5 of ten. Target 700 words. Written after the build, from what actually happened. Australian English, no em dashes, no banned words (delve, leverage, unlock, seamless, game-changing). Run /write-article to draft from this skeleton. -->

"Two hundred applications a week, each read by a person, each decided slightly differently, nobody can explain why."

## The problem nobody owns
<!-- 2 short paragraphs. Who has this problem this month, what it costs them, why the usual fix (a chatbot, a search box, a spreadsheet) did not solve it. Name the role, not a company. -->

## What I built in half a day
<!-- 1 paragraph + the 30-second description of the screen. One screenshot or 45-second clip goes here. -->

## Why naive RAG gets this wrong
<!-- 1 paragraph. The specific failure: no evidence, no score, no structure, no media, no action. -->

## What Agentic RAG does here
`answer_json_schema` on `/ask` for schema-constrained decisions, with the instructions carried in the schema's property descriptions (a system prompt is ignored beside a schema) and provenance from `retrieval_results`; `filter_expression` scopes each case to the policy documents. All of it already runs in `app/pipeline.py` and `app/arag_client.py`. Remove ARAG and this is free text someone re-keys.

## How it works, in four lines
<!-- Four numbered lines a non-developer can follow. No endpoint names. -->

## Where to take it next
Three things I left out on purpose:
- A review queue with SLA timers
- An override log with the reviewer's reason
- Batch upload of a day's cases

## Try it
<!-- Repo link, live URL, one sentence on what to type first. Then: "Tag the person who has this problem." -->

<!-- Tag line for the post itself: Operations manager, service delivery lead. -->
