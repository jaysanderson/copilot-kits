# EvidenceReader: Drop in your documents, ask, and click any claim to land on the exact page that supports it

<!-- Day 4 of ten. Target 700 words. Written after the build, from what actually happened. Australian English, no em dashes, no banned words (delve, leverage, unlock, seamless, game-changing). Run /write-article to draft from this skeleton. -->

"The AI summary looked fine until someone asked 'where does it say that?' and nobody could show them."

## The problem nobody owns
<!-- 2 short paragraphs. Who has this problem this month, what it costs them, why the usual fix (a chatbot, a search box, a spreadsheet) did not solve it. Name the role, not a company. -->

## What I built in half a day
<!-- 1 paragraph + the 30-second description of the screen. One screenshot or 45-second clip goes here. -->

## Why naive RAG gets this wrong
<!-- 1 paragraph. The specific failure: no evidence, no score, no structure, no media, no action. -->

## What Agentic RAG does here
`POST /kb/{id}/upload` for binaries; `/ask` with `citations: true` keyed by paragraph id; paragraph positions from `GET /resource/{id}?show=extracted` give the page; `place_citations` in `arag.py` puts the markers at the claim. Remove ARAG and this is a summary nobody can check.

## How it works, in four lines
<!-- Four numbered lines a non-developer can follow. No endpoint names. -->

## Where to take it next
Three things I left out on purpose:
- Folders and per-folder scopes with `filter_expression`
- Share links to a question and its evidence
- Saved highlights and notes

## Try it
<!-- Repo link, live URL, one sentence on what to type first. Then: "Tag the person who has this problem." -->

<!-- Tag line for the post itself: Compliance, legal, anyone who signs off. -->
