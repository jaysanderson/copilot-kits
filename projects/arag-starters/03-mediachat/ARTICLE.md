# MediaChat: Answers that show the clip, the image and the table, in the language the customer asked in

<!-- Day 3 of ten. Target 700 words. Written after the build, from what actually happened. Australian English, no em dashes, no banned words (delve, leverage, unlock, seamless, game-changing). Run /write-article to draft from this skeleton. -->

"Customers ask questions our videos and manuals already answer, in languages our team doesn't speak. They get a text wall or nothing."

## The problem nobody owns
<!-- 2 short paragraphs. Who has this problem this month, what it costs them, why the usual fix (a chatbot, a search box, a spreadsheet) did not solve it. Name the role, not a company. -->

## What I built in half a day
<!-- 1 paragraph + the 30-second description of the screen. One screenshot or 45-second clip goes here. -->

## Why naive RAG gets this wrong
<!-- 1 paragraph. The specific failure: no evidence, no score, no structure, no media, no action. -->

## What Agentic RAG does here
Multilingual retrieval over one KB with the answer language set in the prompt (the chassis `lang` field; `reference/multilingual-chat.py` shows the per-language prompt and the declined-answer path). Native video, image and PDF ingestion, with thumbnails and media fields read through `GET /resource/{id}?show=basic&show=extracted` and proxied server-side with the token. Remove ARAG and this is a chatbot that cannot see the media.

## How it works, in four lines
<!-- Four numbered lines a non-developer can follow. No endpoint names. -->

## Where to take it next
Three things I left out on purpose:
- Voice input and spoken answers
- Personalisation by signed-in role
- Handoff to a human with the transcript attached

## Try it
<!-- Repo link, live URL, one sentence on what to type first. Then: "Tag the person who has this problem." -->

<!-- Tag line for the post itself: Customer experience lead, support manager. -->
