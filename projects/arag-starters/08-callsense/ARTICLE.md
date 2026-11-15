# CallSense: Upload the recordings. Ask what customers are actually saying. Get answers with the timestamp to prove it

<!-- Day 8 of ten. Target 700 words. Written after the build, from what actually happened. Australian English, no em dashes, no banned words (delve, leverage, unlock, seamless, game-changing). Run /write-article to draft from this skeleton. -->

"Hundreds of recorded calls a month and the only person who knows what customers are saying is the one who was on the call."

## The problem nobody owns
<!-- 2 short paragraphs. Who has this problem this month, what it costs them, why the usual fix (a chatbot, a search box, a spreadsheet) did not solve it. Name the role, not a company. -->

## What I built in half a day
<!-- 1 paragraph + the 30-second description of the screen. One screenshot or 45-second clip goes here. -->

## Why naive RAG gets this wrong
<!-- 1 paragraph. The specific failure: no evidence, no score, no structure, no media, no action. -->

## What Agentic RAG does here
Native audio ingestion and transcription through `/upload`; per-call `/ask` scoped with resource filters; REMi confidence (`lib/confidence.ts`); category labelsets via `/labelsets`. Remove ARAG and this is a transcript search box.

## How it works, in four lines
<!-- Four numbered lines a non-developer can follow. No endpoint names. -->

## Where to take it next
Three things I left out on purpose:
- Call libraries per team
- Speaker tags and talk-time
- Push themes to the CRM

## Try it
<!-- Repo link, live URL, one sentence on what to type first. Then: "Tag the person who has this problem." -->

<!-- Tag line for the post itself: Sales leader, customer success lead. -->
