# MediaChat

> "Customers ask questions our videos and manuals already answer, in languages our team doesn't speak. They get a text wall or nothing."

**Answers that show the clip, the image and the table, in the language the customer asked in.**

A chat that answers in the asker's language and, when the cited source is a video, image or PDF, shows the clip at the cited second, the image, or the page beside the answer.

## What Progress Agentic RAG does here
Multilingual retrieval over one KB with the answer language set in the prompt (the chassis `lang` field; `reference/multilingual-chat.py` shows the per-language prompt and the declined-answer path). Native video, image and PDF ingestion, with thumbnails and media fields read through `GET /resource/{id}?show=basic&show=extracted` and proxied server-side with the token. Remove ARAG and this is a chatbot that cannot see the media.

## Run it
```
cp .env.example .env        # fill ARAG_HOST, KB_ID, KB_TOKEN
pip install -r requirements.txt
uvicorn app:app --port 8080  # http://127.0.0.1:8080
```

## Where to take it next
Three things left out on purpose so this stays a starting point:
- **Voice input and spoken answers**
- **Personalisation by signed-in role**
- **Handoff to a human with the transcript attached**

## Hardest step
Step 3, media positions: confirm the paragraph position keys for video before coding; this is the only step that may need the quirks file.

## Series
Day 3 of ten ARAG starters. Each one is small, finished, and built on a Knowledge Box rather than a vector store. `BRIEF.md` is the build plan; `ARTICLE.md` is the LinkedIn piece.

## The standard

`STANDARD.md` defines what finished means for this product, line by line with blockers marked. `/audit-standard` reports against it; `/raise-standard` fixes one line per chat; `/qa-gate` is the independent check before anything goes public.
