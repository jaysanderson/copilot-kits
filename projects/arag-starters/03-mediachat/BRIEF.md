# BRIEF: MediaChat (day 3 of the series)

> "Customers ask questions our videos and manuals already answer, in languages our team doesn't speak. They get a text wall or nothing."

**Who shares this.** Customer experience lead, support manager.

**Promise.** Answers that show the clip, the image and the table, in the language the customer asked in.

**The one job.** A chat that answers in the asker's language and, when the cited source is a video, image or PDF, shows the clip at the cited second, the image, or the page beside the answer.

**Why ARAG is load-bearing.** Multilingual retrieval over one KB with the answer language set in the prompt (the chassis `lang` field; `reference/multilingual-chat.py` shows the per-language prompt and the declined-answer path). Native video, image and PDF ingestion, with thumbnails and media fields read through `GET /resource/{id}?show=basic&show=extracted` and proxied server-side with the token. Remove ARAG and this is a chatbot that cannot see the media.

**Base.** The chassis (`CHASSIS.md`): `app.py`, `arag.py`, `static/`, `product.json`. Add product routes under `# --- product routes` in `app.py` and a panel in `static/`. Nothing in the chassis is rewritten.

**Knowledge Box.** New KB with media uploaded through `/upload` (binaries only). Writer token.

**Finishing steps, in order (one Copilot chat each).**
1. Seed a small media KB through `/upload` (binaries only): three short videos, five images, three PDFs. Public Progress material or your own; disclose in the footer.
2. Extend `grounded_answer()` in `app.py`: for each cited resource add `kind` (video, image, pdf, text), `thumbnail` (a proxied route) and `at` (start second or page) from the paragraph position metadata. Confirm the exact position keys in `reference/arag-platform-quirks.md` before coding.
3. Add `GET /api/media/{rid}/{field}` that streams the thumbnail or file from `/resource/{rid}` with the token server-side.
4. Render media cards beside the answer in `static/app.js`: copy the layout of `reference/media-citations/Thumbnail.tsx` and `OtherResourceCard.tsx` into vanilla JS; a video card seeks to `at`.
5. One-tag embed: adapt `reference/embed/widget.js` so the chat drops into any page with a single script tag.
6. Keep the chassis language selector and the RTL handling as they are.

**Done when** (these lines are section 0 of `STANDARD.md`; every (B) line there must also be done):
- A question asked in Japanese is answered in Japanese with a video card that starts at the cited second.
- An image card and a PDF page card each open the source.
- No thumbnail URL in the page points at the ARAG host; all go through this app.
- 390 px render clean; zero raw markdown.

**Deliberately not built (the article's "where to take it next").**
- Voice input and spoken answers
- Personalisation by signed-in role
- Handoff to a human with the transcript attached

**Copilot prompts.** `/finish-starter` for each step above, `/qa-gate` at the end, `/write-article` last. Cheapest model for renames and copy; the premium model only for the step marked hardest in `README.md`.

**Token rule.** Copy from `reference/` and the chassis; never generate a client, a renderer or a Dockerfile. If a step needs a mechanism not confirmed in `.github/instructions/arag-api.instructions.md` or `reference/arag-platform-quirks.md`, stop and flag it; do not invent an endpoint.
