# Definition of Pass (content kit edition)

Trimmed from the full factory DoP (`reference/DEFINITION-OF-PASS.full.md`) to the lines that apply to written content. Every piece is walked line by line before it is called done. The reviewer records PASS or FAIL per line with evidence attached; "looks fine" is a FAIL. One FAIL on a truth or safety line means the piece is not done. The reviewer reports; the author fixes and re-gates.

## A. Truth
1. Every product claim traces to the piece's `BRIEF.md` LOCKED FACTS table or `skeletons/positioning/messaging-house.md` section 6. Nothing from memory. A claim the brief cannot confirm is dropped or moved to a "not confirmed" note, never kept silently.
2. No fabricated numbers: no invented accuracy percentage, adoption rate, ROI figure, payback period or benchmark. The product publishes no accuracy percentage; quality is shown with measured per-answer metrics and a cited answer, never a made-up figure.
3. Certifications (SOC 2, ISO 27001 and similar) are named only where the brief marks them verified, and the text states who asserts them ("vendor-stated" or "independently verified").
4. Locked facts hold everywhere: the same value, wording and source appear identically in every piece of a kit. Analyst results are stated exactly (a leader in one criterion is not "a Leader").
5. Statistics come from authoritative independent sources and are cited in-text. Vendor numbers are labelled as vendor numbers. Anything older than five years carries its date or is replaced. Market sizing names the provider and gives a range.
6. The target account's direct competitor is never used as a proof source.
7. All prices are in USD. No geo-localised price appears anywhere, including inside a screenshot crop.
8. Every number in the piece is on a real scale with real units from a named source. Every invented name (fictional company, product, person) has been checked for a collision with a real one.
9. Any statement that a check was performed is backed by the check's output in the certificate, not asserted.

## B. Safety and hygiene
10. No secrets, keys, tokens or internal URLs appear in any file, screenshot or export.
11. No hosting-region or infrastructure string appears on any customer-facing surface or screenshot; checked against the account's residency requirement in the brief.
12. Other customers' names and identifiers are anonymised ("a state agency", "the account") in text and in every screenshot.
13. No real third-party brand is used as if owned; no real personal identifiers; fictional entities and neutral logins only.
14. Outbound (posts, emails, anything sent or published) carries a DRAFT status line until the owner signs off. Nothing in this kit sends or publishes.
15. Reused screenshots are re-checked against the live product before use; a stale figure in a screenshot is a FAIL.

## C. Language and voice
16. Australian English throughout (organise, colour, programme).
17. No em dashes or en dashes; a spaced hyphen " - ", comma, colon or full stop instead. Exception: the owner's personal LinkedIn posts and articles.
18. Banned words absent: delve, leverage, unlock, seamless, game-changing. Watchlist words (utilise, enhance, robust, comprehensive, landscape, journey and the rest in `.github/instructions/writing-voice.instructions.md`) do not cluster: no three in one paragraph.
19. De-AI pass completed and recorded: hedging, filler, reflex triads and corporate fluff removed; at most one "not X but Y" per page; no bridge sentences; no summary ending.
20. Rhythm and paragraphs: sentence lengths vary (in any five sentences one under 8 words and one over 25); paragraphs run 1 to 4 sentences with at most one longer paragraph per page; the first sentences of the paragraphs, read in order, carry the argument.
21. Recipient's vocabulary and genre: load-bearing ideas are stated in ordinary sentences with the reasoning visible, not as internal shorthand or slogans. A response to another team's document follows that document's structure and section numbers.
22. The room test: the piece would survive a CIO, CMO or solutions architect reading it as practitioner work. If not, it is not finished.

## D. Written content
23. LinkedIn and social: hook in line one; short paragraphs; no hashtag spam; ends with a question that has a real answer or a concrete take, never "Thoughts?".
24. Battlecards and objection guides: every row has claim, proof, trap question and counter; every claim and every competitor statement carries a source with the date read; unsourced competitor claims are dropped.
25. Blogs, one-pagers, two-pagers and email sequences consume the locked brief with zero drift: every number and claim in them appears in the brief, word for word where it is a locked value.
26. Emails: one idea, one ask, placeholders in square brackets, a DRAFT status line, no link to anything unverified.
27. Documents ship as .docx built with `tools/md_to_docx_enablement.py`, opened and checked (headings, tables, bold and italics rendered; no literal asterisks or backticks). Markdown is never the deliverable for a document.
28. HTML and PDF outputs follow `.github/instructions/html-reports.instructions.md`: brand tokens, approved fonts or Arial, the genuine logo files, Hex Loop cropped, every page viewed after render, no `{{` left in the HTML.
29. The file carries its header block (For, Purpose, Grounding, Date, Version) and a dated change-log line for this edition.
30. The piece was started from the nearest skeleton under `skeletons/`, and the chat shows the locked-facts check and the outline the user approved before drafting.

## E. Evidence
31. A PASS is only a PASS with evidence attached: the grep output for banned words and dashes, the brief row quoted for each number, the source URL and date for each statistic, the .docx opened, the rendered pages viewed.
32. A relayed verdict is not evidence. The reviewer sees the output directly or runs the check again.

## F. The owner's final read
33. On-message: consistent with the messaging house, no drift.
34. Audience fit: right for the named buyer as a judgment call, not only rule-compliance.
35. Defensible live: nothing in it the owner could not stand behind in the room.
