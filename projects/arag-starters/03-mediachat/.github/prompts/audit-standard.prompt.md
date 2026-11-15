---
mode: agent
description: Audit this starter against STANDARD.md, rank the open lines, report with evidence, fix nothing
---

# Audit against the standard

You report. You do not edit, redeploy or reseed.

1. Read `STANDARD.md`, `BRIEF.md` and `README.md`.
2. Run what can be run: `python smoke_test.py` (or the base app's test), `ruff check .` or `npm run lint` if present, `grep -rniE` for the leak and name lists in `copilot-instructions.md`, and open the app locally at 390x844 and 1440x900 if it runs.
3. Walk every line of `STANDARD.md` in order. Per line: `PASS`, `FAIL` or `NOT YET` with one sentence and the evidence (response body, grep output, screenshot path you viewed, URL you opened). Lines whose status is `chassis` or `verify` still need evidence; do not pass them on trust.
4. Report, most severe first: `(B) lines failing | then non-blockers failing | then passing lines in one compact table`.
5. End with the single line to fix next and why, and the estimated size (small, medium, large).
6. Do not change `STANDARD.md`; `/raise-standard` does that when a line is actually fixed.
