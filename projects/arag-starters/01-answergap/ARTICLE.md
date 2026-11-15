# AnswerGap: See which brand the AI recommends for your buyers' questions, and what to publish to change it

<!-- Day 1 of ten. Target 700 words. Written after the build, from what actually happened. Australian English, no em dashes, no banned words (delve, leverage, unlock, seamless, game-changing). Run /write-article to draft from this skeleton. -->

"Ask ChatGPT about our category and it recommends our competitor. We don't know why, or what to publish to change it."

## The problem nobody owns
<!-- 2 short paragraphs. Who has this problem this month, what it costs them, why the usual fix (a chatbot, a search box, a spreadsheet) did not solve it. Name the role, not a company. -->

## What I built in half a day
<!-- 1 paragraph + the 30-second description of the screen. One screenshot or 45-second clip goes here. -->

## Why naive RAG gets this wrong
<!-- 1 paragraph. The specific failure: no evidence, no score, no structure, no media, no action. -->

## What Agentic RAG does here
One KB, one labelset `source`, one label per domain (`label_filter` in `arag.py`). The cited resources in each `/ask` response decide the winner per question; a question where your label never appears in `retrieval_results` is a gap. Question generation and the publish suggestions use `ask_structured` (JSON schema; never with `citations: true`). Remove ARAG and this is a scraper with opinions.

## How it works, in four lines
<!-- Four numbered lines a non-developer can follow. No endpoint names. -->

## Where to take it next
Three things I left out on purpose:
- Content briefs exported as docx from each gap
- Scheduled re-runs with a trend line per question
- Probing external LLM APIs for the same questions and comparing

## Try it
<!-- Repo link, live URL, one sentence on what to type first. Then: "Tag the person who has this problem." -->

<!-- Tag line for the post itself: Head of marketing, founder. -->
