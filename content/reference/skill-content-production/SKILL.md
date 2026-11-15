---
name: content-production
description: Write blogs, LinkedIn posts/series, battle cards, one-pagers and email sequences from a locked account brief. Use for "write posts / battle card / one-pager / email". Encodes voice rules, the de-AI pass, and the mandatory .docx delivery format.
---

# Content production (Workflow 4)

Blogs, LinkedIn posts and series, battle cards, one-pagers (`python-docx` / `reportlab`),
email sequences. Output to `content/`; outbound to `content/drafts/`.

- **Voice** - first person, humble practitioner, punchy, commercially aware.
- **LinkedIn** - hook in line one, short paragraphs, no hashtag spam, end with a question
  or a concrete take. Never "thoughts?".
- **Battle cards** - claim, proof, trap question, counter. KB-verified.
- **Final de-AI pass on everything** - remove hedging, filler, symmetrical triads, and any
  banned word.
- **Document format for delivery:** any deliverable that ships as `asset_type: document` -
  blogs, LinkedIn posts, battle cards, one-pagers, technical/enablement docs, everything
  currently in this bucket - ships as an actual **Word file (.docx)**, never raw
  markdown/plain text. Build it with `python-docx` and submit with `mime:
  application/vnd.openxmlformats-officedocument.wordprocessingml.document` + a `.docx`
  filename - never as raw text (which strips formatting and is stored as a plain `.md`
  file, the wrong format). Drafting/review can still happen as markdown locally in
  `content/drafts/`; only the final submission needs to be `.docx`.

## Write in the recipient's genre, not our canon (GM feedback, 23 Sep 2026 - eval-spec response)

A response document sent cold to another team was rejected by its reader as "AI wrote
some cryptic set of ideas". Root causes, now binding checks on any document addressed
to a specific external reader or team:

1. **Recipient's vocabulary, never our canon.** Compressed internal phrases (coined
   labels, positioning shorthand, conclusions from conversations the reader was not in)
   read as cryptic slogans to a fresh reader. Every load-bearing idea gets stated in
   ordinary sentences with its reasoning visible, not asserted as a formula.
2. **Recipient's genre.** Match the form of what you are replying to: a team that
   writes numbered engineering specifications gets a plain working response that walks
   THEIR document by THEIR section numbers - not a manifesto, not a position paper.
   Length serves clarity; never compress argument into aphorism to hit a page count
   when the reader is sceptical (aphorism requires trust the audience may not have).
3. **The "X, not Y" rhythm is a named AI tell.** Repeated parallel constructions
   ("delivered not demanded", "orchestrates, not performs") plus short punchy stacked
   sentences read as AI/marketing prose to technical audiences. The de-AI pass scrubs
   RHYTHM as well as words: vary sentence length, allow at most one such construction
   per page, prefer plain declarative sentences.
4. **Sceptical, evidence-first readers trust artefacts over prose.** Where possible,
   attach the started thing (a corpus skeleton, a template, a trace) and let the
   document explain it, rather than sending claims alone.
