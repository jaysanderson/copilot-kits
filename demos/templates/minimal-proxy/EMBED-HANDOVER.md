# Embed and search-experiences handover (mu-embed, 9 Oct 2026)

## Built and verified locally
- `static/embed/widget.js`: self-contained widget (shadow DOM, vanilla). Attributes: data-langs, data-accent, data-placeholder, data-scope, data-scope-label, data-scope-name, data-api. Fires an `ask-lang` event. The markdown block between `BEGIN/END mdlite` is GENERATED: run `python seed/sync_widget_md.py` after any change to `static/mdlite.js`; `tests/md_check.py` (128 items, 0 failures at last run) fails on drift.
- `embed.py`, `templates/embed.html`: `/embed`, the mock third-party page (Westbound Student Network) with two widgets. Deployed by mu-front.
- Proven: overflow at 390/360 (long URL, email, filename, CJK, Arabic tokens; control fails at 1513 vs 390), cross-origin from a foreign origin against the deployed URL, forced-timeout state, Arabic RTL, decline, forced 502.
- `seed/set_origin_path.py`: sets origin.path on all 343 KB resources. REQUIRED for any scope. Re-run after any reseed.

## Built, NOT deployed, NOT handed over as ready
- Section hubs: `sections.py` (module-level `router`), `templates/section.html`, `static/section.css`, `static/section.js`, `static/section-reveal.html`, plus widget.js additions (translated scope label, ask-lang event). Routes `/section/{scholarships,how-to-apply,international}`. Verified locally (real Arabic chip, 1280 and 390, no overflow, scope guard positive control: filter stripped + guard off gave 7 outside-scope sources, guard on withheld). Not verified: reveal screenshots not looked at.
- STATUS UPDATE (team-lead): hubs ship by URL in the in-flight deploy. The home quick-card repoint is HELD (homepage being filmed); wire cards after the film. Original: mu-front has the include line (`from sections import router as sections_router` / `app.include_router(sections_router)`) and the quick-card suggestion, but NO ready signal was sent.

## Specced only
- Header instant search (shape A): hsearch.js, debounce 250ms, 3+ chars, cache, 6 results via POST /api/pages (no generation), "/" focus, 4 languages, retry state, 390px sheet. Needs a mount element id from mu-front (index.html, the dead `.search` span).
- Contextual suggested questions on /page (shape B): sent to mu-page, no reply. 3 questions per (page, lang), one real ask, flash-lite pinned, lazy, cap 16 calls per reseed, no chips on failure, never canned.

## Agreed / resolved collisions (team-lead, 9 Oct)
1. Header mount: mu-front owns index.html and the header; I send the mount point and files, never edit it.
2. Shape B stays mu-page's call; spec states the call ceiling.
3. Home quick-cards may point to /section/<key> BUT each hub carries a prominent outbound button to the real university.edu.au page (conversion path, Field Rule 10 / B48). Done in the hub.
4. include_router lines go to mu-front. I never edit app.py.
Also: the Arabic phone-reversal guard belongs to mu-chat (answers.py), not to me.

## Open defects
- The model intermittently emits Arabic phone numbers reversed (`6063 9360 8 61+`), 1 of 2 samples; no renderer can fix it. Guard parked, unbuilt.
- Arabic answer with a long bare URL at 390px: citation badge lands visually inside the URL fragment (mu-page's renderer).
- /page has no deep-link param; hubs cannot link per page.
