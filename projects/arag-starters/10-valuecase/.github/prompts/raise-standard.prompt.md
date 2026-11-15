---
mode: agent
description: Fix the highest-ranked open line of STANDARD.md, prove it, mark it done, stop
---

# Raise the standard, one line per chat

1. Read `STANDARD.md`. Pick the first open line in this order: section 0 (B), then (B) lines by section, then non-blockers. If an `/audit-standard` report exists in the chat, take its "fix next" line instead.
2. State the line id and the files you will touch. Copy before you write: the chassis, `reference/` and the base app already hold clients, renderers, tests and Dockerfiles. If the fix needs an ARAG mechanism not confirmed in `.github/instructions/arag-api.instructions.md` or `reference/arag-platform-quirks.md`, stop and say so.
3. Do the fix. Stay inside the files the line needs. Do not build anything under Where to take it next.
4. Prove it: run the test or command, paste the response body or grep output, or open the page and describe both widths. A check that cannot fail is not evidence.
5. Update the line's status in `STANDARD.md` to `done (<evidence in five words>)`. If the fix is partial, leave it `todo` and say what remains.
6. Stop. Name the next open line.
