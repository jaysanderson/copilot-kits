---
mode: ask
description: Produce BRIEF.md with a LOCKED FACTS table and a claims-not-confirmed list for a prospect demo
---

# Locked brief

Produce `BRIEF.md` for the prospect or vertical named in the chat. Every later artefact (demo copy, deck, video) cites this file verbatim and never drifts from it.

## Sources, in order
1. Files already in the project (`research/`, the template README, `reference/`).
2. The prospect's own public site and filings. Record the URL and the date read.
3. Named independent sources for any statistic. Never the prospect's direct competitor. Date anything older than five years.
4. ARAG capability claims only where you can point to `reference/skill-arag-kb/SKILL.md`, `reference/skill-arag-demo-app/SKILL.md` or `templates/portal/docs/ARAG-API.md`. No product claim from memory.

## Output: BRIEF.md with these sections
1. **Company snapshot** - five lines maximum: what they do, size, markets, systems named publicly, the buyer.
2. **The problem** - three lines in the prospect's own vocabulary.
3. **Where ARAG fits** - five use cases, each tied to a real mechanism (`/ask` with citations, `answer_json_schema`, labels and `/catalog`, `/graph`, retrieval agent over MCP).
4. **Personas** - one line each (CIO, Solutions Architect, ISV Product Manager, ICT Leader, Developer) with the message for each.
5. **LOCKED FACTS** table: `metric | value | source (URL or file) | verified y/n`. Every number that will appear anywhere goes here. A row with no source is not allowed; move it to section 6.
6. **CLAIMS NOT CONFIRMED - do not use** - every claim you wanted but could not source, with what would confirm it.
7. **Residency note** - the zone the demo KB uses, by env var name only, and whether the prospect has a residency constraint.
8. **Demo plan** - the template to copy and why, the five routes, the wow moment, the honest decline question.

## Rules
- Never invent a number. Never merge two true figures into one range.
- No accuracy, adoption or ROI figure unless a named independent source gives it.
- Pricing in USD only.
- Australian English, no em dashes, none of: delve, leverage, unlock, seamless, game-changing.
- Fictional names for people and demo entities; note that a trademark check is owed on any invented brand.
