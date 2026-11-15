---
mode: agent
description: Do the next unfinished step of BRIEF.md with evidence, then stop
---

# Finish the starter, one step at a time

1. Read `BRIEF.md`. Find the first step under "Finishing steps" that is not yet done (check the repo, do not assume).
2. State the step in one line and list the files you will copy from (`reference/`, the chassis, or the source app). If a mechanism is not confirmed in `.github/instructions/arag-api.instructions.md` or `reference/arag-platform-quirks.md`, stop and say so.
3. Do the step. Copy before you write. Keep the change inside the files the step names.
4. Evidence: run it, paste the response body or the grep output, open the page and describe what is on screen at 390 px and desktop.
5. Check the step against the "Done when" lines it affects and the gates in `copilot-instructions.md`.
6. Stop. One step per chat. Say which step is next.
